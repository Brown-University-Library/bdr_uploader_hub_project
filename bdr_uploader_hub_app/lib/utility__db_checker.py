#!/usr/bin/env python3
"""
Checks that a SQLite database schema matches the Django models for this project.

Usage:
    From the project root, run:
        uv run ./bdr_uploader_hub_app/lib/utility__db_checker.py

    To check a specific sqlite file:
        uv run ./bdr_uploader_hub_app/lib/utility__db_checker.py --db-path ../DBs/bdr_uploader_hub_project.sqlite

    To limit the check to a different Django app label:
        uv run ./bdr_uploader_hub_app/lib/utility__db_checker.py --app-label some_app

Notes:
    - The script opens the SQLite database in read-only mode.
    - It compares Django model expectations against actual SQLite tables, columns, foreign keys, and indexes.
    - Exit-status `0` means no problems were found; exit-status `1` means one or more mismatches were found.
"""

import argparse
import os
import pathlib
import sqlite3
import sys
from dataclasses import dataclass


PROJECT_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class ColumnExpectation:
    """
    Stores the expected shape of a model-backed database column.
    Called by: build_model_expectation()
    """

    name: str
    allows_null: bool
    is_primary_key: bool
    is_unique: bool
    field_class_name: str


@dataclass(frozen=True)
class ForeignKeyExpectation:
    """
    Stores the expected shape of a database foreign-key constraint.
    Called by: build_model_expectation()
    """

    column_name: str
    target_table: str
    target_column: str


@dataclass(frozen=True)
class IndexExpectation:
    """
    Stores the expected shape of a database index.
    Called by: build_model_expectation()
    """

    columns: tuple[str, ...]
    is_unique: bool
    source: str


@dataclass(frozen=True)
class ModelExpectation:
    """
    Stores the expected schema details for one Django model.
    Called by: collect_model_expectations()
    """

    label: str
    table_name: str
    columns: dict[str, ColumnExpectation]
    foreign_keys: dict[str, ForeignKeyExpectation]
    indexes: list[IndexExpectation]


@dataclass(frozen=True)
class ActualColumn:
    """
    Stores the actual shape of a SQLite table column.
    Called by: fetch_table_columns()
    """

    name: str
    allows_null: bool
    is_primary_key: bool
    declared_type: str


@dataclass(frozen=True)
class ActualForeignKey:
    """
    Stores the actual shape of a SQLite foreign-key constraint.
    Called by: fetch_table_foreign_keys()
    """

    column_name: str
    target_table: str
    target_column: str


@dataclass(frozen=True)
class ActualIndex:
    """
    Stores the actual shape of a SQLite index.
    Called by: fetch_table_indexes()
    """

    name: str
    columns: tuple[str, ...]
    is_unique: bool
    origin: str


def configure_django(settings_module: str) -> None:
    """
    Configures Django so model metadata can be inspected.
    Called by: main()
    """
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    django.setup()
    return


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments.
    Called by: main()
    """
    parser = argparse.ArgumentParser(description='Checks whether a SQLite database schema matches Django models.')
    parser.add_argument(
        '--db-path',
        help='Optional path to the sqlite database file. Defaults to DATABASES["default"]["NAME"] from settings.',
    )
    parser.add_argument(
        '--settings-module',
        default='config.settings',
        help='Django settings module to load. Default: config.settings',
    )
    parser.add_argument(
        '--app-label',
        default='bdr_uploader_hub_app',
        help='Django app label whose managed models and migrations should be checked. Default: bdr_uploader_hub_app',
    )
    parser.add_argument(
        '--show-ok',
        action='store_true',
        help='Also print tables, columns, and indexes that match expectations.',
    )
    args: argparse.Namespace = parser.parse_args()
    return args


def resolve_database_path(db_path_argument: str | None) -> pathlib.Path:
    """
    Resolves the database filepath from an argument or Django settings.
    Called by: main()
    """
    configured_name: str
    if db_path_argument:
        configured_name = db_path_argument
    else:
        from django.conf import settings

        default_db: dict = settings.DATABASES['default']
        engine: str = default_db.get('ENGINE', '')
        if engine != 'django.db.backends.sqlite3':
            raise ValueError(f'expected sqlite engine, got `{engine}`')
        configured_name = str(default_db.get('NAME', '')).strip()
        if configured_name == '':
            raise ValueError('DATABASES["default"]["NAME"] is empty')

    db_path: pathlib.Path = pathlib.Path(configured_name).expanduser()
    if not db_path.is_absolute():
        db_path = (PROJECT_ROOT / db_path).resolve()
    return db_path


def open_readonly_connection(db_path: pathlib.Path) -> sqlite3.Connection:
    """
    Opens a sqlite connection in read-only mode.
    Called by: main()
    """
    if db_path.exists() is False:
        raise FileNotFoundError(f'database file does not exist: `{db_path}`')
    connection: sqlite3.Connection = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def fetch_table_names(connection: sqlite3.Connection) -> set[str]:
    """
    Fetches non-internal SQLite table names.
    Called by: evaluate_database()
    """
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
    """
    rows = connection.execute(query).fetchall()
    table_names: set[str] = {row['name'] for row in rows}
    return table_names


