"""
Custom middleware for the psychological assessments platform.
"""
import threading
import uuid
from typing import Optional
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import activate
from organizations.models import Organization
from audit.models import AuditLog

# Thread-local storage for tenant context
_thread_locals = threading.local()


def get_current_tenant() -> Optional[Organization]:
    """Get the current tenant from thread-local storage."""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant: Optional[Organization]) -> None:
    """Set the current tenant in thread-local storage."""
    _thread_locals.tenant = tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to handle multi-tenant functionality.
    
    Resolves tenant by:
    1. Subdomain (orgslug.suaapp.local)
    2. X-Tenant header
    3. Path prefix (/t/<slug>/)
    4. User's default organization after login
    """
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        tenant = None
        
        # Try to resolve tenant by subdomain
        host = request.get_host()
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www' and subdomain != 'suaapp':
                tenant = self._get_tenant_by_slug(subdomain)
        
        # Try X-Tenant header
        if not tenant:
            tenant_header = request.META.get('HTTP_X_TENANT')
            if tenant_header:
                tenant = self._get_tenant_by_slug(tenant_header)
        
        # Try path prefix
        if not tenant:
            path = request.path
            if path.startswith('/t/'):
                parts = path.split('/')
                if len(parts) >= 3:
                    tenant_slug = parts[2]
                    tenant = self._get_tenant_by_slug(tenant_slug)
        
        # If no tenant resolved yet, try user's primary organization
        if not tenant and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                primary_membership = request.user.memberships.filter(
                    is_primary=True, 
                    is_active=True
                ).select_related('organization').first()
                if primary_membership:
                    tenant = primary_membership.organization
            except Exception:
                # Handle case where user model might not have memberships yet
                pass
        
        # Set tenant in request and thread-local
        request.tenant = tenant
        set_current_tenant(tenant)
        
        # Set PostgreSQL session variable for RLS
        if tenant:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET LOCAL app.current_tenant = %s",
                    [str(tenant.id)]
                )
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Clear tenant from thread-local
        set_current_tenant(None)
        return response
    
    def _get_tenant_by_slug(self, slug: str) -> Optional[Organization]:
        """Get tenant by slug with caching."""
        cache_key = f'tenant_slug_{slug}'
        tenant = cache.get(cache_key)
        
        if tenant is None:
            try:
                tenant = Organization.objects.get(slug=slug)
                cache.set(cache_key, tenant, 300)  # Cache for 5 minutes
            except Organization.DoesNotExist:
                tenant = False
                cache.set(cache_key, tenant, 60)  # Cache negative result for 1 minute
        
        return tenant if tenant else None


class LocaleMiddleware(MiddlewareMixin):
    """
    Middleware to handle locale selection based on tenant and user preferences.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        # Get language preference from various sources
        language = None
        
        # 1. URL parameter
        if 'lang' in request.GET:
            language = request.GET['lang']
        
        # 2. User profile
        elif hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'profile'):
                language = request.user.profile.preferred_language
        
        # 3. Tenant default
        elif hasattr(request, 'tenant') and request.tenant:
            language = request.tenant.locale_default
        
        # 4. Session
        elif 'django_language' in request.session:
            language = request.session['django_language']
        
        # Validate and activate language
        if language in ['en', 'pt-br']:
            activate(language)
            request.LANGUAGE_CODE = language


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to log user actions for audit purposes.
    """
    
    AUDIT_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    SKIP_PATHS = ['/health/', '/admin/jsi18n/', '/static/', '/media/']
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Skip if not an auditable method or path
        if (request.method not in self.AUDIT_METHODS or 
            any(request.path.startswith(path) for path in self.SKIP_PATHS)):
            return response
        
        # Skip if user is not authenticated
        if not hasattr(request, 'user') or isinstance(request.user, AnonymousUser):
            return response
        
        # Create audit log entry
        try:
            AuditLog.objects.create(
                organization=getattr(request, 'tenant', None),
                user=request.user,
                action=f'{request.method} {request.path}',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'status_code': response.status_code,
                    'content_type': response.get('Content-Type', ''),
                }
            )
        except Exception:
            # Don't break the request if audit logging fails
            pass
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or ''