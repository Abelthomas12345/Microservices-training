import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
logger = logging.getLogger(__name__)

class NotifyView(APIView):
    def post(self, request):
        data = request.data
        # On simule l'envoi d'une notification (log uniquement)
        print(f"📧 [NOTIFICATION] Contact '{data.get('name')}' (ID: {data.get('contact_id')}) créé.")
        return Response(
            {"message": "Notification envoyée avec succès"},
            status=status.HTTP_200_OK
        )