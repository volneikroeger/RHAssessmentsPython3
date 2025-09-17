"""
User models for the psychological assessments platform.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.fields import EncryptedTextField, EncryptedEmailField
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as username.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)
    
    # Profile fields
    phone = EncryptedTextField(_('phone number'), blank=True)
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=[('en', 'English'), ('pt-br', 'Portuguese (Brazil)')],
        default='en'
    )
    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'accounts_user'
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def short_name(self):
        """Return short name."""
        return self.first_name
    
    def get_organizations(self):
        """Get all organizations this user belongs to."""
        return self.memberships.select_related('organization').filter(is_active=True)
    
    def get_primary_organization(self):
        """Get user's primary organization."""
        membership = self.memberships.filter(is_active=True, is_primary=True).first()
        return membership.organization if membership else None
    
    def has_role_in_organization(self, organization, role):
        """Check if user has specific role in organization."""
        return self.memberships.filter(
            organization=organization,
            role=role,
            is_active=True
        ).exists()
    
    def is_admin_of_organization(self, organization):
        """Check if user is admin of organization."""
        return self.has_role_in_organization(
            organization, 
            'ORG_ADMIN'
        ) or self.is_superuser


class UserProfile(models.Model):
    """
    Extended user profile with additional information.
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal information (encrypted)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(
        _('gender'),
        max_length=20,
        choices=[
            ('male', _('Male')),
            ('female', _('Female')),
            ('other', _('Other')),
            ('prefer_not_to_say', _('Prefer not to say')),
        ],
        blank=True
    )
    
    # Professional information
    job_title = models.CharField(_('job title'), max_length=200, blank=True)
    department = models.CharField(_('department'), max_length=200, blank=True)
    manager_email = EncryptedEmailField(_('manager email'), blank=True)
    
    # Communication preferences
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    sms_notifications = models.BooleanField(_('SMS notifications'), default=False)
    
    # LGPD/Privacy preferences
    data_processing_consent = models.BooleanField(_('data processing consent'), default=False)
    marketing_consent = models.BooleanField(_('marketing consent'), default=False)
    consent_date = models.DateTimeField(_('consent date'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.full_name} Profile"


class UserSession(models.Model):
    """
    Track user sessions for security and audit purposes.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.email} - {self.session_key[:8]}..."


class PasswordResetToken(models.Model):
    """
    Secure password reset tokens.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        verbose_name = _('Password Reset Token')
        verbose_name_plural = _('Password Reset Tokens')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    @property
    def is_expired(self):
        """Check if token is expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def is_used(self):
        """Check if token was used."""
        return self.used_at is not None
    
    def mark_as_used(self):
        """Mark token as used."""
        from django.utils import timezone
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])