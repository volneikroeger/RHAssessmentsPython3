"""
URL configuration for reports app.
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Main dashboard
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    
    # Reports
    path('list/', views.ReportListView.as_view(), name='list'),
    path('generate/', views.ReportGenerateView.as_view(), name='generate'),
    path('quick/', views.QuickReportView.as_view(), name='quick'),
    path('<uuid:pk>/', views.ReportDetailView.as_view(), name='detail'),
    path('<uuid:pk>/share/', views.ReportShareView.as_view(), name='share'),
    path('<uuid:pk>/export/', views.ReportExportView.as_view(), name='export'),
    path('<uuid:pk>/download/', views.ReportDownloadView.as_view(), name='download'),
    
    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('analytics/organization/', views.OrganizationAnalyticsView.as_view(), name='organization_analytics'),
    path('benchmark/', views.BenchmarkComparisonView.as_view(), name='benchmark'),
    
    # Templates
    path('templates/', views.ReportTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ReportTemplateCreateView.as_view(), name='template_create'),
    
    # Dashboards
    path('dashboard/<uuid:pk>/', views.DashboardView.as_view(), name='dashboard_view'),
    
    # API endpoints
    path('api/data/<uuid:pk>/', views.ReportDataAPIView.as_view(), name='report_data'),
    path('api/analytics/', views.AnalyticsDataAPIView.as_view(), name='analytics_data'),
    path('api/bookmark/<uuid:pk>/', views.ReportBookmarkToggleView.as_view(), name='bookmark_toggle'),
]