"""
Email utilities and helper functions.
"""
import base64
import json
import uuid
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import EmailTemplate, EmailMessage, EmailSubscription, EmailBlacklist

User = get_user_model()


def send_email(
    template_type: str,
    to_email: str,
    context_data: Dict[str, Any],
    organization=None,
    language: str = 'en',
    priority: str = 'NORMAL',
    scheduled_for: Optional[timezone.datetime] = None,
    created_by: Optional[User] = None,
    related_object=None
) -> EmailMessage:
    """
    Send email using template.
    
    Args:
        template_type: Type of email template to use
        to_email: Recipient email address
        context_data: Context data for template rendering
        organization: Organization (for multi-tenant templates)
        language: Language code for template
        priority: Email priority (LOW, NORMAL, HIGH, URGENT)
        scheduled_for: When to send the email (None for immediate)
        created_by: User who triggered the email
        related_object: Related model instance
    
    Returns:
        EmailMessage instance
    """
    # Check if email is blacklisted
    if EmailBlacklist.is_blacklisted(to_email):
        raise ValueError(f"Email {to_email} is blacklisted")
    
    # Get template
    template = get_email_template(template_type, organization, language)
    if not template:
        raise ValueError(f"No template found for type {template_type}")
    
    # Add default context data
    context_data = _build_context_data(context_data, organization, to_email)
    
    # Render template
    subject = template.render_subject(context_data)
    html_content = template.render_html_content(context_data)
    text_content = template.render_text_content(context_data)
    
    # Get user if exists
    user = None
    try:
        user = User.objects.get(email=to_email)
    except User.DoesNotExist:
        pass
    
    # Create email message
    email_message = EmailMessage.objects.create(
        organization=organization,
        template=template,
        to_email=to_email,
        to_name=context_data.get('user', {}).get('full_name', ''),
        from_email=template.get_from_email(),
        from_name=template.get_from_name(),
        reply_to=template.reply_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        context_data=context_data,
        status='QUEUED',
        priority=priority,
        scheduled_for=scheduled_for or timezone.now(),
        user=user,
        created_by=created_by
    )
    
    # Set related object info
    if related_object:
        email_message.related_object_type = related_object.__class__.__name__
        email_message.related_object_id = related_object.id
        email_message.save()
    
    # Add tracking URLs
    _add_tracking_urls(email_message)
    
    # Queue for sending
    from .tasks import send_email_message
    if scheduled_for and scheduled_for > timezone.now():
        # Schedule for later
        send_email_message.apply_async(args=[email_message.id], eta=scheduled_for)
    else:
        # Send immediately
        send_email_message.delay(email_message.id)
    
    return email_message


def get_email_template(template_type: str, organization=None, language: str = 'en') -> Optional[EmailTemplate]:
    """
    Get email template by type, organization, and language.
    
    Args:
        template_type: Type of template
        organization: Organization (None for global templates)
        language: Language code
    
    Returns:
        EmailTemplate instance or None
    """
    # Try to get organization-specific template first
    if organization:
        template = EmailTemplate.objects.filter(
            organization=organization,
            template_type=template_type,
            language=language,
            is_active=True
        ).first()
        
        if template:
            return template
    
    # Fallback to default template
    template = EmailTemplate.objects.filter(
        template_type=template_type,
        language=language,
        is_active=True,
        is_default=True
    ).first()
    
    # Fallback to English if language not found
    if not template and language != 'en':
        template = EmailTemplate.objects.filter(
            template_type=template_type,
            language='en',
            is_active=True,
            is_default=True
        ).first()
    
    return template


def _build_context_data(context_data: Dict[str, Any], organization=None, to_email: str = '') -> Dict[str, Any]:
    """Build complete context data with defaults."""
    # Base context
    base_context = {
        'site_name': 'Psychological Assessments Platform',
        'site_url': getattr(settings, 'SITE_URL', 'https://example.com'),
        'current_year': timezone.now().year,
        'timestamp': timezone.now(),
    }
    
    # Organization context
    if organization:
        base_context['organization'] = {
            'name': organization.name,
            'email': organization.email,
            'website': organization.website,
            'primary_color': organization.primary_color,
            'logo_url': organization.logo.url if organization.logo else '',
        }
    
    # User context (try to get from email)
    if to_email and 'user' not in context_data:
        try:
            user = User.objects.get(email=to_email)
            base_context['user'] = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'email': user.email,
            }
        except User.DoesNotExist:
            base_context['user'] = {
                'first_name': '',
                'last_name': '',
                'full_name': to_email,
                'email': to_email,
            }
    
    # Merge with provided context
    base_context.update(context_data)
    
    return base_context


def _add_tracking_urls(email_message: EmailMessage):
    """Add tracking URLs to email content."""
    message_id = str(email_message.id)
    
    # Generate tracking pixel URL
    tracking_pixel_url = f"{settings.SITE_URL}/emails/track/{message_id}/open/"
    email_message.tracking_pixel_url = tracking_pixel_url
    
    # Generate unsubscribe URL
    unsubscribe_data = {
        'email': email_message.to_email,
        'message_id': message_id,
    }
    unsubscribe_token = base64.urlsafe_b64encode(
        json.dumps(unsubscribe_data).encode()
    ).decode()
    
    unsubscribe_url = f"{settings.SITE_URL}/emails/unsubscribe/{unsubscribe_token}/"
    email_message.unsubscribe_url = unsubscribe_url
    
    # Add tracking pixel to HTML content
    if email_message.html_content:
        tracking_pixel = f'<img src="{tracking_pixel_url}" width="1" height="1" style="display:none;" alt="">'
        email_message.html_content += tracking_pixel
    
    # Add unsubscribe link to content
    unsubscribe_link = f'<a href="{unsubscribe_url}">Unsubscribe</a>'
    
    if email_message.html_content:
        # Add to HTML content
        email_message.html_content = email_message.html_content.replace(
            '{{unsubscribe_url}}', unsubscribe_url
        ).replace(
            '{{unsubscribe_link}}', unsubscribe_link
        )
    
    if email_message.text_content:
        # Add to text content
        email_message.text_content = email_message.text_content.replace(
            '{{unsubscribe_url}}', unsubscribe_url
        )
        email_message.text_content += f"\n\nTo unsubscribe: {unsubscribe_url}"
    
    email_message.save()


def send_assessment_invitation(assessment_instance, invited_by=None):
    """Send assessment invitation email."""
    context_data = {
        'user': {
            'first_name': assessment_instance.user.first_name,
            'last_name': assessment_instance.user.last_name,
            'full_name': assessment_instance.user.full_name,
            'email': assessment_instance.user.email,
        },
        'assessment': {
            'name': assessment_instance.assessment.name,
            'description': assessment_instance.assessment.description,
            'estimated_duration': assessment_instance.assessment.estimated_duration,
            'instructions': assessment_instance.assessment.instructions,
            'url': f"{settings.SITE_URL}/assessments/take/{assessment_instance.token}/",
            'expires_at': assessment_instance.expires_at,
        },
        'invited_by': {
            'name': invited_by.full_name if invited_by else '',
            'email': invited_by.email if invited_by else '',
        }
    }
    
    return send_email(
        template_type='ASSESSMENT_INVITATION',
        to_email=assessment_instance.user.email,
        context_data=context_data,
        organization=assessment_instance.organization,
        created_by=invited_by,
        related_object=assessment_instance
    )


def send_pdi_notification(pdi_plan, notification_type='PDI_CREATED', recipient=None):
    """Send PDI-related notifications."""
    recipient = recipient or pdi_plan.employee
    
    context_data = {
        'user': {
            'first_name': recipient.first_name,
            'last_name': recipient.last_name,
            'full_name': recipient.full_name,
            'email': recipient.email,
        },
        'pdi_plan': {
            'title': pdi_plan.title,
            'description': pdi_plan.description,
            'progress': pdi_plan.overall_progress,
            'target_date': pdi_plan.target_completion_date,
            'url': f"{settings.SITE_URL}/pdi/plans/{pdi_plan.id}/",
        },
        'employee': {
            'name': pdi_plan.employee.full_name,
            'email': pdi_plan.employee.email,
        },
        'manager': {
            'name': pdi_plan.manager.full_name if pdi_plan.manager else '',
            'email': pdi_plan.manager.email if pdi_plan.manager else '',
        }
    }
    
    return send_email(
        template_type=notification_type,
        to_email=recipient.email,
        context_data=context_data,
        organization=pdi_plan.organization,
        related_object=pdi_plan
    )


