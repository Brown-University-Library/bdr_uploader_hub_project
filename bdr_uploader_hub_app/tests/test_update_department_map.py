import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase

from bdr_uploader_hub_app.cron_scripts.update_department_map import fetch_departments_map, write_departments_map


class FetchDepartmentsMapTest(SimpleTestCase):
    """
    Checks the department-map fetch and write helpers.
    """

    @mock.patch('bdr_uploader_hub_app.cron_scripts.update_department_map.httpx.get')
    def test_fetch_departments_map_sorts_by_text(self, mock_get):
        """
        Checks that the fetched department list is sorted by the `text` field.
        """
        mock_response = mock.Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {'id': '2', 'text': 'Zoology'},
            {'id': '1', 'text': 'Anthropology'},
            {'id': '3', 'text': 'Biology'},
        ]
        mock_get.return_value = mock_response

        result = fetch_departments_map()

        self.assertEqual(['Anthropology', 'Biology', 'Zoology'], [item['text'] for item in result])

    def test_write_departments_map_writes_pretty_json(self):
        """
        Checks that the department mapping is written as JSON to the target filepath.
        """
        departments = [
            {'id': '1', 'text': 'Anthropology'},
            {'id': '2', 'text': 'Biology'},
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            filepath = Path(tempdir) / 'department-map.json'
            write_departments_map(filepath, departments)

            written = json.loads(filepath.read_text(encoding='utf-8'))
            self.assertTrue(filepath.exists())

        self.assertEqual(departments, written)


if __name__ == '__main__':
    unittest.main()
