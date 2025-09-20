"""
Views for billing app.
"""
import json
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView, TemplateView
)
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from organizations.mixins import OrganizationPermissionMixin
from .models import (
    Plan, Subscription, UsageMeter, Invoice, InvoiceItem, PaymentMethod,
    Payment, WebhookEvent, BillingAddress, Coupon, CouponUsage, BillingNotification
)
from .forms import (
    PlanSelectionForm, BillingAddressForm, PaymentMethodForm, SubscriptionUpdateForm,
    CouponForm, UsageReportForm, BillingSearchForm, CancelSubscriptionForm, PaymentRetryForm
)


class BillingDashboardView(LoginRequiredMixin, OrganizationPermissionMixin, TemplateView):
    """Billing dashboard with subscription overview."""
    template_name = 'billing/dashboard.html'
    required_role = 'ORG_ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Current subscription
        current_subscription = Subscription.objects.filter(
            organization=organization,
            status__in=['ACTIVE', 'TRIALING', 'PAST_DUE']
        ).first()
        
        context['current_subscription'] = current_subscription
        
        if current_subscription:
            # Usage meters
            context['usage_meters'] = UsageMeter.objects.filter(
                subscription=current_subscription,
                period_start__lte=timezone.now(),
                period_end__gte=timezone.now()
            ).order_by('usage_type')
            
            # Recent invoices
            context['recent_invoices'] = Invoice.objects.filter(
                organization=organization
            ).order_by('-created_at')[:5]
            
            # Payment methods
            context['payment_methods'] = PaymentMethod.objects.filter(
                organization=organization,
                is_active=True
            ).order_by('-is_default', '-created_at')
            
            # Billing statistics
            context['billing_stats'] = {
                'total_paid': Payment.objects.filter(
                    organization=organization,
                    status='SUCCEEDED'
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'pending_invoices': Invoice.objects.filter(
                    organization=organization,
                    status='OPEN'
                ).count(),
                'failed_payments': Payment.objects.filter(
                    organization=organization,
                    status='FAILED'
                ).count(),
            }
        
        # Available plans for upgrade/downgrade
        if organization.is_company:
            context['available_plans'] = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_pdi=True
            ).order_by('sort_order', 'price_monthly')
        elif organization.is_recruiter:
            context['available_plans'] = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_recruiting=True
            ).order_by('sort_order', 'price_monthly')
        else:
            context['available_plans'] = Plan.objects.filter(
                is_active=True,
                is_public=True
            ).order_by('sort_order', 'price_monthly')
        
        return context


class PlanListView(LoginRequiredMixin, ListView):
    """List available subscription plans."""
    model = Plan
    template_name = 'billing/plan_list.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        return Plan.objects.filter(
            is_active=True,
            is_public=True
        ).order_by('sort_order', 'price_monthly')


