"""
Views for recruiting app.
"""
import csv
import io
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView
)
from django.views import View
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor

from organizations.mixins import OrganizationPermissionMixin, RecruiterOnlyMixin
from .models import (
    Client, Job, Candidate, JobApplication, Interview, Placement,
    CandidateNote, CandidateAssessment, RecruitingPipeline, CandidateRanking
)
from .forms import (
    ClientForm, JobForm, CandidateForm, JobApplicationForm, InterviewForm,
    CandidateNoteForm, PlacementForm, CandidateSearchForm, JobSearchForm,
    BulkCandidateImportForm
)


class RecruitingDashboardView(LoginRequiredMixin, RecruiterOnlyMixin, ListView):
    """Recruiting dashboard with overview and statistics."""
    model = Job
    template_name = 'recruiting/dashboard.html'
    context_object_name = 'recent_jobs'
    required_role = 'RECRUITER'
    
    def get_queryset(self):
        return Job.objects.filter(
            organization=self.get_organization(),
            status__in=['OPEN', 'IN_PROGRESS']
        ).order_by('-created_at')[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Dashboard statistics
        context['stats'] = {
            'active_jobs': Job.objects.filter(organization=organization, status__in=['OPEN', 'IN_PROGRESS']).count(),
            'total_candidates': Candidate.objects.filter(organization=organization).count(),
            'active_applications': JobApplication.objects.filter(organization=organization, status__in=['APPLIED', 'SCREENING', 'INTERVIEWED']).count(),
            'placements_this_month': Placement.objects.filter(
                organization=organization,
                start_date__month=timezone.now().month,
                start_date__year=timezone.now().year
            ).count(),
        }
        
        # Recent activity
        context['recent_applications'] = JobApplication.objects.filter(
            organization=organization
        ).select_related('candidate', 'job', 'recruiter').order_by('-applied_date')[:5]
        
        context['upcoming_interviews'] = Interview.objects.filter(
            organization=organization,
            status='SCHEDULED',
            scheduled_date__gte=timezone.now()
        ).select_related('application__candidate', 'application__job').order_by('scheduled_date')[:5]
        
        # User-specific data
        user = self.request.user
        context['my_jobs'] = Job.objects.filter(
            organization=organization,
            assigned_recruiter=user,
            status__in=['OPEN', 'IN_PROGRESS']
        ).count()
        
        context['my_candidates'] = Candidate.objects.filter(
            organization=organization,
            assigned_recruiter=user
        ).count()
        
        return context


# Client Views
class ClientListView(LoginRequiredMixin, RecruiterOnlyMixin, ListView):
    """List clients."""
    model = Client
    template_name = 'recruiting/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    required_role = 'RECRUITER'
    
    def get_queryset(self):
        return Client.objects.filter(
            organization=self.get_organization()
        ).order_by('name')


class ClientDetailView(LoginRequiredMixin, RecruiterOnlyMixin, DetailView):
    """Client detail view."""
    model = Client
    template_name = 'recruiting/client_detail.html'
    context_object_name = 'client'
    required_role = 'RECRUITER'


class ClientCreateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, CreateView):
    """Create new client."""
    model = Client
    form_class = ClientForm
    template_name = 'recruiting/client_form.html'
    success_message = _('Client created successfully!')
    required_role = 'RECRUITER'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        
        # Ensure organization is set before validation
        if not form.instance.organization:
            from django.contrib import messages
            messages.error(self.request, _('No organization context available. Please try again.'))
            return self.form_invalid(form)
        
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, UpdateView):
    """Update client."""
    model = Client
    form_class = ClientForm
    template_name = 'recruiting/client_form.html'
    success_message = _('Client updated successfully!')
    required_role = 'RECRUITER'


