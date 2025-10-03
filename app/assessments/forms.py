"""
Forms for assessments app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import AssessmentDefinition, Question, QuestionOption, Response
from .scoring import AssessmentValidator


class AssessmentDefinitionForm(forms.ModelForm):
    """Form for creating/editing assessment definitions."""
    
    class Meta:
        model = AssessmentDefinition
        fields = [
            'name', 'description', 'framework', 'version', 'status',
            'instructions', 'estimated_duration', 'randomize_questions',
            'allow_skip', 'show_progress'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'framework': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class QuestionForm(forms.ModelForm):
    """Form for creating/editing questions."""
    
    class Meta:
        model = Question
        fields = [
            'text', 'question_type', 'dimension', 'order',
            'reverse_scored', 'weight', 'required', 'is_active'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'dimension': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.1, 'min': 0}),
        }


class QuestionOptionForm(forms.ModelForm):
    """Form for creating/editing question options."""
    
    class Meta:
        model = QuestionOption
        fields = ['text', 'value', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class AssessmentResponseForm(forms.Form):
    """Dynamic form for collecting assessment responses."""
    
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for question in questions:
            field_name = f'question_{question.id}'
            
            if question.question_type in ['LIKERT_5', 'LIKERT_7']:
                # Create Likert scale choices
                scale_size = 5 if question.question_type == 'LIKERT_5' else 7
                choices = [(i, str(i)) for i in range(1, scale_size + 1)]
                
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    required=question.required
                )
                
            elif question.question_type == 'MULTIPLE_CHOICE':
                # Use question options
                choices = [(opt.id, opt.text) for opt in question.options.all().order_by('order')]
                
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    required=question.required
                )
                
            elif question.question_type == 'FORCED_CHOICE':
                # Forced choice between pairs of options
                choices = [(opt.id, opt.text) for opt in question.options.all().order_by('order')]
                
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    required=question.required
                )
                
            elif question.question_type == 'RANKING':
                # Ranking of multiple options
                options = question.options.all().order_by('order')
                choices = [(opt.id, opt.text) for opt in options]
                
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=question.text,
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input ranking-field'}),
                    required=question.required
                )
                
            elif question.question_type == 'TEXT':
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                    required=question.required
                )
                
            # Add question metadata as field attributes
            self.fields[field_name].question = question
    
    def clean(self):
        """Validate assessment responses for quality."""
        cleaned_data = super().clean()
        
        # Create temporary response data for validation
        numeric_responses = []
        for field_name, value in cleaned_data.items():
            if field_name.startswith('question_') and value:
                question = self.fields[field_name].question
                
                # Convert to numeric for validation
                if question.question_type in ['LIKERT_5', 'LIKERT_7']:
                    numeric_responses.append(int(value))
                elif question.question_type == 'MULTIPLE_CHOICE':
                    try:
                        option = question.options.get(id=value)
                        numeric_responses.append(option.value)
                    except:
                        pass
        
        # Basic response pattern validation
        if len(numeric_responses) > 5:  # Only validate if enough responses
            # Check for straight-lining
            if len(set(numeric_responses)) == 1:
                raise forms.ValidationError(
                    _("Please vary your responses. All identical answers may not provide accurate results.")
                )
            
            # Check for extreme response bias
            if numeric_responses:
                min_val, max_val = min(numeric_responses), max(numeric_responses)
                extreme_responses = sum(1 for r in numeric_responses if r in [min_val, max_val])
                extreme_rate = extreme_responses / len(numeric_responses)
                
                if extreme_rate > 0.9:
                    self.add_error(None, forms.ValidationError(
                        _("Please consider using the full range of response options for more accurate results.")
                    ))
        
        return cleaned_data


class AssessmentInviteForm(forms.Form):
    """Form for inviting users to take assessments."""
    
    users = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in view
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Select Users'),
        help_text=_('Choose users to invite for this assessment.')
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label=_('Personal Message'),
        help_text=_('Optional message to include with the invitation.'),
        required=False
    )
    
    expires_in_days = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 365}),
        label=_('Expires in (days)'),
        initial=30,
        help_text=_('Number of days until the invitation expires.')
    )
    
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset to organization members
        from organizations.models import Membership
        user_ids = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user_id', flat=True)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['users'].queryset = User.objects.filter(id__in=user_ids)


class AssessmentSearchForm(forms.Form):
    """Form for searching and filtering assessments."""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search assessments...')
        }),
        required=False
    )
    
    framework = forms.ChoiceField(
        choices=[('', _('All Frameworks'))] + AssessmentDefinition.FRAMEWORK_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + AssessmentDefinition.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )