import logging

from django.conf import settings

log = logging.getLogger(__name__)


DEFAULT_GENRE_KEY = 'document'


def _normalize_genre_options() -> dict[str, dict]:
    """
    Normalizes settings.GENRE_OPTIONS into a dict keyed by menu_label.

    Called by: build_genre_choices(), get_default_genre_entry(), get_genre_entry()
    """
    normalized: dict[str, dict] = {}
    raw_options = getattr(settings, 'GENRE_OPTIONS', [])
    if not isinstance(raw_options, list):
        msg = 'GENRE_OPTIONS must be a list of dicts.'
        raise ValueError(msg)

    for entry in raw_options:
        if not isinstance(entry, dict):
            msg = 'GENRE_OPTIONS entries must be dicts.'
            raise ValueError(msg)
        menu_label = str(entry.get('menu_label', '')).strip()
        if not menu_label:
            msg = 'GENRE_OPTIONS entries must include menu_label.'
            raise ValueError(msg)
        normalized[menu_label] = entry

    return normalized


def build_genre_choices() -> list[tuple[str, str]]:
    """
    Builds sorted staff-form choices from settings.GENRE_OPTIONS.

    Called by: bdr_uploader_hub_app.forms.staff_form.StaffForm.__init__()
    """
    genre_map = _normalize_genre_options()
    choices = sorted([(key, key) for key in genre_map], key=lambda item: item[0])
    return choices


def get_default_genre_entry() -> dict:
    """
    Returns the default genre entry.

    Called by: get_genre_entry(), bdr_uploader_hub_app.forms.staff_form.StaffForm.__init__()
    """
    genre_map = _normalize_genre_options()
    default_entry = genre_map.get(DEFAULT_GENRE_KEY)
    if default_entry is None:
        msg = f'Default genre key {DEFAULT_GENRE_KEY!r} is missing from GENRE_OPTIONS.'
        raise ValueError(msg)
    return default_entry


def get_genre_entry(stored_genre_entry: dict | str | None) -> dict:
    """
    Returns a valid genre entry, defaulting to document when no stored entry exists.

    Called by: bdr_uploader_hub_app.lib.mods_handler.ModsMaker.prepare_mods()
    """
    genre_map = _normalize_genre_options()
    if not stored_genre_entry:
        return get_default_genre_entry()

    if isinstance(stored_genre_entry, str):
        menu_label = stored_genre_entry.strip()
    elif isinstance(stored_genre_entry, dict):
        menu_label = str(stored_genre_entry.get('menu_label', '')).strip()
    else:
        msg = 'Genre selection must be a menu_label string or dict entry.'
        raise ValueError(msg)

    if not menu_label:
        return get_default_genre_entry()

    genre_entry = genre_map.get(menu_label)
    if genre_entry is None:
        msg = f'Unknown genre menu_label: {menu_label}'
        raise ValueError(msg)
    return genre_entry