def fetch_table_columns(connection: sqlite3.Connection, table_name: str) -> dict[str, ActualColumn]:
    """
    Fetches column details for one SQLite table.
    Called by: evaluate_database()
    """
    rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    columns: dict[str, ActualColumn] = {}
    for row in rows:
        column = ActualColumn(
            name=row['name'],
            allows_null=not bool(row['notnull']),
            is_primary_key=bool(row['pk']),
            declared_type=str(row['type'] or ''),
        )
        columns[column.name] = column
    return columns


def fetch_table_foreign_keys(connection: sqlite3.Connection, table_name: str) -> dict[str, ActualForeignKey]:
    """
    Fetches foreign-key details for one SQLite table.
    Called by: evaluate_database()
    """
    rows = connection.execute(f'PRAGMA foreign_key_list("{table_name}")').fetchall()
    foreign_keys: dict[str, ActualForeignKey] = {}
    for row in rows:
        foreign_key = ActualForeignKey(
            column_name=row['from'],
            target_table=row['table'],
            target_column=row['to'],
        )
        foreign_keys[foreign_key.column_name] = foreign_key
    return foreign_keys


def fetch_table_indexes(connection: sqlite3.Connection, table_name: str) -> list[ActualIndex]:
    """
    Fetches index details for one SQLite table.
    Called by: evaluate_database()
    """
    rows = connection.execute(f'PRAGMA index_list("{table_name}")').fetchall()
    indexes: list[ActualIndex] = []
    for row in rows:
        index_name: str = row['name']
        index_rows = connection.execute(f'PRAGMA index_info("{index_name}")').fetchall()
        ordered_columns: list[str] = [index_row['name'] for index_row in sorted(index_rows, key=lambda item: item['seqno'])]
        if len(ordered_columns) == 0:
            continue
        indexes.append(
            ActualIndex(
                name=index_name,
                columns=tuple(ordered_columns),
                is_unique=bool(row['unique']),
                origin=str(row['origin']),
            )
        )
    return indexes


def collect_model_expectations(app_label: str) -> list[ModelExpectation]:
    """
    Collects expected schema details from managed Django models.
    Called by: main()
    """
    from django.apps import apps

    app_config = apps.get_app_config(app_label)
    expectations: list[ModelExpectation] = []
    for model in app_config.get_models():
        if model._meta.managed is False or model._meta.proxy:
            continue
        expectations.append(build_model_expectation(model))
    expectations.sort(key=lambda item: item.table_name)
    return expectations


def build_model_expectation(model: type[object]) -> ModelExpectation:
    """
    Builds the expected schema details for one model.
    Called by: collect_model_expectations()
    """
    from django.db import models

    columns: dict[str, ColumnExpectation] = {}
    foreign_keys: dict[str, ForeignKeyExpectation] = {}
    indexes: list[IndexExpectation] = []

    for field in model._meta.local_fields:
        column_name: str = str(field.column)
        columns[column_name] = ColumnExpectation(
            name=column_name,
            allows_null=bool(field.null),
            is_primary_key=bool(field.primary_key),
            is_unique=bool(field.unique),
            field_class_name=field.__class__.__name__,
        )

        if field.db_index and field.primary_key is False and field.unique is False:
            indexes.append(IndexExpectation(columns=(column_name,), is_unique=False, source=f'field:{field.name}'))

        if field.unique and field.primary_key is False:
            indexes.append(IndexExpectation(columns=(column_name,), is_unique=True, source=f'unique-field:{field.name}'))

        if field.is_relation and getattr(field, 'many_to_one', False):
            target_field = field.target_field
            foreign_keys[column_name] = ForeignKeyExpectation(
                column_name=column_name,
                target_table=field.remote_field.model._meta.db_table,
                target_column=str(target_field.column),
            )

    for model_index in model._meta.indexes:
        indexes.append(
            IndexExpectation(
                columns=tuple(model_index.fields),
                is_unique=False,
                source=f'meta-index:{model_index.name}',
            )
        )

    for constraint in model._meta.constraints:
        if isinstance(constraint, models.UniqueConstraint):
            indexes.append(
                IndexExpectation(
                    columns=tuple(constraint.fields),
                    is_unique=True,
                    source=f'unique-constraint:{constraint.name}',
                )
            )

    expectation = ModelExpectation(
        label=model._meta.label,
        table_name=model._meta.db_table,
        columns=columns,
        foreign_keys=foreign_keys,
        indexes=deduplicate_index_expectations(indexes),
    )
    return expectation


