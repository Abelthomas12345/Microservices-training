"""
Tests d'intégration inter-microservices — Ticket 3.

Ces tests valident, sur la VRAIE stack Docker Compose (issue des tickets 1 et
2), que les services communiquent correctement entre eux :

1. Le flux HTTP synchrone contact-service -> notification-service
   (`POST /notify/`), introduit au ticket 1.
2. Le flux asynchrone contact-service -> RabbitMQ -> notification-service
   via Celery, introduit au ticket 2.
3. Le routage de l'API Gateway vers chaque service.

Prérequis :
    docker-compose up --build -d
    (attendre quelques secondes que les migrations et les workers démarrent)

Lancer :
    pytest tests/integration -v
"""
import uuid

import requests

from .conftest import (
    CONTACT_SERVICE_URL,
    GATEWAY_URL,
    NOTIFICATION_SERVICE_URL,
    requires_running_stack,
    wait_for_log_containing,
)


@requires_running_stack
class TestNotificationServiceContract:
    """Vérifie le comportement direct du notification-service (le Provider),
    indépendamment de contact-service. Complète la vérification Pact en
    conditions réelles de conteneur (réseau Docker, vrai serveur Django)."""

    def test_notify_endpoint_accepts_valid_payload(self) -> None:
        response = requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notify/",
            json={"contact_id": 999, "name": "Test Intégration"},
            timeout=5,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Notification envoyée avec succès"


@requires_running_stack
class TestContactToNotificationHttpFlow:
    """Vérifie le flux HTTP synchrone bout-en-bout : la création d'un
    contact sur contact-service déclenche réellement un appel réseau vers
    le notification-service, dans un AUTRE conteneur."""

    def test_creating_contact_triggers_real_http_notification(self) -> None:
        unique_name = f"Integration Test {uuid.uuid4().hex[:8]}"

        response = requests.post(
            f"{CONTACT_SERVICE_URL}/contacts/",
            json={
                "name": unique_name,
                "email": "integration@test.com",
                "company": "QA",
            },
            timeout=5,
        )

        assert response.status_code == 201
        contact_id = response.json()["id"]

        # Preuve que l'appel a réellement traversé le réseau Docker jusqu'au
        # notification-service : on retrouve le nom du contact dans SES
        # propres logs, écrits par NotifyView (voir notifications/views.py).
        found = wait_for_log_containing(
            "notification-service",
            f"Contact '{unique_name}' (ID: {contact_id}) créé.",
            timeout=10,
        )
        assert found, (
            "Le notification-service n'a pas loggé la réception de la "
            "notification HTTP pour ce contact - la communication "
            "inter-services a échoué."
        )


@requires_running_stack
class TestContactToNotificationCeleryFlow:
    """Vérifie le flux asynchrone (ticket 2) : la tâche Celery envoyée par
    contact-service est bien consommée par le worker du
    notification-service, via RabbitMQ."""

    def test_creating_contact_triggers_celery_notification(self) -> None:
        unique_name = f"Celery Integration {uuid.uuid4().hex[:8]}"

        response = requests.post(
            f"{CONTACT_SERVICE_URL}/contacts/",
            json={
                "name": unique_name,
                "email": "celery-integration@test.com",
            },
            timeout=5,
        )
        assert response.status_code == 201

        # Le worker Celery du notification-service log la réception de la
        # tâche "notifications.contact_created" (voir notifications/tasks.py)
        found = wait_for_log_containing(
            "notification-service",
            f"Notification reçue pour: {unique_name}",
            timeout=15,
        )
        assert found, (
            "Le worker Celery du notification-service n'a pas traité la "
            "tâche asynchrone envoyée par contact-service."
        )


@requires_running_stack
class TestApiGatewayRouting:
    """Vérifie que l'API Gateway route correctement vers chaque service
    (complète la couverture d'intégration de bout en bout)."""

    def test_gateway_routes_to_contact_service(self) -> None:
        response = requests.get(f"{GATEWAY_URL}/contacts/", timeout=5)
        assert response.status_code == 200

    def test_gateway_create_contact_end_to_end(self) -> None:
        unique_name = f"Gateway E2E {uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{GATEWAY_URL}/contacts/",
            json={"name": unique_name, "email": "gateway-e2e@test.com"},
            timeout=5,
        )
        assert response.status_code == 201
