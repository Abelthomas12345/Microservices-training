import os
import requests
from django.http import JsonResponse
from django.views import View

class ProxyView(View):
    def dispatch(self, request, *args, **kwargs):
        path = kwargs.get('path', '')
        
        # Décision du routage en fonction du début du chemin
        if path.startswith('users/'):
            target_base = os.getenv('USERS_SERVICE_URL', 'http://localhost:8001')
        elif path.startswith('contacts/'):
            target_base = os.getenv('CONTACT_SERVICE_URL', 'http://localhost:8002')
        elif path.startswith('notify/'):
            target_base = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8003')
        else:
            return JsonResponse({'error': 'Service not found'}, status=404)

        # Construction de l'URL cible
        target_url = f"{target_base}/{path}"
        
        # Nettoyage des headers (on retire Host pour ne pas gêner)
        headers = {key: value for key, value in request.headers.items()}
        headers.pop('Host', None)
        
        try:
            # Forward de la requête vers le microservice
            response = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=request.body,
                params=request.GET,
                timeout=10
            )
            
            # On renvoie la réponse au client
            # Si la réponse est du JSON, on le parse, sinon on renvoie le texte brut
            try:
                return JsonResponse(response.json(), status=response.status_code, safe=False)
            except:
                return JsonResponse({'detail': response.text}, status=response.status_code)
                
        except requests.exceptions.Timeout:
            return JsonResponse({'error': 'Service timeout'}, status=504)
        except requests.exceptions.ConnectionError:
            return JsonResponse({'error': 'Service unavailable'}, status=503)