class SubscribeView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Subscribe to a plan."""
    form_class = PlanSelectionForm
    template_name = 'billing/subscribe.html'
    required_role = 'ORG_ADMIN'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        organization = self.get_organization()
        plan = form.cleaned_data['plan']
        billing_cycle = form.cleaned_data['billing_cycle']
        coupon = form.cleaned_data.get('coupon_code')
        
        # Check if organization already has active subscription
        existing_subscription = Subscription.objects.filter(
            organization=organization,
            status__in=['ACTIVE', 'TRIALING']
        ).first()
        
        if existing_subscription:
            messages.warning(
                self.request,
                _('You already have an active subscription. Please cancel it first or contact support for plan changes.')
            )
            return redirect('billing:dashboard')
        
        # Calculate pricing
        amount = plan.get_price_for_cycle(billing_cycle)
        
        # Apply coupon if provided
        if coupon:
            amount = coupon.apply_discount(amount)
        
        # Store subscription details in session for payment processing
        self.request.session['pending_subscription'] = {
            'plan_id': str(plan.id),
            'billing_cycle': billing_cycle,
            'amount': str(amount),
            'coupon_id': str(coupon.id) if coupon else None,
        }
        
        return redirect('billing:payment_method')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Get available plans
        if organization.is_company:
            context['plans'] = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_pdi=True
            ).order_by('sort_order', 'price_monthly')
        elif organization.is_recruiter:
            context['plans'] = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_recruiting=True
            ).order_by('sort_order', 'price_monthly')
        
        return context


class PaymentMethodView(LoginRequiredMixin, OrganizationPermissionMixin, TemplateView):
    """Select or add payment method."""
    template_name = 'billing/payment_method.html'
    required_role = 'ORG_ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Get pending subscription from session
        pending_subscription = self.request.session.get('pending_subscription')
        if not pending_subscription:
            messages.error(self.request, _('No pending subscription found.'))
            return context
        
        context['pending_subscription'] = pending_subscription
        context['plan'] = get_object_or_404(Plan, id=pending_subscription['plan_id'])
        
        # Get existing payment methods
        context['payment_methods'] = PaymentMethod.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('-is_default', '-created_at')
        
        return context


class InvoiceListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List organization invoices."""
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    required_role = 'ORG_ADMIN'
    
    def get_queryset(self):
        queryset = Invoice.objects.filter(
            organization=self.get_organization()
        ).select_related('subscription', 'subscription__plan')
        
        # Apply search filters
        form = BillingSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            provider = form.cleaned_data.get('provider')
            plan = form.cleaned_data.get('plan')
            
            if search:
                queryset = queryset.filter(
                    Q(invoice_number__icontains=search) |
                    Q(subscription__plan__name__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status)
            
            if provider:
                queryset = queryset.filter(provider=provider)
            
            if plan:
                queryset = queryset.filter(subscription__plan=plan)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = BillingSearchForm(self.request.GET)
        
        # Invoice statistics
        organization = self.get_organization()
        context['invoice_stats'] = {
            'total_invoices': Invoice.objects.filter(organization=organization).count(),
            'paid_invoices': Invoice.objects.filter(organization=organization, status='PAID').count(),
            'open_invoices': Invoice.objects.filter(organization=organization, status='OPEN').count(),
            'overdue_invoices': Invoice.objects.filter(
                organization=organization,
                status='OPEN',
                due_date__lt=timezone.now()
            ).count(),
        }
        
        return context


class InvoiceDetailView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Invoice detail view."""
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    context_object_name = 'invoice'
    required_role = 'ORG_ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get invoice items
        context['invoice_items'] = self.object.items.order_by('item_type', 'description')
        
        # Get payments for this invoice
        context['payments'] = self.object.payments.order_by('-created_at')
        
        return context


class UsageReportView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Generate usage reports."""
    form_class = UsageReportForm
    template_name = 'billing/usage_report.html'
    required_role = 'ORG_ADMIN'
    
    def form_valid(self, form):
        organization = self.get_organization()
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        usage_types = form.cleaned_data.get('usage_types', [])
        include_overages = form.cleaned_data['include_overages']
        
        # Get usage data
        usage_meters = UsageMeter.objects.filter(
            organization=organization,
            period_start__date__gte=date_from,
            period_end__date__lte=date_to
        )
        
        if usage_types:
            usage_meters = usage_meters.filter(usage_type__in=usage_types)
        
        usage_data = usage_meters.order_by('period_start', 'usage_type')
        
        context = self.get_context_data(form=form)
        context.update({
            'usage_data': usage_data,
            'date_from': date_from,
            'date_to': date_to,
            'include_overages': include_overages,
        })
        
        return render(self.request, self.template_name, context)


class SubscriptionUpdateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Update subscription plan."""
    model = Subscription
    form_class = SubscriptionUpdateForm
    template_name = 'billing/subscription_update.html'
    success_message = _('Subscription updated successfully!')
    required_role = 'ORG_ADMIN'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('billing:dashboard')


class CancelSubscriptionView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Cancel subscription."""
    form_class = CancelSubscriptionForm
    template_name = 'billing/cancel_subscription.html'
    required_role = 'ORG_ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        context['subscription'] = Subscription.objects.filter(
            organization=organization,
            status__in=['ACTIVE', 'TRIALING']
        ).first()
        
        return context
    
    def form_valid(self, form):
        organization = self.get_organization()
        subscription = Subscription.objects.filter(
            organization=organization,
            status__in=['ACTIVE', 'TRIALING']
        ).first()
        
        if not subscription:
            messages.error(self.request, _('No active subscription found.'))
            return redirect('billing:dashboard')
        
        reason = form.cleaned_data['reason']
        cancel_immediately = form.cleaned_data['cancel_immediately']
        feedback = form.cleaned_data['feedback']
        
        # Build cancellation reason
        cancellation_reason = f"Reason: {dict(form.CANCELLATION_REASONS)[reason]}"
        if feedback:
            cancellation_reason += f"\nFeedback: {feedback}"
        
        # Cancel subscription
        subscription.cancel(
            reason=cancellation_reason,
            at_period_end=not cancel_immediately
        )
        
        if cancel_immediately:
            messages.success(
                self.request,
                _('Subscription cancelled immediately. Access to premium features has been disabled.')
            )
        else:
            messages.success(
                self.request,
                _('Subscription will be cancelled at the end of the current billing period on {}.').format(
                    subscription.current_period_end.strftime('%B %d, %Y')
                )
            )
        
        return redirect('billing:dashboard')