# Job Views
class JobListView(LoginRequiredMixin, RecruiterOnlyMixin, ListView):
    """List jobs."""
    model = Job
    template_name = 'recruiting/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 20
    required_role = 'RECRUITER'
    
    def get_queryset(self):
        queryset = Job.objects.filter(
            organization=self.get_organization()
        ).select_related('client', 'assigned_recruiter')
        
        # Apply search filters
        form = JobSearchForm(self.get_organization(), self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            client = form.cleaned_data.get('client')
            status = form.cleaned_data.get('status')
            priority = form.cleaned_data.get('priority')
            employment_type = form.cleaned_data.get('employment_type')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(client__name__icontains=search)
                )
            
            if client:
                queryset = queryset.filter(client=client)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if priority:
                queryset = queryset.filter(priority=priority)
            
            if employment_type:
                queryset = queryset.filter(employment_type=employment_type)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = JobSearchForm(self.get_organization(), self.request.GET)
        return context


class JobDetailView(LoginRequiredMixin, RecruiterOnlyMixin, DetailView):
    """Job detail view."""
    model = Job
    template_name = 'recruiting/job_detail.html'
    context_object_name = 'job'
    required_role = 'RECRUITER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get applications for this job - defensive check
        try:
            context['applications'] = self.object.applications.select_related(
                'candidate', 'recruiter'
            ).order_by('-applied_date')
        except AttributeError:
            # Fallback if applications attribute has issues
            context['applications'] = JobApplication.objects.filter(
                job=self.object
            ).select_related('candidate', 'recruiter').order_by('-applied_date')
        
        # Application statistics
        applications = context['applications']
        context['application_stats'] = {
            'total': applications.count(),
            'qualified': applications.filter(status__in=['QUALIFIED', 'INTERVIEWED', 'OFFERED']).count(),
            'in_progress': applications.filter(status__in=['SCREENING', 'ASSESSMENT_SENT', 'INTERVIEWED']).count(),
            'rejected': applications.filter(status='REJECTED').count(),
        }
        
        return context


class JobCreateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, CreateView):
    """Create new job."""
    model = Job
    form_class = JobForm
    template_name = 'recruiting/job_form.html'
    success_message = _('Job created successfully!')
    required_role = 'RECRUITER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class JobUpdateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, UpdateView):
    """Update job."""
    model = Job
    form_class = JobForm
    template_name = 'recruiting/job_form.html'
    success_message = _('Job updated successfully!')
    required_role = 'RECRUITER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_context_data(self, **kwargs):
        # Override get_context_data to prevent it from trying to load related objects
        # that might cause issues if the object is not fully initialized or if
        # there are unexpected data types in the relationships.
        # The form itself should handle populating its fields from the object.
        return super().get_context_data(**kwargs)


