"""
Fetches the Brown departments mapping and writes it to a JSON file.

Called by: main()
"""

import json
import os
import pathlib

import httpx

DEPARTMENTS_URL = 'https://repository.library.brown.edu/services/departments-select2/'


def fetch_departments_map() -> list[dict[str, object]]:
    """
    Fetches the departments mapping from the Brown repository service.

    Called by: main()
    """
    response = httpx.get(DEPARTMENTS_URL, timeout=30.0)
    response.raise_for_status()
    data: object = response.json()
    if not isinstance(data, list):
        msg = f'Expected a list from {DEPARTMENTS_URL}, got {type(data).__name__}'
        raise ValueError(msg)

    departments: list[dict[str, object]] = []
    for item in data:
        if not isinstance(item, dict):
            msg = f'Expected each department entry to be a dict, got {type(item).__name__}'
            raise ValueError(msg)
        departments.append(item)

    departments.sort(key=lambda item: str(item.get('text', item.get('id', ''))).casefold())
    return departments


def write_departments_map(filepath: pathlib.Path, departments: list[dict[str, object]]) -> None:
    """
    Writes the departments mapping to disk as sorted JSON.

    Called by: main()
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(departments, indent=2, sort_keys=True, ensure_ascii=False)
    filepath.write_text(f'{serialized}\n', encoding='utf-8')


def main() -> None:
    """
    Orchestrates the fetch-and-write workflow.

    Called by: __main__
    """
    output_filepath = os.environ.get('DEPARTMENT_MAP_FILEPATH')
    if not output_filepath:
        msg = 'DEPARTMENT_MAP_FILEPATH is not set'
        raise RuntimeError(msg)

    filepath = pathlib.Path(output_filepath)
    departments = fetch_departments_map()
    write_departments_map(filepath, departments)


if __name__ == '__main__':
    main()
