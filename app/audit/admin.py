from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'created_at']
    list_filter = ['created_at', 'organization']
    search_fields = ['user__email', 'action', 'ip_address']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']