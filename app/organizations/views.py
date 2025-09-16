"""
Views for organization management.
"""
import csv
import io
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
)
from django.views import View

from .models import Organization, Membership, Department, Position, Employee, OrganizationInvite
from .forms import (
    OrganizationForm, MembershipForm, InviteForm, DepartmentForm, 
    PositionForm, EmployeeForm, EmployeeImportForm
)
from .mixins import OrganizationPermissionMixin


class OrganizationListView(LoginRequiredMixin, ListView):
    """List user's organizations."""
    model = Organization
    template_name = 'organizations/list.html'
    context_object_name = 'organizations'
    
    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True
        ).distinct()


class OrganizationDetailView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Organization detail view."""
    model = Organization
    template_name = 'organizations/detail.html'
    context_object_name = 'organization'


class OrganizationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create new organization."""
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/create.html'
    success_message = _('Organization created successfully!')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create admin membership for creator
        Membership.objects.create(
            user=self.request.user,
            organization=self.object,
            role='ORG_ADMIN',
            is_primary=True,
            accepted_at=timezone.now()
        )
        
        return response
    
    def get_success_url(self):
        return reverse_lazy('organizations:detail', kwargs={'pk': self.object.pk})


class OrganizationUpdateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Update organization."""
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/update.html'
    success_message = _('Organization updated successfully!')
    required_role = 'ORG_ADMIN'
    
    def get_success_url(self):
        return reverse_lazy('organizations:detail', kwargs={'pk': self.object.pk})


class MembershipListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List organization members."""
    model = Membership
    template_name = 'organizations/members.html'
    context_object_name = 'memberships'
    required_role = 'MANAGER'
    
    def get_queryset(self):
        return Membership.objects.filter(
            organization=self.get_organization(),
            is_active=True
        ).select_related('user')


class InviteUserView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Invite user to organization."""
    model = OrganizationInvite
    form_class = InviteForm
    template_name = 'organizations/invite.html'
    success_message = _('Invitation sent successfully!')
    required_role = 'HR'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.invited_by = self.request.user
        
        # Set expiration date (7 days from now)
        form.instance.expires_at = timezone.now() + timezone.timedelta(days=7)
        
        # Generate token
        import secrets
        form.instance.token = secrets.token_urlsafe(32)
        
        response = super().form_valid(form)
        
        # TODO: Send invitation email
        # send_invitation_email.delay(self.object.id)
        
        return response
    
    def get_success_url(self):
        return reverse_lazy('organizations:members', kwargs={'pk': self.get_organization().pk})


class AcceptInviteView(LoginRequiredMixin, View):
    """Accept organization invitation."""
    
    def get(self, request, token):
        invite = get_object_or_404(OrganizationInvite, token=token)
        
        if invite.is_expired:
            messages.error(request, _('This invitation has expired.'))
            return redirect('dashboard:home')
        
        if invite.is_accepted:
            messages.error(request, _('This invitation has already been accepted.'))
            return redirect('dashboard:home')
        
        try:
            membership = invite.accept(request.user)
            messages.success(
                request, 
                _('Welcome to {}! You have been added as a {}.').format(
                    invite.organization.name,
                    membership.get_role_display()
                )
            )
            return redirect('organizations:detail', pk=invite.organization.pk)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('dashboard:home')


class DepartmentListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List organization departments."""
    model = Department
    template_name = 'organizations/departments.html'
    context_object_name = 'departments'
    required_role = 'MEMBER'
    
    def get_queryset(self):
        return Department.objects.filter(
            organization=self.get_organization(),
            is_active=True
        ).select_related('manager', 'parent')


class DepartmentCreateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Create department."""
    model = Department
    form_class = DepartmentForm
    template_name = 'organizations/create_department.html'
    success_message = _('Department created successfully!')
    required_role = 'HR'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('organizations:departments', kwargs={'pk': self.get_organization().pk})


class DepartmentUpdateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Update department."""
    model = Department
    form_class = DepartmentForm
    template_name = 'organizations/update_department.html'
    success_message = _('Department updated successfully!')
    required_role = 'HR'
    pk_url_kwarg = 'dept_id'
    
    def get_success_url(self):
        return reverse_lazy('organizations:departments', kwargs={'pk': self.object.organization.pk})


class PositionListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List positions in department."""
    model = Position
    template_name = 'organizations/positions.html'
    context_object_name = 'positions'
    required_role = 'MEMBER'
    
    def get_queryset(self):
        department = get_object_or_404(Department, pk=self.kwargs['dept_id'])
        return Position.objects.filter(department=department, is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['department'] = get_object_or_404(Department, pk=self.kwargs['dept_id'])
        return context


class PositionCreateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Create position."""
    model = Position
    form_class = PositionForm
    template_name = 'organizations/create_position.html'
    success_message = _('Position created successfully!')
    required_role = 'HR'
    
    def form_valid(self, form):
        department = get_object_or_404(Department, pk=self.kwargs['dept_id'])
        form.instance.organization = self.get_organization()
        form.instance.department = department
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('organizations:positions', kwargs={'dept_id': self.kwargs['dept_id']})


class PositionUpdateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Update position."""
    model = Position
    form_class = PositionForm
    template_name = 'organizations/update_position.html'
    success_message = _('Position updated successfully!')
    required_role = 'HR'
    pk_url_kwarg = 'pos_id'
    
    def get_success_url(self):
        return reverse_lazy('organizations:positions', kwargs={'dept_id': self.object.department.pk})


class EmployeeListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List organization employees."""
    model = Employee
    template_name = 'organizations/employees.html'
    context_object_name = 'employees'
    required_role = 'MEMBER'
    paginate_by = 50
    
    def get_queryset(self):
        return Employee.objects.filter(
            organization=self.get_organization(),
            is_active=True
        ).select_related('user', 'department', 'position', 'manager')


class EmployeeCreateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Create employee."""
    model = Employee
    form_class = EmployeeForm
    template_name = 'organizations/create_employee.html'
    success_message = _('Employee created successfully!')
    required_role = 'HR'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('organizations:employees', kwargs={'pk': self.get_organization().pk})


class EmployeeUpdateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Update employee."""
    model = Employee
    form_class = EmployeeForm
    template_name = 'organizations/update_employee.html'
    success_message = _('Employee updated successfully!')
    required_role = 'HR'
    pk_url_kwarg = 'emp_id'
    
    def get_success_url(self):
        return reverse_lazy('organizations:employees', kwargs={'pk': self.object.organization.pk})


class EmployeeImportView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Import employees from CSV."""
    form_class = EmployeeImportForm
    template_name = 'organizations/import_employees.html'
    required_role = 'HR'
    
    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        organization = self.get_organization()
        
        try:
            with transaction.atomic():
                # Read CSV
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                created_count = 0
                updated_count = 0
                errors = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Extract data
                        email = row.get('email', '').strip()
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        department_name = row.get('department', '').strip()
                        position_title = row.get('position', '').strip()
                        
                        if not all([email, first_name, last_name, department_name, position_title]):
                            errors.append(f'Row {row_num}: Missing required fields')
                            continue
                        
                        # Get or create user
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        user, user_created = User.objects.get_or_create(
                            email=email,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                            }
                        )
                        
                        # Get department and position
                        try:
                            department = Department.objects.get(
                                organization=organization,
                                name=department_name
                            )
                            position = Position.objects.get(
                                department=department,
                                title=position_title
                            )
                        except (Department.DoesNotExist, Position.DoesNotExist):
                            errors.append(f'Row {row_num}: Department or position not found')
                            continue
                        
                        # Create or update employee
                        employee, emp_created = Employee.objects.get_or_create(
                            organization=organization,
                            user=user,
                            defaults={
                                'department': department,
                                'position': position,
                                'hire_date': timezone.now().date(),
                            }
                        )
                        
                        if emp_created:
                            created_count += 1
                        else:
                            updated_count += 1
                        
                        # Create membership if needed
                        if user_created:
                            Membership.objects.get_or_create(
                                user=user,
                                organization=organization,
                                defaults={'role': 'MEMBER'}
                            )
                    
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
                
                # Show results
                if created_count or updated_count:
                    messages.success(
                        self.request,
                        _('Import completed: {} created, {} updated').format(
                            created_count, updated_count
                        )
                    )
                
                if errors:
                    error_msg = _('Import errors:') + '\n' + '\n'.join(errors[:10])
                    if len(errors) > 10:
                        error_msg += f'\n... and {len(errors) - 10} more errors'
                    messages.error(self.request, error_msg)
        
        except Exception as e:
            messages.error(self.request, _('Import failed: {}').format(str(e)))
        
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('organizations:employees', kwargs={'pk': self.get_organization().pk})


class OrganizationSettingsView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Organization settings."""
    model = Organization
    fields = [
        'name', 'email', 'phone', 'website', 'locale_default', 'timezone',
        'allow_self_registration', 'logo', 'primary_color'
    ]
    template_name = 'organizations/settings.html'
    success_message = _('Settings updated successfully!')
    required_role = 'ORG_ADMIN'
    
    def get_success_url(self):
        return reverse_lazy('organizations:settings', kwargs={'pk': self.object.pk})