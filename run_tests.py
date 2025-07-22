import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_run_tests'  # need to do this as early as possible

import sys
import tempfile

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp_dir:
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=1, interactive=True)
        failures = test_runner.run_tests(['.'])
    sys.exit(failures)
