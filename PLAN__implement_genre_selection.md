# Plan: Implement staff-configurable genre selection

## Recent Prompt

Add a staff-only configuration field named `Assigned Genre` to the `Basics` section of the staff-config form. The selected menu value should be persisted with the app configuration and later used during MODS rendering so that `<mods:genre ...>` is generated from environment-backed settings instead of the current hard-coded template value.

- Review `bdr_uploader_hub_project/AGENTS.md` for coding-directives to follow.

- Review `bdr_uploader_hub_project/README.md` for an overview of the project.

- Review `bdr_uploader_hub_project/PLAN__implement_genre_selection.md` to understand what to do.

- Implement the plan.

- Prepend this prompt to the `## Recent Prompt` section of the `bdr_uploader_hub_project/PLAN__implement_genre_selection.md`.

Plan improvements...

- You're write that my description of the envar was incorrect -- the json represents a list of dicts. Remove references to the errant description to avoid confusion.

- If pre-existing data does not include this genre info -- assume the default 'document' information.

- Update the `bdr_uploader_hub_project/PLAN__implement_genre_selection.md` plan with this feedback.

- Prepend this prompt to the `## Recent Prompt` section of the `bdr_uploader_hub_project/PLAN__implement_genre_selection.md`.

Plan improvements...

- I'm changing the `mods_base.xml` to:
```
<mods:genre authority="THE-AUTHORITY" valueURI="THE-VALUE-URI">THE-GENRE-VALUE</mods:genre>
```
...do indicate these values will be replaced, and to remove the incorrect values.

- Regarding the `## Recommended Stored Value ` section of the plan, make this change: Save the _entire_ genre-selection dict-entry into `AppConfig.temp_config_json`.

- Make these changes to necessary sections of the `bdr_uploader_hub_project/PLAN__implement_genre_selection.md` plan.

- Prepend this prompt to the `## Recent Prompt` section.

Goal: Offer the staff-configurer an additional "Basics" option:
- Label: "Assigned Genre"
- value: a drop-down menu defaulting to "document", with other (alphabetical) options of "poster" and "thesis"


Context:

- Review `bdr_uploader_hub_project/AGENTS.md` for coding-directives to follow.

- Review `bdr_uploader_hub_project/README.md` for an overview of the project.

- Review `bdr_uploader_hub_project/bdr_uploader_hub_app/views.py` to understand the flow of processing.

- Right now there is a hard-coded mods-genre value at `bdr_uploader_hub_project/bdr_uploader_hub_app/bdr_uploader_hub_app_templates/mods_base.xml`, in the line `<mods:genre authority="aat" valueURI="http://vocab.getty.edu/aat/300444670">scholarly works</mods:genre>`.

- That `valueURI` attribute, and the text "scholarly work" is incorrect.

- A staff-configurer should be able to select, from a drop-down menu, for the web-app being configured, the options "document", "poster", or "thesis" (or leave the default "document").

- That selection does not need to appear on the student upload form. 

- The options for the drop down will come from the envar `GENRE_OPTIONS_JSON`, which is a list of dicts and looks like this:
```
GENRE_OPTIONS_JSON='[
    {"menu_label": "document", "mods_string": "publications (documents)","authority": "aat", "value_uri": "http://vocab.getty.edu/aat/300111999"},
    {"menu_label": "poster", "mods_string": "instructional posters","authority": "aat", "value_uri": "http://vocab.getty.edu/aat/300426530"},
    {"menu_label": "thesis", "mods_string": "theses","authority": "aat", "value_uri": "http://vocab.getty.edu/aat/300028028"}
]'
```

- That will be loaded into the setting `GENRE_OPTIONS` and normalized for use in the app.

- That data will be used for the menu drop-down for the staff-configurer.

- Based on the selection, the webapp will save the selected option so that in a later stage, when the mods-document is created, the proper `authority` and `valueURI` and text-string will be used.

- If pre-existing data does not include this genre info -- assume the default 'document' information.

Tasks:

- Develop a plan to implement this drop-down menu in the interface -- and to flow the relevant information along to produce the proper MODS data.

- Save the plan to `bdr_uploader_hub_project/PLAN__implement_genre_selection.md` 

- Add any contextual-info to the plan that could be useful if implementation occurs in a different session.

