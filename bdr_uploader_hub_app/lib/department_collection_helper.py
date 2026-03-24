import json
import logging
from pathlib import Path

from django.conf import settings

log = logging.getLogger(__name__)

FIXED_COLLECTION_MODE = 'fixed_collection'
DEPARTMENT_COLLECTION_MENU_MODE = 'department_collection_menu'
COLLECTION_ASSIGNMENT_MODE_CHOICES = [
    (FIXED_COLLECTION_MODE, 'Fixed collection'),
    (DEPARTMENT_COLLECTION_MENU_MODE, 'Department collection menu'),
]


def get_collection_assignment_mode(config_data: dict) -> str:
    """
    Returns the normalized collection-assignment mode.

    Called by: make_student_form_class()
    """
    mode = config_data.get('collection_assignment_mode') or FIXED_COLLECTION_MODE
    if mode not in {FIXED_COLLECTION_MODE, DEPARTMENT_COLLECTION_MENU_MODE}:
        mode = FIXED_COLLECTION_MODE
    return mode


def load_department_collection_data() -> dict[str, object]:
    """
    Loads and validates the configured department collection mapping file.

    Called by: build_department_collection_choices()
    """
    filepath_value = getattr(settings, 'DEPARTMENT_MAP_FILEPATH', '')
    if not filepath_value:
        msg = 'DEPARTMENT_MAP_FILEPATH is not configured.'
        raise ValueError(msg)

    filepath = Path(filepath_value)
    if not filepath.exists():
        msg = f'Department map file does not exist: {filepath}'
        raise ValueError(msg)

    try:
        raw_data: object = json.loads(filepath.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        msg = f'Department map file contains invalid JSON: {exc}'
        raise ValueError(msg) from exc

    if isinstance(raw_data, dict):
        err_value = raw_data.get('err')
        if err_value:
            msg = f'Department map file reports an error: {err_value}'
            raise ValueError(msg)
        raw_data = raw_data.get('results', raw_data)

    if not isinstance(raw_data, list):
        msg = 'Department map file must contain a list of entries or an object with a results list.'
        raise ValueError(msg)

    choices: list[tuple[str, str]] = [('', '---------')]
    label_by_value: dict[str, str] = {}
    pid_by_value: dict[str, str] = {}
    seen_labels: set[str] = set()

    for entry in raw_data:
        if not isinstance(entry, dict):
            msg = 'Department map entries must be objects.'
            raise ValueError(msg)

        label = str(entry.get('text', '')).strip()
        raw_id = str(entry.get('id', '')).strip()
        if not label or not raw_id:
            msg = 'Department map entries must include non-empty text and id values.'
            raise ValueError(msg)

        if '\t' not in raw_id:
            msg = f'Department map id is missing a tab-delimited collection pid: {raw_id}'
            raise ValueError(msg)

        collection_pid = raw_id.split('\t')[-1].strip()
        if not collection_pid:
            msg = f'Department map id is missing a usable collection pid: {raw_id}'
            raise ValueError(msg)

        if label in seen_labels:
            msg = f'Duplicate department label found: {label}'
            raise ValueError(msg)
        if raw_id in label_by_value:
            msg = f'Duplicate department id found: {raw_id}'
            raise ValueError(msg)

        seen_labels.add(label)
        label_by_value[raw_id] = label
        pid_by_value[raw_id] = collection_pid
        choices.append((raw_id, label))

    if len(choices) == 1:
        msg = 'Department map file does not contain any usable entries.'
        raise ValueError(msg)

    data: dict[str, object] = {
        'choices': choices,
        'label_by_value': label_by_value,
        'pid_by_value': pid_by_value,
    }
    return data


def build_department_collection_choices() -> list[tuple[str, str]]:
    """
    Returns student-form choices for the department collection dropdown.

    Called by: make_student_form_class()
    """
    data = load_department_collection_data()
    choices: list[tuple[str, str]] = data['choices']  # type: ignore[assignment]
    return choices


def resolve_department_collection_choice(choice_value: str) -> tuple[str, str]:
    """
    Resolves a submitted department menu value to display label and collection pid.

    Called by: add_department_collection_submission_data()
    """
    normalized_choice_value = choice_value.strip()
    data = load_department_collection_data()
    label_by_value: dict[str, str] = data['label_by_value']  # type: ignore[assignment]
    pid_by_value: dict[str, str] = data['pid_by_value']  # type: ignore[assignment]

    if normalized_choice_value not in label_by_value or normalized_choice_value not in pid_by_value:
        msg = 'Selected department collection choice is invalid.'
        raise ValueError(msg)

    result = (label_by_value[normalized_choice_value], pid_by_value[normalized_choice_value])
    return result


def add_department_collection_submission_data(config_data: dict, student_data: dict) -> dict:
    """
    Adds resolved department-collection routing data to the submission payload.

    Called by: upload_slug()
    """
    updated_student_data = student_data.copy()
    mode = get_collection_assignment_mode(config_data)
    if mode == DEPARTMENT_COLLECTION_MENU_MODE:
        choice_value = str(updated_student_data.get('department_collection_choice', '')).strip()
        if not choice_value:
            msg = 'A department collection choice is required.'
            raise ValueError(msg)
        label, collection_pid = resolve_department_collection_choice(choice_value)
        updated_student_data['department_collection_label'] = label
        updated_student_data['target_collection_pid'] = collection_pid
    return updated_student_data