def deduplicate_index_expectations(indexes: list[IndexExpectation]) -> list[IndexExpectation]:
    """
    Deduplicates index expectations while preserving the first source label.
    Called by: build_model_expectation()
    """
    deduplicated: list[IndexExpectation] = []
    seen: set[tuple[tuple[str, ...], bool]] = set()
    for index in indexes:
        key = (index.columns, index.is_unique)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(index)
    return deduplicated


def compare_columns(
    expectation: ModelExpectation,
    actual_columns: dict[str, ActualColumn],
    show_ok: bool,
) -> tuple[list[str], list[str], list[str]]:
    """
    Compares expected columns against actual SQLite columns.
    Called by: evaluate_database()
    """
    errors: list[str] = []
    warnings: list[str] = []
    oks: list[str] = []

    expected_column_names: set[str] = set(expectation.columns.keys())
    actual_column_names: set[str] = set(actual_columns.keys())

    for column_name in sorted(expected_column_names - actual_column_names):
        expected_field = expectation.columns[column_name]
        errors.append(
            f'ERROR: missing column `{expectation.table_name}.{column_name}` '
            f'(expected by {expectation.label}, field-type `{expected_field.field_class_name}`)'
        )

    for column_name in sorted(actual_column_names - expected_column_names):
        warnings.append(f'WARNING: extra column `{expectation.table_name}.{column_name}` exists in the database')

    for column_name in sorted(expected_column_names & actual_column_names):
        expected_column = expectation.columns[column_name]
        actual_column = actual_columns[column_name]

        if expected_column.allows_null != actual_column.allows_null:
            errors.append(
                f'ERROR: nullability mismatch on `{expectation.table_name}.{column_name}` '
                f'(model allows_null={expected_column.allows_null}; db allows_null={actual_column.allows_null})'
            )
            continue

        if expected_column.is_primary_key != actual_column.is_primary_key:
            errors.append(
                f'ERROR: primary-key mismatch on `{expectation.table_name}.{column_name}` '
                f'(model is_primary_key={expected_column.is_primary_key}; '
                f'db is_primary_key={actual_column.is_primary_key})'
            )
            continue

        if show_ok:
            oks.append(
                f'OK: column `{expectation.table_name}.{column_name}` matches '
                f'(declared_type `{actual_column.declared_type or "unknown"}`)'
            )

    return errors, warnings, oks


def compare_foreign_keys(
    expectation: ModelExpectation,
    actual_foreign_keys: dict[str, ActualForeignKey],
    show_ok: bool,
) -> tuple[list[str], list[str]]:
    """
    Compares expected foreign keys against actual SQLite foreign keys.
    Called by: evaluate_database()
    """
    errors: list[str] = []
    oks: list[str] = []

    for column_name in sorted(expectation.foreign_keys.keys()):
        expected_foreign_key = expectation.foreign_keys[column_name]
        actual_foreign_key = actual_foreign_keys.get(column_name)
        if actual_foreign_key is None:
            errors.append(
                f'ERROR: missing foreign key on `{expectation.table_name}.{column_name}` '
                f'to `{expected_foreign_key.target_table}.{expected_foreign_key.target_column}`'
            )
            continue

        if (
            expected_foreign_key.target_table != actual_foreign_key.target_table
            or expected_foreign_key.target_column != actual_foreign_key.target_column
        ):
            errors.append(
                f'ERROR: foreign-key mismatch on `{expectation.table_name}.{column_name}` '
                f'(model -> `{expected_foreign_key.target_table}.{expected_foreign_key.target_column}`; '
                f'db -> `{actual_foreign_key.target_table}.{actual_foreign_key.target_column}`)'
            )
            continue

        if show_ok:
            oks.append(
                f'OK: foreign key `{expectation.table_name}.{column_name}` -> '
                f'`{actual_foreign_key.target_table}.{actual_foreign_key.target_column}`'
            )

    return errors, oks


