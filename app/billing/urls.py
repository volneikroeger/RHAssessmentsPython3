"""
URL configuration for billing app.
"""
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Dashboard and main views
    path('', views.BillingDashboardView.as_view(), name='dashboard'),
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('payment-method/', views.PaymentMethodView.as_view(), name='payment_method'),
    
    # Subscription management
    path('subscription/update/', views.SubscriptionUpdateView.as_view(), name='subscription_update'),
    path('subscription/cancel/', views.CancelSubscriptionView.as_view(), name='cancel_subscription'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<uuid:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<uuid:invoice_pk>/retry/', views.PaymentRetryView.as_view(), name='payment_retry'),
    
    # Usage and reports
    path('usage/', views.UsageReportView.as_view(), name='usage_report'),
    path('analytics/data/', views.BillingAnalyticsView.as_view(), name='analytics_data'),
    
    # Billing address
    path('address/', views.BillingAddressView.as_view(), name='billing_address'),
    
    # Coupons (super admin)
    path('coupons/', views.CouponListView.as_view(), name='coupon_list'),
    path('coupons/create/', views.CouponCreateView.as_view(), name='coupon_create'),
    
    # AJAX endpoints
    path('api/validate-coupon/', views.ValidateCouponView.as_view(), name='validate_coupon'),
    path('api/usage/', views.UsageAPIView.as_view(), name='usage_api'),
    path('api/stats/', views.BillingStatsView.as_view(), name='billing_stats'),
]