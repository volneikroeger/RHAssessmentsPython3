"""
Mixins for recruiting-specific permissions and functionality.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from organizations.models import Organization, Membership


class RecruiterPermissionMixin(UserPassesTestMixin):
    """
    Mixin to check if user has recruiter permissions.
    """
    
    required_role = 'RECRUITER'
    
    def test_func(self):
        """Test if user has required recruiter role."""
        organization = self.get_organization()
        if not organization:
            return False
        
        # Super admin can access everything
        if self.request.user.is_superuser:
            return True
        
        # Check if organization is recruiter type
        if not organization.is_recruiter:
            return False
        
        # Check membership and role
        try:
            membership = Membership.objects.get(
                user=self.request.user,
                organization=organization,
                is_active=True
            )
            
            # Role hierarchy for recruiters
            role_hierarchy = {
                'SUPER_ADMIN': 6,
                'ORG_ADMIN': 5,
                'RECRUITER': 4,
                'MANAGER': 3,
                'MEMBER': 2,
                'VIEWER': 1,
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
        
        raise PermissionDenied("You don't have permission to access recruiting features.")


class CandidateAccessMixin(RecruiterPermissionMixin):
    """Mixin for candidate-specific access control."""
    
    def get_queryset(self):
        """Filter candidates by organization and user permissions."""
        queryset = super().get_queryset()
        organization = self.get_organization()
        
        # Filter by organization
        queryset = queryset.filter(organization=organization)
        
        # Additional filtering based on user role
        user = self.request.user
        if not user.is_superuser:
            membership = user.memberships.filter(
                organization=organization,
                is_active=True
            ).first()
            
            if membership and membership.role == 'RECRUITER':
                # Recruiters see only their assigned candidates
                queryset = queryset.filter(
                    Q(assigned_recruiter=user) | Q(assigned_recruiter__isnull=True)
                )
        
        return queryset


class JobAccessMixin(RecruiterPermissionMixin):
    """Mixin for job-specific access control."""
    
    def get_queryset(self):
        """Filter jobs by organization and user permissions."""
        queryset = super().get_queryset()
        organization = self.get_organization()
        
        # Filter by organization
        queryset = queryset.filter(organization=organization)
        
        # Additional filtering based on user role
        user = self.request.user
        if not user.is_superuser:
            membership = user.memberships.filter(
                organization=organization,
                is_active=True
            ).first()
            
            if membership and membership.role == 'RECRUITER':
                # Recruiters see only their assigned jobs
                queryset = queryset.filter(
                    Q(assigned_recruiter=user) | Q(assigned_recruiter__isnull=True)
                )
        
        return queryset