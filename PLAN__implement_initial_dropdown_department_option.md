# Plan: implement dropdown department option

## Recent Prompt

- Review `bdr_uploader_hub_project/AGENTS.md` for coding-directives to follow.
- Review `bdr_uploader_hub_project/PLAN__implement_dropdown_department_option.md` for a sense of what to do.
- Implement the plan.
- Replace the `## Recent Prompt` content in the plan with this prompt.

## Current understanding

- The app’s purpose is to let staff create configurable uploader apps for students, with config stored on `AppConfig.temp_config_json`.
- The staff configurator currently treats `collection_pid` and `collection_title` as required basics fields in `bdr_uploader_hub_app/forms/staff_form.py`.
- Staff-form validation currently validates the configured collection by calling the BDR public API in `bdr_uploader_hub_app/forms/staff_form_validation.py`.
- The student upload form is built dynamically from config in `bdr_uploader_hub_app/forms/student_form.py`.
- Student submissions store free-text `department` on `Submission`, but ingest currently assigns collection membership from `submission.app.temp_config_json['collection_pid']` in `bdr_uploader_hub_app/lib/ingester_handler.py`.
- The new academic-department collection dropdown is separate from the existing free-text `Submission.department` metadata field and separate from the `offer_department` configurator toggle; those existing features should remain unchanged.

## High-level implementation direction

Implement this feature as a configuration mode choice in the staff-config "Basics" section, with two mutually exclusive modes:

- `fixed_collection`
  - Existing behavior.
  - Staff enters `collection_pid` and `collection_title`.
  - Ingest uses the configured collection for every submission under that app.

- `department_collection_menu`
  - New behavior.
  - Staff config selects a mode indicating the app should present a department dropdown to end users.
  - End users must choose a department option.
  - The chosen department resolves to a collection PID, and ingest uses that resolved PID for the specific submission.

This preserves the current app-level configuration shape while making collection assignment per-submission when department mode is enabled.

## Proposed phases

### 1. Add a staff-config collection-assignment mode

Update the staff configuration layer so the Basics section explicitly models how collection assignment works.

Planned changes:
- Add a new field such as `collection_assignment_mode` to the staff form.
- Use explicit choices, for example:
  - `fixed_collection`
  - `department_collection_menu`
- Keep `collection_pid` and `collection_title` in the form, but only require and validate them when `collection_assignment_mode == 'fixed_collection'`.
- Add any companion boolean or metadata fields needed for template rendering, but prefer a single explicit mode field over multiple overlapping booleans.
- Update the staff template so the Basics section clearly shows the two options and conditionally displays relevant inputs.
- Preserve backward compatibility for existing app configs that already only contain `collection_pid` and `collection_title` by treating missing mode as `fixed_collection`.

Acceptance target:
- Staff can save a config in either mode.
- Existing apps continue to behave as fixed-collection apps without manual migration.

### 2. Add a reusable department-map loader in `lib/`

Create a focused helper module under `bdr_uploader_hub_app/lib/` to load and normalize the department JSON file referenced by `DEPARTMENT_MAP_FILEPATH`.

Planned changes:
- Read the JSON file path from environment-backed settings access.
- Parse the JSON structure with `err` and `results`.
- Normalize each entry into a predictable internal shape, for example:
  - `label`: department display text
  - `collection_pid`: parsed from the portion of `id` after the tab character
  - `raw_id`: original source value for logging/debugging if needed
- Validate file existence, JSON format, required keys, duplicate department labels, and malformed `id` values.
- Expose two helper outputs:
  - a list of dropdown choices for the student form
  - a lookup map from selected department label or stable value to collection PID
- Keep all parsing and file-reading logic out of `views.py` to follow repository directives.

Open design decision to resolve during implementation:
- Prefer storing a stable value in the student form that uniquely identifies the selected department, rather than relying only on display text. A good option is to store the original source `id` value or a normalized key derived from it.

Acceptance target:
- A single library helper becomes the source of truth for department dropdown data and department-to-collection resolution.

### 3. Update staff-form validation rules

Modify `bdr_uploader_hub_app/forms/staff_form_validation.py` so validation depends on the selected mode.

Planned changes:
- If mode is `fixed_collection`:
  - require `collection_pid`
  - require `collection_title`
  - keep current BDR API title/PID validation behavior
- If mode is `department_collection_menu`:
  - do not require fixed collection fields
  - validate that department-map data is available and usable
  - optionally validate that the map contains at least one usable result
