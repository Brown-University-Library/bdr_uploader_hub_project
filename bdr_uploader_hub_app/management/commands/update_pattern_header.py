"""
Updates the pattern header HTML from a remote source.

The raw html is saved to `lib/pattern_header_upstream.html`.

Slight parsing is then done to extract the head and body fragments to ensure valid html after the includes.
- The head fragment is saved to `bdr_uploader_hub_app_templates/includes/pattern_header/head.html`.
- The body fragment is saved to `bdr_uploader_hub_app_templates/includes/pattern_header/body.html`.
- The pattern-header CSS is saved to `static/bdr_student_uploader_hub_app/css/bul_patterns.css`.

Usage:
    uv run ./manage.py update_pattern_header

Notes:
- This update will be run manually only.
- The `PATTERN_HEADER_URL` setting comes from the `.env`.
- The `PATTERN_HEADER_URL` source is considered trusted.
"""

import os
import pathlib
import re
from argparse import ArgumentParser

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand

PATTERN_CSS_STATIC_PATH = 'bdr_student_uploader_hub_app/css/bul_patterns.css'


def resolve_target_paths() -> tuple[pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path]:
    """
    Resolves the target paths for the pattern header files.

    Called by: Command.handle()
    """
    app_dir: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent.parent
    upstream_path: pathlib.Path = app_dir / 'lib' / 'pattern_header_upstream.html'
    template_dir: pathlib.Path = app_dir / 'bdr_uploader_hub_app_templates' / 'includes' / 'pattern_header'
    head_path: pathlib.Path = template_dir / 'head.html'
    body_path: pathlib.Path = template_dir / 'body.html'
    css_path: pathlib.Path = app_dir / 'static' / PATTERN_CSS_STATIC_PATH
    return upstream_path, head_path, body_path, css_path


def resolve_verify_ssl() -> bool:
    """
    Resolves whether SSL certificates should be verified for the pattern-header fetch.

    NOTE:
    - This is a work-around to allow local development while our dev-server's cert is down.
    - It allows the `manage.py` command to be run like:
      `PATTERN_HEADER_VERIFY_SSL=false uv run ./manage.py update_pattern_header`
    - This envar is intentionally not loaded in settings from the `.env`, because this should not be an ongoing issue.

    Called by: Command.handle()
    """
    verify_ssl_raw: str = os.environ.get('PATTERN_HEADER_VERIFY_SSL', 'true')
    verify_ssl: bool = verify_ssl_raw.lower() not in {'0', 'false', 'no'}
    return verify_ssl


def fetch_pattern_header(url: str, verify_ssl: bool = True) -> str:
    """
    Fetches pattern header HTML from the given URL.

    Called by: Command.handle()
    """
    content: str = fetch_url(url, verify_ssl=verify_ssl)
    return content


def fetch_url(url: str, verify_ssl: bool = True) -> str:
    """
    Fetches text content from the given URL.

    Called by: fetch_pattern_header(), fetch_pattern_css()
    """
    response: httpx.Response = httpx.get(url, timeout=30.0, verify=verify_ssl)
    response.raise_for_status()
    return response.text


def extract_pattern_css_link(content: str) -> tuple[str, str]:
    """
    Extracts the pattern CSS link tag and URL from upstream pattern header HTML.

    Called by: split_pattern_header(), Command.handle()
    """
    link_tag = ''
    css_url = ''
    link_pattern = re.compile(
        r'(<link\s+[^>]*href=[\'\"](https://[^\'\"]+/common/css/bul_patterns\.css(?:\?[^\'\"]*)?)[\'\"][^>]*>)',
        re.IGNORECASE,
    )
    match = link_pattern.search(content)

    if match:
        link_tag = match.group(1)
        css_url = match.group(2)

    return link_tag, css_url


def fetch_pattern_css(url: str, verify_ssl: bool = True) -> str:
    """
    Fetches pattern header CSS from the given URL.

    Called by: Command.handle()
    """
    content: str = fetch_url(url, verify_ssl=verify_ssl)
    return content


