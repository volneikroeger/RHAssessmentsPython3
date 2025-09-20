"""
URL configuration for recruiting app.
"""
from django.urls import path
from . import views

app_name = 'recruiting'

urlpatterns = [
    # Dashboard
    path('', views.RecruitingDashboardView.as_view(), name='dashboard'),
    
    # Clients
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<uuid:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<uuid:pk>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    
    # Jobs
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/create/', views.JobCreateView.as_view(), name='job_create'),
    path('jobs/<uuid:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<uuid:pk>/edit/', views.JobUpdateView.as_view(), name='job_update'),
    path('jobs/<uuid:job_pk>/matching/', views.CandidateMatchingView.as_view(), name='candidate_matching'),
    
    # Candidates
    path('candidates/', views.CandidateListView.as_view(), name='candidate_list'),
    path('candidates/create/', views.CandidateCreateView.as_view(), name='candidate_create'),
    path('candidates/<uuid:pk>/', views.CandidateDetailView.as_view(), name='candidate_detail'),
    path('candidates/<uuid:pk>/edit/', views.CandidateUpdateView.as_view(), name='candidate_update'),
    path('candidates/<uuid:pk>/note/', views.CandidateNoteCreateView.as_view(), name='candidate_note'),
    path('candidates/import/', views.BulkCandidateImportView.as_view(), name='candidate_import'),
    
    # Job Applications
    path('applications/create/', views.JobApplicationCreateView.as_view(), name='application_create'),
    path('applications/<uuid:pk>/', views.JobApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<uuid:pk>/status/', views.UpdateApplicationStatusView.as_view(), name='update_application_status'),
    
    # Interviews
    path('applications/<uuid:application_pk>/interviews/create/', views.InterviewCreateView.as_view(), name='interview_create'),
    path('interviews/<uuid:pk>/edit/', views.InterviewUpdateView.as_view(), name='interview_update'),
    
    # Placements
    path('placements/', views.PlacementListView.as_view(), name='placement_list'),
    path('applications/<uuid:application_pk>/placement/', views.PlacementCreateView.as_view(), name='placement_create'),
    
    # Reports and Analytics
    path('reports/', views.RecruitingReportsView.as_view(), name='reports'),
    path('analytics/data/', views.RecruitingAnalyticsView.as_view(), name='analytics_data'),
]