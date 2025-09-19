"""
URL configuration for audit app.
"""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('my-data/', views.my_data, name='my_data'),
]