def compare_indexes(
    expectation: ModelExpectation,
    actual_indexes: list[ActualIndex],
    show_ok: bool,
) -> tuple[list[str], list[str], list[str]]:
    """
    Compares expected indexes against actual SQLite indexes.
    Called by: evaluate_database()
    """
    errors: list[str] = []
    warnings: list[str] = []
    oks: list[str] = []

    actual_index_keys: set[tuple[tuple[str, ...], bool]] = {
        (index.columns, index.is_unique)
        for index in actual_indexes
    }
    expected_index_keys: set[tuple[tuple[str, ...], bool]] = {
        (index.columns, index.is_unique)
        for index in expectation.indexes
    }

    for expected_index in expectation.indexes:
        key = (expected_index.columns, expected_index.is_unique)
        if key not in actual_index_keys:
            qualifier = 'unique index' if expected_index.is_unique else 'index'
            errors.append(
                f'ERROR: missing {qualifier} on `{expectation.table_name}` columns {list(expected_index.columns)} '
                f'(source `{expected_index.source}`)'
            )
            continue
        if show_ok:
            qualifier = 'unique index' if expected_index.is_unique else 'index'
            oks.append(f'OK: {qualifier} exists on `{expectation.table_name}` columns {list(expected_index.columns)}')

    for actual_index in actual_indexes:
        if actual_index.origin == 'pk':
            continue
        key = (actual_index.columns, actual_index.is_unique)
        if key not in expected_index_keys:
            warnings.append(
                f'WARNING: extra index `{actual_index.name}` exists on `{expectation.table_name}` '
                f'columns {list(actual_index.columns)} (unique={actual_index.is_unique}, origin=`{actual_index.origin}`)'
            )

    return errors, warnings, oks


def evaluate_database(
    connection: sqlite3.Connection,
    expectations: list[ModelExpectation],
    show_ok: bool,
) -> tuple[list[str], list[str], list[str]]:
    """
    Evaluates actual SQLite schema details against model expectations.
    Called by: main()
    """
    errors: list[str] = []
    warnings: list[str] = []
    oks: list[str] = []

    table_names: set[str] = fetch_table_names(connection)

    for expectation in expectations:
        if expectation.table_name not in table_names:
            errors.append(f'ERROR: missing table `{expectation.table_name}` for model `{expectation.label}`')
            continue

        if show_ok:
            oks.append(f'OK: table `{expectation.table_name}` exists')

        actual_columns = fetch_table_columns(connection, expectation.table_name)
        actual_foreign_keys = fetch_table_foreign_keys(connection, expectation.table_name)
        actual_indexes = fetch_table_indexes(connection, expectation.table_name)

        column_errors, column_warnings, column_oks = compare_columns(expectation, actual_columns, show_ok)
        foreign_key_errors, foreign_key_oks = compare_foreign_keys(expectation, actual_foreign_keys, show_ok)
        index_errors, index_warnings, index_oks = compare_indexes(expectation, actual_indexes, show_ok)

        errors.extend(column_errors)
        errors.extend(foreign_key_errors)
        errors.extend(index_errors)
        warnings.extend(column_warnings)
        warnings.extend(index_warnings)
        oks.extend(column_oks)
        oks.extend(foreign_key_oks)
        oks.extend(index_oks)

    return errors, warnings, oks


def print_report(
    db_path: pathlib.Path,
    app_label: str,
    expectations: list[ModelExpectation],
    errors: list[str],
    warnings: list[str],
    oks: list[str],
) -> None:
    """
    Prints a concise, human-readable validation report.
    Called by: main()
    """
    print(f'Database: {db_path}')
    print(f'App label: {app_label}')
    print(f'Models checked: {len(expectations)}')
    print('')

    if len(errors) == 0:
        print('RESULT: PASS')
    else:
        print('RESULT: FAIL')
    print('')

    if len(errors):
        print('Problems:')
        for item in errors:
            print(item)
        print('')

    if len(warnings):
        print('Warnings:')
        for item in warnings:
            print(item)
        print('')

    if len(oks):
        print('Matches:')
        for item in oks:
            print(item)
        print('')
    return


def main() -> None:
    """
    Orchestrates argument parsing, schema inspection, and reporting.
    Called by: __main__
    """
    args = parse_args()
    configure_django(args.settings_module)
    db_path = resolve_database_path(args.db_path)

    expectations = collect_model_expectations(args.app_label)
    with open_readonly_connection(db_path) as connection:
        schema_errors, schema_warnings, schema_oks = evaluate_database(connection, expectations, args.show_ok)

    all_errors: list[str] = schema_errors
    all_warnings: list[str] = schema_warnings
    all_oks: list[str] = schema_oks if args.show_ok else []

    print_report(
        db_path=db_path,
        app_label=args.app_label,
        expectations=expectations,
        errors=all_errors,
        warnings=all_warnings,
        oks=all_oks,
    )

    if len(all_errors):
        raise SystemExit(1)
    return


if __name__ == '__main__':
    main()
