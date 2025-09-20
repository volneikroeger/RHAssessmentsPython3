"""
Views for emails app.
"""
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView, TemplateView
)
from django.views import View

from organizations.mixins import OrganizationPermissionMixin
from .models import (
    EmailTemplate, EmailMessage, EmailCampaign, EmailSubscription,
    EmailLog, EmailQueue, EmailAnalytics, UnsubscribeRequest, EmailBlacklist
)
from .forms import (
    EmailTemplateForm, EmailCampaignForm, EmailMessageForm, EmailSubscriptionForm,
    BulkEmailForm, EmailTestForm, EmailAnalyticsFilterForm, UnsubscribeForm, EmailPreviewForm
)


class EmailDashboardView(LoginRequiredMixin, OrganizationPermissionMixin, TemplateView):
    """Email dashboard with overview and statistics."""
    template_name = 'emails/dashboard.html'
    required_role = 'HR'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Email statistics
        context['email_stats'] = {
            'total_sent': EmailMessage.objects.filter(organization=organization, status='SENT').count(),
            'sent_today': EmailMessage.objects.filter(
                organization=organization,
                status='SENT',
                sent_at__date=timezone.now().date()
            ).count(),
            'pending_emails': EmailMessage.objects.filter(organization=organization, status='QUEUED').count(),
            'failed_emails': EmailMessage.objects.filter(organization=organization, status='FAILED').count(),
        }
        
        # Recent emails
        context['recent_emails'] = EmailMessage.objects.filter(
            organization=organization
        ).select_related('template', 'user').order_by('-created_at')[:10]
        
        # Active campaigns
        context['active_campaigns'] = EmailCampaign.objects.filter(
            organization=organization,
            status__in=['SCHEDULED', 'SENDING']
        ).order_by('-created_at')[:5]
        
        # Email templates
        context['templates'] = EmailTemplate.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('template_type', 'name')[:8]
        
        # Analytics summary
        latest_analytics = EmailAnalytics.objects.filter(
            organization=organization
        ).order_by('-period_start').first()
        
        if latest_analytics:
            context['analytics_summary'] = {
                'delivery_rate': latest_analytics.delivery_rate,
                'open_rate': latest_analytics.open_rate,
                'click_rate': latest_analytics.click_rate,
                'bounce_rate': latest_analytics.bounce_rate,
            }
        
        return context


class EmailTemplateListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List email templates."""
    model = EmailTemplate
    template_name = 'emails/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    required_role = 'HR'
    
    def get_queryset(self):
        return EmailTemplate.objects.filter(
            organization=self.get_organization()
        ).order_by('template_type', 'language', 'name')


class EmailTemplateDetailView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Email template detail view."""
    model = EmailTemplate
    template_name = 'emails/template_detail.html'
    context_object_name = 'template'
    required_role = 'HR'


class EmailTemplateCreateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Create email template."""
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'emails/template_form.html'
    success_message = _('Email template created successfully!')
    required_role = 'HR'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('emails:template_detail', kwargs={'pk': self.object.pk})


class EmailTemplateUpdateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Update email template."""
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'emails/template_form.html'
    success_message = _('Email template updated successfully!')
    required_role = 'HR'
    
    def get_success_url(self):
        return reverse_lazy('emails:template_detail', kwargs={'pk': self.object.pk})


class EmailMessageListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List email messages."""
    model = EmailMessage
    template_name = 'emails/message_list.html'
    context_object_name = 'messages'
    paginate_by = 50
    required_role = 'HR'
    
    def get_queryset(self):
        queryset = EmailMessage.objects.filter(
            organization=self.get_organization()
        ).select_related('template', 'user', 'created_by')
        
        # Apply filters
        status = self.request.GET.get('status')
        template_type = self.request.GET.get('template_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if template_type:
            queryset = queryset.filter(template__template_type=template_type)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = EmailAnalyticsFilterForm(self.request.GET)
        return context


class EmailMessageDetailView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Email message detail view."""
    model = EmailMessage
    template_name = 'emails/message_detail.html'
    context_object_name = 'message'
    required_role = 'HR'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get email logs
        context['logs'] = self.object.logs.order_by('-timestamp')
        
        # Get tracking data
        context['tracking_data'] = self.object.get_tracking_data()
        
        return context


class EmailCampaignListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List email campaigns."""
    model = EmailCampaign
    template_name = 'emails/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20
    required_role = 'HR'
    
    def get_queryset(self):
        return EmailCampaign.objects.filter(
            organization=self.get_organization()
        ).select_related('template').order_by('-created_at')


class EmailCampaignCreateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Create email campaign."""
    model = EmailCampaign
    form_class = EmailCampaignForm
    template_name = 'emails/campaign_form.html'
    success_message = _('Email campaign created successfully!')
    required_role = 'HR'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('emails:campaign_detail', kwargs={'pk': self.object.pk})


class EmailCampaignDetailView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Email campaign detail view."""
    model = EmailCampaign
    template_name = 'emails/campaign_detail.html'
    context_object_name = 'campaign'
    required_role = 'HR'


class BulkEmailView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Send bulk emails."""
    form_class = BulkEmailForm
    template_name = 'emails/bulk_email.html'
    required_role = 'HR'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        organization = self.get_organization()
        template = form.cleaned_data['template']
        recipient_type = form.cleaned_data['recipient_type']
        send_immediately = form.cleaned_data['send_immediately']
        scheduled_for = form.cleaned_data.get('scheduled_for')
        subject_override = form.cleaned_data.get('subject_override')
        
        # Build recipient list
        recipients = []
        
        if recipient_type == 'all_members':
            from organizations.models import Membership
            memberships = Membership.objects.filter(
                organization=organization,
                is_active=True
            ).select_related('user')
            recipients = [m.user.email for m in memberships]
        
        elif recipient_type == 'specific_roles':
            roles = form.cleaned_data['roles']
            from organizations.models import Membership
            memberships = Membership.objects.filter(
                organization=organization,
                is_active=True,
                role__in=roles
            ).select_related('user')
            recipients = [m.user.email for m in memberships]
        
        elif recipient_type == 'department':
            departments = form.cleaned_data['departments']
            from organizations.models import Employee
            employees = Employee.objects.filter(
                organization=organization,
                department__in=departments,
                is_active=True
            ).select_related('user')
            recipients = [e.user.email for e in employees]
        
        elif recipient_type == 'custom_list':
            recipients = form.cleaned_data['custom_emails']
        
        # Create campaign
        campaign = EmailCampaign.objects.create(
            organization=organization,
            name=f"Bulk Email - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            description=f"Bulk email sent to {len(recipients)} recipients",
            template=template,
            recipient_list=recipients,
            total_recipients=len(recipients),
            scheduled_for=scheduled_for if not send_immediately else None,
            send_immediately=send_immediately,
            created_by=self.request.user
        )
        
        # Start campaign
        if send_immediately:
            campaign.start_campaign()
            messages.success(
                self.request,
                _('Bulk email campaign started! {} emails are being sent.').format(len(recipients))
            )
        else:
            messages.success(
                self.request,
                _('Bulk email campaign scheduled for {}.').format(scheduled_for.strftime('%B %d, %Y at %I:%M %p'))
            )
        
        return redirect('emails:campaign_detail', pk=campaign.pk)


