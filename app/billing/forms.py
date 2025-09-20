"""
Forms for billing app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.apps import apps # Importar apps para acesso seguro ao modelo

# Não importe UsageMeter diretamente aqui no topo,
# pois isso causa o problema de carregamento antecipado.
# from .models import UsageMeter

User = get_user_model()

# Função auxiliar para obter as choices dinamicamente
# Esta função só será chamada quando o formulário for instanciado,
# garantindo que o App Registry do Django já esteja carregado.
def get_usage_meter_choices():
    # Acessa o modelo de forma segura através do App Registry
    UsageMeter = apps.get_model('billing', 'UsageMeter')
    return UsageMeter.USAGE_TYPES


class PlanSelectionForm(forms.Form):
    """Form for selecting subscription plan."""
    
    plan = forms.ModelChoiceField(
        queryset=None,  # Will be set in view
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Select Plan'),
        empty_label=None
    )
    
    billing_cycle = forms.ChoiceField(
        choices=[
            ('MONTHLY', _('Monthly')),
            ('QUARTERLY', _('Quarterly')),
            ('YEARLY', _('Yearly')),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Billing Cycle'),
        initial='MONTHLY'
    )
    
    coupon_code = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter coupon code')}),
        label=_('Coupon Code'),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import Plan model locally to avoid circular imports
        from .models import Plan
        
        # Filter plans based on organization type
        if organization.is_company:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_pdi=True
            ).order_by('sort_order', 'price_monthly')
        elif organization.is_recruiter:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_recruiting=True
            ).order_by('sort_order', 'price_monthly')
        else:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                is_public=True
            ).order_by('sort_order', 'price_monthly')
    
    def clean_coupon_code(self):
        """Validate coupon code if provided."""
        code = self.cleaned_data.get('coupon_code', '').strip().upper()
        if not code:
            return None
        
        # Import Coupon model locally
        from .models import Coupon
        
        try:
            coupon = Coupon.objects.get(code=code)
            if not coupon.is_valid:
                raise forms.ValidationError(_('This coupon is not valid or has expired.'))
            return coupon
        except Coupon.DoesNotExist:
            raise forms.ValidationError(_('Invalid coupon code.'))


class BillingAddressForm(forms.ModelForm):
    """Form for billing address."""
    
    class Meta:
        # Import model locally to avoid circular imports
        from .models import BillingAddress
        model = BillingAddress
        fields = [
            'company_name', 'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'tax_id', 'vat_number'
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
    """Form for payment method."""
    
    class Meta:
        # Import model locally to avoid circular imports
        from .models import PaymentMethod
        model = PaymentMethod
        fields = ['method_type', 'is_default']
        widgets = {
            'method_type': forms.Select(attrs={'class': 'form-select'}),
        }


class SubscriptionUpdateForm(forms.ModelForm):
    """Form for updating subscription."""
    
    class Meta:
        # Import model locally to avoid circular imports
        from .models import Subscription
        model = Subscription
        fields = ['plan', 'billing_cycle']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import Plan model locally
        from .models import Plan
        
        # Filter plans based on organization type
        if organization.is_company:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_pdi=True
            ).order_by('sort_order', 'price_monthly')
        elif organization.is_recruiter:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                is_public=True,
                includes_recruiting=True
            ).order_by('sort_order', 'price_monthly')


class CouponForm(forms.ModelForm):
    """Form for creating/editing coupons."""
    
    class Meta:
        # Import model locally to avoid circular imports
        from .models import Coupon
        model = Coupon
        fields = [
            'code', 'name', 'description', 'discount_type', 'discount_value',
            'currency', 'valid_from', 'valid_until', 'max_uses', 'min_amount',
            'applicable_plans', 'first_time_customers_only', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'applicable_plans': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }


class UsageReportForm(forms.Form):
    """Form for generating usage reports."""
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_('From Date'),
        required=False
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_('To Date'),
        required=False
    )
    
    include_overages = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Include Overage Details'),
        required=False,
        initial=True
    )
    
    # Pass the callable to choices
    usage_types = forms.MultipleChoiceField(
        choices=get_usage_meter_choices, # <--- THIS IS THE KEY CHANGE
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Usage Types'),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date range (last 30 days)
        from django.utils import timezone
        today = timezone.now().date()
        thirty_days_ago = today - timezone.timedelta(days=30)
        
        self.fields['date_from'].initial = thirty_days_ago
        self.fields['date_to'].initial = today
        
        # No need to set choices here anymore, as it's handled by the callable


class BillingSearchForm(forms.Form):
    """Form for searching and filtering billing records."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search invoices, plans...')
        }),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    provider = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    plan = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label=_('All Plans')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import models locally to avoid circular imports
        from .models import Invoice, Subscription, Plan
        
        # Set status choices
        self.fields['status'].choices = [('', _('All Statuses'))] + Invoice.STATUS_CHOICES
        
        # Set provider choices
        self.fields['provider'].choices = [('', _('All Providers'))] + Subscription.PROVIDERS
        
        # Set plan queryset
        self.fields['plan'].queryset = Plan.objects.filter(is_active=True)


class CancelSubscriptionForm(forms.Form):
    """Form for cancelling subscription."""
    
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
        label=_('Cancel Immediately'),
        help_text=_('Cancel now instead of at the end of the billing period'),
        required=False
    )
    
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label=_('Additional Feedback'),
        help_text=_('Help us improve by sharing your feedback'),
        required=False
    )


class PaymentRetryForm(forms.Form):
    """Form for retrying failed payments."""
    
    payment_method = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Payment Method'),
        help_text=_('Choose payment method for retry')
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import PaymentMethod model locally
        from .models import PaymentMethod
        
        # Filter payment methods to organization
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('-is_default', '-created_at')
