# Fix: `Assigned Genre` not persisting after save

## Recent Prompt

- Review `bdr_uploader_hub_project/README.md` for an overview of the project.
- Review `bdr_uploader_hub_project/PLAN__implement_genre_selection.md` to understand the work that was just implemented.
- I just logged into the webapp as a staffperson.
- I opened one of the previously existing "webapp" entries.
- I changed the "Assigned Genre", which was on "document", to "thesis".
- I then clicked "Save".
- When I reopened the configuration I had just changed, the "Assigned Genre" was back on "document" instead of "thesis".
- Review `bdr_uploader_hub_project/AGENTS.md` to understand coding-directives to follow.
- Please analyze the code and explain to me the problem, and proposed solution.
- Save the solution to `bdr_uploader_hub_project/FIX__lack_of_save.md`
- Add this prompt to a `## Recent Prompt` section of the `bdr_uploader_hub_project/FIX__lack_of_save.md`, just below the title.

## Problem summary

The staff UI is allowing `Assigned Genre` to appear selectable, but the value is not reliably surviving the save/reload cycle for existing app configurations.

The code path that matters is:

- `bdr_uploader_hub_app/views.py` → `config_slug()`
- `bdr_uploader_hub_app/forms/staff_form.py`
- `bdr_uploader_hub_app/forms/staff_form_validation.py`
- `AppConfig.temp_config_json`

On POST, `config_slug()` saves `form.cleaned_data` directly into `app_config.temp_config_json`. On GET, it reloads `app_config.temp_config_json` and passes that into `StaffForm(initial=...)`.

That means the bug is most likely in one of these places:

- the submitted genre value is not making it into `cleaned_data`
- the genre value is being normalized incorrectly during validation
- the genre value is being stored in a shape the form does not restore cleanly
- the form field is not enforced strongly enough, so missing/invalid POST data falls back to the default `document`

## Most likely root cause

The current genre flow is still too permissive and relies on fallback behavior.

In particular:

- `assigned_genre` is defined as `required=False` in `StaffForm`
- validation then tries to resolve the value and replaces it with the resolved dict
- if the value is absent, malformed, or not bound the way we expect, the helper defaults to `document`

That makes the saved configuration vulnerable to silently landing on the default genre instead of preserving the staff selection.

## Why this shows up for existing configs

For an existing app entry, the reload path uses `app_config.temp_config_json` as the source of truth.

If the POST save stored:

- no `assigned_genre` key, or
- a value that later resolves to the default genre, or
- a value that gets lost because the form did not treat the field as required

then reopening the configuration will show `document` again.

## Proposed solution

Make the genre selection behave like a required persisted staff setting instead of an optional fallback:

- change `assigned_genre` to a required staff field
- validate that the selected value exists in `GENRE_OPTIONS`
- store the full resolved genre dict entry in `temp_config_json`
- on reload, prefer the stored genre entry and only fall back to the default `document` when the config genuinely has no prior value

## Implementation details

### 1. Treat the field as required

`assigned_genre` should be a required `ChoiceField` in `StaffForm`.

That prevents accidental empty posts from silently collapsing to the default.

### 2. Keep validation strict

`validate_staff_form()` should continue resolving the posted menu label through the genre helper.

If the value is unknown, attach a field error instead of silently substituting `document`.

### 3. Preserve the stored dict entry

The save path in `config_slug()` should continue writing `form.cleaned_data` to `temp_config_json`, but only after validation confirms the genre is valid.

The saved value should remain the full genre dict:

- `menu_label`
- `mods_string`
- `authority`
- `value_uri`

### 4. Restore the stored value explicitly

`StaffForm.__init__()` should continue to translate a stored dict entry back to the select value (`menu_label`) when opening an existing config.

That ensures the dropdown reflects the last saved selection instead of always showing the helper default.

## Suggested verification

Add or update tests for these cases:

- saving `thesis` and reopening preserves `thesis`
- missing `assigned_genre` is rejected or defaults only in the documented fallback path
- `temp_config_json` stores the resolved genre dict, not just the string label
- loading an existing config with no genre still defaults to `document`

## Expected outcome

After the fix:

- staff can change `Assigned Genre` from `document` to `thesis`
- saving persists that selection
- reopening the same config shows `thesis`
- MODS generation continues to use the saved genre metadata correctly
