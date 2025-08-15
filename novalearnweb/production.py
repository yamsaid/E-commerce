"""
Production settings for novalearnweb project.
"""

from .settings import *
import os
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Configure allowed hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '.onrender.com').split(',')

# Database configuration for Render
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    try:
        # Try to use psycopg (newer PostgreSQL adapter)
        import psycopg
        DATABASES = {
            'default': dj_database_url.parse(DATABASE_URL)
        }
        # Use psycopg engine
        if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
        print("Using PostgreSQL with psycopg")
    except ImportError:
        try:
            # Fallback to psycopg2
            import psycopg2
            DATABASES = {
                'default': dj_database_url.parse(DATABASE_URL)
            }
            # Use psycopg2 engine
            if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
                DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
            print("Using PostgreSQL with psycopg2")
        except ImportError:
            print("Neither psycopg nor psycopg2 available, falling back to SQLite")
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
else:
    print("No DATABASE_URL found, using SQLite")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files configuration
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
