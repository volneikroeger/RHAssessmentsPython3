"""
URL configuration for pdi app.
"""
from django.urls import path
from . import views

app_name = 'pdi'

urlpatterns = [
    # PDI Dashboard
    path('', views.PDIDashboardView.as_view(), name='dashboard'),
    
    # PDI Plans
    path('plans/', views.PDIPlanListView.as_view(), name='list'),
    path('plans/create/', views.PDIPlanCreateView.as_view(), name='create'),
    path('plans/<uuid:pk>/', views.PDIPlanDetailView.as_view(), name='detail'),
    path('plans/<uuid:pk>/edit/', views.PDIPlanUpdateView.as_view(), name='update'),
    path('plans/<uuid:pk>/approve/', views.PDIApprovalView.as_view(), name='approve'),
    
    # PDI Tasks
    path('plans/<uuid:plan_pk>/tasks/create/', views.PDITaskCreateView.as_view(), name='create_task'),
    path('tasks/<uuid:pk>/edit/', views.PDITaskUpdateView.as_view(), name='update_task'),
    path('tasks/<uuid:pk>/progress/', views.PDITaskProgressView.as_view(), name='update_progress'),
    
    # Comments
    path('plans/<uuid:pk>/comment/', views.PDICommentCreateView.as_view(), name='add_comment'),
    
    # Action Catalog
    path('catalog/', views.PDIActionCatalogListView.as_view(), name='action_catalog'),
    path('catalog/create/', views.PDIActionCatalogCreateView.as_view(), name='create_action'),
    
    # Bulk Operations
    path('generate/', views.BulkPDIGenerationView.as_view(), name='bulk_generate'),
    
    # Reports
    path('reports/', views.PDIReportsView.as_view(), name='reports'),
]