"""
Admin configuration for emails app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    EmailTemplate, EmailMessage, EmailCampaign, EmailSubscription,
    EmailLog, EmailAttachment, EmailQueue, EmailAnalytics,
    UnsubscribeRequest, EmailProvider, EmailBlacklist
)


class EmailLogInline(admin.TabularInline):
    model = EmailLog
    extra = 0
    fields = ['event_type', 'timestamp', 'ip_address', 'user_agent']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']


class EmailAttachmentInline(admin.TabularInline):
    model = EmailAttachment
    extra = 0
    fields = ['filename', 'content_type', 'file_size', 'created_at']
    readonly_fields = ['file_size', 'created_at']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'language', 'is_default', 'is_active', 'organization', 'created_at']
    list_filter = ['template_type', 'language', 'is_default', 'is_active', 'organization', 'created_at']
    search_fields = ['name', 'subject', 'html_content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template_type', 'language', 'organization')
        }),
        ('Email Content', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Template Configuration', {
            'fields': ('available_variables', 'sample_context')
        }),
        ('Sender Configuration', {
            'fields': ('from_email', 'from_name', 'reply_to')
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'to_email', 'status', 'priority', 'scheduled_for', 'sent_at', 'organization']
    list_filter = ['status', 'priority', 'template__template_type', 'organization', 'created_at']
    search_fields = ['subject', 'to_email', 'to_name', 'html_content']
    readonly_fields = ['id', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'created_at', 'updated_at']
    inlines = [EmailLogInline, EmailAttachmentInline]
    
    fieldsets = (
        (None, {
            'fields': ('template', 'organization')
        }),
        ('Recipients', {
            'fields': ('to_email', 'to_name', 'cc_emails', 'bcc_emails')
        }),
        ('Sender', {
            'fields': ('from_email', 'from_name', 'reply_to')
        }),
        ('Content', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Context & Attachments', {
            'fields': ('context_data', 'attachments'),
            'classes': ('collapse',)
        }),
        ('Delivery', {
            'fields': ('status', 'priority', 'scheduled_for')
        }),
        ('Tracking', {
            'fields': ('sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'provider_message_id'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('Related Objects', {
            'fields': ('user', 'related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def resend_email(self, request, queryset):
        """Resend selected emails."""
        from .tasks import send_email_message
        
        resent_count = 0
        for email in queryset.filter(status='FAILED'):
            if email.can_retry():
                email.status = 'QUEUED'
                email.save()
                send_email_message.delay(email.id)
                resent_count += 1
        
        self.message_user(request, f'{resent_count} emails queued for resending.')
    resend_email.short_description = 'Resend selected failed emails'
    
    actions = [resend_email]


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'status', 'total_recipients', 'emails_sent', 'open_rate_display', 'click_rate_display', 'organization']
    list_filter = ['status', 'template__template_type', 'organization', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['total_recipients', 'emails_sent', 'emails_delivered', 'emails_opened', 'emails_clicked', 'emails_failed', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'template', 'organization')
        }),
        ('Recipients', {
            'fields': ('recipient_list', 'recipient_filter')
        }),
        ('Scheduling', {
            'fields': ('status', 'scheduled_for', 'send_immediately')
        }),
        ('Delivery Settings', {
            'fields': ('batch_size', 'delay_between_batches')
        }),
        ('Tracking', {
            'fields': ('total_recipients', 'emails_sent', 'emails_delivered', 'emails_opened', 'emails_clicked', 'emails_failed'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def open_rate_display(self, obj):
        return f"{obj.open_rate:.1f}%"
    open_rate_display.short_description = 'Open Rate'
    
    def click_rate_display(self, obj):
        return f"{obj.click_rate:.1f}%"
    click_rate_display.short_description = 'Click Rate'
    
    def start_campaign(self, request, queryset):
        """Start selected campaigns."""
        started_count = 0
        for campaign in queryset.filter(status='DRAFT'):
            campaign.start_campaign()
            started_count += 1
        
        self.message_user(request, f'{started_count} campaigns started.')
    start_campaign.short_description = 'Start selected campaigns'
    
    actions = [start_campaign]


@admin.register(EmailSubscription)
class EmailSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_type', 'is_subscribed', 'frequency', 'organization', 'created_at']
    list_filter = ['subscription_type', 'is_subscribed', 'frequency', 'organization', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['unsubscribed_at', 'created_at', 'updated_at']
    
    def bulk_unsubscribe(self, request, queryset):
        """Bulk unsubscribe selected subscriptions."""
        updated = queryset.update(
            is_subscribed=False,
            unsubscribed_at=timezone.now(),
            unsubscribe_reason='Bulk admin action'
        )
        self.message_user(request, f'{updated} subscriptions unsubscribed.')
    bulk_unsubscribe.short_description = 'Unsubscribe selected users'
    
    def bulk_resubscribe(self, request, queryset):
        """Bulk resubscribe selected subscriptions."""
        updated = queryset.update(
            is_subscribed=True,
            unsubscribed_at=None,
            unsubscribe_reason=''
        )
        self.message_user(request, f'{updated} subscriptions reactivated.')
    bulk_resubscribe.short_description = 'Resubscribe selected users'
    
    actions = [bulk_unsubscribe, bulk_resubscribe]


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['email_subject', 'to_email', 'event_type', 'timestamp', 'provider']
    list_filter = ['event_type', 'provider', 'timestamp']
    search_fields = ['email_message__subject', 'email_message__to_email']
    readonly_fields = ['timestamp']
    
    def email_subject(self, obj):
        return obj.email_message.subject
    email_subject.short_description = 'Subject'
    
    def to_email(self, obj):
        return obj.email_message.to_email
    to_email.short_description = 'To Email'


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'progress_display', 'total_emails', 'failed_emails', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['progress_percentage', 'started_at', 'completed_at', 'created_at', 'updated_at']
    
    def progress_display(self, obj):
        percentage = obj.progress_percentage
        if percentage >= 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'blue'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{:.1f}%</div></div>',
            percentage, color, percentage
        )
    progress_display.short_description = 'Progress'


@admin.register(EmailAnalytics)
class EmailAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['organization', 'period_type', 'period_start', 'emails_sent', 'delivery_rate_display', 'open_rate_display', 'click_rate_display']
    list_filter = ['period_type', 'organization', 'period_start']
    search_fields = ['organization__name']
    readonly_fields = ['delivery_rate', 'open_rate', 'click_rate', 'bounce_rate', 'complaint_rate', 'unsubscribe_rate', 'created_at']
    
    def delivery_rate_display(self, obj):
        return f"{obj.delivery_rate:.1f}%"
    delivery_rate_display.short_description = 'Delivery Rate'
    
    def open_rate_display(self, obj):
        return f"{obj.open_rate:.1f}%"
    open_rate_display.short_description = 'Open Rate'
    
    def click_rate_display(self, obj):
        return f"{obj.click_rate:.1f}%"
    click_rate_display.short_description = 'Click Rate'


@admin.register(UnsubscribeRequest)
class UnsubscribeRequestAdmin(admin.ModelAdmin):
    list_display = ['email', 'unsubscribe_type', 'is_processed', 'created_at']
    list_filter = ['unsubscribe_type', 'is_processed', 'created_at']
    search_fields = ['email', 'reason', 'feedback']
    readonly_fields = ['processed_at', 'created_at']
    
    def process_unsubscribe_requests(self, request, queryset):
        """Process selected unsubscribe requests."""
        processed_count = 0
        for unsubscribe_request in queryset.filter(is_processed=False):
            unsubscribe_request.process_unsubscribe()
            processed_count += 1
        
        self.message_user(request, f'{processed_count} unsubscribe requests processed.')
    process_unsubscribe_requests.short_description = 'Process selected unsubscribe requests'
    
    actions = [process_unsubscribe_requests]


@admin.register(EmailProvider)
class EmailProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_default', 'is_active', 'is_healthy', 'emails_sent_today', 'daily_limit']
    list_filter = ['provider_type', 'is_default', 'is_active', 'is_healthy']
    search_fields = ['name']
    readonly_fields = ['emails_sent_today', 'emails_sent_this_month', 'last_health_check', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'provider_type')
        }),
        ('Configuration', {
            'fields': ('configuration', 'api_key', 'webhook_secret')
        }),
        ('Limits & Quotas', {
            'fields': ('daily_limit', 'monthly_limit', 'rate_limit_per_minute')
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
        ('Health Monitoring', {
            'fields': ('last_health_check', 'is_healthy', 'health_check_error')
        }),
        ('Usage Tracking', {
            'fields': ('emails_sent_today', 'emails_sent_this_month'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def test_provider(self, request, queryset):
        """Test selected email providers."""
        from .tasks import test_email_provider
        
        for provider in queryset:
            test_email_provider.delay(provider.id)
        
        self.message_user(request, f'Health check started for {queryset.count()} providers.')
    test_provider.short_description = 'Test selected providers'
    
    actions = [test_provider]


@admin.register(EmailBlacklist)
class EmailBlacklistAdmin(admin.ModelAdmin):
    list_display = ['email', 'blacklist_type', 'reason', 'is_active', 'created_at']
    list_filter = ['blacklist_type', 'is_active', 'created_at']
    search_fields = ['email', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    
    def remove_from_blacklist(self, request, queryset):
        """Remove selected emails from blacklist."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} emails removed from blacklist.')
    remove_from_blacklist.short_description = 'Remove from blacklist'
    
    actions = [remove_from_blacklist]