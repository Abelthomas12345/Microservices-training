"""
Test d'intégration "interne" au contact-service.

Contrairement aux tests de contrat Pact (qui vérifient le FORMAT de
l'échange HTTP) et aux tests unitaires du NotificationClient (qui vérifient
sa résilience), ce test vérifie l'intégration RÉELLE entre les couches du
contact-service :

    requête HTTP entrante -> vue DRF -> ORM (persistance du Contact)
    -> appel sortant au notification-service (HTTP) -> déclenchement Celery

Seul l'appel réseau sortant vers le notification-service est simulé
(avec requests_mock) car ce test se concentre sur le contact-service ;
la véritable communication inter-conteneurs est couverte par la suite
d'intégration inter-services (voir /tests/integration à la racine du
dépôt, à exécuter avec `docker-compose up`).
"""
from unittest.mock import patch

import requests_mock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from contacts.models import Contact


class ContactCreationIntegrationTests(APITestCase):
    """AC2 : exercice pratique fonctionnel (pas seulement théorique)."""

    def setUp(self) -> None:
        self.url = reverse("contact-list-create")
        # La partie Celery/RabbitMQ (ticket 2) est déjà couverte par ses
        # propres tests ; on la neutralise ici pour ne pas dépendre d'un
        # broker RabbitMQ réel dans ce test d'intégration ciblé sur le
        # flux HTTP synchrone contact-service -> notification-service.
        patcher = patch("contacts.views.current_app.send_task")
        self.mock_send_task = patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_contact_persists_and_triggers_notification(self) -> None:
        payload = {
            "name": "Marie Curie",
            "email": "marie@mail.com",
            "company": "Institut",
        }

        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8003/notify/",
                json={"message": "Notification envoyée avec succès"},
                status_code=200,
            )

            response = self.client.post(self.url, payload, format="json")

            # La création du contact a bien réussi et a été persistée
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Contact.objects.count(), 1)
            contact = Contact.objects.first()
            self.assertEqual(contact.name, "Marie Curie")

            # Le notification-service a bien été appelé une fois, avec le
            # bon contact_id et le bon nom
            self.assertEqual(m.call_count, 1)
            sent_body = m.last_request.json()
            self.assertEqual(sent_body["contact_id"], contact.id)
            self.assertEqual(sent_body["contact_name"], "Marie Curie")

    def test_create_contact_succeeds_even_if_notification_service_is_down(self) -> None:
        """La création d'un contact ne doit jamais échouer à cause d'une
        panne du notification-service (le NotificationClient absorbe
        l'erreur, voir contacts/views.py)."""
        payload = {
            "name": "Paul Dupont",
            "email": "paul@mail.com",
        }

        with requests_mock.Mocker() as m:
            m.post("http://localhost:8003/notify/", status_code=500)

            response = self.client.post(self.url, payload, format="json")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Contact.objects.filter(name="Paul Dupont").count(), 1)
