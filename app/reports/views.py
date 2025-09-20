"""
Views for reports app.
"""
import json
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum, F
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView, TemplateView
)
from django.views import View

from organizations.mixins import OrganizationPermissionMixin
from .models import (
    Report, ReportTemplate, ReportSchedule, Dashboard, ReportSubscription,
    ReportExport, AnalyticsSnapshot, ReportMetric, ReportChart
)
from .forms import (
    ReportGenerationForm, ReportTemplateForm, ReportScheduleForm, DashboardForm,
    ReportFilterForm, ReportShareForm, QuickReportForm, ReportExportForm,
    AnalyticsFilterForm, BenchmarkComparisonForm
)


class ReportsDashboardView(LoginRequiredMixin, OrganizationPermissionMixin, TemplateView):
    """Main reports dashboard with overview and quick actions."""
    template_name = 'reports/dashboard.html'
    required_role = 'MEMBER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        user = self.request.user
        
        # Recent reports
        context['recent_reports'] = Report.objects.filter(
            organization=organization,
            status='COMPLETED'
        ).order_by('-generation_completed_at')[:5]
        
        # User's bookmarked reports
        context['bookmarked_reports'] = Report.objects.filter(
            organization=organization,
            bookmarks__user=user
        ).order_by('-created_at')[:5]
        
        # Quick stats
        context['stats'] = {
            'total_reports': Report.objects.filter(organization=organization).count(),
            'reports_this_month': Report.objects.filter(
                organization=organization,
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year
            ).count(),
            'scheduled_reports': ReportSchedule.objects.filter(
                organization=organization,
                is_active=True
            ).count(),
            'shared_reports': Report.objects.filter(
                organization=organization,
                shared_with=user
            ).count(),
        }
        
        # Available templates
        context['available_templates'] = ReportTemplate.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('name')[:6]
        
        # Organization type specific data
        if organization.is_company:
            context['show_pdi_reports'] = True
            context['show_recruiting_reports'] = False
        elif organization.is_recruiter:
            context['show_pdi_reports'] = False
            context['show_recruiting_reports'] = True
        else:
            context['show_pdi_reports'] = True
            context['show_recruiting_reports'] = True
        
        return context


class ReportListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List all reports with filtering."""
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    required_role = 'MEMBER'
    
    def get_queryset(self):
        queryset = Report.objects.filter(
            organization=self.get_organization()
        ).select_related('generated_by')
        
        # Apply access control
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(generated_by=user) |
                Q(is_public=True) |
                Q(shared_with=user)
            ).distinct()
        
        # Apply filters
        form = ReportFilterForm(self.get_organization(), self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            report_type = form.cleaned_data.get('report_type')
            status = form.cleaned_data.get('status')
            format = form.cleaned_data.get('format')
            generated_by = form.cleaned_data.get('generated_by')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
            
            if report_type:
                queryset = queryset.filter(report_type=report_type)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if format:
                queryset = queryset.filter(format=format)
            
            if generated_by:
                queryset = queryset.filter(generated_by=generated_by)
            
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ReportFilterForm(self.get_organization(), self.request.GET)
        return context


class ReportDetailView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Report detail view with content and charts."""
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    required_role = 'MEMBER'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply access control
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(generated_by=user) |
                Q(is_public=True) |
                Q(shared_with=user)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get metrics and charts
        context['metrics'] = self.object.metrics.order_by('name')
        context['charts'] = self.object.charts.order_by('order')
        
        # Check if user can edit/share
        user = self.request.user
        context['can_edit'] = (
            user == self.object.generated_by or
            user.is_superuser or
            user.has_role_in_organization(self.get_organization(), 'ORG_ADMIN')
        )
        
        # Check if user has bookmarked this report
        context['is_bookmarked'] = self.object.bookmarks.filter(user=user).exists()
        
        # Get comments
        context['comments'] = self.object.comments.select_related('author').order_by('-created_at')[:10]
        
        return context


class ReportGenerateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Generate new custom report."""
    model = Report
    form_class = ReportGenerationForm
    template_name = 'reports/report_generate.html'
    success_message = _('Report generation started! You will be notified when it\'s ready.')
    required_role = 'MANAGER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.generated_by = self.request.user
        
        # Set expiration (30 days from now)
        form.instance.expires_at = timezone.now() + timedelta(days=30)
        
        # Build filters from form data
        filters = {}
        if form.cleaned_data.get('include_assessments'):
            filters['include_assessments'] = True
        if form.cleaned_data.get('include_pdi'):
            filters['include_pdi'] = True
        if form.cleaned_data.get('include_recruiting'):
            filters['include_recruiting'] = True
        
        departments = form.cleaned_data.get('departments')
        if departments:
            filters['departments'] = [str(dept.id) for dept in departments]
        
        users = form.cleaned_data.get('users')
        if users:
            filters['users'] = [str(user.id) for user in users]
        
        form.instance.filters = filters
        
        response = super().form_valid(form)
        
        # Trigger report generation
        from .tasks import generate_report_task
        generate_report_task.delay(self.object.id)
        
        return response
    
    def get_success_url(self):
        return reverse_lazy('reports:detail', kwargs={'pk': self.object.pk})


class QuickReportView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Generate quick reports with predefined templates."""
    form_class = QuickReportForm
    template_name = 'reports/quick_report.html'
    required_role = 'MEMBER'
    
    def form_valid(self, form):
        organization = self.get_organization()
        report_type = form.cleaned_data['report_type']
        period = form.cleaned_data['period']
        format = form.cleaned_data['format']
        
        # Calculate date range
        today = timezone.now().date()
        if period == 'custom':
            date_from = form.cleaned_data['custom_date_from']
            date_to = form.cleaned_data['custom_date_to']
        else:
            days = int(period)
            date_from = today - timedelta(days=days)
            date_to = today
        
        # Create report
        report = Report.objects.create(
            organization=organization,
            title=f"{dict(form.QUICK_REPORT_TYPES)[report_type]} - {today}",
            description=f"Quick report for {date_from} to {date_to}",
            report_type='CUSTOM',
            format=format,
            date_from=date_from,
            date_to=date_to,
            filters={'quick_report_type': report_type},
            generated_by=self.request.user,
            expires_at=timezone.now() + timedelta(days=7)  # Quick reports expire in 7 days
        )
        
        # Generate report
        from .tasks import generate_quick_report_task
        generate_quick_report_task.delay(report.id, report_type)
        
        messages.success(
            self.request,
            _('Quick report generation started! You will be redirected when ready.')
        )
        
        return redirect('reports:detail', pk=report.pk)


class AnalyticsView(LoginRequiredMixin, OrganizationPermissionMixin, TemplateView):
    """Interactive analytics dashboard."""
    template_name = 'reports/analytics.html'
    required_role = 'MANAGER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Get latest analytics snapshot
        latest_snapshot = AnalyticsSnapshot.objects.filter(
            organization=organization
        ).order_by('-snapshot_date').first()
        
        context['latest_snapshot'] = latest_snapshot
        context['filter_form'] = AnalyticsFilterForm()
        
        # Key performance indicators
        if latest_snapshot:
            context['kpis'] = {
                'assessment_completion_rate': latest_snapshot.assessment_completion_rate,
                'avg_pdi_progress': latest_snapshot.avg_pdi_progress,
                'active_users': latest_snapshot.active_users,
                'user_retention_rate': latest_snapshot.user_retention_rate,
            }
        
        return context


