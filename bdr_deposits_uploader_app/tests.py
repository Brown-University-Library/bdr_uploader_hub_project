import logging
import pprint
from pathlib import Path

from django.conf import settings as project_settings
from django.test import SimpleTestCase, TestCase  # SimpleTestCase does not require db
from django.test.utils import override_settings

from bdr_deposits_uploader_app.forms.staff_form import StaffForm
from bdr_deposits_uploader_app.lib.ingester_handler import Ingester

log = logging.getLogger(__name__)
TestCase.maxDiff = 1000


class ModsMakerTest(SimpleTestCase):
    """
    Tests the mods_maker function.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        # Set up any necessary data or state for the tests
        pass

    def test_prepare_mods_A(self):
        """
        Tests the mods_maker function.
        """
        # ingester = Ingester()
        # submission = Submission(
        #     title='Sample Title',
        #     author='Sample Author',
        #     date='2023-10-01',
        #     description='Sample Description',
        # )
        # result = ingester.prepare_mods(submission)
        # log.debug(f'mods_maker result: {result}')
        # self.assertIn('<mods:title>Sample Title</mods:title>', result)
        self.assertEqual(1, 2)  # placeholder


class ErrorCheckTest(SimpleTestCase):
    """
    Checks urls.
    """

    @override_settings(DEBUG=True)  # for tests, DEBUG autosets to False
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

    ## end class ErrorCheckTest()


class StaffFormDirectTests(TestCase):
    def test_valid_submission(self):
        data = {
            'collection_pid': project_settings.TEST_COLLECTION_PID_FOR_FORM_VALIDATION,
            'collection_title': project_settings.TEST_COLLECTION_TITLE_FOR_FORM_VALIDATION,
            'staff_to_notify': 'valid@example.com',
            'authorized_student_emails': 'student@example.com',
            ## license fields
            'offer_license_options': True,
            'license_options': ['CC_BY', 'CC_BY-SA', 'CC_BY-NC-SA'],
            'license_default': 'CC_BY',
            # 'license_default': 'foo`',  # invalid default
            ## visibility fields
            'offer_visibility_options': True,
            'visibility_options': ['public', 'private'],
            'visibility_default': 'public',
        }
        form = StaffForm(data=data)
        log.debug(f'form.errors-get-json-data BEFORE is-valid(): {pprint.pformat(form.errors.get_json_data())}')
        self.assertTrue(form.is_valid(), f'Errors: {form.errors.get_json_data()}')
        log.debug(f'form.errors-get-json-data AFTER is-valid(): {pprint.pformat(form.errors.get_json_data())}')
        self.assertEqual(form.cleaned_data.get('offer_license_options'), True)
        self.assertEqual(form.cleaned_data.get('offer_visibility_options'), True)

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
        # Test that if license options are offered but the options and default are missing, errors occur.
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
        # Test that at least one student group or email is required.
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
        self.assertIn('__all__', form.errors)  # Non-field errors are stored under __all__
        self.assertIn('At least one student group or email must be provided.', form.errors['__all__'][0])

    ## end class StaffFormTests()


class IngestTest(TestCase):
    def setUp(self):
        self.ingester = Ingester()

    @override_settings(BDR_MANAGER_GROUP='admin_group', BDR_PUBLIC_GROUP='public_group', BDR_BROWN_GROUP='brown_group')
    def test_prepare_rights_public(self):
        """
        Checks rights for "public" form value.
        """
        result = self.ingester.prepare_rights('student@brown.edu', 'public')
        self.assertEqual(result['owner_id'], 'student@brown.edu#discover,display')
        self.assertIn('admin_group#discover,display', result['additional_rights'])
        self.assertIn('public_group#discover,display', result['additional_rights'])
        self.assertIn('brown_group#discover,display', result['additional_rights'])

    @override_settings(BDR_MANAGER_GROUP='admin_group', BDR_PUBLIC_GROUP='public_group', BDR_BROWN_GROUP='brown_group')
    def test_prepare_rights_private(self):
        """
        Checks rights for "private" form value.
        """
        result = self.ingester.prepare_rights('student@brown.edu', 'private')
        self.assertEqual(result['owner_id'], 'student@brown.edu#discover,display')
        self.assertEqual(result['additional_rights'], 'admin_group#discover,display')

    @override_settings(BDR_MANAGER_GROUP='admin_group', BDR_PUBLIC_GROUP='public_group', BDR_BROWN_GROUP='brown_group')
    def test_prepare_rights_brown_only_discoverable(self):
        """
        Checks rights for "brown_only_discoverable" form value.
        """
        result = self.ingester.prepare_rights('student@brown.edu', 'brown_only_discoverable')
        self.assertEqual(result['owner_id'], 'student@brown.edu#discover,display')
        self.assertEqual(result['additional_rights'], 'admin_group#discover,display+brown_group#discover,display')

    @override_settings(BDR_MANAGER_GROUP='admin_group', BDR_PUBLIC_GROUP='public_group', BDR_BROWN_GROUP='brown_group')
    def test_prepare_rights_brown_only_not_discoverable(self):
        """
        Checks rights for "brown_only_not_discoverable" form value.
        """
        result = self.ingester.prepare_rights('student@brown.edu', 'brown_only_not_discoverable')
        self.assertEqual(result['owner_id'], 'student@brown.edu#discover,display')
        self.assertEqual(result['additional_rights'], 'admin_group#discover,display+brown_group#display')

    @override_settings(BDR_API_FILE_PATH_ROOT='/mock/api/root')
    def test_prepare_file(self):
        """
        Checks the prepare_file function.
        """
        # Arrange
        submission_checksum_type = 'md5'
        submission_checksum = '1234567890abcdef'
        file_path = '/test/path/to/file.txt'
        original_file_name = 'original_filename.txt'

        # Act
        result = self.ingester.prepare_file(submission_checksum_type, submission_checksum, file_path, original_file_name)

        # Assert
        expected_result = {
            'checksum_type': submission_checksum_type,
            'checksum': submission_checksum,
            'file_name': original_file_name,
            'path': Path('/mock/api/root/file.txt'),
        }

        self.assertEqual(result, expected_result)

    ## end class IngestTest()
