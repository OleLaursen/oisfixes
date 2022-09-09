import os

DEBUG = True

MANAGERS = ADMINS = []

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(BASE_DIR, 'test.db'), # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Define this in local_settings.py
SECRET_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

TIME_ZONE = 'Europe/Copenhagen'
LANGUAGE_CODE = 'da-dk'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'utils.modtimeurls.ModTimeUrlsMiddleware',
]

ROOT_URLCONF = 'urls'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'django/contrib/admin/templates')],
        "OPTIONS": {
            "context_processors": [
                'django.template.context_processors.static',
                'django.template.context_processors.request',
            ],
            #"string_if_invalid": "0xdeadbeef",
        }
    }
]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'osm',
    'oisfixes',
]

SESSION_COOKIE_AGE = 6 * 30 * 24 * 60 * 60

# OSM_OAUTH_KEY and OSM_OAUTH_SECRET and SECRET_KEY should be defined
# in local_settings.py which should not be committed.

try:
    from .local_settings import *
except ImportError:
    pass
