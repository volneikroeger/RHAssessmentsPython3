"""
Celery tasks for billing operations.
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def check_subscription_renewals():
    """
    Check for subscription renewals and handle billing events.
    
    This task runs hourly to:
    - Check for expiring subscriptions
    - Process renewal notifications
    - Handle failed payments
    - Update subscription statuses
    """
    logger.info("Starting subscription renewals check")
    
    try:
        from .models import Subscription, BillingNotification
        
        # Find subscriptions expiring in next 7 days
        upcoming_renewals = Subscription.objects.filter(
            status__in=['ACTIVE', 'TRIALING'],
            current_period_end__lte=timezone.now() + timezone.timedelta(days=7),
            current_period_end__gte=timezone.now()
        )
        
        renewal_count = 0
        notification_count = 0
        
        for subscription in upcoming_renewals:
            try:
                # Check if renewal notification already sent
                existing_notification = BillingNotification.objects.filter(
                    subscription=subscription,
                    notification_type='SUBSCRIPTION_RENEWED',
                    created_at__gte=subscription.current_period_start
                ).exists()
                
                if not existing_notification:
                    # Create renewal notification
                    BillingNotification.objects.create(
                        organization=subscription.organization,
                        subscription=subscription,
                        notification_type='SUBSCRIPTION_RENEWED',
                        recipient_email=subscription.organization.email or 'admin@example.com',
                        subject=f'Subscription Renewal - {subscription.plan.name}',
                        message=f'Your subscription to {subscription.plan.name} will renew on {subscription.current_period_end.strftime("%B %d, %Y")}.',
                        scheduled_for=timezone.now()
                    )
                    notification_count += 1
                
                renewal_count += 1
                
            except Exception as e:
                logger.error(f"Error processing renewal for subscription {subscription.id}: {str(e)}")
        
        logger.info(f"Subscription renewals check completed - "
                   f"Renewals processed: {renewal_count}, "
                   f"Notifications created: {notification_count}")
        
        return {
            "status": "success",
            "renewals_processed": renewal_count,
            "notifications_created": notification_count
        }
        
    except Exception as e:
        logger.error(f"Error in subscription renewals check: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def process_webhook_event(webhook_data, provider):
    """
    Process webhook events from payment providers (PayPal, Stripe).
    
    Args:
        webhook_data (dict): The webhook payload
        provider (str): Payment provider ('paypal' or 'stripe')
    """
    logger.info(f"Processing {provider} webhook event")
    
    try:
        from .models import WebhookEvent, Subscription, Payment, Invoice
        
        event_type = webhook_data.get('event_type') or webhook_data.get('type')
        event_id = webhook_data.get('id')
        
        # Get webhook event record
        webhook_event = WebhookEvent.objects.filter(
            provider=provider,
            provider_event_id=event_id
        ).first()
        
        if not webhook_event:
            logger.error(f"Webhook event not found: {event_id}")
            return {"status": "error", "message": "Webhook event not found"}
        
        webhook_event.status = 'PROCESSING'
        webhook_event.save()
        
        # Process based on event type
        if provider == 'paypal':
            result = _process_paypal_webhook(webhook_data, webhook_event)
        elif provider == 'stripe':
            result = _process_stripe_webhook(webhook_data, webhook_event)
        else:
            result = {"status": "error", "message": "Unknown provider"}
        
        if result["status"] == "success":
            webhook_event.mark_as_processed(result.get("data"))
        else:
            webhook_event.mark_as_failed(result.get("message", "Unknown error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing {provider} webhook: {str(e)}")
        if 'webhook_event' in locals():
            webhook_event.mark_as_failed(str(e))
        return {"status": "error", "message": str(e)}


def _process_paypal_webhook(webhook_data, webhook_event):
    """Process PayPal-specific webhook events."""
    event_type = webhook_data.get('event_type', '')
    
    try:
        if event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            # Subscription activated
            subscription_id = webhook_data.get('resource', {}).get('id')
            # TODO: Update subscription status
            logger.info(f"PayPal subscription activated: {subscription_id}")
            
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            # Subscription cancelled
            subscription_id = webhook_data.get('resource', {}).get('id')
            # TODO: Update subscription status
            logger.info(f"PayPal subscription cancelled: {subscription_id}")
            
        elif event_type == 'PAYMENT.SALE.COMPLETED':
            # Payment completed
            payment_id = webhook_data.get('resource', {}).get('id')
            # TODO: Update payment status
            logger.info(f"PayPal payment completed: {payment_id}")
            
        elif event_type == 'PAYMENT.SALE.DENIED':
            # Payment failed
            payment_id = webhook_data.get('resource', {}).get('id')
            # TODO: Update payment status
            logger.info(f"PayPal payment denied: {payment_id}")
        
        return {"status": "success", "event_type": event_type}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _process_stripe_webhook(webhook_data, webhook_event):
    """Process Stripe-specific webhook events."""
    event_type = webhook_data.get('type', '')
    
    try:
        if event_type == 'customer.subscription.updated':
            # Subscription updated
            subscription_data = webhook_data.get('data', {}).get('object', {})
            subscription_id = subscription_data.get('id')
            # TODO: Update subscription status
            logger.info(f"Stripe subscription updated: {subscription_id}")
            
        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled
            subscription_data = webhook_data.get('data', {}).get('object', {})
            subscription_id = subscription_data.get('id')
            # TODO: Update subscription status
            logger.info(f"Stripe subscription cancelled: {subscription_id}")
            
        elif event_type == 'invoice.payment_succeeded':
            # Payment succeeded
            invoice_data = webhook_data.get('data', {}).get('object', {})
            invoice_id = invoice_data.get('id')
            # TODO: Update payment status
            logger.info(f"Stripe payment succeeded: {invoice_id}")
            
        elif event_type == 'invoice.payment_failed':
            # Payment failed
            invoice_data = webhook_data.get('data', {}).get('object', {})
            invoice_id = invoice_data.get('id')
            # TODO: Update payment status
            logger.info(f"Stripe payment failed: {invoice_id}")
        
        return {"status": "success", "event_type": event_type}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@shared_task
def send_billing_notification(notification_id):
    """
    Send billing-related notifications to users.
    
    Args:
        notification_id (str): BillingNotification UUID
    """
    logger.info(f"Sending billing notification: {notification_id}")
    
    try:
        from .models import BillingNotification
        from django.core.mail import send_mail
        
        notification = BillingNotification.objects.get(id=notification_id)
        
        # Send email
        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient_email],
            fail_silently=False
        )
        
        notification.mark_as_sent()
        
        logger.info(f"Billing notification sent to {notification.recipient_email}: {notification.notification_type}")
        return {"status": "success", "recipient": notification.recipient_email, "type": notification.notification_type}
        
    except BillingNotification.DoesNotExist:
        logger.error(f"Billing notification not found: {notification_id}")
        return {"status": "error", "message": "Notification not found"}
    except Exception as e:
        logger.error(f"Error sending billing notification: {str(e)}")
        if 'notification' in locals():
            notification.mark_as_failed(str(e))
        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_expired_payment_sessions():
    """
    Clean up expired payment sessions and temporary data.
    
    This task runs daily to remove:
    - Expired payment sessions
    - Temporary checkout data
    - Failed payment attempts older than 30 days
    """
    logger.info("Starting cleanup of expired payment sessions")
    
    try:
        from .models import Payment, WebhookEvent
        
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        # Clean up old failed payments
        old_failed_payments = Payment.objects.filter(
            status='FAILED',
            created_at__lt=cutoff_date
        )
        failed_count = old_failed_payments.count()
        old_failed_payments.delete()
        
        # Clean up old processed webhooks
        old_webhooks = WebhookEvent.objects.filter(
            status='PROCESSED',
            created_at__lt=cutoff_date
        )
        webhook_count = old_webhooks.count()
        old_webhooks.delete()
        
        # Clean up old notifications
        from .models import BillingNotification
        old_notifications = BillingNotification.objects.filter(
            status='SENT',
            created_at__lt=cutoff_date
        )
        notification_count = old_notifications.count()
        old_notifications.delete()
        
        logger.info(f"Payment sessions cleanup completed - "
                   f"Failed payments: {failed_count}, "
                   f"Webhooks: {webhook_count}, "
                   f"Notifications: {notification_count}")
        
        return {
            "status": "success",
            "failed_payments_cleaned": failed_count,
            "webhooks_cleaned": webhook_count,
            "notifications_cleaned": notification_count
        }
        
    except Exception as e:
        logger.error(f"Error in payment sessions cleanup: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def generate_monthly_invoices():
    """
    Generate monthly invoices for all active subscriptions.
    
    This task runs monthly to:
    - Create invoices for subscription renewals
    - Include overage charges
    - Send invoice notifications
    """
    logger.info("Starting monthly invoice generation")
    
    try:
        from .models import Subscription, Invoice, InvoiceItem, UsageMeter
        
        # Find subscriptions that need invoicing
        now = timezone.now()
        subscriptions_to_invoice = Subscription.objects.filter(
            status__in=['ACTIVE', 'TRIALING'],
            current_period_end__lte=now + timezone.timedelta(days=1),
            current_period_end__gte=now - timezone.timedelta(days=1)
        )
        
        invoices_created = 0
        
        for subscription in subscriptions_to_invoice:
            try:
                with transaction.atomic():
                    # Create invoice
                    invoice = Invoice.objects.create(
                        organization=subscription.organization,
                        subscription=subscription,
                        status='OPEN',
                        period_start=subscription.current_period_start,
                        period_end=subscription.current_period_end,
                        due_date=now + timezone.timedelta(days=7),
                        currency=subscription.currency,
                        provider=subscription.provider
                    )
                    
                    # Add subscription item
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        item_type='SUBSCRIPTION',
                        description=f'{subscription.plan.name} - {subscription.get_billing_cycle_display()}',
                        quantity=1,
                        unit_price=subscription.amount,
                        total_price=subscription.amount
                    )
                    
                    subtotal = subscription.amount
                    
                    # Add overage items
                    usage_meters = UsageMeter.objects.filter(
                        subscription=subscription,
                        period_start=subscription.current_period_start,
                        period_end=subscription.current_period_end,
                        overage_cost__gt=0
                    )
                    
                    for meter in usage_meters:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            item_type='OVERAGE',
                            description=f'{meter.get_usage_type_display()} Overage ({meter.overage_usage} units)',
                            quantity=meter.overage_usage,
                            unit_price=meter.overage_rate,
                            total_price=meter.overage_cost,
                            usage_meter=meter
                        )
                        subtotal += meter.overage_cost
                    
                    # Calculate tax (simplified - would be more complex in real implementation)
                    tax_rate = Decimal('0.08')  # 8% tax rate
                    tax_amount = subtotal * tax_rate
                    
                    # Add tax item
                    if tax_amount > 0:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            item_type='TAX',
                            description='Tax',
                            quantity=1,
                            unit_price=tax_amount,
                            total_price=tax_amount
                        )
                    
                    # Update invoice totals
                    invoice.subtotal = subtotal
                    invoice.tax_amount = tax_amount
                    invoice.total_amount = subtotal + tax_amount
                    invoice.save()
                    
                    # Create notification
                    BillingNotification.objects.create(
                        organization=subscription.organization,
                        subscription=subscription,
                        invoice=invoice,
                        notification_type='INVOICE_CREATED',
                        recipient_email=subscription.organization.email or 'admin@example.com',
                        subject=f'New Invoice {invoice.invoice_number}',
                        message=f'A new invoice for {invoice.total_amount} {invoice.currency} has been generated.',
                        scheduled_for=timezone.now()
                    )
                    
                    invoices_created += 1
                    logger.info(f"Invoice created for {subscription.organization.name}: {invoice.invoice_number}")
                    
            except Exception as e:
                logger.error(f"Error creating invoice for subscription {subscription.id}: {str(e)}")
        
        logger.info(f"Monthly invoice generation completed - Invoices created: {invoices_created}")
        return {"status": "success", "invoices_created": invoices_created}
        
    except Exception as e:
        logger.error(f"Error in monthly invoice generation: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def send_usage_alerts():
    """
    Send alerts when organizations approach usage limits.
    
    This task runs daily to:
    - Check usage meters approaching limits
    - Send warning notifications
    - Alert about overage charges
    """
    logger.info("Starting usage alerts check")
    
    try:
        from .models import UsageMeter, BillingNotification
        
        # Find usage meters approaching limits (80% and 100%)
        warning_threshold = 80
        critical_threshold = 100
        
        now = timezone.now()
        current_meters = UsageMeter.objects.filter(
            period_start__lte=now,
            period_end__gte=now
        ).select_related('subscription', 'organization')
        
        alerts_sent = 0
        
        for meter in current_meters:
            usage_percentage = meter.usage_percentage
            
            # Check if we should send an alert
            should_alert = False
            alert_type = None
            
            if usage_percentage >= critical_threshold and meter.is_over_limit:
                should_alert = True
                alert_type = 'USAGE_LIMIT_REACHED'
            elif usage_percentage >= warning_threshold:
                should_alert = True
                alert_type = 'USAGE_LIMIT_REACHED'  # Same type, different message
            
            if should_alert:
                # Check if alert already sent for this period
                existing_alert = BillingNotification.objects.filter(
                    organization=meter.organization,
                    notification_type=alert_type,
                    created_at__gte=meter.period_start,
                    message__icontains=meter.get_usage_type_display()
                ).exists()
                
                if not existing_alert:
                    # Create usage alert
                    if usage_percentage >= critical_threshold:
                        message = f'You have reached {usage_percentage:.0f}% of your {meter.get_usage_type_display().lower()} limit ({meter.current_usage}/{meter.limit}).'
                        if meter.overage_allowed:
                            message += f' Overage charges may apply at {meter.overage_rate} per unit.'
                        else:
                            message += ' Further usage may be blocked until your next billing cycle.'
                    else:
                        message = f'You have used {usage_percentage:.0f}% of your {meter.get_usage_type_display().lower()} limit ({meter.current_usage}/{meter.limit}).'
                    
                    BillingNotification.objects.create(
                        organization=meter.organization,
                        subscription=meter.subscription,
                        notification_type=alert_type,
                        recipient_email=meter.organization.email or 'admin@example.com',
                        subject=f'Usage Alert - {meter.get_usage_type_display()}',
                        message=message,
                        scheduled_for=timezone.now()
                    )
                    
                    alerts_sent += 1
        
        logger.info(f"Usage alerts check completed - Alerts sent: {alerts_sent}")
        return {"status": "success", "alerts_sent": alerts_sent}
        
    except Exception as e:
        logger.error(f"Error in usage alerts check: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def process_pending_notifications():
    """
    Process and send pending billing notifications.
    
    This task runs every 15 minutes to:
    - Send scheduled notifications
    - Retry failed notifications
    - Update notification statuses
    """
    logger.info("Processing pending billing notifications")
    
    try:
        from .models import BillingNotification
        from django.core.mail import send_mail
        
        # Get pending notifications
        pending_notifications = BillingNotification.objects.filter(
            status='PENDING',
            scheduled_for__lte=timezone.now()
        ).order_by('scheduled_for')
        
        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                # Send email
                send_mail(
                    subject=notification.subject,
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.recipient_email],
                    fail_silently=False
                )
                
                notification.mark_as_sent()
                sent_count += 1
                
            except Exception as e:
                notification.mark_as_failed(str(e))
                failed_count += 1
                logger.error(f"Failed to send notification {notification.id}: {str(e)}")
        
        logger.info(f"Notification processing completed - Sent: {sent_count}, Failed: {failed_count}")
        return {"status": "success", "sent": sent_count, "failed": failed_count}
        
    except Exception as e:
        logger.error(f"Error processing notifications: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def update_subscription_statuses():
    """
    Update subscription statuses based on current state.
    
    This task runs daily to:
    - Mark expired trials
    - Update past due subscriptions
    - Handle automatic cancellations
    """
    logger.info("Updating subscription statuses")
    
    try:
        from .models import Subscription
        
        now = timezone.now()
        updated_count = 0
        
        # Mark expired trials
        expired_trials = Subscription.objects.filter(
            status='TRIALING',
            trial_end__lt=now
        )
        
        for subscription in expired_trials:
            subscription.status = 'PAST_DUE'
            subscription.save()
            updated_count += 1
        
        # Mark past due subscriptions
        past_due_subscriptions = Subscription.objects.filter(
            status='ACTIVE',
            current_period_end__lt=now - timezone.timedelta(days=7)  # 7 days grace period
        )
        
        for subscription in past_due_subscriptions:
            subscription.status = 'PAST_DUE'
            subscription.save()
            updated_count += 1
        
        # Handle automatic cancellations
        auto_cancel_subscriptions = Subscription.objects.filter(
            cancel_at_period_end=True,
            current_period_end__lt=now,
            status__in=['ACTIVE', 'TRIALING']
        )
        
        for subscription in auto_cancel_subscriptions:
            subscription.status = 'CANCELLED'
            subscription.cancelled_at = now
            subscription.save()
            updated_count += 1
        
        logger.info(f"Subscription status update completed - Updated: {updated_count}")
        return {"status": "success", "updated_count": updated_count}
        
    except Exception as e:
        logger.error(f"Error updating subscription statuses: {str(e)}")
        return {"status": "error", "message": str(e)}