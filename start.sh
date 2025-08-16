#!/usr/bin/env bash

# Script de démarrage pour Render
# Configure Gunicorn avec les bonnes options pour éviter l'erreur 502

echo "🚀 Démarrage de l'application Django sur Render..."

# Variables d'environnement Render
PORT=${PORT:-10000}
HOST=${HOST:-0.0.0.0}

echo "📍 Port: $PORT"
echo "🌐 Host: $HOST"
echo "🔧 Workers: 2"
echo "⏱️  Timeout: 120s"

# Diagnostic des variables d'environnement
echo "🔍 Diagnostic des variables d'environnement..."
echo "SECRET_KEY: ${SECRET_KEY:+SET (length: ${#SECRET_KEY})}"
echo "DATABASE_URL: ${DATABASE_URL:+SET}"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-NOT SET}"
echo "DEBUG: ${DEBUG:-NOT SET}"

# Vérifier SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  WARNING: SECRET_KEY not set, Django will generate one"
fi

# Collecter les fichiers statiques si nécessaire
if [ ! -d "staticfiles" ]; then
    echo "📁 Collecte des fichiers statiques..."
    python manage.py collectstatic --no-input
fi

# Exécuter les migrations
echo "🗄️  Exécution des migrations..."
python manage.py migrate --no-input

# Démarrer Gunicorn avec les bonnes options
echo "🚀 Démarrage de Gunicorn..."
exec gunicorn novalearnweb.wsgi:application \
    --bind $HOST:$PORT \
    --workers 2 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
