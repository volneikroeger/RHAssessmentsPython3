"""
Reports models for analytics and reporting.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from core.db import BaseTenantModel

User = get_user_model()


class Report(BaseTenantModel):
    """
    Generated reports for various analytics and insights.
    """
    
    REPORT_TYPES = [
        ('ASSESSMENT_SUMMARY', _('Assessment Summary')),
        ('TEAM_PERFORMANCE', _('Team Performance')),
        ('PDI_PROGRESS', _('PDI Progress')),
        ('RECRUITING_METRICS', _('Recruiting Metrics')),
        ('USAGE_ANALYTICS', _('Usage Analytics')),
        ('ORGANIZATION_OVERVIEW', _('Organization Overview')),
        ('CUSTOM', _('Custom Report')),
    ]
    
    FORMAT_CHOICES = [
        ('HTML', _('HTML Report')),
        ('PDF', _('PDF Report')),
        ('EXCEL', _('Excel Spreadsheet')),
        ('CSV', _('CSV Data')),
        ('JSON', _('JSON Data')),
    ]
    
    STATUS_CHOICES = [
        ('GENERATING', _('Generating')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
        ('EXPIRED', _('Expired')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    report_type = models.CharField(_('report type'), max_length=30, choices=REPORT_TYPES)
    format = models.CharField(_('format'), max_length=10, choices=FORMAT_CHOICES, default='HTML')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='GENERATING')
    
    # Report scope and filters
    date_from = models.DateField(_('date from'), null=True, blank=True)
    date_to = models.DateField(_('date to'), null=True, blank=True)
    filters = models.JSONField(_('filters'), default=dict, blank=True)
    
    # Report content
    content = models.TextField(_('content'), blank=True)
    data = models.JSONField(_('report data'), default=dict, blank=True)
    file_path = models.CharField(_('file path'), max_length=500, blank=True)
    file_size = models.PositiveIntegerField(_('file size (bytes)'), default=0)
    
    # Access control
    is_public = models.BooleanField(_('public'), default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_general_reports')
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    
    # Generation details
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    generation_started_at = models.DateTimeField(_('generation started'), auto_now_add=True)
    generation_completed_at = models.DateTimeField(_('generation completed'), null=True, blank=True)
    generation_error = models.TextField(_('generation error'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_format_display()})"
    
    def get_absolute_url(self):
        return reverse('reports:detail', kwargs={'pk': self.pk})
    
    @property
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def generation_duration(self):
        if self.generation_completed_at and self.generation_started_at:
            return self.generation_completed_at - self.generation_started_at
        return None
    
    def mark_as_completed(self, file_path='', file_size=0):
        """Mark report as completed."""
        self.status = 'COMPLETED'
        self.generation_completed_at = timezone.now()
        self.file_path = file_path
        self.file_size = file_size
        self.save(update_fields=['status', 'generation_completed_at', 'file_path', 'file_size'])
    
    def mark_as_failed(self, error_message):
        """Mark report as failed."""
        self.status = 'FAILED'
        self.generation_error = error_message
        self.save(update_fields=['status', 'generation_error'])


class ReportTemplate(BaseTenantModel):
    """
    Templates for generating standardized reports.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    report_type = models.CharField(_('report type'), max_length=30, choices=Report.REPORT_TYPES)
    
    # Template configuration
    template_config = models.JSONField(_('template configuration'), default=dict)
    default_filters = models.JSONField(_('default filters'), default=dict)
    chart_configs = models.JSONField(_('chart configurations'), default=list)
    
    # Content structure
    sections = models.JSONField(_('report sections'), default=list)
    metrics = models.JSONField(_('metrics to include'), default=list)
    
    # Access and scheduling
    is_public = models.BooleanField(_('public template'), default=False)
    auto_generate = models.BooleanField(_('auto generate'), default=False)
    generation_frequency = models.CharField(
        _('generation frequency'),
        max_length=20,
        choices=[
            ('DAILY', _('Daily')),
            ('WEEKLY', _('Weekly')),
            ('MONTHLY', _('Monthly')),
            ('QUARTERLY', _('Quarterly')),
        ],
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Report Template')
        verbose_name_plural = _('Report Templates')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    def generate_report(self, user, date_from=None, date_to=None, additional_filters=None):
        """Generate a report from this template."""
        filters = self.default_filters.copy()
        if additional_filters:
            filters.update(additional_filters)
        
        report = Report.objects.create(
            organization=self.organization,
            title=f"{self.name} - {timezone.now().strftime('%Y-%m-%d')}",
            description=self.description,
            report_type=self.report_type,
            date_from=date_from,
            date_to=date_to,
            filters=filters,
            generated_by=user
        )
        
        # Trigger report generation
        from .tasks import generate_report_task
        generate_report_task.delay(report.id, self.id)
        
        return report


class ReportSchedule(BaseTenantModel):
    """
    Scheduled report generation.
    """
    
    FREQUENCY_CHOICES = [
        ('DAILY', _('Daily')),
        ('WEEKLY', _('Weekly')),
        ('MONTHLY', _('Monthly')),
        ('QUARTERLY', _('Quarterly')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(_('schedule name'), max_length=200)
    
    # Schedule configuration
    frequency = models.CharField(_('frequency'), max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.PositiveIntegerField(_('day of week'), null=True, blank=True)  # 0=Monday
    day_of_month = models.PositiveIntegerField(_('day of month'), null=True, blank=True)  # 1-31
    time_of_day = models.TimeField(_('time of day'), default='09:00')
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='report_schedules')
    send_to_organization_admins = models.BooleanField(_('send to organization admins'), default=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    last_generated_at = models.DateTimeField(_('last generated'), null=True, blank=True)
    next_generation_at = models.DateTimeField(_('next generation'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Report Schedule')
        verbose_name_plural = _('Report Schedules')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"
    
    def calculate_next_generation(self):
        """Calculate next generation time."""
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        if self.frequency == 'DAILY':
            next_gen = now.replace(hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
            if next_gen <= now:
                next_gen += timedelta(days=1)
        
        elif self.frequency == 'WEEKLY':
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_gen = now + timedelta(days=days_ahead)
            next_gen = next_gen.replace(hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
        
        elif self.frequency == 'MONTHLY':
            if now.day < self.day_of_month:
                next_gen = now.replace(day=self.day_of_month, hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
            else:
                # Next month
                if now.month == 12:
                    next_gen = now.replace(year=now.year + 1, month=1, day=self.day_of_month)
                else:
                    next_gen = now.replace(month=now.month + 1, day=self.day_of_month)
                next_gen = next_gen.replace(hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
        
        else:  # QUARTERLY
            # Simplified quarterly calculation
            next_gen = now + timedelta(days=90)
            next_gen = next_gen.replace(hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
        
        self.next_generation_at = next_gen
        self.save(update_fields=['next_generation_at'])
        
        return next_gen


class ReportMetric(models.Model):
    """
    Individual metrics within reports.
    """
    
    METRIC_TYPES = [
        ('COUNT', _('Count')),
        ('PERCENTAGE', _('Percentage')),
        ('AVERAGE', _('Average')),
        ('SUM', _('Sum')),
        ('RATIO', _('Ratio')),
        ('TREND', _('Trend')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='metrics')
    
    # Metric details
    name = models.CharField(_('metric name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    metric_type = models.CharField(_('metric type'), max_length=20, choices=METRIC_TYPES)
    
    # Values
    value = models.FloatField(_('value'))
    previous_value = models.FloatField(_('previous value'), null=True, blank=True)
    target_value = models.FloatField(_('target value'), null=True, blank=True)
    
    # Formatting
    unit = models.CharField(_('unit'), max_length=20, blank=True)
    decimal_places = models.PositiveIntegerField(_('decimal places'), default=2)
    
    # Visualization
    chart_type = models.CharField(
        _('chart type'),
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('LINE', _('Line Chart')),
            ('PIE', _('Pie Chart')),
            ('RADAR', _('Radar Chart')),
            ('GAUGE', _('Gauge')),
            ('NUMBER', _('Number Only')),
        ],
        default='NUMBER'
    )
    chart_data = models.JSONField(_('chart data'), default=dict, blank=True)
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Report Metric')
        verbose_name_plural = _('Report Metrics')
        ordering = ['report', 'name']
    
    def __str__(self):
        return f"{self.report.title} - {self.name}"
    
    @property
    def formatted_value(self):
        """Get formatted value with unit."""
        if self.metric_type == 'PERCENTAGE':
            return f"{self.value:.{self.decimal_places}f}%"
        elif self.unit:
            return f"{self.value:.{self.decimal_places}f} {self.unit}"
        else:
            return f"{self.value:.{self.decimal_places}f}"
    
    @property
    def change_percentage(self):
        """Calculate percentage change from previous value."""
        if self.previous_value and self.previous_value != 0:
            return ((self.value - self.previous_value) / self.previous_value) * 100
        return None
    
    @property
    def is_improving(self):
        """Check if metric is improving (higher is better)."""
        if self.previous_value is None:
            return None
        return self.value > self.previous_value


class Dashboard(BaseTenantModel):
    """
    Custom dashboards with multiple reports and metrics.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('dashboard name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Dashboard configuration
    layout = models.JSONField(_('layout configuration'), default=dict)
    widgets = models.JSONField(_('widget configuration'), default=list)
    refresh_interval = models.PositiveIntegerField(_('refresh interval (minutes)'), default=30)
    
    # Access control
    is_public = models.BooleanField(_('public dashboard'), default=False)
    allowed_roles = models.JSONField(_('allowed roles'), default=list)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_default = models.BooleanField(_('default dashboard'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Dashboard')
        verbose_name_plural = _('Dashboards')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one default dashboard per organization
        if self.is_default:
            Dashboard.objects.filter(
                organization=self.organization,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)


class ReportSubscription(BaseTenantModel):
    """
    User subscriptions to receive reports automatically.
    """
    
    DELIVERY_METHODS = [
        ('EMAIL', _('Email')),
        ('DASHBOARD', _('Dashboard Only')),
        ('BOTH', _('Email + Dashboard')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_subscriptions')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='subscriptions')
    
    # Delivery preferences
    delivery_method = models.CharField(_('delivery method'), max_length=20, choices=DELIVERY_METHODS, default='EMAIL')
    email_address = models.EmailField(_('email address'), blank=True)
    
    # Frequency override
    custom_frequency = models.CharField(
        _('custom frequency'),
        max_length=20,
        choices=ReportSchedule.FREQUENCY_CHOICES,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    last_sent_at = models.DateTimeField(_('last sent'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Report Subscription')
        verbose_name_plural = _('Report Subscriptions')
        unique_together = ['user', 'template']
        ordering = ['user', 'template']
    
    def __str__(self):
        return f"{self.user.full_name} → {self.template.name}"


class ReportExport(models.Model):
    """
    Export jobs for large reports.
    """
    
    STATUS_CHOICES = [
        ('QUEUED', _('Queued')),
        ('PROCESSING', _('Processing')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    
    # Export details
    format = models.CharField(_('export format'), max_length=10, choices=Report.FORMAT_CHOICES)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    
    # File details
    file_path = models.CharField(_('file path'), max_length=500, blank=True)
    file_size = models.PositiveIntegerField(_('file size (bytes)'), default=0)
    download_count = models.PositiveIntegerField(_('download count'), default=0)
    
    # Processing
    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Access
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_exports')
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Report Export')
        verbose_name_plural = _('Report Exports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.report.title} ({self.get_format_display()})"
    
    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at
    
    def mark_as_completed(self, file_path, file_size):
        """Mark export as completed."""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.file_path = file_path
        self.file_size = file_size
        self.save()
    
    def increment_download_count(self):
        """Increment download counter."""
        self.download_count += 1
        self.save(update_fields=['download_count'])


class AnalyticsSnapshot(BaseTenantModel):
    """
    Periodic snapshots of key metrics for trend analysis.
    """
    
    SNAPSHOT_TYPES = [
        ('DAILY', _('Daily Snapshot')),
        ('WEEKLY', _('Weekly Snapshot')),
        ('MONTHLY', _('Monthly Snapshot')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot_type = models.CharField(_('snapshot type'), max_length=20, choices=SNAPSHOT_TYPES)
    snapshot_date = models.DateField(_('snapshot date'))
    
    # Assessment metrics
    assessments_sent = models.PositiveIntegerField(_('assessments sent'), default=0)
    assessments_completed = models.PositiveIntegerField(_('assessments completed'), default=0)
    assessment_completion_rate = models.FloatField(_('completion rate'), default=0.0)
    avg_assessment_score = models.FloatField(_('average assessment score'), default=0.0)
    
    # PDI metrics
    pdi_plans_created = models.PositiveIntegerField(_('PDI plans created'), default=0)
    pdi_plans_completed = models.PositiveIntegerField(_('PDI plans completed'), default=0)
    avg_pdi_progress = models.FloatField(_('average PDI progress'), default=0.0)
    overdue_pdi_tasks = models.PositiveIntegerField(_('overdue PDI tasks'), default=0)
    
    # Recruiting metrics (for recruiter organizations)
    candidates_added = models.PositiveIntegerField(_('candidates added'), default=0)
    jobs_posted = models.PositiveIntegerField(_('jobs posted'), default=0)
    applications_received = models.PositiveIntegerField(_('applications received'), default=0)
    placements_made = models.PositiveIntegerField(_('placements made'), default=0)
    avg_time_to_fill = models.FloatField(_('average time to fill (days)'), default=0.0)
    
    # User engagement
    active_users = models.PositiveIntegerField(_('active users'), default=0)
    new_users = models.PositiveIntegerField(_('new users'), default=0)
    user_retention_rate = models.FloatField(_('user retention rate'), default=0.0)
    
    # Usage metrics
    total_logins = models.PositiveIntegerField(_('total logins'), default=0)
    avg_session_duration = models.FloatField(_('average session duration (minutes)'), default=0.0)
    feature_usage = models.JSONField(_('feature usage'), default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Analytics Snapshot')
        verbose_name_plural = _('Analytics Snapshots')
        unique_together = ['organization', 'snapshot_type', 'snapshot_date']
        ordering = ['-snapshot_date']
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_snapshot_type_display()} - {self.snapshot_date}"


class ReportChart(models.Model):
    """
    Chart configurations for reports.
    """
    
    CHART_TYPES = [
        ('BAR', _('Bar Chart')),
        ('LINE', _('Line Chart')),
        ('PIE', _('Pie Chart')),
        ('DOUGHNUT', _('Doughnut Chart')),
        ('RADAR', _('Radar Chart')),
        ('SCATTER', _('Scatter Plot')),
        ('AREA', _('Area Chart')),
        ('GAUGE', _('Gauge Chart')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='charts')
    
    # Chart details
    title = models.CharField(_('chart title'), max_length=200)
    chart_type = models.CharField(_('chart type'), max_length=20, choices=CHART_TYPES)
    
    # Data configuration
    data_source = models.CharField(_('data source'), max_length=100)
    x_axis_field = models.CharField(_('X-axis field'), max_length=100, blank=True)
    y_axis_field = models.CharField(_('Y-axis field'), max_length=100, blank=True)
    group_by_field = models.CharField(_('group by field'), max_length=100, blank=True)
    
    # Chart data
    chart_data = models.JSONField(_('chart data'), default=dict)
    chart_options = models.JSONField(_('chart options'), default=dict)
    
    # Layout
    width = models.PositiveIntegerField(_('width'), default=12)  # Bootstrap columns (1-12)
    height = models.PositiveIntegerField(_('height (px)'), default=400)
    order = models.PositiveIntegerField(_('display order'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Report Chart')
        verbose_name_plural = _('Report Charts')
        ordering = ['report', 'order']
    
    def __str__(self):
        return f"{self.report.title} - {self.title}"


class ReportComment(models.Model):
    """
    Comments and annotations on reports.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='comments')
    
    # Comment content
    content = models.TextField(_('content'))
    is_internal = models.BooleanField(_('internal comment'), default=False)
    
    # Author
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_comments')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Report Comment')
        verbose_name_plural = _('Report Comments')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.report.title} by {self.author.full_name}"


class ReportBookmark(models.Model):
    """
    User bookmarks for frequently accessed reports.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_bookmarks')
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='bookmarks')
    
    # Bookmark details
    name = models.CharField(_('bookmark name'), max_length=200, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Report Bookmark')
        verbose_name_plural = _('Report Bookmarks')
        unique_together = ['user', 'report']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} → {self.report.title}"
    
    def save(self, *args, **kwargs):
        # Set default name if not provided
        if not self.name:
            self.name = self.report.title
        super().save(*args, **kwargs)