"""
Celery tasks for email operations.
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_email_message(message_id):
    """
    Send individual email message.
    
    Args:
        message_id (str): UUID of the EmailMessage to send
    """
    logger.info(f"Sending email message: {message_id}")
    
    try:
        from .models import EmailMessage, EmailLog, EmailBlacklist
        
        email_message = EmailMessage.objects.get(id=message_id)
        
        # Check if email is blacklisted
        if EmailBlacklist.is_blacklisted(email_message.to_email):
            email_message.mark_as_failed("Email is blacklisted")
            return {"status": "error", "message": "Email is blacklisted"}
        
        # Check if already sent
        if email_message.status in ['SENT', 'DELIVERED', 'OPENED', 'CLICKED']:
            return {"status": "already_sent", "message_id": message_id}
        
        # Update status
        email_message.status = 'SENDING'
        email_message.save()
        
        # Create email
        email = EmailMultiAlternatives(
            subject=email_message.subject,
            body=email_message.text_content or '',
            from_email=f"{email_message.from_name} <{email_message.from_email}>" if email_message.from_name else email_message.from_email,
            to=[email_message.to_email],
            reply_to=[email_message.reply_to] if email_message.reply_to else None
        )
        
        # Add HTML content
        if email_message.html_content:
            email.attach_alternative(email_message.html_content, "text/html")
        
        # Add CC and BCC
        if email_message.cc_emails:
            email.cc = email_message.cc_emails
        if email_message.bcc_emails:
            email.bcc = email_message.bcc_emails
        
        # Send email
        email.send()
        
        # Mark as sent
        email_message.mark_as_sent()
        
        # Create log entry
        EmailLog.objects.create(
            email_message=email_message,
            event_type='SENT',
            event_data={
                'sent_at': timezone.now().isoformat(),
                'provider': 'django_email',
            }
        )
        
        logger.info(f"Email sent successfully: {message_id} to {email_message.to_email}")
        return {"status": "success", "message_id": message_id}
        
    except EmailMessage.DoesNotExist:
        logger.error(f"Email message not found: {message_id}")
        return {"status": "error", "message": "Email message not found"}
    except Exception as e:
        logger.error(f"Error sending email {message_id}: {str(e)}")
        if 'email_message' in locals():
            email_message.mark_as_failed(str(e))
        return {"status": "error", "message": str(e)}


@shared_task
def send_email_campaign(campaign_id):
    """
    Send email campaign in batches.
    
    Args:
        campaign_id (str): UUID of the EmailCampaign to send
    """
    logger.info(f"Starting email campaign: {campaign_id}")
    
    try:
        from .models import EmailCampaign, EmailMessage
        
        campaign = EmailCampaign.objects.get(id=campaign_id)
        
        # Check if campaign can be sent
        if campaign.status not in ['SCHEDULED', 'SENDING']:
            return {"status": "error", "message": "Campaign cannot be sent"}
        
        # Update status
        campaign.status = 'SENDING'
        campaign.save()
        
        # Create individual email messages
        created_count = 0
        
        for email in campaign.recipient_list:
            try:
                # Check if email already exists for this campaign
                existing = EmailMessage.objects.filter(
                    to_email=email,
                    template=campaign.template,
                    created_at__gte=campaign.created_at
                ).exists()
                
                if not existing:
                    # Create context data for this recipient
                    context_data = {
                        'campaign': {
                            'name': campaign.name,
                            'description': campaign.description,
                        }
                    }
                    
                    # Render template
                    subject = campaign.template.render_subject(context_data)
                    html_content = campaign.template.render_html_content(context_data)
                    text_content = campaign.template.render_text_content(context_data)
                    
                    # Create email message
                    email_message = EmailMessage.objects.create(
                        organization=campaign.organization,
                        template=campaign.template,
                        to_email=email,
                        from_email=campaign.template.get_from_email(),
                        from_name=campaign.template.get_from_name(),
                        reply_to=campaign.template.reply_to,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        context_data=context_data,
                        status='QUEUED',
                        priority='NORMAL',
                        created_by=campaign.created_by
                    )
                    
                    # Send email
                    send_email_message.delay(email_message.id)
                    created_count += 1
                    
            except Exception as e:
                logger.error(f"Error creating email for {email}: {str(e)}")
                campaign.emails_failed += 1
        
        # Update campaign
        campaign.emails_sent = created_count
        campaign.status = 'SENT'
        campaign.save()
        
        logger.info(f"Email campaign completed: {campaign_id}, sent: {created_count}")
        return {"status": "success", "campaign_id": campaign_id, "emails_sent": created_count}
        
    except EmailCampaign.DoesNotExist:
        logger.error(f"Email campaign not found: {campaign_id}")
        return {"status": "error", "message": "Campaign not found"}
    except Exception as e:
        logger.error(f"Error sending email campaign: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def process_email_queue():
    """
    Process pending emails in the queue.
    
    This task runs every minute to send queued emails.
    """
    logger.info("Processing email queue")
    
    try:
        from .models import EmailMessage
        
        # Get pending emails
        pending_emails = EmailMessage.objects.filter(
            status='QUEUED',
            scheduled_for__lte=timezone.now()
        ).order_by('priority', 'scheduled_for')[:100]  # Process up to 100 emails
        
        sent_count = 0
        failed_count = 0
        
        for email in pending_emails:
            try:
                # Send email
                result = send_email_message(email.id)
                if result.get('status') == 'success':
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing email {email.id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Email queue processed - Sent: {sent_count}, Failed: {failed_count}")
        return {"status": "success", "sent": sent_count, "failed": failed_count}
        
    except Exception as e:
        logger.error(f"Error processing email queue: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def generate_email_analytics():
    """
    Generate email analytics snapshots.
    
    This task runs daily to create analytics snapshots.
    """
    logger.info("Generating email analytics")
    
    try:
        from .models import EmailAnalytics, EmailMessage
        from organizations.models import Organization
        
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)
        
        snapshots_created = 0
        
        for organization in Organization.objects.filter(is_active=True):
            try:
                # Check if snapshot already exists
                if EmailAnalytics.objects.filter(
                    organization=organization,
                    period_type='DAILY',
                    period_start__date=yesterday
                ).exists():
                    continue
                
                # Calculate metrics for yesterday
                emails = EmailMessage.objects.filter(
                    organization=organization,
                    created_at__date=yesterday
                )
                
                emails_sent = emails.filter(status='SENT').count()
                emails_delivered = emails.filter(status='DELIVERED').count()
                emails_opened = emails.filter(status='OPENED').count()
                emails_clicked = emails.filter(status='CLICKED').count()
                emails_bounced = emails.filter(status='BOUNCED').count()
                emails_complained = emails.filter(status='COMPLAINED').count()
                
                # Create analytics snapshot
                analytics = EmailAnalytics.objects.create(
                    organization=organization,
                    period_type='DAILY',
                    period_start=timezone.datetime.combine(yesterday, timezone.datetime.min.time()),
                    period_end=timezone.datetime.combine(yesterday, timezone.datetime.max.time()),
                    emails_sent=emails_sent,
                    emails_delivered=emails_delivered,
                    emails_opened=emails_opened,
                    emails_clicked=emails_clicked,
                    emails_bounced=emails_bounced,
                    emails_complained=emails_complained
                )
                
                # Calculate rates
                analytics.calculate_rates()
                snapshots_created += 1
                
            except Exception as e:
                logger.error(f"Error creating analytics for {organization.name}: {str(e)}")
        
        logger.info(f"Email analytics generated: {snapshots_created} snapshots")
        return {"status": "success", "snapshots_created": snapshots_created}
        
    except Exception as e:
        logger.error(f"Error generating email analytics: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_old_emails():
    """
    Clean up old email data.
    
    This task runs weekly to remove old emails and logs.
    """
    logger.info("Cleaning up old email data")
    
    try:
        from .models import EmailMessage, EmailLog, EmailAnalytics
        
        # Define retention periods
        email_retention_days = 90
        log_retention_days = 30
        analytics_retention_days = 365
        
        cutoff_emails = timezone.now() - timezone.timedelta(days=email_retention_days)
        cutoff_logs = timezone.now() - timezone.timedelta(days=log_retention_days)
        cutoff_analytics = timezone.now() - timezone.timedelta(days=analytics_retention_days)
        
        # Clean up old emails
        old_emails = EmailMessage.objects.filter(
            created_at__lt=cutoff_emails,
            status__in=['SENT', 'DELIVERED', 'FAILED']
        )
        emails_deleted = old_emails.count()
        old_emails.delete()
        
        # Clean up old logs
        old_logs = EmailLog.objects.filter(timestamp__lt=cutoff_logs)
        logs_deleted = old_logs.count()
        old_logs.delete()
        
        # Clean up old analytics
        old_analytics = EmailAnalytics.objects.filter(
            period_start__lt=cutoff_analytics,
            period_type='DAILY'
        )
        analytics_deleted = old_analytics.count()
        old_analytics.delete()
        
        logger.info(f"Email cleanup completed - "
                   f"Emails: {emails_deleted}, "
                   f"Logs: {logs_deleted}, "
                   f"Analytics: {analytics_deleted}")
        
        return {
            "status": "success",
            "emails_deleted": emails_deleted,
            "logs_deleted": logs_deleted,
            "analytics_deleted": analytics_deleted
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up email data: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def send_scheduled_emails():
    """
    Send scheduled emails that are due.
    
    This task runs every 15 minutes to check for scheduled emails.
    """
    logger.info("Checking for scheduled emails")
    
    try:
        from .models import EmailMessage
        
        # Get emails scheduled for now or earlier
        scheduled_emails = EmailMessage.objects.filter(
            status='QUEUED',
            scheduled_for__lte=timezone.now()
        ).order_by('priority', 'scheduled_for')[:50]  # Limit to 50 per run
        
        sent_count = 0
        
        for email in scheduled_emails:
            try:
                send_email_message.delay(email.id)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error queuing scheduled email {email.id}: {str(e)}")
        
        logger.info(f"Scheduled emails processed: {sent_count}")
        return {"status": "success", "emails_processed": sent_count}
        
    except Exception as e:
        logger.error(f"Error processing scheduled emails: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def test_email_provider(provider_id):
    """
    Test email provider health.
    
    Args:
        provider_id (str): UUID of the EmailProvider to test
    """
    logger.info(f"Testing email provider: {provider_id}")
    
    try:
        from .models import EmailProvider
        
        provider = EmailProvider.objects.get(id=provider_id)
        
        # Simple health check - try to send test email
        try:
            from django.core.mail import send_mail
            
            send_mail(
                subject='Email Provider Health Check',
                message='This is a health check email.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],  # Would use a real test email
                fail_silently=False
            )
            
            # Mark as healthy
            provider.is_healthy = True
            provider.health_check_error = ''
            provider.last_health_check = timezone.now()
            provider.save()
            
            logger.info(f"Email provider {provider.name} is healthy")
            return {"status": "success", "provider": provider.name}
            
        except Exception as e:
            # Mark as unhealthy
            provider.is_healthy = False
            provider.health_check_error = str(e)
            provider.last_health_check = timezone.now()
            provider.save()
            
            logger.error(f"Email provider {provider.name} failed health check: {str(e)}")
            return {"status": "error", "provider": provider.name, "error": str(e)}
        
    except EmailProvider.DoesNotExist:
        logger.error(f"Email provider not found: {provider_id}")
        return {"status": "error", "message": "Provider not found"}
    except Exception as e:
        logger.error(f"Error testing email provider: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def process_email_bounces():
    """
    Process email bounces and update blacklist.
    
    This task would integrate with email provider webhooks.
    """
    logger.info("Processing email bounces")
    
    try:
        from .models import EmailMessage, EmailBlacklist
        
        # Find emails that bounced
        bounced_emails = EmailMessage.objects.filter(
            status='BOUNCED',
            created_at__gte=timezone.now() - timezone.timedelta(days=1)
        )
        
        blacklisted_count = 0
        
        for email in bounced_emails:
            # Add to blacklist if hard bounce
            if 'hard' in email.error_message.lower():
                EmailBlacklist.add_to_blacklist(
                    email=email.to_email,
                    blacklist_type='BOUNCE',
                    reason=email.error_message,
                    source_email=email
                )
                blacklisted_count += 1
        
        logger.info(f"Email bounces processed - Blacklisted: {blacklisted_count}")
        return {"status": "success", "blacklisted": blacklisted_count}
        
    except Exception as e:
        logger.error(f"Error processing email bounces: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def send_assessment_reminders():
    """
    Send reminders for incomplete assessments.
    
    This task runs daily to send reminders.
    """
    logger.info("Sending assessment reminders")
    
    try:
        from assessments.models import AssessmentInstance
        from .utils import send_email
        
        # Find assessments that need reminders
        reminder_date = timezone.now() - timezone.timedelta(days=3)  # 3 days after invitation
        
        instances_needing_reminder = AssessmentInstance.objects.filter(
            status__in=['INVITED', 'STARTED', 'IN_PROGRESS'],
            invited_at__date=reminder_date.date(),
            expires_at__gt=timezone.now()
        )
        
        reminders_sent = 0
        
        for instance in instances_needing_reminder:
            try:
                context_data = {
                    'user': {
                        'first_name': instance.user.first_name,
                        'full_name': instance.user.full_name,
                        'email': instance.user.email,
                    },
                    'assessment': {
                        'name': instance.assessment.name,
                        'url': f"{settings.SITE_URL}/assessments/take/{instance.token}/",
                        'expires_at': instance.expires_at,
                        'progress': instance.progress_percentage,
                    }
                }
                
                send_email(
                    template_type='ASSESSMENT_REMINDER',
                    to_email=instance.user.email,
                    context_data=context_data,
                    organization=instance.organization,
                    related_object=instance
                )
                
                reminders_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending reminder for assessment {instance.id}: {str(e)}")
        
        logger.info(f"Assessment reminders sent: {reminders_sent}")
        return {"status": "success", "reminders_sent": reminders_sent}
        
    except Exception as e:
        logger.error(f"Error sending assessment reminders: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def send_pdi_reminders():
    """
    Send reminders for PDI tasks and reviews.
    
    This task runs daily to send PDI-related reminders.
    """
    logger.info("Sending PDI reminders")
    
    try:
        from pdi.models import PDITask, PDIPlan
        from .utils import send_email
        
        today = timezone.now().date()
        reminder_date = today + timezone.timedelta(days=7)  # 7 days before deadline
        
        # Find tasks due soon
        tasks_due_soon = PDITask.objects.filter(
            status__in=['NOT_STARTED', 'IN_PROGRESS'],
            time_bound_deadline=reminder_date,
            is_active=True
        )
        
        # Find overdue tasks
        overdue_tasks = PDITask.objects.filter(
            status__in=['NOT_STARTED', 'IN_PROGRESS'],
            time_bound_deadline__lt=today,
            is_active=True
        )
        
        reminders_sent = 0
        
        # Send due soon reminders
        for task in tasks_due_soon:
            try:
                context_data = {
                    'user': {
                        'first_name': task.pdi_plan.employee.first_name,
                        'full_name': task.pdi_plan.employee.full_name,
                    },
                    'task': {
                        'title': task.title,
                        'deadline': task.time_bound_deadline,
                        'progress': task.progress_percentage,
                    },
                    'pdi_plan': {
                        'title': task.pdi_plan.title,
                        'url': f"{settings.SITE_URL}/pdi/plans/{task.pdi_plan.id}/",
                    }
                }
                
                send_email(
                    template_type='PDI_TASK_DUE',
                    to_email=task.pdi_plan.employee.email,
                    context_data=context_data,
                    organization=task.pdi_plan.organization,
                    related_object=task
                )
                
                reminders_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending PDI reminder for task {task.id}: {str(e)}")
        
        # Send overdue reminders
        for task in overdue_tasks:
            try:
                context_data = {
                    'user': {
                        'first_name': task.pdi_plan.employee.first_name,
                        'full_name': task.pdi_plan.employee.full_name,
                    },
                    'task': {
                        'title': task.title,
                        'deadline': task.time_bound_deadline,
                        'days_overdue': (today - task.time_bound_deadline).days,
                        'progress': task.progress_percentage,
                    },
                    'pdi_plan': {
                        'title': task.pdi_plan.title,
                        'url': f"{settings.SITE_URL}/pdi/plans/{task.pdi_plan.id}/",
                    }
                }
                
                send_email(
                    template_type='PDI_TASK_OVERDUE',
                    to_email=task.pdi_plan.employee.email,
                    context_data=context_data,
                    organization=task.pdi_plan.organization,
                    related_object=task
                )
                
                reminders_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending overdue reminder for task {task.id}: {str(e)}")
        
        logger.info(f"PDI reminders sent: {reminders_sent}")
        return {"status": "success", "reminders_sent": reminders_sent}
        
    except Exception as e:
        logger.error(f"Error sending PDI reminders: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def update_email_provider_usage():
    """
    Update email provider usage counters.
    
    This task runs daily to reset daily counters and monthly on the 1st.
    """
    logger.info("Updating email provider usage")
    
    try:
        from .models import EmailProvider
        
        today = timezone.now().date()
        
        # Reset daily counters
        EmailProvider.objects.all().update(emails_sent_today=0)
        
        # Reset monthly counters on the 1st
        if today.day == 1:
            EmailProvider.objects.all().update(emails_sent_this_month=0)
        
        logger.info("Email provider usage updated")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error updating email provider usage: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def process_unsubscribe_requests():
    """
    Process pending unsubscribe requests.
    
    This task runs hourly to process unsubscribe requests.
    """
    logger.info("Processing unsubscribe requests")
    
    try:
        from .models import UnsubscribeRequest
        
        # Get pending unsubscribe requests
        pending_requests = UnsubscribeRequest.objects.filter(
            is_processed=False
        )
        
        processed_count = 0
        
        for request in pending_requests:
            try:
                request.process_unsubscribe()
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing unsubscribe request {request.id}: {str(e)}")
        
        logger.info(f"Unsubscribe requests processed: {processed_count}")
        return {"status": "success", "processed": processed_count}
        
    except Exception as e:
        logger.error(f"Error processing unsubscribe requests: {str(e)}")
        return {"status": "error", "message": str(e)}