- Do not change any code, just develop and save the plan.

- Add this prompt to a `## Recent Prompt` section, just below the plan's title.


## Objective

Add a staff-only configuration field named `Assigned Genre` to the `Basics` section of the staff-config form. The selected menu value should be persisted with the app configuration and later used during MODS rendering so that `<mods:genre ...>` is generated from environment-backed settings instead of the current hard-coded template value.

## Current State Summary

### Relevant flow

1. Staff config is entered in `bdr_uploader_hub_app/forms/staff_form.py` and rendered explicitly in `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/staff_form.html`.
2. In `bdr_uploader_hub_app/views.py`, `config_slug()` saves `form.cleaned_data` directly into `AppConfig.temp_config_json`.
3. Student uploads use `upload_slug()` to load `app_config.temp_config_json` as `config_data` and build the student form from that config.
4. The student form does not currently expose any genre field, and this request says it should remain staff-only.
5. On student confirmation, `student_confirm()` creates a `Submission` and stores the student payload in `Submission.temp_submission_json`; the `Submission` keeps a reference to `app` (`AppConfig`).
6. During ingest, `bdr_uploader_hub_app/lib/ingester_handler.py` calls `ModsMaker(submission).prepare_mods()`.
7. `bdr_uploader_hub_app/lib/mods_handler.py` builds a template context and renders `mods_base.xml`.
8. `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/mods_base.xml` currently hard-codes:
    - placeholder `authority="THE-AUTHORITY"` that will be replaced by the selected genre data
    - placeholder `valueURI="THE-VALUE-URI"` that will be replaced by the selected genre data
    - placeholder inner text `THE-GENRE-VALUE` that will be replaced by the selected genre data

### Persistence model already available

- `AppConfig.temp_config_json` is a `JSONField` and already stores arbitrary staff-config values.
- Because `Submission` references `Submission.app`, MODS generation can read the selected genre from `submission.app.temp_config_json` without requiring a new database column.
- If existing app data does not yet include genre information, the later MODS step should assume the default `document` genre information.

### Existing patterns to copy

- Staff-config choice fields already exist for license and visibility in `StaffForm`.
- Tests already exercise:
  - staff form rendering and validation in `bdr_uploader_hub_app/tests/test_department_collection.py`
  - MODS generation in `bdr_uploader_hub_app/tests/test_mods_maker.py`
- The template `staff_form.html` manually lays out each field, so adding the field to the form class is not enough; the template must also be updated.

## Proposed Data Shape

Use the environment-backed `settings.GENRE_OPTIONS` as the single source of truth.

The sample JSON in `GENRE_OPTIONS_JSON` is a list of objects. Normalize it into one authoritative runtime structure so the rest of the app does not depend on settings-format quirks. The least-friction runtime shape for later use is one of these:

1. A list of dicts preserving source order, transformed into form choices in code, or
2. A dict keyed by `menu_label`, for example:

```python
{
    "document": {
        "menu_label": "document",
        "mods_string": "publications (documents)",
        "authority": "aat",
        "value_uri": "http://vocab.getty.edu/aat/300111999",
    },
    ...
}
```

For the actual implementation, choose one authoritative structure and normalize it in a helper so the rest of the app does not depend on settings-format quirks.

## Recommended Stored Value

Persist the entire selected genre-entry dict in `AppConfig.temp_config_json`, for example:

```python
{
    "assigned_genre": {
        "menu_label": "document",
        "mods_string": "publications (documents)",
        "authority": "aat",
        "value_uri": "http://vocab.getty.edu/aat/300111999",
    }
}
```

Reasoning:

- It preserves the exact genre metadata chosen at configuration time.
- It keeps the later MODS step independent of any changes to the environment variable.
- It avoids needing a second lookup if the later ingest path already has the stored config.
- It still allows the plan to treat `settings.GENRE_OPTIONS` as the source for the available menu entries.

## Implementation Plan

### 1. Add a reusable genre-options helper

Create a new helper module under `bdr_uploader_hub_app/lib/` such as `genre_helper.py`.

Responsibilities:

