"""
Test de contrat (côté PROVIDER) : notification-service honore le contrat
défini par contact-service.

Ce test :
1. Localise le fichier de contrat généré par le test consumer
   (contact-service/tests/pact/test_notification_consumer.py), soit en local
   (chemin relatif dans le dépôt), soit via la variable d'environnement
   PACT_FILE si le fichier a été copié/récupéré autrement (ex: artefact CI,
   Pact Broker).
2. Démarre une VRAIE instance du notification-service (via le fixture
   `live_server` de pytest-django, qui lance le serveur de dev Django dans
   un thread du même process).
3. Rejoue chaque interaction du contrat contre ce serveur réel et vérifie
   que les réponses correspondent à ce que contact-service attend.

Prérequis :
    - Le fichier de contrat doit exister. Générez-le d'abord avec :
        cd contact-service && pytest tests/pact -v

Lancer uniquement ce test :
    cd notification-service
    pytest tests/pact -v
"""
import os
from pathlib import Path
from typing import Any, Literal

import pytest
from pact import Verifier

CONSUMER_NAME = "contact-service"
PROVIDER_NAME = "notification-service"

DEFAULT_PACT_FILE = (
    Path(__file__).resolve().parents[3]
    / "contact-service"
    / "pacts"
    / f"{CONSUMER_NAME}-{PROVIDER_NAME}.json"
)
PACT_FILE = Path(os.getenv("PACT_FILE", str(DEFAULT_PACT_FILE)))


def handle_provider_state(
    state: str,
    action: Literal["setup", "teardown"],
    parameters: dict[str, Any] | None,
) -> None:
    """Le NotifyView actuel n'a pas d'état interne (pas de base de données,
    pas de dépendance externe) : il répond toujours de la même façon.
    Il n'y a donc rien à préparer/nettoyer pour l'état
    "le notification-service est disponible" ; ce handler ne fait
    qu'acquitter l'état pour que la Verifier ne lève pas d'erreur
    "unknown state"."""
    known_states = {"le notification-service est disponible"}
    if state not in known_states:
        raise ValueError(f"État provider inconnu : {state!r} (action={action})")


@pytest.mark.skipif(
    not PACT_FILE.exists(),
    reason=(
        f"Fichier de contrat introuvable ({PACT_FILE}). "
        "Générez-le d'abord avec : cd contact-service && pytest tests/pact -v"
    ),
)
@pytest.mark.django_db
def test_notification_provider_honors_contract(live_server) -> None:
    verifier = (
        Verifier(PROVIDER_NAME)
        .add_source(str(PACT_FILE))
        .add_transport(url=live_server.url)
        .state_handler(handle_provider_state, teardown=True)
    )

    verifier.verify()
