# OCLC FAST Suggest Integration: Implementation Plan

## Summary
Implement live authority-term suggestions for the student upload form's `keywords` field using htmx calling the existing Django endpoint `check_oclc_fastapi_url`. The UI must support multiple keywords in a single input separated by pipes (`|`). The query for suggestions uses the active segment: if there is no `|`, use the entire input; if there is one or more `|`, use only the text after the last `|` (trimmed). Selecting a suggestion replaces only that last segment, preserving earlier segments.

This plan only describes changes and the sequence. No code is included in this document.


## Project directives that affect implementation
From `pyproject.toml` → `[tool.birkin_project_guidelines].llm_code_directives`:
- Use Python 3.12 type hints everywhere; avoid unnecessary `typing` imports when generics are available.
- Structure scripts with `if __name__ == '__main__': main()` and keep `main()` minimal where applicable.
- Use standard `unittest` (not pytest).
- Run tests with `uv`: `uv run ./manage.py test`.
- Use `httpx` for HTTP calls.
- Prefer single-return functions when reasonable.
- Use present-tense triple-quoted docstrings.

Impact: We will keep helpers in `bdr_uploader_hub_app/lib/fastapi.py` typed, continue using `httpx`, and write Django tests with `unittest`, executing the full test suite via `uv run ./manage.py test`.


## Current codebase context
- Endpoint is already routed: `config/urls.py` defines `path('check_oclc_fastapi/', views.check_oclc_fastapi, name='check_oclc_fastapi_url')`.
- Placeholder view: `bdr_uploader_hub_app/views.py` → `check_oclc_fastapi()` (currently returns a simple `HttpResponse`).
- HTTP client and helpers scaffolded: `bdr_uploader_hub_app/lib/fastapi.py` contains `get_client()`, `prep_url_params()`, `make_request()`, `parse_response()`, and `manage_oclc_fastapi_call()`.
- Student form template: `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/student_form.html` renders `{{ form.keywords }}` when enabled by config.
- htmx is already available globally in `base.html` via `<script src="https://unpkg.com/htmx.org"></script>`.


## Requirements recap
- As a user types in the single `keywords` input, call `check_oclc_fastapi_url` to retrieve authority-term suggestions.
- The input allows multiple keywords separated by pipes: `economic development | world bank`.
- Use the active segment for autosuggest requests: if the input has no `|`, use the entire value; otherwise use only the text after the last `|` (trimmed).
- Selecting a suggestion replaces only the final segment after the last pipe, preserving earlier segments.
- User may choose or ignore suggestions.
- Good UX: debounce, cancel stale requests, show a spinner, accessible list.


## Design overview
- Keep the visible input as the authoritative form field (`#id_keywords`).
- Add a hidden input `name="q"` used only for the suggest endpoint; keep it in sync with the last segment of `#id_keywords`, but trigger network requests only after a debounce (e.g., 300–400 ms of inactivity) and when the segment length meets a minimum (e.g., 2+ chars).
- Trigger htmx requests on input with a debounce. Use `hx-sync="this:replace"` to abort in-flight requests.
- Restrict params to only `q` for the suggest endpoint via `hx-params`.
- Render results into a dedicated suggestions container below the field.
- On click of a suggestion, replace only the last segment in `#id_keywords` and keep earlier segments intact.


## Data flow
1. User types in `#id_keywords`.
2. JS (via `hx-on:input` or a tiny helper) updates a hidden `<input type="hidden" name="q" id="id_keyword_q">` with the last segment after the final `|`, trimmed.
3. An htmx request `GET /check_oclc_fastapi/?q=<lastSegment>` is sent after a short debounce.
4. `views.check_oclc_fastapi` uses `lib.fastapi.manage_oclc_fastapi_call(q)` to query the OCLC FAST suggest endpoint and normalizes output via `parse_response()`.
5. The view returns an HTML partial containing a list of suggestions.
6. Clicking a suggestion updates `#id_keywords` to replace only the last segment, and focuses the input for continued typing.


## File changes
- `bdr_uploader_hub_app/views.py`
  - Implement `check_oclc_fastapi` to accept GET param `q`, return a partial with suggestion items.
  - Handle edge cases (empty/short `q`) by returning a minimal partial (e.g., "Type to see suggestions").

