from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from bdr_uploader_hub_app.forms.student_form import make_student_form_class


class StudentFormMaxLengthTest(SimpleTestCase):
    """
    Checks student form max-length behavior.
    """

    def test_targeted_char_fields_render_with_maxlength_and_unlimited_fields_remain_uncapped(self):
        """
        Checks the targeted student text inputs render with maxlength while abstract and keywords remain uncapped.
        """
        config_data: dict[str, object] = {
            'collection_assignment_mode': 'fixed_collection',
            'offer_advisors_and_readers': True,
            'offer_team_members': True,
            'offer_faculty_mentors': True,
            'offer_authors': True,
            'offer_department': True,
            'offer_research_program': True,
            'ask_for_keywords': True,
            'ask_for_concentrations': True,
            'ask_for_degrees': True,
        }
        form_class = make_student_form_class(config_data)
        form = form_class()
        capped_field_names: list[str] = [
            'title',
            'advisors_and_readers',
            'team_members',
            'faculty_mentors',
            'authors',
            'department',
            'research_program',
            'concentrations',
            'degrees',
        ]

        for field_name in capped_field_names:
            with self.subTest(field_name=field_name):
                self.assertEqual(255, form.fields[field_name].max_length)
                self.assertIn('maxlength="255"', str(form[field_name]))

        self.assertIsNone(form.fields['abstract'].max_length)
        self.assertNotIn('maxlength="255"', str(form['abstract']))
        self.assertIsNone(form.fields['keywords'].max_length)
        self.assertNotIn('maxlength="255"', str(form['keywords']))

    def test_title_over_255_characters_fails_form_validation(self):
        """
        Checks a 256-character title fails form validation with the standard max-length message.
        """
        title_value: str = 'x' * 256
        form_class = make_student_form_class({})
        form = form_class(
            data={
                'title': title_value,
                'abstract': 'Abstract text',
                'accessibility_agreement': 'on',
            },
            files={'main_file': SimpleUploadedFile('example.txt', b'example file contents', content_type='text/plain')},
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(['Ensure this value has at most 255 characters (it has 256).'], form.errors['title'])

    def test_title_at_255_characters_is_valid(self):
        """
        Checks a 255-character title remains valid.
        """
        title_value: str = 'x' * 255
        form_class = make_student_form_class({})
        form = form_class(
            data={
                'title': title_value,
                'abstract': 'Abstract text',
                'accessibility_agreement': 'on',
            },
            files={'main_file': SimpleUploadedFile('example.txt', b'example file contents', content_type='text/plain')},
        )

        self.assertTrue(form.is_valid(), form.errors)
