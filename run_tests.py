import os
import sys
import tempfile

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == '__main__':
    os.environ['ADMINS_JSON'] = '[]'
    os.environ['ALL_LICENSE_OPTIONS_JSON'] = '[]'
    os.environ['ALL_VISIBILITY_OPTIONS_JSON'] = '[]'
    os.environ['ALLOWED_HOSTS_JSON'] = '[]'
    os.environ['BDR_API_FILE_PATH_ROOT'] = '/tmp/'
    os.environ['BDR_BROWN_GROUP'] = 'brown_group'
    os.environ['BDR_MANAGER_GROUP'] = 'manager_group'
    os.environ['BDR_PRIVATE_API_ROOT_URL'] = 'http://localhost:8000/api/private/items/'
    os.environ['BDR_PUBLIC_API_COLLECTION_ROOT_URL'] = 'http://localhost:8000/api/collections/'
    os.environ['BDR_PUBLIC_GROUP'] = 'public_group'
    os.environ['BDR_PUBLIC_STUDIO_ITEM_ROOT_URL'] = 'http://localhost:8000/studio/items/'
    os.environ['CSRF_TRUSTED_ORIGINS_JSON'] = '[]'
    os.environ['DATABASES_JSON'] = '[]'
    os.environ['DEBUG_JSON'] = 'true'
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    os.environ['EMAIL_HOST'] = 'localhost'
    os.environ['EMAIL_PORT'] = '1025'
    os.environ['FAST_URI'] = 'http://fast.org/url'
    os.environ['FILE_UPLOAD_DIRECTORY_PERMISSIONS'] = 'None'
    os.environ['FILE_UPLOAD_PERMISSIONS'] = 'None'
    os.environ['LOG_PATH'] = '/tmp/'
    os.environ['LOGIN_URL'] = '/login/'
    os.environ['MEDIA_ROOT'] = '/tmp/'
    os.environ['SECRET_KEY'] = 'abcd'
    os.environ['SERVER_EMAIL'] = 'example@domain.edu'
    os.environ['SHIB_IDP_LOGOUT_URL'] = 'http://localhost:8000/shib_logout/'
    os.environ['SHIB_SP_LOGIN_URL'] = 'http://localhost:8000/shib_login/'
    os.environ['STATIC_ROOT'] = '/tmp/'
    os.environ['STATIC_URL'] = '/static/'
    os.environ['TEST_COLLECTION_PID_FOR_FORM_VALIDATION'] = 'test:123'
    os.environ['TEST_COLLECTION_TITLE_FOR_FORM_VALIDATION'] = 'Test Collection'
    os.environ['TEST_SHIB_META_DCT_JSON'] = '{}'
    os.environ['LOG_PATH'] = '/tmp/'
    with tempfile.TemporaryDirectory() as tmp_dir:
        # os.environ['LOG_PATH'] = tmp_dir
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=1, interactive=True)
        failures = test_runner.run_tests(['.'])
    sys.exit(failures)
