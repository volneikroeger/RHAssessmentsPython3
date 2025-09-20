"""
PDI models for Individual Development Plans.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from core.db import BaseTenantModel

User = get_user_model()


class PDIPlan(BaseTenantModel):
    """
    Individual Development Plan for an employee.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('PENDING_APPROVAL', _('Pending Approval')),
        ('APPROVED', _('Approved')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', _('Low')),
        ('MEDIUM', _('Medium')),
        ('HIGH', _('High')),
        ('CRITICAL', _('Critical')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdi_plans')
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_pdi_plans'
    )
    hr_contact = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='hr_pdi_plans'
    )
    
    # Plan details
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Assessment integration
    source_assessment = models.ForeignKey(
        'assessments.AssessmentInstance',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generated_pdi_plans'
    )
    
    # Timeline
    start_date = models.DateField(_('start date'))
    target_completion_date = models.DateField(_('target completion date'))
    actual_completion_date = models.DateField(_('actual completion date'), null=True, blank=True)
    
    # Progress tracking
    overall_progress = models.FloatField(_('overall progress'), default=0.0)
    last_review_date = models.DateField(_('last review date'), null=True, blank=True)
    next_review_date = models.DateField(_('next review date'), null=True, blank=True)
    
    # Approval workflow
    submitted_for_approval_at = models.DateTimeField(_('submitted for approval'), null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_pdi_plans'
    )
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    approval_notes = models.TextField(_('approval notes'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_pdi_plans'
    )
    
    class Meta:
        verbose_name = _('PDI Plan')
        verbose_name_plural = _('PDI Plans')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('pdi:detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        return self.status in ['APPROVED', 'IN_PROGRESS']
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return (self.target_completion_date < timezone.now().date() and 
                self.status not in ['COMPLETED', 'CANCELLED'])
    
    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.status in ['COMPLETED', 'CANCELLED']:
            return 0
        delta = self.target_completion_date - timezone.now().date()
        return max(0, delta.days)
    
    def calculate_progress(self):
        """Calculate overall progress based on tasks."""
        tasks = self.tasks.filter(is_active=True)
        if not tasks.exists():
            return 0.0
        
        total_weight = sum(task.weight for task in tasks)
        if total_weight == 0:
            return 0.0
        
        weighted_progress = sum(
            (task.progress_percentage / 100) * task.weight 
            for task in tasks
        )
        
        return (weighted_progress / total_weight) * 100
    
    def update_progress(self):
        """Update overall progress and save."""
        self.overall_progress = self.calculate_progress()
        self.save(update_fields=['overall_progress'])
    
    def submit_for_approval(self):
        """Submit plan for manager approval."""
        from django.utils import timezone
        self.status = 'PENDING_APPROVAL'
        self.submitted_for_approval_at = timezone.now()
        self.save(update_fields=['status', 'submitted_for_approval_at'])
    
    def approve(self, approved_by, notes=''):
        """Approve the PDI plan."""
        from django.utils import timezone
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'approval_notes'])


