import os
import requests
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .models import Contact
from .serializers import ContactSerializer

class ContactListCreateView(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def perform_create(self, serializer):
        # 1. Sauvegarde du contact
        contact = serializer.save()
        
        # 2. Appel HTTP vers Notification Service (communication synchrone)
        notification_url = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8003')
        try:
            response = requests.post(
                f"{notification_url}/notify/",
                json={
                    "contact_id": contact.id,
                    "name": contact.name,
                    "email": contact.email
                },
                timeout=3
            )
            print(f"✅ Notification envoyée: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # On ne bloque pas la création du contact si la notif échoue
            print(f"⚠️ Erreur notification: {e}")

class ContactRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer