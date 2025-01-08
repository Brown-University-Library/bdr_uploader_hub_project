import logging

from django.urls import reverse

from bdr_deposits_uploader_app.models import AppConfig

log = logging.getLogger(__name__)


def get_existing_names_and_slugs() -> list[tuple[str, ...]]:
    """
    Returns a list of app names.
    Called by views.config_new().
    """
    apps = AppConfig.objects.values_list('name', 'slug')
    names: tuple[str, ...]  # elipsis indicates the tuple can contain any number of elements
    slugs: tuple[str, ...]
    names, slugs = zip(*apps)
    return [names, slugs]


def get_recent_configs() -> list:
    """
    Shows the recent configs.
    Dummy implementation for now.
    Called by views.config_new().
    """
    log.debug('Showing recent configs')
    dummy_data = [
        {
            'mod_date': '2024-12-03 16:29:59.746846',
            'name': 'Med-School Posters',
            'items_count': 250,
            'config_link': f'{reverse("config_slug_url", args=["med-school-posters"])}',
            'upload_link': f'{reverse("upload_slug_url", args=["med-school-posters"])}',
        },
        {
            'mod_date': '2024-11-03 16:29:59.746846',
            'name': 'UTRA Posters',
            'items_count': 5000,
            'config_link': f'{reverse("config_slug_url", args=["utra-posters"])}',
            'upload_link': f'{reverse("upload_slug_url", args=["utra-posters"])}',
        },
        {
            'mod_date': '2024-10-03 16:29:59.746846',
            'name': 'Watson Capstones',
            'items_count': 75,
            'config_link': f'{reverse("config_slug_url", args=["watson-capstones"])}',
            'upload_link': f'{reverse("upload_slug_url", args=["watson-capstones"])}',
        },
        {
            'mod_date': '2024-11-04 16:29:59.746846',
            'name': 'BDH Oral Histories',
            'items_count': 100,
            'config_link': f'{reverse("config_slug_url", args=["bdh-oral-histories"])}',
            'upload_link': f'{reverse("upload_slug_url", args=["bdh-oral-histories"])}',
        },
        {
            'mod_date': '2024-08-03 16:29:59.746846',
            'name': 'Rites & Reason Images',
            'items_count': 125,
            'config_link': f'{reverse("config_slug_url", args=["rites-reason-images"])}',
            'upload_link': f'{reverse("upload_slug_url", args=["rites-reason-images"])}',
        },
    ]
    ## sort dict by date descending
    dummy_data.sort(key=lambda x: x['mod_date'], reverse=True)
    return dummy_data

    ## end def get_recent_collections()
