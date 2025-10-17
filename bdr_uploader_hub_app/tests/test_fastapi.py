import unittest
from unittest.mock import MagicMock, patch

import httpx
from django.test import TestCase

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
    def test_parse_normalizes(self):
        data = {
            'response': {
                'docs': [
                    {'idroot': '123', 'auth': 'World Bank', 'type': 'topic'},
                    {'idroot': 456, 'auth': ['Economics'], 'type': ['topic']},
                    {'idroot': '789', 'suggestall': ['Fallback Label'], 'type': ''},
                    {'idroot': '', 'auth': 'No ID should be dropped'},
                    'not a dict',
                ]
            }
        }
        result = fastapi.parse_response(data)
        self.assertIsInstance(result, list)
        # Should keep only entries with label and fast_id
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['label'], 'World Bank')
        self.assertEqual(result[0]['fast_id'], '123')
        self.assertEqual(result[0]['type'], 'topic')
        self.assertEqual(result[1]['label'], 'Economics')
        self.assertEqual(result[1]['fast_id'], '456')
        self.assertEqual(result[1]['type'], 'topic')
        self.assertEqual(result[2]['label'], 'Fallback Label')
        self.assertEqual(result[2]['fast_id'], '789')


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
            payload = {'response': {'docs': [{'idroot': '1', 'auth': 'Bar', 'type': 'topic'}]}}
            return httpx.Response(status_code=200, request=request, json=payload)

        fake_httpx_client.send = send_ok
        mock_get_client.return_value = fake_httpx_client

        # Act
        result = fastapi.manage_oclc_fastapi_call('bar')

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn('suggestions', result)
        self.assertEqual(len(result['suggestions']), 1)
        self.assertEqual(result['suggestions'][0]['label'], 'Bar')


class TestCheckOclcFastApiView(TestCase):
    def test_short_query_returns_prompt(self):
        resp = self.client.get('/check_oclc_fastapi/', {'q': 'a'})
        self.assertEqual(200, resp.status_code)
        self.assertIn('Type at least 2 characters', resp.content.decode('utf-8'))

    @patch('bdr_uploader_hub_app.views.manage_oclc_fastapi_call')
    def test_view_returns_suggestions(self, mock_mgr):
        mock_mgr.return_value = {
            'suggestions': [
                {'label': 'World Bank', 'fast_id': '123', 'type': 'topic'},
                {'label': 'Economics', 'fast_id': '456', 'type': 'topic'},
            ]
        }
        resp = self.client.get('/check_oclc_fastapi/', {'q': 'world'})
        self.assertEqual(200, resp.status_code)
        text = resp.content.decode('utf-8')
        self.assertIn('World Bank', text)
        self.assertIn('FAST 123', text)
        self.assertIn('Economics', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
