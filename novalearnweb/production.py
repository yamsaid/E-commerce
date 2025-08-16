"""
Production settings for novalearnweb project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
print(f"SECRET_KEY from env: {'SET' if SECRET_KEY else 'NOT SET'}")

if not SECRET_KEY or SECRET_KEY.strip() == '':
    print("WARNING: SECRET_KEY not set or empty, using fallback")
    import secrets
    SECRET_KEY = secrets.token_urlsafe(50)
    print(f"Generated fallback SECRET_KEY: {SECRET_KEY[:20]}...")

# Ensure SECRET_KEY is not empty
if not SECRET_KEY or SECRET_KEY.strip() == '':
    raise ValueError("SECRET_KEY cannot be empty in production")

print(f"Final SECRET_KEY length: {len(SECRET_KEY)}")

# Configure allowed hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '.onrender.com').split(',')
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'social_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'novalearnweb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'novalearnweb.wsgi.application'

# Database configuration for Render
DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DATABASE_URL present: {bool(DATABASE_URL)}")

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
        print(f"Database host: {DATABASES['default'].get('HOST', 'N/A')}")
    except ImportError as e:
        print(f"psycopg not available: {e}")
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
            print(f"Database host: {DATABASES['default'].get('HOST', 'N/A')}")
        except ImportError as e:
            print(f"psycopg2 not available: {e}")
            print("Falling back to SQLite")
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
    except Exception as e:
        print(f"Error parsing DATABASE_URL: {e}")
        print("Falling back to SQLite")
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

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication backends
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Login/Logout redirects
LOGIN_URL = 'store:login'
LOGIN_REDIRECT_URL = 'store:home'
LOGOUT_REDIRECT_URL = 'store:home'

# Social Auth settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_OAUTH2_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']

SOCIAL_AUTH_FACEBOOK_KEY = os.getenv('FACEBOOK_APP_ID', 'YOUR_FACEBOOK_APP_ID')
SOCIAL_AUTH_FACEBOOK_SECRET = os.getenv('FACEBOOK_APP_SECRET', 'YOUR_FACEBOOK_APP_SECRET')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, email, first_name, last_name'
}

# Redirections en cas d'erreur OAuth
SOCIAL_AUTH_LOGIN_ERROR_URL = '/login/'
SOCIAL_AUTH_RAISE_EXCEPTIONS = False

# Configuration générale
SITE_URL = os.getenv('SITE_URL', 'https://your-app.onrender.com')

# Timeout pour les API de paiement (en secondes)
PAYMENT_API_TIMEOUT = 30

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
X_FRAME_OPTIONS = 'DENY'

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'store.services': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuration CinetPay
CINETPAY_API_URL = os.getenv('CINETPAY_API_URL', 'https://api-checkout.cinetpay.com/v2/payment')
CINETPAY_SITE_ID = os.getenv('CINETPAY_SITE_ID', '')
CINETPAY_API_KEY = os.getenv('CINETPAY_API_KEY', '')
CINETPAY_ENVIRONMENT = os.getenv('CINETPAY_ENVIRONMENT', 'PROD')
CINETPAY_SECRET_KEY = os.getenv('CINETPAY_SECRET_KEY', '')

print("Using production settings")
print(f"SECRET_KEY length: {len(SECRET_KEY)}")
print(f"Database engine: {DATABASES['default']['ENGINE']}")
