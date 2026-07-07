
# Microservices - Gestionnaire de Contacts

## Présentation du projet

Ce projet est un système de microservices développé dans le cadre du Sprint S2 de la formation Dev Backend (Django REST) – Master 1.
Il implémente une architecture orientée microservices avec une API Gateway, trois services autonomes, et une communication inter-services en HTTP.

L’objectif pédagogique est de maîtriser la conteneurisation avec Docker, l’orchestration avec Docker Compose, et la communication entre services dans une architecture distribuée.

---

🏗️ Architecture

```text
                Client (Postman / Navigateur)
                          │
                          ▼
                     API Gateway
                    (Port 8000)
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
  User Service      Contact Service     Notification Service
    (8001)             (8002)              (8003)
       │                  │                  │
       │                  └──────────────►   │
       │               Appel HTTP POST       │
       │               /notify/              │
       │                                     │
       └─────────────────────────────────────┘
```

---

📦 Services

Service | Rôle | Port interne | Port local (debug)
---|---:|---:|---:
User Service | Gestion des utilisateurs (CRUD) | 8000 | 8001
Contact Service | Gestion des contacts + déclenchement des notifications | 8000 | 8002
Notification Service | Réception des notifications (logging) | 8000 | 8003
API Gateway | Point d’entrée unique, routage vers les services | 8000 | 8000

---

🚀 Prérequis

· Python 3.12 ou supérieur
· pip (gestionnaire de paquets Python)
· Docker et Docker Compose (optionnel)
· curl ou Postman pour les tests

---

⚙️ Installation et exécution en local (sans Docker)

1. Cloner le dépôt

```bash
git clone https://github.com/<votre-utilisateur>/microservices-training.git
cd microservices-training
```

2. Installer les dépendances de chaque service

```bash
cd api-gateway && pip install -r requirements.txt
cd ../user-service && pip install -r requirements.txt
cd ../contact-service && pip install -r requirements.txt
cd ../notification-service && pip install -r requirements.txt
```

3. Appliquer les migrations (pour les services avec base de données)

```bash
cd user-service
py manage.py makemigrations
py manage.py migrate

cd ../contact-service
py manage.py makemigrations
py manage.py migrate
```

4. Lancer les services (4 terminaux distincts)

Terminal 1 – User Service

```bash
cd user-service
py manage.py runserver 8001
```

Terminal 2 – Notification Service

```bash
cd notification-service
py manage.py runserver 8003
```

Terminal 3 – Contact Service

```bash
cd contact-service
set NOTIFICATION_SERVICE_URL=http://localhost:8003   # Windows CMD
# ou
$env:NOTIFICATION_SERVICE_URL="http://localhost:8003"   # PowerShell

```

Terminal 4 – API Gateway

```bash
cd api-gateway
set USERS_SERVICE_URL=http://localhost:8001
set CONTACT_SERVICE_URL=http://localhost:8002
set NOTIFICATION_SERVICE_URL=http://localhost:8003
py manage.py runserver 8000
```

---

🐳 Installation et exécution avec Docker

1. Construire et lancer tous les services

```bash
docker-compose up --build
```

2. Arrêter les services

```bash
docker-compose down
```

3. Voir les logs d’un service spécifique

```bash
docker-compose logs -f notification-service
```

---

🔌 Endpoints de l’API (via Gateway)

Tous les endpoints sont accessibles sur http://localhost:8000.

User Service

Méthode | URL | Description
---:|:---|:---
GET | /users/ | Liste de tous les utilisateurs
POST | /users/ | Créer un utilisateur
GET | /users/<id>/ | Détail d’un utilisateur

Contact Service

Méthode | URL | Description
---:|:---|:---
GET | /contacts/ | Liste de tous les contacts
POST | /contacts/ | Créer un contact (déclenche une notification)
GET | /contacts/<id>/ | Détail d’un contact
PUT | /contacts/<id>/ | Modifier un contact
DELETE | /contacts/<id>/ | Supprimer un contact

Notification Service

