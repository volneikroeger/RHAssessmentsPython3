"""
Assessment models for psychological assessments.
"""
import uuid
import json
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from core.db import BaseTenantModel

User = get_user_model()


class AssessmentDefinition(BaseTenantModel):
    """
    Definition of an assessment framework (e.g., Big Five, DISC).
    """
    
    FRAMEWORK_CHOICES = [
        ('BIG_FIVE', _('Big Five Personality')),
        ('DISC', _('DISC Assessment')),
        ('CAREER_ANCHORS', _('Career Anchors')),
        ('OCEAN', _('OCEAN Model')),
        ('CUSTOM', _('Custom Assessment')),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('ACTIVE', _('Active')),
        ('ARCHIVED', _('Archived')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    framework = models.CharField(_('framework'), max_length=20, choices=FRAMEWORK_CHOICES)
    version = models.CharField(_('version'), max_length=20, default='1.0')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Configuration
    instructions = models.TextField(_('instructions'), blank=True)
    estimated_duration = models.PositiveIntegerField(_('estimated duration (minutes)'), default=15)
    randomize_questions = models.BooleanField(_('randomize questions'), default=False)
    allow_skip = models.BooleanField(_('allow skip questions'), default=False)
    show_progress = models.BooleanField(_('show progress'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Assessment Definition')
        verbose_name_plural = _('Assessment Definitions')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_framework_display()})"
    
    def get_absolute_url(self):
        return reverse('assessments:detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        return self.status == 'ACTIVE'
    
    @property
    def question_count(self):
        return self.questions.filter(is_active=True).count()


class Question(models.Model):
    """
    Individual question within an assessment.
    """
    
    QUESTION_TYPES = [
        ('LIKERT_5', _('5-Point Likert Scale')),
        ('LIKERT_7', _('7-Point Likert Scale')),
        ('MULTIPLE_CHOICE', _('Multiple Choice')),
        ('FORCED_CHOICE', _('Forced Choice (Pairs)')),
        ('RANKING', _('Ranking')),
        ('TEXT', _('Text Response')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(AssessmentDefinition, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(_('question text'))
    question_type = models.CharField(_('question type'), max_length=20, choices=QUESTION_TYPES)
    order = models.PositiveIntegerField(_('order'), default=0)
    
    # Scoring
    dimension = models.CharField(_('dimension'), max_length=50, blank=True)
    reverse_scored = models.BooleanField(_('reverse scored'), default=False)
    weight = models.FloatField(_('weight'), default=1.0)
    
    # Configuration
    required = models.BooleanField(_('required'), default=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['assessment', 'order']
    
    def __str__(self):
        return f"{self.assessment.name} - Q{self.order}: {self.text[:50]}..."


class QuestionOption(models.Model):
    """
    Response options for multiple choice and Likert scale questions.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(_('option text'), max_length=200)
    value = models.IntegerField(_('numeric value'))
    order = models.PositiveIntegerField(_('order'), default=0)
    
    class Meta:
        verbose_name = _('Question Option')
        verbose_name_plural = _('Question Options')
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"{self.question.assessment.name} - {self.text} ({self.value})"


class AssessmentInstance(BaseTenantModel):
    """
    An instance of an assessment being taken by a user.
    """
    
    STATUS_CHOICES = [
        ('INVITED', _('Invited')),
        ('STARTED', _('Started')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('EXPIRED', _('Expired')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(AssessmentDefinition, on_delete=models.CASCADE, related_name='instances')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_instances')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='INVITED')
    
    # Access control
    token = models.CharField(_('access token'), max_length=100, unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_assessments')
    
    # Progress tracking
    current_question = models.PositiveIntegerField(_('current question'), default=0)
    progress_percentage = models.FloatField(_('progress percentage'), default=0.0)
    
    # Timing
    invited_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    
    # Results
    raw_score = models.JSONField(_('raw scores'), default=dict, blank=True)
    percentile_score = models.JSONField(_('percentile scores'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Assessment Instance')
        verbose_name_plural = _('Assessment Instances')
        ordering = ['-invited_at']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.assessment.name} ({self.status})"
    
    def get_absolute_url(self):
        return reverse('assessments:take', kwargs={'token': self.token})
    
    @property
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expires_at and timezone.now() > self.expires_at
    
    def calculate_progress(self):
        """Calculate completion progress."""
        total_questions = self.assessment.questions.filter(is_active=True).count()
        if total_questions == 0:
            return 0.0
        
        answered_questions = self.responses.count()
        return (answered_questions / total_questions) * 100
    
    def update_progress(self):
        """Update progress percentage."""
        self.progress_percentage = self.calculate_progress()
        self.save(update_fields=['progress_percentage'])


class Response(models.Model):
    """
    User's response to a specific question.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(AssessmentInstance, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    
    # Response data
    numeric_value = models.IntegerField(_('numeric value'), null=True, blank=True)
    text_value = models.TextField(_('text value'), blank=True)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    answered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Response')
        verbose_name_plural = _('Responses')
        unique_together = ['instance', 'question']
        ordering = ['instance', 'question__order']
    
    def __str__(self):
        return f"{self.instance.user.full_name} - {self.question.text[:30]}..."
    
    @property
    def display_value(self):
        """Get display value for the response."""
        if self.selected_option:
            return self.selected_option.text
        elif self.numeric_value is not None:
            return str(self.numeric_value)
        elif self.text_value:
            return self.text_value
        return _('No response')


class ScoreProfile(BaseTenantModel):
    """
    Calculated scores and profile for a completed assessment.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.OneToOneField(AssessmentInstance, on_delete=models.CASCADE, related_name='score_profile')
    
    # Dimensional scores
    dimension_scores = models.JSONField(_('dimension scores'), default=dict)
    percentile_scores = models.JSONField(_('percentile scores'), default=dict)
    norm_scores = models.JSONField(_('norm scores'), default=dict)
    
    # Profile interpretation
    profile_type = models.CharField(_('profile type'), max_length=100, blank=True)
    strengths = models.JSONField(_('strengths'), default=list)
    development_areas = models.JSONField(_('development areas'), default=list)
    recommendations = models.JSONField(_('recommendations'), default=list)
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Score Profile')
        verbose_name_plural = _('Score Profiles')
    
    def __str__(self):
        return f"Profile for {self.instance.user.full_name} - {self.instance.assessment.name}"
    
    def get_dimension_score(self, dimension):
        """Get score for a specific dimension."""
        return self.dimension_scores.get(dimension, 0)
    
    def get_percentile_score(self, dimension):
        """Get percentile score for a specific dimension."""
        return self.percentile_scores.get(dimension, 50)


class AssessmentReport(BaseTenantModel):
    """
    Generated report for a completed assessment.
    """
    
    FORMAT_CHOICES = [
        ('HTML', _('HTML Report')),
        ('PDF', _('PDF Report')),
        ('JSON', _('JSON Data')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(AssessmentInstance, on_delete=models.CASCADE, related_name='reports')
    format = models.CharField(_('format'), max_length=10, choices=FORMAT_CHOICES)
    
    # Report content
    title = models.CharField(_('title'), max_length=200)
    content = models.TextField(_('content'), blank=True)
    file_path = models.CharField(_('file path'), max_length=500, blank=True)
    
    # Access control
    is_public = models.BooleanField(_('public'), default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_reports')
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Assessment Report')
        verbose_name_plural = _('Assessment Reports')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} ({self.format})"
    
    def get_absolute_url(self):
        return reverse('assessments:report', kwargs={'pk': self.pk})