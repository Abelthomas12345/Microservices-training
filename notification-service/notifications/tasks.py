from celery import shared_task
import logging

logger = logging.getLogger(__name__)

# Recue la notification de création d'un contact depuis le contact-service
@shared_task(
    name="notifications.contact_created",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def contact_created(self, contact_data):
    print("=" * 60)
    print(f"📬 [CELERY] Notification reçue pour: {contact_data.get('name')}")
    print("=" * 60)

    logger.info("=" * 60)
    logger.info("NOTIFICATION RECUE")
    logger.info(contact_data)
    logger.info("=" * 60)

    return True