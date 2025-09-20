"""
Billing models for subscription and payment management.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from core.db import BaseTenantModel

User = get_user_model()


class Plan(models.Model):
    """
    Subscription plans with configurable limits and features.
    """
    
    PLAN_TYPES = [
        ('BASIC', _('Basic')),
        ('PROFESSIONAL', _('Professional')),
        ('ENTERPRISE', _('Enterprise')),
        ('CUSTOM', _('Custom')),
    ]
    
    BILLING_CYCLES = [
        ('MONTHLY', _('Monthly')),
        ('QUARTERLY', _('Quarterly')),
        ('YEARLY', _('Yearly')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('plan name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    plan_type = models.CharField(_('plan type'), max_length=20, choices=PLAN_TYPES)
    
    # Pricing
    price_monthly = models.DecimalField(_('monthly price'), max_digits=10, decimal_places=2, default=0)
    price_quarterly = models.DecimalField(_('quarterly price'), max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(_('yearly price'), max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Usage limits
    max_assessments_per_month = models.PositiveIntegerField(_('max assessments per month'), default=10)
    max_team_members = models.PositiveIntegerField(_('max team members'), default=5)
    max_organizations = models.PositiveIntegerField(_('max organizations'), default=1)
    max_storage_gb = models.PositiveIntegerField(_('max storage (GB)'), default=1)
    
    # Features
    includes_pdi = models.BooleanField(_('includes PDI'), default=True)
    includes_recruiting = models.BooleanField(_('includes recruiting'), default=False)
    includes_advanced_reports = models.BooleanField(_('includes advanced reports'), default=False)
    includes_api_access = models.BooleanField(_('includes API access'), default=False)
    includes_white_labeling = models.BooleanField(_('includes white labeling'), default=False)
    includes_priority_support = models.BooleanField(_('includes priority support'), default=False)
    
    # Payment provider IDs
    paypal_plan_id_monthly = models.CharField(_('PayPal monthly plan ID'), max_length=100, blank=True)
    paypal_plan_id_quarterly = models.CharField(_('PayPal quarterly plan ID'), max_length=100, blank=True)
    paypal_plan_id_yearly = models.CharField(_('PayPal yearly plan ID'), max_length=100, blank=True)
    stripe_price_id_monthly = models.CharField(_('Stripe monthly price ID'), max_length=100, blank=True)
    stripe_price_id_quarterly = models.CharField(_('Stripe quarterly price ID'), max_length=100, blank=True)
    stripe_price_id_yearly = models.CharField(_('Stripe yearly price ID'), max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_public = models.BooleanField(_('public'), default=True)
    sort_order = models.PositiveIntegerField(_('sort order'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')
        ordering = ['sort_order', 'price_monthly']
    
    def __str__(self):
        return f"{self.name} ({self.get_plan_type_display()})"
    
    def get_price_for_cycle(self, billing_cycle):
        """Get price for specific billing cycle."""
        if billing_cycle == 'MONTHLY':
            return self.price_monthly
        elif billing_cycle == 'QUARTERLY':
            return self.price_quarterly
        elif billing_cycle == 'YEARLY':
            return self.price_yearly
        return self.price_monthly
    
    def get_provider_id(self, provider, billing_cycle):
        """Get provider-specific plan/price ID."""
        if provider == 'paypal':
            if billing_cycle == 'MONTHLY':
                return self.paypal_plan_id_monthly
            elif billing_cycle == 'QUARTERLY':
                return self.paypal_plan_id_quarterly
            elif billing_cycle == 'YEARLY':
                return self.paypal_plan_id_yearly
        elif provider == 'stripe':
            if billing_cycle == 'MONTHLY':
                return self.stripe_price_id_monthly
            elif billing_cycle == 'QUARTERLY':
                return self.stripe_price_id_quarterly
            elif billing_cycle == 'YEARLY':
                return self.stripe_price_id_yearly
        return None


class Subscription(BaseTenantModel):
    """
    Active subscriptions with provider integration.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', _('Active')),
        ('TRIALING', _('Trial')),
        ('PAST_DUE', _('Past Due')),
        ('CANCELLED', _('Cancelled')),
        ('UNPAID', _('Unpaid')),
        ('INCOMPLETE', _('Incomplete')),
        ('INCOMPLETE_EXPIRED', _('Incomplete Expired')),
        ('PAUSED', _('Paused')),
    ]
    
    PROVIDERS = [
        ('paypal', _('PayPal')),
        ('stripe', _('Stripe')),
        ('manual', _('Manual')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    billing_cycle = models.CharField(_('billing cycle'), max_length=20, choices=Plan.BILLING_CYCLES)
    
    # Provider integration
    provider = models.CharField(_('payment provider'), max_length=20, choices=PROVIDERS)
    provider_subscription_id = models.CharField(_('provider subscription ID'), max_length=200, blank=True)
    provider_customer_id = models.CharField(_('provider customer ID'), max_length=200, blank=True)
    
    # Subscription details
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    current_period_start = models.DateTimeField(_('current period start'))
    current_period_end = models.DateTimeField(_('current period end'))
    
    # Trial
    trial_start = models.DateTimeField(_('trial start'), null=True, blank=True)
    trial_end = models.DateTimeField(_('trial end'), null=True, blank=True)
    
    # Pricing
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Cancellation
    cancel_at_period_end = models.BooleanField(_('cancel at period end'), default=False)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    cancellation_reason = models.TextField(_('cancellation reason'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.organization.name} - {self.plan.name} ({self.status})"
    
    def get_absolute_url(self):
        return reverse('billing:subscription_detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        return self.status in ['ACTIVE', 'TRIALING']
    
    @property
    def is_trial(self):
        return self.status == 'TRIALING'
    
    @property
    def days_until_renewal(self):
        if not self.current_period_end:
            return 0
        delta = self.current_period_end.date() - timezone.now().date()
        return max(0, delta.days)
    
    @property
    def is_past_due(self):
        return self.status == 'PAST_DUE'
    
    def cancel(self, reason='', at_period_end=True):
        """Cancel subscription."""
        self.cancel_at_period_end = at_period_end
        self.cancellation_reason = reason
        if not at_period_end:
            self.status = 'CANCELLED'
            self.cancelled_at = timezone.now()
        self.save()
    
    def renew(self, next_period_end):
        """Renew subscription for next period."""
        self.current_period_start = self.current_period_end
        self.current_period_end = next_period_end
        self.status = 'ACTIVE'
        self.save()


class UsageMeter(BaseTenantModel):
    """
    Real-time usage tracking per billing cycle.
    """
    
    USAGE_TYPES = [
        ('ASSESSMENTS', _('Assessments')),
        ('TEAM_MEMBERS', _('Team Members')),
        ('STORAGE', _('Storage')),
        ('API_CALLS', _('API Calls')),
        ('REPORTS', _('Reports')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usage_meters')
    usage_type = models.CharField(_('usage type'), max_length=20, choices=USAGE_TYPES)
    
    # Usage tracking
    current_usage = models.PositiveIntegerField(_('current usage'), default=0)
    limit = models.PositiveIntegerField(_('limit'), default=0)
    
    # Billing period
    period_start = models.DateTimeField(_('period start'))
    period_end = models.DateTimeField(_('period end'))
    
    # Overage handling
    overage_allowed = models.BooleanField(_('overage allowed'), default=False)
    overage_rate = models.DecimalField(_('overage rate'), max_digits=10, decimal_places=2, default=0)
    overage_usage = models.PositiveIntegerField(_('overage usage'), default=0)
    overage_cost = models.DecimalField(_('overage cost'), max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Usage Meter')
        verbose_name_plural = _('Usage Meters')
        unique_together = ['subscription', 'usage_type', 'period_start']
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_usage_type_display()} ({self.current_usage}/{self.limit})"
    
    @property
    def usage_percentage(self):
        if self.limit == 0:
            return 0
        return min(100, (self.current_usage / self.limit) * 100)
    
    @property
    def is_over_limit(self):
        return self.current_usage > self.limit
    
    @property
    def remaining_usage(self):
        return max(0, self.limit - self.current_usage)
    
    def increment_usage(self, amount=1):
        """Increment usage and calculate overage if applicable."""
        old_usage = self.current_usage
        self.current_usage += amount
        
        # Calculate overage
        if self.current_usage > self.limit:
            new_overage = self.current_usage - self.limit
            old_overage = max(0, old_usage - self.limit)
            overage_increase = new_overage - old_overage
            
            if overage_increase > 0:
                self.overage_usage += overage_increase
                self.overage_cost += overage_increase * self.overage_rate
        
        self.save()
        return self.current_usage
    
    def reset_for_new_period(self, period_start, period_end):
        """Reset usage for new billing period."""
        self.current_usage = 0
        self.overage_usage = 0
        self.overage_cost = 0
        self.period_start = period_start
        self.period_end = period_end
        self.save()


class Invoice(BaseTenantModel):
    """
    Generated invoices for subscriptions and usage.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('OPEN', _('Open')),
        ('PAID', _('Paid')),
        ('PAST_DUE', _('Past Due')),
        ('CANCELLED', _('Cancelled')),
        ('UNCOLLECTIBLE', _('Uncollectible')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice details
    invoice_number = models.CharField(_('invoice number'), max_length=50, unique=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Amounts
    subtotal = models.DecimalField(_('subtotal'), max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_('tax amount'), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Billing period
    period_start = models.DateTimeField(_('period start'))
    period_end = models.DateTimeField(_('period end'))
    
    # Payment details
    due_date = models.DateTimeField(_('due date'))
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    payment_method = models.CharField(_('payment method'), max_length=50, blank=True)
    
    # Provider integration
    provider = models.CharField(_('provider'), max_length=20, choices=Subscription.PROVIDERS, blank=True)
    provider_invoice_id = models.CharField(_('provider invoice ID'), max_length=200, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.organization.name}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not provided
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        super().save(*args, **kwargs)
    
    def _generate_invoice_number(self):
        """Generate unique invoice number."""
        import datetime
        today = datetime.date.today()
        prefix = f"INV-{today.year}{today.month:02d}"
        
        # Find last invoice for this month
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            try:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"{prefix}-{next_number:04d}"
    
    @property
    def is_paid(self):
        return self.status == 'PAID'
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now() and not self.is_paid
    
    def mark_as_paid(self, payment_method=''):
        """Mark invoice as paid."""
        self.status = 'PAID'
        self.paid_at = timezone.now()
        self.payment_method = payment_method
        self.save()


class InvoiceItem(models.Model):
    """
    Individual line items on invoices.
    """
    
    ITEM_TYPES = [
        ('SUBSCRIPTION', _('Subscription')),
        ('OVERAGE', _('Overage')),
        ('ONE_TIME', _('One-time')),
        ('DISCOUNT', _('Discount')),
        ('TAX', _('Tax')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    
    # Item details
    item_type = models.CharField(_('item type'), max_length=20, choices=ITEM_TYPES)
    description = models.CharField(_('description'), max_length=500)
    quantity = models.DecimalField(_('quantity'), max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(_('unit price'), max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(_('total price'), max_digits=10, decimal_places=2, default=0)
    
    # Usage meter reference
    usage_meter = models.ForeignKey(UsageMeter, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Invoice Item')
        verbose_name_plural = _('Invoice Items')
        ordering = ['item_type', 'description']
    
    def __str__(self):
        return f"{self.description} - {self.total_price} {self.invoice.currency}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class PaymentMethod(BaseTenantModel):
    """
    Stored payment methods for organizations.
    """
    
    METHOD_TYPES = [
        ('CREDIT_CARD', _('Credit Card')),
        ('DEBIT_CARD', _('Debit Card')),
        ('BANK_ACCOUNT', _('Bank Account')),
        ('PAYPAL', _('PayPal')),
        ('OTHER', _('Other')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Method details
    method_type = models.CharField(_('method type'), max_length=20, choices=METHOD_TYPES)
    is_default = models.BooleanField(_('default method'), default=False)
    
    # Provider details
    provider = models.CharField(_('provider'), max_length=20, choices=Subscription.PROVIDERS)
    provider_payment_method_id = models.CharField(_('provider payment method ID'), max_length=200)
    
    # Card details (masked for security)
    card_last_four = models.CharField(_('card last four digits'), max_length=4, blank=True)
    card_brand = models.CharField(_('card brand'), max_length=20, blank=True)
    card_exp_month = models.PositiveIntegerField(_('card expiry month'), null=True, blank=True)
    card_exp_year = models.PositiveIntegerField(_('card expiry year'), null=True, blank=True)
    
    # Bank details (masked)
    bank_name = models.CharField(_('bank name'), max_length=100, blank=True)
    account_last_four = models.CharField(_('account last four digits'), max_length=4, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.method_type in ['CREDIT_CARD', 'DEBIT_CARD'] and self.card_last_four:
            return f"{self.get_method_type_display()} ****{self.card_last_four}"
        elif self.method_type == 'BANK_ACCOUNT' and self.account_last_four:
            return f"{self.bank_name} ****{self.account_last_four}"
        else:
            return self.get_method_type_display()
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per organization
        if self.is_default:
            PaymentMethod.objects.filter(
                organization=self.organization,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)


class Payment(BaseTenantModel):
    """
    Payment records for invoices.
    """
    
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('SUCCEEDED', _('Succeeded')),
        ('FAILED', _('Failed')),
        ('CANCELLED', _('Cancelled')),
        ('REFUNDED', _('Refunded')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Provider integration
    provider = models.CharField(_('provider'), max_length=20, choices=Subscription.PROVIDERS)
    provider_payment_id = models.CharField(_('provider payment ID'), max_length=200, blank=True)
    provider_charge_id = models.CharField(_('provider charge ID'), max_length=200, blank=True)
    
    # Transaction details
    description = models.CharField(_('description'), max_length=500, blank=True)
    failure_reason = models.CharField(_('failure reason'), max_length=500, blank=True)
    
    # Refund details
    refunded_amount = models.DecimalField(_('refunded amount'), max_digits=10, decimal_places=2, default=0)
    refund_reason = models.CharField(_('refund reason'), max_length=500, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.amount} {self.currency} - {self.status}"
    
    @property
    def is_successful(self):
        return self.status == 'SUCCEEDED'
    
    @property
    def is_refundable(self):
        return self.status == 'SUCCEEDED' and self.refunded_amount < self.amount


class WebhookEvent(models.Model):
    """
    Webhook events from payment providers.
    """
    
    PROVIDERS = [
        ('paypal', _('PayPal')),
        ('stripe', _('Stripe')),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('PROCESSED', _('Processed')),
        ('FAILED', _('Failed')),
        ('IGNORED', _('Ignored')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event details
    provider = models.CharField(_('provider'), max_length=20, choices=PROVIDERS)
    event_type = models.CharField(_('event type'), max_length=100)
    provider_event_id = models.CharField(_('provider event ID'), max_length=200, unique=True)
    
    # Processing
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    retry_count = models.PositiveIntegerField(_('retry count'), default=0)
    
    # Data
    raw_data = models.JSONField(_('raw webhook data'), default=dict)
    processed_data = models.JSONField(_('processed data'), default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Webhook Event')
        verbose_name_plural = _('Webhook Events')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} ({self.status})"
    
    def mark_as_processed(self, processed_data=None):
        """Mark webhook as successfully processed."""
        self.status = 'PROCESSED'
        self.processed_at = timezone.now()
        if processed_data:
            self.processed_data = processed_data
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark webhook as failed with error message."""
        self.status = 'FAILED'
        self.error_message = error_message
        self.retry_count += 1
        self.save()


class BillingAddress(BaseTenantModel):
    """
    Billing addresses for organizations.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Address details
    company_name = models.CharField(_('company name'), max_length=200, blank=True)
    address_line1 = models.CharField(_('address line 1'), max_length=200)
    address_line2 = models.CharField(_('address line 2'), max_length=200, blank=True)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state/province'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=100)
    
    # Tax information
    tax_id = models.CharField(_('tax ID'), max_length=50, blank=True)
    vat_number = models.CharField(_('VAT number'), max_length=50, blank=True)
    
    # Status
    is_default = models.BooleanField(_('default address'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Billing Address')
        verbose_name_plural = _('Billing Addresses')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.organization.name} - {self.city}, {self.state}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per organization
        if self.is_default:
            BillingAddress.objects.filter(
                organization=self.organization,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)


class Coupon(models.Model):
    """
    Discount coupons and promotional codes.
    """
    
    DISCOUNT_TYPES = [
        ('PERCENTAGE', _('Percentage')),
        ('FIXED_AMOUNT', _('Fixed Amount')),
        ('FREE_TRIAL', _('Free Trial Extension')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(_('coupon code'), max_length=50, unique=True)
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Discount details
    discount_type = models.CharField(_('discount type'), max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(_('discount value'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Validity
    valid_from = models.DateTimeField(_('valid from'))
    valid_until = models.DateTimeField(_('valid until'), null=True, blank=True)
    max_uses = models.PositiveIntegerField(_('max uses'), null=True, blank=True)
    uses_count = models.PositiveIntegerField(_('uses count'), default=0)
    
    # Restrictions
    min_amount = models.DecimalField(_('minimum amount'), max_digits=10, decimal_places=2, null=True, blank=True)
    applicable_plans = models.ManyToManyField(Plan, blank=True, related_name='applicable_coupons')
    first_time_customers_only = models.BooleanField(_('first-time customers only'), default=False)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Coupon')
        verbose_name_plural = _('Coupons')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        return True
    
    def can_be_used_by(self, organization, amount=None):
        """Check if coupon can be used by organization."""
        if not self.is_valid:
            return False
        
        # Check minimum amount
        if self.min_amount and amount and amount < self.min_amount:
            return False
        
        # Check first-time customer restriction
        if self.first_time_customers_only:
            has_previous_subscription = Subscription.objects.filter(
                organization=organization
            ).exists()
            if has_previous_subscription:
                return False
        
        return True
    
    def apply_discount(self, amount):
        """Calculate discounted amount."""
        if self.discount_type == 'PERCENTAGE':
            discount = amount * (self.discount_value / 100)
        elif self.discount_type == 'FIXED_AMOUNT':
            discount = min(self.discount_value, amount)
        else:
            discount = 0
        
        return max(0, amount - discount)
    
    def use_coupon(self):
        """Increment usage count."""
        self.uses_count += 1
        self.save(update_fields=['uses_count'])


class CouponUsage(BaseTenantModel):
    """
    Track coupon usage by organizations.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='coupon_usages')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True, related_name='coupon_usages')
    
    # Usage details
    original_amount = models.DecimalField(_('original amount'), max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(_('discount amount'), max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(_('final amount'), max_digits=10, decimal_places=2)
    
    # Metadata
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Coupon Usage')
        verbose_name_plural = _('Coupon Usages')
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.coupon.code} used by {self.organization.name}"


class BillingNotification(BaseTenantModel):
    """
    Billing-related notifications and alerts.
    """
    
    NOTIFICATION_TYPES = [
        ('PAYMENT_SUCCESS', _('Payment Successful')),
        ('PAYMENT_FAILED', _('Payment Failed')),
        ('INVOICE_CREATED', _('Invoice Created')),
        ('SUBSCRIPTION_RENEWED', _('Subscription Renewed')),
        ('SUBSCRIPTION_CANCELLED', _('Subscription Cancelled')),
        ('TRIAL_ENDING', _('Trial Ending')),
        ('USAGE_LIMIT_REACHED', _('Usage Limit Reached')),
        ('OVERAGE_ALERT', _('Overage Alert')),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('SENT', _('Sent')),
        ('FAILED', _('Failed')),
        ('IGNORED', _('Ignored')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Notification details
    notification_type = models.CharField(_('notification type'), max_length=30, choices=NOTIFICATION_TYPES)
    recipient_email = models.EmailField(_('recipient email'))
    subject = models.CharField(_('subject'), max_length=200)
    message = models.TextField(_('message'))
    
    # Related objects
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Delivery
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    scheduled_for = models.DateTimeField(_('scheduled for'), default=timezone.now)
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Billing Notification')
        verbose_name_plural = _('Billing Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} to {self.recipient_email}"
    
    def mark_as_sent(self):
        """Mark notification as sent."""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark notification as failed."""
        self.status = 'FAILED'
        self.error_message = error_message
        self.save()