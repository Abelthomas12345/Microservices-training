"""
Tests unitaires du NotificationClient.

Ces tests complètent le test de contrat Pact (tests/pact/) : ils vérifient
la résilience du client (gestion des erreurs réseau, timeout, statuts HTTP
d'erreur, réponse non-JSON) sans dépendre d'un serveur réel ni du contrat
Pact, en mockant la couche HTTP avec `requests_mock`.
"""
import pytest
import requests
import requests_mock

from contacts.notification_client import NotificationClient, NotificationServiceError


@pytest.fixture()
def client() -> NotificationClient:
    return NotificationClient(base_url="http://notification-service.test")


def test_notify_contact_created_success(client: NotificationClient) -> None:
    with requests_mock.Mocker() as m:
        m.post(
            "http://notification-service.test/notify/",
            json={"message": "Notification envoyée avec succès"},
            status_code=200,
        )
        result = client.notify_contact_created(contact_id=1, contact_name="Marie Curie")

    assert result == {"message": "Notification envoyée avec succès"}


def test_notify_contact_created_sends_expected_payload(client: NotificationClient) -> None:
    with requests_mock.Mocker() as m:
        m.post(
            "http://notification-service.test/notify/",
            json={"message": "ok"},
            status_code=200,
        )
        client.notify_contact_created(contact_id=42, contact_name="Ada Lovelace")

        assert m.last_request.json() == {"contact_id": 42, "contact_name": "Ada Lovelace"}


def test_notify_contact_created_raises_on_server_error(client: NotificationClient) -> None:
    with requests_mock.Mocker() as m:
        m.post(
            "http://notification-service.test/notify/",
            status_code=500,
            json={"detail": "internal error"},
        )
        with pytest.raises(NotificationServiceError):
            client.notify_contact_created(contact_id=1, contact_name="Marie Curie")


def test_notify_contact_created_raises_on_connection_error(client: NotificationClient) -> None:
    with requests_mock.Mocker() as m:
        m.post(
            "http://notification-service.test/notify/",
            exc=requests.exceptions.ConnectionError,
        )
        with pytest.raises(NotificationServiceError):
            client.notify_contact_created(contact_id=1, contact_name="Marie Curie")


def test_notify_contact_created_raises_on_timeout(client: NotificationClient) -> None:
    with requests_mock.Mocker() as m:
        m.post(
            "http://notification-service.test/notify/",
            exc=requests.exceptions.Timeout,
        )
        with pytest.raises(NotificationServiceError):
            client.notify_contact_created(contact_id=1, contact_name="Marie Curie")


def test_notify_contact_created_raises_on_invalid_json(client: NotificationClient) -> None:
    with requests_mock.Mocker() as m:
        m.post(
            "http://notification-service.test/notify/",
            status_code=200,
            text="not-json",
        )
        with pytest.raises(NotificationServiceError):
            client.notify_contact_created(contact_id=1, contact_name="Marie Curie")