- Add a cross-field validation error if mode is missing or invalid.
- Ensure cleaned config data stores enough information for downstream form-building and ingest logic.

Acceptance target:
- The form enforces the correct requirements for each mode and produces clear validation errors.

### 4. Update student form generation for department mode

Modify `bdr_uploader_hub_app/forms/student_form.py` so student upload fields reflect the configured collection-assignment mode.

Planned changes:
- Continue building the existing free-text `department` field when `offer_department` is enabled for descriptive metadata purposes.
- Do not repurpose, rename, or couple that free-text field to the new collection-assignment dropdown.
- Do not change the meaning or behavior of the existing `offer_department` toggle as part of this feature.
- In department-collection mode, add a required dropdown field dedicated to collection selection by department.
- Populate that dropdown from the department-map helper.
- Store a stable submitted value that can later resolve to a collection PID without ambiguity.
- Use clear help text so the end user understands the dropdown controls repository assignment.
- Ensure there is no default selected department; the field should require an explicit user choice.

Important design note:
- The existing `department` submission field is currently descriptive metadata.
- The new dropdown should be a separate field, for example `department_collection_choice`, to avoid confusing metadata with ingest-target routing.
- The new dropdown must not populate or otherwise drive `Submission.department`; it exists only to determine collection assignment.

Acceptance target:
- In fixed mode, student form behavior is unchanged.
- In department-menu mode, student form requires a department selection from the dropdown.

### 5. Persist the resolved collection target on submission

Ensure the chosen department-based collection PID is preserved with each submission so ingest is deterministic and does not depend on later changes to the JSON file.

Preferred implementation:
- Add a new submission field such as `target_collection_pid`.
- On student form submission or confirmation, resolve the selected department to its collection PID and store that resolved PID on the `Submission` record.
- Also store the selected department/menu value in `temp_submission_json` and optionally in a dedicated field if it will be useful for admin display or auditing.

Why this is important:
- If the JSON mapping file changes after a student submits but before staff ingests, ingest should still use the collection intended at submission time.
- This avoids time-of-ingest ambiguity.

Alternative, lower-confidence approach:
- Resolve the PID at ingest time from the saved department selection and current JSON map.
- This is simpler initially but weaker operationally because mappings can drift.

Acceptance target:
- Every submission has an explicit collection target by the time it is ready to ingest.

### 6. Update ingest logic to use per-submission collection target when present

Modify `bdr_uploader_hub_app/lib/ingester_handler.py` so RELS preparation uses the correct collection source.

Planned changes:
- Update `prepare_rels()` and/or the caller so collection PID resolution follows this order:
  - use `submission.target_collection_pid` if present
  - otherwise fall back to `submission.app.temp_config_json['collection_pid']`
- Keep this logic in `lib/` and avoid pushing resolution logic into views.
- Add explicit error handling for missing collection target in department-menu mode.

Acceptance target:
- Existing submissions continue to ingest successfully.
- New department-menu submissions ingest into the collection mapped from the user’s chosen department.

### 7. Update templates and UX affordances

Update the staff and student templates to make the two modes understandable and reduce configuration errors.

Planned changes:
- In the staff "Basics" section, visually group collection assignment choices.
- Show/hide or clearly annotate fields that are active for the selected mode.
- Do not add a staff preview of department options on the config page; validation-only is sufficient there.
- In the student form, make the department dropdown label explicit, for example "Department Collection" or similar if needed for clarity.
- In the confirmation view, display both the human-readable department choice and the resolved collection PID when department-menu mode is active.

Acceptance target:
- Staff can understand the difference between fixed collection assignment and user-selected department routing.
- End users can understand what they must select.

### 8. Add tests

Add focused tests around the new branching behavior.

Planned test coverage:
- Staff form validation in fixed mode:
  - valid PID/title path
  - missing PID/title errors
- Staff form validation in department-menu mode:
  - fixed collection fields not required
  - invalid or missing department-map file errors
  - malformed JSON structure errors
- Department-map helper:
  - valid JSON parses into expected choices and lookup map
  - malformed `id` values fail clearly
  - duplicate entries are handled or rejected consistently
- Student form generation:
  - fixed mode does not add the dropdown
  - department-menu mode adds required dropdown choices
- Submission persistence:
  - selected department resolves to stored `target_collection_pid`
- Ingest behavior:
  - `prepare_rels()` prefers per-submission collection PID
  - fallback to app-level `collection_pid` remains intact

Testing notes:
- Existing tests show the repo already uses Django tests and direct form tests.
- Tests should avoid depending on external VPN/API behavior unless specifically validating the existing fixed-collection check.
- Use temporary files or settings overrides for department-map fixtures.