class PDITask(models.Model):
    """
    Individual SMART goal within a PDI plan.
    """
    
    STATUS_CHOICES = [
        ('NOT_STARTED', _('Not Started')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('ON_HOLD', _('On Hold')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    CATEGORY_CHOICES = [
        ('TECHNICAL_SKILLS', _('Technical Skills')),
        ('SOFT_SKILLS', _('Soft Skills')),
        ('LEADERSHIP', _('Leadership')),
        ('COMMUNICATION', _('Communication')),
        ('CAREER_DEVELOPMENT', _('Career Development')),
        ('PERFORMANCE', _('Performance Improvement')),
        ('KNOWLEDGE', _('Knowledge Acquisition')),
        ('CERTIFICATION', _('Certification/Training')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdi_plan = models.ForeignKey(PDIPlan, on_delete=models.CASCADE, related_name='tasks')
    
    # SMART goal components
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    specific_objective = models.TextField(_('specific objective'))
    measurable_criteria = models.TextField(_('measurable criteria'))
    achievable_steps = models.TextField(_('achievable steps'))
    relevant_justification = models.TextField(_('relevant justification'))
    time_bound_deadline = models.DateField(_('deadline'))
    
    # Categorization
    category = models.CharField(_('category'), max_length=20, choices=CATEGORY_CHOICES)
    competency_area = models.CharField(_('competency area'), max_length=100, blank=True)
    
    # Progress tracking
    status = models.CharField(_('status'), max_length=15, choices=STATUS_CHOICES, default='NOT_STARTED')
    progress_percentage = models.FloatField(_('progress percentage'), default=0.0)
    weight = models.FloatField(_('weight'), default=1.0)
    
    # Resources and support
    required_resources = models.TextField(_('required resources'), blank=True)
    assigned_mentor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mentored_pdi_tasks'
    )
    estimated_hours = models.PositiveIntegerField(_('estimated hours'), default=0)
    actual_hours = models.PositiveIntegerField(_('actual hours'), default=0)
    
    # Tracking
    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    last_update_at = models.DateTimeField(_('last update'), null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('PDI Task')
        verbose_name_plural = _('PDI Tasks')
        ordering = ['pdi_plan', 'time_bound_deadline']
    
    def __str__(self):
        return f"{self.pdi_plan.employee.full_name} - {self.title}"
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return (self.time_bound_deadline < timezone.now().date() and 
                self.status not in ['COMPLETED', 'CANCELLED'])
    
    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.status in ['COMPLETED', 'CANCELLED']:
            return 0
        delta = self.time_bound_deadline - timezone.now().date()
        return max(0, delta.days)
    
    def mark_completed(self):
        """Mark task as completed."""
        from django.utils import timezone
        self.status = 'COMPLETED'
        self.progress_percentage = 100.0
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'progress_percentage', 'completed_at'])
        
        # Update PDI plan progress
        self.pdi_plan.update_progress()
    
    def update_progress(self, percentage, notes=''):
        """Update task progress."""
        from django.utils import timezone
        self.progress_percentage = max(0, min(100, percentage))
        self.last_update_at = timezone.now()
        
        if percentage >= 100 and self.status != 'COMPLETED':
            self.mark_completed()
        elif percentage > 0 and self.status == 'NOT_STARTED':
            self.status = 'IN_PROGRESS'
            self.started_at = timezone.now()
        
        self.save()
        
        # Create progress update record
        PDIProgressUpdate.objects.create(
            task=self,
            progress_percentage=percentage,
            notes=notes,
            updated_by=None  # Will be set in view
        )


class PDIProgressUpdate(models.Model):
    """
    Progress updates for PDI tasks.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(PDITask, on_delete=models.CASCADE, related_name='progress_updates')
    progress_percentage = models.FloatField(_('progress percentage'))
    notes = models.TextField(_('notes'), blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('PDI Progress Update')
        verbose_name_plural = _('PDI Progress Updates')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.title} - {self.progress_percentage}%"


class PDITemplate(BaseTenantModel):
    """
    Template for generating PDI plans based on assessment results.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Assessment integration
    assessment_framework = models.CharField(
        _('assessment framework'),
        max_length=20,
        choices=[
            ('BIG_FIVE', _('Big Five Personality')),
            ('DISC', _('DISC Assessment')),
            ('CAREER_ANCHORS', _('Career Anchors')),
            ('OCEAN', _('OCEAN Model')),
            ('CUSTOM', _('Custom Assessment')),
        ]
    )
    
    # Template configuration
    auto_generate = models.BooleanField(_('auto generate'), default=True)
    requires_approval = models.BooleanField(_('requires approval'), default=True)
    default_duration_days = models.PositiveIntegerField(_('default duration (days)'), default=90)
    
    # Content
    template_tasks = models.JSONField(_('template tasks'), default=list)
    scoring_rules = models.JSONField(_('scoring rules'), default=dict)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('PDI Template')
        verbose_name_plural = _('PDI Templates')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_assessment_framework_display()})"
    
    def generate_pdi_for_assessment(self, assessment_instance):
        """Generate PDI plan from assessment results."""
        from assessments.models import ScoreProfile
        
        try:
            score_profile = assessment_instance.score_profile
        except ScoreProfile.DoesNotExist:
            return None
        
        # Create PDI plan
        pdi_plan = PDIPlan.objects.create(
            organization=assessment_instance.organization,
            employee=assessment_instance.user,
            title=f"Development Plan - {assessment_instance.assessment.name}",
            description=f"Auto-generated from {assessment_instance.assessment.name} results",
            source_assessment=assessment_instance,
            start_date=timezone.now().date(),
            target_completion_date=timezone.now().date() + timezone.timedelta(days=self.default_duration_days),
            status='PENDING_APPROVAL' if self.requires_approval else 'APPROVED',
            created_by=assessment_instance.invited_by
        )
        
        # Generate tasks based on template and scores
        self._generate_tasks_from_template(pdi_plan, score_profile)
        
        return pdi_plan
    
    def _generate_tasks_from_template(self, pdi_plan, score_profile):
        """Generate tasks based on template rules and assessment scores."""
        from django.utils import timezone
        
        for task_template in self.template_tasks:
            # Check if task should be generated based on scoring rules
            should_generate = self._evaluate_scoring_rules(
                task_template.get('conditions', {}),
                score_profile.dimension_scores
            )
            
            if should_generate:
                PDITask.objects.create(
                    pdi_plan=pdi_plan,
                    title=task_template['title'],
                    description=task_template['description'],
                    specific_objective=task_template.get('specific_objective', ''),
                    measurable_criteria=task_template.get('measurable_criteria', ''),
                    achievable_steps=task_template.get('achievable_steps', ''),
                    relevant_justification=task_template.get('relevant_justification', ''),
                    time_bound_deadline=pdi_plan.target_completion_date,
                    category=task_template.get('category', 'PERFORMANCE'),
                    competency_area=task_template.get('competency_area', ''),
                    weight=task_template.get('weight', 1.0),
                    estimated_hours=task_template.get('estimated_hours', 0)
                )
    
    def _evaluate_scoring_rules(self, conditions, dimension_scores):
        """Evaluate if conditions are met based on dimension scores."""
        if not conditions:
            return True
        
        for dimension, rule in conditions.items():
            score = dimension_scores.get(dimension, 0)
            
            if 'min_score' in rule and score < rule['min_score']:
                return False
            if 'max_score' in rule and score > rule['max_score']:
                return False
            if 'percentile_below' in rule:
                # Would need percentile calculation
                pass
        
        return True


class PDIActionCatalog(BaseTenantModel):
    """
    Catalog of pre-defined development actions.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    category = models.CharField(_('category'), max_length=20, choices=PDITask.CATEGORY_CHOICES)
    
    # Action details
    estimated_duration = models.PositiveIntegerField(_('estimated duration (hours)'), default=1)
    difficulty_level = models.CharField(
        _('difficulty level'),
        max_length=10,
        choices=[
            ('BEGINNER', _('Beginner')),
            ('INTERMEDIATE', _('Intermediate')),
            ('ADVANCED', _('Advanced')),
        ],
        default='INTERMEDIATE'
    )
    
    # Resources
    required_resources = models.TextField(_('required resources'), blank=True)
    recommended_tools = models.JSONField(_('recommended tools'), default=list)
    external_links = models.JSONField(_('external links'), default=list)
    
    # Targeting
    target_competencies = models.JSONField(_('target competencies'), default=list)
    target_roles = models.JSONField(_('target roles'), default=list)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('PDI Action Catalog')
        verbose_name_plural = _('PDI Action Catalog')
        ordering = ['category', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class PDIComment(models.Model):
    """
    Comments and feedback on PDI plans and tasks.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdi_plan = models.ForeignKey(PDIPlan, on_delete=models.CASCADE, related_name='comments')
    task = models.ForeignKey(PDITask, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    
    # Comment content
    content = models.TextField(_('content'))
    is_private = models.BooleanField(_('private comment'), default=False)
    
    # Author
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdi_comments')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('PDI Comment')
        verbose_name_plural = _('PDI Comments')
        ordering = ['created_at']
    
    def __str__(self):
        target = self.task.title if self.task else self.pdi_plan.title
        return f"Comment on {target} by {self.author.full_name}"


class PDIReminder(models.Model):
    """
    Reminders for PDI tasks and reviews.
    """
    
    REMINDER_TYPES = [
        ('TASK_DUE', _('Task Due Soon')),
        ('TASK_OVERDUE', _('Task Overdue')),
        ('REVIEW_DUE', _('Review Due')),
        ('APPROVAL_PENDING', _('Approval Pending')),
        ('PLAN_COMPLETION', _('Plan Completion')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdi_plan = models.ForeignKey(PDIPlan, on_delete=models.CASCADE, related_name='reminders')
    task = models.ForeignKey(PDITask, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    
    # Reminder details
    reminder_type = models.CharField(_('reminder type'), max_length=20, choices=REMINDER_TYPES)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdi_reminders')
    message = models.TextField(_('message'))
    
    # Scheduling
    scheduled_for = models.DateTimeField(_('scheduled for'))
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    is_sent = models.BooleanField(_('sent'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('PDI Reminder')
        verbose_name_plural = _('PDI Reminders')
        ordering = ['scheduled_for']
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} for {self.recipient.full_name}"
    
    def mark_as_sent(self):
        """Mark reminder as sent."""
        from django.utils import timezone
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['is_sent', 'sent_at'])