"""
Test de contrat (côté CONSUMER) : contact-service -> notification-service.

Rôle dans l'architecture (voir README.md) :
    contact-service (Consumer) appelle POST /notify/ sur notification-service
    (Provider) à chaque création de contact.

Ce test :
1. Décrit l'interaction HTTP attendue avec notification-service.
2. Démarre un mock server Pact qui simule notification-service.
3. Exécute le VRAI code client (NotificationClient) contre ce mock server
   (jamais de mock "requests" ici : on veut vérifier que le client construit
   bien la requête attendue par le contrat).
4. Génère le fichier de contrat dans contact-service/pacts/, qui sera ensuite
   rejoué contre le vrai notification-service dans son test provider
   (notification-service/tests/pact/test_notification_provider.py).

Lancer uniquement ces tests :
    cd contact-service
    pytest tests/pact -v
"""
from pathlib import Path
from typing import Generator

import pytest
from pact import Pact, match

from contacts.notification_client import NotificationClient, NotificationServiceError

PACT_DIR = Path(__file__).resolve().parents[2] / "pacts"

CONSUMER_NAME = "contact-service"
PROVIDER_NAME = "notification-service"


@pytest.fixture()
def pact() -> Generator[Pact, None, None]:
    """Fournit un Pact réutilisable représentant le contrat entre
    contact-service et notification-service, et écrit le fichier de
    contrat une fois le test terminé."""
    pact = Pact(CONSUMER_NAME, PROVIDER_NAME).with_specification("V4")
    yield pact
    PACT_DIR.mkdir(parents=True, exist_ok=True)
    pact.write_file(PACT_DIR)


def test_notify_contact_created_success(pact: Pact) -> None:
    """Cas nominal : le notification-service accepte la notification et
    répond 200 avec un message de confirmation."""
    expected_response = {
        "message": match.str("Notification envoyée avec succès"),
    }

    (
        pact.upon_receiving(
            "Une notification de création de contact"
        )
        .given("le notification-service est disponible")
        .with_request("POST", "/notify/")
        .with_body(
            {
                "contact_id": match.int(1),
                "name": match.str("Marie Curie"),
            },
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(expected_response, content_type="application/json")
    )

    with pact.serve() as srv:
        client = NotificationClient(base_url=str(srv.url))
        result = client.notify_contact_created(contact_id=1, name="Marie Curie")

    assert result["message"] == "Notification envoyée avec succès"


# NB : le cas d'erreur (notification-service indisponible / 500) n'est PAS
# modélisé ici en tant qu'interaction Pact, car le contrat doit refléter un
# comportement que le Provider peut réellement reproduire lors de la
# vérification (le NotifyView actuel ne renvoie jamais 500). La résilience
# du NotificationClient face à une erreur réseau est couverte par un test
# unitaire dédié : tests/unit/test_notification_client.py