## Data-shape proposal

### AppConfig `temp_config_json`

Current fixed mode can evolve toward this shape:

```json
{
  "collection_assignment_mode": "fixed_collection",
  "collection_pid": "bdr:123456",
  "collection_title": "Example Collection",
  "staff_to_notify": "a@brown.edu | b@brown.edu"
}
```

Department-menu mode can look like:

```json
{
  "collection_assignment_mode": "department_collection_menu",
  "staff_to_notify": "a@brown.edu | b@brown.edu"
}
```

No app-level collection PID is required in department-menu mode unless a fallback/default is intentionally added later.

### Submission persistence

Recommended additions:

```json
{
  "department_collection_choice": "Computer Science\ttest:3dhnp23z",
  "target_collection_pid": "test:3dhnp23z"
}
```

Also keep human-readable department display available either in:
- `Submission.temp_submission_json`
- or a dedicated new submission field if useful for admin/reporting visibility.
- Do not use the existing `Submission.department` metadata field for this feature's routing state.

## Risks and compatibility considerations

- Existing apps likely have no mode field, so implementation should default them to fixed-collection behavior.
- Current ingest assumes app-level `collection_pid`; this is the key behavior that must be generalized.
- The existing free-text `department` metadata field could be confused with the new routing dropdown unless naming is kept explicit.
- If the department map uses display text as the only key, duplicate department names could become ambiguous. Prefer a stable internal value.

## Recommended implementation order

1. Add department-map helper and tests.
2. Add staff config mode field and conditional validation.
3. Update staff template Basics section.
4. Update dynamic student form generation to add the dropdown in department mode.
5. Persist selected department and resolved collection PID on `Submission`.
6. Update ingest logic to prefer submission-level target collection PID.
7. Add confirmation/admin display refinements.
8. Run `uv run ./run_tests.py`.

## Questions to resolve during implementation

These design decisions are now resolved:
- The end-user-facing academic-department dropdown is completely separate from the existing `Submission.department` free-text metadata field.
- The existing free-text department field and its `offer_department` metadata toggle remain unchanged and are not part of this feature.
- The collection-assignment dropdown is shown only when `collection_assignment_mode` is `department_collection_menu`.
- Staff do not need a preview of available department options on the config page; validation-only is sufficient.
- There is no default selected department; the end user must explicitly choose one.

## Definition of done

The feature is complete when:
- Staff can configure an uploader app using either a fixed collection PID/title or a department-driven collection menu.
- The department dropdown is populated from the JSON file at `DEPARTMENT_MAP_FILEPATH`.
- Student selection of a department deterministically resolves to a collection PID.
- Each submission carries the correct collection target into ingest.
- Existing fixed-collection apps continue to work unchanged.
- Focused tests cover the new behavior and compatibility path.

## Implementation handoff context for a future session

- Staff-config persistence currently happens in `views.config_slug()`, which saves `form.cleaned_data` directly into `AppConfig.temp_config_json`.
- Student form generation currently happens in `forms.student_form.make_student_form_class(config_data)`.
- Student submission persistence currently happens in `views.student_confirm()`, which copies values from session-backed `student_form_data` into `Submission.objects.create(...)`.
- Collection membership for ingest is currently derived in `lib.ingester_handler.Ingester.prepare_rels()` from `submission.app.temp_config_json['collection_pid']`.
- Because the department-routing feature changes collection assignment from app-level to submission-level in one mode, implementation will likely require coordinated edits across:
  - `bdr_uploader_hub_app/forms/staff_form.py`
  - `bdr_uploader_hub_app/forms/staff_form_validation.py`
  - `bdr_uploader_hub_app/forms/student_form.py`
  - `bdr_uploader_hub_app/views.py`
  - `bdr_uploader_hub_app/lib/ingester_handler.py`
  - a new helper module under `bdr_uploader_hub_app/lib/`
  - tests in `bdr_uploader_hub_app/tests/`
- Because `Submission` currently has no field for a resolved per-submission collection PID, implementation will likely require a model change plus a migration.
- Backward compatibility matters: existing apps without `collection_assignment_mode` should be treated as `fixed_collection`.
- The department-map file format should be treated as authoritative input, with the value after the tab character in each `results[*].id` used as the collection PID.
- The student-facing department-routing dropdown should have no preselected default; the user must actively choose a value.
- When implementation begins, run tests with `uv run ./run_tests.py` after updating or adding focused coverage.
