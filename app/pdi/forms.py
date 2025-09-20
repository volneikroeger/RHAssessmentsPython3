"""
Forms for PDI app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import PDIPlan, PDITask, PDIProgressUpdate, PDIComment, PDIActionCatalog

User = get_user_model()


class PDIPlanForm(forms.ModelForm):
    """Form for creating/editing PDI plans."""
    
    class Meta:
        model = PDIPlan
        fields = [
            'employee', 'manager', 'hr_contact', 'title', 'description',
            'priority', 'start_date', 'target_completion_date'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'hr_contact': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter users to organization members
        from organizations.models import Membership
        user_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        users_queryset = User.objects.filter(id__in=user_ids)
        
        self.fields['employee'].queryset = users_queryset
        self.fields['manager'].queryset = users_queryset.filter(
            memberships__role__in=['MANAGER', 'ORG_ADMIN']
        )
        self.fields['hr_contact'].queryset = users_queryset.filter(
            memberships__role__in=['HR', 'ORG_ADMIN']
        )


class PDITaskForm(forms.ModelForm):
    """Form for creating/editing PDI tasks."""
    
    class Meta:
        model = PDITask
        fields = [
            'title', 'description', 'category', 'competency_area',
            'specific_objective', 'measurable_criteria', 'achievable_steps',
            'relevant_justification', 'time_bound_deadline',
            'required_resources', 'assigned_mentor', 'estimated_hours', 'weight'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'competency_area': forms.TextInput(attrs={'class': 'form-control'}),
            'specific_objective': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'measurable_criteria': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'achievable_steps': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'relevant_justification': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'time_bound_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'required_resources': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'assigned_mentor': forms.Select(attrs={'class': 'form-select'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.1, 'min': 0.1}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter mentors to organization members with appropriate roles
        from organizations.models import Membership
        mentor_ids = Membership.objects.filter(
            organization=organization,
            is_active=True,
            role__in=['MANAGER', 'HR', 'ORG_ADMIN']
        ).values_list('user_id', flat=True)
        
        self.fields['assigned_mentor'].queryset = User.objects.filter(id__in=mentor_ids)


class PDIProgressUpdateForm(forms.ModelForm):
    """Form for updating PDI task progress."""
    
    class Meta:
        model = PDIProgressUpdate
        fields = ['progress_percentage', 'notes']
        widgets = {
            'progress_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 5
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PDICommentForm(forms.ModelForm):
    """Form for adding comments to PDI plans."""
    
    class Meta:
        model = PDIComment
        fields = ['content', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PDIActionCatalogForm(forms.ModelForm):
    """Form for creating/editing PDI action catalog items."""
    
    class Meta:
        model = PDIActionCatalog
        fields = [
            'title', 'description', 'category', 'estimated_duration',
            'difficulty_level', 'required_resources', 'recommended_tools',
            'external_links', 'target_competencies', 'target_roles'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'difficulty_level': forms.Select(attrs={'class': 'form-select'}),
            'required_resources': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recommended_tools': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': _('Enter tools separated by commas')
            }),
            'external_links': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': _('Enter URLs separated by commas')
            }),
            'target_competencies': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': _('Enter competencies separated by commas')
            }),
            'target_roles': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': _('Enter roles separated by commas')
            }),
        }
    
    def clean_recommended_tools(self):
        """Convert comma-separated string to list."""
        tools = self.cleaned_data['recommended_tools']
        if tools:
            return [tool.strip() for tool in tools.split(',') if tool.strip()]
        return []
    
    def clean_external_links(self):
        """Convert comma-separated string to list."""
        links = self.cleaned_data['external_links']
        if links:
            return [link.strip() for link in links.split(',') if link.strip()]
        return []
    
    def clean_target_competencies(self):
        """Convert comma-separated string to list."""
        competencies = self.cleaned_data['target_competencies']
        if competencies:
            return [comp.strip() for comp in competencies.split(',') if comp.strip()]
        return []
    
    def clean_target_roles(self):
        """Convert comma-separated string to list."""
        roles = self.cleaned_data['target_roles']
        if roles:
            return [role.strip() for role in roles.split(',') if role.strip()]
        return []


class PDISearchForm(forms.Form):
    """Form for searching and filtering PDI plans."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search PDI plans...')
        }),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + PDIPlan.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    priority = forms.ChoiceField(
        choices=[('', _('All Priorities'))] + PDIPlan.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    employee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label=_('All Employees')
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter employees to organization members
        from organizations.models import Membership
        user_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        self.fields['employee'].queryset = User.objects.filter(id__in=user_ids)


class PDIApprovalForm(forms.Form):
    """Form for approving/rejecting PDI plans."""
    
    APPROVAL_CHOICES = [
        ('approve', _('Approve')),
        ('reject', _('Request Changes')),
    ]
    
    action = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Approval Decision')
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label=_('Notes'),
        help_text=_('Provide feedback or approval notes.'),
        required=False
    )


class BulkPDIGenerationForm(forms.Form):
    """Form for bulk PDI generation from assessments."""
    
    assessment_instances = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in view
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Select Completed Assessments'),
        help_text=_('Choose assessments to generate PDI plans from.')
    )
    
    template = forms.ModelChoiceField(
        queryset=None,  # Will be set in view
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('PDI Template'),
        help_text=_('Choose the template to use for generating PDI plans.')
    )
    
    auto_approve = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Auto-approve plans'),
        help_text=_('Automatically approve generated plans without manager review.'),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter to completed assessments without PDI plans
        from assessments.models import AssessmentInstance
        self.fields['assessment_instances'].queryset = AssessmentInstance.objects.filter(
            organization=organization,
            status='COMPLETED'
        ).exclude(
            generated_pdi_plans__isnull=False
        ).select_related('user', 'assessment')
        
        # Filter templates to organization and active
        from .models import PDITemplate
        self.fields['template'].queryset = PDITemplate.objects.filter(
            organization=organization,
            is_active=True
        )