def send_organization_invite(invite, invited_by=None):
    """Send organization invitation email."""
    context_data = {
        'organization': {
            'name': invite.organization.name,
            'kind': invite.organization.get_kind_display(),
        },
        'invite': {
            'role': invite.get_role_display(),
            'message': invite.message,
            'expires_at': invite.expires_at,
            'url': f"{settings.SITE_URL}/organizations/invites/accept/{invite.token}/",
        },
        'invited_by': {
            'name': invited_by.full_name if invited_by else '',
            'email': invited_by.email if invited_by else '',
        }
    }
    
    return send_email(
        template_type='ORGANIZATION_INVITE',
        to_email=invite.email,
        context_data=context_data,
        organization=invite.organization,
        created_by=invited_by,
        related_object=invite
    )


def send_billing_notification(subscription, notification_type, additional_context=None):
    """Send billing-related notifications."""
    context_data = {
        'subscription': {
            'plan_name': subscription.plan.name,
            'amount': subscription.amount,
            'currency': subscription.currency,
            'billing_cycle': subscription.get_billing_cycle_display(),
            'current_period_end': subscription.current_period_end,
            'status': subscription.get_status_display(),
        }
    }
    
    if additional_context:
        context_data.update(additional_context)
    
    # Send to organization admin email
    admin_email = subscription.organization.email
    if not admin_email:
        # Fallback to organization admin users
        from organizations.models import Membership
        admin_membership = Membership.objects.filter(
            organization=subscription.organization,
            role='ORG_ADMIN',
            is_active=True
        ).first()
        
        if admin_membership:
            admin_email = admin_membership.user.email
        else:
            return None
    
    return send_email(
        template_type=notification_type,
        to_email=admin_email,
        context_data=context_data,
        organization=subscription.organization,
        related_object=subscription
    )


def send_recruiting_notification(application, notification_type, recipient_email=None):
    """Send recruiting-related notifications."""
    recipient_email = recipient_email or application.candidate.email
    
    context_data = {
        'candidate': {
            'first_name': application.candidate.first_name,
            'last_name': application.candidate.last_name,
            'full_name': application.candidate.full_name,
            'email': application.candidate.email,
        },
        'job': {
            'title': application.job.title,
            'company': application.job.client.name,
            'location': application.job.location,
            'description': application.job.description,
        },
        'application': {
            'status': application.get_status_display(),
            'applied_date': application.applied_date,
            'fit_score': application.fit_score,
        }
    }
    
    return send_email(
        template_type=notification_type,
        to_email=recipient_email,
        context_data=context_data,
        organization=application.organization,
        related_object=application
    )


