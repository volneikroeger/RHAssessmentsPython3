from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _


def privacy_policy(request):
    """Privacy policy view."""
    return render(request, 'audit/privacy_policy.html')


def terms_of_service(request):
    """Terms of service view."""
    return render(request, 'audit/terms_of_service.html')


@login_required
def my_data(request):
    """User data export/management view."""
    return render(request, 'audit/my_data.html')