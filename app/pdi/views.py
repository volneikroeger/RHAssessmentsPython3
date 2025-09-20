"""
Views for PDI app.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView
)
from django.views import View

from organizations.mixins import OrganizationPermissionMixin, CompanyOnlyMixin
from .models import PDIPlan, PDITask, PDIProgressUpdate, PDIComment, PDIActionCatalog, PDITemplate
from .forms import (
    PDIPlanForm, PDITaskForm, PDIProgressUpdateForm, PDICommentForm,
    PDIActionCatalogForm, PDISearchForm, PDIApprovalForm, BulkPDIGenerationForm
)


class PDIPlanListView(LoginRequiredMixin, CompanyOnlyMixin, ListView):
    """List PDI plans."""
    model = PDIPlan
    template_name = 'pdi/pdi_plan_list.html'
    context_object_name = 'pdi_plans'
    paginate_by = 20
    required_role = 'MEMBER'
    
    def get_queryset(self):
        queryset = PDIPlan.objects.filter(
            organization=self.get_organization()
        ).select_related('employee', 'manager', 'approved_by')
        
        # Filter by user role
        user = self.request.user
        if not user.is_superuser:
            # Employees see their own plans
            # Managers see their team's plans
            # HR sees all plans
            membership = user.memberships.filter(
                organization=self.get_organization(),
                is_active=True
            ).first()
            
            if membership and membership.role in ['HR', 'ORG_ADMIN']:
                pass  # See all plans
            elif membership and membership.role == 'MANAGER':
                queryset = queryset.filter(
                    Q(employee=user) | Q(manager=user)
                )
            else:
                queryset = queryset.filter(employee=user)
        
        # Apply search filters
        form = PDISearchForm(self.get_organization(), self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            priority = form.cleaned_data.get('priority')
            employee = form.cleaned_data.get('employee')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(employee__first_name__icontains=search) |
                    Q(employee__last_name__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status)
            
            if priority:
                queryset = queryset.filter(priority=priority)
            
            if employee:
                queryset = queryset.filter(employee=employee)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PDISearchForm(self.get_organization(), self.request.GET)
        
        # Add statistics
        organization = self.get_organization()
        context['stats'] = {
            'total_plans': PDIPlan.objects.filter(organization=organization).count(),
            'active_plans': PDIPlan.objects.filter(organization=organization, status__in=['APPROVED', 'IN_PROGRESS']).count(),
            'pending_approval': PDIPlan.objects.filter(organization=organization, status='PENDING_APPROVAL').count(),
            'completed_plans': PDIPlan.objects.filter(organization=organization, status='COMPLETED').count(),
        }
        
        return context


class PDIPlanDetailView(LoginRequiredMixin, CompanyOnlyMixin, DetailView):
    """PDI plan detail view."""
    model = PDIPlan
    template_name = 'pdi/pdi_plan_detail.html'
    context_object_name = 'pdi_plan'
    required_role = 'MEMBER'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply same filtering as list view
        user = self.request.user
        if not user.is_superuser:
            membership = user.memberships.filter(
                organization=self.get_organization(),
                is_active=True
            ).first()
            
            if membership and membership.role in ['HR', 'ORG_ADMIN']:
                pass  # See all plans
            elif membership and membership.role == 'MANAGER':
                queryset = queryset.filter(
                    Q(employee=user) | Q(manager=user)
                )
            else:
                queryset = queryset.filter(employee=user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get tasks grouped by category
        tasks = self.object.tasks.filter(is_active=True).order_by('time_bound_deadline')
        context['tasks'] = tasks
        context['tasks_by_category'] = {}
        
        for task in tasks:
            category = task.get_category_display()
            if category not in context['tasks_by_category']:
                context['tasks_by_category'][category] = []
            context['tasks_by_category'][category].append(task)
        
        # Get recent comments
        context['recent_comments'] = self.object.comments.select_related('author').order_by('-created_at')[:5]
        
        # Check permissions
        user = self.request.user
        context['can_edit'] = (
            user == self.object.employee or
            user == self.object.manager or
            user.has_role_in_organization(self.get_organization(), 'HR') or
            user.is_superuser
        )
        context['can_approve'] = (
            user == self.object.manager or
            user.has_role_in_organization(self.get_organization(), 'HR') or
            user.is_superuser
        )
        
        return context


class PDIPlanCreateView(LoginRequiredMixin, CompanyOnlyMixin, SuccessMessageMixin, CreateView):
    """Create new PDI plan."""
    model = PDIPlan
    form_class = PDIPlanForm
    template_name = 'pdi/pdi_plan_form.html'
    success_message = _('PDI plan created successfully!')
    required_role = 'HR'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('pdi:detail', kwargs={'pk': self.object.pk})


class PDIPlanUpdateView(LoginRequiredMixin, CompanyOnlyMixin, SuccessMessageMixin, UpdateView):
    """Update PDI plan."""
    model = PDIPlan
    form_class = PDIPlanForm
    template_name = 'pdi/pdi_plan_form.html'
    success_message = _('PDI plan updated successfully!')
    required_role = 'MEMBER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('pdi:detail', kwargs={'pk': self.object.pk})


class PDITaskCreateView(LoginRequiredMixin, CompanyOnlyMixin, SuccessMessageMixin, CreateView):
    """Create new PDI task."""
    model = PDITask
    form_class = PDITaskForm
    template_name = 'pdi/pdi_task_form.html'
    success_message = _('PDI task created successfully!')
    required_role = 'MEMBER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        pdi_plan = get_object_or_404(PDIPlan, pk=self.kwargs['plan_pk'])
        form.instance.pdi_plan = pdi_plan
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('pdi:detail', kwargs={'pk': self.kwargs['plan_pk']})


class PDITaskUpdateView(LoginRequiredMixin, CompanyOnlyMixin, SuccessMessageMixin, UpdateView):
    """Update PDI task."""
    model = PDITask
    form_class = PDITaskForm
    template_name = 'pdi/pdi_task_form.html'
    success_message = _('PDI task updated successfully!')
    required_role = 'MEMBER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('pdi:detail', kwargs={'pk': self.object.pdi_plan.pk})


class PDITaskProgressView(LoginRequiredMixin, CompanyOnlyMixin, View):
    """Update PDI task progress via AJAX."""
    required_role = 'MEMBER'
    
    def post(self, request, pk):
        task = get_object_or_404(PDITask, pk=pk)
        
        # Check permissions
        user = request.user
        if not (user == task.pdi_plan.employee or 
                user == task.pdi_plan.manager or
                user.has_role_in_organization(self.get_organization(), 'HR')):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            progress = float(request.POST.get('progress', 0))
            notes = request.POST.get('notes', '')
            
            # Update task progress
            task.update_progress(progress, notes)
            
            # Update the progress update record with the user
            if task.progress_updates.exists():
                latest_update = task.progress_updates.first()
                latest_update.updated_by = user
                latest_update.save()
            
            return JsonResponse({
                'success': True,
                'progress': task.progress_percentage,
                'status': task.get_status_display(),
                'overall_progress': task.pdi_plan.overall_progress
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'error': str(e)}, status=400)


class PDIApprovalView(LoginRequiredMixin, CompanyOnlyMixin, FormView):
    """Approve or reject PDI plan."""
    form_class = PDIApprovalForm
    template_name = 'pdi/pdi_approval.html'
    required_role = 'MANAGER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pdi_plan'] = get_object_or_404(PDIPlan, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        pdi_plan = get_object_or_404(PDIPlan, pk=self.kwargs['pk'])
        action = form.cleaned_data['action']
        notes = form.cleaned_data['notes']
        
        if action == 'approve':
            pdi_plan.approve(self.request.user, notes)
            messages.success(self.request, _('PDI plan approved successfully!'))
        else:
            pdi_plan.status = 'DRAFT'
            pdi_plan.approval_notes = notes
            pdi_plan.save(update_fields=['status', 'approval_notes'])
            messages.info(self.request, _('PDI plan returned for revisions.'))
        
        return redirect('pdi:detail', pk=pdi_plan.pk)


class PDIActionCatalogListView(LoginRequiredMixin, CompanyOnlyMixin, ListView):
    """List PDI action catalog items."""
    model = PDIActionCatalog
    template_name = 'pdi/action_catalog_list.html'
    context_object_name = 'actions'
    paginate_by = 20
    required_role = 'MEMBER'
    
    def get_queryset(self):
        return PDIActionCatalog.objects.filter(
            organization=self.get_organization(),
            is_active=True
        ).order_by('category', 'title')


class PDIActionCatalogCreateView(LoginRequiredMixin, CompanyOnlyMixin, SuccessMessageMixin, CreateView):
    """Create new action catalog item."""
    model = PDIActionCatalog
    form_class = PDIActionCatalogForm
    template_name = 'pdi/action_catalog_form.html'
    success_message = _('Action catalog item created successfully!')
    required_role = 'HR'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('pdi:action_catalog')


class BulkPDIGenerationView(LoginRequiredMixin, CompanyOnlyMixin, SuccessMessageMixin, FormView):
    """Bulk generate PDI plans from assessments."""
    form_class = BulkPDIGenerationForm
    template_name = 'pdi/bulk_generation.html'
    success_message = _('PDI plans generated successfully!')
    required_role = 'HR'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        assessment_instances = form.cleaned_data['assessment_instances']
        template = form.cleaned_data['template']
        auto_approve = form.cleaned_data['auto_approve']
        
        generated_count = 0
        
        with transaction.atomic():
            for instance in assessment_instances:
                try:
                    pdi_plan = template.generate_pdi_for_assessment(instance)
                    if pdi_plan:
                        if auto_approve:
                            pdi_plan.approve(self.request.user, 'Auto-approved during bulk generation')
                        generated_count += 1
                except Exception as e:
                    messages.warning(
                        self.request,
                        _('Failed to generate PDI for {}: {}').format(
                            instance.user.full_name, str(e)
                        )
                    )
        
        messages.success(
            self.request,
            _('Generated {} PDI plans successfully.').format(generated_count)
        )
        
        return redirect('pdi:list')


class PDIDashboardView(LoginRequiredMixin, CompanyOnlyMixin, ListView):
    """PDI dashboard with overview and statistics."""
    model = PDIPlan
    template_name = 'pdi/dashboard.html'
    context_object_name = 'recent_plans'
    required_role = 'MEMBER'
    
    def get_queryset(self):
        # Get recent plans for current user
        user = self.request.user
        return PDIPlan.objects.filter(
            organization=self.get_organization(),
            employee=user
        ).order_by('-created_at')[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        user = self.request.user
        
        # User's PDI statistics
        user_plans = PDIPlan.objects.filter(organization=organization, employee=user)
        context['user_stats'] = {
            'total_plans': user_plans.count(),
            'active_plans': user_plans.filter(status__in=['APPROVED', 'IN_PROGRESS']).count(),
            'completed_plans': user_plans.filter(status='COMPLETED').count(),
            'avg_progress': user_plans.filter(status__in=['APPROVED', 'IN_PROGRESS']).aggregate(
                avg=Avg('overall_progress')
            )['avg'] or 0,
        }
        
        # Upcoming deadlines
        context['upcoming_tasks'] = PDITask.objects.filter(
            pdi_plan__organization=organization,
            pdi_plan__employee=user,
            status__in=['NOT_STARTED', 'IN_PROGRESS'],
            time_bound_deadline__gte=timezone.now().date(),
            time_bound_deadline__lte=timezone.now().date() + timezone.timedelta(days=30)
        ).order_by('time_bound_deadline')[:5]
        
        # Overdue tasks
        context['overdue_tasks'] = PDITask.objects.filter(
            pdi_plan__organization=organization,
            pdi_plan__employee=user,
            status__in=['NOT_STARTED', 'IN_PROGRESS'],
            time_bound_deadline__lt=timezone.now().date()
        ).order_by('time_bound_deadline')[:5]
        
        # Manager view (if user is a manager)
        membership = user.memberships.filter(organization=organization, is_active=True).first()
        if membership and membership.role in ['MANAGER', 'HR', 'ORG_ADMIN']:
            context['pending_approvals'] = PDIPlan.objects.filter(
                organization=organization,
                status='PENDING_APPROVAL',
                manager=user
            ).count()
            
            context['team_plans'] = PDIPlan.objects.filter(
                organization=organization,
                manager=user,
                status__in=['APPROVED', 'IN_PROGRESS']
            ).order_by('-updated_at')[:5]
        
        return context


class PDICommentCreateView(LoginRequiredMixin, CompanyOnlyMixin, View):
    """Add comment to PDI plan via AJAX."""
    required_role = 'MEMBER'
    
    def post(self, request, pk):
        pdi_plan = get_object_or_404(PDIPlan, pk=pk)
        
        # Check permissions
        user = request.user
        if not (user == pdi_plan.employee or 
                user == pdi_plan.manager or
                user.has_role_in_organization(self.get_organization(), 'HR')):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        content = request.POST.get('content', '').strip()
        is_private = request.POST.get('is_private') == 'true'
        
        if not content:
            return JsonResponse({'error': 'Comment content is required'}, status=400)
        
        comment = PDIComment.objects.create(
            pdi_plan=pdi_plan,
            content=content,
            is_private=is_private,
            author=user
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': str(comment.id),
                'content': comment.content,
                'author': comment.author.full_name,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_private': comment.is_private
            }
        })


class PDIReportsView(LoginRequiredMixin, CompanyOnlyMixin, ListView):
    """PDI reports and analytics."""
    model = PDIPlan
    template_name = 'pdi/reports.html'
    context_object_name = 'plans'
    required_role = 'MANAGER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Organization-wide statistics
        all_plans = PDIPlan.objects.filter(organization=organization)
        context['org_stats'] = {
            'total_plans': all_plans.count(),
            'active_plans': all_plans.filter(status__in=['APPROVED', 'IN_PROGRESS']).count(),
            'completed_plans': all_plans.filter(status='COMPLETED').count(),
            'avg_progress': all_plans.filter(status__in=['APPROVED', 'IN_PROGRESS']).aggregate(
                avg=Avg('overall_progress')
            )['avg'] or 0,
            'overdue_plans': all_plans.filter(
                target_completion_date__lt=timezone.now().date(),
                status__in=['APPROVED', 'IN_PROGRESS']
            ).count(),
        }
        
        # Progress by category
        from django.db.models import Case, When, Value, CharField
        context['progress_by_category'] = PDITask.objects.filter(
            pdi_plan__organization=organization,
            is_active=True
        ).values('category').annotate(
            category_name=Case(
                *[When(category=choice[0], then=Value(choice[1])) for choice in PDITask.CATEGORY_CHOICES],
                output_field=CharField()
            ),
            avg_progress=Avg('progress_percentage'),
            task_count=Count('id')
        ).order_by('category')
        
        return context