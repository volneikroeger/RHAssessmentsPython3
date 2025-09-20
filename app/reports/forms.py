"""
Forms for reports app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Report, ReportTemplate, ReportSchedule, Dashboard, ReportSubscription

User = get_user_model()


class ReportGenerationForm(forms.ModelForm):
    """Form for generating custom reports."""
    
    class Meta:
        model = Report
        fields = ['title', 'description', 'report_type', 'format', 'date_from', 'date_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'date_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    # Additional filter fields
    include_assessments = forms.BooleanField(
        label=_('Include Assessment Data'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_pdi = forms.BooleanField(
        label=_('Include PDI Data'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_recruiting = forms.BooleanField(
        label=_('Include Recruiting Data'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    departments = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Departments'),
        required=False
    )
    
    users = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Specific Users'),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date range (last 30 days)
        today = timezone.now().date()
        thirty_days_ago = today - timezone.timedelta(days=30)
        
        self.fields['date_from'].initial = thirty_days_ago
        self.fields['date_to'].initial = today
        
        # Filter departments and users to organization
        if organization.is_company:
            from organizations.models import Department, Membership
            
            self.fields['departments'].queryset = Department.objects.filter(
                organization=organization,
                is_active=True
            )
            
            user_ids = Membership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            
            self.fields['users'].queryset = User.objects.filter(id__in=user_ids)
        else:
            # For recruiter organizations, remove department field
            del self.fields['departments']
            
            from organizations.models import Membership
            user_ids = Membership.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            
            self.fields['users'].queryset = User.objects.filter(id__in=user_ids)
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_('Start date must be before end date.'))
        
        return cleaned_data


class ReportTemplateForm(forms.ModelForm):
    """Form for creating/editing report templates."""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'description', 'report_type', 'is_public', 'auto_generate',
            'generation_frequency', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'generation_frequency': forms.Select(attrs={'class': 'form-select'}),
        }


class ReportScheduleForm(forms.ModelForm):
    """Form for scheduling reports."""
    
    class Meta:
        model = ReportSchedule
        fields = [
            'name', 'template', 'frequency', 'day_of_week', 'day_of_month',
            'time_of_day', 'recipients', 'send_to_organization_admins', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 6}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'time_of_day': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'recipients': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter templates and recipients to organization
        self.fields['template'].queryset = ReportTemplate.objects.filter(
            organization=organization,
            is_active=True
        )
        
        from organizations.models import Membership
        user_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        self.fields['recipients'].queryset = User.objects.filter(id__in=user_ids)


class DashboardForm(forms.ModelForm):
    """Form for creating/editing dashboards."""
    
    class Meta:
        model = Dashboard
        fields = [
            'name', 'description', 'refresh_interval', 'is_public',
            'allowed_roles', 'is_active', 'is_default'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'refresh_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'allowed_roles': forms.CheckboxSelectMultiple(),
        }


class ReportFilterForm(forms.Form):
    """Form for filtering reports list."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search reports...')
        }),
        required=False
    )
    
    report_type = forms.ChoiceField(
        choices=[('', _('All Types'))] + Report.REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + Report.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    format = forms.ChoiceField(
        choices=[('', _('All Formats'))] + Report.FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    generated_by = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label=_('All Users')
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter users to organization members
        from organizations.models import Membership
        user_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        self.fields['generated_by'].queryset = User.objects.filter(id__in=user_ids)


class ReportShareForm(forms.Form):
    """Form for sharing reports with users."""
    
    users = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Share with Users'),
        help_text=_('Select users to share this report with.')
    )
    
    make_public = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Make Public'),
        help_text=_('Make this report visible to all organization members.'),
        required=False
    )
    
    expires_in_days = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 365}),
        label=_('Expires in (days)'),
        initial=30,
        help_text=_('Number of days until shared access expires.'),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter users to organization members
        from organizations.models import Membership
        user_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        self.fields['users'].queryset = User.objects.filter(id__in=user_ids)