class BillingAddressView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Manage billing address."""
    model = BillingAddress
    form_class = BillingAddressForm
    template_name = 'billing/billing_address.html'
    success_message = _('Billing address updated successfully!')
    required_role = 'ORG_ADMIN'
    
    def get_object(self, queryset=None):
        """Get existing billing address or return None for new."""
        return BillingAddress.objects.filter(
            organization=self.get_organization()
        ).first()
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object:
            return self.render_to_response(self.get_context_data(form=self.get_form()))
        else:
            return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object:
            return self.put(request, *args, **kwargs)
        else:
            return super().post(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        """Handle update of existing address."""
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        if self.object:
            # Update existing
            for field, value in form.cleaned_data.items():
                setattr(self.object, field, value)
            self.object.save()
            self.object = self.object  # For success_url
        else:
            # Create new
            form.instance.organization = self.get_organization()
            self.object = form.save()
        
        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('billing:dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['form'] = self.form_class(instance=self.object)
        return context


class CouponListView(LoginRequiredMixin, ListView):
    """List available coupons (super admin only)."""
    model = Coupon
    template_name = 'billing/coupon_list.html'
    context_object_name = 'coupons'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Coupon.objects.all().order_by('-created_at')


class CouponCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create new coupon (super admin only)."""
    model = Coupon
    form_class = CouponForm
    template_name = 'billing/coupon_form.html'
    success_message = _('Coupon created successfully!')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('billing:coupon_list')


