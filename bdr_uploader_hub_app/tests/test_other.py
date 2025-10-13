import logging
import os
import pprint

from django.conf import settings as project_settings
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings

from bdr_uploader_hub_app.forms.staff_form import StaffForm

log = logging.getLogger(__name__)
TestCase.maxDiff = 1000


class ErrorCheckTest(SimpleTestCase):
    """
    Checks urls.
    """

    @override_settings(DEBUG=True)
    def test_dev_errorcheck(self):
        """
        Checks that dev error_check url triggers error.
        """
        log.debug(f'debug, ``{project_settings.DEBUG}``')
        try:
            log.debug('about to initiate client.get()')
            self.client.get('/error_check/')
        except Exception as e:
            log.debug(f'e, ``{repr(e)}``')
            self.assertEqual(
                "Exception('Raising intentional exception to check email-admins-on-error functionality.')",
                repr(e),
            )

    def test_prod_errorcheck(self):
        """
        Checks that production error_check url returns 404.
        """
        log.debug(f'debug, ``{project_settings.DEBUG}``')
        response = self.client.get('/error_check/')
        self.assertEqual(404, response.status_code)


class FastApiTest(TestCase):
    """
    Checks fast-api-related functions.
    """

    def test_call_oclc_fastapi(self):
        """
        Checks that the OCLC FastAPI call works.
        """
        expected: str = 'foo'
        result = fastapi.call_oclc_fastapi('bar')
        self.assertEqual(expected, result)


