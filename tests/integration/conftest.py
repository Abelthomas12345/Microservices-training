"""
Fixtures partagées pour la suite de tests d'intégration inter-services.

Ces tests supposent que la stack complète tourne via Docker Compose :

    docker-compose up --build -d

Ils ne mockent RIEN : ils envoient de vraies requêtes HTTP aux vrais
conteneurs (contact-service, notification-service, api-gateway) à travers
le réseau Docker, exactement comme le ferait un client Postman en suivant
le README. C'est ce qui en fait des tests d'INTÉGRATION inter-services,
par opposition aux tests de contrat Pact (qui testent le format de
l'échange en isolation) et aux tests unitaires/internes de chaque service.

Si la stack n'est pas démarrée, les tests sont automatiquement "skip" (pour
ne pas faire échouer une exécution `pytest` lancée par erreur sans Docker)
plutôt que d'échouer avec une erreur de connexion peu lisible.
"""
import os
import subprocess
import time

import pytest
import requests

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
CONTACT_SERVICE_URL = os.getenv("CONTACT_SERVICE_URL", "http://localhost:8002")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8003")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")


def _is_stack_up() -> bool:
    try:
        # /users/ répond même sans body particulier -> 200/404 selon la
        # route, l'important est d'obtenir une réponse HTTP (pas une
        # exception de connexion).
        requests.get(f"{CONTACT_SERVICE_URL}/contacts/", timeout=1.5)
        requests.get(f"{NOTIFICATION_SERVICE_URL}/notify/", timeout=1.5)
        return True
    except requests.exceptions.RequestException:
        return False


requires_running_stack = pytest.mark.skipif(
    not _is_stack_up(),
    reason=(
        "La stack Docker Compose ne semble pas démarrée. "
        "Lancez `docker-compose up --build -d` à la racine du dépôt "
        "avant d'exécuter la suite d'intégration inter-services."
    ),
)


def docker_compose_logs(service: str, since_seconds: int = 30) -> str:
    """Récupère les logs récents d'un service Docker Compose.

    Utilisé pour prouver, sans toucher au code applicatif, qu'un appel
    inter-services a effectivement eu lieu (le service appelé l'a bien
    reçu et traité), ce qui va au-delà d'un simple contrôle du code
    HTTP retourné au client.
    """
    result = subprocess.run(
        [
            "docker",
            "compose",
            "logs",
            f"--since={since_seconds}s",
            service,
        ],
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout + result.stderr


def wait_for_log_containing(service: str, needle: str, timeout: float = 10.0) -> bool:
    """Attend (en ré-interrogeant les logs) qu'une chaîne apparaisse dans les
    logs d'un service, utile car le traitement Celery est asynchrone."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if needle in docker_compose_logs(service):
            return True
        time.sleep(0.5)
    return False
