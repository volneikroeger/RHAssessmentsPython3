"""
Views for the accounts app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from organizations.models import Membership
from .models import User


@login_required
def profile(request):
    """User profile view."""
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


@login_required
def edit_profile(request):
    """Edit user profile view."""
    if request.method == 'POST':
        messages.success(request, _('Profile updated successfully!'))

    return render(request, 'accounts/edit_profile.html', {
        'user': request.user
    })


@login_required
def change_password(request):
    """Change password view."""
    if request.method == 'POST':
        messages.success(request, _('Password changed successfully!'))

    return render(request, 'accounts/change_password.html')


@login_required
def account_settings(request):
    """Account settings view."""
    return render(request, 'accounts/settings.html', {
        'user': request.user
    })


class UserManagementView(LoginRequiredMixin, ListView):
    """Admin view for managing all users."""
    model = User
    template_name = 'accounts/user_management.html'
    context_object_name = 'users'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or
                request.user.memberships.filter(
                    is_active=True,
                    role__in=['SUPER_ADMIN', 'ORG_ADMIN']
                ).exists()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = User.objects.annotate(
            membership_count=Count('memberships')
        ).prefetch_related('memberships__organization')

        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        role = self.request.GET.get('role')

        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        if role:
            queryset = queryset.filter(memberships__role=role).distinct()

        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['role_choices'] = Membership.ROLE_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_role'] = self.request.GET.get('role', '')
        return context