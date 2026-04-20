"""
Runs ci-compatible django tests.

Usage examples:
    (all) uv run ./run_tests.py
    (module) uv run ./run_tests.py bdr_uploader_hub_app.tests.test_other
    (class) uv run ./run_tests.py bdr_uploader_hub_app.tests.test_other.ErrorCheckTest
    (method) uv run ./run_tests.py bdr_uploader_hub_app.tests.test_other.ErrorCheckTest.test_prod_errorcheck

Also takes a -v or --verbose flag to increase verbosity to level 2.
"""

import argparse
import logging
import os
import sys
import tempfile

## set settings as early as possible --------------------------------
is_running_on_github: bool = os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'
if is_running_on_github:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_run_tests'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django  # noqa: E402 (ignoring import order linter warning due to need to set DJANGO_SETTINGS_MODULE early)
from django.conf import settings  # noqa: E402
from django.test.utils import get_runner  # noqa: E402

log = logging.getLogger(__name__)
log.debug(f'is_running_on_github, ``{is_running_on_github}``')
log.debug(f'settings-module, ``{os.environ.get("DJANGO_SETTINGS_MODULE")}``')


def build_parser() -> argparse.ArgumentParser:
    """
    Builds the command-line parser for the test runner.

    Called by: main()
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'test_label',
        nargs='?',
        default='.',
        help='Optional Django test label for a module, class, or method.',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Increase verbosity to level 2.',
    )
    return parser


def normalize_test_label(test_label: str) -> str:
    """
    Normalizes a user-provided test label for Django test execution.

    Called by: main()
    """
    normalized_label: str = test_label[:-3] if test_label.endswith('.py') else test_label
    if normalized_label in {'tests', 'test', '.'}:
        normalized_label = '.'
    return normalized_label


def run_tests(test_label: str, verbose: bool) -> int:
    """
    Runs Django tests for the provided test label.

    Called by: main()
    """
    normalized_label: str = normalize_test_label(test_label)
    test_labels: list[str] = [normalized_label]
    verbosity: int = 2 if verbose else 1
    print(f'using settings-module, ``{os.environ.get("DJANGO_SETTINGS_MODULE")}``')
    with tempfile.TemporaryDirectory():
        django.setup()
        test_runner_class = get_runner(settings)
        test_runner = test_runner_class(verbosity=verbosity, interactive=True)
        failures: int = test_runner.run_tests(test_labels)
    return failures


def main() -> None:
    """
    Parses arguments and runs the requested Django tests.

    Called by: __main__
    """
    parser = build_parser()
    args = parser.parse_args()
    failures: int = run_tests(args.test_label, args.verbose)
    sys.exit(failures)


if __name__ == '__main__':
    main()
