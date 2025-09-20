"""
URL configuration for emails app.
"""
from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    # Dashboard
    path('', views.EmailDashboardView.as_view(), name='dashboard'),
    
    # Templates
    path('templates/', views.EmailTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.EmailTemplateCreateView.as_view(), name='template_create'),
    path('templates/<uuid:pk>/', views.EmailTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<uuid:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='template_update'),
    
    # Messages
    path('messages/', views.EmailMessageListView.as_view(), name='message_list'),
    path('messages/<uuid:pk>/', views.EmailMessageDetailView.as_view(), name='message_detail'),
    
    # Campaigns
    path('campaigns/', views.EmailCampaignListView.as_view(), name='campaign_list'),
    path('campaigns/create/', views.EmailCampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<uuid:pk>/', views.EmailCampaignDetailView.as_view(), name='campaign_detail'),
    
    # Bulk operations
    path('bulk/', views.BulkEmailView.as_view(), name='bulk_email'),
    path('test/', views.EmailTestView.as_view(), name='test'),
    path('preview/', views.EmailPreviewView.as_view(), name='preview'),
    
    # Analytics
    path('analytics/', views.EmailAnalyticsView.as_view(), name='analytics'),
    
    # User preferences
    path('subscriptions/', views.EmailSubscriptionView.as_view(), name='subscriptions'),
    
    # Public pages
    path('unsubscribe/<str:token>/', views.UnsubscribeView.as_view(), name='unsubscribe'),
    
    # Tracking
    path('track/<uuid:message_id>/<str:event_type>/', views.EmailTrackingView.as_view(), name='tracking'),
    
    # Management
    path('queue/', views.EmailQueueView.as_view(), name='queue'),
    path('blacklist/', views.EmailBlacklistView.as_view(), name='blacklist'),
    
    # API endpoints
    path('api/template-preview/', views.EmailTemplatePreviewAPIView.as_view(), name='template_preview_api'),
    path('api/analytics/', views.EmailAnalyticsAPIView.as_view(), name='analytics_api'),
]