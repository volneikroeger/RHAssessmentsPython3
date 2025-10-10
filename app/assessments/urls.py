"""
URL configuration for assessments app.
"""
from django.urls import path
from . import views
from . import disc_api

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

    # Admin views
    path('admin/templates/', views.TemplateLibraryView.as_view(), name='template_library'),
    path('admin/questions/', views.QuestionBankView.as_view(), name='question_bank'),

    # Question management
    path('<uuid:assessment_pk>/questions/', views.QuestionListView.as_view(), name='question_list'),
    path('<uuid:assessment_pk>/questions/create/', views.QuestionCreateView.as_view(), name='question_create'),
    path('<uuid:assessment_pk>/questions/<uuid:pk>/edit/', views.QuestionUpdateView.as_view(), name='question_update'),
    path('<uuid:assessment_pk>/questions/<uuid:pk>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),
    path('<uuid:assessment_pk>/questions/<uuid:question_pk>/options/', views.QuestionOptionManageView.as_view(), name='question_options'),
    path('<uuid:assessment_pk>/questions/<uuid:question_pk>/options/<uuid:pk>/delete/', views.QuestionOptionDeleteView.as_view(), name='question_option_delete'),

    # DISC Assessment Bank API
    path('api/disc/bank/', disc_api.DISCBankView.as_view(), name='disc_bank_api'),
    path('api/disc/templates/', disc_api.DISCTemplatesView.as_view(), name='disc_templates_api'),
]