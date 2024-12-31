## <https://peps.python.org/pep-0723/> recently adopted python standard.
## Allows, for development, to run the app via `uv run ./manage.py runserver`, with no venv.
# /// script
# requires-python = "~=3.12.0"
# dependencies = [
#     "django~=4.2.0",
#     "python-dotenv~=1.0.0",
#     "requests~=2.27.0",
#     "trio~=0.26.0",
#     "urllib3~=1.26.0",
# ]
# ///

import os
import sys
import tempfile

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    with tempfile.TemporaryDirectory() as tmp:
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=1, interactive=True)
        failures = test_runner.run_tests(['.'])
    sys.exit(failures)
