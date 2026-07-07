"""
Client HTTP pour la communication synchrone contact-service -> notification-service.

Ce module isole l'appel HTTP qui était auparavant écrit directement dans
`ContactListCreateView.perform_create`. L'isoler dans une classe dédiée permet :

- de le réutiliser à la fois depuis les vues Django ET depuis les tests de
  contrat Pact (tests/pact/test_notification_consumer.py) ;
- de le mocker facilement dans des tests unitaires (sans appel réseau réel) ;
- de centraliser la configuration (URL du service, timeout).

C'est ce client qui joue le rôle de "Consumer" dans la relation Pact avec le
notification-service (le "Provider").
"""
from __future__ import annotations

import os

import requests


class NotificationServiceError(Exception):
    """Levée lorsque le notification-service ne peut pas être contacté
    ou renvoie une réponse invalide."""


class NotificationClient:
    """Client HTTP dédié au notification-service."""

    def __init__(self, base_url: str | None = None, timeout: float = 2.0) -> None:
        # base_url est injectable : en prod, il vient de la variable d'env
        # NOTIFICATION_SERVICE_URL ; dans les tests de contrat Pact, il pointe
        # vers le mock server démarré par pact.serve().
        self.base_url = (base_url or os.getenv(
            "NOTIFICATION_SERVICE_URL", "http://localhost:8003"
        )).rstrip("/")
        self.timeout = timeout

    def notify_contact_created(self, contact_id: int, contact_name: str) -> dict:
        """Notifie la création d'un contact.

        Effectue POST {base_url}/notify/ avec {"contact_id": ..., "contact_name": ...}.

        Retourne le corps JSON de la réponse en cas de succès.
        Lève NotificationServiceError en cas d'échec réseau ou de statut
        HTTP d'erreur.
        """
        url = f"{self.base_url}/notify/"
        try:
            response = requests.post(
                url,
                json={"contact_id": contact_id, "contact_name": contact_name},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise NotificationServiceError(
                f"Échec de l'appel au notification-service pour le contact "
                f"{contact_id}: {exc}"
            ) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise NotificationServiceError(
                "Réponse du notification-service non-JSON"
            ) from exc
