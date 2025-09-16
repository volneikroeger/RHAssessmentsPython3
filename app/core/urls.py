"""
URL configuration for psychological assessments SaaS platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView

# Health check endpoint
urlpatterns = [
    path('health/', TemplateView.as_view(template_name='health.html'), name='health'),
]

# Internationalized URLs
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('dashboard.urls')),
    path('organizations/', include('organizations.urls')),
    path('assessments/', include('assessments.urls')),
    path('pdi/', include('pdi.urls')),
    path('recruiting/', include('recruiting.urls')),
    path('billing/', include('billing.urls')),
    path('reports/', include('reports.urls')),
    path('audit/', include('audit.urls')),
    path('api/webhooks/', include('billing.webhook_urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin customization
admin.site.site_header = 'Psychological Assessments SaaS'
admin.site.site_title = 'Assessments Admin'
admin.site.index_title = 'Welcome to Assessments Administration'