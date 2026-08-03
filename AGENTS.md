# AGENTS.md — Repository Agent Instructions (Source of Truth)

This file defines the canonical coding directives for this repository.

If other instruction files exist (Copilot, IDE rules, contributor docs) and conflict with this file, follow this file and treat the others as stale.


## Table of contents

- [Project basics](#project-basics)
- [How to run code](#how-to-run-code)
- [Coding directives (Python)](#coding-directives-python)
- [Django architecture conventions](#django-architecture-conventions)
- [Front-end change guidance](#front-end-change-guidance)
- [Tests](#tests)
- [Change workflow expectations](#change-workflow-expectations)
- [If instructions are missing or ambiguous](#if-instructions-are-missing-or-ambiguous)
- [Agent project index](#agent-project-index)


## Project basics

- Primary language: Python
- Target runtime: Python 3.12 -- unless `pyproject.toml` specifies a different version
- Dependency / execution tool: `uv`
- Project-root is the directory containing this file (and `.git/`, and `.gitignore`).


## How to run code

- Assume user is in the project-root directory.
- Do not use `python` to run scripts.
- Run a script via: `uv run ./path_to_script.py --help`
- Run tests via:
    - `uv run ./run_tests.py`
        - Note that `run_tests.py` has usage instructions about how to run more granular tests.
- Run Django management scripts via: `uv run ./manage.py THE-COMMAND`


## Coding directives (Python)

### Type hints and imports

- Use Python 3.12 type hints everywhere (functions and important variables). (Unless `pyproject.toml` specifies a different version.)
- Prefer builtin generics (e.g., `list[str]`, `dict[str, int]`) over `typing.List` / `typing.Dict`.
- Prefer PEP 604 unions (e.g., `str | None`) over `Optional[str]`.
- Avoid `typing` and `annotations` imports unless strictly necessary.

### Script structure

- Structure runnable modules as:
  - `def main() -> None: ...`
  - `if __name__ == '__main__': main()`
- Keep `main()` simple: parse args / orchestrate calls only.
- Put real logic into top-level helper functions and modules (no nested function definitions).
- Rarely use more than three levels of call depth: `main()` may call helper A, which may call helper B, which may, if necessary, call helper C.

### Functions and control flow

- Prefer single-return functions (use local variables and a final return).
- Do not define functions inside other functions.
- Favor clarity and explicitness over cleverness.

### Logging

- When adding a log statement, when possible, format variable values as a label, followed by a comma and a space, with the value enclosed in double backticks.
- Prefer a label that matches the variable name. For example: `log.debug(f'branch_and_commit, ``{branch_and_commit}``')`

### HTTP and networking

- Use `httpx` for all HTTP calls.
- Do not introduce alternate HTTP libraries (e.g., `requests`, `aiohttp`) unless the repository already depends on them and there is a documented reason.

### Docstrings

- Use triple-quoted docstrings.
- Write docstrings in present tense, with triple-quotes on their own lines.
  - Good:
    ```
    """
    Parses ...
    """
    ```
  - Avoid: `"""Parse ..."""`
- The last line of non-test function docstrings should be: `Called by: the_caller_function()` (or, if in another class/module, `Called by: module.Class.the_caller_function()`)
- Start test-function docstring text with "Checks..."
- For header comments in functions, start the comment with two hashes (e.g., `## does this`).

### Additional coding directives

- Inspect `ruff.toml` for additional coding directives, such as `max-line-length` and `quote-style`.

### Markdown formatting

- Do not use hard line breaks in Markdown files; let paragraphs wrap naturally.
- When creating a Markdown file with more than three top-level `##` headings, add a table of contents near the top with links to those `##` headings.


## Django architecture conventions

### View-layer responsibilities

- `bdr_uploader_hub_app/views.py` should contain **only** view functions that directly handle URL endpoints.
- Every view function in `bdr_uploader_hub_app/views.py` should correspond to an entry in `config/urls.py`.
- Views should act as **manager/orchestrator** functions:
  - Parse request input (query params, POST body, files)
  - Perform minimal validation and shaping of inputs
  - Delegate substantive work to modules under `bdr_uploader_hub_app/lib/`
  - Convert returned results into the appropriate `HttpResponse` (HTML, JSON, redirects)

### Business logic placement

- Put domain logic, integrations, and reusable operations in `bdr_uploader_hub_app/lib/` (not in `views.py`).
- If multiple endpoints share logic, move that shared logic into `bdr_uploader_hub_app/lib/` and keep each view thin.
- Prefer pure, testable functions in `bdr_uploader_hub_app/lib/` that accept plain Python values (not Django request objects) unless passing the request is necessary for a narrow, well-justified reason.

### Imports and dependencies

- `views.py` should primarily import:
  - Django primitives (`HttpRequest`, `HttpResponse`, `render`, `redirect`, etc.)
  - The minimal set of functions/classes from `bdr_uploader_hub_app/lib/` needed for each endpoint
- Avoid creating a secondary abstraction layer inside `views.py` (no view-helper utilities); place helpers in `bdr_uploader_hub_app/lib/`.


## Front-end change guidance

- When front-end changes are required, use JavaScript only where it is truly required.
- Prefer updates in CSS, Python code, or Django template code when those can satisfy the behavior or presentation need.


## Tests

- Use the standard library `unittest` framework (not pytest) for non-Django projects.
- Use Django's test framework for Django projects.
- New behavior should usually come with a focused test covering:
  - the happy path
  - at least one failure / edge case


## Change workflow expectations

When implementing a change (especially from an issue/task):

1. Read relevant surrounding code and match existing conventions.
2. Make the smallest correct change that satisfies the request.
3. Update tests and run: `uv run ./run_tests.py`
4. If you cannot run tests in your environment, still write/adjust tests and state what you would run.

### Commit messages

- Group related files into logical, focused commits; do not require a separate commit for every file.
- Keep each commit message brief, with no more than ten words.
- Write messages in the present tense so they complete the phrase "This commit..." Begin with a fitting verb such as "Adds," "Implements," or "Updates."


## If instructions are missing or ambiguous

- Do not ask questions unless absolutely necessary to proceed.
- Make reasonable assumptions, state them explicitly, then implement.
- If blocked, provide:
  - what you tried
  - what you found in the repository
  - a concrete next step (command, file to edit, or minimal decision needed)


## Agent project index

### Purpose and main flows

- This Django webapp lets authorized staff configure upload portals and lets authorized students stage files and metadata for later Brown Digital Repository ingest.
- Staff configuration flows through `config_new()` and `config_slug()` in `bdr_uploader_hub_app/views.py`; `StaffForm.cleaned_data` is saved in `AppConfig.temp_config_json`.
- Student submission flows through `upload()`, `upload_slug()`, and `student_confirm()` in `bdr_uploader_hub_app/views.py`; the form is created dynamically from the saved app configuration, the primary file is staged, and a `Submission` is created with status `ready_to_ingest`.
- Final ingest starts from the `SubmissionAdmin.ingest` admin action, which delegates to `bdr_uploader_hub_app/lib/ingester_handler.py` to build metadata and file parameters, post to the private BDR API, and update the submission status.

### Where to look

- URL endpoints: `config/urls.py`
- Runtime configuration: `config/settings.py`; test-only configuration: `config/settings_run_tests.py`
- Data models and persisted fields: `bdr_uploader_hub_app/models.py`
- Staff configuration contract: `bdr_uploader_hub_app/forms/staff_form.py` and `bdr_uploader_hub_app/forms/staff_form_validation.py`
- Dynamic student form and submission orchestration: `bdr_uploader_hub_app/forms/student_form.py` and `bdr_uploader_hub_app/views.py`
- Department-to-collection routing: `bdr_uploader_hub_app/lib/department_collection_helper.py` and `bdr_uploader_hub_app/cron_scripts/update_department_map.py`
- Genre normalization and MODS output: `bdr_uploader_hub_app/lib/genre_helper.py`, `bdr_uploader_hub_app/lib/mods_handler.py`, and `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/mods_base.xml`
- File staging and ingest parameters: `bdr_uploader_hub_app/lib/uploaded_file_handler.py` and `bdr_uploader_hub_app/lib/ingester_handler.py`
- Shibboleth provisioning and automatic `UserProfile` creation: `bdr_uploader_hub_app/lib/shib_handler.py`, `bdr_uploader_hub_app/signals.py`, and `bdr_uploader_hub_app/apps.py`
- Pattern-header refresh workflow: `bdr_uploader_hub_app/management/commands/update_pattern_header.py` and the "Updating pattern-header" section of `README.md`

### External boundaries

- Production authentication depends on Shibboleth request metadata; local and test behavior can use `TEST_SHIB_META_DCT`.
- Fixed-collection validation calls the public BDR API. Admin ingest posts to the private BDR API. Post-ingest item links use the configured BDR Studio URL.
- Uploaded files are staged under `MEDIA_ROOT`; ingest rewrites the filename under `BDR_API_FILE_PATH_ROOT`, so the webapp and BDR API must agree on the shared filesystem layout.
- Department-menu routing depends on the JSON file named by `DEPARTMENT_MAP_FILEPATH`; the cron script refreshes it from `DEPARTMENT_MAP_URL` using an atomic file replacement.

### Tests and operational notes

- `uv run ./run_tests.py` uses `config.settings` locally and therefore requires the outer-directory `.env`; GitHub Actions sets `GITHUB_ACTIONS=true`, causing the runner to use `config.settings_run_tests` instead.
- `run_tests.py` accepts module, class, or method labels; read its opening usage block before running a narrow test.
- `StaffFormDirectTests.test_valid_submission()` is intentionally skipped in GitHub Actions but calls a VPN- or server-reachable collection-validation endpoint when run locally or on a server.
- The pattern-header update command is intentionally manual. After refreshing the local snapshot, CSS, and split `head.html` / `body.html` includes, review rendered pages for conflicts before committing.
- CI installs from `uv.lock` with `uv sync --locked` and runs `uv run ./run_tests.py`.

### Gotchas

- Treat `AppConfig.temp_config_json` as a persisted data contract. Renaming keys or changing value shapes can break existing configured upload portals, dynamic student forms, or MODS generation.
- `hlpr_check_name_and_slug()` is not a read-only uniqueness check; it creates the `AppConfig` row before redirecting staff to the full configuration form.
- `upload_slug()` stores submission data in the `student_form_data` session key. `student_confirm()` removes `accessibility_agreement` before persistence because that checkbox is a submission-time gate, not descriptive metadata.
- Collection routing has two modes: fixed collection data comes from the app configuration, while department-menu mode stores a submission-level `target_collection_pid`; ingest prefers the submission-level PID and falls back to the app-level PID.
- `config/settings.py` asserts that the outer-directory `.env` exists during import. Never copy secret values from that file into this public repository or into `AGENTS.md`; use `example.env` only to understand variable names and shapes.
- `README.md` currently shows the stale app label `bdr_student_uploader_hub_app` in its `makemigrations` example; the actual Django app label is `bdr_uploader_hub_app`.
- `ruff.toml` currently retains `target-version = "py38"`, but `pyproject.toml` is the runtime authority and requires Python 3.12.
- `bdr_uploader_hub_app/lib/OLD_version_helper.py` is retained history; active version endpoint code imports `bdr_uploader_hub_app/lib/version_helper.py`.
- `send_ingest_success_email()` in `bdr_uploader_hub_app/lib/emailer.py` currently logs inputs but does not send email.

---