- Normalize `settings.GENRE_OPTIONS` into a predictable internal structure.
- Produce sorted staff-form choices by `menu_label`.
- Ensure `document`, `poster`, and `thesis` resolve correctly.
- Provide a function to fetch a genre record from the stored genre dict-entry.
- Provide a function that returns the default genre dict-entry (`document`).
- Raise a clear `ValueError` when settings are malformed or a saved key no longer exists.

Suggested helper functions:

- `build_genre_choices() -> list[tuple[str, str]]`
- `get_default_genre_key() -> str`
- `get_genre_config(stored_genre_entry: dict | None) -> dict`

Notes:

- Sort display options alphabetically by label in the helper, even if the input JSON order is not alphabetical.
- Default should remain `document` even if source ordering changes.
- Keep this logic out of `views.py` per `AGENTS.md` architecture guidance.

### 2. Add the staff-only form field

Update `bdr_uploader_hub_app/forms/staff_form.py`.

Add a `ChoiceField` in the `Basics` section:

- field name: likely `assigned_genre`
- label: `Assigned Genre`
- required: `True`
- initial: default key from helper or `document`
- choices: generated from helper / settings-backed data

Implementation detail:

- If choices are settings-derived at import time today, prefer populating them in `__init__()` instead, similar to how license/visibility choices are refreshed.
- Ensure the field pre-populates correctly from `initial_data = app_config.temp_config_json or {}` in `config_slug()`.

### 3. Update staff-form validation

Update `bdr_uploader_hub_app/forms/staff_form_validation.py`.

Add validation to ensure:

- a value is present
- the submitted key exists in the normalized settings data

This can be minimal because it is a required `ChoiceField`, but explicit validation is still useful because:

- settings may be malformed
- old saved config values may become invalid
- POSTs can be tampered with

If helper loading fails, attach a form error to `assigned_genre` or a non-field error with a clear message.

### 4. Render the field in the staff template

Update `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/staff_form.html`.

Add the new field in the `Basics` section, likely after `collection_title` and before notification / authorization fields, or wherever best matches the existing UI grouping.

Important:

- The template manually renders each field, so this change is required for the field to appear.
- No changes should be made to `student_form.html` or `make_student_form_class()` because the field must not appear for students.

### 5. Thread the saved value into MODS generation

Update `bdr_uploader_hub_app/lib/mods_handler.py`.

Add logic in `ModsMaker.prepare_mods()` to:

- read the stored genre-entry from `self.submission.app.temp_config_json`
- resolve that stored entry through the genre helper to obtain:
  - `authority`
  - `value_uri`
  - `mods_string`
- add those values to the template context

Suggested context keys:

- `genre_authority`
- `genre_value_uri`
- `genre_text`

Fallback behavior recommendation:

- If config is absent for older apps, default to `document`.
- If the stored genre-entry is invalid, either:
  - fail loudly with a clear exception during MODS preparation, or
  - log and fall back to `document`

Preferred approach: default missing-to-`document`, but treat explicitly invalid stored genre-entries as an error so bad configuration is not silently ingested.

### 6. Replace the hard-coded MODS genre element

Update `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/mods_base.xml`.

Replace the current hard-coded line with a template-driven version using the new context values, for example conceptually:

- `authority` from resolved config
- `valueURI` from resolved config
- element text from resolved config

This keeps the template declarative and uses `ModsMaker` to decide the values.

### 7. Add focused tests

Add or update tests in at least these areas.

#### Staff-form tests

Likely file:

- `bdr_uploader_hub_app/tests/test_department_collection.py`
- or add a new focused test module if that is cleaner

Test cases:

- staff form shows `assigned_genre` field
- choices are `document`, `poster`, `thesis`
- displayed order is alphabetical
- initial/default is `document`
- valid post with `assigned_genre="poster"` survives validation
- invalid submitted key is rejected

Use `override_settings()` to inject deterministic `GENRE_OPTIONS` during tests.

#### MODS tests

Update `bdr_uploader_hub_app/tests/test_mods_maker.py`.

Test cases:

- default / missing config yields document MODS genre values
- `poster` selection renders:
  - text `instructional posters`
  - authority `aat`
  - `valueURI` `http://vocab.getty.edu/aat/300426530`
- `thesis` selection renders:
  - text `theses`
  - authority `aat`
  - `valueURI` `http://vocab.getty.edu/aat/300028028`
- old hard-coded `scholarly works` value no longer appears

Important setup note:

