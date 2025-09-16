"""
Organization models for multi-tenant functionality.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from fernet_fields import EncryptedTextField
from core.utils import generate_tenant_slug

User = get_user_model()


class Organization(models.Model):
    """
    Organization model for multi-tenant functionality.
    """
    
    KIND_CHOICES = [
        ('COMPANY', _('Company (HR + PDI)')),
        ('RECRUITER', _('Recruiter (R&S)')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    kind = models.CharField(_('kind'), max_length=20, choices=KIND_CHOICES)
    
    # Localization
    locale_default = models.CharField(
        _('default locale'),
        max_length=10,
        choices=[('en', 'English'), ('pt-br', 'Portuguese (Brazil)')],
        default='en'
    )
    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    
    # Domain settings for tenant resolution
    domain_primary = models.CharField(_('primary domain'), max_length=255, blank=True)
    subdomain = models.CharField(_('subdomain'), max_length=100, blank=True, unique=True)
    
    # Contact information
    email = models.EmailField(_('contact email'), blank=True)
    phone = EncryptedTextField(_('phone number'), blank=True)
    website = models.URLField(_('website'), blank=True)
    
    # Address (encrypted for privacy)
    address_line1 = EncryptedTextField(_('address line 1'), blank=True)
    address_line2 = EncryptedTextField(_('address line 2'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state'), max_length=100, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    country = models.CharField(_('country'), max_length=100, blank=True)
    
    # Compliance and legal
    tax_id = EncryptedTextField(_('tax ID'), blank=True)  # CNPJ, EIN, etc.
    legal_name = models.CharField(_('legal name'), max_length=300, blank=True)
    
    # Settings
    is_active = models.BooleanField(_('active'), default=True)
    allow_self_registration = models.BooleanField(_('allow self registration'), default=False)
    
    # Branding
    logo = models.ImageField(_('logo'), upload_to='org_logos/', blank=True)
    primary_color = models.CharField(_('primary color'), max_length=7, default='#007bff')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = generate_tenant_slug(self.name)
        
        # Generate subdomain if not provided
        if not self.subdomain:
            self.subdomain = self.slug
        
        super().save(*args, **kwargs)
    
    @property
    def is_company(self):
        """Check if organization is a company."""
        return self.kind == 'COMPANY'
    
    @property
    def is_recruiter(self):
        """Check if organization is a recruiter."""
        return self.kind == 'RECRUITER'
    
    def get_active_members(self):
        """Get all active members of the organization."""
        return self.memberships.filter(is_active=True).select_related('user')
    
    def get_admin_members(self):
        """Get all admin members of the organization."""
        return self.get_active_members().filter(role='ORG_ADMIN')


class Membership(models.Model):
    """
    User membership in organizations with roles.
    """
    
    ROLE_CHOICES = [
        ('SUPER_ADMIN', _('Super Admin')),  # Global admin across all tenants
        ('ORG_ADMIN', _('Organization Admin')),
        ('MANAGER', _('Manager')),
        ('HR', _('HR')),
        ('RECRUITER', _('Recruiter')),
        ('MEMBER', _('Member')),
        ('VIEWER', _('Viewer')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_primary = models.BooleanField(_('primary organization'), default=False)
    
    # Invitation tracking
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_invitations'
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')
        unique_together = ['user', 'organization']
        ordering = ['organization__name', 'user__email']
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary organization per user
        if self.is_primary:
            Membership.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    @property
    def is_admin(self):
        """Check if membership has admin privileges."""
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN']
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'HR']
    
    @property
    def can_view_reports(self):
        """Check if user can view reports."""
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'MANAGER', 'HR', 'RECRUITER']


class OrganizationInvite(models.Model):
    """
    Pending invitations to join organizations.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invites')
    email = models.EmailField(_('email address'))
    role = models.CharField(_('role'), max_length=20, choices=Membership.ROLE_CHOICES, default='MEMBER')
    token = models.CharField(_('token'), max_length=100, unique=True)
    
    # Invitation details
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_invites_sent')
    message = models.TextField(_('personal message'), blank=True)
    
    # Status
    is_accepted = models.BooleanField(_('accepted'), default=False)
    accepted_at = models.DateTimeField(_('accepted at'), null=True, blank=True)
    expires_at = models.DateTimeField(_('expires at'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Organization Invite')
        verbose_name_plural = _('Organization Invites')
        unique_together = ['organization', 'email']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invite to {self.email} for {self.organization.name}"
    
    @property
    def is_expired(self):
        """Check if invitation is expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def accept(self, user):
        """Accept the invitation and create membership."""
        from django.utils import timezone
        
        if self.is_expired:
            raise ValueError("Invitation has expired")
        
        if self.is_accepted:
            raise ValueError("Invitation already accepted")
        
        # Create membership
        membership = Membership.objects.create(
            user=user,
            organization=self.organization,
            role=self.role,
            invited_by=self.invited_by,
            invited_at=self.created_at,
            accepted_at=timezone.now()
        )
        
        # Mark invitation as accepted
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save(update_fields=['is_accepted', 'accepted_at'])
        
        return membership


class Department(models.Model):
    """
    Department within an organization (for companies).
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # Manager
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_departments'
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        unique_together = ['organization', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class Position(models.Model):
    """
    Job positions within an organization.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='positions')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Hierarchy
    level = models.PositiveIntegerField(_('level'), default=1)  # 1=entry, 5=executive
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Requirements
    required_skills = models.JSONField(_('required skills'), default=list, blank=True)
    preferred_skills = models.JSONField(_('preferred skills'), default=list, blank=True)
    min_experience_years = models.PositiveIntegerField(_('minimum experience (years)'), default=0)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Position')
        verbose_name_plural = _('Positions')
        unique_together = ['organization', 'department', 'title']
        ordering = ['department__name', 'title']
    
    def __str__(self):
        return f"{self.department.name} - {self.title}"


class Employee(models.Model):
    """
    Employee information within an organization.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='employees')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employments')
    
    # Position information
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='employees')
    employee_id = models.CharField(_('employee ID'), max_length=50, blank=True)
    
    # Employment details
    hire_date = models.DateField(_('hire date'))
    termination_date = models.DateField(_('termination date'), null=True, blank=True)
    employment_type = models.CharField(
        _('employment type'),
        max_length=20,
        choices=[
            ('FULL_TIME', _('Full Time')),
            ('PART_TIME', _('Part Time')),
            ('CONTRACTOR', _('Contractor')),
            ('INTERN', _('Intern')),
        ],
        default='FULL_TIME'
    )
    
    # Reporting
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    
    # Compensation (encrypted)
    salary = EncryptedTextField(_('salary'), blank=True)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')
        unique_together = ['organization', 'user']
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.position.title}"
    
    @property
    def is_manager(self):
        """Check if employee is a manager."""
        return self.direct_reports.filter(is_active=True).exists()
    
    def get_direct_reports(self):
        """Get all direct reports."""
        return self.direct_reports.filter(is_active=True)