# Candidate Views
class CandidateListView(LoginRequiredMixin, RecruiterOnlyMixin, ListView):
    """List candidates."""
    model = Candidate
    template_name = 'recruiting/candidate_list.html'
    context_object_name = 'candidates'
    paginate_by = 20
    required_role = 'RECRUITER'
    
    def get_queryset(self):
        queryset = Candidate.objects.filter(
            organization=self.get_organization()
        ).select_related('assigned_recruiter')
        
        # Apply search filters
        form = CandidateSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            experience_min = form.cleaned_data.get('experience_min')
            experience_max = form.cleaned_data.get('experience_max')
            education_level = form.cleaned_data.get('education_level')
            remote_work_preference = form.cleaned_data.get('remote_work_preference')
            skills = form.cleaned_data.get('skills')
            
            if search:
                queryset = queryset.filter(
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(current_title__icontains=search) |
                    Q(current_company__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status)
            
            if experience_min is not None:
                queryset = queryset.filter(experience_years__gte=experience_min)
            
            if experience_max is not None:
                queryset = queryset.filter(experience_years__lte=experience_max)
            
            if education_level:
                queryset = queryset.filter(education_level=education_level)
            
            if remote_work_preference:
                queryset = queryset.filter(remote_work_preference=remote_work_preference)
            
            if skills:
                skill_list = [skill.strip().lower() for skill in skills.split(',')]
                for skill in skill_list:
                    queryset = queryset.filter(skills__icontains=skill)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = CandidateSearchForm(self.request.GET)
        
        # Statistics
        organization = self.get_organization()
        context['stats'] = {
            'total_candidates': Candidate.objects.filter(organization=organization).count(),
            'new_candidates': Candidate.objects.filter(organization=organization, status='NEW').count(),
            'qualified_candidates': Candidate.objects.filter(organization=organization, status='QUALIFIED').count(),
            'placed_candidates': Candidate.objects.filter(organization=organization, status='PLACED').count(),
        }
        
        return context


class CandidateDetailView(LoginRequiredMixin, RecruiterOnlyMixin, DetailView):
    """Candidate detail view."""
    model = Candidate
    template_name = 'recruiting/candidate_detail.html'
    context_object_name = 'candidate'
    required_role = 'RECRUITER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Defensive check for applications attribute
        if hasattr(self.object.applications, 'select_related'):
            context['applications'] = self.object.applications.select_related(
                'job', 'job__client', 'recruiter'
            ).order_by('-applied_date')
        else:
            # Fallback if applications doesn't have select_related method
            # This indicates a deeper issue, but allows the page to load.
            print(f"WARNING: self.object.applications is of type {type(self.object.applications)}, expected a manager.")
            context['applications'] = JobApplication.objects.filter(candidate=self.object).select_related(
                'job', 'job__client', 'recruiter'
            ).order_by('-applied_date')
        
        # Defensive check for assessment_instances attribute
        if hasattr(self.object.assessment_instances, 'select_related'):
            context['assessments'] = self.object.assessment_instances.select_related(
                'assessment_instance__assessment'
            ).order_by('-created_at')
        else:
            print(f"WARNING: self.object.assessment_instances is of type {type(self.object.assessment_instances)}, expected a manager.")
            context['assessments'] = CandidateAssessment.objects.filter(candidate=self.object).select_related(
                'assessment_instance__assessment'
            ).order_by('-created_at')
        
        # Defensive check for candidate_notes attribute
        if hasattr(self.object.candidate_notes, 'select_related'):
            context['notes'] = self.object.candidate_notes.select_related('author').order_by('-created_at')[:10]
        else:
            print(f"WARNING: self.object.candidate_notes is of type {type(self.object.candidate_notes)}, expected a manager.")
            context['notes'] = CandidateNote.objects.filter(candidate=self.object).select_related('author').order_by('-created_at')[:10]
        
        return context


class CandidateCreateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, CreateView):
    """Create new candidate."""
    model = Candidate
    form_class = CandidateForm
    template_name = 'recruiting/candidate_form.html'
    success_message = _('Candidate created successfully!')
    required_role = 'RECRUITER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class CandidateUpdateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, UpdateView):
    """Update candidate."""
    model = Candidate
    form_class = CandidateForm
    template_name = 'recruiting/candidate_form.html'
    success_message = _('Candidate updated successfully!')
    required_role = 'RECRUITER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs


# Job Application Views
class JobApplicationCreateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, CreateView):
    """Create job application."""
    model = JobApplication
    form_class = JobApplicationForm
    template_name = 'recruiting/application_form.html'
    success_message = _('Job application created successfully!')
    required_role = 'RECRUITER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('recruiting:candidate_detail', kwargs={'pk': self.object.candidate.pk})


class JobApplicationDetailView(LoginRequiredMixin, RecruiterOnlyMixin, DetailView):
    """Job application detail view."""
    model = JobApplication
    template_name = 'recruiting/application_detail.html'
    context_object_name = 'application'
    required_role = 'RECRUITER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get interviews for this application
        context['interviews'] = self.object.interviews.select_related('interviewer').order_by('-scheduled_date')
        
        # Get placement if exists
        try:
            context['placement'] = self.object.placement
        except Placement.DoesNotExist:
            context['placement'] = None
        
        return context


