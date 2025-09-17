"""
Audit models for logging and compliance tracking.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AuditLog(models.Model):
    """
    Audit log for tracking user actions.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(_('action'), max_length=200)
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('user agent'), blank=True)
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.action}"