Méthode | URL | Description
---:|:---|:---
POST | /notify/ | Réception d’une notification (appel interne)

---

🧪 Tests de démonstration

1. Créer un utilisateur

```bash
Invoke-RestMethod -Uri "http://localhost:8001/users/" -Method Post -ContentType "application/json" -Body '{"first_name":"Jean","last_name":"Dupont","email":"jean@mail.com"}'
```

Réponse attendue :

```json
{
  "id": 1,
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean@mail.com",
  "created_at": "2026-06-28T..."
}
```

---

2. Créer un contact (déclenche la notification)

```bash
Invoke-RestMethod -Uri "http://localhost:8002/contacts/"  -Method Post -ContentType "application/json" -Body '{"name":"Marie Curie","email":"marie@mail.com","company":"Institut"}'
```

Réponse attendue :

```json
{
  "id": 1,
  "name": "Marie Curie",
  "email": "marie@mail.com",
  "phone": "",
  "company": "Institut",
  "created_at": "2026-06-28T..."
}
```

---

3. Vérifier la notification

Dans le terminal du notification-service, vous devez voir :

```
📧 [NOTIFICATION] Contact 'Marie Curie' (ID: 1) créé.
```

Dans les logs Docker :

```bash
docker-compose logs notification-service
```

---

4. Vérifier la communication inter-services

· Le contact-service appelle notification-service via HTTP sur /notify/.
· Le notification-service répond avec un statut 200 OK.
· Preuve : dans les logs du notification-service, on voit :

```
"POST /notify/ HTTP/1.1" 200 48
```



## Structure du dépôt

```text
microservices-training/
│
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── gateway/
│       ├── views.py
│       ├── urls.py
│       └── tests.py
│
├── user-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   └── users/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── tests.py
│
├── contact-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   └── contacts/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── tests.py
│
├── notification-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   └── notifications/
│       ├── views.py
│       ├── urls.py
│       └── tests.py
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## Technologies utilisées

- Django 5.1.4 – Framework web
- Django REST Framework 3.15.2 – API REST
- SQLite – Base de données légère (pour les tests)
- Requests – Communication HTTP entre services
- Docker – Conteneurisation
- Docker Compose – Orchestration multi-conteneurs

---

🔜 Évolutions prévues (Tickets suivants)

· ✅ Communication asynchrone avec RabbitMQ et Celery (remplacement de l’appel HTTP)
· ✅ Authentification avec JWT
· ✅ Tests d’intégration et de contrat
· ✅ Sécurisation OWASP (rate limiting, validation, etc.)
· ✅ Passage à PostgreSQL pour la production

---

## Auteur

- ABEL – Stagiaire Master 1, Parcours Dev Backend (Django REST)
  Formation : Optimisez votre architecture microservices – OpenClassrooms
  Projet : API REST – Gestionnaire de Contacts

## Variables d'environnement importantes

- USERS_SERVICE_URL (utilisé par API Gateway)
- CONTACT_SERVICE_URL (utilisé par API Gateway)
- NOTIFICATION_SERVICE_URL (utilisé par contact-service et API Gateway)

Exemples (Windows CMD):

```bash
set USERS_SERVICE_URL=http://localhost:8001
set CONTACT_SERVICE_URL=http://localhost:8002
set NOTIFICATION_SERVICE_URL=http://localhost:8003
```

Exemples (PowerShell / bash):

```bash
export USERS_SERVICE_URL="http://localhost:8001"
export CONTACT_SERVICE_URL="http://localhost:8002"
export NOTIFICATION_SERVICE_URL="http://localhost:8003"
```

## Tests

- Chaque service contient un fichier tests.py avec tests unitaires basiques. Lancer depuis la racine du service:

```bash
py manage.py test
```

## Contribution

- Ouvrez une issue pour proposer des évolutions ou signaler un bug.
- Forkez, créez une branche et soumettez une pull request.

## Licence

- MIT (à adapter selon besoin)

---

📚 Références

· Documentation Django
· Django REST Framework
· Docker Documentation
· OpenClassrooms – Microservices