class QuickReportForm(forms.Form):
    """Form for generating quick reports with predefined options."""
    
    QUICK_REPORT_TYPES = [
        ('assessment_completion', _('Assessment Completion Rates')),
        ('team_performance', _('Team Performance Overview')),
        ('pdi_progress', _('PDI Progress Summary')),
        ('user_engagement', _('User Engagement Metrics')),
        ('monthly_summary', _('Monthly Activity Summary')),
    ]
    
    report_type = forms.ChoiceField(
        choices=QUICK_REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Report Type')
    )
    
    period = forms.ChoiceField(
        choices=[
            ('7', _('Last 7 days')),
            ('30', _('Last 30 days')),
            ('90', _('Last 90 days')),
            ('365', _('Last year')),
            ('custom', _('Custom period')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Time Period'),
        initial='30'
    )
    
    custom_date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_('Custom Start Date'),
        required=False
    )
    
    custom_date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_('Custom End Date'),
        required=False
    )
    
    format = forms.ChoiceField(
        choices=[
            ('HTML', _('View Online')),
            ('PDF', _('Download PDF')),
            ('EXCEL', _('Download Excel')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Output Format'),
        initial='HTML'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        custom_date_from = cleaned_data.get('custom_date_from')
        custom_date_to = cleaned_data.get('custom_date_to')
        
        if period == 'custom':
            if not custom_date_from or not custom_date_to:
                raise forms.ValidationError(_('Custom period requires both start and end dates.'))
            
            if custom_date_from > custom_date_to:
                raise forms.ValidationError(_('Start date must be before end date.'))
        
        return cleaned_data


class ReportExportForm(forms.Form):
    """Form for exporting reports in different formats."""
    
    format = forms.ChoiceField(
        choices=Report.FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Export Format')
    )
    
    include_charts = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Include Charts'),
        initial=True,
        required=False
    )
    
    include_raw_data = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Include Raw Data'),
        initial=False,
        required=False
    )
    
    compress_file = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Compress File (ZIP)'),
        initial=False,
        required=False
    )


class AnalyticsFilterForm(forms.Form):
    """Form for filtering analytics data."""
    
    metric_type = forms.ChoiceField(
        choices=[
            ('', _('All Metrics')),
            ('assessments', _('Assessment Metrics')),
            ('pdi', _('PDI Metrics')),
            ('recruiting', _('Recruiting Metrics')),
            ('users', _('User Metrics')),
            ('usage', _('Usage Metrics')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    time_range = forms.ChoiceField(
        choices=[
            ('7d', _('Last 7 days')),
            ('30d', _('Last 30 days')),
            ('90d', _('Last 90 days')),
            ('6m', _('Last 6 months')),
            ('1y', _('Last year')),
            ('all', _('All time')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='30d'
    )
    
    granularity = forms.ChoiceField(
        choices=[
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
            ('monthly', _('Monthly')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='daily'
    )
    
    compare_previous = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Compare with Previous Period'),
        required=False
    )


class BenchmarkComparisonForm(forms.Form):
    """Form for benchmark comparison reports."""
    
    comparison_type = forms.ChoiceField(
        choices=[
            ('industry', _('Industry Benchmarks')),
            ('size', _('Company Size Benchmarks')),
            ('internal', _('Internal Historical Comparison')),
            ('custom', _('Custom Comparison')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Comparison Type')
    )
    
    industry = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Industry'),
        required=False,
        help_text=_('Required for industry benchmarks')
    )
    
    company_size = forms.ChoiceField(
        choices=[
            ('small', _('Small (1-50 employees)')),
            ('medium', _('Medium (51-200 employees)')),
            ('large', _('Large (201-1000 employees)')),
            ('enterprise', _('Enterprise (1000+ employees)')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Company Size'),
        required=False
    )
    
    metrics_to_compare = forms.MultipleChoiceField(
        choices=[
            ('assessment_completion_rate', _('Assessment Completion Rate')),
            ('avg_assessment_scores', _('Average Assessment Scores')),
            ('pdi_completion_rate', _('PDI Completion Rate')),
            ('user_engagement', _('User Engagement')),
            ('time_to_complete_assessments', _('Time to Complete Assessments')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Metrics to Compare')
    )
    
    def clean(self):
        cleaned_data = super().clean()
        comparison_type = cleaned_data.get('comparison_type')
        industry = cleaned_data.get('industry')
        company_size = cleaned_data.get('company_size')
        
        if comparison_type == 'industry' and not industry:
            raise forms.ValidationError(_('Industry is required for industry benchmarks.'))
        
        if comparison_type == 'size' and not company_size:
            raise forms.ValidationError(_('Company size is required for size benchmarks.'))
        
        return cleaned_data