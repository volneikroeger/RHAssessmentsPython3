from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from organizations.models import Organization, Membership
from assessments.models import AssessmentDefinition, AssessmentInstance
from accounts.models import User


def home(request):
    """Dashboard home view."""
    return render(request, 'dashboard/home.html')


@login_required
def super_admin(request):
    """Super admin dashboard."""
    if not request.user.is_superuser:
        raise PermissionDenied

    return render(request, 'dashboard/super_admin.html')


@login_required
def system_config(request):
    """System configuration dashboard."""
    if not (request.user.is_superuser or
            request.user.memberships.filter(
                is_active=True,
                role__in=['SUPER_ADMIN', 'ORG_ADMIN']
            ).exists()):
        raise PermissionDenied

    context = {
        'total_organizations': Organization.objects.count(),
        'active_organizations': Organization.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_templates': AssessmentDefinition.objects.count(),
        'active_templates': AssessmentDefinition.objects.filter(status='ACTIVE').count(),
        'total_assessments': AssessmentInstance.objects.count(),
        'completed_assessments': AssessmentInstance.objects.filter(status='COMPLETED').count(),
    }

    return render(request, 'dashboard/system_config.html', context)