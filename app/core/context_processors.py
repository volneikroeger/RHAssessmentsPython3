"""
Context processors for the psychological assessments platform.
"""
from typing import Any, Dict
from django.conf import settings
from django.http import HttpRequest


def tenant_context(request: HttpRequest) -> Dict[str, Any]:
    """Add tenant information to template context."""
    return {
        'current_tenant': getattr(request, 'tenant', None),
        'tenant_subdomain_enabled': getattr(settings, 'TENANT_SUBDOMAIN_ENABLED', True),
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
        'enable_registration': getattr(settings, 'ENABLE_REGISTRATION', True),
        'enable_billing': getattr(settings, 'ENABLE_BILLING', True),
        'enable_analytics': getattr(settings, 'ENABLE_ANALYTICS', True),
    }