class ReportShareView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Share report with other users."""
    form_class = ReportShareForm
    template_name = 'reports/report_share.html'
    required_role = 'MEMBER'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = get_object_or_404(Report, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        report = get_object_or_404(Report, pk=self.kwargs['pk'])
        users = form.cleaned_data['users']
        make_public = form.cleaned_data['make_public']
        expires_in_days = form.cleaned_data.get('expires_in_days')
        
        # Update report sharing
        if make_public:
            report.is_public = True
        
        if expires_in_days:
            report.expires_at = timezone.now() + timedelta(days=expires_in_days)
        
        report.save()
        
        # Add shared users
        for user in users:
            report.shared_with.add(user)
        
        messages.success(
            self.request,
            _('Report shared with {} users.').format(users.count())
        )
        
        return redirect('reports:detail', pk=report.pk)


class ReportExportView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Export report in different formats."""
    form_class = ReportExportForm
    template_name = 'reports/report_export.html'
    required_role = 'MEMBER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = get_object_or_404(Report, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        report = get_object_or_404(Report, pk=self.kwargs['pk'])
        format = form.cleaned_data['format']
        include_charts = form.cleaned_data['include_charts']
        include_raw_data = form.cleaned_data['include_raw_data']
        compress_file = form.cleaned_data['compress_file']
        
        # Create export job
        export = ReportExport.objects.create(
            report=report,
            format=format,
            requested_by=self.request.user,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Trigger export generation
        from .tasks import export_report_task
        export_report_task.delay(
            export.id,
            include_charts=include_charts,
            include_raw_data=include_raw_data,
            compress_file=compress_file
        )
        
        messages.success(
            self.request,
            _('Export started! You will receive a notification when ready.')
        )
        
        return redirect('reports:detail', pk=report.pk)


class BenchmarkComparisonView(LoginRequiredMixin, OrganizationPermissionMixin, FormView):
    """Generate benchmark comparison reports."""
    form_class = BenchmarkComparisonForm
    template_name = 'reports/benchmark_comparison.html'
    required_role = 'MANAGER'
    
    def form_valid(self, form):
        organization = self.get_organization()
        comparison_type = form.cleaned_data['comparison_type']
        metrics_to_compare = form.cleaned_data['metrics_to_compare']
        
        # Create benchmark report
        report = Report.objects.create(
            organization=organization,
            title=f"Benchmark Comparison - {comparison_type.title()}",
            description=f"Comparison with {comparison_type} benchmarks",
            report_type='CUSTOM',
            format='HTML',
            filters={
                'comparison_type': comparison_type,
                'industry': form.cleaned_data.get('industry'),
                'company_size': form.cleaned_data.get('company_size'),
                'metrics': metrics_to_compare,
            },
            generated_by=self.request.user,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Generate benchmark report
        from .tasks import generate_benchmark_report_task
        generate_benchmark_report_task.delay(report.id)
        
        messages.success(
            self.request,
            _('Benchmark comparison report generation started!')
        )
        
        return redirect('reports:detail', pk=report.pk)


# AJAX and API Views
class ReportDataAPIView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """API for fetching report data for charts."""
    required_role = 'MEMBER'
    
    def get(self, request, pk):
        report = get_object_or_404(Report, pk=pk, organization=self.get_organization())
        
        # Check access
        user = request.user
        if not (user == report.generated_by or report.is_public or 
                user in report.shared_with.all() or user.is_superuser):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Return chart data
        charts_data = []
        for chart in report.charts.order_by('order'):
            charts_data.append({
                'id': str(chart.id),
                'title': chart.title,
                'type': chart.chart_type,
                'data': chart.chart_data,
                'options': chart.chart_options,
                'width': chart.width,
                'height': chart.height,
            })
        
        return JsonResponse({
            'report_id': str(report.id),
            'title': report.title,
            'charts': charts_data,
            'metrics': [
                {
                    'name': metric.name,
                    'value': metric.formatted_value,
                    'type': metric.metric_type,
                    'change': metric.change_percentage,
                }
                for metric in report.metrics.all()
            ]
        })


class AnalyticsDataAPIView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """API for real-time analytics data."""
    required_role = 'MEMBER'
    
    def get(self, request):
        organization = self.get_organization()
        
        # Get filter parameters
        metric_type = request.GET.get('metric_type', '')
        time_range = request.GET.get('time_range', '30d')
        granularity = request.GET.get('granularity', 'daily')
        
        # Calculate date range
        today = timezone.now().date()
        if time_range == '7d':
            date_from = today - timedelta(days=7)
        elif time_range == '30d':
            date_from = today - timedelta(days=30)
        elif time_range == '90d':
            date_from = today - timedelta(days=90)
        elif time_range == '6m':
            date_from = today - timedelta(days=180)
        elif time_range == '1y':
            date_from = today - timedelta(days=365)
        else:
            date_from = today - timedelta(days=30)
        
        # Get analytics data
        analytics_data = self._get_analytics_data(
            organization, metric_type, date_from, today, granularity
        )
        
        return JsonResponse(analytics_data)
    
    def _get_analytics_data(self, organization, metric_type, date_from, date_to, granularity):
        """Get analytics data for specified parameters."""
        data = {}
        
        if not metric_type or metric_type == 'assessments':
            data['assessments'] = self._get_assessment_metrics(organization, date_from, date_to)
        
        if not metric_type or metric_type == 'pdi':
            data['pdi'] = self._get_pdi_metrics(organization, date_from, date_to)
        
        if not metric_type or metric_type == 'recruiting':
            data['recruiting'] = self._get_recruiting_metrics(organization, date_from, date_to)
        
        if not metric_type or metric_type == 'users':
            data['users'] = self._get_user_metrics(organization, date_from, date_to)
        
        return data
    
    def _get_assessment_metrics(self, organization, date_from, date_to):
        """Get assessment-related metrics."""
        from assessments.models import AssessmentInstance
        
        instances = AssessmentInstance.objects.filter(
            organization=organization,
            invited_at__date__gte=date_from,
            invited_at__date__lte=date_to
        )
        
        total_sent = instances.count()
        completed = instances.filter(status='COMPLETED').count()
        completion_rate = (completed / total_sent * 100) if total_sent > 0 else 0
        
        return {
            'total_sent': total_sent,
            'completed': completed,
            'completion_rate': completion_rate,
            'in_progress': instances.filter(status='IN_PROGRESS').count(),
            'expired': instances.filter(status='EXPIRED').count(),
        }
    
    def _get_pdi_metrics(self, organization, date_from, date_to):
        """Get PDI-related metrics."""
        from pdi.models import PDIPlan, PDITask
        
        plans = PDIPlan.objects.filter(
            organization=organization,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        tasks = PDITask.objects.filter(
            pdi_plan__organization=organization,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        return {
            'plans_created': plans.count(),
            'plans_completed': plans.filter(status='COMPLETED').count(),
            'tasks_created': tasks.count(),
            'tasks_completed': tasks.filter(status='COMPLETED').count(),
            'avg_progress': plans.aggregate(avg=Avg('overall_progress'))['avg'] or 0,
        }
    
    def _get_recruiting_metrics(self, organization, date_from, date_to):
        """Get recruiting-related metrics."""
        if not organization.is_recruiter:
            return {}
        
        from recruiting.models import Candidate, Job, JobApplication, Placement
        
        candidates = Candidate.objects.filter(
            organization=organization,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        applications = JobApplication.objects.filter(
            organization=organization,
            applied_date__date__gte=date_from,
            applied_date__date__lte=date_to
        )
        
        placements = Placement.objects.filter(
            organization=organization,
            start_date__gte=date_from,
            start_date__lte=date_to
        )
        
        return {
            'candidates_added': candidates.count(),
            'applications_received': applications.count(),
            'placements_made': placements.count(),
            'active_jobs': Job.objects.filter(
                organization=organization,
                status__in=['OPEN', 'IN_PROGRESS']
            ).count(),
        }
    
    def _get_user_metrics(self, organization, date_from, date_to):
        """Get user engagement metrics."""
        from organizations.models import Membership
        
        memberships = Membership.objects.filter(
            organization=organization,
            is_active=True
        )
        
        new_members = memberships.filter(
            accepted_at__date__gte=date_from,
            accepted_at__date__lte=date_to
        )
        
        return {
            'total_members': memberships.count(),
            'new_members': new_members.count(),
            'active_members': memberships.filter(
                user__last_login__date__gte=date_from
            ).count(),
        }


class ReportBookmarkToggleView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """Toggle report bookmark via AJAX."""
    required_role = 'MEMBER'
    
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk, organization=self.get_organization())
        user = request.user
        
        # Check access
        if not (user == report.generated_by or report.is_public or 
                user in report.shared_with.all() or user.is_superuser):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Toggle bookmark
        from .models import ReportBookmark
        bookmark, created = ReportBookmark.objects.get_or_create(
            user=user,
            report=report
        )
        
        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True
        
        return JsonResponse({
            'bookmarked': bookmarked,
            'message': _('Report bookmarked') if bookmarked else _('Bookmark removed')
        })


class ReportTemplateListView(LoginRequiredMixin, OrganizationPermissionMixin, ListView):
    """List report templates."""
    model = ReportTemplate
    template_name = 'reports/template_list.html'
    context_object_name = 'templates'
    required_role = 'MANAGER'
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(
            organization=self.get_organization()
        ).order_by('name')


class ReportTemplateCreateView(LoginRequiredMixin, OrganizationPermissionMixin, SuccessMessageMixin, CreateView):
    """Create report template."""
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_message = _('Report template created successfully!')
    required_role = 'ORG_ADMIN'
    
    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('reports:template_list')


class DashboardView(LoginRequiredMixin, OrganizationPermissionMixin, DetailView):
    """Custom dashboard view."""
    model = Dashboard
    template_name = 'reports/dashboard_view.html'
    context_object_name = 'dashboard'
    required_role = 'MEMBER'
    
    def get_object(self):
        """Get dashboard by ID or default dashboard."""
        dashboard_id = self.kwargs.get('pk')
        organization = self.get_organization()
        
        if dashboard_id:
            return get_object_or_404(Dashboard, pk=dashboard_id, organization=organization)
        else:
            # Get default dashboard
            return Dashboard.objects.filter(
                organization=organization,
                is_default=True,
                is_active=True
            ).first()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.object:
            # Get real-time data for dashboard widgets
            context['dashboard_data'] = self._get_dashboard_data()
        
        return context
    
    def _get_dashboard_data(self):
        """Get real-time data for dashboard widgets."""
        organization = self.get_organization()
        
        # This would be expanded based on dashboard configuration
        return {
            'assessments_this_month': 0,  # Would calculate from actual data
            'pdi_completion_rate': 0,     # Would calculate from actual data
            'active_users': 0,            # Would calculate from actual data
            'recent_activity': [],        # Would get recent activities
        }


class ReportDownloadView(LoginRequiredMixin, OrganizationPermissionMixin, View):
    """Download report file."""
    required_role = 'MEMBER'
    
    def get(self, request, pk):
        report = get_object_or_404(Report, pk=pk, organization=self.get_organization())
        
        # Check access
        user = request.user
        if not (user == report.generated_by or report.is_public or 
                user in report.shared_with.all() or user.is_superuser):
            raise Http404
        
        # Check if report is expired
        if report.is_expired:
            messages.error(request, _('This report has expired and is no longer available.'))
            return redirect('reports:list')
        
        # For now, return a placeholder response
        # In production, this would serve the actual file
        response = HttpResponse(
            f"Report: {report.title}\nGenerated: {report.generation_completed_at}\nFormat: {report.format}",
            content_type='text/plain'
        )
        response['Content-Disposition'] = f'attachment; filename="{report.title}.txt"'
        
        return response


class OrganizationAnalyticsView(LoginRequiredMixin, OrganizationPermissionMixin, TemplateView):
    """Organization-wide analytics and insights."""
    template_name = 'reports/organization_analytics.html'
    required_role = 'MANAGER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        # Get comprehensive organization metrics
        context['org_metrics'] = self._calculate_organization_metrics(organization)
        context['trend_data'] = self._get_trend_data(organization)
        context['department_breakdown'] = self._get_department_breakdown(organization)
        
        return context
    
    def _calculate_organization_metrics(self, organization):
        """Calculate comprehensive organization metrics."""
        from assessments.models import AssessmentInstance
        from pdi.models import PDIPlan
        from organizations.models import Membership
        
        # Assessment metrics
        total_assessments = AssessmentInstance.objects.filter(organization=organization).count()
        completed_assessments = AssessmentInstance.objects.filter(
            organization=organization,
            status='COMPLETED'
        ).count()
        
        # PDI metrics
        total_pdi_plans = PDIPlan.objects.filter(organization=organization).count()
        active_pdi_plans = PDIPlan.objects.filter(
            organization=organization,
            status__in=['APPROVED', 'IN_PROGRESS']
        ).count()
        
        # User metrics
        total_members = Membership.objects.filter(
            organization=organization,
            is_active=True
        ).count()
        
        return {
            'total_assessments': total_assessments,
            'completed_assessments': completed_assessments,
            'assessment_completion_rate': (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0,
            'total_pdi_plans': total_pdi_plans,
            'active_pdi_plans': active_pdi_plans,
            'total_members': total_members,
        }
    
    def _get_trend_data(self, organization):
        """Get trend data for the last 12 months."""
        trends = []
        
        for i in range(12):
            month_date = timezone.now().replace(day=1) - timedelta(days=30*i)
            
            # Get snapshot for this month
            snapshot = AnalyticsSnapshot.objects.filter(
                organization=organization,
                snapshot_type='MONTHLY',
                snapshot_date__year=month_date.year,
                snapshot_date__month=month_date.month
            ).first()
            
            if snapshot:
                trends.append({
                    'month': month_date.strftime('%b %Y'),
                    'assessments': snapshot.assessments_completed,
                    'pdi_plans': snapshot.pdi_plans_created,
                    'active_users': snapshot.active_users,
                })
            else:
                trends.append({
                    'month': month_date.strftime('%b %Y'),
                    'assessments': 0,
                    'pdi_plans': 0,
                    'active_users': 0,
                })
        
        return list(reversed(trends))
    
    def _get_department_breakdown(self, organization):
        """Get metrics broken down by department."""
        if not organization.is_company:
            return []
        
        from organizations.models import Department
        from assessments.models import AssessmentInstance
        from pdi.models import PDIPlan
        
        departments = Department.objects.filter(
            organization=organization,
            is_active=True
        )
        
        breakdown = []
        for dept in departments:
            # Get employees in this department
            employees = dept.employees.filter(is_active=True)
            employee_users = [emp.user for emp in employees]
            
            # Calculate metrics
            dept_assessments = AssessmentInstance.objects.filter(
                organization=organization,
                user__in=employee_users,
                status='COMPLETED'
            ).count()
            
            dept_pdi_plans = PDIPlan.objects.filter(
                organization=organization,
                employee__in=employee_users
            ).count()
            
            breakdown.append({
                'name': dept.name,
                'employees': employees.count(),
                'assessments': dept_assessments,
                'pdi_plans': dept_pdi_plans,
            })
        
        return breakdown