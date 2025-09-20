```python
"""
Forms for emails app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import EmailTemplate, EmailCampaign, EmailMessage, EmailSubscription # Removed UsageMeter from here

User = get_user_model()


class EmailTemplateForm(forms.ModelForm):
    """Form for creating/editing email templates."""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'template_type', 'language', 'subject', 'html_content',
            'text_content', 'from_email', 'from_name', 'reply_to',
            'is_active', 'is_default'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'html_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'from_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'from_name': forms.TextInput(attrs={'class': 'form-control'}),
            'reply_to': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class EmailCampaignForm(forms.ModelForm):
    """Form for creating/editing email campaigns."""
    
    recipient_emails = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label=_('Recipient Emails'),
        help_text=_('Enter email addresses separated by commas or new lines'),
        required=False
    )
    
    class Meta:
        model = EmailCampaign
        fields = [
            'name', 'description', 'template', 'scheduled_for',
            'send_immediately', 'batch_size', 'delay_between_batches'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_for': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'batch_size': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 1000}),
            'delay_between_batches': forms.NumberInput(attrs={'class': 'form-control', 'min': 10}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter templates to organization
        self.fields['template'].queryset = EmailTemplate.objects.filter(
            organization=organization,
            is_active=True
        )
        
        # Set initial recipient emails if editing
        if self.instance.pk and self.instance.recipient_list:
            self.fields['recipient_emails'].initial = '\n'.join(self.instance.recipient_list)
    
    def clean_recipient_emails(self):
        """Parse and validate recipient emails."""
        emails_text = self.cleaned_data['recipient_emails']
        if not emails_text:
            return []
        
        # Split by commas and newlines
        import re
        emails = re.split(r'[,\n\r]+', emails_text)
        
        # Clean and validate emails
        clean_emails = []
        for email in emails:
            email = email.strip()
            if email:
                # Basic email validation
                if '@' in email and '.' in email:
                    clean_emails.append(email)
                else:
                    raise forms.ValidationError(f'Invalid email address: {email}')
        
        return clean_emails
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set recipient list from parsed emails
        recipient_emails = self.cleaned_data.get('recipient_emails', [])
        instance.recipient_list = recipient_emails
        instance.total_recipients = len(recipient_emails)
        
        if commit:
            instance.save()
        return instance


class EmailMessageForm(forms.ModelForm):
    """Form for composing individual emails."""
    
    class Meta:
        model = EmailMessage
        fields = [
            'template', 'to_email', 'to_name', 'subject', 'html_content',
            'text_content', 'priority', 'scheduled_for'
        ]
        widgets = {
            'template': forms.Select(attrs={'class': 'form-select'}),
            'to_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'to_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'html_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_for': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter templates to organization
        self.fields['template'].queryset = EmailTemplate.objects.filter(
            organization=organization,
            is_active=True
        )


class EmailSubscriptionForm(forms.ModelForm):
    """Form for managing email subscriptions."""
    
    class Meta:
        model = EmailSubscription
        fields = ['subscription_type', 'is_subscribed', 'frequency']
        widgets = {
            'subscription_type': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
        }


class BulkEmailForm(forms.Form):
    """Form for sending bulk emails."""
    
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Email Template')
    )
    
    recipient_type = forms.ChoiceField(
        choices=[
            ('all_members', _('All Organization Members')),
            ('specific_roles', _('Specific Roles')),
            ('department', _('Specific Department')),
            ('custom_list', _('Custom Email List')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Recipients')
    )
    
    roles = forms.MultipleChoiceField(
        choices=[],  # Will be populated in __init__
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Roles'),
        required=False
    )
    
    departments = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Departments'),
        required=False
    )
    
    custom_emails = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label=_('Custom Email List'),
        help_text=_('Enter email addresses separated by commas or new lines'),
        required=False
    )
    
    subject_override = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Subject Override'),
        help_text=_('Leave empty to use template subject'),
        required=False
    )
    
    send_immediately = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Send Immediately'),
        initial=True,
        required=False
    )
    
    scheduled_for = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        label=_('Schedule For'),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter templates to organization
        self.fields['template'].queryset = EmailTemplate.objects.filter(
            organization=organization,
            is_active=True
        )
        
        # Set role choices
        from organizations.models import Membership
        self.fields['roles'].choices = Membership.ROLE_CHOICES
        
        # Set department queryset for company organizations
        if organization.is_company:
            from organizations.models import Department
            self.fields['departments'].queryset = Department.objects.filter(
                organization=organization,
                is_active=True
            )
        else:
            # Remove department field for non-company organizations
            del self.fields['departments']
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        send_immediately = cleaned_data.get('send_immediately')
        scheduled_for = cleaned_data.get('scheduled_for')
        
        # Validate recipient selection
        if recipient_type == 'specific_roles' and not cleaned_data.get('roles'):
            raise forms.ValidationError(_('Please select at least one role.'))
        
        if recipient_type == 'department' and not cleaned_data.get('departments'):
            raise forms.ValidationError(_('Please select at least one department.'))
        
        if recipient_type == 'custom_list' and not cleaned_data.get('custom_emails'):
            raise forms.ValidationError(_('Please provide custom email list.'))
        
        # Validate scheduling
        if not send_immediately and not scheduled_for:
            raise forms.ValidationError(_('Please provide a scheduled time or select send immediately.'))
        
        return cleaned_data
    
    def clean_custom_emails(self):
        """Parse and validate custom emails."""
        emails_text = self.cleaned_data.get('custom_emails', '')
        if not emails_text:
            return []
        
        import re
        emails = re.split(r'[,\n\r]+', emails_text)
        
        clean_emails = []
        for email in emails:
            email = email.strip()
            if email:
                if '@' in email and '.' in email:
                    clean_emails.append(email)
                else:
                    raise forms.ValidationError(f'Invalid email address: {email}')
        
        return clean_emails


class EmailTestForm(forms.Form):
    """Form for testing email templates."""
    
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Template to Test')
    )
    
    test_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label=_('Test Email Address'),
        help_text=_('Email address to send test to')
    )
    
    context_data = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        label=_('Test Context Data (JSON)'),
        help_text=_('JSON data to use for template rendering'),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter templates to organization
        self.fields['template'].queryset = EmailTemplate.objects.filter(
            organization=organization,
            is_active=True
        )
        
        # Set default context data
        self.fields['context_data'].initial = '''{
    "user": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com"
    },
    "organization": {
        "name": "Test Organization"
    },
    "assessment": {
        "name": "Big Five Personality Test",
        "url": "https://example.com/assessment/123"
    }
}'''
    
    def clean_context_data(self):
        """Validate and parse JSON context data."""
        context_text = self.cleaned_data.get('context_data', '{}')
        if not context_text.strip():
            return {}
        
        try:
            import json
            return json.loads(context_text)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Invalid JSON: {str(e)}')


class EmailAnalyticsFilterForm(forms.Form):
    """Form for filtering email analytics."""
    
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
    
    template_type = forms.ChoiceField(
        choices=[('', _('All Types'))] + EmailTemplate.TEMPLATE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + EmailMessage.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
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


class UnsubscribeForm(forms.Form):
    """Form for unsubscribe page."""
    
    unsubscribe_type = forms.ChoiceField(
        choices=[
            ('ALL', _('Unsubscribe from all emails')),
            ('MARKETING', _('Unsubscribe from marketing emails only')),
            ('NOTIFICATIONS', _('Unsubscribe from notifications only')),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Unsubscribe Options')
    )
    
    reason = forms.ChoiceField(
        choices=[
            ('TOO_FREQUENT', _('Too frequent')),
            ('NOT_RELEVANT', _('Not relevant')),
            ('NEVER_SIGNED_UP', _('Never signed up')),
            ('SPAM', _('Spam')),
            ('OTHER', _('Other')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Reason (Optional)'),
        required=False
    )
    
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label=_('Additional Feedback'),
        required=False
    )


class EmailPreviewForm(forms.Form):
    """Form for previewing email templates."""
    
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Template')
    )
    
    language = forms.ChoiceField(
        choices=EmailTemplate.LANGUAGES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Language'),
        initial='en'
    )
    
    sample_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Sample User'),
        help_text=_('User data to use for preview'),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter templates and users to organization
        self.fields['template'].queryset = EmailTemplate.objects.filter(
            organization=organization,
            is_active=True
        )
        
        from organizations.models import Membership
        user_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        self.fields['sample_user'].queryset = User.objects.filter(id__in=user_ids)


class UsageReportForm(forms.Form):
    """Form for generating usage reports."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search usage...')
        }),
        required=False
    )
    
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
    
    # Removed usage_types from here
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
        
        # Dynamically define and set choices for usage_types here
        from .models import UsageMeter # Import UsageMeter locally within __init__
        self.fields['usage_types'] = forms.MultipleChoiceField(
            choices=UsageMeter.USAGE_TYPES,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            label=_('Usage Types'),
            required=False
        )
```