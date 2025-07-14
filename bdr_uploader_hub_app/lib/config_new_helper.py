import logging
from urllib.parse import urlencode

from django.db.models.functions import Lower
from django.urls import reverse

from bdr_uploader_hub_app.models import AppConfig

log = logging.getLogger(__name__)


def get_configs() -> list:
    """
    Returns a list of app names and slugs.
    Called by views.config_new().
    """
    log.debug('starting get_configs()')
    existing_app_data: list = []

    apps = AppConfig.objects.order_by(Lower('name'))
    if apps:
        app_label = apps[0]._meta.app_label
        log.debug(f'app_label, ``{app_label}``')
        # model_name = apps[0]._meta.model_name
        # log.debug(f'model_name, ``{model_name}``')
        base_admin_url = reverse('admin:bdr_uploader_hub_app_submission_changelist')
        log.debug(f'base_admin_url, ``{base_admin_url}``')
        for app in apps:
            app_data: dict = {}
            mod_date_without_microseconds: str = app.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            app_data['mod_date'] = mod_date_without_microseconds
            app_data['name'] = app.name
            submission_count_for_app = app.submission_set.count()
            app_data['items_count'] = submission_count_for_app
            app_data['config_link'] = f'{reverse("staff_config_slug_url", args=[app.slug])}'
            app_data['upload_link'] = f'{reverse("student_upload_slug_url", args=[app.slug])}'
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

    ## end def get_configs()
