import os
import sys
import tempfile

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    os.environ['SECRET_KEY'] = 'abcd'
    os.environ['DEBUG_JSON'] = 'true'
    os.environ['ADMINS_JSON'] = '[]'
    os.environ['ALLOWED_HOSTS_JSON'] = '[]'
    os.environ['CSRF_TRUSTED_ORIGINS_JSON'] = '[]'
    os.environ['DATABASES_JSON'] = '[]'
    os.environ['STATIC_URL'] = '/static/'
    os.environ['STATIC_ROOT'] = '/tmp/'
    os.environ['SERVER_EMAIL'] = 'example@domain.edu'
    os.environ['EMAIL_HOST'] = 'localhost'
    os.environ['EMAIL_PORT'] = '1025'
    os.environ['MEDIA_ROOT'] = '/tmp/'
    os.environ['BDR_API_FILE_PATH_ROOT'] = '/tmp/'
    os.environ['FILE_UPLOAD_PERMISSIONS'] = 'None'
    os.environ['FILE_UPLOAD_DIRECTORY_PERMISSIONS'] = 'None'
    os.environ['LOG_PATH'] = '/tmp/'
    with tempfile.TemporaryDirectory() as tmp:
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=1, interactive=True)
        failures = test_runner.run_tests(['.'])
    sys.exit(failures)
