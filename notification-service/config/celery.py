# import os
# from celery import Celery
# from kombu import Queue


# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# app = Celery('notification_service')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks()

# #creation d'une queue spécifique pour les notifications
# app.conf.task_default_queue = "notifications"
# app.conf.task_queues = (
#     Queue("notifications"),
# )

from celery import Celery
from kombu import Exchange, Queue
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.task_default_exchange = "microservices"
app.conf.task_default_exchange_type = "direct"
app.conf.task_default_routing_key = "notifications"
app.conf.task_default_queue = "notifications"

app.conf.task_queues = (
    Queue(
        "notifications",
        Exchange("microservices", type="direct", durable=True),
        routing_key="notifications",
        durable=True,
        exclusive=False,
        auto_delete=False,
    ),
)
app.conf.task_routes = {
    "notifications.contact_created": {
        "queue": "notifications"
    }
}