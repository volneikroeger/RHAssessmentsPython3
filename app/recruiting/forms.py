"""
Forms for recruiting app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Client, Job, Candidate, JobApplication, Interview, CandidateNote, Placement

User = get_user_model()


class ClientForm(forms.ModelForm):
    """Form for creating/editing clients."""
    
    class Meta:
        model = Client
        fields = [
            'name', 'industry', 'size', 'primary_contact_name', 'primary_contact_email',
            'primary_contact_phone', 'website', 'description', 'address_line1',
            'address_line2', 'city', 'state', 'postal_code', 'country',
            'contract_start_date', 'contract_end_date', 'commission_rate', 'payment_terms'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'primary_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'primary_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
        }


class JobForm(forms.ModelForm):
    """Form for creating/editing jobs."""
    
    required_skills_text = forms.CharField(
        label=_('Required Skills'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text=_('Enter skills separated by commas'),
        required=False
    )
    
    preferred_skills_text = forms.CharField(
        label=_('Preferred Skills'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text=_('Enter skills separated by commas'),
        required=False
    )
    
    languages_text = forms.CharField(
        label=_('Languages'),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_('Enter languages separated by commas'),
        required=False
    )
    
    class Meta:
        model = Job
        fields = [
            'client', 'title', 'description', 'requirements', 'responsibilities',
            'employment_type', 'location', 'remote_allowed', 'travel_required',
            'min_experience_years', 'max_experience_years', 'education_level',
            'salary_min', 'salary_max', 'currency', 'benefits',
            'status', 'priority', 'positions_available',
            'posted_date', 'application_deadline', 'target_start_date',
            'requires_assessment', 'assessment_definition', 'assigned_recruiter'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'travel_required': forms.TextInput(attrs={'class': 'form-control'}),
            'min_experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'education_level': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'positions_available': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'posted_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'application_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assessment_definition': forms.Select(attrs={'class': 'form-select'}),
            'assigned_recruiter': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter clients and recruiters to organization
        self.fields['client'].queryset = Client.objects.filter(organization=organization, is_active=True)
        
        # Filter recruiters to organization members with recruiter role
        from organizations.models import Membership
        recruiter_ids = Membership.objects.filter(
            organization=organization,
            is_active=True,
            role__in=['RECRUITER', 'ORG_ADMIN']
        ).values_list('user_id', flat=True)
        
        self.fields['assigned_recruiter'].queryset = User.objects.filter(id__in=recruiter_ids)
        
        # Filter assessments to organization
        from assessments.models import AssessmentDefinition
        self.fields['assessment_definition'].queryset = AssessmentDefinition.objects.filter(
            organization=organization,
            status='ACTIVE'
        )
        
        # Set initial values for skills fields if editing
        if self.instance.pk:
            self.fields['required_skills_text'].initial = ', '.join(self.instance.required_skills)
            self.fields['preferred_skills_text'].initial = ', '.join(self.instance.preferred_skills)
            self.fields['languages_text'].initial = ', '.join(self.instance.languages)
    
    def clean_required_skills_text(self):
        """Convert comma-separated string to list."""
        skills = self.cleaned_data['required_skills_text']
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []
    
    def clean_preferred_skills_text(self):
        """Convert comma-separated string to list."""
        skills = self.cleaned_data['preferred_skills_text']
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []
    
    def clean_languages_text(self):
        """Convert comma-separated string to list."""
        languages = self.cleaned_data['languages_text']
        if languages:
            return [lang.strip() for lang in languages.split(',') if lang.strip()]
        return []
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set skills and languages from text fields
        instance.required_skills = self.cleaned_data['required_skills_text']
        instance.preferred_skills = self.cleaned_data['preferred_skills_text']
        instance.languages = self.cleaned_data['languages_text']
        
        if commit:
            instance.save()
        return instance


class CandidateForm(forms.ModelForm):
    """Form for creating/editing candidates."""
    
    skills_text = forms.CharField(
        label=_('Skills'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text=_('Enter skills separated by commas'),
        required=False
    )
    
    languages_text = forms.CharField(
        label=_('Languages'),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_('Enter languages separated by commas'),
        required=False
    )
    
    certifications_text = forms.CharField(
        label=_('Certifications'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text=_('Enter certifications separated by commas'),
        required=False
    )
    
    class Meta:
        model = Candidate
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'current_title', 'current_company', 'experience_years', 'education_level',
            'location', 'willing_to_relocate', 'remote_work_preference',
            'salary_expectation_min', 'salary_expectation_max', 'currency',
            'resume_file', 'portfolio_url', 'linkedin_url',
            'status', 'assigned_recruiter', 'notes', 'source', 'source_details'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'current_title': forms.TextInput(attrs={'class': 'form-control'}),
            'current_company': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'education_level': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'remote_work_preference': forms.Select(attrs={'class': 'form-select'}),
            'salary_expectation_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'salary_expectation_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'resume_file': forms.FileInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_recruiter': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'source_details': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter recruiters to organization members
        from organizations.models import Membership
        recruiter_ids = Membership.objects.filter(
            organization=organization,
            is_active=True,
            role__in=['RECRUITER', 'ORG_ADMIN']
        ).values_list('user_id', flat=True)
        
        self.fields['assigned_recruiter'].queryset = User.objects.filter(id__in=recruiter_ids)
        
        # Set initial values for skills fields if editing
        if self.instance.pk:
            self.fields['skills_text'].initial = ', '.join(self.instance.skills)
            self.fields['languages_text'].initial = ', '.join(self.instance.languages)
            self.fields['certifications_text'].initial = ', '.join(self.instance.certifications)
    
    def clean_skills_text(self):
        """Convert comma-separated string to list."""
        skills = self.cleaned_data['skills_text']
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []
    
    def clean_languages_text(self):
        """Convert comma-separated string to list."""
        languages = self.cleaned_data['languages_text']
        if languages:
            return [lang.strip() for lang in languages.split(',') if lang.strip()]
        return []
    
    def clean_certifications_text(self):
        """Convert comma-separated string to list."""
        certifications = self.cleaned_data['certifications_text']
        if certifications:
            return [cert.strip() for cert in certifications.split(',') if cert.strip()]
        return []
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set skills, languages, and certifications from text fields
        instance.skills = self.cleaned_data['skills_text']
        instance.languages = self.cleaned_data['languages_text']
        instance.certifications = self.cleaned_data['certifications_text']
        
        if commit:
            instance.save()
        return instance


class JobApplicationForm(forms.ModelForm):
    """Form for creating/editing job applications."""
    
    class Meta:
        model = JobApplication
        fields = [
            'candidate', 'job', 'status', 'cover_letter', 'recruiter',
            'interview_scheduled_date', 'interview_notes', 'interview_rating'
        ]
        widgets = {
            'candidate': forms.Select(attrs={'class': 'form-select'}),
            'job': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recruiter': forms.Select(attrs={'class': 'form-select'}),
            'interview_scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'interview_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'interview_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter candidates, jobs, and recruiters to organization
        self.fields['candidate'].queryset = Candidate.objects.filter(organization=organization)
        self.fields['job'].queryset = Job.objects.filter(organization=organization, is_active=True)
        
        from organizations.models import Membership
        recruiter_ids = Membership.objects.filter(
            organization=organization,
            is_active=True,
            role__in=['RECRUITER', 'ORG_ADMIN']
        ).values_list('user_id', flat=True)
        
        self.fields['recruiter'].queryset = User.objects.filter(id__in=recruiter_ids)


class InterviewForm(forms.ModelForm):
    """Form for creating/editing interviews."""
    
    class Meta:
        model = Interview
        fields = [
            'interview_type', 'scheduled_date', 'duration_minutes', 'location_or_link',
            'interviewer', 'additional_interviewers', 'overall_rating', 'technical_rating',
            'communication_rating', 'cultural_fit_rating', 'feedback', 'strengths',
            'concerns', 'recommendation'
        ]
        widgets = {
            'interview_type': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 15}),
            'location_or_link': forms.TextInput(attrs={'class': 'form-control'}),
            'interviewer': forms.Select(attrs={'class': 'form-select'}),
            'additional_interviewers': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'overall_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'technical_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'communication_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'cultural_fit_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'concerns': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recommendation': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter interviewers to organization members
        from organizations.models import Membership
        interviewer_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        self.fields['interviewer'].queryset = User.objects.filter(id__in=interviewer_ids)
        self.fields['additional_interviewers'].queryset = User.objects.filter(id__in=interviewer_ids)


class CandidateNoteForm(forms.ModelForm):
    """Form for adding notes to candidates."""
    
    class Meta:
        model = CandidateNote
        fields = ['content', 'note_type', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note_type': forms.Select(attrs={'class': 'form-select'}),
        }


class CandidateSearchForm(forms.Form):
    """Form for searching and filtering candidates."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search candidates...')
        }),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + Candidate.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    experience_min = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        label=_('Min Experience (years)'),
        required=False
    )
    
    experience_max = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        label=_('Max Experience (years)'),
        required=False
    )
    
    education_level = forms.ChoiceField(
        choices=[('', _('All Education Levels'))] + Candidate._meta.get_field('education_level').choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    remote_work_preference = forms.ChoiceField(
        choices=[('', _('All Remote Preferences'))] + Candidate._meta.get_field('remote_work_preference').choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    skills = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Skills (comma-separated)')
        }),
        required=False
    )


