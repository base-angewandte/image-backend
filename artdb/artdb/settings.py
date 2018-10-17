"""
Django settings for artdb project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/

Before deployment please see
https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/
"""

import os
import sys
from email.utils import getaddresses
from urllib.parse import urlparse

import environ
import requests
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

env = environ.Env()
env.read_env()


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_NAME = '.'.join(__name__.split('.')[:-1])

try:
    from .secret_key import SECRET_KEY
except ImportError:
    from django.core.management.utils import get_random_secret_key
    f = open(os.path.join(BASE_DIR, PROJECT_NAME, 'secret_key.py'), 'w+')
    SECRET_KEY = get_random_secret_key()
    f.write("SECRET_KEY = '%s'\n" % SECRET_KEY)
    f.close()

DEBUG = env.bool('DEBUG', default=False)

# Detect if executed under test
TESTING = any(test in sys.argv for test in (
    'test', 'csslint', 'jenkins', 'jslint',
    'jtest', 'lettuce', 'pep8', 'pyflakes',
    'pylint', 'sloccount',
))

DOCKER = env.bool('DOCKER', default=True)

SITE_URL = env.str('SITE_URL')

FORCE_SCRIPT_NAME = env.str('FORCE_SCRIPT_NAME', default='/image')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[urlparse(SITE_URL).hostname])

BEHIND_PROXY = env.bool('BEHIND_PROXY', default=True)

ADMINS = getaddresses([env('DJANGO_ADMINS', default='Philipp Mayer <philipp.mayer@uni-ak.ac.at>')])

MANAGERS = ADMINS

# Application definition

INSTALLED_APPS = [
    # need to be before django.contrib.admin and grapelli
    'dal',
    'dal_select2',


    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    #'debug_toolbar',
    'rest_framework',
    'versatileimagefield',
    'django_cleanup',
    'django_cas_ng',
    'mptt',

    # Project apps
    'general',
    'artworkusers',
    'artworks',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
]

LOGIN_URL = reverse_lazy('cas_ng_login')
LOGOUT_URL = reverse_lazy('cas_ng_logout')

CAS_SERVER_URL = env.str('CAS_SERVER', default='{}cas/'.format(SITE_URL))
CAS_LOGIN_MSG = None
CAS_LOGGED_MSG = None
CAS_RENEW = False
CAS_LOGOUT_COMPLETELY = True
CAS_RETRY_LOGIN = True
CAS_VERSION = '3'
CAS_APPLY_ATTRIBUTES_TO_USER = True
CAS_RENAME_ATTRIBUTES = {
    'firstName': 'first_name',
    'lastName': 'last_name',
    'email0': 'email',
}

""" Email settings """
EMAIL_SUBJECT_PREFIX = '{} '.format(env.str('EMAIL_SUBJECT_PREFIX', default='[Image]').strip())
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, '..', 'tmp', 'emails')

    if not os.path.exists(EMAIL_FILE_PATH):
        os.makedirs(EMAIL_FILE_PATH)

""" Https settings """
if SITE_URL.startswith('https'):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000


X_FRAME_OPTIONS = 'DENY'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    # insert before SessionMiddleware
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.contrib.sessions.middleware.SessionMiddleware'),
        'debug_toolbar.middleware.DebugToolbarMiddleware'
    )

    # for django debug toolbar
    INTERNAL_IPS = ('127.0.0.1')
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda r: False,  # disables it
    }

if BEHIND_PROXY:
    MIDDLEWARE += ['general.middleware.SetRemoteAddrFromForwardedFor', ]
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


ROOT_URLCONF = '{}.urls'.format(PROJECT_NAME)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'artdb', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
            'string_if_invalid': "[invalid variable '%s'!]" if DEBUG else "",
        },
    },
]

WSGI_APPLICATION = '{}.wsgi.application'.format(PROJECT_NAME)


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB', 'django_{}'.format(PROJECT_NAME)),
        'USER': os.environ.get('POSTGRES_USER', 'django_{}'.format(PROJECT_NAME)),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'password_{}'.format(PROJECT_NAME)),
        'HOST': '{}-postgres'.format(PROJECT_NAME) if DOCKER else 'localhost',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'de-at'
TIME_ZONE = 'Europe/Vienna'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = (
    ('de', _('German')),
    ('en', _('English')),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATICFILES_DIRS = (
    # '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'static')), os.sep),
    os.path.join(BASE_DIR, 'artdb/static_dev'),
)
STATIC_URL = '{}/static/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
STATIC_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'static')), os.sep)

MEDIA_URL = '{}/media/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
MEDIA_ROOT = '{}{}'.format(os.path.normpath(os.path.join(BASE_DIR, 'assets', 'media')), os.sep)


# config of versatileimagefield
# used to edit artworks
VERSATILEIMAGEFIELD_SETTINGS = {
    # The amount of time, in seconds, that references to created images
    # should be stored in the cache. Defaults to `2592000` (30 days)
    'cache_length': 2592000,
    # The save quality of modified JPEG images. More info here:
    # https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#jpeg
    'jpeg_resize_quality': 82,
    # Whether or not to create new images on-the-fly. Set this to `False` for
    # speedy performance but don't forget to 'pre-warm' to ensure they're
    # created and available at the appropriate URL.
    'create_images_on_demand': True,
    # Whether to create progressive JPEGs. Read more about progressive JPEGs
    # here: https://optimus.io/support/progressive-jpeg/
    'progressive_jpeg': False
}

""" Logging """
LOG_DIR = os.path.join(BASE_DIR, '..', 'logs')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'application.log'),
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 100,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'stream_to_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': True,
            'level': 'INFO',
        },
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

""" Cache settings """
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{}:6379/0'.format('{}-redis'.format(PROJECT_NAME) if DOCKER else 'localhost'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

""" Session settings """
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_NAME = 'sessionid_{}'.format(PROJECT_NAME)

CSRF_COOKIE_NAME = 'csrftoken_{}'.format(PROJECT_NAME)

# base Header
BASE_HEADER_SITE_URL = env.str('BASE_HEADER_SITE_URL', SITE_URL)
BASE_HEADER_JSON = '{}bs/base-header.json'.format(BASE_HEADER_SITE_URL)
BASE_HEADER = '{}{}'.format(BASE_HEADER_SITE_URL, requests.get(BASE_HEADER_JSON).json()['latest'])
