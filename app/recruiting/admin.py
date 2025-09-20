"""
Admin configuration for recruiting app.
"""
from django.contrib import admin
from .models import (
    Client, Job, Candidate, JobApplication, CandidateNote, Interview,
    Placement, CandidateAssessment, RecruitingPipeline, CandidateRanking,
    CandidateRankingEntry, RecruitingReport
)


class JobInline(admin.TabularInline):
    model = Job
    extra = 0
    fields = ['title', 'status', 'priority', 'positions_available', 'posted_date']
    readonly_fields = ['created_at']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'size', 'primary_contact_name', 'active_jobs_count', 'is_active', 'organization']
    list_filter = ['industry', 'size', 'is_active', 'organization', 'created_at']
    search_fields = ['name', 'primary_contact_name', 'primary_contact_email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [JobInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'industry', 'size', 'organization')
        }),
        ('Contact Information', {
            'fields': ('primary_contact_name', 'primary_contact_email', 'primary_contact_phone')
        }),
        ('Company Details', {
            'fields': ('website', 'description')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Business Relationship', {
            'fields': ('contract_start_date', 'contract_end_date', 'commission_rate', 'payment_terms')
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


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ['candidate', 'status', 'fit_score', 'applied_date']
    readonly_fields = ['applied_date', 'fit_score']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'status', 'priority', 'applications_count', 'assigned_recruiter', 'posted_date']
    list_filter = ['status', 'priority', 'employment_type', 'client', 'organization', 'posted_date']
    search_fields = ['title', 'description', 'client__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [JobApplicationInline]
    
    fieldsets = (
        (None, {
            'fields': ('client', 'title', 'status', 'priority', 'organization')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'responsibilities')
        }),
        ('Job Specifications', {
            'fields': ('employment_type', 'location', 'remote_allowed', 'travel_required')
        }),
        ('Experience & Education', {
            'fields': ('min_experience_years', 'max_experience_years', 'education_level')
        }),
        ('Skills & Competencies', {
            'fields': ('required_skills', 'preferred_skills', 'languages')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'currency', 'benefits')
        }),
        ('Management', {
            'fields': ('positions_available', 'positions_filled', 'assigned_recruiter')
        }),
        ('Timeline', {
            'fields': ('posted_date', 'application_deadline', 'target_start_date')
        }),
        ('Assessment', {
            'fields': ('requires_assessment', 'assessment_definition')
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


class CandidateNoteInline(admin.TabularInline):
    model = CandidateNote
    extra = 0
    fields = ['note_type', 'content', 'is_private', 'author', 'created_at']
    readonly_fields = ['created_at']


class CandidateAssessmentInline(admin.TabularInline):
    model = CandidateAssessment
    extra = 0
    fields = ['assessment_instance', 'purpose', 'overall_score', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'current_title', 'experience_years', 'status', 'assigned_recruiter', 'organization']
    list_filter = ['status', 'education_level', 'remote_work_preference', 'source', 'organization', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'current_title', 'current_company']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [CandidateNoteInline, CandidateAssessmentInline]
    
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'organization')
        }),
        ('Professional Information', {
            'fields': ('current_title', 'current_company', 'experience_years', 'education_level')
        }),
        ('Location & Availability', {
            'fields': ('location', 'willing_to_relocate', 'remote_work_preference')
        }),
        ('Skills & Competencies', {
            'fields': ('skills', 'languages', 'certifications')
        }),
        ('Compensation', {
            'fields': ('salary_expectation_min', 'salary_expectation_max', 'currency')
        }),
        ('Documents', {
            'fields': ('resume_file', 'portfolio_url', 'linkedin_url')
        }),
        ('Status & Management', {
            'fields': ('status', 'assigned_recruiter', 'notes')
        }),
        ('Source Tracking', {
            'fields': ('source', 'source_details')
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


class InterviewInline(admin.TabularInline):
    model = Interview
    extra = 0
    fields = ['interview_type', 'status', 'scheduled_date', 'overall_rating', 'recommendation']
    readonly_fields = ['created_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'status', 'fit_score', 'recruiter', 'applied_date']
    list_filter = ['status', 'job__client', 'organization', 'applied_date']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'job__title']
    readonly_fields = ['applied_date', 'fit_score']
    inlines = [InterviewInline]
    
    fieldsets = (
        (None, {
            'fields': ('candidate', 'job', 'status', 'recruiter')
        }),
        ('Application Details', {
            'fields': ('cover_letter', 'applied_date')
        }),
        ('Assessment', {
            'fields': ('assessment_instance', 'assessment_score', 'fit_score')
        }),
        ('Interview Process', {
            'fields': ('interview_scheduled_date', 'interview_completed_date', 'interview_notes', 'interview_rating')
        }),
        ('Offer Details', {
            'fields': ('offer_extended_date', 'offer_amount', 'offer_currency', 'offer_accepted_date', 'start_date'),
            'classes': ('collapse',)
        }),
        ('Rejection', {
            'fields': ('rejection_date', 'rejection_reason', 'rejection_notes'),
            'classes': ('collapse',)
        })
    )


@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'note_type', 'author', 'is_private', 'created_at']
    list_filter = ['note_type', 'is_private', 'created_at']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['application_candidate', 'interview_type', 'status', 'scheduled_date', 'overall_rating', 'recommendation']
    list_filter = ['interview_type', 'status', 'recommendation', 'scheduled_date']
    search_fields = ['application__candidate__first_name', 'application__candidate__last_name', 'application__job__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('application', 'interview_type', 'status', 'organization')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'duration_minutes', 'location_or_link')
        }),
        ('Participants', {
            'fields': ('interviewer', 'additional_interviewers')
        }),
        ('Results', {
            'fields': ('completed_date', 'overall_rating', 'technical_rating', 'communication_rating', 'cultural_fit_rating')
        }),
        ('Feedback', {
            'fields': ('feedback', 'strengths', 'concerns', 'recommendation')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def application_candidate(self, obj):
        return obj.application.candidate.full_name
    application_candidate.short_description = 'Candidate'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ['application_candidate', 'application_job', 'start_date', 'salary', 'commission_earned', 'is_active']
    list_filter = ['is_active', 'start_date', 'organization']
    search_fields = ['application__candidate__first_name', 'application__candidate__last_name', 'application__job__title']
    readonly_fields = ['commission_earned', 'guarantee_end_date', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('application', 'organization')
        }),
        ('Placement Details', {
            'fields': ('start_date', 'salary', 'currency', 'commission_earned')
        }),
        ('Guarantee Period', {
            'fields': ('guarantee_period_days', 'guarantee_end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'termination_date', 'termination_reason')
        }),
        ('Follow-up', {
            'fields': ('follow_up_30_days', 'follow_up_60_days', 'follow_up_90_days')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def application_candidate(self, obj):
        return obj.application.candidate.full_name
    application_candidate.short_description = 'Candidate'
    
    def application_job(self, obj):
        return f"{obj.application.job.client.name} - {obj.application.job.title}"
    application_job.short_description = 'Job'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CandidateAssessment)
class CandidateAssessmentAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'assessment_name', 'purpose', 'overall_score', 'created_at']
    list_filter = ['purpose', 'created_at']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'assessment_instance__assessment__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def assessment_name(self, obj):
        return obj.assessment_instance.assessment.name
    assessment_name.short_description = 'Assessment'


@admin.register(RecruitingPipeline)
class RecruitingPipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_active', 'required_assessment', 'organization']
    list_filter = ['is_default', 'is_active', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'organization')
        }),
        ('Pipeline Configuration', {
            'fields': ('stages', 'default_stage_durations', 'is_default', 'is_active')
        }),
        ('Assessment Integration', {
            'fields': ('assessment_stage', 'required_assessment')
        }),
        ('Automation', {
            'fields': ('auto_advance_on_assessment', 'auto_reject_on_low_score', 'min_assessment_score')
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


class CandidateRankingEntryInline(admin.TabularInline):
    model = CandidateRankingEntry
    extra = 0
    fields = ['candidate', 'rank', 'total_score', 'assessment_score', 'interview_score']
    readonly_fields = ['calculated_at']


@admin.register(CandidateRanking)
class CandidateRankingAdmin(admin.ModelAdmin):
    list_display = ['name', 'job', 'candidates_count', 'auto_update', 'organization']
    list_filter = ['auto_update', 'include_assessment_scores', 'organization', 'created_at']
    search_fields = ['name', 'description', 'job__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [CandidateRankingEntryInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'job', 'organization')
        }),
        ('Ranking Criteria', {
            'fields': ('criteria', 'weights')
        }),
        ('Configuration', {
            'fields': ('auto_update', 'include_assessment_scores', 'include_interview_ratings', 'include_experience_match')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def candidates_count(self, obj):
        return obj.candidates.count()
    candidates_count.short_description = 'Candidates'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecruitingReport)
class RecruitingReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'format', 'client', 'generated_at', 'generated_by']
    list_filter = ['report_type', 'format', 'is_confidential', 'shared_with_client', 'generated_at']
    search_fields = ['title', 'client__name', 'job__title', 'candidate__first_name', 'candidate__last_name']
    readonly_fields = ['generated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'report_type', 'format')
        }),
        ('Scope', {
            'fields': ('client', 'job', 'candidate', 'date_from', 'date_to')
        }),
        ('Content', {
            'fields': ('content', 'data', 'file_path')
        }),
        ('Access Control', {
            'fields': ('is_confidential', 'shared_with_client')
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        })
    )