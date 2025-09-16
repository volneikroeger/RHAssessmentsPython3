"""
URL configuration for organizations app.
"""
from django.urls import path, include
from . import views

app_name = 'organizations'

urlpatterns = [
    # Organization management
    path('', views.OrganizationListView.as_view(), name='list'),
    path('create/', views.OrganizationCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.OrganizationDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.OrganizationUpdateView.as_view(), name='update'),
    
    # Membership management
    path('<uuid:pk>/members/', views.MembershipListView.as_view(), name='members'),
    path('<uuid:pk>/invite/', views.InviteUserView.as_view(), name='invite'),
    path('invites/accept/<str:token>/', views.AcceptInviteView.as_view(), name='accept_invite'),
    
    # Department management
    path('<uuid:pk>/departments/', views.DepartmentListView.as_view(), name='departments'),
    path('<uuid:pk>/departments/create/', views.DepartmentCreateView.as_view(), name='create_department'),
    path('departments/<uuid:dept_id>/edit/', views.DepartmentUpdateView.as_view(), name='update_department'),
    
    # Position management
    path('departments/<uuid:dept_id>/positions/', views.PositionListView.as_view(), name='positions'),
    path('departments/<uuid:dept_id>/positions/create/', views.PositionCreateView.as_view(), name='create_position'),
    path('positions/<uuid:pos_id>/edit/', views.PositionUpdateView.as_view(), name='update_position'),
    
    # Employee management
    path('<uuid:pk>/employees/', views.EmployeeListView.as_view(), name='employees'),
    path('<uuid:pk>/employees/create/', views.EmployeeCreateView.as_view(), name='create_employee'),
    path('employees/<uuid:emp_id>/edit/', views.EmployeeUpdateView.as_view(), name='update_employee'),
    path('employees/import/', views.EmployeeImportView.as_view(), name='import_employees'),
    
    # Settings
    path('<uuid:pk>/settings/', views.OrganizationSettingsView.as_view(), name='settings'),
]