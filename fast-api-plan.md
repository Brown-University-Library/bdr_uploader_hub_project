# OCLC FAST autosuggest plan (no code yet)

Goal: When a user starts typing a keyword (e.g., "histry"), show a small list of authority suggestions from OCLC FAST to pick from (e.g., "History"). Implemented via a small Django API the browser calls, which in turn calls the FAST service.


## Architecture overview
- __Client JS__ in `bdr_uploader_hub_app/static/bdr_student_uploader_hub_app/js/fast_suggest.js` debounces input and calls a Django endpoint with `?q=...&rows=...`.
- __Django view__ `fast_suggest` in `bdr_uploader_hub_app/views.py` validates the query, calls a new lib module, and returns normalized JSON.
- __Lib module__ `bdr_uploader_hub_app/lib/oclc_fast.py` calls OCLC FAST, parses results, shapes them for the frontend.
- __URL route__ added under `config/urls.py` at `/api/fast/suggest/`.
- __Template__ `bdr_uploader_hub_app_templates/student_form.html` loads the JS and marks the relevant input(s) (initially `keywords`) with data-attrs for progressive enhancement.


## External API notes (to confirm during implementation)
- Primary endpoint (FAST suggest): `https://fast.oclc.org/searchfast/fastsuggest`
  - Likely params: `query={text}`, `queryIndex=suggestall`, `rows=8`, `wt=json`.
  - For a misspelling like "histry", suggest may return nothing; we can optionally fallback.
- Fallback endpoint (FAST search): `https://fast.oclc.org/searchfast/fastsearch`
  - Params: `query={text}`, `queryReturn=idroot,auth,type,displayForm`, `rows=8`, `wt=json`.
  - Consider experimenting with query variants or enabling spellcheck if available to recover near-miss results.
- Output fields to normalize (subject to what the API returns):
  - `displayForm` or `suggestall` (human label)
  - `idroot` (FAST ID root, e.g., `fst00912345`)
  - `type` (e.g., topic, personalName)
  - Construct URI: `https://id.worldcat.org/fast/{idroot}`


## Lib module: `bdr_uploader_hub_app/lib/oclc_fast.py`
Responsibilities:
- __fetch_suggestions(query: str, rows: int, min_chars: int)__
  - Validate `query` length; return empty list if below threshold.
  - Build request to `fastsuggest` with timeouts, user-agent, and safe defaults.
  - If empty and query looks like a near miss, optionally try `fastsearch` as a fallback.
- __parse_fastsuggest(json)__ -> list of normalized suggestions.
- __parse_fastsearch(json)__ -> list of normalized suggestions.
- __normalize(item)__ -> `{label, fast_id, uri, type}`.
- __error handling__:
  - Timeouts -> empty suggestions with `source: "timeout"` note in logs.
  - Non-200 -> log warning, return empty list.
- __caching__ (optional initial, easy to add):
  - Use Django cache with short TTL (e.g., 60s) keyed by `(query, rows)`.
- __configuration hooks__ pulled from `django.conf.settings`:
  - `FAST_SUGGEST_ENABLED` (bool)
  - `FAST_SUGGEST_BASE_URL` (default `https://fast.oclc.org/searchfast/fastsuggest`)
  - `FAST_SEARCH_BASE_URL` (default `https://fast.oclc.org/searchfast/fastsearch`)
  - `FAST_SUGGEST_TIMEOUT` (float seconds, default 2.0)
  - `FAST_SUGGEST_ROWS` (default 8)
  - `FAST_SUGGEST_MIN_CHARS` (default 2 or 3)

Implementation details to decide while coding:
- Whether to use `httpx` (already in deps) with a short timeout and optional retry policy.
- Whether to return partials for multi-token input (e.g., append or replace behavior; see JS below).


## Django URL endpoint
- Add to `bdr_uploader_hub_project/config/urls.py`:
  - `path('api/fast/suggest/', views.fast_suggest, name='fast_suggest_url')`
- No CORS needed because same-origin. This avoids browser cross-origin issues when calling OCLC directly.


