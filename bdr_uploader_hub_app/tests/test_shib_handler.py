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
