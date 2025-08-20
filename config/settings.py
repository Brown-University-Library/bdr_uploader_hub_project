"""
Django settings for bdr_uploader_hub_project.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import json
import logging
import os
import pathlib

from dotenv import find_dotenv, load_dotenv

## load envars ------------------------------------------------------
dotenv_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
assert dotenv_path.exists(), f'file does not exist, ``{dotenv_path}``'
load_dotenv(find_dotenv(str(dotenv_path), raise_error_if_not_found=True), override=True)


log = logging.getLogger(__name__)


## django PROJECT settings ------------------------------------------

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
# log.debug( f'BASE_DIR, ``{BASE_DIR}``' )


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-3ory+ty87_wq8-21ki6d&a+x=z9_$2m(gr4@vxri@@^g7u!*oc'
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = json.loads(os.environ['DEBUG_JSON'])

ADMINS = json.loads(os.environ['ADMINS_JSON'])

ALLOWED_HOSTS = json.loads(os.environ['ALLOWED_HOSTS_JSON'])
CSRF_TRUSTED_ORIGINS = json.loads(os.environ['CSRF_TRUSTED_ORIGINS_JSON'])

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
        # 'DIRS': [ '%s/bdr_student_uploader_hub_app' % BASE_DIR ],
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
DATABASES = json.loads(os.environ['DATABASES_JSON'])

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

STATIC_URL = os.environ['STATIC_URL']
STATIC_ROOT = os.environ['STATIC_ROOT']  # needed for collectstatic command

# Email
SERVER_EMAIL = os.environ['SERVER_EMAIL']
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = int(os.environ['EMAIL_PORT'])

## user uploaded files ----------------------------------------------
MEDIA_ROOT = os.environ['MEDIA_ROOT']
BDR_API_FILE_PATH_ROOT = os.environ['BDR_API_FILE_PATH_ROOT']
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
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'logfile': {
            'level': os.environ.get('LOG_LEVEL', 'INFO'),  # add LOG_LEVEL=DEBUG to the .env file to see debug messages
            'class': 'logging.FileHandler',  # note: configure server to use system's log-rotate to avoid permissions issues
            'filename': os.environ['LOG_PATH'],
            'formatter': 'standard',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'bdr_uploader_hub_app': {
            'handlers': ['logfile'],
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
CACHES_JSON = os.environ['CACHES_JSON']
CACHES: dict = json.loads(CACHES_JSON)

LOGIN_URL = os.environ['LOGIN_URL']

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
# TEST_RUNNER = 'test_runner.JSONTestRunner'


## django APP settings ----------------------------------------------

TEST_SHIB_META_DCT: dict = json.loads(os.environ['TEST_SHIB_META_DCT_JSON'])

SHIB_SP_LOGIN_URL: str = os.environ['SHIB_SP_LOGIN_URL']
SHIB_IDP_LOGOUT_URL: str = os.environ['SHIB_IDP_LOGOUT_URL']

## creates, eg: [('all_rights_reserved', 'All Rights Reserved'), ('CC_BY', 'Attribution (CC BY)'), etc.]
all_licenses_json: str = os.environ['ALL_LICENSE_OPTIONS_JSON']
licenses_list: list = json.loads(all_licenses_json)
ALL_LICENSE_OPTIONS: list[tuple[str, str]] = [tuple(item) for item in licenses_list]

## creates, eg: [('public', 'Public'), ('private', 'Private'), etc.]
all_visibilities_json: str = os.environ['ALL_VISIBILITY_OPTIONS_JSON']
visibilities_list: list = json.loads(all_visibilities_json)
ALL_VISIBILITY_OPTIONS: list[tuple[str, str]] = [tuple(item) for item in visibilities_list]

## used for pid<-->collection-name validation
BDR_PUBLIC_API_COLLECTION_ROOT_URL: str = os.environ['BDR_PUBLIC_API_COLLECTION_ROOT_URL']
TEST_COLLECTION_PID_FOR_FORM_VALIDATION: str = os.environ['TEST_COLLECTION_PID_FOR_FORM_VALIDATION']
TEST_COLLECTION_TITLE_FOR_FORM_VALIDATION: str = os.environ['TEST_COLLECTION_TITLE_FOR_FORM_VALIDATION']

## used for rightsMetadata xml file
BDR_MANAGER_GROUP: str = os.environ['BDR_MANAGER_GROUP']
BDR_BROWN_GROUP: str = os.environ['BDR_BROWN_GROUP']
BDR_PUBLIC_GROUP: str = os.environ['BDR_PUBLIC_GROUP']

## used for bdr-post
BDR_PRIVATE_API_ROOT_URL: str = os.environ['BDR_PRIVATE_API_ROOT_URL']

## used for ingest confirmation-email to student
BDR_PUBLIC_STUDIO_ITEM_ROOT_URL: str = os.environ['BDR_PUBLIC_STUDIO_ITEM_ROOT_URL']

## for mount check on version-url call
MOUNT_POINT: str = os.environ['MOUNT_POINT']