## View: `bdr_uploader_hub_app/views.py`
- New view: `fast_suggest(request)`
  - Method: `GET`
  - Auth: `login_required` (the student form page is behind login, so OK; can revisit if needed)
  - Query params:
    - `q` (required, trimmed)
    - `rows` (optional, default from settings)
  - Validation: if `not settings.FAST_SUGGEST_ENABLED` or `len(q) < FAST_SUGGEST_MIN_CHARS` -> return `{query: q, suggestions: []}` immediately.
  - Call `oclc_fast.fetch_suggestions(q, rows, min_chars)`.
  - Return JSON: `{ "query": q, "suggestions": [ {"label": str, "fast_id": str, "uri": str, "type": str} ] }`.
  - Rate limiting (nice-to-have): simple in-memory throttle by IP and minute to avoid hammering remote.
  - Caching: rely on lib or cache at view layer.
  - Logging: log slow calls and non-200s at warning level.


## Template updates
- File: `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/student_form.html`
  - Load the new JS in `{% block header_other %}`:
    - `<script src="{% static 'bdr_student_uploader_hub_app/js/fast_suggest.js' %}"></script>`
  - Mark the `keywords` input so JS can locate it predictably.
    - The Django form will render `id="id_keywords"` by default; we will also add attributes from the form field widget:
      - `autocomplete="off"`
      - `data-suggest-url="{% url 'fast_suggest_url' %}"`
      - Optional: `data-suggest-delimiter=" | "` to support multiple selections in a single input.
  - Optionally add a placeholder container after the input (JS can also inject one):
    - `<div id="id_keywords_suggestions" class="fast-suggest-list" aria-live="polite"></div>`


## Form field adjustments
- File: `bdr_uploader_hub_app/forms/student_form.py`
  - When creating the `keywords` field, set a TextInput widget with `attrs` to include the data-attrs and `autocomplete="off"` so the JS can enhance it without fighting the browser’s own suggestions.
  - Same approach can later be reused for `concentrations`, `degrees`, etc.


## Front-end behavior (fast_suggest.js)
- Debounced input listener (e.g., 250–300ms) on the target input(s).
- AbortController to cancel in-flight requests when the user keeps typing.
- Fetch `GET /api/fast/suggest/?q=...&rows=...` and render a positioned suggestions list under the input.
- Keyboard support:
  - Arrow Up/Down to navigate items
  - Enter to choose; Escape to close
  - Mouse click to choose
- Selection behavior:
  - If using delimiter mode (e.g., ` | `), insert the selected label at the current token position; otherwise, replace the field value.
- Accessibility:
  - Role `listbox`/`option`, ARIA attributes (`aria-expanded`, `aria-controls`, `aria-activedescendant`), `aria-live` for updates.
- Styling:
  - Minimal CSS rules can go into `static/bdr_student_uploader_hub_app/css/common.css` or a new small CSS file.


## Settings (config/settings.py)
Add toggles and defaults:
- `FAST_SUGGEST_ENABLED = True`
- `FAST_SUGGEST_BASE_URL = "https://fast.oclc.org/searchfast/fastsuggest"`
- `FAST_SEARCH_BASE_URL = "https://fast.oclc.org/searchfast/fastsearch"`
- `FAST_SUGGEST_TIMEOUT = 2.0`
- `FAST_SUGGEST_ROWS = 8`
- `FAST_SUGGEST_MIN_CHARS = 2`


## Testing plan
- Unit tests for `oclc_fast.parse_fastsuggest` and `parse_fastsearch` using small JSON fixtures.
- Integration-ish tests for the view with mocked HTTP (e.g., `httpx` mocking) for:
  - normal hits (returns N suggestions)
  - near-miss misspelling (primary empty, fallback returns suggestions)
  - timeouts/non-200s (empty list)
  - min-chars enforcement
- Template smoke test: page renders with the script tag when feature is enabled.
- Run tests with: `uv run ./manage.py test`.


## Rollout & toggles
- Feature is behind `FAST_SUGGEST_ENABLED` so it can be disabled without code changes.
- Start with `keywords` only; if well-received, enable for other fields.
- Add basic logging and a short TTL cache to reduce remote calls.


## Acceptance criteria
- Typing at least `FAST_SUGGEST_MIN_CHARS` characters in `keywords` triggers suggestions.
- Selecting a suggestion inserts the normalized label into the input.
- API returns JSON in the agreed shape and handles network errors gracefully.
- For misspellings like "histry", either the suggest or the fallback search provides likely matches (e.g., "History") or we return an empty, non-error response.
