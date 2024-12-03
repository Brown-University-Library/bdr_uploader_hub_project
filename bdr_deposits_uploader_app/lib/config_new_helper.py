import logging

log = logging.getLogger(__name__)


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
            'config_link': 'http://127.0.0.1/config/med-school-posters/',
            'upload_link': 'http://127.0.0.1/upload/med-school-posters/',
        },
        {
            'mod_date': '2024-11-03 16:29:59.746846',
            'name': 'UTRA Posters',
            'items_count': 5000,
            'config_link': 'http://127.0.0.1/config/utra-posters/',
            'upload_link': 'http://127.0.0.1/upload/utra-posters/',
        },
        {
            'mod_date': '2024-10-03 16:29:59.746846',
            'name': 'Watson Capstones',
            'items_count': 75,
            'config_link': 'http://127.0.0.1/config/watson-capstones/',
            'upload_link': 'http://127.0.0.1/upload/watson-capstones/',
        },
        {
            'mod_date': '2024-11-04 16:29:59.746846',
            'name': 'BDH Oral Histories',
            'items_count': 100,
            'config_link': 'http://127.0.0.1/config/bdh-oral-histories/',
            'upload_link': 'http://127.0.0.1/upload/bdh-oral-histories/',
        },
        {
            'mod_date': '2024-08-03 16:29:59.746846',
            'name': 'Rites & Reason Images',
            'items_count': 125,
            'config_link': 'http://127.0.0.1/config/rites-reason-images/',
            'upload_link': 'http://127.0.0.1/upload/rites-reason-images/',
        },
    ]
    ## sort dict by date descending
    dummy_data.sort(key=lambda x: x['mod_date'], reverse=True)
    return dummy_data

    ## end def get_recent_collections()