- `bdr_uploader_hub_app/lib/fastapi.py`
  - Implement `parse_response()` to normalize OCLC JSON into a list of suggestions. Each suggestion should include at least: `label` (display text), `fast_id` (from `idroot`), and `type` (e.g., topic, name, etc.). Prefer `auth` or `suggestall` for label; fall back appropriately.
  - Keep `manage_oclc_fastapi_call()` responsible only for orchestration; let the view pass the normalized list to the template.

- Templates
  - `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/student_form.html`
    - Enhance only when `{{ form.keywords }}` is present:
      - Add a hidden input `#id_keyword_q` (name `q`).
      - Add an htmx-enabled wrapper (or place htmx attributes on the appropriate element) that:
        - `hx-get` to `{% url 'check_oclc_fastapi_url' %}`
        - `hx-trigger="input from:#id_keywords changed delay:300ms, keyup[key=='Enter'] from:#id_keywords"`
        - `hx-indicator=".keyword-spinner"`
        - `hx-target="#keyword-suggestions"`
        - `hx-include="#id_keyword_q"`
        - `hx-params="q"`
        - `hx-sync="this:replace"`
      - Add a spinner element `.keyword-spinner`.
      - Add a container `<ul id="keyword-suggestions" role="listbox"></ul>` for results.
      - Add a small script (or `hx-on:input`) to set `#id_keyword_q.value = lastSegmentOf(#id_keywords.value)`.
  - New partial template: `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/partials/_keyword_suggestions.html`
    - Renders suggestions as `<li role="option">` with a `<button type="button">`.
    - Each button’s click handler replaces only the last segment of `#id_keywords` with the selected suggestion and then places the caret at the end.
    - Accessible text formatting, e.g., `{{ label }} (FAST {{ fast_id }})` and optionally type.

- Static JS
  - New: `bdr_uploader_hub_app/static/bdr_student_uploader_hub_app/js/keywords.js`
    - Provide two tiny helpers:
      - `lastSegment(value: string) -> string`
      - `replaceLastSegment(inputEl: HTMLInputElement, text: string) -> void`
    - Keep vanilla and minimal; wire via `student_form.html` in its `{% block header_other %}`.

- Tests
  - `bdr_uploader_hub_app/tests/` additions:
    - Unit tests for `lib.fastapi.prep_url_params()` and `parse_response()` (mock HTTP as needed, avoid hitting network).
    - View test for `check_oclc_fastapi` that validates 200 responses and partial rendering with sample OCLC JSON.
  - Run with `uv run ./manage.py test` per project convention.


## Edge cases and behavior
- Empty or whitespace-only last segment → return a partial with a gentle prompt (no suggestions).
- Last char is a pipe (`... |`) → treat last segment as empty; suggestions should not fire until 1–2 characters are typed.
- Rapid typing → older requests should be aborted via `hx-sync="this:replace"`.
- Selecting a suggestion should preserve earlier segments and normalize spacing around `|` (e.g., `"term A | term B"`).
- If no results → partial returns a single disabled list item stating "No suggestions".


## Accessibility and UX
- Use `role="listbox"` and `role="option"` semantics for the suggestions.
- Spinner indicates activity via `.htmx-request` toggling.
- Click selects a suggestion; optional future enhancement: keyboard navigation.


## Performance and network
- `httpx.Client` is pooled in `lib.fastapi.get_client()` with HTTP/2 enabled; re-use it for efficiency.
- Timeouts in `manage_oclc_fastapi_call()` are already tuned; consider adjusting via settings if needed later.
- Consider simple caching in a later iteration if needed.


## Step-by-step implementation sequence
1. Update `lib/fastapi.py`:
   - Implement `parse_response()` to return a normalized list `[{'label': str, 'fast_id': str, 'type': str}]` given the OCLC payload shape.
2. Implement `views.check_oclc_fastapi`:
   - Read `q` from `request.GET`.
   - If short/empty, return the suggestions partial with a prompt.
   - Else call `manage_oclc_fastapi_call(q)`, extract normalized suggestions, and render the partial.
3. Create partial template `partials/_keyword_suggestions.html`.
4. Modify `student_form.html`:
   - Add hidden input `#id_keyword_q`.
   - Add htmx wiring as described.
   - Add spinner and suggestions container.
   - Include the new `keywords.js` for segment helpers, and wire `#id_keyword_q` updates on input.
5. Add tests for the parser and the view.
6. Execute tests with `uv run ./manage.py test`.


## Rollback
- Template changes are additive and behind the presence of the `keywords` field; removing the htmx attributes and partial include reverts behavior.
- The new view logic can safely return a simple placeholder as it does now; no data model changes are involved.
