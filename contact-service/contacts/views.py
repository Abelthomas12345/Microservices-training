import os
import requests
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .models import Contact
from .serializers import ContactSerializer
from celery import current_app
class ContactListCreateView(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def perform_create(self, serializer):
        # 1. Sauvegarde du contact
        contact = serializer.save()
        
        # 2. Communication HTTP (envoide synchrone) vers le notification-service
        notification_url = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8003')
        try:
            response = requests.post(
                f"{notification_url}/notify/",
                json={"contact_id": contact.id, "name": contact.name},
                timeout=2
            )
            print(f"✅ [HTTP] Notification envoyée: {response.status_code}")
        except Exception as e:
            print(f"⚠️ [HTTP] Erreur notification: {e}")
        
        # 3. 👇 NOUVEAU : Envoi asynchrone via Celery (en parallèle)
        try:
            contact_data = {
                'contact_id': contact.id,
                'name': contact.name,
                'email': contact.email,
                'owner_id': 1
            }

            print("=== AVANT SEND_TASK ===")

            result = current_app.send_task(
                "notifications.contact_created",
                kwargs={"contact_data": contact_data},
                queue="notifications"
            )

            print("TASK ID :", result.id)

            # Envoi de la tâche à la queue "notifications" pour le notification-service
            current_app.send_task(
                "notifications.contact_created",
                kwargs={
                    "contact_data": contact_data
                },
                queue="notifications"
            )
            print(f"✅ [Celery] Tâche de notification envoyée pour {contact.name}")
        except Exception as e:
            print(f"⚠️ [Celery] Erreur: {e}")
            print("=== APRES SEND_TASK ===")
            

class ContactRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer