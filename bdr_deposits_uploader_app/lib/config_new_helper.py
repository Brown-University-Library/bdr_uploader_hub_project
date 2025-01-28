import logging
from urllib.parse import urlencode

from django.urls import reverse

from bdr_deposits_uploader_app.models import AppConfig

log = logging.getLogger(__name__)


def get_existing_names_and_slugs() -> list[tuple[str, ...]]:
    """
    Returns a list of app names.
    Called by views.hlpr_check_name_and_slug().
    """
    apps = AppConfig.objects.values_list('name', 'slug')
    names: tuple[str, ...]  # elipsis indicates the tuple can contain any number of elements
    slugs: tuple[str, ...]
    names, slugs = zip(*apps)
    return [names, slugs]


def get_configs() -> list:
    """
    Returns a list of app names and slugs. Will replace get_recent_configs() soon.
    Called by views.config_new().
    """
    log.debug('starting get_configs()')
    existing_app_data: list = []
    apps = AppConfig.objects.all()
    if apps:
        app_label = apps[0]._meta.app_label
        log.debug(f'app_label, ``{app_label}``')
        # model_name = apps[0]._meta.model_name
        # log.debug(f'model_name, ``{model_name}``')
        base_admin_url = reverse('admin:bdr_deposits_uploader_app_submission_changelist')
        log.debug(f'base_admin_url, ``{base_admin_url}``')
        for app in apps:
            app_data: dict = {}
            mod_date_without_microseconds: str = app.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            app_data['mod_date'] = mod_date_without_microseconds
            app_data['name'] = app.name
            submission_count_for_app = app.submission_set.count()
            app_data['items_count'] = submission_count_for_app
            app_data['config_link'] = f'{reverse("config_slug_url", args=[app.slug])}'
            app_data['upload_link'] = f'{reverse("upload_slug_url", args=[app.slug])}'
            # app_data['admin_link'] = reverse(
            #     f'admin:{app_label}_{model_name}_change', args=[app.id]
            # )  # works, but not what I want

            query_params = {'app__id__exact': str(app.id)}
            full_admin_url = f'{base_admin_url}?{urlencode(query_params)}'
            app_data['admin_link'] = full_admin_url

            existing_app_data.append(app_data)
    else:
        log.debug('no apps found')

    log.debug(f'existing_app_data, ``{existing_app_data}``')
    return existing_app_data


# def get_configs() -> list:
#     """
#     Returns a list of app names and slugs. Will replace get_recent_configs() soon.
#     Called by views.config_new().
#     """
#     log.debug('starting get_configs()')
#     existing_app_data: list = []
#     apps = AppConfig.objects.all()
#     app_label = apps[0]._meta.app_label
#     log.debug(f'app_label, ``{app_label}``')
#     # model_name = apps[0]._meta.model_name
#     # log.debug(f'model_name, ``{model_name}``')
#     base_admin_url = reverse('admin:bdr_deposits_uploader_app_submission_changelist')
#     log.debug(f'base_admin_url, ``{base_admin_url}``')
#     for app in apps:
#         app_data: dict = {}
#         mod_date_without_microseconds: str = app.updated_at.strftime('%Y-%m-%d %H:%M:%S')
#         app_data['mod_date'] = mod_date_without_microseconds
#         app_data['name'] = app.name
#         submission_count_for_app = app.submission_set.count()
#         app_data['items_count'] = submission_count_for_app
#         app_data['config_link'] = f'{reverse("config_slug_url", args=[app.slug])}'
#         app_data['upload_link'] = f'{reverse("upload_slug_url", args=[app.slug])}'
#         # app_data['admin_link'] = reverse(
#         #     f'admin:{app_label}_{model_name}_change', args=[app.id]
#         # )  # works, but not what I want

#         query_params = {'app__id__exact': str(app.id)}
#         full_admin_url = f'{base_admin_url}?{urlencode(query_params)}'
#         app_data['admin_link'] = full_admin_url

#         existing_app_data.append(app_data)

#     log.debug(f'existing_app_data, ``{existing_app_data}``')
#     return existing_app_data


# def get_recent_configs() -> list:
#     """
#     Shows the recent configs.
#     Dummy implementation for now.
#     Called by views.config_new().
#     """
#     log.debug('Showing recent configs')
#     dummy_data = [
#         {
#             'mod_date': '2024-12-03 16:29:59.746846',
#             'name': 'Med-School Posters',
#             'items_count': 250,
#             'config_link': f'{reverse("config_slug_url", args=["med-school-posters"])}',
#             'upload_link': f'{reverse("upload_slug_url", args=["med-school-posters"])}',
#         },
#         {
#             'mod_date': '2024-11-03 16:29:59.746846',
#             'name': 'UTRA Posters',
#             'items_count': 5000,
#             'config_link': f'{reverse("config_slug_url", args=["utra-posters"])}',
#             'upload_link': f'{reverse("upload_slug_url", args=["utra-posters"])}',
#         },
#         {
#             'mod_date': '2024-10-03 16:29:59.746846',
#             'name': 'Watson Capstones',
#             'items_count': 75,
#             'config_link': f'{reverse("config_slug_url", args=["watson-capstones"])}',
#             'upload_link': f'{reverse("upload_slug_url", args=["watson-capstones"])}',
#         },
#         {
#             'mod_date': '2024-11-04 16:29:59.746846',
#             'name': 'BDH Oral Histories',
#             'items_count': 100,
#             'config_link': f'{reverse("config_slug_url", args=["bdh-oral-histories"])}',
#             'upload_link': f'{reverse("upload_slug_url", args=["bdh-oral-histories"])}',
#         },
#         {
#             'mod_date': '2024-08-03 16:29:59.746846',
#             'name': 'Rites & Reason Images',
#             'items_count': 125,
#             'config_link': f'{reverse("config_slug_url", args=["rites-reason-images"])}',
#             'upload_link': f'{reverse("upload_slug_url", args=["rites-reason-images"])}',
#         },
#     ]
#     ## sort dict by date descending
#     dummy_data.sort(key=lambda x: x['mod_date'], reverse=True)
#     return dummy_data

## end def get_recent_collections()