class EmailTestView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Test email templates."""
    form_class = EmailTestForm
    template_name = 'emails/test_email.html'
    required_role = 'HR'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        template = form.cleaned_data['template']
        test_email = form.cleaned_data['test_email']
        context_data = form.cleaned_data['context_data']
        
        # Send test email
        from .utils import send_email
        
        try:
            send_email(
                template_type=template.template_type,
                to_email=test_email,
                context_data=context_data,
                organization=self.get_organization(),
                created_by=self.request.user
            )
            
            messages.success(
                self.request,
                _('Test email sent to {}!').format(test_email)
            )
        except Exception as e:
            messages.error(
                self.request,
                _('Failed to send test email: {}').format(str(e))
            )
        
        return redirect('emails:test')


class EmailAnalyticsView(LoginRequiredMixin, OrganizationPermissionMixin, TemplateView):
    """Email analytics dashboard."""
    template_name = 'emails/analytics.html'
    required_role = 'MANAGER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Get filter parameters
        filter_form = EmailAnalyticsFilterForm(self.request.GET)
        context['filter_form'] = filter_form
        
        if filter_form.is_valid():
            date_from = filter_form.cleaned_data.get('date_from')
            date_to = filter_form.cleaned_data.get('date_to')
            template_type = filter_form.cleaned_data.get('template_type')
            status = filter_form.cleaned_data.get('status')
        else:
            # Default to last 30 days
            today = timezone.now().date()
            date_from = today - timezone.timedelta(days=30)
            date_to = today
            template_type = None
            status = None
        
        # Get email metrics
        emails = EmailMessage.objects.filter(organization=organization)
        
        if date_from:
            emails = emails.filter(created_at__date__gte=date_from)
        if date_to:
            emails = emails.filter(created_at__date__lte=date_to)
        if template_type:
            emails = emails.filter(template__template_type=template_type)
        if status:
            emails = emails.filter(status=status)
        
        # Calculate metrics
        total_emails = emails.count()
        sent_emails = emails.filter(status='SENT').count()
        delivered_emails = emails.filter(status='DELIVERED').count()
        opened_emails = emails.filter(status='OPENED').count()
        clicked_emails = emails.filter(status='CLICKED').count()
        failed_emails = emails.filter(status='FAILED').count()
        
        context['metrics'] = {
            'total_emails': total_emails,
            'sent_emails': sent_emails,
            'delivered_emails': delivered_emails,
            'opened_emails': opened_emails,
            'clicked_emails': clicked_emails,
            'failed_emails': failed_emails,
            'delivery_rate': (delivered_emails / sent_emails * 100) if sent_emails > 0 else 0,
            'open_rate': (opened_emails / delivered_emails * 100) if delivered_emails > 0 else 0,
            'click_rate': (clicked_emails / delivered_emails * 100) if delivered_emails > 0 else 0,
            'failure_rate': (failed_emails / total_emails * 100) if total_emails > 0 else 0,
        }
        
        # Template performance
        template_performance = emails.values(
            'template__name', 'template__template_type'
        ).annotate(
            total=Count('id'),
            delivered=Count('id', filter=Q(status='DELIVERED')),
            opened=Count('id', filter=Q(status='OPENED')),
            clicked=Count('id', filter=Q(status='CLICKED'))
        ).order_by('-total')[:10]
        
        context['template_performance'] = template_performance
        
        return context


class EmailPreviewView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Preview email templates."""
    form_class = EmailPreviewForm
    template_name = 'emails/preview.html'
    required_role = 'HR'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        template = form.cleaned_data['template']
        language = form.cleaned_data['language']
        sample_user = form.cleaned_data.get('sample_user')
        
        # Build context data
        context_data = {
            'user': {
                'first_name': sample_user.first_name if sample_user else 'John',
                'last_name': sample_user.last_name if sample_user else 'Doe',
                'email': sample_user.email if sample_user else 'john.doe@example.com',
                'full_name': sample_user.full_name if sample_user else 'John Doe',
            },
            'organization': {
                'name': self.get_organization().name,
                'primary_color': self.get_organization().primary_color,
            },
            'assessment': {
                'name': 'Sample Assessment',
                'url': 'https://example.com/assessment/123',
                'deadline': (timezone.now() + timezone.timedelta(days=7)).strftime('%B %d, %Y'),
            },
            'pdi_plan': {
                'title': 'Sample Development Plan',
                'url': 'https://example.com/pdi/123',
                'progress': 75,
            }
        }
        
        # Render template
        try:
            rendered_subject = template.render_subject(context_data)
            rendered_html = template.render_html_content(context_data)
            rendered_text = template.render_text_content(context_data)
            
            context = self.get_context_data(form=form)
            context.update({
                'preview_template': template,
                'rendered_subject': rendered_subject,
                'rendered_html': rendered_html,
                'rendered_text': rendered_text,
                'context_data': context_data,
            })
            
            return render(self.request, self.template_name, context)
            
        except Exception as e:
            messages.error(
                self.request,
                _('Error rendering template: {}').format(str(e))
            )
            return self.form_invalid(form)


