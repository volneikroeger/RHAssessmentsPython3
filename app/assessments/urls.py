"""
URL configuration for assessments app.
"""
from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Assessment definitions
    path('', views.AssessmentDefinitionListView.as_view(), name='list'),
    path('create/', views.AssessmentDefinitionCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.AssessmentDefinitionDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.AssessmentDefinitionUpdateView.as_view(), name='update'),
    path('<uuid:pk>/invite/', views.AssessmentInviteView.as_view(), name='invite'),
    
    # Assessment taking
    path('take/<str:token>/', views.AssessmentTakeView.as_view(), name='take'),
    path('result/<str:token>/', views.AssessmentResultView.as_view(), name='result'),
    
    # Assessment instances management
    path('instances/', views.AssessmentInstanceListView.as_view(), name='instances'),
]