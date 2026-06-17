from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from bdr_uploader_hub_app.lib.shib_handler import provision_user, shib_decorator


def shib_test_view(request: HttpRequest) -> HttpResponse:
    """
    Provides a minimal decorated view for Shib decorator tests.
    Called by: ShibDecoratorTest.test_missing_mail_redirects_with_problem_message()
    """
    return HttpResponse('ok')


class ShibDecoratorTest(TestCase):
    def test_missing_mail_redirects_with_problem_message(self):
        """
        Checks that missing Shib mail shows a user-facing problem message.
        """
        shib_metadata = {
            'Shibboleth-eppn': 'student@brown.edu',
            'Shibboleth-givenName': 'Student',
            'Shibboleth-sn': 'Person',
            'Shibboleth-isMemberOf': 'BROWN:COMMUNITY:ALL;COURSE:TEST:Student',
        }
        request = RequestFactory().get('/shib_login/')
        request.user = AnonymousUser()
        SessionMiddleware(lambda req: None).process_request(request)

        with override_settings(TEST_SHIB_META_DCT=shib_metadata):
            response = shib_decorator(shib_test_view)(request)

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('info_url'), response.url)
        self.assertIn('did not include an email address', request.session['problem_message'])
        self.assertIn('bdr@brown.edu', request.session['problem_message'])


class InfoProblemMessageTemplateTest(TestCase):
    def test_missing_mail_problem_message_renders_subject_mailto(self):
        """
        Checks that the missing Shib mail problem message renders a mailto link with a subject.
        """
        problem_message = (
            'Your Brown/Shibboleth login did not include an email address, '
            'which is required to use this uploader. Please contact bdr@brown.edu for assistance.'
        )
        session = self.client.session
        session['problem_message'] = problem_message
        session.save()

        response = self.client.get(reverse('info_url'))

        self.assertContains(response, 'did not include an email address')
        self.assertContains(response, 'bdr@brown.edu')
        self.assertContains(
            response,
            'mailto:bdr@brown.edu?subject=bdr-uploader-hub%3A%20missing%20Shibboleth%20email',
        )


class ShibProvisionUserTest(TestCase):
    def test_missing_mail_returns_none(self):
        """
        Checks that Shib provisioning still requires mail.
        """
        shib_metadata = {
            'Shibboleth-eppn': 'student@brown.edu',
            'Shibboleth-givenName': 'Student',
            'Shibboleth-sn': 'Person',
            'Shibboleth-isMemberOf': 'BROWN:COMMUNITY:ALL;COURSE:TEST:Student',
        }

        user = provision_user(shib_metadata)

        self.assertIsNone(user)
