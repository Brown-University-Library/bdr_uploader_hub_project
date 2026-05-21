import json
import tempfile
from unittest import mock

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from bdr_uploader_hub_app.lib.ingester_handler import Ingester
from bdr_uploader_hub_app.models import AppConfig, Submission

LONG_KEYWORD_TERMS: list[str] = [f'keyword-{index:02d}-extended-topic' for index in range(1, 22)]
LONG_KEYWORDS: str = '|'.join(LONG_KEYWORD_TERMS)


class SubmissionKeywordFlowTest(TestCase):
    """
    Checks long-keyword submission flows that persist and ingest submissions.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='student-keywords',
            password='password123',
            email='student-keywords@example.com',
            first_name='Student',
            last_name='Keywords',
        )
        self.app_config = AppConfig.objects.create(
            name='Keyword Test App',
            slug='keyword-test-app',
            temp_config_json={'collection_pid': 'bdr:test-collection'},
        )
        self.client.force_login(self.user)

    def test_student_confirm_persists_keywords_longer_than_255_characters(self):
        """
        Checks student confirmation persists long keyword strings without error.
        """
        session = self.client.session
        session['student_form_data'] = {
            'title': 'Long keyword submission',
            'abstract': 'Submission abstract',
            'keywords': LONG_KEYWORDS,
            'staged_file_path': '/tmp/long-keywords.pdf',
            'original_file_name': 'long-keywords.pdf',
            'checksum_type': 'md5',
            'checksum': 'abc123',
            'accessibility_agreement': True,
        }
        session.save()

        response = self.client.post(
            reverse('student_confirm_url', kwargs={'slug': self.app_config.slug}),
            data={'confirm': '1'},
        )

        submission = Submission.objects.get(app=self.app_config)
        self.assertGreater(len(LONG_KEYWORDS), 255)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('upload_successful_url'), response.url)
        self.assertEqual(LONG_KEYWORDS, submission.keywords)
        self.assertEqual('ready_to_ingest', submission.status)

    @override_settings(
        BDR_API_FILE_PATH_ROOT='/tmp/bdr-api-files',
        BDR_BROWN_GROUP='brown:test',
        BDR_MANAGER_GROUP='manager:test',
        BDR_PUBLIC_GROUP='public:test',
        BDR_PUBLIC_STUDIO_ITEM_ROOT_URL='https://example.edu/studio/item/',
    )
    def test_ingester_manage_ingest_accepts_long_keywords(self):
        """
        Checks mocked ingest succeeds with long keywords and preserves MODS topics.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            with override_settings(MEDIA_ROOT=tempdir):
                submission = Submission.objects.create(
                    app=self.app_config,
                    student_eppn=self.user.username,
                    student_email=self.user.email,
                    title='Long keyword ingest',
                    abstract='Submission abstract',
                    keywords=LONG_KEYWORDS,
                    license_options='CC0',
                    visibility_options='public',
                    original_file_name='long-keywords.txt',
                    primary_file=SimpleUploadedFile('long-keywords.txt', b'hello world', content_type='text/plain'),
                    checksum_type='md5',
                    checksum='abc123',
                    status='ready_to_ingest',
                )
                request = RequestFactory().post('/admin/bdr_uploader_hub_app/submission/')
                request.user = self.user
                request.session = self.client.session
                setattr(request, '_messages', FallbackStorage(request))

                with (
                    mock.patch.object(Ingester, 'post', return_value=('bdr:999999', None)) as mock_post,
                    mock.patch('bdr_uploader_hub_app.lib.ingester_handler.send_ingest_success_email') as mock_email,
                ):
                    Ingester().manage_ingest(request, Submission.objects.filter(pk=submission.pk))

        submission.refresh_from_db()
        params = mock_post.call_args.args[0]
        mods_payload: dict[str, str] = json.loads(params['mods'])
        mods_xml: str = mods_payload['xml_data']
        topic_count = len(BeautifulSoup(mods_xml, 'xml').find_all('topic'))

        self.assertEqual('ingested', submission.status)
        self.assertEqual('bdr:999999', submission.bdr_pid)
        self.assertIsNone(submission.ingest_error_message)
        self.assertEqual(len(LONG_KEYWORD_TERMS), topic_count)
        mock_email.assert_called_once()
