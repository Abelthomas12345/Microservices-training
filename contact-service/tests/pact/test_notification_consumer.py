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
print("Bonjour \n")
from pact_ffi import ffi
try:
    from pact import Pact, match
except Exception:  # pragma: no cover - fallback for editors / CI without pact installed
    try:
        from pact import Pact, match  # alternate import location
    except Exception:
        # Minimal fallbacks so linters/IDEs don't flag unresolved imports
        class _Match:
            @staticmethod
            def str(v):
                return v

            @staticmethod
            def int(v):
                return v

        class Pact:
            def __init__(self, *a, **k):
                pass

            def with_specification(self, *_):
                return self

            def upon_receiving(self, *_):
                return self

            def given(self, *_):
                return self

            def with_request(self, *_):
                return self

            def with_body(self, *_a, **_k):
                return self

            def will_respond_with(self, *_):
                return self

            from contextlib import contextmanager

            @contextmanager
            def serve(self):
                class _Srv:
                    url = "http://localhost:1234"

                yield _Srv()

            def write_file(self, *_):
                return None

        match = _Match()

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
                "contact_name": match.str("Marie Curie"),
            },
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(expected_response, content_type="application/json")
    )

    with pact.serve() as srv:
        client = NotificationClient(base_url=str(srv.url))
        result = client.notify_contact_created(contact_id=1, contact_name="Marie Curie")

    assert result["message"] == "Notification envoyée avec succès"


# NB : le cas d'erreur (notification-service indisponible / 500) n'est PAS
# modélisé ici en tant qu'interaction Pact, car le contrat doit refléter un
# comportement que le Provider peut réellement reproduire lors de la
# vérification (le NotifyView actuel ne renvoie jamais 500). La résilience
# du NotificationClient face à une erreur réseau est couverte par un test
# unitaire dédié : tests/unit/test_notification_client.py


# """
# Test de contrat (côté CONSUMER) : contact-service -> notification-service.
# """
# from pathlib import Path
# import pytest

# # Import pour pact-python 1.7.0
# from pact import Consumer, Provider, Term, Like

# from contacts.notification_client import NotificationClient

# PACT_DIR = Path(__file__).resolve().parents[2] / "pacts"

# CONSUMER_NAME = "contact-service"
# PROVIDER_NAME = "notification-service"


# @pytest.fixture()
# def pact() -> Consumer:
#     """Fournit un Pact réutilisable."""
#     pact = Consumer(CONSUMER_NAME).has_pact_with(Provider(PROVIDER_NAME))
#     return pact


# def test_notify_contact_created_success() -> None:
#     """Cas nominal : le notification-service accepte la notification et répond 200."""
    

#     pact = Consumer(CONSUMER_NAME).has_pact_with(
#         Provider(PROVIDER_NAME),
#         pact_dir=str(PACT_DIR),  # ✅ Spécifier le dossier directement
#         port=5555  # ✅ Spécifier le port directement
#     )
    
#     # Définition de l'interaction
#     (pact
#      .given("le notification-service est disponible")
#      .upon_receiving("Une notification de création de contact")
#      .with_request(
#          method="POST",
#          path="/notify/",
#          headers={"Content-Type": "application/json"},
#          body={
#              "contact_id": Term(
#                  generate=1,
#                  matcher="^[0-9]+$"
#              ),
#              "contact_name": Term(
#                  generate="Marie Curie",
#                  matcher="^[a-zA-Z ]+$"
#              )
#          }
#      )
#      .will_respond_with(
#          status=200,
#          headers={"Content-Type": "application/json"},
#          body={
#              "message": Like("Notification envoyée avec succès")
#          }
#      )
#     )
    
#     # ✅ Méthode correcte pour v1.7.0
#     with pact:
#         client = NotificationClient(base_url=pact.uri)
#         result = client.notify_contact_created(contact_id=1, contact_name="Marie Curie")
#         assert result["message"] == "Notification envoyée avec succès"


# def test_notify_contact_created_with_email() -> None:
#     """Cas nominal : notification avec email du contact."""
    
#     pact = Consumer(CONSUMER_NAME).has_pact_with(
#         Provider(PROVIDER_NAME),
#         pact_dir=str(PACT_DIR)
#     )
    
#     (pact
#      .given("le notification-service est disponible")
#      .upon_receiving("Une notification de création de contact avec email")
#      .with_request(
#          method="POST",
#          path="/notify/",
#          headers={"Content-Type": "application/json"},
#          body={
#              "contact_id": Term(generate=2, matcher="^[0-9]+$"),
#              "contact_name": Term(generate="Paul Dupont", matcher="^[a-zA-Z ]+$"),
#              "email": Term(generate="paul@mail.com", matcher="^[a-zA-Z0-9@.]+$")
#          }
#      )
#      .will_respond_with(
#          status=200,
#          headers={"Content-Type": "application/json"},
#          body={
#              "message": Like("Notification envoyée avec succès")
#          }
#      )
#     )
    
#     # ✅ Méthode correcte pour v1.7.0
#     with pact:
#         client = NotificationClient(base_url=pact.uri)
#         result = client.notify_contact_created(
#             contact_id=2, 
#             contact_name="Paul Dupont",
#             email="paul@mail.com"
#         )
#         assert result["message"] == "Notification envoyée avec succès"