class JobSearchForm(forms.Form):
    """Form for searching and filtering jobs."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search jobs...')
        }),
        required=False
    )
    
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label=_('All Clients')
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + Job.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    priority = forms.ChoiceField(
        choices=[('', _('All Priorities'))] + Job.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    employment_type = forms.ChoiceField(
        choices=[('', _('All Types'))] + Job.EMPLOYMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(organization=organization, is_active=True)


class PlacementForm(forms.ModelForm):
    """Form for creating/editing placements."""
    
    class Meta:
        model = Placement
        fields = [
            'start_date', 'salary', 'currency', 'guarantee_period_days',
            'follow_up_30_days', 'follow_up_60_days', 'follow_up_90_days',
            'is_active', 'termination_date', 'termination_reason'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'guarantee_period_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'termination_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'termination_reason': forms.Select(attrs={'class': 'form-select'}),
        }


class BulkCandidateImportForm(forms.Form):
    """Form for importing candidates from CSV."""
    
    csv_file = forms.FileField(
        label=_('CSV File'),
        help_text=_('Upload a CSV file with candidate information'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError(_('File must be a CSV file.'))
        
        if csv_file.size > 10 * 1024 * 1024:  # 10MB limit
            raise forms.ValidationError(_('File size cannot exceed 10MB.'))
        
        return csv_file