"""
Views for assessments app.
"""
import secrets
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView
)
from django.views import View

from organizations.mixins import OrganizationPermissionMixin
from .models import (
    AssessmentDefinition, AssessmentInstance, Question, Response, ScoreProfile
)
from .forms import (
    AssessmentDefinitionForm, AssessmentResponseForm, AssessmentInviteForm,
    AssessmentSearchForm
)


class AssessmentDefinitionListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List assessment definitions."""
    model = AssessmentDefinition
    template_name = 'assessments/assessment_definition_list.html'
    context_object_name = 'assessments'
    paginate_by = 20
    required_role = 'MEMBER'
    
    def get_queryset(self):
        queryset = AssessmentDefinition.objects.filter(
            organization=self.get_organization()
        ).select_related('created_by')
        
        # Apply search filters
        form = AssessmentSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            framework = form.cleaned_data.get('framework')
            status = form.cleaned_data.get('status')
            
            if search:
                queryset = queryset.filter(
                    models.Q(name__icontains=search) |
                    models.Q(description__icontains=search)
                )
            
            if framework:
                queryset = queryset.filter(framework=framework)
            
            if status:
                queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AssessmentSearchForm(self.request.GET)
        return context


class AssessmentDefinitionDetailView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Assessment definition detail view."""
    model = AssessmentDefinition
    template_name = 'assessments/assessment_detail.html'
    context_object_name = 'assessment'
    required_role = 'MEMBER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's assessment instances for this assessment
        user_instances = AssessmentInstance.objects.filter(
            assessment=self.object,
            user=self.request.user
        ).order_by('-invited_at')
        
        context['user_instances'] = user_instances
        context['can_take_assessment'] = self.object.is_active
        context['questions'] = self.object.questions.filter(is_active=True).order_by('order')
        
        return context


class AssessmentDefinitionCreateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Create new assessment definition."""
    model = AssessmentDefinition
    form_class = AssessmentDefinitionForm
    template_name = 'assessments/assessment_definition_form.html'
    success_message = _('Assessment created successfully!')
    required_role = 'HR'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('assessments:detail', kwargs={'pk': self.object.pk})


class AssessmentDefinitionUpdateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    """Update assessment definition."""
    model = AssessmentDefinition
    form_class = AssessmentDefinitionForm
    template_name = 'assessments/assessment_definition_form.html'
    success_message = _('Assessment updated successfully!')
    required_role = 'HR'
    
    def get_success_url(self):
        return reverse_lazy('assessments:detail', kwargs={'pk': self.object.pk})


class AssessmentInviteView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, FormView):
    """Invite users to take assessment."""
    form_class = AssessmentInviteForm
    template_name = 'assessments/assessment_invite.html'
    success_message = _('Assessment invitations sent successfully!')
    required_role = 'HR'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assessment'] = get_object_or_404(
            AssessmentDefinition,
            pk=self.kwargs['pk'],
            organization=self.get_organization()
        )
        return context
    
    def form_valid(self, form):
        assessment = get_object_or_404(
            AssessmentDefinition,
            pk=self.kwargs['pk'],
            organization=self.get_organization()
        )
        
        users = form.cleaned_data['users']
        expires_in_days = form.cleaned_data['expires_in_days']
        message = form.cleaned_data['message']
        
        expires_at = timezone.now() + timedelta(days=expires_in_days)
        
        created_count = 0
        
        with transaction.atomic():
            for user in users:
                # Check if user already has an active instance
                existing = AssessmentInstance.objects.filter(
                    assessment=assessment,
                    user=user,
                    status__in=['INVITED', 'STARTED', 'IN_PROGRESS']
                ).exists()
                
                if not existing:
                    AssessmentInstance.objects.create(
                        assessment=assessment,
                        user=user,
                        organization=self.get_organization(),
                        token=secrets.token_urlsafe(32),
                        invited_by=self.request.user,
                        expires_at=expires_at,
                        status='INVITED'
                    )
                    created_count += 1
        
        messages.success(
            self.request,
            _('Sent {} assessment invitations.').format(created_count)
        )
        
        return redirect('assessments:detail', pk=assessment.pk)


class AssessmentTakeView(View):
    """Take an assessment using token-based access."""
    
    def get(self, request, token):
        instance = get_object_or_404(AssessmentInstance, token=token)
        
        # Check if assessment is expired
        if instance.is_expired:
            messages.error(request, _('This assessment invitation has expired.'))
            return redirect('dashboard:home')
        
        # Check if already completed
        if instance.is_completed:
            return redirect('assessments:result', token=token)
        
        # Update status to started if not already
        if instance.status == 'INVITED':
            instance.status = 'STARTED'
            instance.started_at = timezone.now()
            instance.save()
        
        # Get questions
        questions = instance.assessment.questions.filter(is_active=True).order_by('order')
        
        # Get existing responses
        existing_responses = {
            r.question_id: r for r in instance.responses.select_related('question', 'selected_option')
        }
        
        # Create form with initial data
        initial_data = {}
        for question in questions:
            if question.id in existing_responses:
                response = existing_responses[question.id]
                if response.selected_option:
                    initial_data[f'question_{question.id}'] = response.selected_option.id
                elif response.numeric_value is not None:
                    initial_data[f'question_{question.id}'] = response.numeric_value
                elif response.text_value:
                    initial_data[f'question_{question.id}'] = response.text_value
        
        form = AssessmentResponseForm(questions, initial=initial_data)
        
        context = {
            'instance': instance,
            'assessment': instance.assessment,
            'questions': questions,
            'form': form,
            'progress_percentage': instance.calculate_progress(),
        }
        
        return render(request, 'assessments/assessment_take.html', context)
    
    def post(self, request, token):
        instance = get_object_or_404(AssessmentInstance, token=token)
        
        # Check if assessment is expired or completed
        if instance.is_expired or instance.is_completed:
            return redirect('assessments:result', token=token)
        
        questions = instance.assessment.questions.filter(is_active=True).order_by('order')
        form = AssessmentResponseForm(questions, request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                # Save responses
                for field_name, value in form.cleaned_data.items():
                    if field_name.startswith('question_'):
                        question_id = field_name.replace('question_', '')
                        question = get_object_or_404(Question, id=question_id)
                        
                        # Get or create response
                        response, created = Response.objects.get_or_create(
                            instance=instance,
                            question=question,
                            defaults={}
                        )
                        
                        # Set response value based on question type
                        if question.question_type in ['LIKERT_5', 'LIKERT_7']:
                            response.numeric_value = int(value)
                            response.selected_option = None
                            response.text_value = ''
                        elif question.question_type == 'MULTIPLE_CHOICE':
                            from .models import QuestionOption
                            response.selected_option = get_object_or_404(QuestionOption, id=value)
                            response.numeric_value = response.selected_option.value
                            response.text_value = ''
                        elif question.question_type == 'TEXT':
                            response.text_value = value
                            response.numeric_value = None
                            response.selected_option = None
                        
                        response.save()
                
                # Update progress
                instance.update_progress()
                
                # Check if assessment is complete
                total_questions = questions.count()
                answered_questions = instance.responses.count()
                
                if answered_questions >= total_questions:
                    instance.status = 'COMPLETED'
                    instance.completed_at = timezone.now()
                    instance.progress_percentage = 100.0
                    instance.save()
                    
                    # Calculate scores (basic implementation)
                    self._calculate_scores(instance)
                    
                    messages.success(request, _('Assessment completed successfully!'))
                    return redirect('assessments:result', token=token)
                else:
                    instance.status = 'IN_PROGRESS'
                    instance.save()
                    messages.success(request, _('Progress saved. You can continue later.'))
        
        # Re-render form with errors
        context = {
            'instance': instance,
            'assessment': instance.assessment,
            'questions': questions,
            'form': form,
            'progress_percentage': instance.calculate_progress(),
        }
        
        return render(request, 'assessments/assessment_take.html', context)
    
    def _calculate_scores(self, instance):
        """Calculate basic scores for completed assessment."""
        responses = instance.responses.select_related('question')
        
        # Group responses by dimension
        dimension_scores = {}
        dimension_counts = {}
        
        for response in responses:
            dimension = response.question.dimension or 'general'
            score = response.numeric_value or 0
            
            # Apply reverse scoring if needed
            if response.question.reverse_scored:
                if response.question.question_type == 'LIKERT_5':
                    score = 6 - score
                elif response.question.question_type == 'LIKERT_7':
                    score = 8 - score
            
            # Apply weight
            score *= response.question.weight
            
            if dimension not in dimension_scores:
                dimension_scores[dimension] = 0
                dimension_counts[dimension] = 0
            
            dimension_scores[dimension] += score
            dimension_counts[dimension] += 1
        
        # Calculate averages
        for dimension in dimension_scores:
            if dimension_counts[dimension] > 0:
                dimension_scores[dimension] /= dimension_counts[dimension]
        
        # Create or update score profile
        score_profile, created = ScoreProfile.objects.get_or_create(
            instance=instance,
            defaults={'organization': instance.organization}
        )
        
        score_profile.dimension_scores = dimension_scores
        # Simple percentile calculation (would be more sophisticated in real implementation)
        score_profile.percentile_scores = {
            dim: min(100, max(0, (score / 7.0) * 100)) 
            for dim, score in dimension_scores.items()
        }
        score_profile.save()


class AssessmentResultView(View):
    """View assessment results."""
    
    def get(self, request, token):
        instance = get_object_or_404(AssessmentInstance, token=token)
        
        # Check if user has permission to view results
        if not (instance.user == request.user or 
                request.user.has_perm('assessments.view_assessmentinstance')):
            raise Http404
        
        # Check if assessment is completed
        if not instance.is_completed:
            messages.warning(request, _('Assessment is not yet completed.'))
            return redirect('assessments:take', token=token)
        
        # Get score profile
        try:
            score_profile = instance.score_profile
        except ScoreProfile.DoesNotExist:
            score_profile = None
        
        context = {
            'instance': instance,
            'assessment': instance.assessment,
            'score_profile': score_profile,
            'responses': instance.responses.select_related('question', 'selected_option').order_by('question__order'),
        }
        
        return render(request, 'assessments/assessment_result.html', context)


class AssessmentInstanceListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List assessment instances for organization."""
    model = AssessmentInstance
    template_name = 'assessments/assessment_instance_list.html'
    context_object_name = 'instances'
    paginate_by = 50
    required_role = 'HR'
    
    def get_queryset(self):
        return AssessmentInstance.objects.filter(
            organization=self.get_organization()
        ).select_related('assessment', 'user', 'invited_by').order_by('-invited_at')