"""
Admin configuration for billing app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Plan, Subscription, UsageMeter, Invoice, InvoiceItem, PaymentMethod,
    Payment, WebhookEvent, BillingAddress, Coupon, CouponUsage, BillingNotification
)


class UsageMeterInline(admin.TabularInline):
    model = UsageMeter
    extra = 0
    fields = ['usage_type', 'current_usage', 'limit', 'overage_usage', 'overage_cost']
    readonly_fields = ['current_usage', 'overage_usage', 'overage_cost']


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    fields = ['invoice_number', 'status', 'total_amount', 'due_date', 'paid_at']
    readonly_fields = ['invoice_number', 'total_amount', 'paid_at']


class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_monthly', 'max_assessments_per_month', 'max_team_members', 'is_active', 'is_public']
    list_filter = ['plan_type', 'is_active', 'is_public', 'includes_pdi', 'includes_recruiting']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'plan_type')
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_quarterly', 'price_yearly', 'currency')
        }),
        ('Usage Limits', {
            'fields': ('max_assessments_per_month', 'max_team_members', 'max_organizations', 'max_storage_gb')
        }),
        ('Features', {
            'fields': ('includes_pdi', 'includes_recruiting', 'includes_advanced_reports', 
                      'includes_api_access', 'includes_white_labeling', 'includes_priority_support')
        }),
        ('Provider Integration', {
            'fields': ('paypal_plan_id_monthly', 'paypal_plan_id_quarterly', 'paypal_plan_id_yearly',
                      'stripe_price_id_monthly', 'stripe_price_id_quarterly', 'stripe_price_id_yearly'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_public', 'sort_order')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan', 'status', 'billing_cycle', 'amount', 'current_period_end', 'provider']
    list_filter = ['status', 'billing_cycle', 'provider', 'plan', 'organization', 'created_at']
    search_fields = ['organization__name', 'plan__name', 'provider_subscription_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [UsageMeterInline, InvoiceInline]
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'plan', 'billing_cycle', 'status')
        }),
        ('Provider Integration', {
            'fields': ('provider', 'provider_subscription_id', 'provider_customer_id')
        }),
        ('Billing Period', {
            'fields': ('current_period_start', 'current_period_end')
        }),
        ('Trial', {
            'fields': ('trial_start', 'trial_end'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('amount', 'currency')
        }),
        ('Cancellation', {
            'fields': ('cancel_at_period_end', 'cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class UsageMeterAdmin(admin.ModelAdmin):
    list_display = ['organization', 'usage_type', 'current_usage', 'limit', 'usage_percentage_display', 'is_over_limit']
    list_filter = ['usage_type', 'subscription__plan', 'organization', 'period_start']
    search_fields = ['organization__name', 'subscription__plan__name']
    readonly_fields = ['overage_cost', 'created_at', 'updated_at']
    
    def usage_percentage_display(self, obj):
        percentage = obj.usage_percentage
        if percentage >= 100:
            color = 'red'
        elif percentage >= 80:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, percentage
        )
    usage_percentage_display.short_description = 'Usage %'


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ['item_type', 'description', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['amount', 'status', 'provider', 'created_at']
    readonly_fields = ['created_at']


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'organization', 'status', 'total_amount', 'due_date', 'paid_at']
    list_filter = ['status', 'provider', 'organization', 'due_date', 'created_at']
    search_fields = ['invoice_number', 'organization__name', 'provider_invoice_id']
    readonly_fields = ['invoice_number', 'id', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline, PaymentInline]
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'subscription', 'invoice_number', 'status')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'currency')
        }),
        ('Billing Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Payment', {
            'fields': ('due_date', 'paid_at', 'payment_method')
        }),
        ('Provider', {
            'fields': ('provider', 'provider_invoice_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['organization', 'method_type', 'masked_details', 'is_default', 'is_active', 'provider']
    list_filter = ['method_type', 'provider', 'is_default', 'is_active', 'organization']
    search_fields = ['organization__name', 'card_last_four', 'bank_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def masked_details(self, obj):
        if obj.method_type in ['CREDIT_CARD', 'DEBIT_CARD'] and obj.card_last_four:
            return f"****{obj.card_last_four} ({obj.card_brand})"
        elif obj.method_type == 'BANK_ACCOUNT' and obj.account_last_four:
            return f"{obj.bank_name} ****{obj.account_last_four}"
        return "—"
    masked_details.short_description = 'Details'


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['organization', 'amount', 'status', 'provider', 'invoice', 'created_at']
    list_filter = ['status', 'provider', 'organization', 'created_at']
    search_fields = ['organization__name', 'provider_payment_id', 'invoice__invoice_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'invoice', 'payment_method')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'status', 'description')
        }),
        ('Provider', {
            'fields': ('provider', 'provider_payment_id', 'provider_charge_id')
        }),
        ('Failure/Refund', {
            'fields': ('failure_reason', 'refunded_amount', 'refund_reason'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['provider', 'event_type', 'status', 'retry_count', 'created_at']
    list_filter = ['provider', 'status', 'event_type', 'created_at']
    search_fields = ['provider_event_id', 'event_type']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processed_at']
    
    fieldsets = (
        (None, {
            'fields': ('provider', 'event_type', 'provider_event_id', 'status')
        }),
        ('Processing', {
            'fields': ('processed_at', 'error_message', 'retry_count')
        }),
        ('Data', {
            'fields': ('raw_data', 'processed_data'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def reprocess_webhook(self, request, queryset):
        """Reprocess selected webhook events."""
        for webhook in queryset:
            # TODO: Implement webhook reprocessing
            webhook.status = 'PENDING'
            webhook.error_message = ''
            webhook.save()
        
        self.message_user(request, f'{queryset.count()} webhooks marked for reprocessing.')
    reprocess_webhook.short_description = 'Reprocess selected webhooks'
    
    actions = [reprocess_webhook]


class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ['organization', 'company_name', 'city', 'state', 'country', 'is_default']
    list_filter = ['country', 'state', 'is_default', 'organization']
    search_fields = ['organization__name', 'company_name', 'city']
    readonly_fields = ['id', 'created_at', 'updated_at']


class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'discount_type', 'discount_value', 'uses_count', 'max_uses', 'is_valid_display', 'is_active']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['id', 'uses_count', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_plans']
    
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description')
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value', 'currency')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'max_uses', 'uses_count')
        }),
        ('Restrictions', {
            'fields': ('min_amount', 'applicable_plans', 'first_time_customers_only')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_valid_display(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Invalid</span>')
    is_valid_display.short_description = 'Valid'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'organization', 'original_amount', 'discount_amount', 'final_amount', 'used_at']
    list_filter = ['coupon', 'organization', 'used_at']
    search_fields = ['coupon__code', 'organization__name']
    readonly_fields = ['used_at']


class BillingNotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'recipient_email', 'status', 'scheduled_for', 'sent_at']
    list_filter = ['notification_type', 'status', 'organization', 'scheduled_for']
    search_fields = ['recipient_email', 'subject', 'organization__name']
    readonly_fields = ['sent_at']
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'notification_type', 'recipient_email')
        }),
        ('Content', {
            'fields': ('subject', 'message')
        }),
        ('Related Objects', {
            'fields': ('subscription', 'invoice', 'payment'),
            'classes': ('collapse',)
        }),
        ('Delivery', {
            'fields': ('status', 'scheduled_for', 'sent_at', 'error_message')
        })
    )
    
    def resend_notification(self, request, queryset):
        """Resend selected notifications."""
        queryset.update(status='PENDING', error_message='')
        self.message_user(request, f'{queryset.count()} notifications marked for resending.')
    resend_notification.short_description = 'Resend selected notifications'
    
    actions = [resend_notification]


# Register models with the admin site
admin.site.register(Plan, PlanAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(UsageMeter, UsageMeterAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(WebhookEvent, WebhookEventAdmin)
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(CouponUsage, CouponUsageAdmin)
admin.site.register(BillingNotification, BillingNotificationAdmin)