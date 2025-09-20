"""
Admin configuration for assessments app.
"""
from django.contrib import admin
from .models import (
    AssessmentDefinition, Question, QuestionOption, 
    AssessmentInstance, Response, ScoreProfile, AssessmentReport
)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0
    fields = ['text', 'value', 'order']
    ordering = ['order']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['text', 'question_type', 'dimension', 'order', 'is_active']
    ordering = ['order']


@admin.register(AssessmentDefinition)
class AssessmentDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'framework', 'status', 'question_count', 'organization', 'created_at']
    list_filter = ['framework', 'status', 'organization', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [QuestionInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'framework', 'version', 'status', 'organization')
        }),
        ('Configuration', {
            'fields': ('instructions', 'estimated_duration', 'randomize_questions', 
                      'allow_skip', 'show_progress')
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


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'text_preview', 'question_type', 'dimension', 'order', 'is_active']
    list_filter = ['assessment', 'question_type', 'dimension', 'is_active']
    search_fields = ['text', 'dimension']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [QuestionOptionInline]
    
    fieldsets = (
        (None, {
            'fields': ('assessment', 'text', 'question_type', 'order', 'is_active')
        }),
        ('Scoring', {
            'fields': ('dimension', 'reverse_scored', 'weight')
        }),
        ('Configuration', {
            'fields': ('required',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question Text'


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'text', 'value', 'order']
    list_filter = ['question__assessment', 'question__question_type']
    search_fields = ['text', 'question__text']
    
    def question_preview(self, obj):
        return f"{obj.question.assessment.name} - Q{obj.question.order}"
    question_preview.short_description = 'Question'


class ResponseInline(admin.TabularInline):
    model = Response
    extra = 0
    readonly_fields = ['question', 'numeric_value', 'text_value', 'selected_option', 'answered_at']
    can_delete = False


@admin.register(AssessmentInstance)
class AssessmentInstanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'assessment', 'status', 'progress_percentage', 'invited_at', 'completed_at']
    list_filter = ['status', 'assessment', 'organization', 'invited_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'assessment__name']
    readonly_fields = ['id', 'token', 'invited_at', 'started_at', 'completed_at', 'progress_percentage']
    inlines = [ResponseInline]
    
    fieldsets = (
        (None, {
            'fields': ('assessment', 'user', 'status', 'organization')
        }),
        ('Access Control', {
            'fields': ('token', 'invited_by', 'expires_at')
        }),
        ('Progress', {
            'fields': ('current_question', 'progress_percentage')
        }),
        ('Timing', {
            'fields': ('invited_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('raw_score', 'percentile_score'),
            'classes': ('collapse',)
        })
    )


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ['instance_user', 'question_preview', 'display_value', 'answered_at']
    list_filter = ['instance__assessment', 'question__dimension', 'answered_at']
    search_fields = ['instance__user__email', 'question__text']
    readonly_fields = ['answered_at', 'updated_at']
    
    def instance_user(self, obj):
        return obj.instance.user.full_name or obj.instance.user.email
    instance_user.short_description = 'User'
    
    def question_preview(self, obj):
        return obj.question.text[:50] + "..." if len(obj.question.text) > 50 else obj.question.text
    question_preview.short_description = 'Question'


@admin.register(ScoreProfile)
class ScoreProfileAdmin(admin.ModelAdmin):
    list_display = ['instance_user', 'instance_assessment', 'profile_type', 'calculated_at']
    list_filter = ['instance__assessment', 'profile_type', 'calculated_at']
    search_fields = ['instance__user__email', 'instance__assessment__name']
    readonly_fields = ['calculated_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('instance', 'profile_type', 'organization')
        }),
        ('Scores', {
            'fields': ('dimension_scores', 'percentile_scores', 'norm_scores')
        }),
        ('Interpretation', {
            'fields': ('strengths', 'development_areas', 'recommendations')
        }),
        ('Metadata', {
            'fields': ('calculated_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def instance_user(self, obj):
        return obj.instance.user.full_name or obj.instance.user.email
    instance_user.short_description = 'User'
    
    def instance_assessment(self, obj):
        return obj.instance.assessment.name
    instance_assessment.short_description = 'Assessment'


@admin.register(AssessmentReport)
class AssessmentReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'format', 'instance_user', 'is_public', 'generated_at']
    list_filter = ['format', 'is_public', 'generated_at']
    search_fields = ['title', 'instance__user__email']
    readonly_fields = ['generated_at', 'updated_at']
    filter_horizontal = ['shared_with']
    
    def instance_user(self, obj):
        return obj.instance.user.full_name or obj.instance.user.email
    instance_user.short_description = 'User'