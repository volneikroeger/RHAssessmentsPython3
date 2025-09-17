from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    """Dashboard home view."""
    return render(request, 'dashboard/home.html')


@login_required
def super_admin(request):
    """Super admin dashboard."""
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    return render(request, 'dashboard/super_admin.html')