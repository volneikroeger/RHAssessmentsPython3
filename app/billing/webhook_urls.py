"""
Webhook URL configuration for billing app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('paypal/', views.PayPalWebhookView.as_view(), name='paypal_webhook'),
    path('stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
]