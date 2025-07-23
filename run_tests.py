"""
Runs ci-compatible django tests.
"""

import os
import socket

## set settings as early as possible --------------------------------
server_name = socket.gethostname()
if server_name.startswith(('dl', 'pl')):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_run_tests'  # need to do this as early as possible

## back to normal processing ----------------------------------------
import logging  # noqa: E402 (ignoring import order linter warning due to need to set DJANGO_SETTINGS_MODULE early)
import sys  # noqa: E402
import tempfile  # noqa: E402

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.test.utils import get_runner  # noqa: E402

log = logging.getLogger(__name__)
log.debug(f'server_name: ``{server_name}``')
print(f'server_name: ``{server_name}``')
print(f'settings-envar, ``{os.environ.get("DJANGO_SETTINGS_MODULE")}``')


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp_dir:
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=1, interactive=True)
        failures = test_runner.run_tests(['.'])
    sys.exit(failures)
