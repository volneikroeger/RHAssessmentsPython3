"""
Admin configuration for reports app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Report, ReportTemplate, ReportSchedule, ReportMetric, Dashboard,
    ReportSubscription, ReportExport, AnalyticsSnapshot, ReportChart,
    ReportComment, ReportBookmark
)


class ReportMetricInline(admin.TabularInline):
    model = ReportMetric
    extra = 0
    fields = ['name', 'metric_type', 'value', 'unit', 'chart_type']
    readonly_fields = ['calculated_at']


class ReportChartInline(admin.TabularInline):
    model = ReportChart
    extra = 0
    fields = ['title', 'chart_type', 'width', 'height', 'order']
    ordering = ['order']


class ReportCommentInline(admin.TabularInline):
    model = ReportComment
    extra = 0
    fields = ['author', 'content', 'is_internal', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'format', 'status', 'generated_by', 'generation_completed_at', 'organization']
    list_filter = ['report_type', 'format', 'status', 'organization', 'created_at']
    search_fields = ['title', 'description', 'generated_by__email']
    readonly_fields = ['id', 'generation_started_at', 'generation_completed_at', 'generation_duration']
    inlines = [ReportMetricInline, ReportChartInline, ReportCommentInline]
    filter_horizontal = ['shared_with']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'report_type', 'format', 'status', 'organization')
        }),
        ('Scope & Filters', {
            'fields': ('date_from', 'date_to', 'filters')
        }),
        ('Content', {
            'fields': ('content', 'data', 'file_path', 'file_size')
        }),
        ('Access Control', {
            'fields': ('is_public', 'shared_with', 'expires_at')
        }),
        ('Generation Details', {
            'fields': ('generated_by', 'generation_started_at', 'generation_completed_at', 'generation_error'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def generation_duration(self, obj):
        duration = obj.generation_duration
        if duration:
            return f"{duration.total_seconds():.1f}s"
        return "—"
    generation_duration.short_description = 'Generation Time'


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_public', 'auto_generate', 'generation_frequency', 'is_active', 'organization']
    list_filter = ['report_type', 'is_public', 'auto_generate', 'generation_frequency', 'is_active', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'report_type', 'organization')
        }),
        ('Template Configuration', {
            'fields': ('template_config', 'default_filters', 'chart_configs')
        }),
        ('Content Structure', {
            'fields': ('sections', 'metrics')
        }),
        ('Access & Scheduling', {
            'fields': ('is_public', 'auto_generate', 'generation_frequency')
        }),
        ('Status', {
            'fields': ('is_active',)
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


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'frequency', 'is_active', 'last_generated_at', 'next_generation_at']
    list_filter = ['frequency', 'is_active', 'organization', 'last_generated_at']
    search_fields = ['name', 'template__name']
    readonly_fields = ['last_generated_at', 'next_generation_at', 'created_at', 'updated_at']
    filter_horizontal = ['recipients']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template', 'organization')
        }),
        ('Schedule Configuration', {
            'fields': ('frequency', 'day_of_week', 'day_of_month', 'time_of_day')
        }),
        ('Recipients', {
            'fields': ('recipients', 'send_to_organization_admins')
        }),
        ('Status', {
            'fields': ('is_active', 'last_generated_at', 'next_generation_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_public', 'is_active', 'refresh_interval', 'organization']
    list_filter = ['is_default', 'is_public', 'is_active', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'organization')
        }),
        ('Configuration', {
            'fields': ('layout', 'widgets', 'refresh_interval')
        }),
        ('Access Control', {
            'fields': ('is_public', 'allowed_roles')
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


@admin.register(ReportSubscription)
class ReportSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'template', 'delivery_method', 'is_active', 'last_sent_at']
    list_filter = ['delivery_method', 'is_active', 'organization', 'created_at']
    search_fields = ['user__email', 'template__name']
    readonly_fields = ['last_sent_at', 'created_at', 'updated_at']


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ['report_title', 'format', 'status', 'file_size_display', 'download_count', 'requested_by', 'created_at']
    list_filter = ['format', 'status', 'created_at']
    search_fields = ['report__title', 'requested_by__email']
    readonly_fields = ['started_at', 'completed_at', 'created_at']
    
    def report_title(self, obj):
        return obj.report.title
    report_title.short_description = 'Report'
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "—"
    file_size_display.short_description = 'File Size'


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ['organization', 'snapshot_type', 'snapshot_date', 'assessments_completed', 'pdi_plans_created', 'active_users']
    list_filter = ['snapshot_type', 'snapshot_date', 'organization']
    search_fields = ['organization__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'snapshot_type', 'snapshot_date')
        }),
        ('Assessment Metrics', {
            'fields': ('assessments_sent', 'assessments_completed', 'assessment_completion_rate', 'avg_assessment_score')
        }),
        ('PDI Metrics', {
            'fields': ('pdi_plans_created', 'pdi_plans_completed', 'avg_pdi_progress', 'overdue_pdi_tasks')
        }),
        ('Recruiting Metrics', {
            'fields': ('candidates_added', 'jobs_posted', 'applications_received', 'placements_made', 'avg_time_to_fill'),
            'classes': ('collapse',)
        }),
        ('User Engagement', {
            'fields': ('active_users', 'new_users', 'user_retention_rate')
        }),
        ('Usage Metrics', {
            'fields': ('total_logins', 'avg_session_duration', 'feature_usage'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(ReportChart)
class ReportChartAdmin(admin.ModelAdmin):
    list_display = ['report', 'title', 'chart_type', 'width', 'height', 'order']
    list_filter = ['chart_type', 'report__report_type']
    search_fields = ['title', 'report__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('report', 'title', 'chart_type')
        }),
        ('Data Configuration', {
            'fields': ('data_source', 'x_axis_field', 'y_axis_field', 'group_by_field')
        }),
        ('Chart Data', {
            'fields': ('chart_data', 'chart_options')
        }),
        ('Layout', {
            'fields': ('width', 'height', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ['report', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['content', 'author__email', 'report__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ReportBookmark)
class ReportBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'report', 'name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'report__title', 'name']
    readonly_fields = ['created_at']