# Webhook Views
@method_decorator(csrf_exempt, name='dispatch')
class PayPalWebhookView(View):
    """Handle PayPal webhook events."""
    
    def post(self, request):
        try:
            # Parse webhook data
            webhook_data = json.loads(request.body.decode('utf-8'))
            event_type = webhook_data.get('event_type', '')
            event_id = webhook_data.get('id', '')
            
            # Create webhook event record
            webhook_event = WebhookEvent.objects.create(
                provider='paypal',
                event_type=event_type,
                provider_event_id=event_id,
                raw_data=webhook_data
            )
            
            # Process webhook asynchronously
            from .tasks import process_webhook_event
            process_webhook_event.delay(webhook_data, 'paypal')
            
            return JsonResponse({'status': 'received'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """Handle Stripe webhook events."""
    
    def post(self, request):
        try:
            # Parse webhook data
            webhook_data = json.loads(request.body.decode('utf-8'))
            event_type = webhook_data.get('type', '')
            event_id = webhook_data.get('id', '')
            
            # TODO: Verify webhook signature
            # sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
            
            # Create webhook event record
            webhook_event = WebhookEvent.objects.create(
                provider='stripe',
                event_type=event_type,
                provider_event_id=event_id,
                raw_data=webhook_data
            )
            
            # Process webhook asynchronously
            from .tasks import process_webhook_event
            process_webhook_event.delay(webhook_data, 'stripe')
            
            return JsonResponse({'status': 'received'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class UsageAPIView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """API for incrementing usage meters."""
    required_role = 'MEMBER'
    
    def post(self, request):
        organization = self.get_organization()
        usage_type = request.POST.get('usage_type')
        amount = int(request.POST.get('amount', 1))
        
        # Get current subscription
        subscription = Subscription.objects.filter(
            organization=organization,
            status__in=['ACTIVE', 'TRIALING']
        ).first()
        
        if not subscription:
            return JsonResponse({'error': 'No active subscription'}, status=400)
        
        # Get current usage meter
        now = timezone.now()
        usage_meter = UsageMeter.objects.filter(
            subscription=subscription,
            usage_type=usage_type,
            period_start__lte=now,
            period_end__gte=now
        ).first()
        
        if not usage_meter:
            return JsonResponse({'error': 'Usage meter not found'}, status=400)
        
        # Check if usage would exceed limit (for non-overage plans)
        if not usage_meter.overage_allowed and usage_meter.current_usage + amount > usage_meter.limit:
            return JsonResponse({
                'error': 'Usage limit exceeded',
                'current_usage': usage_meter.current_usage,
                'limit': usage_meter.limit,
                'remaining': usage_meter.remaining_usage
            }, status=429)
        
        # Increment usage
        new_usage = usage_meter.increment_usage(amount)
        
        return JsonResponse({
            'success': True,
            'current_usage': new_usage,
            'limit': usage_meter.limit,
            'remaining': usage_meter.remaining_usage,
            'usage_percentage': usage_meter.usage_percentage,
            'is_over_limit': usage_meter.is_over_limit,
            'overage_cost': float(usage_meter.overage_cost)
        })


class BillingAnalyticsView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """Get billing analytics data for charts."""
    required_role = 'ORG_ADMIN'
    
    def get(self, request):
        organization = self.get_organization()
        
        # Monthly revenue
        monthly_revenue = []
        for i in range(12):
            month_date = timezone.now().replace(day=1) - timezone.timedelta(days=30*i)
            revenue = Payment.objects.filter(
                organization=organization,
                status='SUCCEEDED',
                created_at__year=month_date.year,
                created_at__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_revenue.append({
                'month': month_date.strftime('%b %Y'),
                'revenue': float(revenue)
            })
        
        # Usage trends
        usage_trends = {}
        for usage_type, _ in UsageMeter.USAGE_TYPES:
            trend_data = []
            for i in range(6):  # Last 6 months
                month_date = timezone.now().replace(day=1) - timezone.timedelta(days=30*i)
                usage = UsageMeter.objects.filter(
                    organization=organization,
                    usage_type=usage_type,
                    period_start__year=month_date.year,
                    period_start__month=month_date.month
                ).aggregate(avg_usage=Sum('current_usage'))['avg_usage'] or 0
                
                trend_data.append({
                    'month': month_date.strftime('%b'),
                    'usage': usage
                })
            
            usage_trends[usage_type] = list(reversed(trend_data))
        
        return JsonResponse({
            'monthly_revenue': list(reversed(monthly_revenue)),
            'usage_trends': usage_trends,
        })


class PaymentRetryView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Retry failed payment."""
    form_class = PaymentRetryForm
    template_name = 'billing/payment_retry.html'
    required_role = 'ORG_ADMIN'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = get_object_or_404(Invoice, pk=self.kwargs['invoice_pk'])
        return context
    
    def form_valid(self, form):
        invoice = get_object_or_404(Invoice, pk=self.kwargs['invoice_pk'])
        payment_method = form.cleaned_data['payment_method']
        
        # TODO: Implement payment retry logic with selected payment method
        # This would integrate with PayPal/Stripe APIs
        
        messages.success(
            self.request,
            _('Payment retry initiated. You will receive an email confirmation.')
        )
        
        return redirect('billing:invoice_detail', pk=invoice.pk)


# AJAX Views
class ValidateCouponView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """Validate coupon code via AJAX."""
    required_role = 'ORG_ADMIN'
    
    def post(self, request):
        code = request.POST.get('code', '').upper()
        amount = request.POST.get('amount', 0)
        
        try:
            amount = Decimal(amount)
        except:
            amount = Decimal('0')
        
        try:
            coupon = Coupon.objects.get(code=code)
            organization = self.get_organization()
            
            if coupon.can_be_used_by(organization, amount):
                discounted_amount = coupon.apply_discount(amount)
                discount_amount = amount - discounted_amount
                
                return JsonResponse({
                    'valid': True,
                    'coupon_name': coupon.name,
                    'discount_type': coupon.get_discount_type_display(),
                    'discount_value': float(coupon.discount_value),
                    'original_amount': float(amount),
                    'discount_amount': float(discount_amount),
                    'final_amount': float(discounted_amount),
                })
            else:
                return JsonResponse({
                    'valid': False,
                    'error': _('This coupon cannot be used for your organization or order.')
                })
                
        except Coupon.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'error': _('Invalid coupon code.')
            })


class BillingStatsView(LoginRequiredMixin, View):
    """Get billing statistics for super admin."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        # Platform-wide statistics
        stats = {
            'total_subscriptions': Subscription.objects.filter(status__in=['ACTIVE', 'TRIALING']).count(),
            'total_revenue': Payment.objects.filter(status='SUCCEEDED').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'monthly_revenue': Payment.objects.filter(
                status='SUCCEEDED',
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'failed_payments': Payment.objects.filter(status='FAILED').count(),
            'active_trials': Subscription.objects.filter(status='TRIALING').count(),
            'churn_rate': 0,  # Would calculate from cancellation data
        }
        
        # Plan distribution
        plan_distribution = Plan.objects.annotate(
            subscription_count=Count('subscriptions', filter=Q(subscriptions__status__in=['ACTIVE', 'TRIALING']))
        ).values('name', 'subscription_count')
        
        # Revenue by plan
        revenue_by_plan = []
        for plan in Plan.objects.filter(is_active=True):
            revenue = Payment.objects.filter(
                status='SUCCEEDED',
                invoice__subscription__plan=plan
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            revenue_by_plan.append({
                'plan_name': plan.name,
                'revenue': float(revenue)
            })
        
        return JsonResponse({
            'stats': stats,
            'plan_distribution': list(plan_distribution),
            'revenue_by_plan': revenue_by_plan,
        })