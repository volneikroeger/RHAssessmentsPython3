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
        Prioritizes request.tenant. If not found, tries to get from URL kwargs
        but only if the view's model is explicitly Organization.
        """
        if hasattr(self, '_organization'):
            return self._organization

        # 1. Prioritize request.tenant (set by TenantMiddleware)
        if hasattr(self.request, 'tenant') and self.request.tenant:
            self._organization = self.request.tenant
            return self._organization

        # 2. If request.tenant is not set, and this view is for an Organization model,
        #    try to get the organization from URL kwargs.
        #    This handles cases like /organizations/<uuid:pk>/detail/
        is_organization_model_view = False
        if hasattr(self, 'model') and self.model == Organization:
            is_organization_model_view = True
        
        org_id_from_kwargs = self.kwargs.get('pk') or self.kwargs.get('org_id')
        
        if org_id_from_kwargs and is_organization_model_view:
            try:
                self._organization = get_object_or_404(Organization, pk=org_id_from_kwargs)
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
        # tenant context. In this case, the BaseTenantModel's manager would
        # already filter the queryset to empty, leading to a 404 for the object.
        # So, if get_organization returns None, we should fail test_func.
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