"""
Runs ci-compatible django tests.
"""

import os

## set settings as early as possible --------------------------------
is_running_on_github: bool = os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'
if is_running_on_github:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_run_tests'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

## back to normal imports -------------------------------------------
import logging  # noqa: E402 (ignoring import order linter warning due to need to set DJANGO_SETTINGS_MODULE early)
import sys  # noqa: E402
import tempfile  # noqa: E402

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.test.utils import get_runner  # noqa: E402

log = logging.getLogger(__name__)
log.debug(f'is_running_on_github, ``{is_running_on_github}``')
log.debug(f'settings-module, ``{os.environ.get("DJANGO_SETTINGS_MODULE")}``')
print(f'using settings-module, ``{os.environ.get("DJANGO_SETTINGS_MODULE")}``')


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp_dir:
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=1, interactive=True)
        failures = test_runner.run_tests(['.'])
    sys.exit(failures)
