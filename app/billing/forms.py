"""
Forms for billing app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Plan, Subscription, BillingAddress, PaymentMethod, Coupon

User = get_user_model()


class PlanSelectionForm(forms.Form):
    """Form for selecting a subscription plan."""
    
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True, is_public=True),
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Select Plan'),
        empty_label=None
    )
    
    billing_cycle = forms.ChoiceField(
        choices=Plan.BILLING_CYCLES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Billing Cycle'),
        initial='MONTHLY'
    )
    
    coupon_code = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter coupon code')}),
        label=_('Coupon Code'),
        required=False
    )
    
    def __init__(self, organization=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        
        # Filter plans based on organization type
        if organization:
            if organization.is_company:
                # Companies need PDI features
                self.fields['plan'].queryset = Plan.objects.filter(
                    is_active=True,
                    is_public=True,
                    includes_pdi=True
                )
            elif organization.is_recruiter:
                # Recruiters need recruiting features
                self.fields['plan'].queryset = Plan.objects.filter(
                    is_active=True,
                    is_public=True,
                    includes_recruiting=True
                )
    
    def clean_coupon_code(self):
        """Validate coupon code."""
        code = self.cleaned_data.get('coupon_code')
        if code:
            try:
                coupon = Coupon.objects.get(code=code.upper())
                if not coupon.can_be_used_by(self.organization):
                    raise forms.ValidationError(_('This coupon is not valid or has expired.'))
                return coupon
            except Coupon.DoesNotExist:
                raise forms.ValidationError(_('Invalid coupon code.'))
        return None


class BillingAddressForm(forms.ModelForm):
    """Form for billing address."""
    
    class Meta:
        model = BillingAddress
        fields = [
            'company_name', 'address_line1', 'address_line2', 'city',
            'state', 'postal_code', 'country', 'tax_id', 'vat_number'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PaymentMethodForm(forms.ModelForm):
    """Form for adding payment methods."""
    
    class Meta:
        model = PaymentMethod
        fields = ['method_type', 'is_default']
        widgets = {
            'method_type': forms.Select(attrs={'class': 'form-select'}),
        }


class SubscriptionUpdateForm(forms.ModelForm):
    """Form for updating subscription details."""
    
    class Meta:
        model = Subscription
        fields = ['plan', 'billing_cycle']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter plans based on organization type
        if organization.is_company:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                includes_pdi=True
            )
        elif organization.is_recruiter:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                includes_recruiting=True
            )


class CouponForm(forms.ModelForm):
    """Form for creating/editing coupons."""
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'name', 'description', 'discount_type', 'discount_value',
            'currency', 'valid_from', 'valid_until', 'max_uses',
            'min_amount', 'applicable_plans', 'first_time_customers_only', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform: uppercase;'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'applicable_plans': forms.CheckboxSelectMultiple(),
        }
    
    def clean_code(self):
        """Ensure coupon code is uppercase and unique."""
        code = self.cleaned_data['code'].upper()
        
        # Check for existing coupon (excluding current instance if editing)
        existing = Coupon.objects.filter(code=code)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError(_('A coupon with this code already exists.'))
        
        return code


class UsageReportForm(forms.Form):
    """Form for generating usage reports."""
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_('From Date')
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_('To Date')
    )
    
    usage_types = forms.MultipleChoiceField(
        choices=[],  # Will be set in __init__
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Usage Types'),
        required=False
    )
    
    include_overages = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Include Overage Details'),
        required=False,
        initial=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import UsageMeter here to avoid circular import issues
        from .models import UsageMeter
        
        # Set choices dynamically
        self.fields['usage_types'].choices = UsageMeter.USAGE_TYPES
        
        # Set default date range (last 30 days)
        from django.utils import timezone
        today = timezone.now().date()
        thirty_days_ago = today - timezone.timedelta(days=30)
        
        self.fields['date_from'].initial = thirty_days_ago
        self.fields['date_to'].initial = today


class BillingSearchForm(forms.Form):
    """Form for searching billing records."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search invoices, subscriptions...')
        }),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + Subscription.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    provider = forms.ChoiceField(
        choices=[('', _('All Providers'))] + Subscription.PROVIDERS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label=_('All Plans')
    )


class CancelSubscriptionForm(forms.Form):
    """Form for cancelling subscriptions."""
    
    CANCELLATION_REASONS = [
        ('TOO_EXPENSIVE', _('Too expensive')),
        ('NOT_USING', _('Not using the service')),
        ('MISSING_FEATURES', _('Missing features')),
        ('POOR_SUPPORT', _('Poor customer support')),
        ('SWITCHING_PROVIDER', _('Switching to another provider')),
        ('BUSINESS_CLOSURE', _('Business closure')),
        ('OTHER', _('Other')),
    ]
    
    reason = forms.ChoiceField(
        choices=CANCELLATION_REASONS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Reason for Cancellation')
    )
    
    cancel_immediately = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Cancel immediately (forfeit remaining period)'),
        required=False,
        help_text=_('If unchecked, subscription will cancel at the end of current billing period.')
    )
    
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label=_('Additional Feedback'),
        required=False,
        help_text=_('Help us improve by sharing your feedback.')
    )
    
    confirm_cancellation = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('I understand that cancelling will stop all billing and may limit access to features.'),
        required=True
    )


class PaymentRetryForm(forms.Form):
    """Form for retrying failed payments."""
    
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Payment Method'),
        help_text=_('Select the payment method to use for retry.')
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
            organization=organization,
            is_active=True
        )