import json
from io import StringIO
from unittest.runner import TextTestResult

from django.test.runner import DiscoverRunner


class JSONTestResult(TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.results = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.results.append({'test': str(test), 'status': 'success'})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append({'test': str(test), 'status': 'failure', 'error': self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.results.append({'test': str(test), 'status': 'error', 'error': self._exc_info_to_string(err, test)})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.results.append({'test': str(test), 'status': 'skipped', 'reason': reason})

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.results.append({'test': str(test), 'status': 'expected failure', 'error': self._exc_info_to_string(err, test)})

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.results.append({'test': str(test), 'status': 'unexpected success'})


class JSONTestRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        # Create a stream to capture output (StringIO acts as a writable buffer)
        stream = StringIO()
        verbosity = self.verbosity
        descriptions = self.descriptions

        # Initialize the custom result class
        result = JSONTestResult(stream, descriptions, verbosity)

        # Run the test suite with the custom result
        suite.run(result)

        # Display results as JSON
        self.display_results_as_json(result)

        return result

    @staticmethod
    def display_results_as_json(result):
        output = {'tests': result.results}
        print(json.dumps(output, indent=4))
