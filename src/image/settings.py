"""Django settings for image project.

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
from pathlib import Path
from urllib.parse import urlparse

import environ
import requests
from drf_spectacular.utils import OpenApiParameter

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_NAME = '.'.join(__name__.split('.')[:-1])

env = environ.Env()
env.read_env(BASE_DIR / '..' / '.env')

try:
    from .secret_key import SECRET_KEY
except ImportError:
    from django.core.management.utils import get_random_secret_key

    secret_key_path = BASE_DIR / PROJECT_NAME / 'secret_key.py'
    with secret_key_path.open(mode='w+') as f:
        SECRET_KEY = get_random_secret_key()
        f.write(f"SECRET_KEY = '{SECRET_KEY}'\n")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DEBUG = env.bool('DEBUG', default=False)

# Detect if executed under test
TESTING = any(
    test in sys.argv
    for test in (
        'test',
        'csslint',
        'jenkins',
        'jslint',
        'jtest',
        'lettuce',
        'pep8',
        'pyflakes',
        'pylint',
        'sloccount',
    )
)

DOCKER = env.bool('DOCKER', default=True)

SITE_URL = env.str('SITE_URL')

# Https settings
if SITE_URL.startswith('https'):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000


FORCE_SCRIPT_NAME = env.str('FORCE_SCRIPT_NAME', default='/image')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[urlparse(SITE_URL).hostname])

BEHIND_PROXY = env.bool('BEHIND_PROXY', default=True)

DJANGO_ADMIN_PATH = env.str('DJANGO_ADMIN_PATH', default='editing')

DJANGO_ADMIN_TITLE = _('Image Admin')

ADMINS = getaddresses(
    [env('DJANGO_ADMINS', default='Philipp Mayer <philipp.mayer@uni-ak.ac.at>')],
)

MANAGERS = ADMINS

# Application definition

INSTALLED_APPS = [
    # dal hast to be loaded before django.contrib.admin
    'dal',
    'dal_select2',
    # Django main components
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    # base common apps
    'base_common',
    'base_common_drf',
    # Third-party apps
    'rest_framework',
    'versatileimagefield',
    'django_cleanup',
    'django_cas_ng',
    'mptt',
    'massadmin',
    'ordered_model',
    'corsheaders',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'django_jsonform',
    'tinymce',
    # Project apps
    'accounts',
    'core',
    'artworks',
    'api',
    'texts',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
]

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = reverse_lazy('cas_ng_login')
LOGOUT_URL = reverse_lazy('cas_ng_logout')

CAS_SERVER_URL = env.str('CAS_SERVER', default=f'{SITE_URL}cas/')
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
"""Email settings."""
SERVER_EMAIL = f'error@{urlparse(SITE_URL).hostname}'

EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
EMAIL_HOST = env.str('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_LOCALTIME = env.bool('EMAIL_USE_LOCALTIME', default=True)

EMAIL_SUBJECT_PREFIX = '{} '.format(
    env.str('EMAIL_SUBJECT_PREFIX', default='[Image]').strip(),
)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = BASE_DIR / '..' / 'tmp' / 'emails'

    if not EMAIL_FILE_PATH.exists():
        EMAIL_FILE_PATH.mkdir(parents=True)

""" Https settings """
if SITE_URL.startswith('https'):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000

X_FRAME_OPTIONS = 'DENY'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if BEHIND_PROXY:
    MIDDLEWARE += [
        'base_common.middleware.SetRemoteAddrFromForwardedFor',
    ]
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = f'{PROJECT_NAME}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'base_common.context_processors.global_settings',
            ],
            'debug': DEBUG,
            'string_if_invalid': "[invalid variable '%s'!]" if DEBUG else '',
        },
    },
]

CONTEXT_SETTINGS = (
    'DEBUG',
    'BASE_HEADER',
    'FORCE_SCRIPT_NAME',
    'DJANGO_ADMIN_TITLE',
)

WSGI_APPLICATION = f'{PROJECT_NAME}.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('POSTGRES_DB', default=f'django_{PROJECT_NAME}'),
        'USER': env.str('POSTGRES_USER', default=f'django_{PROJECT_NAME}'),
        'PASSWORD': env.str('POSTGRES_PASSWORD', default=f'password_{PROJECT_NAME}'),
        'HOST': f'{PROJECT_NAME}-postgres' if DOCKER else 'localhost',
        'PORT': env.str('POSTGRES_PORT', default='5432'),
    },
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

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Europe/Vienna'
USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ('de', _('German')),
    ('en', _('English')),
)

LANGUAGES_DICT = dict(LANGUAGES)

LOCALE_PATHS = (BASE_DIR / 'locale',)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

STATICFILES_DIRS = (BASE_DIR / 'static',)

STATIC_URL = '{}/static/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
STATIC_ROOT = '{}{}'.format(
    os.path.normpath(BASE_DIR / 'assets' / 'static'),
    os.sep,
)

MEDIA_URL = '{}/media/'.format(FORCE_SCRIPT_NAME if FORCE_SCRIPT_NAME else '')
MEDIA_ROOT = '{}{}'.format(
    os.path.normpath(BASE_DIR / 'assets' / 'media'),
    os.sep,
)
MEDIA_ROOT_PATH = Path(MEDIA_ROOT)

# config of versatileimagefield
# used to edit artworks
VERSATILEIMAGEFIELD_SETTINGS = {
    # The amount of time, in seconds, that references to created images
    # should be stored in the cache. Defaults to `2592000` (30 days)
    'cache_length': 2592000,
    # The save quality of modified JPEG images. More info here:
    # https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#jpeg
    'jpeg_resize_quality': 92,
    # Whether or not to create new images on-the-fly. Set this to `False` for
    # speedy performance but don't forget to 'pre-warm' to ensure they're
    # created and available at the appropriate URL.
    'create_images_on_demand': True,
    # Whether to create progressive JPEGs. Read more about progressive JPEGs
    # here: https://optimus.io/support/progressive-jpeg/
    'progressive_jpeg': False,
}
"""Logging."""
LOG_DIR = BASE_DIR / '..' / 'logs'

if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
        },
        'simple': {'format': '%(levelname)s %(message)s'},
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentTimedRotatingFileHandler',
            'filename': LOG_DIR / 'application.log',
            'when': 'midnight',
            'backupCount': 1000,
            'use_gzip': True,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'stream_to_console': {'level': 'DEBUG', 'class': 'logging.StreamHandler'},
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
    },
}

LOG_DB_BACKEND = env.bool('LOG_DB_BACKEND', default=False)

if LOG_DB_BACKEND:
    LOGGING['loggers']['django.db.backends'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }

"""Cache settings."""
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{}:{}/0'.format(
            f'{PROJECT_NAME}-redis' if DOCKER else 'localhost',
            env.int('REDIS_PORT', default=6379),
        ),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{}:{}/1'.format(
            f'{PROJECT_NAME}-redis' if DOCKER else 'localhost',
            env.int('REDIS_PORT', default=6379),
        ),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    },
}
"""Session settings."""
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_NAME = 'sessionid_{}'.format('image')
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_NAME = 'csrftoken_{}'.format('image')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=False)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_EXPOSE_HEADERS = env.list('CORS_EXPOSE_HEADERS', default=[])

# base Header
BASE_HEADER_SITE_URL = env.str('BASE_HEADER_SITE_URL', SITE_URL)
BASE_HEADER_JSON = f'{BASE_HEADER_SITE_URL}bs/base-header.json'
BASE_HEADER = '{}{}'.format(
    BASE_HEADER_SITE_URL,
    requests.get(BASE_HEADER_JSON, timeout=60).json()['latest'],
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'base_common_drf.authentication.SessionAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': ('rest_framework.parsers.JSONParser',),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'api.permissions.TosAcceptedPermission',
    ),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'DEFAULT_SCHEMA_CLASS': 'base_common_drf.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Image API',
    'DESCRIPTION': '',
    'VERSION': '1.0',
    'SERVERS': [
        {
            'url': env.str(
                'OPENAPI_SERVER_URL',
                default=f'{SITE_URL.rstrip("/")}{FORCE_SCRIPT_NAME}',
            ),
            'description': env.str('OPENAPI_SERVER_DESCRIPTION', default='Image+'),
        },
    ],
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'displayOperationId': True,
    },
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    # OTHER SETTINGS
    # set GLOBAL_PARAMS used in base_common_drf.openapi.AutoSchema
    'GLOBAL_PARAMS': [
        OpenApiParameter(
            name='Accept-Language',
            type=str,
            location=OpenApiParameter.HEADER,
            required=False,
            enum=list(LANGUAGES_DICT.keys()),
            default='en',
        ),
    ],
}

PERMISSIONS = (
    'VIEW',
    'EDIT',
)

DEFAULT_PERMISSIONS = env.list('DEFAULT_PERMISSIONS', default=['VIEW'])

for permission in DEFAULT_PERMISSIONS:
    if permission not in PERMISSIONS:
        raise ImproperlyConfigured(
            f'Permission {repr(permission)} not allowed in DEFAULT_PERMISSIONS',
        )

SEARCH_LIMIT = 30

LOCATION_SEARCH_LEVELS = env.int('LOCATION_SEARCH_LEVELS', default=1)

# Sentry
SENTRY_DSN = env.str('SENTRY_DSN', default=None)
SENTRY_ENVIRONMENT = env.str(
    'SENTRY_ENVIRONMENT',
    default='development'
    if any(i in SITE_URL for i in ['dev', 'localhost', '127.0.0.1'])
    else 'production',
)
SENTRY_TRACES_SAMPLE_RATE = env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.2)
SENTRY_PROFILES_SAMPLE_RATE = env.float('SENTRY_PROFILES_SAMPLE_RATE', default=0.2)

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=True,
    )

GND_API_BASE_URL = env.str('GND_API_BASE_URL', default='https://lobid.org/gnd/')
GND_ID_REGEX = r'^(1[0123]?\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X])$'
GND_DATE_REGEX = r'^-?[0-9]{1,4}-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])$'
GND_LABEL = 'GND'

GETTY_ID_REGEX = r'^http:\/\/vocab\.getty\.edu\/aat\/[0-9]+$'
GETTY_LABEL = 'Getty AAT'

WIKIDATA_LABEL = 'Wikidata'

REQUESTS_TIMEOUT = env.int('REQUESTS_TIMEOUT', default=5)

GOTENBERG_SERVER_NAME = f'{PROJECT_NAME}-gotenberg' if DOCKER else 'localhost'
GOTENBERG_API_URL = env.str(
    'GOTENBERG_API_URL',
    default=f'http://{GOTENBERG_SERVER_NAME}:3000/forms/libreoffice/convert',
)

TINYMCE_DEFAULT_CONFIG = {
    'theme': 'silver',
    'height': 500,
    'menubar': False,
    'plugins': 'autolink,lists,link,paste,wordcount',
    'toolbar': 'undo redo | styles | bold italic link | alignleft aligncenter alignright alignjustify | bullist numlist',
    'style_formats': [
        {'title': 'Heading', 'block': 'h2'},
        {'title': 'Paragraph', 'block': 'p'},
    ],
    'paste_block_drop': True,
    'paste_as_text': True,
    'entity_encoding': 'raw',
}