# Interview Views
class InterviewCreateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, CreateView):
    """Create interview."""
    model = Interview
    form_class = InterviewForm
    template_name = 'recruiting/interview_form.html'
    success_message = _('Interview scheduled successfully!')
    required_role = 'RECRUITER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        application = get_object_or_404(JobApplication, pk=self.kwargs['application_pk'])
        form.instance.application = application
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('recruiting:application_detail', kwargs={'pk': self.object.application.pk})


class InterviewUpdateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, UpdateView):
    """Update interview."""
    model = Interview
    form_class = InterviewForm
    template_name = 'recruiting/interview_form.html'
    success_message = _('Interview updated successfully!')
    required_role = 'RECRUITER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('recruiting:application_detail', kwargs={'pk': self.object.application.pk})


# Placement Views
class PlacementCreateView(LoginRequiredMixin, RecruiterOnlyMixin, SuccessMessageMixin, CreateView):
    """Create placement."""
    model = Placement
    form_class = PlacementForm
    template_name = 'recruiting/placement_form.html'
    success_message = _('Placement recorded successfully!')
    required_role = 'RECRUITER'
    
    def form_valid(self, form):
        application = get_object_or_404(JobApplication, pk=self.kwargs['application_pk'])
        form.instance.application = application
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        
        # Update application status
        application.status = 'HIRED'
        application.save()
        
        # Update candidate status
        application.candidate.status = 'PLACED'
        application.candidate.save()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('recruiting:application_detail', kwargs={'pk': self.object.application.pk})


class PlacementListView(LoginRequiredMixin, RecruiterOnlyMixin, ListView):
    """List placements."""
    model = Placement
    template_name = 'recruiting/placement_list.html'
    context_object_name = 'placements'
    paginate_by = 20
    required_role = 'RECRUITER'
    
    def get_queryset(self):
        return Placement.objects.filter(
            organization=self.get_organization()
        ).select_related('application__candidate', 'application__job', 'application__job__client').order_by('-start_date')


# Candidate Note Views
class CandidateNoteCreateView(LoginRequiredMixin, RecruiterOnlyMixin, View):
    """Add note to candidate via AJAX."""
    required_role = 'RECRUITER'
    
    def post(self, request, pk):
        candidate = get_object_or_404(Candidate, pk=pk, organization=self.get_organization())
        
        content = request.POST.get('content', '').strip()
        note_type = request.POST.get('note_type', 'GENERAL')
        is_private = request.POST.get('is_private') == 'true'
        
        if not content:
            return JsonResponse({'error': 'Note content is required'}, status=400)
        
        note = CandidateNote.objects.create(
            candidate=candidate,
            content=content,
            note_type=note_type,
            is_private=is_private,
            author=request.user
        )
        
        return JsonResponse({
            'success': True,
            'note': {
                'id': str(note.id),
                'content': note.content,
                'note_type': note.get_note_type_display(),
                'author': note.author.full_name,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_private': note.is_private
            }
        })


# Bulk Operations
class BulkCandidateImportView(LoginRequiredMixin, RecruiterOnlyMixin, FormView):
    """Import candidates from CSV."""
    form_class = BulkCandidateImportForm
    template_name = 'recruiting/bulk_import.html'
    required_role = 'RECRUITER'
    
    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        organization = self.get_organization()
        
        try:
            with transaction.atomic():
                # Read CSV
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                created_count = 0
                updated_count = 0
                errors = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Extract required data
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        email = row.get('email', '').strip()
                        
                        if not all([first_name, last_name, email]):
                            errors.append(f'Row {row_num}: Missing required fields (first_name, last_name, email)')
                            continue
                        
                        # Create or update candidate
                        candidate, created = Candidate.objects.get_or_create(
                            email=email,
                            organization=organization,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'current_title': row.get('current_title', ''),
                                'current_company': row.get('current_company', ''),
                                'experience_years': int(row.get('experience_years', 0) or 0),
                                'location': row.get('location', ''),
                                'phone': row.get('phone', ''),
                                'created_by': self.request.user,
                            }
                        )
                        
                        # Update skills if provided
                        skills = row.get('skills', '')
                        if skills:
                            candidate.skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
                            candidate.save()
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
                
                # Show results
                if created_count or updated_count:
                    messages.success(
                        self.request,
                        _('Import completed: {} created, {} updated').format(created_count, updated_count)
                    )
                
                if errors:
                    error_msg = _('Import errors:') + '\n' + '\n'.join(errors[:10])
                    if len(errors) > 10:
                        error_msg += f'\n... and {len(errors) - 10} more errors'
                    messages.error(self.request, error_msg)
        
        except Exception as e:
            messages.error(self.request, _('Import failed: {}').format(str(e)))
        
        return redirect('recruiting:candidate_list')


