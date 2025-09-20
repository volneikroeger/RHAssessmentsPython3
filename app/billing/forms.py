from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal

# Import UsageMeter at the top (or before usage) to avoid circular import
from .utils import UsageMeter

User = get_user_model()


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


# The rest of your form classes follow...

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date range (last 30 days)
        from django.utils import timezone
        today = timezone.now().date()
        thirty_days_ago = today - timezone.timedelta(days=30)
        
        self.fields['date_from'].initial = thirty_days_ago
        self.fields['date_to'].initial = today
        
        # Dynamically define usage_types field to avoid circular import issues
        self.fields['usage_types'] = forms.MultipleChoiceField(
            choices=UsageMeter.USAGE_TYPES,  # Now this will work with the import above
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            label=_('Usage Types'),
            required=False
        )

# And other forms remain the same
