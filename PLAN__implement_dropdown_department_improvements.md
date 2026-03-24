# Plan: implement dropdown department improvements

## Recent Prompt

- Review `bdr_uploader_hub_project/AGENTS.md` for coding-directives to follow.
- Review `bdr_uploader_hub_project/README.md` for an overview of the project.
- Review `bdr_uploader_hub_project/PLAN__implement_initial_dropdown_department_option.md` for a sense of work that has been successfully completed.
- Review `bdr_uploader_hub_project/PLAN__implement_dropdown_department_improvements.md` to understand what now needs to be done.
- Implement the `bdr_uploader_hub_project/PLAN__implement_dropdown_department_improvements.md` plan.
- Replace the `## Recent Prompt` content in the `bdr_uploader_hub_project/PLAN__implement_dropdown_department_improvements.md` plan with this prompt.

## Current understanding

- The initial department-collection-menu feature has already been planned and likely implemented or partially implemented.
- This follow-up work is a UX and display refinement, not a redesign of the collection-assignment model.
- The requested changes affect three surfaces:
  - the staff configurator Basics section
  - the student upload form layout and wording
  - the student confirmation/review page
- The department-routing dropdown remains conceptually separate from the existing free-text `department` metadata field controlled by `offer_department`.
- No new configuration mode is being introduced; the work should refine behavior when `collection_assignment_mode == 'department_collection_menu'`.

## Scope of the improvements

### 1. Staff configurator conditional field visibility

When the staff user selects `Department collection menu` in the Basics section:

- Hide the `Collection PID` label and field.
- Hide the `Collection Title` label and field.
- Ensure the hide/show behavior updates immediately when the dropdown selection changes.
- Preserve existing fixed-collection behavior when `fixed_collection` is selected.

Implementation expectation:
- This is likely a template/UI behavior change, possibly with existing JavaScript already used for conditional configurator sections.
- Server-side validation rules should remain aligned with the visible state, but this plan assumes the earlier implementation already made those fields non-required in department-menu mode.

Acceptance target:
- In `department_collection_menu` mode, the fixed-collection fields are not visible in the Basics UI.
- Switching back to fixed mode makes them visible again.

### 2. Student form placement and wording of the department-routing dropdown

When the app is configured for `department_collection_menu`:

- Show the dropdown only once.
- Place it in the top `Basic Information` section.
- Render it immediately after the `Upload File` field.
- Set its label to `Thesis Collection`.
- Set its help text to `(required)`.

Important constraint:
- The dropdown should not also appear later in the form or in any secondary section.
- This change is about the routing dropdown only, not the existing free-text department metadata field.

Implementation expectation:
- The dynamic field-building logic in `forms/student_form.py` likely controls both field order and section assignment.
- If field layout is influenced in the template rather than only in the form class, both form-generation and rendering code may need review.

Acceptance target:
- In department-menu mode, the routing dropdown appears exactly once, in the Basic Information section, directly after `Upload File`, with the required wording.
- In fixed mode, there is no routing dropdown.

### 3. Confirmation-page display of selected collection label

On the student `Review Your Submission...` page, when department-menu mode is active:

- Continue showing `Target Collection PID`.
- Append the human-readable selected department/collection label in parentheses.
- Example: `bdr:123456 (Physics Theses)`.

Implementation expectation:
- The confirmation page will need access to both:
  - the resolved collection PID
  - the selected display label for the department-routing choice
- If only the PID is currently persisted or passed into context, implementation may need to preserve the selected display text in session state, temp submission JSON, or model-backed submission data.

Acceptance target:
- Confirmation view clearly shows both PID and selected label in department-menu mode.
- Fixed-collection mode continues to behave as before unless a harmless consistency improvement is desirable.

## Likely implementation areas

These files are the most likely touchpoints when implementation begins:

- `bdr_uploader_hub_app/forms/staff_form.py`
  - for the mode field and any widget attributes used by the configurator template
- staff configurator template(s)
  - for conditional display of `Collection PID` and `Collection Title`
- `bdr_uploader_hub_app/forms/student_form.py`
  - for routing-dropdown label, help text, order, and section placement
- student upload template(s)
  - if section grouping or render order is template-driven
- `bdr_uploader_hub_app/views.py`
  - for confirmation-page context assembly
- confirmation/review template(s)
  - for displaying `Target Collection PID (Selected Label)`

## Recommended implementation sequence

1. Inspect the staff configurator template and any JavaScript/helpers already controlling conditional field visibility.
2. Update the configurator UI so `Collection PID` and `Collection Title` disappear in department-menu mode.
3. Inspect how the student form decides field order and section membership.
4. Move or render the department-routing dropdown only in the Basic Information section after `Upload File`, and update its label/help text.
5. Trace how the confirmation page currently derives `Target Collection PID` and ensure the selected human-readable label is available there.
6. Update the confirmation template/context to render `PID (Label)` for department-menu submissions.
7. Add or adjust focused tests for configurator rendering behavior, student form field order/attributes, and confirmation-page content.
8. Run `uv run ./run_tests.py`.

## Test ideas

### Staff configurator

- Verify the Basics page includes the fixed-collection inputs in fixed mode.
- Verify department-menu mode hides the fixed-collection inputs in rendered output or via the JS state markers used by the template.

### Student form

- Verify the routing dropdown is present only in department-menu mode.
- Verify its label is `Thesis Collection`.
- Verify its help text is `(required)`.
- Verify it is ordered directly after the upload field.
- Verify it is not duplicated in another section.

### Confirmation page

- Verify department-menu confirmation output includes the resolved PID and the selected label in parentheses.
- Verify fixed-collection confirmation behavior remains stable.

## Risks and open checks

- The current student form may build sections using a field-name list, so changing order may require updating more than one place.
- The confirmation page may currently know only the PID, not the selected label, which could require plumbing additional context through session data or submission persistence.
- If the configurator hide/show behavior is currently server-render-only, a small client-side enhancement may be needed so the fields disappear immediately when the dropdown changes.
- Care is needed not to interfere with the existing free-text `department` metadata field and its `offer_department` toggle.

## Assumptions

- The earlier implementation already made `collection_pid` and `collection_title` non-required in department-menu mode.
- A department-routing field already exists in the student form in some location, and this work is mainly repositioning and relabeling it.
- The confirmation flow already resolves or can access the target PID before final submission creation.

## Implementation handoff context for a future session

- Start by locating the staff configurator Basics template and any existing JavaScript that reacts to `collection_assignment_mode`; that is the most direct place to implement field disappearance.
- For the student form, inspect both the dynamic form builder and the template because field order in Django apps is often split between form definition and template section rendering.
- Specifically verify whether `Upload File` is rendered from a dedicated field list for the Basic Information section; the new routing dropdown should likely be inserted into that same list immediately after the upload field.
- For the confirmation page, trace from `views.student_confirm()` into the confirmation template to see whether the selected routing label is still available in session-backed `student_form_data`; if so, reuse it rather than recomputing from the JSON map unless that data is absent.
- If recomputation is necessary, prefer reusing the same department-map helper introduced for the initial feature so display labels and PID resolution come from one source of truth.
- Keep the work narrow: no model changes should be needed unless the initial implementation failed to preserve the selected routing label anywhere accessible during confirmation.
- Follow repository directives in `AGENTS.md`: keep view logic thin, put reusable logic in `lib/`, and run tests with `uv run ./run_tests.py` after implementation.
