import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
)

log = logging.getLogger(__name__)


def infer_environment_type() -> str:
    """
    Infers the environment type based on the system hostname.
    Returns 'local', 'staging', or 'production'.
    """
    hostname: str = subprocess.check_output(['hostname'], text=True).strip()
    if hostname.startswith('d') or hostname.startswith('q'):
        env_type: str = 'staging'
    elif hostname.startswith('p'):
        env_type: str = 'production'
    else:
        env_type: str = 'local'
    log.debug(f'env_type: {env_type}')
    return env_type


def validate_project_path(project_path: str) -> None:
    """
    Validate that the provided project path exists.
    Exits the script if the path is invalid.
    """
    log.debug('starting validate_project_path()')
    if not Path(project_path).exists():
        message = f'Error: The provided project_path ``{project_path}`` does not exist.'
        log.exception(message)
        raise Exception(message)


def activate_virtualenv(project_path: Path) -> None:
    """
    Activates the virtual environment for the project.
    """
    log.debug('starting activate_virtualenv()')
    activate_script: Path = (project_path / '../env/bin/activate').resolve()
    log.debug(f'activate_script: ``{activate_script}``')
    if not activate_script.exists():
        message = 'Error: Activate script not found.'
        log.exception(message)
        raise Exception(message)

    activate_command: str = f'source {activate_script}'
    try:
        subprocess.run(activate_command, shell=True, check=True, executable='/bin/bash')
    except subprocess.CalledProcessError:
        message = 'Error activating virtual environment'
        log.exception(message)
        raise Exception(message)


def infer_python_version(project_path: Path) -> str:
    """
    Determine the Python version from the virtual environment in the project.
    Exits the script if the virtual environment or Python version is invalid.
    """
    log.debug('starting infer_python_version()')
    env_python_path: Path = project_path.parent / 'env/bin/python3'
    if not env_python_path.exists():
        message = 'Error: Virtual environment not found.'
        log.exception(message)
        raise Exception(message)

    python_version: str = subprocess.check_output([str(env_python_path), '--version'], text=True).strip().split()[-1]
    if not python_version.startswith('3.'):
        message = 'Error: Invalid Python version.'
        log.exception(message)
        raise Exception(message)
    return python_version


def compile_requirements(project_path: Path, python_version: str, environment_type: str) -> Path:
    """
    Compile the project's requirements.in file into a versioned requirements.txt backup.
    Returns the path to the newly created backup file.
    """
    log.debug('starting compile_requirements()')
    activate_virtualenv(project_path)
    log.debug('virtual-enviroment activated.')

    timestamp: str = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    backup_dir: Path = project_path.parent / 'requirements_backups'
    log.debug(f'backup_dir: ``{backup_dir}``')
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file: Path = backup_dir / f'{environment_type}_{timestamp}.txt'
    log.debug(f'backup_file: ``{backup_file}``')

    requirements_in: Path = project_path / 'requirements' / f'{environment_type}.in'  # local.in, staging.in, production.in
    log.debug(f'requirements.in path, ``{requirements_in}``')

    compile_command: list[str] = [
        'uv',
        'pip',
        'compile',
        str(requirements_in),
        '--output-file',
        str(backup_file),
        '--universal',
        '--python',
        python_version,
    ]

    try:
        subprocess.run(compile_command, check=True)
    except subprocess.CalledProcessError:
        message = 'Error during pip compile'
        log.exception(message)
        raise Exception(message)

    return backup_file


def remove_old_backups(backup_dir: Path, keep_recent: int = 7) -> None:
    """
    Removes all files in the backup directory except the most recent `keep_recent` files.
    """
    log.debug('starting remove_old_backups()')
    backups: list[Path] = sorted([f for f in backup_dir.iterdir() if f.is_file() and f.suffix == '.txt'], reverse=True)
    old_backups: list[Path] = backups[keep_recent:]

    for old_backup in old_backups:
        log.debug(f'removing old backup: {old_backup}')
        old_backup.unlink()


def compare_with_previous_backup(project_path: Path, backup_file: Path) -> bool:
    """
    Compare the newly created requirements backup with the most recent previous backup.
    Excludes line 2 (timestamp line) from the comparison.
    Returns False if there are no changes, True otherwise.
    """
    log.debug('starting compare_with_previous_backup()')
    backup_dir: Path = project_path.parent / 'requirements_backups'
    previous_files: list[Path] = sorted([f for f in backup_dir.iterdir() if f.suffix == '.txt' and f != backup_file])

    if previous_files:
        previous_file_path: Path = previous_files[-1]
        with previous_file_path.open() as prev, backup_file.open() as curr:
            prev_lines = prev.readlines()
            curr_lines = curr.readlines()

            # Exclude line 2 from comparison
            prev_lines_filtered = prev_lines[:1] + prev_lines[2:]
            curr_lines_filtered = curr_lines[:1] + curr_lines[2:]

            if prev_lines_filtered == curr_lines_filtered:
                log.debug('no differences found in dependencies.')
                return False
    return True


def activate_and_sync_dependencies(project_path: Path, backup_file: Path) -> None:
    """
    Activate the virtual environment and sync dependencies using the provided backup file.
    Exits the script if any command fails.
    """
    log.debug('starting activate_and_sync_dependencies()')
    activate_virtualenv(project_path)

    sync_command: list[str] = ['uv', 'pip', 'sync', str(backup_file)]

    try:
        subprocess.run(sync_command, check=True)
    except subprocess.CalledProcessError:
        message = 'Error during pip sync'
        log.exception(message)
        raise Exception(message)


def update_permissions_and_mark_active(project_path: Path, backup_file: Path) -> None:
    """
    Update group ownership and permissions for relevant directories.
    Mark the backup file as active by adding a header comment.
    """
    log.debug('starting update_permissions_and_mark_active()')
    backup_dir: Path = project_path.parent / 'requirements_backups'
    for path in [project_path / 'env', backup_dir]:
        subprocess.run(['chgrp', '-R', 'foo', str(path)], check=True)
        subprocess.run(['chmod', '-R', 'g+rw', str(path)], check=True)

    with backup_file.open('r') as file:
        content: list[str] = file.readlines()
    content.insert(0, '# ACTIVE\n')

    with backup_file.open('w') as file:
        file.writelines(content)


def manage_update(project_path: str) -> None:
    """
    Main function to manage the update process for the project's dependencies.
    Calls various helper functions to validate, compile, compare, sync, and update permissions.
    """
    log.debug('starting manage_update()')
    environment_type: str = infer_environment_type()
    validate_project_path(project_path)
    project_path: Path = Path(project_path).resolve()
    python_version: str = infer_python_version(project_path)
    backup_file: Path = compile_requirements(project_path, python_version, environment_type)
    backup_dir: Path = project_path.parent / 'requirements_backups'
    remove_old_backups(backup_dir)
    differences_found: bool = compare_with_previous_backup(project_path, backup_file)
    if not differences_found:
        log.debug('no differences found in dependencies; exiting.')
        return
    else:  # differences
        activate_and_sync_dependencies(project_path, backup_file)
        update_permissions_and_mark_active(project_path, backup_file)
        log.debug('dependencies updated successfully.')


if __name__ == '__main__':
    log.debug('starting dundermain')
    if len(sys.argv) != 2:
        print('Usage: python update_packages.py <project_path>')
        sys.exit(1)

    project_path: str = sys.argv[1]
    manage_update(project_path)