class StaffFormDirectTests(TestCase):
    # def test_valid_submission(self):
    #     data = {
    #         'collection_pid': project_settings.TEST_COLLECTION_PID_FOR_FORM_VALIDATION,
    #         'collection_title': project_settings.TEST_COLLECTION_TITLE_FOR_FORM_VALIDATION,
    #         'staff_to_notify': 'valid@example.com',
    #         'authorized_student_emails': 'student@example.com',
    #         ## license fields
    #         'offer_license_options': True,
    #         'license_options': ['CC_BY', 'CC_BY-SA', 'CC_BY-NC-SA'],
    #         'license_default': 'CC_BY',
    #         # 'license_default': 'foo`',  # invalid default
    #         ## visibility fields
    #         'offer_visibility_options': True,
    #         'visibility_options': ['public', 'private'],
    #         'visibility_default': 'public',
    #     }
    #     form = StaffForm(data=data)
    #     log.debug(f'form.errors-get-json-data BEFORE is-valid(): {pprint.pformat(form.errors.get_json_data())}')
    #     if '127.0.0.1' in project_settings.LOGIN_URL:
    #         errors = f'{form.errors.get_json_data()} -- note that the pid-title check requires VPN'
    #     else:
    #         errors = form.errors.get_json_data()
    #     self.assertTrue(form.is_valid(), f'Errors: {errors}')
    #     log.debug(f'form.errors-get-json-data AFTER is-valid(): {pprint.pformat(form.errors.get_json_data())}')
    #     self.assertEqual(form.cleaned_data.get('offer_license_options'), True)
    #     self.assertEqual(form.cleaned_data.get('offer_visibility_options'), True)

    def test_valid_submission(self):
        """
        Checks valid submission -- part of which requires a dev (so not public) BDR API call. Because of that API call...

        When running locally:
        - I want this test to run and fail if I'm not on VPN, giving me the helpful error message.
        - I want this test to run and pass if I'm on VPN.
        When running in CI:
        - I want this test to be skipped.
        When running on the server:
        - I want this test to run and pass.
        """
        is_running_on_github: bool = os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'
        log.debug(f'is_running_on_github, ``{is_running_on_github}``')
        if is_running_on_github:
            msg = 'skipping CI test that requires VPN'
            log.debug(msg)
            self.skipTest(msg)
        else:  # running locally or on server
            log.debug('running locally or on server, so running test')
            data = {
                'collection_pid': project_settings.TEST_COLLECTION_PID_FOR_FORM_VALIDATION,
                'collection_title': project_settings.TEST_COLLECTION_TITLE_FOR_FORM_VALIDATION,
                'staff_to_notify': 'valid@example.com',
                'authorized_student_emails': 'student@example.com',
                ## license fields
                'offer_license_options': True,
                'license_options': ['CC_BY', 'CC_BY-SA', 'CC_BY-NC-SA'],
                'license_default': 'CC_BY',
                ## visibility fields
                'offer_visibility_options': True,
                'visibility_options': ['public', 'private'],
                'visibility_default': 'public',
            }
            form = StaffForm(data=data)
            log.debug(f'form.errors-get-json-data BEFORE is-valid(): {pprint.pformat(form.errors.get_json_data())}')
            if '127.0.0.1' in project_settings.LOGIN_URL:
                errors = f'{form.errors.get_json_data()} -- note that the pid-title check requires VPN'
            else:
                errors = form.errors.get_json_data()
            self.assertTrue(form.is_valid(), f'Errors: {errors}')
            log.debug(f'form.errors-get-json-data AFTER is-valid(): {pprint.pformat(form.errors.get_json_data())}')
            self.assertEqual(form.cleaned_data.get('offer_license_options'), True)
            self.assertEqual(form.cleaned_data.get('offer_visibility_options'), True)
        ## end def test_valid_submission()

    def test_invalid_staff_email(self):
        data = {
            'collection_pid': '1234',
            'collection_title': 'My Collection',
            'staff_to_notify': 'invalid-email',
            'authorized_student_emails': 'student@example.com',
            ## minimal valid license/visibility inputs to avoid extra errors
            'offer_license_options': True,
            'license_options': ['CC_BY', 'CC_BY-SA', 'CC_BY-NC-SA'],
            'license_default': 'CC_BY',
            'offer_visibility_options': True,
            'visibility_options': ['public'],
            'visibility_default': 'public',
        }
        form = StaffForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('staff_to_notify', form.errors)
        self.assertIn('Invalid email(s): invalid-email', form.errors['staff_to_notify'][0])

    def test_license_dependency_error(self):
        data = {
            'collection_pid': '1234',
            'collection_title': 'My Collection',
            'staff_to_notify': 'valid@example.com',
            'authorized_student_emails': 'student@example.com',
            'offer_license_options': True,
            ## Missing license_options and license_default
            'offer_visibility_options': True,
            'visibility_options': ['public'],
            'visibility_default': 'public',
        }
        form = StaffForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('license_options', form.errors)
        self.assertIn('At least one license must be selected.', form.errors['license_options'][0])
        self.assertIn('license_default', form.errors)
        self.assertIn('A default license is required.', form.errors['license_default'][0])

    def test_missing_student_contacts(self):
        data = {
            'collection_pid': '1234',
            'collection_title': 'My Collection',
            'staff_to_notify': 'valid@example.com',
            ## Neither authorized_student_emails nor authorized_student_groups provided
            'offer_license_options': True,
            'license_options': ['MIT'],
            'license_default': 'MIT',
            'offer_visibility_options': True,
            'visibility_options': ['public'],
            'visibility_default': 'public',
        }
        form = StaffForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class IngestTest(SimpleTestCase):
    def setUp(self):
        pass

    def test_prepare_rights_public(self):
        """
        Checks rights for "public" form value.
        """
        pass

    def test_prepare_rights_private(self):
        """
        Checks rights for "private" form value.
        """
        pass

    def test_prepare_rights_brown_only_discoverable(self):
        """
        Checks rights for "brown_only_discoverable" form value.
        """
        pass

    def test_prepare_rights_brown_only_not_discoverable(self):
        """
        Checks rights for "brown_only_not_discoverable" form value.
        """
        pass

    def test_prepare_file(self):
        """
        Checks that the prepare_file function:
        - separates the file path root from the file name,
        - switches the file path to the BDR API file path root,
        - returns a dictionary with the expected values.
        """
        pass
