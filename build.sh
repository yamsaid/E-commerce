#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Démarrage du processus de build..."

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Vérifier les dépendances PostgreSQL
echo "🔍 Vérification des dépendances PostgreSQL..."
python -c "import psycopg; print('✅ psycopg disponible')" || {
    echo "⚠️  psycopg non disponible, installation..."
    pip install psycopg[binary]
}

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --no-input

# Vérifier la configuration
echo "🔧 Vérification de la configuration..."
python manage.py check --deploy

# Planifier les migrations
echo "🗄️  Planification des migrations..."
python manage.py migrate --plan

echo "✅ Build terminé avec succès!"