def create_default_templates(organization):
    """Create default email templates for an organization."""
    templates = [
        {
            'name': 'Assessment Invitation',
            'template_type': 'ASSESSMENT_INVITATION',
            'subject': 'You\'re invited to complete: {{assessment.name}}',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {{organization.primary_color|default:"#007bff"}}; color: white; padding: 20px; text-align: center;">
                    <h1>Assessment Invitation</h1>
                </div>
                
                <div style="padding: 20px;">
                    <p>Hello {{user.first_name}},</p>
                    
                    <p>You have been invited to complete the following psychological assessment:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: {{organization.primary_color|default:"#007bff"}};">{{assessment.name}}</h3>
                        <p style="margin: 0;"><strong>Estimated Duration:</strong> {{assessment.estimated_duration}} minutes</p>
                        {% if assessment.description %}
                        <p style="margin: 10px 0 0 0;">{{assessment.description}}</p>
                        {% endif %}
                    </div>
                    
                    {% if assessment.instructions %}
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="margin: 0 0 10px 0;">Instructions:</h4>
                        <p style="margin: 0;">{{assessment.instructions}}</p>
                    </div>
                    {% endif %}
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{assessment.url}}" style="background-color: {{organization.primary_color|default:"#007bff"}}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Start Assessment
                        </a>
                    </div>
                    
                    <p><strong>Important:</strong> This invitation expires on {{assessment.expires_at|date:"F d, Y"}}.</p>
                    
                    {% if invited_by.name %}
                    <p>This assessment was sent by {{invited_by.name}} ({{invited_by.email}}).</p>
                    {% endif %}
                    
                    <p>If you have any questions, please contact your HR department or the person who sent this invitation.</p>
                    
                    <hr style="margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        This assessment is for organizational use only and is not intended for clinical diagnosis.
                        <br><a href="{{unsubscribe_url}}">Unsubscribe</a> from these emails.
                    </p>
                </div>
            </div>
            ''',
            'text_content': '''
Hello {{user.first_name}},

You have been invited to complete the following psychological assessment:

Assessment: {{assessment.name}}
Duration: {{assessment.estimated_duration}} minutes
{% if assessment.description %}Description: {{assessment.description}}{% endif %}

{% if assessment.instructions %}
Instructions:
{{assessment.instructions}}
{% endif %}

To start the assessment, visit: {{assessment.url}}

Important: This invitation expires on {{assessment.expires_at|date:"F d, Y"}}.

{% if invited_by.name %}This assessment was sent by {{invited_by.name}} ({{invited_by.email}}).{% endif %}

If you have any questions, please contact your HR department.

---
This assessment is for organizational use only and is not intended for clinical diagnosis.
To unsubscribe: {{unsubscribe_url}}
            '''
        },
        {
            'name': 'PDI Plan Created',
            'template_type': 'PDI_CREATED',
            'subject': 'Your Development Plan is Ready: {{pdi_plan.title}}',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
                    <h1>Development Plan Created</h1>
                </div>
                
                <div style="padding: 20px;">
                    <p>Hello {{user.first_name}},</p>
                    
                    <p>Your Individual Development Plan (PDI) has been created and is ready for review:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #28a745;">{{pdi_plan.title}}</h3>
                        <p style="margin: 0;"><strong>Target Completion:</strong> {{pdi_plan.target_date|date:"F d, Y"}}</p>
                        <p style="margin: 10px 0 0 0;">{{pdi_plan.description}}</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{pdi_plan.url}}" style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Development Plan
                        </a>
                    </div>
                    
                    {% if manager.name %}
                    <p>Your manager {{manager.name}} will review and approve this plan.</p>
                    {% endif %}
                    
                    <p>This plan is designed to help you grow professionally and achieve your career goals.</p>
                    
                    <hr style="margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        <a href="{{unsubscribe_url}}">Unsubscribe</a> from these emails.
                    </p>
                </div>
            </div>
            ''',
        },
        {
            'name': 'Organization Invitation',
            'template_type': 'ORGANIZATION_INVITE',
            'subject': 'You\'re invited to join {{organization.name}}',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {{organization.primary_color|default:"#007bff"}}; color: white; padding: 20px; text-align: center;">
                    <h1>Organization Invitation</h1>
                </div>
                
                <div style="padding: 20px;">
                    <p>Hello,</p>
                    
                    <p>You have been invited to join <strong>{{organization.name}}</strong> as a {{invite.role}}.</p>
                    
                    {% if invite.message %}
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="margin: 0 0 10px 0;">Personal Message:</h4>
                        <p style="margin: 0;">{{invite.message}}</p>
                    </div>
                    {% endif %}
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{invite.url}}" style="background-color: {{organization.primary_color|default:"#007bff"}}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Accept Invitation
                        </a>
                    </div>
                    
                    <p><strong>Important:</strong> This invitation expires on {{invite.expires_at|date:"F d, Y"}}.</p>
                    
                    {% if invited_by.name %}
                    <p>This invitation was sent by {{invited_by.name}} ({{invited_by.email}}).</p>
                    {% endif %}
                    
                    <hr style="margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        <a href="{{unsubscribe_url}}">Unsubscribe</a> from these emails.
                    </p>
                </div>
            </div>
            ''',
        },
        {
            'name': 'Welcome Email',
            'template_type': 'WELCOME',
            'subject': 'Welcome to {{organization.name}}!',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {{organization.primary_color|default:"#007bff"}}; color: white; padding: 20px; text-align: center;">
                    <h1>Welcome!</h1>
                </div>
                
                <div style="padding: 20px;">
                    <p>Hello {{user.first_name}},</p>
                    
                    <p>Welcome to <strong>{{organization.name}}</strong>! We're excited to have you on board.</p>
                    
                    <p>Our psychological assessments platform will help you:</p>
                    <ul>
                        <li>Complete personality and skills assessments</li>
                        <li>Receive personalized development recommendations</li>
                        <li>Track your professional growth</li>
                        <li>Collaborate with your team and managers</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{site_url}}" style="background-color: {{organization.primary_color|default:"#007bff"}}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Get Started
                        </a>
                    </div>
                    
                    <p>If you have any questions, don't hesitate to reach out to your HR team.</p>
                    
                    <hr style="margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        <a href="{{unsubscribe_url}}">Unsubscribe</a> from these emails.
                    </p>
                </div>
            </div>
            ''',
        }
    ]
    
    for template_data in templates:
        EmailTemplate.objects.get_or_create(
            organization=organization,
            template_type=template_data['template_type'],
            language='en',
            defaults={
                'name': template_data['name'],
                'subject': template_data['subject'],
                'html_content': template_data['html_content'],
                'text_content': template_data.get('text_content', ''),
                'is_default': True,
                'is_active': True,
            }
        )


