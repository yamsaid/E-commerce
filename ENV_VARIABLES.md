# Variables d'Environnement pour NovaLearn

## Variables Obligatoires

### Django
- `SECRET_KEY` : Clé secrète Django (générée automatiquement par Render)
- `DEBUG` : Mode debug (False en production)
- `ALLOWED_HOSTS` : Domaines autorisés (séparés par des virgules)

### Base de Données PostgreSQL Render
- `DATABASE_URL` : URL de connexion PostgreSQL (à configurer manuellement)
  - Format : `postgresql://username:password@host:port/database_name`
  - Exemple : `postgresql://novalearnweb_user:your_password@dpg-xxxxx-a.frankfurt-postgres.render.com/novalearnweb_db`

## Variables Optionnelles

### CinetPay (Paiements)
- `CINETPAY_SITE_ID` : ID du site CinetPay
- `CINETPAY_API_KEY` : Clé API CinetPay
- `CINETPAY_ENVIRONMENT` : Environnement (TEST ou PROD)
- `CINETPAY_SECRET_KEY` : Clé secrète pour les webhooks

### OAuth (Authentification Sociale)
- `GOOGLE_OAUTH2_CLIENT_ID` : ID client Google OAuth2
- `GOOGLE_OAUTH2_CLIENT_SECRET` : Secret client Google OAuth2
- `FACEBOOK_APP_ID` : ID application Facebook
- `FACEBOOK_APP_SECRET` : Secret application Facebook

### Configuration Générale
- `SITE_URL` : URL complète du site
- `CINETPAY_API_URL` : URL de l'API CinetPay

## Exemple de Configuration

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com,localhost

# CinetPay
CINETPAY_SITE_ID=123456
CINETPAY_API_KEY=your-api-key
CINETPAY_ENVIRONMENT=PROD
CINETPAY_SECRET_KEY=your-secret-key

# OAuth
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret

# Site
SITE_URL=https://your-app.onrender.com
```

## Configuration sur Render

1. Allez dans le dashboard de votre service
2. Cliquez sur "Environment"
3. Ajoutez chaque variable avec sa valeur
4. Redéployez l'application
