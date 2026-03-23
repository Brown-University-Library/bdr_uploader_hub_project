"""
Fetches the Brown departments mapping and writes it to a JSON file.

Called by: main()

Usage:
    cd /path/to/bdr_uploader_hub_project/
    uv run --env-file="/path/to/.env" "./bdr_uploader_hub_app/cron_scripts/update_department_map.py"
"""

import json
import os
import pathlib
import tempfile

import httpx


def fetch_departments_map(department_map_url: str) -> list[dict[str, object]]:
    """
    Fetches the departments mapping from the Brown repository service.

    Called by: main()
    """
    response = httpx.get(department_map_url, timeout=30.0)
    response.raise_for_status()
    data: object = response.json()

    if isinstance(data, dict):
        data = data.get('results', data.get('items', data.get('data')))

    if not isinstance(data, list):
        msg = f'Expected a list from {department_map_url}, got {type(data).__name__}'
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
    temp_filepath: pathlib.Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=filepath.parent,
            delete=False,
            prefix=f'.{filepath.name}.',
            suffix='.tmp',
        ) as temp_file:
            temp_filepath = pathlib.Path(temp_file.name)
            temp_file.write(f'{serialized}\n')
            temp_file.flush()
            os.fsync(temp_file.fileno())

        if filepath.exists():
            existing_stat = filepath.stat()
            os.chmod(temp_filepath, existing_stat.st_mode)

        os.replace(temp_filepath, filepath)

        dir_fd = os.open(filepath.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    except Exception:
        if temp_filepath is not None:
            temp_filepath.unlink(missing_ok=True)
        raise


def main() -> None:
    """
    Orchestrates the fetch-and-write workflow.

    Called by: __main__
    """
    department_map_url = os.environ.get('DEPARTMENT_MAP_URL')
    if not department_map_url:
        msg = 'DEPARTMENT_MAP_URL is not set'
        raise RuntimeError(msg)

    output_filepath = os.environ.get('DEPARTMENT_MAP_FILEPATH')
    if not output_filepath:
        msg = 'DEPARTMENT_MAP_FILEPATH is not set'
        raise RuntimeError(msg)

    filepath = pathlib.Path(output_filepath)
    departments = fetch_departments_map(department_map_url)
    write_departments_map(filepath, departments)


if __name__ == '__main__':
    main()
