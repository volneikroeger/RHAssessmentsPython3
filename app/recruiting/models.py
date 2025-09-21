"""
Recruiting models for candidate and job management.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from core.db import BaseTenantModel
from core.fields import EncryptedTextField, EncryptedEmailField

User = get_user_model()


class Client(BaseTenantModel):
    """
    Client companies that hire through recruiting agencies.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('company name'), max_length=200)
    industry = models.CharField(_('industry'), max_length=100, blank=True)
    size = models.CharField(
        _('company size'),
        max_length=20,
        choices=[
            ('STARTUP', _('Startup (1-10)')),
            ('SMALL', _('Small (11-50)')),
            ('MEDIUM', _('Medium (51-200)')),
            ('LARGE', _('Large (201-1000)')),
            ('ENTERPRISE', _('Enterprise (1000+)')),
        ],
        blank=True
    )
    
    # Contact information
    primary_contact_name = models.CharField(_('primary contact name'), max_length=200)
    primary_contact_email = EncryptedEmailField(_('primary contact email'))
    primary_contact_phone = EncryptedTextField(_('primary contact phone'), blank=True)
    
    # Company details
    website = models.URLField(_('website'), blank=True)
    description = models.TextField(_('description'), blank=True)
    
    # Address
    address_line1 = EncryptedTextField(_('address line 1'), blank=True)
    address_line2 = EncryptedTextField(_('address line 2'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state'), max_length=100, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    country = models.CharField(_('country'), max_length=100, blank=True)
    
    # Business relationship
    contract_start_date = models.DateField(_('contract start date'), null=True, blank=True)
    contract_end_date = models.DateField(_('contract end date'), null=True, blank=True)
    commission_rate = models.DecimalField(_('commission rate'), max_digits=5, decimal_places=2, default=15.00)
    payment_terms = models.CharField(_('payment terms'), max_length=100, default='Net 30')
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('recruiting:client_detail', kwargs={'pk': self.pk})
    
    @property
    def active_jobs_count(self):
        return self.jobs.filter(status__in=['OPEN', 'IN_PROGRESS']).count()
    
    @property
    def total_placements(self):
        return self.jobs.filter(status='FILLED').count()


class Job(BaseTenantModel):
    """
    Job openings from clients.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('OPEN', _('Open')),
        ('IN_PROGRESS', _('In Progress')),
        ('FILLED', _('Filled')),
        ('ON_HOLD', _('On Hold')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', _('Low')),
        ('MEDIUM', _('Medium')),
        ('HIGH', _('High')),
        ('URGENT', _('Urgent')),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULL_TIME', _('Full Time')),
        ('PART_TIME', _('Part Time')),
        ('CONTRACT', _('Contract')),
        ('TEMPORARY', _('Temporary')),
        ('REMOTE', _('Remote')),
        ('HYBRID', _('Hybrid')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='jobs')
    
    # Job details
    title = models.CharField(_('job title'), max_length=200)
    description = models.TextField(_('job description'))
    requirements = models.TextField(_('requirements'))
    responsibilities = models.TextField(_('responsibilities'))
    
    # Job specifications
    employment_type = models.CharField(_('employment type'), max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    location = models.CharField(_('location'), max_length=200)
    remote_allowed = models.BooleanField(_('remote work allowed'), default=False)
    travel_required = models.CharField(_('travel required'), max_length=50, blank=True)
    
    # Experience and education
    min_experience_years = models.PositiveIntegerField(_('minimum experience (years)'), default=0)
    max_experience_years = models.PositiveIntegerField(_('maximum experience (years)'), null=True, blank=True)
    education_level = models.CharField(
        _('education level'),
        max_length=20,
        choices=[
            ('HIGH_SCHOOL', _('High School')),
            ('ASSOCIATE', _('Associate Degree')),
            ('BACHELOR', _('Bachelor Degree')),
            ('MASTER', _('Master Degree')),
            ('DOCTORATE', _('Doctorate')),
            ('CERTIFICATION', _('Professional Certification')),
        ],
        blank=True
    )
    
    # Skills and competencies
    required_skills = models.JSONField(_('required skills'), default=list)
    preferred_skills = models.JSONField(_('preferred skills'), default=list)
    languages = models.JSONField(_('languages'), default=list)
    
    # Compensation
    salary_min = models.DecimalField(_('minimum salary'), max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(_('maximum salary'), max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    benefits = models.TextField(_('benefits'), blank=True)
    
    # Job management
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    positions_available = models.PositiveIntegerField(_('positions available'), default=1)
    positions_filled = models.PositiveIntegerField(_('positions filled'), default=0)
    
    # Timeline
    posted_date = models.DateField(_('posted date'), null=True, blank=True)
    application_deadline = models.DateField(_('application deadline'), null=True, blank=True)
    target_start_date = models.DateField(_('target start date'), null=True, blank=True)
    
    # Assessment requirements
    requires_assessment = models.BooleanField(_('requires assessment'), default=True)
    assessment_definition = models.ForeignKey(
        'assessments.AssessmentDefinition',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='required_for_jobs'
    )
    
    # Recruiter assignment
    assigned_recruiter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_jobs'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Job')
        verbose_name_plural = _('Jobs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client.name} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('recruiting:job_detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        return self.status in ['OPEN', 'IN_PROGRESS']
    
    @property
    def is_filled(self):
        return self.positions_filled >= self.positions_available
    
    @property
    def applications_count(self):
        return self.applications.count()
    
    @property
    def qualified_candidates_count(self):
        return self.applications.filter(status__in=['QUALIFIED', 'INTERVIEWED', 'OFFERED']).count()


class Candidate(BaseTenantModel):
    """
    Candidates in the recruiting pipeline.
    """
    
    STATUS_CHOICES = [
        ('NEW', _('New')),
        ('SCREENING', _('Screening')),
        ('QUALIFIED', _('Qualified')),
        ('REJECTED', _('Rejected')),
        ('PLACED', _('Placed')),
        ('BLACKLISTED', _('Blacklisted')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Personal information
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    email = EncryptedEmailField(_('email address'), unique=True)
    phone = EncryptedTextField(_('phone number'), blank=True)
    
    # Professional information
    current_title = models.CharField(_('current job title'), max_length=200, blank=True)
    current_company = models.CharField(_('current company'), max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(_('years of experience'), default=0)
    education_level = models.CharField(
        _('education level'),
        max_length=20,
        choices=[
            ('HIGH_SCHOOL', _('High School')),
            ('ASSOCIATE', _('Associate Degree')),
            ('BACHELOR', _('Bachelor Degree')),
            ('MASTER', _('Master Degree')),
            ('DOCTORATE', _('Doctorate')),
            ('CERTIFICATION', _('Professional Certification')),
        ],
        blank=True
    )
    
    # Location and availability
    location = models.CharField(_('location'), max_length=200, blank=True)
    willing_to_relocate = models.BooleanField(_('willing to relocate'), default=False)
    remote_work_preference = models.CharField(
        _('remote work preference'),
        max_length=20,
        choices=[
            ('OFFICE_ONLY', _('Office Only')),
            ('HYBRID', _('Hybrid')),
            ('REMOTE_ONLY', _('Remote Only')),
            ('FLEXIBLE', _('Flexible')),
        ],
        default='FLEXIBLE'
    )
    
    # Skills and competencies
    skills = models.JSONField(_('skills'), default=list)
    languages = models.JSONField(_('languages'), default=list)
    certifications = models.JSONField(_('certifications'), default=list)
    
    # Compensation expectations
    salary_expectation_min = models.DecimalField(_('minimum salary expectation'), max_digits=12, decimal_places=2, null=True, blank=True)
    salary_expectation_max = models.DecimalField(_('maximum salary expectation'), max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Documents
    resume_file = models.FileField(_('resume'), upload_to='resumes/', blank=True)
    portfolio_url = models.URLField(_('portfolio URL'), blank=True)
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True)
    
    # Status and notes
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='NEW')
    notes = models.TextField(_('internal notes'), blank=True)
    
    # Source tracking
    source = models.CharField(
        _('source'),
        max_length=50,
        choices=[
            ('REFERRAL', _('Referral')),
            ('LINKEDIN', _('LinkedIn')),
            ('JOB_BOARD', _('Job Board')),
            ('COMPANY_WEBSITE', _('Company Website')),
            ('SOCIAL_MEDIA', _('Social Media')),
            ('DIRECT_CONTACT', _('Direct Contact')),
            ('OTHER', _('Other')),
        ],
        default='OTHER'
    )
    source_details = models.CharField(_('source details'), max_length=200, blank=True)
    
    # Recruiter assignment
    assigned_recruiter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_candidates'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Candidate')
        verbose_name_plural = _('Candidates')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        return reverse('recruiting:candidate_detail', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def active_applications_count(self):
        return self.applications.filter(status__in=['APPLIED', 'SCREENING', 'INTERVIEWED']).count()
    
    @property
    def assessment_completed(self):
        # Corrected: Filter by the status of the related AssessmentInstance
        return self.assessment_instances.filter(assessment_instance__status='COMPLETED').exists()


class JobApplication(BaseTenantModel):
    """
    Application of a candidate to a specific job.
    """
    
    STATUS_CHOICES = [
        ('APPLIED', _('Applied')),
        ('SCREENING', _('Screening')),
        ('ASSESSMENT_SENT', _('Assessment Sent')),
        ('ASSESSMENT_COMPLETED', _('Assessment Completed')),
        ('QUALIFIED', _('Qualified')),
        ('INTERVIEWED', _('Interviewed')),
        ('OFFERED', _('Offered')),
        ('HIRED', _('Hired')),
        ('REJECTED', _('Rejected')),
        ('WITHDRAWN', _('Withdrawn')),
    ]
    
    REJECTION_REASONS = [
        ('SKILLS_MISMATCH', _('Skills Mismatch')),
        ('EXPERIENCE_INSUFFICIENT', _('Insufficient Experience')),
        ('SALARY_MISMATCH', _('Salary Expectations Mismatch')),
        ('LOCATION_INCOMPATIBLE', _('Location Incompatible')),
        ('ASSESSMENT_FAILED', _('Assessment Results')),
        ('INTERVIEW_PERFORMANCE', _('Interview Performance')),
        ('REFERENCE_CHECK', _('Reference Check Issues')),
        ('OTHER', _('Other')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    
    # Application details
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    applied_date = models.DateTimeField(_('applied date'), auto_now_add=True)
    cover_letter = models.TextField(_('cover letter'), blank=True)
    
    # Assessment integration
    assessment_instance = models.ForeignKey(
        'assessments.AssessmentInstance',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='job_applications'
    )
    assessment_score = models.JSONField(_('assessment scores'), default=dict, blank=True)
    fit_score = models.FloatField(_('job fit score'), null=True, blank=True)
    
    # Interview process
    interview_scheduled_date = models.DateTimeField(_('interview scheduled'), null=True, blank=True)
    interview_completed_date = models.DateTimeField(_('interview completed'), null=True, blank=True)
    interview_notes = models.TextField(_('interview notes'), blank=True)
    interview_rating = models.PositiveIntegerField(_('interview rating'), null=True, blank=True)
    
    # Offer details
    offer_extended_date = models.DateTimeField(_('offer extended'), null=True, blank=True)
    offer_amount = models.DecimalField(_('offer amount'), max_digits=12, decimal_places=2, null=True, blank=True)
    offer_currency = models.CharField(_('offer currency'), max_length=3, default='USD')
    offer_accepted_date = models.DateTimeField(_('offer accepted'), null=True, blank=True)
    start_date = models.DateField(_('start date'), null=True, blank=True)
    
    # Rejection handling
    rejection_date = models.DateTimeField(_('rejection date'), null=True, blank=True)
    rejection_reason = models.CharField(_('rejection reason'), max_length=30, choices=REJECTION_REASONS, blank=True)
    rejection_notes = models.TextField(_('rejection notes'), blank=True)
    
    # Recruiter tracking
    recruiter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_applications'
    )
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Job Application')
        verbose_name_plural = _('Job Applications')
        unique_together = ['candidate', 'job']
        ordering = ['-applied_date']
    
    def __str__(self):
        return f"{self.candidate.full_name} → {self.job.title}"
    
    def get_absolute_url(self):
        return reverse('recruiting:application_detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        return self.status not in ['HIRED', 'REJECTED', 'WITHDRAWN']
    
    @property
    def days_in_pipeline(self):
        from django.utils import timezone
        return (timezone.now().date() - self.applied_date.date()).days
    
    def calculate_fit_score(self):
        """Calculate job fit score based on assessment and job requirements."""
        if not self.assessment_instance or not self.assessment_instance.is_completed:
            return None
        
        # Basic fit score calculation (would be more sophisticated in real implementation)
        try:
            score_profile = self.assessment_instance.score_profile
            job_requirements = self.job.required_skills
            
            # Simple matching algorithm
            if score_profile.dimension_scores and job_requirements:
                # This is a placeholder - real implementation would be more complex
                base_score = 50.0
                
                # Adjust based on experience match
                exp_match = min(self.candidate.experience_years / max(self.job.min_experience_years, 1), 2.0)
                base_score += exp_match * 20
                
                # Adjust based on skills match (simplified)
                candidate_skills = set(skill.lower() for skill in self.candidate.skills)
                required_skills = set(skill.lower() for skill in job_requirements)
                
                if required_skills:
                    skills_match = len(candidate_skills.intersection(required_skills)) / len(required_skills)
                    base_score += skills_match * 30
                
                return min(100.0, max(0.0, base_score))
            
        except Exception:
            pass
        
        return None
    
    def update_fit_score(self):
        """Update and save fit score."""
        self.fit_score = self.calculate_fit_score()
        self.save(update_fields=['fit_score'])


class CandidateNote(models.Model):
    """
    Notes and comments about candidates.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='candidate_notes')
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    
    # Note content
    content = models.TextField(_('content'))
    note_type = models.CharField(
        _('note type'),
        max_length=20,
        choices=[
            ('GENERAL', _('General')),
            ('SCREENING', _('Screening')),
            ('INTERVIEW', _('Interview')),
            ('REFERENCE', _('Reference Check')),
            ('ASSESSMENT', _('Assessment')),
            ('OFFER', _('Offer')),
        ],
        default='GENERAL'
    )
    is_private = models.BooleanField(_('private note'), default=False)
    
    # Author
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidate_notes')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Candidate Note')
        verbose_name_plural = _('Candidate Notes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note on {self.candidate.full_name} by {self.author.full_name}"


class Interview(BaseTenantModel):
    """
    Interview sessions for job applications.
    """
    
    INTERVIEW_TYPES = [
        ('PHONE', _('Phone Screen')),
        ('VIDEO', _('Video Interview')),
        ('IN_PERSON', _('In-Person')),
        ('TECHNICAL', _('Technical Interview')),
        ('BEHAVIORAL', _('Behavioral Interview')),
        ('PANEL', _('Panel Interview')),
        ('FINAL', _('Final Interview')),
    ]
    
    STATUS_CHOICES = [
        ('SCHEDULED', _('Scheduled')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
        ('NO_SHOW', _('No Show')),
        ('RESCHEDULED', _('Rescheduled')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    
    # Interview details
    interview_type = models.CharField(_('interview type'), max_length=20, choices=INTERVIEW_TYPES)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Scheduling
    scheduled_date = models.DateTimeField(_('scheduled date'))
    duration_minutes = models.PositiveIntegerField(_('duration (minutes)'), default=60)
    location_or_link = models.CharField(_('location or video link'), max_length=500, blank=True)
    
    # Participants
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conducted_interviews')
    additional_interviewers = models.ManyToManyField(User, blank=True, related_name='participated_interviews')
    
    # Results
    completed_date = models.DateTimeField(_('completed date'), null=True, blank=True)
    overall_rating = models.PositiveIntegerField(_('overall rating (1-10)'), null=True, blank=True)
    technical_rating = models.PositiveIntegerField(_('technical rating (1-10)'), null=True, blank=True)
    communication_rating = models.PositiveIntegerField(_('communication rating (1-10)'), null=True, blank=True)
    cultural_fit_rating = models.PositiveIntegerField(_('cultural fit rating (1-10)'), null=True, blank=True)
    
    # Feedback
    feedback = models.TextField(_('interview feedback'), blank=True)
    strengths = models.TextField(_('strengths'), blank=True)
    concerns = models.TextField(_('concerns'), blank=True)
    recommendation = models.CharField(
        _('recommendation'),
        max_length=20,
        choices=[
            ('STRONG_HIRE', _('Strong Hire')),
            ('HIRE', _('Hire')),
            ('MAYBE', _('Maybe')),
            ('NO_HIRE', _('No Hire')),
            ('STRONG_NO_HIRE', _('Strong No Hire')),
        ],
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Interview')
        verbose_name_plural = _('Interviews')
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.get_interview_type_display()} - {self.application.candidate.full_name}"
    
    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.scheduled_date > timezone.now() and self.status == 'SCHEDULED'
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return (self.scheduled_date < timezone.now() and 
                self.status in ['SCHEDULED', 'IN_PROGRESS'])


class Placement(BaseTenantModel):
    """
    Successful job placements.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='placement')
    
    # Placement details
    start_date = models.DateField(_('start date'))
    salary = models.DecimalField(_('salary'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    commission_earned = models.DecimalField(_('commission earned'), max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Guarantee period
    guarantee_period_days = models.PositiveIntegerField(_('guarantee period (days)'), default=90)
    guarantee_end_date = models.DateField(_('guarantee end date'), null=True, blank=True)
    
    # Status tracking
    is_active = models.BooleanField(_('active placement'), default=True)
    termination_date = models.DateField(_('termination date'), null=True, blank=True)
    termination_reason = models.CharField(
        _('termination reason'),
        max_length=50,
        choices=[
            ('VOLUNTARY', _('Voluntary Resignation')),
            ('INVOLUNTARY', _('Terminated by Company')),
            ('PERFORMANCE', _('Performance Issues')),
            ('LAYOFF', _('Layoff')),
            ('OTHER', _('Other')),
        ],
        blank=True
    )
    
    # Follow-up
    follow_up_30_days = models.BooleanField(_('30-day follow-up completed'), default=False)
    follow_up_60_days = models.BooleanField(_('60-day follow-up completed'), default=False)
    follow_up_90_days = models.BooleanField(_('90-day follow-up completed'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Placement')
        verbose_name_plural = _('Placements')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.application.candidate.full_name} → {self.application.job.title}"
    
    def save(self, *args, **kwargs):
        # Calculate guarantee end date
        if self.start_date and not self.guarantee_end_date:
            from datetime import timedelta
            self.guarantee_end_date = self.start_date + timedelta(days=self.guarantee_period_days)
        
        # Calculate commission
        if not self.commission_earned and self.salary:
            commission_rate = self.application.job.client.commission_rate / 100
            self.commission_earned = self.salary * commission_rate
        
        super().save(*args, **kwargs)
    
    @property
    def is_within_guarantee(self):
        from django.utils import timezone
        return (self.guarantee_end_date and 
                timezone.now().date() <= self.guarantee_end_date and
                self.is_active)
    
    @property
    def days_since_start(self):
        from django.utils import timezone
        return (timezone.now().date() - self.start_date).days


class CandidateAssessment(BaseTenantModel):
    """
    Link between candidates and their assessment instances.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='assessment_instances')
    assessment_instance = models.ForeignKey(
        'assessments.AssessmentInstance',
        on_delete=models.CASCADE,
        related_name='candidate_assessments'
    )
    job_application = models.ForeignKey(
        JobApplication, on_delete=models.CASCADE, null=True, blank=True,
        related_name='assessments'
    )
    
    # Assessment context
    purpose = models.CharField(
        _('assessment purpose'),
        max_length=20,
        choices=[
            ('SCREENING', _('Initial Screening')),
            ('DETAILED', _('Detailed Assessment')),
            ('COMPARISON', _('Candidate Comparison')),
            ('DEVELOPMENT', _('Development Planning')),
        ],
        default='SCREENING'
    )
    
    # Results summary
    overall_score = models.FloatField(_('overall score'), null=True, blank=True)
    personality_summary = models.TextField(_('personality summary'), blank=True)
    strengths = models.JSONField(_('strengths'), default=list)
    development_areas = models.JSONField(_('development areas'), default=list)
    job_fit_analysis = models.TextField(_('job fit analysis'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Candidate Assessment')
        verbose_name_plural = _('Candidate Assessments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.assessment_instance.assessment.name}"


class RecruitingPipeline(BaseTenantModel):
    """
    Recruiting pipeline configuration and tracking.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('pipeline name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Pipeline stages configuration
    stages = models.JSONField(_('pipeline stages'), default=list)
    default_stage_durations = models.JSONField(_('default stage durations'), default=dict)
    
    # Assessment integration
    assessment_stage = models.CharField(_('assessment stage'), max_length=50, default='SCREENING')
    required_assessment = models.ForeignKey(
        'assessments.AssessmentDefinition',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recruiting_pipelines'
    )
    
    # Automation settings
    auto_advance_on_assessment = models.BooleanField(_('auto advance on assessment completion'), default=True)
    auto_reject_on_low_score = models.BooleanField(_('auto reject on low assessment score'), default=False)
    min_assessment_score = models.FloatField(_('minimum assessment score'), default=60.0)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_default = models.BooleanField(_('default pipeline'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Recruiting Pipeline')
        verbose_name_plural = _('Recruiting Pipelines')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one default pipeline per organization
        if self.is_default:
            RecruitingPipeline.objects.filter(
                organization=self.organization,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)


class CandidateRanking(BaseTenantModel):
    """
    Ranking of candidates for specific jobs or general talent pool.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='candidate_rankings')
    name = models.CharField(_('ranking name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Ranking criteria
    criteria = models.JSONField(_('ranking criteria'), default=dict)
    weights = models.JSONField(_('criteria weights'), default=dict)
    
    # Candidates in ranking
    candidates = models.ManyToManyField(Candidate, through='CandidateRankingEntry', related_name='rankings')
    
    # Configuration
    auto_update = models.BooleanField(_('auto update rankings'), default=True)
    include_assessment_scores = models.BooleanField(_('include assessment scores'), default=True)
    include_interview_ratings = models.BooleanField(_('include interview ratings'), default=True)
    include_experience_match = models.BooleanField(_('include experience match'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Candidate Ranking')
        verbose_name_plural = _('Candidate Rankings')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class CandidateRankingEntry(models.Model):
    """
    Individual candidate entry in a ranking.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ranking = models.ForeignKey(CandidateRanking, on_delete=models.CASCADE, related_name='entries')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ranking_entries')
    
    # Ranking data
    rank = models.PositiveIntegerField(_('rank'))
    total_score = models.FloatField(_('total score'))
    score_breakdown = models.JSONField(_('score breakdown'), default=dict)
    
    # Individual scores
    assessment_score = models.FloatField(_('assessment score'), null=True, blank=True)
    interview_score = models.FloatField(_('interview score'), null=True, blank=True)
    experience_score = models.FloatField(_('experience score'), null=True, blank=True)
    skills_match_score = models.FloatField(_('skills match score'), null=True, blank=True)
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Candidate Ranking Entry')
        verbose_name_plural = _('Candidate Ranking Entries')
        unique_together = ['ranking', 'candidate']
        ordering = ['rank']
    
    def __str__(self):
        return f"#{self.rank} {self.candidate.full_name} ({self.total_score:.1f})"


class RecruitingReport(BaseTenantModel):
    """
    Generated reports for recruiting activities.
    """
    
    REPORT_TYPES = [
        ('CLIENT_SUMMARY', _('Client Summary')),
        ('CANDIDATE_PROFILE', _('Candidate Profile')),
        ('JOB_ANALYSIS', _('Job Analysis')),
        ('PIPELINE_METRICS', _('Pipeline Metrics')),
        ('PLACEMENT_REPORT', _('Placement Report')),
        ('ASSESSMENT_SUMMARY', _('Assessment Summary')),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', _('PDF Report')),
        ('HTML', _('HTML Report')),
        ('EXCEL', _('Excel Spreadsheet')),
        ('CSV', _('CSV Data')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(_('report type'), max_length=20, choices=REPORT_TYPES)
    format = models.CharField(_('format'), max_length=10, choices=FORMAT_CHOICES, default='PDF')
    
    # Report scope
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    
    # Report content
    title = models.CharField(_('title'), max_length=200)
    content = models.TextField(_('content'), blank=True)
    data = models.JSONField(_('report data'), default=dict)
    file_path = models.CharField(_('file path'), max_length=500, blank=True)
    
    # Date range for metrics
    date_from = models.DateField(_('date from'), null=True, blank=True)
    date_to = models.DateField(_('date to'), null=True, blank=True)
    
    # Access control
    is_confidential = models.BooleanField(_('confidential'), default=True)
    shared_with_client = models.BooleanField(_('shared with client'), default=False)
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Recruiting Report')
        verbose_name_plural = _('Recruiting Reports')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} ({self.format})"
    
    def get_absolute_url(self):
        return reverse('recruiting:report_detail', kwargs={'pk': self.pk})