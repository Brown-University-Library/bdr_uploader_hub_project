from pathlib import Path
import sys
import subprocess
from datetime import datetime

def manage_update(project_path: str) -> None:
    '''
    Main function to manage the update process for the project's dependencies.
    Calls various helper functions to validate, compile, compare, sync, and update permissions.
    '''
    validate_project_path(project_path)
    project_path: Path = Path(project_path).resolve()
    python_version: str = infer_python_version(project_path)
    backup_file: Path = compile_requirements(project_path, python_version)
    if not compare_with_previous_backup(project_path, backup_file):
        return
    activate_and_sync_dependencies(project_path, backup_file)
    update_permissions_and_mark_active(project_path, backup_file)
    print('Dependencies updated successfully.')

def validate_project_path(project_path: str) -> None:
    '''
    Validate that the provided project path exists.
    Exits the script if the path is invalid.
    '''
    if not Path(project_path).exists():
        print(f'Error: The provided path '{project_path}' does not exist.')
        sys.exit(1)

def infer_python_version(project_path: Path) -> str:
    '''
    Determine the Python version from the virtual environment in the project.
    Exits the script if the virtual environment or Python version is invalid.
    '''
    env_python_path: Path = project_path.parent / 'env/bin/python3'
    if not env_python_path.exists():
        print('Error: Virtual environment not found.')
        sys.exit(1)

    python_version: str = subprocess.check_output([str(env_python_path), '--version'], text=True).strip().split()[-1]
    if not python_version.startswith('3.'):
        print('Error: Invalid Python version.')
        sys.exit(1)
    return python_version

def compile_requirements(project_path: Path, python_version: str) -> Path:
    '''
    Compile the project's requirements.in file into a versioned requirements.txt backup.
    Returns the path to the newly created backup file.
    '''
    timestamp: str = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    backup_dir: Path = project_path.parent / 'requirements_backups'
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file: Path = backup_dir / f'requirements_{timestamp}.txt'
    requirements_in: Path = project_path / 'requirements.in'

    compile_command: list[str] = [
        'uv', 'pip', 'compile', str(requirements_in),
        '--output-file', str(backup_file),
        '--universal', '--python', python_version
    ]

    try:
        subprocess.run(compile_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error during pip compile: {e}')
        sys.exit(1)

    return backup_file

def compare_with_previous_backup(project_path: Path, backup_file: Path) -> bool:
    '''
    Compare the newly created requirements backup with the most recent previous backup.
    Returns False if there are no changes, True otherwise.
    '''
    backup_dir: Path = project_path.parent / 'requirements_backups'
    previous_files: list[Path] = sorted([
        f for f in backup_dir.iterdir() if f.suffix == '.txt' and f != backup_file
    ])

    if previous_files:
        previous_file_path: Path = previous_files[-1]
        with previous_file_path.open() as prev, backup_file.open() as curr:
            if prev.read() == curr.read():
                print('No changes detected in dependencies.')
                return False
    return True

def activate_and_sync_dependencies(project_path: Path, backup_file: Path) -> None:
    '''
    Activate the virtual environment and sync dependencies using the provided backup file.
    Exits the script if any command fails.
    '''
    activate_script: Path = project_path / 'env/bin/activate'
    if not activate_script.exists():
        print('Error: Activate script not found.')
        sys.exit(1)

    activate_command: str = f'source {activate_script}'
    sync_command: list[str] = [
        'uv', 'pip', 'sync', str(backup_file)
    ]

    try:
        subprocess.run(activate_command, shell=True, check=True, executable='/bin/bash')
        subprocess.run(sync_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error during pip sync: {e}')
        sys.exit(1)

def update_permissions_and_mark_active(project_path: Path, backup_file: Path) -> None:
    '''
    Update group ownership and permissions for relevant directories.
    Mark the backup file as active by adding a header comment.
    '''
    backup_dir: Path = project_path.parent / 'requirements_backups'
    for path in [project_path / 'env', backup_dir]:
        subprocess.run(['chgrp', '-R', 'foo', str(path)], check=True)
        subprocess.run(['chmod', '-R', 'g+rw', str(path)], check=True)

    with backup_file.open('r') as file:
        content: list[str] = file.readlines()
    content.insert(0, '# ACTIVE\n')

    with backup_file.open('w') as file:
        file.writelines(content)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python update_packages.py <project_path>')
        sys.exit(1)

    project_path: str = sys.argv[1]
    manage_update(project_path)
