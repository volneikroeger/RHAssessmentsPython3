"""
Celery configuration for psychological assessments SaaS platform.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('assessments')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Periodic tasks
app.conf.beat_schedule = {
    'send-pdi-reminders': {
        'task': 'pdi.tasks.send_pdi_reminders',
        'schedule': 86400.0,  # Run daily
    },
    'check-subscription-renewals': {
        'task': 'billing.tasks.check_subscription_renewals',
        'schedule': 3600.0,  # Run hourly
    },
    'cleanup-expired-sessions': {
        'task': 'assessments.tasks.cleanup_expired_sessions',
        'schedule': 21600.0,  # Run every 6 hours
    },
}