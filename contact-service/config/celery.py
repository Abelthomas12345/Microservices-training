import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('contact_service')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.task_default_queue = "notifications"

app.conf.task_routes = {
    "notifications.contact_created": {
        "queue": "notifications"
    }
}