def split_pattern_header(content: str) -> tuple[str, str]:
    """
    Splits the upstream pattern header into head and body fragments.

    Called by: Command.handle()
    """
    head_content = ''
    body_content = content
    link_tag, css_url = extract_pattern_css_link(content)

    if link_tag and css_url:
        head_content = build_pattern_css_head_content()
        body_content = content.replace(link_tag, '', 1)

    return head_content, body_content


def build_pattern_css_head_content() -> str:
    """
    Builds the template head content for the locally saved pattern CSS.

    Called by: split_pattern_header()
    """
    head_content = f'{{% load static %}}\n<link rel="stylesheet" href="{{% static \'{PATTERN_CSS_STATIC_PATH}\' %}}">\n'
    return head_content


def save_pattern_header(content: str, target_path: pathlib.Path) -> None:
    """
    Saves pattern header HTML to the target file.

    Called by: Command.handle()
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding='utf-8')


class Command(BaseCommand):
    """
    Updates the pattern header HTML from a remote source.
    """

    help = 'Updates the pattern header HTML from PATTERN_HEADER_URL'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds command-line arguments.

        Called by: Django management command runner
        """
        parser.add_argument(
            '--url',
            type=str,
            help='Override URL from settings',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch but do not save',
        )

    def handle(self, *args: object, **options: object) -> None:
        """
        Executes the command.

        Called by: Django management command runner
        """
        ## analyze options ------------------------------------------
        options_dict: dict[str, object] = options
        url_option = options_dict.get('url')
        url_override = url_option if isinstance(url_option, str) else ''
        url: str = url_override or getattr(settings, 'PATTERN_HEADER_URL', '')
        if not url:
            self.stdout.write(self.style.ERROR('PATTERN_HEADER_URL not set in settings and --url not provided'))
            return
        dry_run = bool(options_dict.get('dry_run'))

        ## prep paths -----------------------------------------------
        upstream_path, head_path, body_path, css_path = (
            resolve_target_paths()
        )  # returns tuple[pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path]
        verify_ssl: bool = resolve_verify_ssl()

        ## fetch pattern-header html --------------------------------
        self.stdout.write(f'Fetching pattern header from: {url}')
        if not verify_ssl:
            self.stdout.write(self.style.WARNING('SSL certificate verification is disabled for this fetch'))
        try:
            content = fetch_pattern_header(url, verify_ssl=verify_ssl)
        except httpx.HTTPError as exc:
            self.stdout.write(self.style.ERROR(f'Failed to fetch: {exc}'))
            return
        self.stdout.write(f'Fetched {len(content)} characters')

        ## fetch css ------------------------------------------------
        _, css_url = extract_pattern_css_link(content)
        css_content = ''
        if css_url:
            self.stdout.write(f'Fetching pattern CSS from: {css_url}')
            try:
                css_content = fetch_pattern_css(css_url, verify_ssl=verify_ssl)
            except httpx.HTTPError as exc:
                self.stdout.write(self.style.ERROR(f'Failed to fetch pattern CSS: {exc}'))
                return
            self.stdout.write(f'Fetched {len(css_content)} CSS characters')
        else:
            self.stdout.write(self.style.WARNING('No bul_patterns.css link found in pattern header HTML'))

        ## split pattern-header into head and body ------------------
        head_content, body_content = split_pattern_header(content)

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run - not saving'))
            return

        ## save files -----------------------------------------------
        save_pattern_header(content, upstream_path)
        save_pattern_header(head_content, head_path)
        save_pattern_header(body_content, body_path)
        if css_content:
            save_pattern_header(css_content, css_path)

        self.stdout.write(self.style.SUCCESS(f'Saved upstream snapshot to: {upstream_path}\n'))
        self.stdout.write(self.style.SUCCESS(f'Saved head include to: {head_path}\n'))
        self.stdout.write(self.style.SUCCESS(f'Saved body include to: {body_path}\n'))
        if css_content:
            self.stdout.write(self.style.SUCCESS(f'Saved CSS to: {css_path}\n'))

        ## end def handle()

    ## end class Command()
