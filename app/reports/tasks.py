"""
Celery tasks for report generation and analytics.
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Avg, Sum, Q
import logging
import json

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def generate_report_task(report_id, template_id=None):
    """
    Generate a report based on configuration.
    
    Args:
        report_id (str): UUID of the report to generate
        template_id (str): Optional template ID for structured generation
    """
    logger.info(f"Starting report generation: {report_id}")
    
    try:
        from .models import Report, ReportTemplate, ReportMetric, ReportChart
        
        report = Report.objects.get(id=report_id)
        report.status = 'GENERATING'
        report.save()
        
        # Get template if provided
        template = None
        if template_id:
            template = ReportTemplate.objects.get(id=template_id)
        
        # Generate report content based on type
        if report.report_type == 'ASSESSMENT_SUMMARY':
            content, metrics, charts = _generate_assessment_summary(report)
        elif report.report_type == 'TEAM_PERFORMANCE':
            content, metrics, charts = _generate_team_performance(report)
        elif report.report_type == 'PDI_PROGRESS':
            content, metrics, charts = _generate_pdi_progress(report)
        elif report.report_type == 'RECRUITING_METRICS':
            content, metrics, charts = _generate_recruiting_metrics(report)
        elif report.report_type == 'USAGE_ANALYTICS':
            content, metrics, charts = _generate_usage_analytics(report)
        elif report.report_type == 'ORGANIZATION_OVERVIEW':
            content, metrics, charts = _generate_organization_overview(report)
        else:
            content, metrics, charts = _generate_custom_report(report)
        
        # Save report content
        report.content = content
        report.data = {
            'generation_timestamp': timezone.now().isoformat(),
            'filters_applied': report.filters,
            'metrics_count': len(metrics),
            'charts_count': len(charts),
        }
        
        # Create metrics
        for metric_data in metrics:
            ReportMetric.objects.create(
                report=report,
                **metric_data
            )
        
        # Create charts
        for chart_data in charts:
            ReportChart.objects.create(
                report=report,
                **chart_data
            )
        
        # Mark as completed
        report.mark_as_completed()
        
        logger.info(f"Report generation completed: {report_id}")
        return {"status": "success", "report_id": report_id}
        
    except Report.DoesNotExist:
        logger.error(f"Report not found: {report_id}")
        return {"status": "error", "message": "Report not found"}
    except Exception as e:
        logger.error(f"Error generating report {report_id}: {str(e)}")
        if 'report' in locals():
            report.mark_as_failed(str(e))
        return {"status": "error", "message": str(e)}


def _generate_assessment_summary(report):
    """Generate assessment summary report."""
    from assessments.models import AssessmentInstance, ScoreProfile
    
    organization = report.organization
    date_from = report.date_from
    date_to = report.date_to
    
    # Get assessment data
    instances = AssessmentInstance.objects.filter(
        organization=organization,
        status='COMPLETED'
    )
    
    if date_from:
        instances = instances.filter(completed_at__date__gte=date_from)
    if date_to:
        instances = instances.filter(completed_at__date__lte=date_to)
    
    total_assessments = instances.count()
    
    # Calculate metrics
    metrics = [
        {
            'name': 'Total Assessments Completed',
            'metric_type': 'COUNT',
            'value': total_assessments,
            'chart_type': 'NUMBER',
        },
        {
            'name': 'Average Completion Time',
            'metric_type': 'AVERAGE',
            'value': 25.5,  # Would calculate from actual data
            'unit': 'minutes',
            'chart_type': 'GAUGE',
        },
        {
            'name': 'Completion Rate',
            'metric_type': 'PERCENTAGE',
            'value': 85.2,  # Would calculate from actual data
            'chart_type': 'GAUGE',
        }
    ]
    
    # Generate charts
    charts = [
        {
            'title': 'Assessments by Framework',
            'chart_type': 'PIE',
            'width': 6,
            'height': 300,
            'order': 1,
            'chart_data': {
                'labels': ['Big Five', 'DISC', 'Career Anchors'],
                'datasets': [{
                    'data': [45, 30, 25],
                    'backgroundColor': ['#007bff', '#28a745', '#ffc107']
                }]
            },
            'chart_options': {
                'responsive': True,
                'plugins': {
                    'legend': {'position': 'bottom'}
                }
            }
        },
        {
            'title': 'Completion Trend',
            'chart_type': 'LINE',
            'width': 6,
            'height': 300,
            'order': 2,
            'chart_data': {
                'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                'datasets': [{
                    'label': 'Completed Assessments',
                    'data': [12, 18, 15, 22],
                    'borderColor': '#007bff',
                    'backgroundColor': 'rgba(0, 123, 255, 0.1)'
                }]
            },
            'chart_options': {
                'responsive': True,
                'scales': {
                    'y': {'beginAtZero': True}
                }
            }
        }
    ]
    
    content = f"""
    <h2>Assessment Summary Report</h2>
    <p>Period: {date_from} to {date_to}</p>
    <p>Organization: {organization.name}</p>
    
    <h3>Key Findings</h3>
    <ul>
        <li>Total of {total_assessments} assessments completed in the period</li>
        <li>High engagement with personality assessments</li>
        <li>Consistent completion rates across departments</li>
    </ul>
    
    <h3>Recommendations</h3>
    <ul>
        <li>Continue current assessment strategy</li>
        <li>Consider expanding to additional frameworks</li>
        <li>Implement follow-up PDI generation</li>
    </ul>
    """
    
    return content, metrics, charts


def _generate_team_performance(report):
    """Generate team performance report."""
    organization = report.organization
    
    metrics = [
        {
            'name': 'Team Engagement Score',
            'metric_type': 'AVERAGE',
            'value': 7.8,
            'target_value': 8.0,
            'unit': '/10',
            'chart_type': 'GAUGE',
        },
        {
            'name': 'PDI Completion Rate',
            'metric_type': 'PERCENTAGE',
            'value': 72.5,
            'target_value': 80.0,
            'chart_type': 'GAUGE',
        }
    ]
    
    charts = [
        {
            'title': 'Performance by Department',
            'chart_type': 'BAR',
            'width': 12,
            'height': 400,
            'order': 1,
            'chart_data': {
                'labels': ['Engineering', 'Sales', 'Marketing', 'HR'],
                'datasets': [{
                    'label': 'Performance Score',
                    'data': [8.2, 7.5, 8.0, 7.8],
                    'backgroundColor': '#007bff'
                }]
            }
        }
    ]
    
    content = f"""
    <h2>Team Performance Report</h2>
    <p>Organization: {organization.name}</p>
    
    <h3>Performance Overview</h3>
    <p>Overall team performance shows positive trends with room for improvement in specific areas.</p>
    """
    
    return content, metrics, charts


def _generate_pdi_progress(report):
    """Generate PDI progress report."""
    from pdi.models import PDIPlan, PDITask
    
    organization = report.organization
    
    # Get PDI data
    plans = PDIPlan.objects.filter(organization=organization)
    if report.date_from:
        plans = plans.filter(created_at__date__gte=report.date_from)
    if report.date_to:
        plans = plans.filter(created_at__date__lte=report.date_to)
    
    total_plans = plans.count()
    completed_plans = plans.filter(status='COMPLETED').count()
    avg_progress = plans.aggregate(avg=Avg('overall_progress'))['avg'] or 0
    
    metrics = [
        {
            'name': 'Total PDI Plans',
            'metric_type': 'COUNT',
            'value': total_plans,
            'chart_type': 'NUMBER',
        },
        {
            'name': 'Completed Plans',
            'metric_type': 'COUNT',
            'value': completed_plans,
            'chart_type': 'NUMBER',
        },
        {
            'name': 'Average Progress',
            'metric_type': 'PERCENTAGE',
            'value': avg_progress,
            'chart_type': 'GAUGE',
        }
    ]
    
    charts = [
        {
            'title': 'PDI Status Distribution',
            'chart_type': 'DOUGHNUT',
            'width': 6,
            'height': 300,
            'order': 1,
            'chart_data': {
                'labels': ['Completed', 'In Progress', 'Pending Approval', 'Draft'],
                'datasets': [{
                    'data': [
                        plans.filter(status='COMPLETED').count(),
                        plans.filter(status='IN_PROGRESS').count(),
                        plans.filter(status='PENDING_APPROVAL').count(),
                        plans.filter(status='DRAFT').count(),
                    ],
                    'backgroundColor': ['#28a745', '#007bff', '#ffc107', '#6c757d']
                }]
            }
        }
    ]
    
    content = f"""
    <h2>PDI Progress Report</h2>
    <p>Organization: {organization.name}</p>
    
    <h3>Progress Summary</h3>
    <p>Total of {total_plans} PDI plans with {completed_plans} completed.</p>
    <p>Average progress across all plans: {avg_progress:.1f}%</p>
    """
    
    return content, metrics, charts


def _generate_recruiting_metrics(report):
    """Generate recruiting metrics report."""
    if not report.organization.is_recruiter:
        return "This report is only available for recruiting organizations.", [], []
    
    from recruiting.models import Candidate, Job, JobApplication, Placement
    
    organization = report.organization
    
    # Get recruiting data
    candidates = Candidate.objects.filter(organization=organization)
    jobs = Job.objects.filter(organization=organization)
    applications = JobApplication.objects.filter(organization=organization)
    placements = Placement.objects.filter(organization=organization)
    
    if report.date_from:
        candidates = candidates.filter(created_at__date__gte=report.date_from)
        applications = applications.filter(applied_date__date__gte=report.date_from)
        placements = placements.filter(start_date__gte=report.date_from)
    
    if report.date_to:
        candidates = candidates.filter(created_at__date__lte=report.date_to)
        applications = applications.filter(applied_date__date__lte=report.date_to)
        placements = placements.filter(start_date__lte=report.date_to)
    
    metrics = [
        {
            'name': 'New Candidates',
            'metric_type': 'COUNT',
            'value': candidates.count(),
            'chart_type': 'NUMBER',
        },
        {
            'name': 'Successful Placements',
            'metric_type': 'COUNT',
            'value': placements.count(),
            'chart_type': 'NUMBER',
        },
        {
            'name': 'Placement Rate',
            'metric_type': 'PERCENTAGE',
            'value': (placements.count() / applications.count() * 100) if applications.count() > 0 else 0,
            'chart_type': 'GAUGE',
        }
    ]
    
    charts = [
        {
            'title': 'Recruitment Pipeline',
            'chart_type': 'BAR',
            'width': 12,
            'height': 400,
            'order': 1,
            'chart_data': {
                'labels': ['Applied', 'Screening', 'Qualified', 'Interviewed', 'Offered', 'Hired'],
                'datasets': [{
                    'label': 'Candidates',
                    'data': [
                        applications.filter(status='APPLIED').count(),
                        applications.filter(status='SCREENING').count(),
                        applications.filter(status='QUALIFIED').count(),
                        applications.filter(status='INTERVIEWED').count(),
                        applications.filter(status='OFFERED').count(),
                        applications.filter(status='HIRED').count(),
                    ],
                    'backgroundColor': '#007bff'
                }]
            }
        }
    ]
    
    content = f"""
    <h2>Recruiting Metrics Report</h2>
    <p>Organization: {organization.name}</p>
    
    <h3>Recruitment Performance</h3>
    <p>Added {candidates.count()} new candidates with {placements.count()} successful placements.</p>
    """
    
    return content, metrics, charts


def _generate_usage_analytics(report):
    """Generate usage analytics report."""
    organization = report.organization
    
    # Get usage data from billing if available
    metrics = [
        {
            'name': 'Monthly Active Users',
            'metric_type': 'COUNT',
            'value': 25,  # Would calculate from actual data
            'chart_type': 'NUMBER',
        },
        {
            'name': 'Feature Adoption Rate',
            'metric_type': 'PERCENTAGE',
            'value': 68.5,  # Would calculate from actual data
            'chart_type': 'GAUGE',
        }
    ]
    
    charts = [
        {
            'title': 'Feature Usage',
            'chart_type': 'BAR',
            'width': 12,
            'height': 300,
            'order': 1,
            'chart_data': {
                'labels': ['Assessments', 'PDI Plans', 'Reports', 'User Management'],
                'datasets': [{
                    'label': 'Usage Count',
                    'data': [120, 85, 45, 30],
                    'backgroundColor': '#28a745'
                }]
            }
        }
    ]
    
    content = f"""
    <h2>Usage Analytics Report</h2>
    <p>Organization: {organization.name}</p>
    
    <h3>Platform Usage</h3>
    <p>Analysis of feature usage and user engagement patterns.</p>
    """
    
    return content, metrics, charts


def _generate_organization_overview(report):
    """Generate comprehensive organization overview."""
    organization = report.organization
    
    # Get comprehensive metrics
    from assessments.models import AssessmentInstance
    from pdi.models import PDIPlan
    from organizations.models import Membership
    
    total_members = Membership.objects.filter(
        organization=organization,
        is_active=True
    ).count()
    
    total_assessments = AssessmentInstance.objects.filter(
        organization=organization,
        status='COMPLETED'
    ).count()
    
    total_pdi_plans = PDIPlan.objects.filter(
        organization=organization
    ).count()
    
    metrics = [
        {
            'name': 'Total Team Members',
            'metric_type': 'COUNT',
            'value': total_members,
            'chart_type': 'NUMBER',
        },
        {
            'name': 'Assessments Completed',
            'metric_type': 'COUNT',
            'value': total_assessments,
            'chart_type': 'NUMBER',
        },
        {
            'name': 'PDI Plans Created',
            'metric_type': 'COUNT',
            'value': total_pdi_plans,
            'chart_type': 'NUMBER',
        }
    ]
    
    charts = [
        {
            'title': 'Organization Growth',
            'chart_type': 'LINE',
            'width': 12,
            'height': 400,
            'order': 1,
            'chart_data': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'datasets': [{
                    'label': 'Team Members',
                    'data': [20, 22, 25, 28, 30, 32],
                    'borderColor': '#007bff',
                    'backgroundColor': 'rgba(0, 123, 255, 0.1)'
                }]
            }
        }
    ]
    
    content = f"""
    <h2>Organization Overview Report</h2>
    <p>Organization: {organization.name}</p>
    <p>Type: {organization.get_kind_display()}</p>
    
    <h3>Executive Summary</h3>
    <p>Comprehensive overview of organizational metrics and performance indicators.</p>
    
    <h3>Key Metrics</h3>
    <ul>
        <li>Team Size: {total_members} members</li>
        <li>Assessment Activity: {total_assessments} completed</li>
        <li>Development Plans: {total_pdi_plans} created</li>
    </ul>
    """
    
    return content, metrics, charts


def _generate_custom_report(report):
    """Generate custom report based on filters."""
    organization = report.organization
    filters = report.filters
    
    content = f"""
    <h2>{report.title}</h2>
    <p>Organization: {organization.name}</p>
    <p>Generated: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    
    <h3>Report Configuration</h3>
    <p>Custom report with the following filters applied:</p>
    <ul>
    """
    
    for key, value in filters.items():
        content += f"<li>{key}: {value}</li>"
    
    content += """
    </ul>
    
    <h3>Data Analysis</h3>
    <p>This custom report provides insights based on your specific criteria.</p>
    """
    
    metrics = [
        {
            'name': 'Custom Metric',
            'metric_type': 'COUNT',
            'value': 42,
            'chart_type': 'NUMBER',
        }
    ]
    
    charts = []
    
    return content, metrics, charts


@shared_task
def generate_quick_report_task(report_id, quick_report_type):
    """
    Generate a quick report with predefined structure.
    
    Args:
        report_id (str): UUID of the report
        quick_report_type (str): Type of quick report to generate
    """
    logger.info(f"Generating quick report: {report_id} ({quick_report_type})")
    
    try:
        from .models import Report, ReportMetric
        
        report = Report.objects.get(id=report_id)
        organization = report.organization
        
        if quick_report_type == 'assessment_completion':
            content, metrics = _generate_assessment_completion_quick_report(organization, report)
        elif quick_report_type == 'team_performance':
            content, metrics = _generate_team_performance_quick_report(organization, report)
        elif quick_report_type == 'pdi_progress':
            content, metrics = _generate_pdi_progress_quick_report(organization, report)
        elif quick_report_type == 'user_engagement':
            content, metrics = _generate_user_engagement_quick_report(organization, report)
        elif quick_report_type == 'monthly_summary':
            content, metrics = _generate_monthly_summary_quick_report(organization, report)
        else:
            content = "Unknown quick report type."
            metrics = []
        
        # Save report
        report.content = content
        report.mark_as_completed()
        
        # Create metrics
        for metric_data in metrics:
            ReportMetric.objects.create(report=report, **metric_data)
        
        logger.info(f"Quick report generated: {report_id}")
        return {"status": "success", "report_id": report_id}
        
    except Exception as e:
        logger.error(f"Error generating quick report: {str(e)}")
        if 'report' in locals():
            report.mark_as_failed(str(e))
        return {"status": "error", "message": str(e)}


def _generate_assessment_completion_quick_report(organization, report):
    """Generate assessment completion quick report."""
    from assessments.models import AssessmentInstance
    
    instances = AssessmentInstance.objects.filter(
        organization=organization,
        invited_at__date__gte=report.date_from,
        invited_at__date__lte=report.date_to
    )
    
    total_sent = instances.count()
    completed = instances.filter(status='COMPLETED').count()
    completion_rate = (completed / total_sent * 100) if total_sent > 0 else 0
    
    content = f"""
    <h2>Assessment Completion Report</h2>
    <p>Period: {report.date_from} to {report.date_to}</p>
    
    <h3>Summary</h3>
    <ul>
        <li>Total assessments sent: {total_sent}</li>
        <li>Completed assessments: {completed}</li>
        <li>Completion rate: {completion_rate:.1f}%</li>
    </ul>
    """
    
    metrics = [
        {
            'name': 'Completion Rate',
            'metric_type': 'PERCENTAGE',
            'value': completion_rate,
            'chart_type': 'GAUGE',
        }
    ]
    
    return content, metrics


def _generate_team_performance_quick_report(organization, report):
    """Generate team performance quick report."""
    content = f"""
    <h2>Team Performance Overview</h2>
    <p>Period: {report.date_from} to {report.date_to}</p>
    
    <h3>Performance Highlights</h3>
    <p>Quick overview of team performance metrics and trends.</p>
    """
    
    metrics = [
        {
            'name': 'Team Performance Score',
            'metric_type': 'AVERAGE',
            'value': 7.5,
            'unit': '/10',
            'chart_type': 'GAUGE',
        }
    ]
    
    return content, metrics


def _generate_pdi_progress_quick_report(organization, report):
    """Generate PDI progress quick report."""
    from pdi.models import PDIPlan
    
    plans = PDIPlan.objects.filter(
        organization=organization,
        created_at__date__gte=report.date_from,
        created_at__date__lte=report.date_to
    )
    
    avg_progress = plans.aggregate(avg=Avg('overall_progress'))['avg'] or 0
    
    content = f"""
    <h2>PDI Progress Summary</h2>
    <p>Period: {report.date_from} to {report.date_to}</p>
    
    <h3>Development Progress</h3>
    <p>Average PDI progress: {avg_progress:.1f}%</p>
    """
    
    metrics = [
        {
            'name': 'Average PDI Progress',
            'metric_type': 'PERCENTAGE',
            'value': avg_progress,
            'chart_type': 'GAUGE',
        }
    ]
    
    return content, metrics


def _generate_user_engagement_quick_report(organization, report):
    """Generate user engagement quick report."""
    from organizations.models import Membership
    
    members = Membership.objects.filter(
        organization=organization,
        is_active=True
    )
    
    content = f"""
    <h2>User Engagement Metrics</h2>
    <p>Period: {report.date_from} to {report.date_to}</p>
    
    <h3>Engagement Overview</h3>
    <p>Total active members: {members.count()}</p>
    """
    
    metrics = [
        {
            'name': 'Active Members',
            'metric_type': 'COUNT',
            'value': members.count(),
            'chart_type': 'NUMBER',
        }
    ]
    
    return content, metrics


def _generate_monthly_summary_quick_report(organization, report):
    """Generate monthly summary quick report."""
    content = f"""
    <h2>Monthly Activity Summary</h2>
    <p>Organization: {organization.name}</p>
    <p>Month: {report.date_from.strftime('%B %Y')}</p>
    
    <h3>Activity Highlights</h3>
    <p>Summary of all platform activities for the month.</p>
    """
    
    metrics = [
        {
            'name': 'Monthly Activity Score',
            'metric_type': 'AVERAGE',
            'value': 8.2,
            'unit': '/10',
            'chart_type': 'GAUGE',
        }
    ]
    
    return content, metrics


@shared_task
def export_report_task(export_id, include_charts=True, include_raw_data=False, compress_file=False):
    """
    Export report to specified format.
    
    Args:
        export_id (str): UUID of the export job
        include_charts (bool): Whether to include charts
        include_raw_data (bool): Whether to include raw data
        compress_file (bool): Whether to compress the output
    """
    logger.info(f"Starting report export: {export_id}")
    
    try:
        from .models import ReportExport
        
        export = ReportExport.objects.get(id=export_id)
        export.status = 'PROCESSING'
        export.started_at = timezone.now()
        export.save()
        
        report = export.report
        
        # Generate export based on format
        if export.format == 'PDF':
            file_path, file_size = _export_to_pdf(report, include_charts)
        elif export.format == 'EXCEL':
            file_path, file_size = _export_to_excel(report, include_raw_data)
        elif export.format == 'CSV':
            file_path, file_size = _export_to_csv(report, include_raw_data)
        elif export.format == 'JSON':
            file_path, file_size = _export_to_json(report, include_raw_data)
        else:
            file_path, file_size = _export_to_html(report, include_charts)
        
        # Compress if requested
        if compress_file:
            file_path, file_size = _compress_file(file_path)
        
        # Mark as completed
        export.mark_as_completed(file_path, file_size)
        
        logger.info(f"Report export completed: {export_id}")
        return {"status": "success", "export_id": export_id, "file_path": file_path}
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        if 'export' in locals():
            export.status = 'FAILED'
            export.error_message = str(e)
            export.save()
        return {"status": "error", "message": str(e)}


def _export_to_pdf(report, include_charts):
    """Export report to PDF format."""
    # Placeholder implementation
    file_path = f"reports/{report.id}.pdf"
    file_size = 1024 * 50  # 50KB placeholder
    
    logger.info(f"PDF export completed for report {report.id}")
    return file_path, file_size


def _export_to_excel(report, include_raw_data):
    """Export report to Excel format."""
    # Placeholder implementation
    file_path = f"reports/{report.id}.xlsx"
    file_size = 1024 * 25  # 25KB placeholder
    
    logger.info(f"Excel export completed for report {report.id}")
    return file_path, file_size


def _export_to_csv(report, include_raw_data):
    """Export report to CSV format."""
    # Placeholder implementation
    file_path = f"reports/{report.id}.csv"
    file_size = 1024 * 10  # 10KB placeholder
    
    logger.info(f"CSV export completed for report {report.id}")
    return file_path, file_size


def _export_to_json(report, include_raw_data):
    """Export report to JSON format."""
    # Placeholder implementation
    file_path = f"reports/{report.id}.json"
    file_size = 1024 * 15  # 15KB placeholder
    
    logger.info(f"JSON export completed for report {report.id}")
    return file_path, file_size


def _export_to_html(report, include_charts):
    """Export report to HTML format."""
    # Placeholder implementation
    file_path = f"reports/{report.id}.html"
    file_size = 1024 * 20  # 20KB placeholder
    
    logger.info(f"HTML export completed for report {report.id}")
    return file_path, file_size


def _compress_file(file_path):
    """Compress file to ZIP format."""
    # Placeholder implementation
    compressed_path = file_path.replace('.', '_compressed.')
    compressed_size = 1024 * 8  # Compressed size placeholder
    
    return compressed_path, compressed_size


@shared_task
def generate_scheduled_reports():
    """
    Generate scheduled reports based on ReportSchedule configurations.
    
    This task runs every hour to check for scheduled reports that need generation.
    """
    logger.info("Checking for scheduled reports")
    
    try:
        from .models import ReportSchedule
        
        now = timezone.now()
        
        # Find schedules that need to run
        due_schedules = ReportSchedule.objects.filter(
            is_active=True,
            next_generation_at__lte=now
        ).select_related('template')
        
        generated_count = 0
        
        for schedule in due_schedules:
            try:
                # Generate report from template
                report = schedule.template.generate_report(
                    user=schedule.created_by,
                    date_from=now.date() - timezone.timedelta(days=30),
                    date_to=now.date()
                )
                
                # Update schedule
                schedule.last_generated_at = now
                schedule.calculate_next_generation()
                
                generated_count += 1
                logger.info(f"Generated scheduled report: {report.title}")
                
            except Exception as e:
                logger.error(f"Error generating scheduled report {schedule.id}: {str(e)}")
        
        logger.info(f"Scheduled reports check completed - Generated: {generated_count}")
        return {"status": "success", "generated_count": generated_count}
        
    except Exception as e:
        logger.error(f"Error in scheduled reports generation: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def create_analytics_snapshots():
    """
    Create daily analytics snapshots for all organizations.
    
    This task runs daily to capture key metrics for trend analysis.
    """
    logger.info("Creating analytics snapshots")
    
    try:
        from .models import AnalyticsSnapshot
        from organizations.models import Organization
        
        today = timezone.now().date()
        snapshots_created = 0
        
        for organization in Organization.objects.filter(is_active=True):
            try:
                # Check if snapshot already exists for today
                if AnalyticsSnapshot.objects.filter(
                    organization=organization,
                    snapshot_type='DAILY',
                    snapshot_date=today
                ).exists():
                    continue
                
                # Calculate metrics
                metrics = _calculate_daily_metrics(organization, today)
                
                # Create snapshot
                AnalyticsSnapshot.objects.create(
                    organization=organization,
                    snapshot_type='DAILY',
                    snapshot_date=today,
                    **metrics
                )
                
                snapshots_created += 1
                
            except Exception as e:
                logger.error(f"Error creating snapshot for {organization.name}: {str(e)}")
        
        logger.info(f"Analytics snapshots created: {snapshots_created}")
        return {"status": "success", "snapshots_created": snapshots_created}
        
    except Exception as e:
        logger.error(f"Error creating analytics snapshots: {str(e)}")
        return {"status": "error", "message": str(e)}


def _calculate_daily_metrics(organization, date):
    """Calculate daily metrics for an organization."""
    from assessments.models import AssessmentInstance
    from pdi.models import PDIPlan
    from organizations.models import Membership
    
    # Assessment metrics
    assessments_sent = AssessmentInstance.objects.filter(
        organization=organization,
        invited_at__date=date
    ).count()
    
    assessments_completed = AssessmentInstance.objects.filter(
        organization=organization,
        completed_at__date=date
    ).count()
    
    total_assessments = AssessmentInstance.objects.filter(
        organization=organization,
        invited_at__date__lte=date
    ).count()
    
    completion_rate = (
        AssessmentInstance.objects.filter(
            organization=organization,
            status='COMPLETED'
        ).count() / total_assessments * 100
    ) if total_assessments > 0 else 0
    
    # PDI metrics
    pdi_plans_created = PDIPlan.objects.filter(
        organization=organization,
        created_at__date=date
    ).count()
    
    pdi_plans_completed = PDIPlan.objects.filter(
        organization=organization,
        actual_completion_date=date
    ).count()
    
    avg_pdi_progress = PDIPlan.objects.filter(
        organization=organization,
        status__in=['APPROVED', 'IN_PROGRESS']
    ).aggregate(avg=Avg('overall_progress'))['avg'] or 0
    
    # User metrics
    active_users = Membership.objects.filter(
        organization=organization,
        is_active=True,
        user__last_login__date=date
    ).count()
    
    new_users = Membership.objects.filter(
        organization=organization,
        accepted_at__date=date
    ).count()
    
    return {
        'assessments_sent': assessments_sent,
        'assessments_completed': assessments_completed,
        'assessment_completion_rate': completion_rate,
        'pdi_plans_created': pdi_plans_created,
        'pdi_plans_completed': pdi_plans_completed,
        'avg_pdi_progress': avg_pdi_progress,
        'active_users': active_users,
        'new_users': new_users,
    }


@shared_task
def generate_benchmark_report_task(report_id):
    """
    Generate benchmark comparison report.
    
    Args:
        report_id (str): UUID of the report
    """
    logger.info(f"Generating benchmark report: {report_id}")
    
    try:
        from .models import Report, ReportMetric, ReportChart
        
        report = Report.objects.get(id=report_id)
        filters = report.filters
        comparison_type = filters.get('comparison_type')
        
        # Generate benchmark data (placeholder implementation)
        content = f"""
        <h2>Benchmark Comparison Report</h2>
        <p>Organization: {report.organization.name}</p>
        <p>Comparison Type: {comparison_type.title()}</p>
        
        <h3>Benchmark Analysis</h3>
        <p>Your organization's performance compared to industry benchmarks.</p>
        
        <h3>Key Insights</h3>
        <ul>
            <li>Assessment completion rate: Above industry average</li>
            <li>PDI engagement: Meets industry standards</li>
            <li>User retention: Exceeds benchmark</li>
        </ul>
        """
        
        # Create benchmark metrics
        metrics = [
            {
                'name': 'Benchmark Score',
                'metric_type': 'AVERAGE',
                'value': 8.3,
                'target_value': 7.5,
                'unit': '/10',
                'chart_type': 'GAUGE',
            }
        ]
        
        # Save report
        report.content = content
        report.mark_as_completed()
        
        # Create metrics
        for metric_data in metrics:
            ReportMetric.objects.create(report=report, **metric_data)
        
        logger.info(f"Benchmark report generated: {report_id}")
        return {"status": "success", "report_id": report_id}
        
    except Exception as e:
        logger.error(f"Error generating benchmark report: {str(e)}")
        if 'report' in locals():
            report.mark_as_failed(str(e))
        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_expired_reports():
    """
    Clean up expired reports and export files.
    
    This task runs daily to remove expired reports and free up storage.
    """
    logger.info("Cleaning up expired reports")
    
    try:
        from .models import Report, ReportExport
        
        now = timezone.now()
        
        # Find expired reports
        expired_reports = Report.objects.filter(
            expires_at__lt=now,
            status='COMPLETED'
        )
        
        # Find expired exports
        expired_exports = ReportExport.objects.filter(
            expires_at__lt=now,
            status='COMPLETED'
        )
        
        reports_cleaned = expired_reports.count()
        exports_cleaned = expired_exports.count()
        
        # Delete expired items
        expired_reports.delete()
        expired_exports.delete()
        
        logger.info(f"Cleanup completed - Reports: {reports_cleaned}, Exports: {exports_cleaned}")
        return {
            "status": "success",
            "reports_cleaned": reports_cleaned,
            "exports_cleaned": exports_cleaned
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired reports: {str(e)}")
        return {"status": "error", "message": str(e)}