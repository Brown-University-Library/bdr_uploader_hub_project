# Test Coverage Assessment and Improvement Plan

2025-Oct-13-Mon -- This document summarizes the current state of tests, highlights gaps, and proposes concrete test additions and small refactors to raise confidence and coverage.

## Prompt

_(given to Windsurf's `GPT-5 (high-reasoning)` model)_

- give me an overview of the comprehensiveness and quality of my test-coverage.
- recommend functions that, without change, are good candidates for tests.
- recommend modules/functions that should have tests even though it would require refactoring.


## Findings: Current Coverage and Quality

- __Strong: MODS XML generation__
  - Tests in `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_mods_maker.py` exercise `ModsMaker.prepare_mods()`, `validate_xml()`, `format_xml()`, and many content paths (authors, advisors/readers, departments, license/access conditions). These are data-driven and provide good confidence.

- __Some coverage: Staff form validation__
  - `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_other.py` includes:
    - `ErrorCheckTest` covering `/error_check/` in both DEBUG and non-DEBUG.
    - `StaffFormDirectTests` for invalid email paths, license/visibility dependencies, and a "valid submission" path that is skipped on CI and depends on the BDR API locally. This path would benefit from mocking to reduce brittleness.

- __Placeholders or stale__
  - `IngestTest` in `test_other.py` contains placeholders (`pass`) for key ingest-prep behaviors.
  - Top-level `test_forms.py` imports `bdr_uploader_hub_stuff.forms.staff_form.StaffForm` and calls `StaffForm._validate_visibility_options`, which do not exist in this project. This file likely doesn’t run or fails discovery. It should be removed or updated and moved under the app’s `tests/` folder._(birkin-note: this is in my dev-box "stuff" dir, from early development; i'll either remove it or move the tests to a better place.)_

## Coverage Breadth Summary

- __Well covered__: `bdr_uploader_hub_app/lib/mods_handler.py`
- __Partially covered__: form validation via `StaffForm` + `validate_staff_form`
- __Little / no direct tests__:
  - `bdr_uploader_hub_app/views.py` (many routes)
  - `bdr_uploader_hub_app/lib/ingester_handler.py`
  - `bdr_uploader_hub_app/lib/uploaded_file_handler.py`
  - `bdr_uploader_hub_app/lib/shib_handler.py`
  - `bdr_uploader_hub_app/lib/version_helper.py`
  - `bdr_uploader_hub_app/lib/config_new_helper.py`
  - `bdr_uploader_hub_app/forms/student_form.py`
  - `bdr_uploader_hub_app/models.py` helpers (property `bdr_url`)

## Quick Wins: Add Tests Without Changing Code

- __lib/ingester_handler.py__
  - `prepare_rights(student_eppn, visibility)`: cover all branches: `public`, `private`, `brown_only_discoverable`, `brown_only_not_discoverable`.
  - `prepare_ir(eppn, email)`: assert dict structure.
  - `prepare_rels(app_config_dict)`: assert mapping from `collection_pid`.
  - `format_mods(unformatted_xml)`: assert pretty-printed output.
  - `parameterize()`: set `self.mods/right/ir/rels/file_data` on `Ingester()` and assert composed JSON strings and keys.

- __lib/uploaded_file_handler.py__
  - `make_checksum(saved_path)`: write a small temp file and assert MD5 and type.
  - `handle_uploaded_file(uploaded_file)`: with `override_settings(MEDIA_ROOT=tempdir)` or by patching `FileSystemStorage.location`, post a small in-memory `UploadedFile`, assert returned `Path` and that the file exists.

- __lib/shib_handler.py__
  - `prep_shib_meta(META, host)`: with `host='testserver'`, verify it returns `settings.TEST_SHIB_META_DCT`; with non-local host, ensure only `Shib*` keys are extracted.
  - `provision_user(shib_metadata)`: with valid metadata, assert user creation and profile update; with missing keys, return `None`.

- __lib/version_helper.py__
  - `make_context(request, rq_now, info_txt, mount_check_txt)`: assert response structure and URL composition.
  - `fetch_mount_data(mount_point)`: mock `subprocess.run` and `django.core.cache.cache` to cover both "mounted" and "not-mounted" paths.

- __lib/config_new_helper.py__
  - `get_configs()`: create a few `AppConfig` rows; assert ordering, links (`config_link`, `upload_link`, `admin_link`) and `items_count`.

- __forms/staff_form_validation.py__
  - `_validate_visibility(form, cleaned_data)`: unit-test combinations that produce each specific error. No network needed.
  - `validate_staff_form(form, cleaned_data)`: mock `httpx.get` to drive BDR responses (success, 404, 5xx) and assert the correct form errors for the PID/title check.

- __views.py__
  - `hlpr_generate_slug`: POST test with `RequestFactory`; assert slugified value in HTML snippet.
  - `root`: assert redirect to `info_url`.
  - `info`: with/without `session['problem_message']` and with `?format=json`, assert response and that the session message is popped.
  - `error_check`: you cover behavior; consider also asserting response body types/messages.

- __models.py__
  - `Submission.bdr_url` property: with and without `bdr_pid`.

## Good Candidates for Tests After Small Refactors

- __forms/staff_form_validation.validate_staff_form__
  - Extract the BDR collection PID/title lookup into a helper, e.g. `fetch_collection_title(pid) -> tuple[str|None, status_code]`, so tests can mock that helper instead of patching `httpx` in multiple places. This also removes local VPN dependency.

- __views.upload and views.upload_slug__
  - Extract pure helpers:
    - `compute_permitted_apps(user_groups, user_email, all_configs) -> list[AppConfig]`
    - `prepare_upload_cleaned_data(cleaned_data, uploaded_file) -> dict`
  - Unit-test these helpers deterministically; keep view tests thin (wiring/redirects).

- __lib/version_helper.GatherCommitAndBranchData__
  - Reading `.git/HEAD` and running `df -h` is harder to test deterministically. Inject file/command readers (e.g., `GitReader`, `SystemReader`) so tests can use fakes without patching the world.

- __lib/ingester_handler.post__
  - Accept an injectable client (default to `httpx`) or callable to enable testing success/failure paths. Also avoid logging an exception on success (see issue below).

- __views.pre_login / logout / shib_login__
  - Move URL-construction to pure helpers; test URL building logic separately from session/middleware coupling.

- __forms/student_form.make_student_form_class__
  - Already testable now by passing config dicts; a future split into small field-builder helpers (`build_license_field`, `build_visibility_field`, etc.) would make granular tests simpler.

## Potential Issues Discovered (Add Tests That Would Expose These)

- __Status default mismatch__
  - `bdr_uploader_hub_app/models.py`: `Submission.status` default is `'created'`, but `STATUS_CHOICES` does not include `'created'`. This is a bug; fix choices or default, and add a regression test.

- __Unconditional exception logging on success__
  - `bdr_uploader_hub_app/lib/ingester_handler.py:278` calls `log.exception(error_message)` even on 200 OK, where `error_message` is empty. Adjust logic; add a unit test for both success and failure paths.

- __Docstring vs behavior mismatch__
  - `ModsMaker.validate_xml()` docstring suggests raising `ValueError`, but implementation returns `True`/`False`. Align docstring with behavior (current tests expect booleans).

- __Unknown field reference in validation__
  - `validate_staff_form()` checks `cleaned_data.get('offer_access_options')`, which isn’t a `StaffForm` field. Clean this up or add the field; add an "empty form" test ensuring behavior remains correct.

- __Single permitted app branch in views.upload__
  - The code for redirecting when exactly one permitted app is found is commented; the code falls through to the multi-app rendering. Add a test to capture intended behavior and restore the redirect.

- __Stale test file__
  - Top-level `test_forms.py` references wrong modules and a non-existent method. Either update it to target `bdr_uploader_hub_app/forms/staff_form_validation.py::_validate_visibility` or remove it. Move any replacement under `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/`.

## How to Measure and Enforce Coverage

- __Run tests__
  - Command: `uv run ./manage.py test` (project root).

- __Optional: coverage report__
  - If desired, add coverage and run:
    - `uv run coverage run ./manage.py test`
    - `uv run coverage html`
    - _(birkin-note: this confused me; the advice is to install the coverage package, <https://coverage.readthedocs.io/en/7.10.7/>)_
  - Consider a `.coveragerc` that focuses on `bdr_uploader_hub_project/` and omits migrations and settings.

### Example `.coveragerc`
```ini
[run]
omit =
    */migrations/*
    */config/*
    */OBSOLETE/*
    */venv*/*

[report]
show_missing = True
skip_covered = True

[html]
directory = htmlcov
```

## Prioritized Next Steps

1) __Fix obvious issues__
- Add `'created'` to `STATUS_CHOICES` or change `Submission.status` default.
- Remove or fix `test_forms.py`; relocate any updated tests into `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/`.
- Stop unconditional `log.exception()` in `Ingester.post`.

2) __Add quick-win unit tests__
- Target `prepare_rights/ir/rels/format_mods/parameterize` in `ingester_handler`.
- Cover `make_checksum` and `handle_uploaded_file`.
- Cover `prep_shib_meta` and `provision_user`.
- Cover `make_context` and `fetch_mount_data` via mocks.
- Cover `get_configs` for links and counts.
- Cover `Submission.bdr_url`, `views.hlpr_generate_slug`, `views.root`, and `views.info`.

3) __De-flake the StaffForm happy path__
- Extract and mock a `fetch_collection_title(pid)` helper used by `validate_staff_form()`; update `StaffFormDirectTests.test_valid_submission` to rely on the helper mock instead of environment/VPN.

## Proposed New Test Modules (Skeleton Names)

- `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_ingester_handler_unit.py`
- `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_uploaded_file_handler.py`
- `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_shib_handler.py`
- `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_version_helper.py`
- `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_config_new_helper.py`
- `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_models_submission.py`
- `bdr_uploader_hub_project/bdr_uploader_hub_app/tests/test_views_simple.py` (for `root`, `info`, `hlpr_generate_slug`)
- Update/replace `test_other.py` to fill in `IngestTest` or move ingest unit tests into `test_ingester_handler_unit.py`.

## Notes

- Keep tests deterministic and fast by mocking network calls (`httpx`) and isolating pure functions where possible.
- Prefer small pure helpers to make logic testable without full Django request/session setup.
- Continue to run tests with: `uv run ./manage.py test`.

---
