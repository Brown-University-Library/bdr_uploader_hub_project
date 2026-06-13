from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import SimpleTestCase as TestCase

from bdr_uploader_hub_app.management.commands import update_pattern_header


class PatternHeaderSplitTest(TestCase):
    """
    Checks split_pattern_header parsing.
    """

    def test_split_pattern_header_extracts_link_tag(self) -> None:
        """
        Checks split_pattern_header() extracts the bul_patterns.css link tag.
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

        head_soup = BeautifulSoup(head_content, 'html.parser')
        parsed_link = head_soup.find('link')
        self.assertIsNotNone(parsed_link)
        self.assertEqual(
            parsed_link.get('href'),
            'https://example.edu/common/css/bul_patterns.css',
        )
        self.assertEqual(parsed_link.get('rel'), ['stylesheet'])
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

        self.assertIn(link_tag, head_content)
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

        head_soup = BeautifulSoup(head_content, 'html.parser')
        parsed_link = head_soup.find('link')
        self.assertIsNotNone(parsed_link)
        self.assertEqual(
            parsed_link.get('href'),
            'https://static.example.edu/common/css/bul_patterns.css?v=3',
        )
        self.assertEqual(parsed_link.get('rel'), ['stylesheet'])
        self.assertNotIn('bul_patterns.css', body_content)


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
