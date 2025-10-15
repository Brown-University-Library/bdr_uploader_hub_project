import unittest
from unittest.mock import MagicMock, patch

import httpx

from bdr_uploader_hub_app.lib import fastapi


class TestPrepUrlParams(unittest.TestCase):
    def test_prep_url_params(self):
        url, params = fastapi.prep_url_params('bar')
        self.assertEqual(url, 'https://fast.oclc.org/searchfast/fastsuggest')
        self.assertIsInstance(params, dict)
        self.assertEqual(params.get('query'), 'bar')
        self.assertEqual(params.get('queryIndex'), 'suggestall')
        self.assertEqual(params.get('queryReturn'), 'idroot,auth,type,suggestall')
        self.assertEqual(params.get('suggest'), 'autoSubject')


class FakeHttpxClient(httpx.Client):
    def __init__(self):
        self.last_request = None

    def build_request(self, method, url, params=None, timeout=None):
        # Build a real httpx.Request to keep behavior consistent
        req = httpx.Request(method, url, params=params)
        self.last_request = req
        return req

    def send(self, request: httpx.Request) -> httpx.Response:
        # Overridden per-test via monkeypatch or by replacing the method
        raise NotImplementedError


class TestMakeRequest(unittest.TestCase):
    def test_make_request_success(self):
        fake_httpx_client = FakeHttpxClient()
        req = fake_httpx_client.build_request('GET', 'https://example.org/')
        payload = {'response': {'docs': [{'auth': 'X'}]}}

        def send_ok(request):
            return httpx.Response(status_code=200, request=request, json=payload)

        fake_httpx_client.send = send_ok
        result = fastapi.make_request(fake_httpx_client, req)
        self.assertEqual(result, payload)

    def test_make_request_non_200(self):
        client = FakeHttpxClient()
        req = client.build_request('GET', 'https://example.org/')

        def send_500(request):
            return httpx.Response(status_code=500, request=request, json={'error': 'boom'})

        client.send = send_500
        result = fastapi.make_request(client, req)
        self.assertEqual(result, {'response': {'docs': []}})

    def test_make_request_timeout(self):
        client = FakeHttpxClient()
        req = client.build_request('GET', 'https://example.org/')

        def send_timeout(request):
            raise httpx.TimeoutException('timeout')

        client.send = send_timeout
        result = fastapi.make_request(client, req)
        self.assertEqual(result, {'response': {'docs': []}})


class TestParseResponse(unittest.TestCase):
    def test_parse_identity(self):
        data = {'response': {'docs': []}}
        self.assertEqual(fastapi.parse_response(data), data)


class TestGetClient(unittest.TestCase):
    def test_singleton(self):
        c1 = fastapi.get_client()
        c2 = fastapi.get_client()
        self.assertIs(c1, c2)


class TestManageCall(unittest.TestCase):
    """
    How the @patch() decorator works...
    - It temporarily replaces `lib.fastapi.get_client` with a MagicMock.
    - A MagicMock is a flexible mock object that records calls and simulates behaviors.
    - The MagicMock is passed as the `mock_get_client` argument to the test function.
    - We
    """

    @patch('bdr_uploader_hub_app.lib.fastapi.get_client')
    def test_manage_oclc_fastapi_call_success(self, mock_get_client: MagicMock):
        ## setup fake client with controlled behavior ---------------
        fake_httpx_client = FakeHttpxClient()

        def send_ok(request):
            # Assert URL looks like the OCLC endpoint with query params
            self.assertIn('fast.oclc.org/searchfast/fastsuggest', str(request.url))
            self.assertIn('query=bar', str(request.url))
            payload = {'response': {'docs': [{'auth': 'Bar'}]}}
            return httpx.Response(status_code=200, request=request, json=payload)

        fake_httpx_client.send = send_ok
        mock_get_client.return_value = fake_httpx_client

        # Act
        result = fastapi.manage_oclc_fastapi_call('bar')

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn('response', result)
        self.assertIn('docs', result['response'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
