#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip

# Install main requirements
pip install -r requirements.txt

# Ensure psycopg is available for PostgreSQL
echo "Verifying PostgreSQL dependencies..."
python -c "import psycopg; print('✓ psycopg is available')" || {
    echo "Installing psycopg as fallback..."
    pip install psycopg[binary]
}

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running database migrations..."
python manage.py migrate

echo "Build completed successfully!"
