# NovaLearn Web

Application web Django pour la vente de produits numériques et de formations.

## Installation et démarrage

### Prérequis
- Python 3.8 ou supérieur
- pip

### Installation

1. Cloner le projet
```bash
git clone <url-du-repo>
cd novalearnweb
```

2. Créer un environnement virtuel
```bash
python -m venv novenv
```

3. Activer l'environnement virtuel
```bash
# Windows
novenv\Scripts\activate

# Linux/Mac
source novenv/bin/activate
```

4. Installer les dépendances
```bash
pip install -r requirements.txt
```

5. Effectuer les migrations
```bash
python manage.py migrate
```

6. Créer un superutilisateur (optionnel)
```bash
python manage.py createsuperuser
```

### Démarrage du serveur

```bash
python manage.py runserver
```

L'application sera accessible à l'adresse : http://127.0.0.1:8000

## Configuration

Le projet est configuré pour fonctionner en local avec :
- Base de données SQLite
- Mode DEBUG activé
- Fichiers statiques servis par Django
- Authentification sociale (Google, Facebook) - à configurer

## Structure du projet

- `novalearnweb/` - Configuration principale Django
- `store/` - Application principale pour la boutique
- `static/` - Fichiers statiques (CSS, JS, images)
- `media/` - Fichiers uploadés par les utilisateurs
- `logs/` - Fichiers de logs

## Fonctionnalités

- Gestion des produits numériques
- Système de panier et commandes
- Authentification utilisateur
- Authentification sociale (Google, Facebook)
- Système de paiement CinetPay
- Gestion des téléchargements
- Interface d'administration
