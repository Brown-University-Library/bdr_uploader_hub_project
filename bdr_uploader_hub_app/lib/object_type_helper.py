from __future__ import annotations

import logging

from django.conf import settings

log = logging.getLogger(__name__)


DEFAULT_OBJECT_TYPE_KEY = 'none'


def _normalize_object_type_options() -> dict[str, dict]:
    """
    Normalizes settings.OBJECT_TYPE_OPTIONS into a dict keyed by menu_label.

    Called by: build_object_type_choices(), get_default_object_type_entry(), get_object_type_entry()
    """
    normalized: dict[str, dict] = {}
    raw_options = getattr(settings, 'OBJECT_TYPE_OPTIONS', [])
    if not isinstance(raw_options, list):
        msg = 'OBJECT_TYPE_OPTIONS must be a list of dicts.'
        raise ValueError(msg)

    for entry in raw_options:
        if not isinstance(entry, dict):
            msg = 'OBJECT_TYPE_OPTIONS entries must be dicts.'
            raise ValueError(msg)
        menu_label = str(entry.get('menu_label', '')).strip()
        if not menu_label:
            msg = 'OBJECT_TYPE_OPTIONS entries must include menu_label.'
            raise ValueError(msg)
        normalized[menu_label] = entry

    return normalized


def build_object_type_choices() -> list[tuple[str, str]]:
    """
    Builds sorted staff-form choices from settings.OBJECT_TYPE_OPTIONS.

    Called by: bdr_uploader_hub_app.forms.staff_form.StaffForm.__init__()
    """
    object_type_map = _normalize_object_type_options()
    choices = sorted([(key, key) for key in object_type_map], key=lambda item: item[0])
    return choices


def get_default_object_type_entry() -> dict:
    """
    Returns the default object type entry.

    Called by: get_object_type_entry(), bdr_uploader_hub_app.forms.staff_form.StaffForm.__init__()
    """
    object_type_map = _normalize_object_type_options()
    default_entry = object_type_map.get(DEFAULT_OBJECT_TYPE_KEY)
    if default_entry is None:
        msg = f'Default object type key {DEFAULT_OBJECT_TYPE_KEY!r} is missing from OBJECT_TYPE_OPTIONS.'
        raise ValueError(msg)
    return default_entry


def get_object_type_entry(stored_object_type_entry: dict | str | None) -> dict:
    """
    Returns a valid object type entry, defaulting to none when no stored entry exists.

    Called by: bdr_uploader_hub_app.forms.staff_form_validation.validate_staff_form(), bdr_uploader_hub_app.lib.ingester_handler.Ingester.prepare_rels()
    """
    object_type_map = _normalize_object_type_options()
    if not stored_object_type_entry:
        return get_default_object_type_entry()

    if isinstance(stored_object_type_entry, str):
        menu_label = stored_object_type_entry.strip()
    elif isinstance(stored_object_type_entry, dict):
        menu_label = str(stored_object_type_entry.get('menu_label', '')).strip()
    else:
        msg = 'Object type selection must be a menu_label string or dict entry.'
        raise ValueError(msg)

    if not menu_label:
        return get_default_object_type_entry()

    object_type_entry = object_type_map.get(menu_label)
    if object_type_entry is None:
        msg = f'Unknown object type menu_label: {menu_label}'
        raise ValueError(msg)
    return object_type_entry
