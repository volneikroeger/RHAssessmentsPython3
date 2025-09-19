"""
Utility functions and context processors.
"""
from typing import Any, Dict
from django.conf import settings
from django.http import HttpRequest


def tenant_context(request: HttpRequest) -> Dict[str, Any]:
    """Add tenant information to template context."""
    return {
        'current_tenant': getattr(request, 'tenant', None),
        'tenant_subdomain_enabled': settings.TENANT_SUBDOMAIN_ENABLED,
    }


def locale_context(request: HttpRequest) -> Dict[str, Any]:
    """Add locale information to template context."""
    return {
        'current_language': getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE),
        'available_languages': settings.LANGUAGES,
    }


def feature_flags(request: HttpRequest) -> Dict[str, Any]:
    """Add feature flags to template context."""
    return {
        'enable_registration': settings.ENABLE_REGISTRATION,
        'enable_billing': settings.ENABLE_BILLING,
        'enable_analytics': settings.ENABLE_ANALYTICS,
    }


def get_client_ip(request: HttpRequest) -> str:
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def generate_tenant_slug(name: str) -> str:
    """Generate a URL-safe slug from organization name."""
    import re
    import unidecode
    
    # Convert to ASCII and lowercase
    slug = unidecode.unidecode(name).lower()
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Limit length
    slug = slug[:50]
    
    return slug