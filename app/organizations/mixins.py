"""
Mixins for organization-based permissions.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import Http404
from .models import Organization, Membership


class OrganizationPermissionMixin(UserPassesTestMixin):
    """
    Mixin to check if user has permission to access organization resources.
    """
    
    required_role = 'MEMBER'  # Default minimum role
    
    def get_organization(self):
        """
        Get the current organization for the request.
        Prioritizes URL kwargs first, then falls back to request.tenant.
        """
        if hasattr(self, '_organization'):
            return self._organization

        # 1. Try to get from URL kwargs first if 'pk' or 'org_id' is present
        org_id_from_kwargs = self.kwargs.get('pk') or self.kwargs.get('org_id')
        if org_id_from_kwargs:
            try:
                self._organization = get_object_or_404(Organization, pk=org_id_from_kwargs)
                # Set request.tenant if it's not already set, for consistency
                if not hasattr(self.request, 'tenant') or not self.request.tenant:
                    self.request.tenant = self._organization
                return self._organization
            except Http404:
                # If the PK was for an Organization but not found, it's a legitimate 404.
                # Let it fall through to None, which will cause test_func to fail.
                pass

        # If none of the above, no organization could be determined.
        # This means the tenant context is missing for a tenant-scoped object.
        self._organization = None
        return self._organization

    def test_func(self):
        """Test if user has required role in organization."""
        organization = self.get_organization()
        
        # If no organization is found, and the view is for a tenant-scoped model
        # (i.e., not an Organization model itself), then it implies a missing
        # 2. Fallback to request.tenant (set by TenantMiddleware for subdomain/path-prefix tenants)
        if hasattr(self.request, 'tenant') and self.request.tenant:
            self._organization = self.request.tenant
            return self._organization

        # If none of the above, no organization could be determined.
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