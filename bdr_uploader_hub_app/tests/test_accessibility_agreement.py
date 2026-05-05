from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from bdr_uploader_hub_app.forms.student_form import make_student_form_class
from bdr_uploader_hub_app.models import AppConfig


class AccessibilityAgreementTest(TestCase):
    """
    Checks student upload accessibility agreement behavior.
    """

    def test_make_student_form_class_adds_required_accessibility_agreement_in_basic_field_order(self):
        """
        Checks the generated student form always includes the required accessibility agreement field.
        """
        form_class = make_student_form_class({})

        self.assertIn('accessibility_agreement', form_class.base_fields)
        self.assertTrue(form_class.base_fields['accessibility_agreement'].required)
        self.assertEqual('(required)', form_class.base_fields['accessibility_agreement'].help_text)
        self.assertEqual(
            ['title', 'abstract', 'accessibility_agreement', 'main_file'],
            list(form_class.base_fields.keys())[:4],
        )

    def test_student_form_template_places_accessibility_agreement_above_upload_file(self):
        """
        Checks the student form template renders the agreement block above the upload field with the required link.
        """
        form_class = make_student_form_class({})
        form = form_class()
        template = Template(
            """
            {% load static %}
            {% include 'student_form.html' %}
            """
        )
        context = Context(
            {
                'form': form,
                'slug': 'test-slug',
                'back_url': '/back/',
                'back_url_text': 'back',
                'depositor_fullname': 'Test User',
                'depositor_email': 'test@example.com',
                'deposit_iso_date': '2026-05-05T00:00:00',
                'app_name': 'Test App',
            }
        )

        rendered = template.render(context)

        abstract_position = rendered.find('id="abstract_group"')
        agreement_text_position = rendered.find('id="accessibility_agreement_text"')
        agreement_position = rendered.find('id="accessibility_agreement_group"')
        main_file_position = rendered.find('id="main_file_group"')
        self.assertLess(abstract_position, agreement_text_position)
        self.assertLess(agreement_text_position, agreement_position)
        self.assertLess(agreement_position, main_file_position)
        self.assertIn(
            "By using this uploader, you are agreeing that your content meets Brown's Digital Accessibility policy standards.",
            rendered,
        )
        self.assertIn(
            '<a href="https://digital-accessibility.brown.edu/" target="_blank" rel="noopener noreferrer">Brown\'s Digital Accessibility website</a>',
            rendered,
        )
        self.assertIn('class="accessibility-agreement-text"', rendered)
        self.assertIn('<label for="id_accessibility_agreement">Accessibility agreement</label>', rendered)

    def test_upload_slug_rejects_valid_submission_when_accessibility_agreement_is_unchecked(self):
        """
        Checks upload submission stays on the form when the accessibility agreement is not checked.
        """
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username='student1',
            password='password123',
            email='student1@example.com',
            first_name='Student',
            last_name='One',
        )
        app_config = AppConfig.objects.create(
            name='Accessibility Test App',
            slug='accessibility-test-app',
            temp_config_json={},
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('student_upload_slug_url', kwargs={'slug': app_config.slug}),
            data={
                'title': 'Accessible title',
                'abstract': 'Accessible abstract',
                'license_options': '',
                'visibility_options': '',
                'main_file': SimpleUploadedFile('example.txt', b'example file contents', content_type='text/plain'),
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertIn('accessibility_agreement', response.context['form'].errors)
        self.assertContains(response, 'Please correct the errors below.')
        self.assertContains(response, 'field: Accessibility agreement')
        self.assertNotIn('student_form_data', self.client.session)