class EmailSubscriptionView(LoginRequiredMixin, TemplateView):
    """Manage email subscriptions."""
    template_name = 'emails/subscriptions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's subscriptions for all organizations
        subscriptions = EmailSubscription.objects.filter(
            user=user
        ).select_related('organization').order_by('organization__name', 'subscription_type')
        
        context['subscriptions'] = subscriptions
        
        return context
    
    def post(self, request):
        """Update subscription preferences."""
        user = request.user
        
        # Process form data
        for key, value in request.POST.items():
            if key.startswith('subscription_'):
                try:
                    subscription_id = key.replace('subscription_', '')
                    subscription = EmailSubscription.objects.get(
                        id=subscription_id,
                        user=user
                    )
                    
                    # Update subscription status
                    is_subscribed = value == 'on'
                    if subscription.is_subscribed != is_subscribed:
                        if is_subscribed:
                            subscription.resubscribe()
                        else:
                            subscription.unsubscribe('User preference')
                
                except (EmailSubscription.DoesNotExist, ValueError):
                    continue
        
        messages.success(request, _('Email preferences updated successfully!'))
        return redirect('emails:subscriptions')


class UnsubscribeView(View):
    """Public unsubscribe page."""
    
    def get(self, request, token):
        """Show unsubscribe form."""
        # Decode token to get email and message info
        try:
            import base64
            import json
            
            decoded_data = base64.urlsafe_b64decode(token.encode()).decode()
            unsubscribe_data = json.loads(decoded_data)
            
            email = unsubscribe_data.get('email')
            message_id = unsubscribe_data.get('message_id')
            
        except Exception:
            return render(request, 'emails/unsubscribe_invalid.html')
        
        # Get email message if exists
        email_message = None
        if message_id:
            try:
                email_message = EmailMessage.objects.get(id=message_id)
            except EmailMessage.DoesNotExist:
                pass
        
        form = UnsubscribeForm()
        
        return render(request, 'emails/unsubscribe.html', {
            'form': form,
            'email': email,
            'email_message': email_message,
            'token': token,
        })
    
    def post(self, request, token):
        """Process unsubscribe request."""
        form = UnsubscribeForm(request.POST)
        
        if form.is_valid():
            # Decode token
            try:
                import base64
                import json
                
                decoded_data = base64.urlsafe_b64decode(token.encode()).decode()
                unsubscribe_data = json.loads(decoded_data)
                
                email = unsubscribe_data.get('email')
                message_id = unsubscribe_data.get('message_id')
                
            except Exception:
                return render(request, 'emails/unsubscribe_invalid.html')
            
            # Create unsubscribe request
            unsubscribe_type = form.cleaned_data['unsubscribe_type']
            reason = form.cleaned_data.get('reason', '')
            feedback = form.cleaned_data.get('feedback', '')
            
            source_email = None
            if message_id:
                try:
                    source_email = EmailMessage.objects.get(id=message_id)
                except EmailMessage.DoesNotExist:
                    pass
            
            unsubscribe_request = UnsubscribeRequest.objects.create(
                email=email,
                unsubscribe_type=unsubscribe_type,
                reason=reason,
                feedback=feedback,
                source_email=source_email,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Process immediately
            unsubscribe_request.process_unsubscribe()
            
            return render(request, 'emails/unsubscribe_success.html', {
                'email': email,
                'unsubscribe_type': unsubscribe_type,
            })
        
        # Form invalid
        try:
            import base64
            import json
            decoded_data = base64.urlsafe_b64decode(token.encode()).decode()
            unsubscribe_data = json.loads(decoded_data)
            email = unsubscribe_data.get('email')
        except Exception:
            email = None
        
        return render(request, 'emails/unsubscribe.html', {
            'form': form,
            'email': email,
            'token': token,
        })
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# AJAX Views
class EmailTemplatePreviewAPIView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """API for previewing email templates."""
    required_role = 'HR'
    
    def post(self, request):
        template_id = request.POST.get('template_id')
        context_data_json = request.POST.get('context_data', '{}')
        
        try:
            template = EmailTemplate.objects.get(
                id=template_id,
                organization=self.get_organization()
            )
            
            context_data = json.loads(context_data_json)
            
            rendered_subject = template.render_subject(context_data)
            rendered_html = template.render_html_content(context_data)
            rendered_text = template.render_text_content(context_data)
            
            return JsonResponse({
                'success': True,
                'subject': rendered_subject,
                'html_content': rendered_html,
                'text_content': rendered_text,
            })
            
        except EmailTemplate.DoesNotExist:
            return JsonResponse({'error': 'Template not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON context data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class EmailAnalyticsAPIView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """API for email analytics data."""
    required_role = 'MANAGER'
    
    def get(self, request):
        organization = self.get_organization()
        
        # Get date range
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        # Daily email metrics
        daily_metrics = []
        for i in range(days):
            date = start_date + timezone.timedelta(days=i)
            
            day_emails = EmailMessage.objects.filter(
                organization=organization,
                created_at__date=date
            )
            
            daily_metrics.append({
                'date': date.isoformat(),
                'sent': day_emails.filter(status='SENT').count(),
                'delivered': day_emails.filter(status='DELIVERED').count(),
                'opened': day_emails.filter(status='OPENED').count(),
                'clicked': day_emails.filter(status='CLICKED').count(),
                'failed': day_emails.filter(status='FAILED').count(),
            })
        
        # Template performance
        template_performance = EmailMessage.objects.filter(
            organization=organization,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values(
            'template__name', 'template__template_type'
        ).annotate(
            total=Count('id'),
            delivered=Count('id', filter=Q(status='DELIVERED')),
            opened=Count('id', filter=Q(status='OPENED')),
            clicked=Count('id', filter=Q(status='CLICKED'))
        ).order_by('-total')
        
        # Calculate rates for template performance
        template_data = []
        for perf in template_performance:
            total = perf['total']
            delivered = perf['delivered']
            
            template_data.append({
                'name': perf['template__name'] or f"Type: {perf['template__template_type']}",
                'total': total,
                'delivery_rate': (delivered / total * 100) if total > 0 else 0,
                'open_rate': (perf['opened'] / delivered * 100) if delivered > 0 else 0,
                'click_rate': (perf['clicked'] / delivered * 100) if delivered > 0 else 0,
            })
        
        return JsonResponse({
            'daily_metrics': daily_metrics,
            'template_performance': template_data,
        })


class EmailTrackingView(View):
    """Handle email tracking pixels and clicks."""
    
    def get(self, request, message_id, event_type):
        """Track email events (open, click)."""
        try:
            email_message = EmailMessage.objects.get(id=message_id)
            
            # Create log entry
            EmailLog.objects.create(
                email_message=email_message,
                event_type=event_type.upper(),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                event_data={
                    'url': request.GET.get('url', ''),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            # Update email status
            if event_type == 'open':
                email_message.mark_as_opened()
            elif event_type == 'click':
                email_message.mark_as_clicked()
                
                # Redirect to original URL if provided
                url = request.GET.get('url')
                if url:
                    return redirect(url)
            
            # Return 1x1 transparent pixel for open tracking
            if event_type == 'open':
                response = HttpResponse(
                    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B',
                    content_type='image/gif'
                )
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                return response
            
            return HttpResponse('OK')
            
        except EmailMessage.DoesNotExist:
            return HttpResponse('Not Found', status=404)
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EmailQueueView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """View email queues."""
    model = EmailQueue
    template_name = 'emails/queue_list.html'
    context_object_name = 'queues'
    required_role = 'HR'
    
    def get_queryset(self):
        return EmailQueue.objects.all().order_by('-created_at')


class EmailBlacklistView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """View email blacklist."""
    model = EmailBlacklist
    template_name = 'emails/blacklist.html'
    context_object_name = 'blacklisted_emails'
    paginate_by = 50
    required_role = 'ORG_ADMIN'
    
    def get_queryset(self):
        return EmailBlacklist.objects.filter(is_active=True).order_by('-created_at')