import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from django import forms
from django.test import SimpleTestCase, override_settings

from bdr_uploader_hub_app.forms.staff_form import StaffForm
from bdr_uploader_hub_app.forms.student_form import make_student_form_class
from bdr_uploader_hub_app.lib.department_collection_helper import build_department_collection_choices
from bdr_uploader_hub_app.lib.department_collection_helper import resolve_department_collection_choice
from bdr_uploader_hub_app.lib.ingester_handler import Ingester


class DepartmentCollectionHelperTest(SimpleTestCase):
    """
    Checks department collection helper behavior.
    """

    def test_build_department_collection_choices_includes_blank_option_and_entries(self):
        """
        Checks valid department map parsing into dropdown choices.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            filepath = Path(tempdir) / 'department-map.json'
            filepath.write_text(
                json.dumps(
                    [
                        {'id': 'Computer Science\ttest:cs', 'text': 'Computer Science'},
                        {'id': 'History\ttest:hist', 'text': 'History'},
                    ]
                ),
                encoding='utf-8',
            )

            with override_settings(DEPARTMENT_MAP_FILEPATH=str(filepath)):
                choices = build_department_collection_choices()
                self.assertEqual(('', '---------'), choices[0])
                self.assertIn(('Computer Science\ttest:cs', 'Computer Science'), choices)
                self.assertIn(('History\ttest:hist', 'History'), choices)

    def test_resolve_department_collection_choice_returns_label_and_pid(self):
        """
        Checks submitted department choice resolution.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            filepath = Path(tempdir) / 'department-map.json'
            filepath.write_text(json.dumps([{'id': 'Biology\ttest:bio', 'text': 'Biology'}]), encoding='utf-8')

            with override_settings(DEPARTMENT_MAP_FILEPATH=str(filepath)):
                result = resolve_department_collection_choice('Biology\ttest:bio')

        self.assertEqual(('Biology', 'test:bio'), result)

    def test_build_department_collection_choices_rejects_duplicate_labels(self):
        """
        Checks duplicate labels fail clearly.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            filepath = Path(tempdir) / 'department-map.json'
            filepath.write_text(
                json.dumps(
                    [
                        {'id': 'Anthropology\ttest:anth1', 'text': 'Anthropology'},
                        {'id': 'Anthropology\ttest:anth2', 'text': 'Anthropology'},
                    ]
                ),
                encoding='utf-8',
            )

            with override_settings(DEPARTMENT_MAP_FILEPATH=str(filepath)):
                with self.assertRaisesRegex(ValueError, 'Duplicate department label found'):
                    build_department_collection_choices()


class StudentFormDepartmentCollectionTest(SimpleTestCase):
    """
    Checks student form branching for department collection mode.
    """

    def test_fixed_collection_mode_does_not_add_department_dropdown(self):
        """
        Checks fixed mode leaves the department collection dropdown absent.
        """
        form_class = make_student_form_class({'collection_assignment_mode': 'fixed_collection'})
        self.assertNotIn('department_collection_choice', form_class.base_fields)

    def test_department_collection_mode_adds_required_dropdown(self):
        """
        Checks department menu mode adds a required dropdown field.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            filepath = Path(tempdir) / 'department-map.json'
            filepath.write_text(json.dumps([{'id': 'Biology\ttest:bio', 'text': 'Biology'}]), encoding='utf-8')

            with override_settings(DEPARTMENT_MAP_FILEPATH=str(filepath)):
                form_class = make_student_form_class({'collection_assignment_mode': 'department_collection_menu'})

        field = form_class.base_fields['department_collection_choice']
        self.assertIsInstance(field, forms.ChoiceField)
        self.assertTrue(field.required)
        self.assertEqual('', field.choices[0][0])


class StaffFormDepartmentCollectionValidationTest(SimpleTestCase):
    """
    Checks staff form validation for department collection mode.
    """

    @override_settings(
        ALL_LICENSE_OPTIONS=[('CC_BY', 'CC BY')],
        ALL_VISIBILITY_OPTIONS=[('public', 'Public')],
    )
    def test_department_collection_mode_does_not_require_fixed_collection_fields(self):
        """
        Checks department mode skips fixed collection pid/title requirements.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            filepath = Path(tempdir) / 'department-map.json'
            filepath.write_text(json.dumps([{'id': 'Biology\ttest:bio', 'text': 'Biology'}]), encoding='utf-8')

            with override_settings(DEPARTMENT_MAP_FILEPATH=str(filepath)):
                form = StaffForm(
                    data={
                        'collection_assignment_mode': 'department_collection_menu',
                        'staff_to_notify': 'valid@example.com',
                        'authorized_student_emails': 'student@example.com',
                        'license_options': ['CC_BY'],
                        'visibility_options': ['public'],
                    }
                )

                self.assertTrue(form.is_valid(), form.errors.as_json())
                self.assertNotIn('collection_pid', form.errors)
                self.assertNotIn('collection_title', form.errors)

    @override_settings(
        ALL_LICENSE_OPTIONS=[('CC_BY', 'CC BY')],
        ALL_VISIBILITY_OPTIONS=[('public', 'Public')],
    )
    def test_department_collection_mode_requires_valid_department_map(self):
        """
        Checks department mode reports invalid department map errors.
        """
        with override_settings(DEPARTMENT_MAP_FILEPATH='/tmp/does-not-exist.json'):
            form = StaffForm(
                data={
                    'collection_assignment_mode': 'department_collection_menu',
                    'staff_to_notify': 'valid@example.com',
                    'authorized_student_emails': 'student@example.com',
                    'license_options': ['CC_BY'],
                    'visibility_options': ['public'],
                }
            )

            self.assertFalse(form.is_valid())
            self.assertIn('collection_assignment_mode', form.errors)


class IngesterDepartmentCollectionTest(SimpleTestCase):
    """
    Checks ingest collection pid selection behavior.
    """

    def test_prepare_rels_prefers_submission_target_collection_pid(self):
        """
        Checks submission-level target collection pid takes precedence.
        """
        submission = mock.Mock()
        submission.target_collection_pid = 'test:submission'
        rels = Ingester().prepare_rels(submission, {'collection_pid': 'test:app'})
        self.assertEqual({'isMemberOfCollection': 'test:submission'}, rels)

    def test_prepare_rels_falls_back_to_app_collection_pid(self):
        """
        Checks ingest falls back to app-level collection pid.
        """
        submission = mock.Mock()
        submission.target_collection_pid = None
        rels = Ingester().prepare_rels(submission, {'collection_pid': 'test:app'})
        self.assertEqual({'isMemberOfCollection': 'test:app'}, rels)

    def test_prepare_rels_requires_any_collection_pid(self):
        """
        Checks ingest errors when no collection pid is available.
        """
        submission = mock.Mock()
        submission.target_collection_pid = None
        with self.assertRaisesRegex(ValueError, 'No collection pid is available for ingest'):
            Ingester().prepare_rels(submission, {})


if __name__ == '__main__':
    unittest.main()