- For these MODS tests, create a `Submission` whose `app` has `temp_config_json={'assigned_genre': 'poster'}` (or similar), since `ModsMaker` will need to read through `submission.app`.
- If existing `SimpleTestCase` usage makes model relations awkward, evaluate whether a focused `TestCase` is cleaner.

## Likely Files to Change in a Later Implementation Session

- `bdr_uploader_hub_app/forms/staff_form.py`
- `bdr_uploader_hub_app/forms/staff_form_validation.py`
- `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/staff_form.html`
- `bdr_uploader_hub_app/lib/mods_handler.py`
- `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/mods_base.xml`
- `bdr_uploader_hub_app/tests/test_mods_maker.py`
- one or more staff-form test files
- possibly settings-loading code if `GENRE_OPTIONS` is not yet wired into Django settings
- new helper module, likely `bdr_uploader_hub_app/lib/genre_helper.py`

## Explicit Non-Goals

- Do not add the genre field to the student upload form.
- Do not add a new database column unless a later session identifies a compelling reason.
- Do not duplicate the full genre metadata into `Submission.temp_submission_json` unless there is a later ingest requirement that needs historical snapshots.

## Open Questions / Decisions for the Implementer

### Settings shape

Confirm the exact runtime shape of `settings.GENRE_OPTIONS`.

The prompt says “dict,” while the sample environment variable is a JSON list. Before coding:

- inspect settings-loading code
- normalize the shape in one helper
- keep the rest of the code independent of raw settings format

### Missing or invalid saved config behavior

Decide and document behavior for:

- older apps with no `assigned_genre` saved yet
- apps whose saved value is no longer present in settings

Recommended policy:

- missing => default to `document`
- invalid saved key => fail clearly during form validation and/or MODS preparation

### Backward compatibility

This change will affect existing apps only when they are re-saved, unless MODS generation defaults missing config to `document`. That default is recommended to keep older apps working immediately.

## Cross-Session Notes

### Files inspected for this plan

- `AGENTS.md`
- `README.md`
- `bdr_uploader_hub_app/views.py`
- `bdr_uploader_hub_app/forms/staff_form.py`
- `bdr_uploader_hub_app/forms/staff_form_validation.py`
- `bdr_uploader_hub_app/forms/student_form.py`
- `bdr_uploader_hub_app/lib/mods_handler.py`
- `bdr_uploader_hub_app/lib/ingester_handler.py`
- `bdr_uploader_hub_app/models.py`
- `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/staff_form.html`
- `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/mods_base.xml`
- `bdr_uploader_hub_app/tests/test_mods_maker.py`
- `bdr_uploader_hub_app/tests/test_department_collection.py`

### Architectural observations

- `config_slug()` persists the entire cleaned staff form directly into `AppConfig.temp_config_json`, so adding a new staff field is low-friction.
- `upload_slug()` loads config but only uses it to build the student form and route collection assignment; no genre change is needed there unless future requirements change.
- `student_confirm()` does not copy app config into `Submission` fields, but `Submission.app` is available later, so MODS generation can still resolve the genre at ingest time.
- `mods_base.xml` already relies on template context for many dynamic values, so making genre dynamic fits the existing pattern.

### Test execution note for later

Per repository instructions, the relevant test command after implementation should be:

```text
uv run ./run_tests.py
```

## Suggested Implementation Order

1. Confirm / add `settings.GENRE_OPTIONS` loading.
2. Add `genre_helper.py` normalization functions.
3. Add `assigned_genre` to `StaffForm` and validation.
4. Render the field in `staff_form.html`.
5. Update `ModsMaker.prepare_mods()` to resolve the configured genre.
6. Replace hard-coded MODS genre template markup.
7. Add tests for form behavior and MODS output.
8. Run `uv run ./run_tests.py`.

## Expected End State

After implementation:

- Staff configuring an app see an `Assigned Genre` dropdown in `Basics`.
- The dropdown defaults to `document` and offers `poster` and `thesis` alphabetically.
- The full selected genre dict-entry is saved in `AppConfig.temp_config_json`.
- Students do not see or edit the field.
- MODS generation uses the saved genre-entry plus `settings.GENRE_OPTIONS` to render the correct `mods:genre` element with the correct `authority`, `valueURI`, and text.
