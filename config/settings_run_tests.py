"""
Django settings for `run_tests.py`.

TODO: experiment with a `from .settings import *` approach
"""

import logging
import pathlib

## load envars ------------------------------------------------------
# dotenv_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
# load_dotenv(find_dotenv(str(dotenv_path)), override=True)

log = logging.getLogger(__name__)


## django PROJECT settings ------------------------------------------

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
# log.debug( f'BASE_DIR, ``{BASE_DIR}``' )


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-3ory+ty87_wq8-21ki6d&a+x=z9_$2m(gr4@vxri@@^g7u!*oc'
SECRET_KEY = 'abcd'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ADMINS = []

ALLOWED_HOSTS = []
CSRF_TRUSTED_ORIGINS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bdr_uploader_hub_app.apps.BdrUploaderHubAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [f'{BASE_DIR}/bdr_uploader_hub_app/bdr_uploader_hub_app_templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'local_data.db',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'  ## the default
TIME_ZONE = 'America/New_York'

USE_I18N = True

# USE_TZ = True  ## the default
USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/'  # needed for collectstatic command

# Email
SERVER_EMAIL = 'example@domain.edu'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

## user uploaded files ----------------------------------------------
MEDIA_ROOT = '/tmp/'
BDR_API_FILE_PATH_ROOT = '/tmp/'
"""
The two settings below prevent django from auto-running chmod on uploaded files
    (which can cause permission issues when using a shared volume)
    see: https://docs.djangoproject.com/en/4.2/ref/settings/#file-upload-permissions
"""
FILE_UPLOAD_PERMISSIONS = None
FILE_UPLOAD_DIRECTORY_PERMISSIONS = None

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

## reminder:
## "Each 'logger' will pass messages above its log-level to its associated 'handlers',
## ...which will then output messages above the handler's own log-level."
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        },
    },
    'handlers': {
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'include_html': True,
        # },
        # 'logfile': {
        #     'level': os.environ.get('LOG_LEVEL', 'INFO'),  # add LOG_LEVEL=DEBUG to the .env file to see debug messages
        #     'class': 'logging.FileHandler',  # note: configure server to use system's log-rotate to avoid permissions issues
        #     'filename': os.environ['LOG_PATH'],
        #     'formatter': 'standard',
        # },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'bdr_uploader_hub_app': {
            'handlers': ['console'],
            'level': 'DEBUG',  # messages above this will get sent to the `logfile` handler
            'propagate': False,
        },
        # 'django.db.backends': {  # re-enable to check sql-queries! <https://docs.djangoproject.com/en/4.2/ref/logging/#django-db-backends>
        #     'handlers': ['logfile'],
        #     'level': os.environ['LOG_LEVEL'],
        #     'propagate': False
        # },
    },
}

## cache settings ---------------------------------------------------
# CACHES: dict = {}  ## raises SystemCheckError: "(caches.E001) You must define a 'default' cache in your CACHES setting.
CACHES: dict = {'default': {}}

LOGIN_URL = '/foo/'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
# TEST_RUNNER = 'test_runner.JSONTestRunner'


## django APP settings ----------------------------------------------

TEST_SHIB_META_DCT: dict = {}

SHIB_SP_LOGIN_URL: str = 'http://localhost:8000/shib_login/'
SHIB_IDP_LOGOUT_URL: str = 'http://localhost:8000/shib_logout/'

## creates, eg: [('all_rights_reserved', 'All Rights Reserved'), ('CC_BY', 'Attribution (CC BY)'), etc.]
ALL_LICENSE_OPTIONS: list[tuple[str, str]] = []

## creates, eg: [('public', 'Public'), ('private', 'Private'), etc.]
ALL_VISIBILITY_OPTIONS: list[tuple[str, str]] = []

## used for pid<-->collection-name validation
BDR_PUBLIC_API_COLLECTION_ROOT_URL: str = 'http://localhost:8000/api/collections/'
TEST_COLLECTION_PID_FOR_FORM_VALIDATION: str = 'test:123'
TEST_COLLECTION_TITLE_FOR_FORM_VALIDATION: str = 'Test Collection'

## used for rightsMetadata xml file
BDR_MANAGER_GROUP: str = 'manager_group'
BDR_BROWN_GROUP: str = 'brown_group'
BDR_PUBLIC_GROUP: str = 'public_group'

## used for bdr-post
BDR_PRIVATE_API_ROOT_URL: str = 'http://localhost:8000/api/private/items/'

## used for ingest confirmation-email to student
BDR_PUBLIC_STUDIO_ITEM_ROOT_URL: str = 'http://localhost:8000/studio/items/'

## for mount check on version-url call
MOUNT_POINT: str = 'FOO'