# Reports and Analytics
class RecruitingReportsView(LoginRequiredMixin, RecruiterOnlyMixin, ListView):
    """Recruiting reports and analytics."""
    model = Job
    template_name = 'recruiting/reports.html'
    context_object_name = 'jobs'
    required_role = 'RECRUITER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Organization-wide statistics
        context['org_stats'] = {
            'total_clients': Client.objects.filter(organization=organization, is_active=True).count(),
            'active_jobs': Job.objects.filter(organization=organization, status__in=['OPEN', 'IN_PROGRESS']).count(),
            'total_candidates': Candidate.objects.filter(organization=organization).count(),
            'total_placements': Placement.objects.filter(organization=organization, is_active=True).count(),
            'avg_time_to_fill': 0,  # Would calculate from placement data
            'placement_rate': 0,  # Would calculate from application data
        }
        
        # Monthly metrics
        current_month = timezone.now().replace(day=1)
        context['monthly_stats'] = {
            'new_candidates': Candidate.objects.filter(
                organization=organization,
                created_at__gte=current_month
            ).count(),
            'new_applications': JobApplication.objects.filter(
                organization=organization,
                applied_date__gte=current_month
            ).count(),
            'placements': Placement.objects.filter(
                organization=organization,
                start_date__gte=current_month.date()
            ).count(),
            'interviews': Interview.objects.filter(
                organization=organization,
                scheduled_date__gte=current_month
            ).count(),
        }
        
        # Top performing metrics
        context['top_clients'] = Client.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            active_jobs_count=Count('jobs', filter=Q(jobs__status__in=['OPEN', 'IN_PROGRESS']))
        ).order_by('-active_jobs_count')[:5]
        
        return context


