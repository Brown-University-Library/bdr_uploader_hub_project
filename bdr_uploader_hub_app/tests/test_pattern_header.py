from unittest.mock import Mock, patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase as TestCase

from bdr_uploader_hub_app.management.commands import update_pattern_header


class PatternHeaderSplitTest(TestCase):
    """
    Checks split_pattern_header parsing.
    """

    def test_split_pattern_header_extracts_link_tag(self) -> None:
        """
        Checks split_pattern_header() extracts and rewrites the bul_patterns.css link tag.
        """
        link_tag = '<link rel="stylesheet" href="https://example.edu/common/css/bul_patterns.css" />'
        content = '\n'.join(
            [
                '<!-- begin bul_pl_header -->',
                link_tag,
                '<div id="bul_pl_header_begin">',
                'header content',
                '</div>',
            ]
        )

        head_content, body_content = update_pattern_header.split_pattern_header(content)

        self.assertIn('{% load static %}', head_content)
        self.assertIn("{% static 'bdr_student_uploader_hub_app/css/bul_patterns.css' %}", head_content)
        self.assertNotIn('https://example.edu/common/css/bul_patterns.css', head_content)
        self.assertNotIn('bul_patterns.css', body_content)
        self.assertIn('header content', body_content)

    def test_split_pattern_header_preserves_django_tag(self) -> None:
        """
        Checks split_pattern_header() preserves Django template tags.
        """
        link_tag = '<link rel="stylesheet" href="https://example.edu/common/css/bul_patterns.css" />'
        content = '\n'.join(
            [
                '<!-- begin bul_pl_header -->',
                link_tag,
                '<a href="{% url "info_url" %}">About</a>',
                '</div>',
            ]
        )

        head_content, body_content = update_pattern_header.split_pattern_header(content)

        self.assertIn("{% static 'bdr_student_uploader_hub_app/css/bul_patterns.css' %}", head_content)
        self.assertNotIn(link_tag, head_content)
        self.assertIn('{% url "info_url" %}', body_content)

    def test_split_pattern_header_extracts_link_tag_with_query(self) -> None:
        """
        Checks split_pattern_header() extracts a link tag with query params.
        """
        link_tag = '<link href="https://static.example.edu/common/css/bul_patterns.css?v=3" rel="stylesheet">'
        content = '\n'.join(
            [
                '<!-- begin bul_pl_header -->',
                link_tag,
                '<div id="bul_pl_header_begin">',
                'header content',
                '</div>',
            ]
        )

        head_content, body_content = update_pattern_header.split_pattern_header(content)

        self.assertIn("{% static 'bdr_student_uploader_hub_app/css/bul_patterns.css' %}", head_content)
        self.assertNotIn('https://static.example.edu/common/css/bul_patterns.css?v=3', head_content)
        self.assertNotIn('bul_patterns.css', body_content)

    def test_extract_pattern_css_link_returns_link_and_url(self) -> None:
        """
        Checks extract_pattern_css_link() returns the upstream CSS link tag and URL.
        """
        link_tag = '<link rel="stylesheet" href="https://example.edu/common/css/bul_patterns.css?v=3" />'
        content = f'{link_tag}\n<div>header</div>'

        parsed_link_tag, css_url = update_pattern_header.extract_pattern_css_link(content)

        self.assertEqual(link_tag, parsed_link_tag)
        self.assertEqual('https://example.edu/common/css/bul_patterns.css?v=3', css_url)


class PatternHeaderFetchTest(TestCase):
    """
    Checks pattern-header fetch configuration.
    """

    def test_resolve_verify_ssl_defaults_to_true(self) -> None:
        """
        Checks SSL certificate verification defaults to enabled.
        """
        with patch.dict('os.environ', {}, clear=True):
            verify_ssl = update_pattern_header.resolve_verify_ssl()

        self.assertTrue(verify_ssl)

    def test_resolve_verify_ssl_accepts_false_values(self) -> None:
        """
        Checks SSL certificate verification can be disabled by environment variable.
        """
        for value in ['0', 'false', 'no', 'FALSE']:
            with patch.dict('os.environ', {'PATTERN_HEADER_VERIFY_SSL': value}, clear=True):
                verify_ssl = update_pattern_header.resolve_verify_ssl()

            self.assertFalse(verify_ssl)

    @patch('bdr_uploader_hub_app.management.commands.update_pattern_header.httpx.get')
    def test_fetch_pattern_header_passes_verify_ssl_to_httpx(self, mock_get: Mock) -> None:
        """
        Checks fetch_url() passes the SSL verification setting to httpx.
        """
        mock_response = Mock()
        mock_response.text = 'pattern header'
        mock_get.return_value = mock_response

        content = update_pattern_header.fetch_url('https://example.edu/header.html', verify_ssl=False)

        self.assertEqual(content, 'pattern header')
        mock_get.assert_called_once_with('https://example.edu/header.html', timeout=30.0, verify=False)
        mock_response.raise_for_status.assert_called_once_with()

    def test_build_pattern_css_head_content_uses_local_static_path(self) -> None:
        """
        Checks build_pattern_css_head_content() uses the local static CSS path.
        """
        head_content = update_pattern_header.build_pattern_css_head_content()

        self.assertIn('{% load static %}', head_content)
        self.assertIn("{% static 'bdr_student_uploader_hub_app/css/bul_patterns.css' %}", head_content)


class PatternHeaderTemplateTest(TestCase):
    """
    Checks base template pattern-header integration.
    """

    def test_base_template_renders_local_unauthenticated_header_links(self) -> None:
        """
        Checks base.html renders the app title and unauthenticated login links.
        """
        rendered = render_to_string('base.html', {})

        self.assertIn('BDR Uploader Hub', rendered)
        self.assertIn('Student Login', rendered)
        self.assertIn('Staff Login', rendered)
        self.assertIn('href="/login/?type=student"', rendered)
        self.assertIn('href="/login/?type=staff"', rendered)
        self.assertIn('class="bdr-app-header"', rendered)
        self.assertNotIn('font-awesome', rendered)
        self.assertNotIn('fa-book-open', rendered)
