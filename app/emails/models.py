"""
Email models for email management and templates.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.utils import timezone
from core.db import BaseTenantModel

User = get_user_model()


class EmailTemplate(BaseTenantModel):
    """
    Email templates for various notification types.
    """
    
    TEMPLATE_TYPES = [
        ('ASSESSMENT_INVITATION', _('Assessment Invitation')),
        ('ASSESSMENT_REMINDER', _('Assessment Reminder')),
        ('ASSESSMENT_COMPLETED', _('Assessment Completed')),
        ('PDI_CREATED', _('PDI Plan Created')),
        ('PDI_APPROVED', _('PDI Plan Approved')),
        ('PDI_TASK_DUE', _('PDI Task Due')),
        ('PDI_TASK_OVERDUE', _('PDI Task Overdue')),
        ('ORGANIZATION_INVITE', _('Organization Invitation')),
        ('PASSWORD_RESET', _('Password Reset')),
        ('WELCOME', _('Welcome Email')),
        ('BILLING_INVOICE', _('Billing Invoice')),
        ('BILLING_PAYMENT_FAILED', _('Payment Failed')),
        ('BILLING_SUBSCRIPTION_RENEWED', _('Subscription Renewed')),
        ('RECRUITING_APPLICATION', _('Job Application')),
        ('RECRUITING_INTERVIEW', _('Interview Scheduled')),
        ('RECRUITING_OFFER', _('Job Offer')),
        ('SYSTEM_NOTIFICATION', _('System Notification')),
        ('CUSTOM', _('Custom Template')),
    ]
    
    LANGUAGES = [
        ('en', _('English')),
        ('pt-br', _('Portuguese (Brazil)')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('template name'), max_length=200)
    template_type = models.CharField(_('template type'), max_length=30, choices=TEMPLATE_TYPES)
    language = models.CharField(_('language'), max_length=10, choices=LANGUAGES, default='en')
    
    # Email content
    subject = models.CharField(_('subject'), max_length=200)
    html_content = models.TextField(_('HTML content'))
    text_content = models.TextField(_('text content'), blank=True)
    
    # Template variables documentation
    available_variables = models.JSONField(_('available variables'), default=dict, blank=True)
    sample_context = models.JSONField(_('sample context'), default=dict, blank=True)
    
    # Configuration
    from_email = models.EmailField(_('from email'), blank=True)
    from_name = models.CharField(_('from name'), max_length=100, blank=True)
    reply_to = models.EmailField(_('reply to'), blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_default = models.BooleanField(_('default template'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
        unique_together = ['organization', 'template_type', 'language', 'is_default']
        ordering = ['template_type', 'language', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()}) - {self.get_language_display()}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default template per type/language/organization
        if self.is_default:
            EmailTemplate.objects.filter(
                organization=self.organization,
                template_type=self.template_type,
                language=self.language,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def render_subject(self, context_data):
        """Render subject with context data."""
        template = Template(self.subject)
        context = Context(context_data)
        return template.render(context)
    
    def render_html_content(self, context_data):
        """Render HTML content with context data."""
        template = Template(self.html_content)
        context = Context(context_data)
        return template.render(context)
    
    def render_text_content(self, context_data):
        """Render text content with context data."""
        if self.text_content:
            template = Template(self.text_content)
            context = Context(context_data)
            return template.render(context)
        return None
    
    def get_from_email(self):
        """Get from email with fallback to organization or default."""
        if self.from_email:
            return self.from_email
        elif self.organization and self.organization.email:
            return self.organization.email
        else:
            from django.conf import settings
            return settings.DEFAULT_FROM_EMAIL
    
    def get_from_name(self):
        """Get from name with fallback to organization."""
        if self.from_name:
            return self.from_name
        elif self.organization:
            return self.organization.name
        else:
            return "Psychological Assessments Platform"


class EmailMessage(BaseTenantModel):
    """
    Email messages sent through the platform.
    """
    
    STATUS_CHOICES = [
        ('QUEUED', _('Queued')),
        ('SENDING', _('Sending')),
        ('SENT', _('Sent')),
        ('DELIVERED', _('Delivered')),
        ('OPENED', _('Opened')),
        ('CLICKED', _('Clicked')),
        ('FAILED', _('Failed')),
        ('BOUNCED', _('Bounced')),
        ('COMPLAINED', _('Complained')),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', _('Low')),
        ('NORMAL', _('Normal')),
        ('HIGH', _('High')),
        ('URGENT', _('Urgent')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    
    # Recipients
    to_email = models.EmailField(_('to email'))
    to_name = models.CharField(_('to name'), max_length=100, blank=True)
    cc_emails = models.JSONField(_('CC emails'), default=list, blank=True)
    bcc_emails = models.JSONField(_('BCC emails'), default=list, blank=True)
    
    # Sender
    from_email = models.EmailField(_('from email'))
    from_name = models.CharField(_('from name'), max_length=100, blank=True)
    reply_to = models.EmailField(_('reply to'), blank=True)
    
    # Content
    subject = models.CharField(_('subject'), max_length=200)
    html_content = models.TextField(_('HTML content'))
    text_content = models.TextField(_('text content'), blank=True)
    
    # Context data used for rendering
    context_data = models.JSONField(_('context data'), default=dict, blank=True)
    
    # Attachments
    attachments = models.JSONField(_('attachments'), default=list, blank=True)
    
    # Delivery
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    
    # Scheduling
    scheduled_for = models.DateTimeField(_('scheduled for'), default=timezone.now)
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    opened_at = models.DateTimeField(_('opened at'), null=True, blank=True)
    clicked_at = models.DateTimeField(_('clicked at'), null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(_('error message'), blank=True)
    retry_count = models.PositiveIntegerField(_('retry count'), default=0)
    max_retries = models.PositiveIntegerField(_('max retries'), default=3)
    
    # Tracking
    provider_message_id = models.CharField(_('provider message ID'), max_length=200, blank=True)
    tracking_pixel_url = models.URLField(_('tracking pixel URL'), blank=True)
    unsubscribe_url = models.URLField(_('unsubscribe URL'), blank=True)
    
    # Related objects
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_emails')
    related_object_type = models.CharField(_('related object type'), max_length=50, blank=True)
    related_object_id = models.UUIDField(_('related object ID'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_emails')
    
    class Meta:
        verbose_name = _('Email Message')
        verbose_name_plural = _('Email Messages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['to_email', 'created_at']),
            models.Index(fields=['organization', 'template', 'status']),
        ]
    
    def __str__(self):
        return f"{self.subject} → {self.to_email} ({self.status})"
    
    def mark_as_sent(self, provider_message_id=''):
        """Mark email as sent."""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.provider_message_id = provider_message_id
        self.save(update_fields=['status', 'sent_at', 'provider_message_id'])
    
    def mark_as_delivered(self):
        """Mark email as delivered."""
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_opened(self):
        """Mark email as opened."""
        if self.status in ['SENT', 'DELIVERED']:
            self.status = 'OPENED'
            self.opened_at = timezone.now()
            self.save(update_fields=['status', 'opened_at'])
    
    def mark_as_clicked(self):
        """Mark email as clicked."""
        if self.status in ['SENT', 'DELIVERED', 'OPENED']:
            self.status = 'CLICKED'
            self.clicked_at = timezone.now()
            self.save(update_fields=['status', 'clicked_at'])
    
    def mark_as_failed(self, error_message):
        """Mark email as failed."""
        self.status = 'FAILED'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count'])
    
    def can_retry(self):
        """Check if email can be retried."""
        return self.status == 'FAILED' and self.retry_count < self.max_retries
    
    def get_tracking_data(self):
        """Get email tracking data."""
        return {
            'sent': bool(self.sent_at),
            'delivered': bool(self.delivered_at),
            'opened': bool(self.opened_at),
            'clicked': bool(self.clicked_at),
            'delivery_time': (self.delivered_at - self.sent_at).total_seconds() if self.sent_at and self.delivered_at else None,
        }


class EmailCampaign(BaseTenantModel):
    """
    Email campaigns for bulk messaging.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('SCHEDULED', _('Scheduled')),
        ('SENDING', _('Sending')),
        ('SENT', _('Sent')),
        ('PAUSED', _('Paused')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('campaign name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='campaigns')
    
    # Recipients
    recipient_list = models.JSONField(_('recipient list'), default=list)
    recipient_filter = models.JSONField(_('recipient filter'), default=dict, blank=True)
    
    # Scheduling
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    scheduled_for = models.DateTimeField(_('scheduled for'), null=True, blank=True)
    
    # Delivery settings
    send_immediately = models.BooleanField(_('send immediately'), default=False)
    batch_size = models.PositiveIntegerField(_('batch size'), default=100)
    delay_between_batches = models.PositiveIntegerField(_('delay between batches (seconds)'), default=60)
    
    # Tracking
    total_recipients = models.PositiveIntegerField(_('total recipients'), default=0)
    emails_sent = models.PositiveIntegerField(_('emails sent'), default=0)
    emails_delivered = models.PositiveIntegerField(_('emails delivered'), default=0)
    emails_opened = models.PositiveIntegerField(_('emails opened'), default=0)
    emails_clicked = models.PositiveIntegerField(_('emails clicked'), default=0)
    emails_failed = models.PositiveIntegerField(_('emails failed'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Email Campaign')
        verbose_name_plural = _('Email Campaigns')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def open_rate(self):
        """Calculate email open rate."""
        if self.emails_delivered == 0:
            return 0
        return (self.emails_opened / self.emails_delivered) * 100
    
    @property
    def click_rate(self):
        """Calculate email click rate."""
        if self.emails_delivered == 0:
            return 0
        return (self.emails_clicked / self.emails_delivered) * 100
    
    @property
    def delivery_rate(self):
        """Calculate email delivery rate."""
        if self.emails_sent == 0:
            return 0
        return (self.emails_delivered / self.emails_sent) * 100
    
    def start_campaign(self):
        """Start the email campaign."""
        if self.status == 'DRAFT':
            self.status = 'SCHEDULED' if self.scheduled_for else 'SENDING'
            self.save()
            
            # Trigger campaign sending
            from .tasks import send_email_campaign
            send_email_campaign.delay(self.id)
    
    def pause_campaign(self):
        """Pause the email campaign."""
        if self.status in ['SCHEDULED', 'SENDING']:
            self.status = 'PAUSED'
            self.save()
    
    def cancel_campaign(self):
        """Cancel the email campaign."""
        if self.status in ['DRAFT', 'SCHEDULED', 'PAUSED']:
            self.status = 'CANCELLED'
            self.save()


class EmailSubscription(BaseTenantModel):
    """
    User email subscription preferences.
    """
    
    SUBSCRIPTION_TYPES = [
        ('ASSESSMENT_NOTIFICATIONS', _('Assessment Notifications')),
        ('PDI_NOTIFICATIONS', _('PDI Notifications')),
        ('RECRUITING_NOTIFICATIONS', _('Recruiting Notifications')),
        ('BILLING_NOTIFICATIONS', _('Billing Notifications')),
        ('SYSTEM_NOTIFICATIONS', _('System Notifications')),
        ('MARKETING_EMAILS', _('Marketing Emails')),
        ('NEWSLETTER', _('Newsletter')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_subscriptions')
    subscription_type = models.CharField(_('subscription type'), max_length=30, choices=SUBSCRIPTION_TYPES)
    
    # Preferences
    is_subscribed = models.BooleanField(_('subscribed'), default=True)
    frequency = models.CharField(
        _('frequency'),
        max_length=20,
        choices=[
            ('IMMEDIATE', _('Immediate')),
            ('DAILY', _('Daily Digest')),
            ('WEEKLY', _('Weekly Digest')),
            ('MONTHLY', _('Monthly Digest')),
            ('NEVER', _('Never')),
        ],
        default='IMMEDIATE'
    )
    
    # Unsubscribe tracking
    unsubscribed_at = models.DateTimeField(_('unsubscribed at'), null=True, blank=True)
    unsubscribe_reason = models.CharField(_('unsubscribe reason'), max_length=200, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Email Subscription')
        verbose_name_plural = _('Email Subscriptions')
        unique_together = ['user', 'organization', 'subscription_type']
        ordering = ['user', 'subscription_type']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_subscription_type_display()} ({self.get_frequency_display()})"
    
    def unsubscribe(self, reason=''):
        """Unsubscribe user from this type."""
        self.is_subscribed = False
        self.unsubscribed_at = timezone.now()
        self.unsubscribe_reason = reason
        self.save()
    
    def resubscribe(self):
        """Resubscribe user to this type."""
        self.is_subscribed = True
        self.unsubscribed_at = None
        self.unsubscribe_reason = ''
        self.save()


class EmailLog(models.Model):
    """
    Comprehensive email delivery logs.
    """
    
    EVENT_TYPES = [
        ('QUEUED', _('Queued')),
        ('SENT', _('Sent')),
        ('DELIVERED', _('Delivered')),
        ('OPENED', _('Opened')),
        ('CLICKED', _('Clicked')),
        ('BOUNCED', _('Bounced')),
        ('COMPLAINED', _('Complained')),
        ('UNSUBSCRIBED', _('Unsubscribed')),
        ('FAILED', _('Failed')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='logs')
    
    # Event details
    event_type = models.CharField(_('event type'), max_length=20, choices=EVENT_TYPES)
    event_data = models.JSONField(_('event data'), default=dict, blank=True)
    
    # Provider details
    provider = models.CharField(_('email provider'), max_length=50, blank=True)
    provider_event_id = models.CharField(_('provider event ID'), max_length=200, blank=True)
    
    # User agent and tracking
    user_agent = models.TextField(_('user agent'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Email Log')
        verbose_name_plural = _('Email Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['email_message', 'event_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.email_message.to_email}"


class EmailAttachment(models.Model):
    """
    Email attachments.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='attachment_files')
    
    # File details
    file = models.FileField(_('file'), upload_to='email_attachments/')
    filename = models.CharField(_('filename'), max_length=255)
    content_type = models.CharField(_('content type'), max_length=100)
    file_size = models.PositiveIntegerField(_('file size (bytes)'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Email Attachment')
        verbose_name_plural = _('Email Attachments')
    
    def __str__(self):
        return f"{self.filename} ({self.file_size} bytes)"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.filename:
                self.filename = self.file.name
        super().save(*args, **kwargs)


class EmailQueue(models.Model):
    """
    Email queue for batch processing.
    """
    
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Queue details
    name = models.CharField(_('queue name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Processing
    total_emails = models.PositiveIntegerField(_('total emails'), default=0)
    processed_emails = models.PositiveIntegerField(_('processed emails'), default=0)
    failed_emails = models.PositiveIntegerField(_('failed emails'), default=0)
    
    # Timing
    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    # Configuration
    batch_size = models.PositiveIntegerField(_('batch size'), default=100)
    delay_between_batches = models.PositiveIntegerField(_('delay between batches (seconds)'), default=60)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Email Queue')
        verbose_name_plural = _('Email Queues')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.processed_emails}/{self.total_emails})"
    
    @property
    def progress_percentage(self):
        """Calculate processing progress."""
        if self.total_emails == 0:
            return 0
        return (self.processed_emails / self.total_emails) * 100
    
    def start_processing(self):
        """Start queue processing."""
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.save()
    
    def mark_as_completed(self):
        """Mark queue as completed."""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()


class EmailAnalytics(BaseTenantModel):
    """
    Email analytics and performance metrics.
    """
    
    PERIOD_TYPES = [
        ('DAILY', _('Daily')),
        ('WEEKLY', _('Weekly')),
        ('MONTHLY', _('Monthly')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_type = models.CharField(_('period type'), max_length=20, choices=PERIOD_TYPES)
    period_start = models.DateTimeField(_('period start'))
    period_end = models.DateTimeField(_('period end'))
    
    # Email metrics
    emails_sent = models.PositiveIntegerField(_('emails sent'), default=0)
    emails_delivered = models.PositiveIntegerField(_('emails delivered'), default=0)
    emails_opened = models.PositiveIntegerField(_('emails opened'), default=0)
    emails_clicked = models.PositiveIntegerField(_('emails clicked'), default=0)
    emails_bounced = models.PositiveIntegerField(_('emails bounced'), default=0)
    emails_complained = models.PositiveIntegerField(_('emails complained'), default=0)
    emails_unsubscribed = models.PositiveIntegerField(_('emails unsubscribed'), default=0)
    
    # Calculated rates
    delivery_rate = models.FloatField(_('delivery rate'), default=0.0)
    open_rate = models.FloatField(_('open rate'), default=0.0)
    click_rate = models.FloatField(_('click rate'), default=0.0)
    bounce_rate = models.FloatField(_('bounce rate'), default=0.0)
    complaint_rate = models.FloatField(_('complaint rate'), default=0.0)
    unsubscribe_rate = models.FloatField(_('unsubscribe rate'), default=0.0)
    
    # Template performance
    template_performance = models.JSONField(_('template performance'), default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Email Analytics')
        verbose_name_plural = _('Email Analytics')
        unique_together = ['organization', 'period_type', 'period_start']
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_period_type_display()} - {self.period_start.date()}"
    
    def calculate_rates(self):
        """Calculate all performance rates."""
        if self.emails_sent > 0:
            self.delivery_rate = (self.emails_delivered / self.emails_sent) * 100
            self.bounce_rate = (self.emails_bounced / self.emails_sent) * 100
            self.complaint_rate = (self.emails_complained / self.emails_sent) * 100
            self.unsubscribe_rate = (self.emails_unsubscribed / self.emails_sent) * 100
        
        if self.emails_delivered > 0:
            self.open_rate = (self.emails_opened / self.emails_delivered) * 100
            self.click_rate = (self.emails_clicked / self.emails_delivered) * 100
        
        self.save()


class UnsubscribeRequest(models.Model):
    """
    Unsubscribe requests and preferences.
    """
    
    UNSUBSCRIBE_TYPES = [
        ('ALL', _('All Emails')),
        ('MARKETING', _('Marketing Only')),
        ('NOTIFICATIONS', _('Notifications Only')),
        ('SPECIFIC_TYPE', _('Specific Type')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='unsubscribe_requests')
    
    # Unsubscribe details
    unsubscribe_type = models.CharField(_('unsubscribe type'), max_length=20, choices=UNSUBSCRIBE_TYPES)
    specific_types = models.JSONField(_('specific types'), default=list, blank=True)
    reason = models.CharField(_('reason'), max_length=200, blank=True)
    feedback = models.TextField(_('feedback'), blank=True)
    
    # Source tracking
    source_email = models.ForeignKey(EmailMessage, on_delete=models.SET_NULL, null=True, blank=True)
    source_campaign = models.ForeignKey(EmailCampaign, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Processing
    is_processed = models.BooleanField(_('processed'), default=False)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    class Meta:
        verbose_name = _('Unsubscribe Request')
        verbose_name_plural = _('Unsubscribe Requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - {self.get_unsubscribe_type_display()}"
    
    def process_unsubscribe(self):
        """Process the unsubscribe request."""
        if self.is_processed:
            return
        
        if self.user:
            if self.unsubscribe_type == 'ALL':
                # Unsubscribe from all email types
                EmailSubscription.objects.filter(
                    user=self.user
                ).update(is_subscribed=False, unsubscribed_at=timezone.now())
            
            elif self.unsubscribe_type == 'MARKETING':
                # Unsubscribe from marketing emails only
                EmailSubscription.objects.filter(
                    user=self.user,
                    subscription_type__in=['MARKETING_EMAILS', 'NEWSLETTER']
                ).update(is_subscribed=False, unsubscribed_at=timezone.now())
            
            elif self.unsubscribe_type == 'SPECIFIC_TYPE':
                # Unsubscribe from specific types
                EmailSubscription.objects.filter(
                    user=self.user,
                    subscription_type__in=self.specific_types
                ).update(is_subscribed=False, unsubscribed_at=timezone.now())
        
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save()


class EmailProvider(models.Model):
    """
    Email provider configurations.
    """
    
    PROVIDER_TYPES = [
        ('SMTP', _('SMTP Server')),
        ('SENDGRID', _('SendGrid')),
        ('MAILGUN', _('Mailgun')),
        ('SES', _('Amazon SES')),
        ('POSTMARK', _('Postmark')),
        ('MANDRILL', _('Mandrill')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('provider name'), max_length=100)
    provider_type = models.CharField(_('provider type'), max_length=20, choices=PROVIDER_TYPES)
    
    # Configuration
    configuration = models.JSONField(_('configuration'), default=dict)
    api_key = models.CharField(_('API key'), max_length=500, blank=True)
    webhook_secret = models.CharField(_('webhook secret'), max_length=200, blank=True)
    
    # Limits and quotas
    daily_limit = models.PositiveIntegerField(_('daily limit'), default=1000)
    monthly_limit = models.PositiveIntegerField(_('monthly limit'), default=10000)
    rate_limit_per_minute = models.PositiveIntegerField(_('rate limit per minute'), default=100)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_default = models.BooleanField(_('default provider'), default=False)
    
    # Health monitoring
    last_health_check = models.DateTimeField(_('last health check'), null=True, blank=True)
    is_healthy = models.BooleanField(_('healthy'), default=True)
    health_check_error = models.TextField(_('health check error'), blank=True)
    
    # Usage tracking
    emails_sent_today = models.PositiveIntegerField(_('emails sent today'), default=0)
    emails_sent_this_month = models.PositiveIntegerField(_('emails sent this month'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Email Provider')
        verbose_name_plural = _('Email Providers')
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default provider
        if self.is_default:
            EmailProvider.objects.filter(is_default=True).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def can_send_email(self):
        """Check if provider can send email based on limits."""
        if not self.is_active or not self.is_healthy:
            return False
        
        if self.emails_sent_today >= self.daily_limit:
            return False
        
        if self.emails_sent_this_month >= self.monthly_limit:
            return False
        
        return True
    
    def increment_usage(self):
        """Increment usage counters."""
        self.emails_sent_today += 1
        self.emails_sent_this_month += 1
        self.save(update_fields=['emails_sent_today', 'emails_sent_this_month'])
    
    def reset_daily_usage(self):
        """Reset daily usage counter."""
        self.emails_sent_today = 0
        self.save(update_fields=['emails_sent_today'])
    
    def reset_monthly_usage(self):
        """Reset monthly usage counter."""
        self.emails_sent_this_month = 0
        self.save(update_fields=['emails_sent_this_month'])


class EmailBlacklist(models.Model):
    """
    Email blacklist for bounced and complained addresses.
    """
    
    BLACKLIST_TYPES = [
        ('BOUNCE', _('Bounced')),
        ('COMPLAINT', _('Complaint')),
        ('MANUAL', _('Manual')),
        ('UNSUBSCRIBE', _('Unsubscribed')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    blacklist_type = models.CharField(_('blacklist type'), max_length=20, choices=BLACKLIST_TYPES)
    
    # Details
    reason = models.CharField(_('reason'), max_length=500, blank=True)
    bounce_type = models.CharField(_('bounce type'), max_length=50, blank=True)  # hard, soft, etc.
    
    # Source tracking
    source_email = models.ForeignKey(EmailMessage, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Email Blacklist')
        verbose_name_plural = _('Email Blacklist')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({self.get_blacklist_type_display()})"
    
    @classmethod
    def is_blacklisted(cls, email):
        """Check if email is blacklisted."""
        return cls.objects.filter(email=email, is_active=True).exists()
    
    @classmethod
    def add_to_blacklist(cls, email, blacklist_type, reason='', source_email=None):
        """Add email to blacklist."""
        blacklist_entry, created = cls.objects.get_or_create(
            email=email,
            defaults={
                'blacklist_type': blacklist_type,
                'reason': reason,
                'source_email': source_email,
            }
        )
        
        if not created:
            # Update existing entry
            blacklist_entry.blacklist_type = blacklist_type
            blacklist_entry.reason = reason
            blacklist_entry.is_active = True
            blacklist_entry.save()
        
        return blacklist_entry