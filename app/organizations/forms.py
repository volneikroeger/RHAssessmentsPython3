"""
Forms for organization management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Organization, Membership, Department, Position, Employee, OrganizationInvite


class OrganizationForm(forms.ModelForm):
    """Form for creating/updating organizations."""
    
    class Meta:
        model = Organization
        fields = [
            'name', 'kind', 'locale_default', 'timezone',
            'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'allow_self_registration', 'logo', 'primary_color'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'locale_default': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class MembershipForm(forms.ModelForm):
    """Form for managing memberships."""
    
    class Meta:
        model = Membership
        fields = ['role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class InviteForm(forms.ModelForm):
    """Form for inviting users to organizations."""
    
    class Meta:
        model = OrganizationInvite
        fields = ['email', 'role', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_email(self):
        email = self.cleaned_data['email']
        organization = self.instance.organization
        
        # Check if user already has membership
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=email)
            if Membership.objects.filter(user=user, organization=organization).exists():
                raise forms.ValidationError(_('User is already a member of this organization.'))
        except User.DoesNotExist:
            pass
        
        # Check if invite already exists
        if OrganizationInvite.objects.filter(
            organization=organization,
            email=email,
            is_accepted=False
        ).exists():
            raise forms.ValidationError(_('An invitation has already been sent to this email.'))
        
        return email


class DepartmentForm(forms.ModelForm):
    """Form for creating/updating departments."""
    
    class Meta:
        model = Department
        fields = ['name', 'description', 'parent', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
        }


class PositionForm(forms.ModelForm):
    """Form for creating/updating positions."""
    
    class Meta:
        model = Position
        fields = [
            'title', 'description', 'level', 'reports_to',
            'min_experience_years'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'reports_to': forms.Select(attrs={'class': 'form-select'}),
            'min_experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class EmployeeForm(forms.ModelForm):
    """Form for creating/updating employees."""
    
    class Meta:
        model = Employee
        fields = [
            'user', 'department', 'position', 'employee_id',
            'hire_date', 'employment_type', 'manager', 'salary', 'currency'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EmployeeImportForm(forms.Form):
    """Form for importing employees from CSV."""
    
    csv_file = forms.FileField(
        label=_('CSV File'),
        help_text=_('Upload a CSV file with columns: email, first_name, last_name, department, position'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError(_('File must be a CSV file.'))
        
        if csv_file.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError(_('File size cannot exceed 5MB.'))
        
        return csv_file