# AJAX Views
class UpdateApplicationStatusView(LoginRequiredMixin, RecruiterOnlyMixin, View):
    """Update job application status via AJAX."""
    required_role = 'RECRUITER'
    
    def post(self, request, pk):
        application = get_object_or_404(JobApplication, pk=pk, organization=self.get_organization())
        
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status not in dict(JobApplication.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        # Update application
        old_status = application.status
        application.status = new_status
        application.save()
        
        # Add note if provided
        if notes:
            CandidateNote.objects.create(
                candidate=application.candidate,
                application=application,
                content=f"Status changed from {old_status} to {new_status}: {notes}",
                note_type='GENERAL',
                author=request.user
            )
        
        return JsonResponse({
            'success': True,
            'status': application.get_status_display(),
            'message': f'Status updated to {application.get_status_display()}'
        })


class CandidateMatchingView(LoginRequiredMixin, RecruiterOnlyMixin, View):
    """Find matching candidates for a job."""
    required_role = 'RECRUITER'
    
    def get(self, request, job_pk):
        job = get_object_or_404(Job, pk=job_pk, organization=self.get_organization())
        
        # Basic matching algorithm
        candidates = Candidate.objects.filter(
            organization=self.get_organization(),
            status__in=['NEW', 'QUALIFIED']
        )
        
        # Filter by experience
        if job.min_experience_years:
            candidates = candidates.filter(experience_years__gte=job.min_experience_years)
        
        if job.max_experience_years:
            candidates = candidates.filter(experience_years__lte=job.max_experience_years)
        
        # Filter by education
        if job.education_level:
            education_hierarchy = {
                'HIGH_SCHOOL': 1,
                'ASSOCIATE': 2,
                'BACHELOR': 3,
                'MASTER': 4,
                'DOCTORATE': 5,
                'CERTIFICATION': 3,
            }
            min_education_level = education_hierarchy.get(job.education_level, 1)
            
            candidates = candidates.filter(
                education_level__in=[
                    level for level, value in education_hierarchy.items()
                    if value >= min_education_level
                ]
            )
        
        # Calculate match scores
        matched_candidates = []
        for candidate in candidates[:20]:  # Limit to top 20
            match_score = self._calculate_match_score(candidate, job)
            matched_candidates.append({
                'candidate': candidate,
                'match_score': match_score,
                'skills_match': self._calculate_skills_match(candidate, job),
            })
        
        # Sort by match score
        matched_candidates.sort(key=lambda x: x['match_score'], reverse=True)
        
        return render(request, 'recruiting/candidate_matching.html', {
            'job': job,
            'matched_candidates': matched_candidates[:10],  # Top 10
        })
    
    def _calculate_match_score(self, candidate, job):
        """Calculate basic match score between candidate and job."""
        score = 0.0
        
        # Experience match (30% weight)
        if job.min_experience_years <= candidate.experience_years:
            if job.max_experience_years:
                if candidate.experience_years <= job.max_experience_years:
                    score += 30  # Perfect match
                else:
                    score += 20  # Over-qualified
            else:
                score += 30
        else:
            # Under-qualified
            score += max(0, 15 - (job.min_experience_years - candidate.experience_years) * 3)
        
        # Skills match (40% weight)
        skills_match = self._calculate_skills_match(candidate, job)
        score += skills_match * 0.4
        
        # Location match (20% weight)
        if job.remote_allowed or candidate.willing_to_relocate:
            score += 20
        elif candidate.location.lower() in job.location.lower():
            score += 20
        else:
            score += 10
        
        # Education match (10% weight)
        education_hierarchy = {
            'HIGH_SCHOOL': 1, 'ASSOCIATE': 2, 'BACHELOR': 3,
            'MASTER': 4, 'DOCTORATE': 5, 'CERTIFICATION': 3,
        }
        
        candidate_edu = education_hierarchy.get(candidate.education_level, 1)
        job_edu = education_hierarchy.get(job.education_level, 1)
        
        if candidate_edu >= job_edu:
            score += 10
        else:
            score += max(0, 5 - (job_edu - candidate_edu) * 2)
        
        return min(100.0, max(0.0, score))
    
    def _calculate_skills_match(self, candidate, job):
        """Calculate skills match percentage."""
        if not job.required_skills:
            return 100.0
        
        candidate_skills = set(skill.lower() for skill in candidate.skills)
        required_skills = set(skill.lower() for skill in job.required_skills)
        
        if not required_skills:
            return 100.0
        
        matched_skills = candidate_skills.intersection(required_skills)
        return (len(matched_skills) / len(required_skills)) * 100


class RecruitingAnalyticsView(LoginRequiredMixin, RecruiterOnlyMixin, View):
    """Get recruiting analytics data for charts."""
    required_role = 'RECRUITER'
    
    def get(self, request):
        organization = self.get_organization()
        
        # Pipeline metrics
        pipeline_data = []
        for status_code, status_name in JobApplication.STATUS_CHOICES:
            count = JobApplication.objects.filter(
                organization=organization,
                status=status_code
            ).count()
            pipeline_data.append({
                'status': status_name,
                'count': count
            })
        
        # Monthly placements
        monthly_placements = []
        for i in range(12):
            month_date = timezone.now().replace(day=1) - timezone.timedelta(days=30*i)
            count = Placement.objects.filter(
                organization=organization,
                start_date__year=month_date.year,
                start_date__month=month_date.month
            ).count()
            monthly_placements.append({
                'month': month_date.strftime('%b %Y'),
                'count': count
            })
        
        return JsonResponse({
            'pipeline_data': pipeline_data,
            'monthly_placements': list(reversed(monthly_placements)),
        })