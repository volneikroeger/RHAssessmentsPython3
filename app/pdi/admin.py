"""
Admin configuration for PDI app.
"""
from django.contrib import admin
from .models import PDIPlan, PDITask, PDIProgressUpdate, PDITemplate, PDIActionCatalog, PDIComment, PDIReminder


class PDITaskInline(admin.TabularInline):
    model = PDITask
    extra = 0
    fields = ['title', 'category', 'status', 'progress_percentage', 'time_bound_deadline', 'weight']
    readonly_fields = ['progress_percentage']
    ordering = ['time_bound_deadline']


class PDICommentInline(admin.TabularInline):
    model = PDIComment
    extra = 0
    fields = ['author', 'content', 'is_private', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(PDIPlan)
class PDIPlanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'title', 'status', 'priority', 'overall_progress', 'target_completion_date', 'organization']
    list_filter = ['status', 'priority', 'organization', 'created_at', 'target_completion_date']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'title']
    readonly_fields = ['id', 'overall_progress', 'created_at', 'updated_at']
    inlines = [PDITaskInline, PDICommentInline]
    
    fieldsets = (
        (None, {
            'fields': ('employee', 'manager', 'hr_contact', 'organization')
        }),
        ('Plan Details', {
            'fields': ('title', 'description', 'status', 'priority')
        }),
        ('Assessment Integration', {
            'fields': ('source_assessment',)
        }),
        ('Timeline', {
            'fields': ('start_date', 'target_completion_date', 'actual_completion_date')
        }),
        ('Progress', {
            'fields': ('overall_progress', 'last_review_date', 'next_review_date')
        }),
        ('Approval', {
            'fields': ('submitted_for_approval_at', 'approved_by', 'approved_at', 'approval_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PDIProgressUpdateInline(admin.TabularInline):
    model = PDIProgressUpdate
    extra = 0
    fields = ['progress_percentage', 'notes', 'updated_by', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(PDITask)
class PDITaskAdmin(admin.ModelAdmin):
    list_display = ['pdi_plan_employee', 'title', 'category', 'status', 'progress_percentage', 'time_bound_deadline', 'is_overdue']
    list_filter = ['status', 'category', 'pdi_plan__organization', 'time_bound_deadline', 'created_at']
    search_fields = ['title', 'description', 'pdi_plan__employee__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'started_at', 'completed_at']
    inlines = [PDIProgressUpdateInline]
    
    fieldsets = (
        (None, {
            'fields': ('pdi_plan', 'title', 'description', 'category', 'competency_area')
        }),
        ('SMART Goal Components', {
            'fields': ('specific_objective', 'measurable_criteria', 'achievable_steps', 
                      'relevant_justification', 'time_bound_deadline')
        }),
        ('Progress', {
            'fields': ('status', 'progress_percentage', 'weight')
        }),
        ('Resources', {
            'fields': ('required_resources', 'assigned_mentor', 'estimated_hours', 'actual_hours')
        }),
        ('Tracking', {
            'fields': ('started_at', 'completed_at', 'last_update_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def pdi_plan_employee(self, obj):
        return obj.pdi_plan.employee.full_name or obj.pdi_plan.employee.email
    pdi_plan_employee.short_description = 'Employee'
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'


@admin.register(PDIProgressUpdate)
class PDIProgressUpdateAdmin(admin.ModelAdmin):
    list_display = ['task_title', 'progress_percentage', 'updated_by', 'created_at']
    list_filter = ['created_at', 'task__pdi_plan__organization']
    search_fields = ['task__title', 'notes', 'updated_by__email']
    readonly_fields = ['created_at']
    
    def task_title(self, obj):
        return obj.task.title
    task_title.short_description = 'Task'


@admin.register(PDITemplate)
class PDITemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'assessment_framework', 'auto_generate', 'requires_approval', 'is_active', 'organization']
    list_filter = ['assessment_framework', 'auto_generate', 'requires_approval', 'is_active', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'assessment_framework', 'organization')
        }),
        ('Configuration', {
            'fields': ('auto_generate', 'requires_approval', 'default_duration_days', 'is_active')
        }),
        ('Template Content', {
            'fields': ('template_tasks', 'scoring_rules')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PDIActionCatalog)
class PDIActionCatalogAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty_level', 'estimated_duration', 'is_active', 'organization']
    list_filter = ['category', 'difficulty_level', 'is_active', 'organization']
    search_fields = ['title', 'description', 'target_competencies']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'organization')
        }),
        ('Action Details', {
            'fields': ('estimated_duration', 'difficulty_level', 'required_resources')
        }),
        ('Resources', {
            'fields': ('recommended_tools', 'external_links')
        }),
        ('Targeting', {
            'fields': ('target_competencies', 'target_roles')
        }),
        ('Metadata', {
            'fields': ('id', 'is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PDIComment)
class PDICommentAdmin(admin.ModelAdmin):
    list_display = ['pdi_plan_employee', 'task_title', 'author', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at', 'pdi_plan__organization']
    search_fields = ['content', 'author__email', 'pdi_plan__employee__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def pdi_plan_employee(self, obj):
        return obj.pdi_plan.employee.full_name or obj.pdi_plan.employee.email
    pdi_plan_employee.short_description = 'Employee'
    
    def task_title(self, obj):
        return obj.task.title if obj.task else '—'
    task_title.short_description = 'Task'


@admin.register(PDIReminder)
class PDIReminderAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'reminder_type', 'scheduled_for', 'is_sent', 'sent_at']
    list_filter = ['reminder_type', 'is_sent', 'scheduled_for', 'pdi_plan__organization']
    search_fields = ['recipient__email', 'message']
    readonly_fields = ['sent_at']
    
    def mark_as_sent(self, request, queryset):
        """Mark selected reminders as sent."""
        from django.utils import timezone
        updated = queryset.update(is_sent=True, sent_at=timezone.now())
        self.message_user(request, f'{updated} reminders marked as sent.')
    mark_as_sent.short_description = 'Mark selected reminders as sent'
    
    actions = [mark_as_sent]