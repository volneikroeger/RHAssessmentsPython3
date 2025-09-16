"""
Mixins for organization-based permissions.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import Organization, Membership


class OrganizationPermissionMixin(UserPassesTestMixin):
    """
    Mixin to check if user has permission to access organization resources.
    """
    
    required_role = 'MEMBER'  # Default minimum role
    
    def test_func(self):
        """Test if user has required role in organization."""
        organization = self.get_organization()
        if not organization:
            return False
        
        # Super admin can access everything
        if self.request.user.is_superuser:
            return True
        
        # Check membership and role
        try:
            membership = Membership.objects.get(
                user=self.request.user,
                organization=organization,
                is_active=True
            )
            
            # Role hierarchy check
            role_hierarchy = {
                'SUPER_ADMIN': 6,
                'ORG_ADMIN': 5,
                'MANAGER': 4,
                'HR': 3,
                'RECRUITER': 2,
                'MEMBER': 1,
                'VIEWER': 0,
            }
            
            user_level = role_hierarchy.get(membership.role, 0)
            required_level = role_hierarchy.get(self.required_role, 0)
            
            return user_level >= required_level
            
        except Membership.DoesNotExist:
            return False
    
    def get_organization(self):
        """Get organization from URL parameter or request."""
        if hasattr(self, '_organization'):
            return self._organization
        
        # Try to get from URL
        org_id = self.kwargs.get('pk') or self.kwargs.get('org_id')
        if org_id:
            self._organization = get_object_or_404(Organization, pk=org_id)
        else:
            # Try to get from request tenant
            self._organization = getattr(self.request, 'tenant', None)
        
        return self._organization
    
    def handle_no_permission(self):
        """Handle cases where user doesn't have permission."""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        raise PermissionDenied("You don't have permission to access this resource.")


class CompanyOnlyMixin(OrganizationPermissionMixin):
    """Mixin that restricts access to company organizations only."""
    
    def test_func(self):
        if not super().test_func():
            return False
        
        organization = self.get_organization()
        return organization and organization.is_company


class RecruiterOnlyMixin(OrganizationPermissionMixin):
    """Mixin that restricts access to recruiter organizations only."""
    
    def test_func(self):
        if not super().test_func():
            return False
        
        organization = self.get_organization()
        return organization and organization.is_recruiter