def create_user_email_subscriptions(user, organization):
    """Create default email subscriptions for a new user."""
    subscription_types = [
        'ASSESSMENT_NOTIFICATIONS',
        'PDI_NOTIFICATIONS',
        'SYSTEM_NOTIFICATIONS',
    ]
    
    # Add recruiting notifications for recruiter organizations
    if organization.is_recruiter:
        subscription_types.append('RECRUITING_NOTIFICATIONS')
    
    # Add billing notifications for admins
    from organizations.models import Membership
    membership = Membership.objects.filter(
        user=user,
        organization=organization,
        role__in=['ORG_ADMIN', 'HR']
    ).first()
    
    if membership:
        subscription_types.append('BILLING_NOTIFICATIONS')
    
    # Create subscriptions
    for subscription_type in subscription_types:
        EmailSubscription.objects.get_or_create(
            user=user,
            organization=organization,
            subscription_type=subscription_type,
            defaults={
                'is_subscribed': True,
                'frequency': 'IMMEDIATE',
            }
        )


def get_email_analytics_data(organization, days=30):
    """Get email analytics data for organization."""
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=days)
    
    emails = EmailMessage.objects.filter(
        organization=organization,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Daily metrics
    daily_data = []
    for i in range(days):
        date = start_date + timezone.timedelta(days=i)
        day_emails = emails.filter(created_at__date=date)
        
        daily_data.append({
            'date': date.isoformat(),
            'sent': day_emails.filter(status='SENT').count(),
            'delivered': day_emails.filter(status='DELIVERED').count(),
            'opened': day_emails.filter(status='OPENED').count(),
            'clicked': day_emails.filter(status='CLICKED').count(),
            'failed': day_emails.filter(status='FAILED').count(),
        })
    
    # Overall metrics
    total_emails = emails.count()
    sent_emails = emails.filter(status='SENT').count()
    delivered_emails = emails.filter(status='DELIVERED').count()
    opened_emails = emails.filter(status='OPENED').count()
    clicked_emails = emails.filter(status='CLICKED').count()
    failed_emails = emails.filter(status='FAILED').count()
    
    return {
        'daily_data': daily_data,
        'summary': {
            'total_emails': total_emails,
            'delivery_rate': (delivered_emails / sent_emails * 100) if sent_emails > 0 else 0,
            'open_rate': (opened_emails / delivered_emails * 100) if delivered_emails > 0 else 0,
            'click_rate': (clicked_emails / delivered_emails * 100) if delivered_emails > 0 else 0,
            'failure_rate': (failed_emails / total_emails * 100) if total_emails > 0 else 0,
        }
    }


def validate_email_template(template_content, context_data):
    """Validate email template with sample context."""
    try:
        template = Template(template_content)
        context = Context(context_data)
        rendered = template.render(context)
        return True, rendered
    except Exception as e:
        return False, str(e)


def generate_unsubscribe_token(email, message_id=None):
    """Generate unsubscribe token."""
    data = {
        'email': email,
        'message_id': str(message_id) if message_id else None,
        'timestamp': timezone.now().isoformat(),
    }
    
    token = base64.urlsafe_b64encode(
        json.dumps(data).encode()
    ).decode()
    
    return token


def parse_unsubscribe_token(token):
    """Parse unsubscribe token."""
    try:
        decoded_data = base64.urlsafe_b64decode(token.encode()).decode()
        return json.loads(decoded_data)
    except Exception:
        return None