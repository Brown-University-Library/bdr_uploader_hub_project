# Plan: Implement Pattern-Library Header

## Objective

Update the BDR Uploader Hub header so it follows the same pattern-header architecture used by the alt-text-maker app:

- Fetch trusted pattern-library header HTML from `PATTERN_HEADER_URL`.
- Split the upstream HTML into a `<head>` CSS include and a body/header markup include.
- Render the pattern-header first in `base.html`.
- Render the local app title, login/logout links, and welcome text below the pattern-header.
- Keep the dynamic staff/student login flow outside the upstream pattern-header fragment.
- Contain CSS changes so the imported pattern-header CSS does not unintentionally restyle the existing BDR forms and pages beyond the new header/title/login area.

No app code has been changed yet; this is an implementation plan only.

## Directives Reviewed

- `AGENTS.md`
- `ruff.toml`

Relevant directives:

- Use `uv run ./manage.py THE-COMMAND` for Django management commands.
- Use `uv run ./run_tests.py` for tests.
- Use Python 3.12 type hints.
- Prefer `httpx` for HTTP calls.
- Keep docstrings in present tense, with the final non-test docstring line as `Called by: ...`.
- Keep changes small and aligned with existing project conventions.
- `ruff.toml` uses single quotes and max line length `125`.

## Alt-Text-Maker Pattern To Copy

The reference implementation is in `alt_text_maker_stuff_copy/alt_text_project`.

Important files:

- `alt_text_project/alt_text_app/management/commands/update_pattern_header.py`
- `alt_text_project/alt_text_app/alt_text_app_templates/alt_text_app/includes/pattern_header/head.html`
- `alt_text_project/alt_text_app/alt_text_app_templates/alt_text_app/includes/pattern_header/body.html`
- `alt_text_project/alt_text_app/lib/pattern_header_upstream.html`
- `alt_text_project/alt_text_app/tests/test_pattern_header.py`
- `alt_text_project/config/settings.py`
- `alt_text_project/config/settings_ci_tests.py`
- `alt_text_project/alt_text_app/alt_text_app_templates/alt_text_app/base.html`

The pattern is:

1. A manual Django management command reads `settings.PATTERN_HEADER_URL`, optionally accepts `--url`, and supports `--dry-run`.
2. The command fetches the upstream HTML with `httpx`.
3. The command stores the full upstream snapshot in `lib/pattern_header_upstream.html`.
4. The command extracts the `bul_patterns.css` `<link>` tag into `includes/pattern_header/head.html`.
5. The command removes that link tag from the body fragment and stores the remaining markup in `includes/pattern_header/body.html`.
6. The base template includes the head fragment inside `<head>` and body fragment immediately after `<body>`.
7. Tests cover the split behavior and preservation of Django template syntax.

## Current BDR State

Relevant BDR files:

- `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/base.html`
- `bdr_uploader_hub_app/static/bdr_student_uploader_hub_app/css/common.css`
- `config/settings.py`
- `config/settings_run_tests.py`
- `pyproject.toml`

Current behavior:

- `base.html` renders a local `<header>` with `<div class="header-content">`.
- That block contains the `BDR Uploader Hub` `<h1>`, a Font Awesome book icon link, the welcome/logout text, and unauthenticated `Student Login` / `Staff Login` links.
- `common.css` styles the generic `header` selector as a maroon bar and styles `.header-content`, `.welcome-text`, `.login_logout`, and `.staff-login`.
- The staff/student links depend on `{% url 'pre_login_url' %}?type=student` and `{% url 'pre_login_url' %}?type=staff`.
- Authenticated pages pass `username` in context and show `Welcome ... / Logout`.
- `pyproject.toml` already includes `httpx` and `beautifulsoup4`, so no dependency additions should be necessary for the command/tests.

Important difference from alt-text-maker:

- BDR must keep dynamic login/logout links in local template code below the pattern-header, not embedded into the fetched pattern-header HTML.

## Implementation Steps

### 1. Add pattern-header setting

Edit `config/settings.py`:

- Add a short app-level section for pattern-header configuration.
- Set `PATTERN_HEADER_URL: str = os.environ.get('PATTERN_HEADER_URL', '')`.
- Do not hard-code the URL in settings.

Edit `config/settings_run_tests.py`:

- Add `PATTERN_HEADER_URL: str = ''` so tests do not depend on `.env`.

Optional documentation follow-up:

- Add `PATTERN_HEADER_URL=""` to `config/dotenv_example_file.txt` without using the real central URL.

### 2. Add management-command package structure

Create:

- `bdr_uploader_hub_app/management/__init__.py`
- `bdr_uploader_hub_app/management/commands/__init__.py`
- `bdr_uploader_hub_app/management/commands/update_pattern_header.py`

Copy the alt-text-maker command structure, adjusted for BDR paths:

- Upstream snapshot target: `bdr_uploader_hub_app/lib/pattern_header_upstream.html`
- Head include target: `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/includes/pattern_header/head.html`
- Body include target: `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/includes/pattern_header/body.html`

Keep the same useful command options:

- `--url`
- `--dry-run`

Use:

```shell
uv run ./manage.py update_pattern_header --dry-run
uv run ./manage.py update_pattern_header
```

Implementation notes:

- Keep `fetch_pattern_header(url: str) -> str`.
- Keep `resolve_target_paths() -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]`.
- Keep `split_pattern_header(content: str) -> tuple[str, str]`.
- Keep `save_pattern_header(content: str, target_path: pathlib.Path) -> None`.
- Use `httpx.get(url, timeout=30.0)`.
- Keep the source treated as trusted, as in the alt-text-maker implementation.
- The regex can stay focused on extracting the `bul_patterns.css` stylesheet link from an HTTPS URL, but avoid writing any real central URL into tests or docs.

### 3. Add initial include files

Create the include directory:

- `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/includes/pattern_header/`

The implementation should commit real generated include files if the fetch can be run during implementation. If network access is unavailable, create valid placeholder include files so template rendering does not fail, and document that the maintainer should run:

```shell
uv run ./manage.py update_pattern_header
```

Recommended files:

- `includes/pattern_header/head.html`
- `includes/pattern_header/body.html`

The full upstream snapshot should be written by the command to:

- `bdr_uploader_hub_app/lib/pattern_header_upstream.html`

### 4. Update `base.html`

Edit `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/base.html`.

In `<head>`:

- Keep the local `common.css` include.
- Include `includes/pattern_header/head.html`.
- Remove the Font Awesome stylesheet include if no other template depends on it.
- Remove the Font Awesome book icon from the local app title; the pattern-header should carry the Brown Library brand signal.
- Keep HTMX as-is unless unrelated cleanup is explicitly requested.

In `<body>`:

- Include `includes/pattern_header/body.html` immediately after the opening `<body>`.
- Replace the existing maroon `<header><div class="header-content">...</div></header>` block with a local app header region below the pattern-header.
- Keep the app title as a local `<h1>BDR Uploader Hub</h1>`.
- Keep the unauthenticated login links:
  - `{% url 'pre_login_url' %}?type=student`
  - `{% url 'pre_login_url' %}?type=staff`
- Keep the authenticated logout link:
  - `{% url 'logout_url' %}`
- Use local class names that are unlikely to collide with the pattern-library CSS, for example:
  - `.bdr-app-header`
  - `.bdr-app-header__inner`
  - `.bdr-app-title`
  - `.bdr-auth-links`
  - `.bdr-auth-link`
  - `.bdr-auth-link--staff`
  - `.bdr-welcome-text`

Avoid generic selectors in the new markup where possible.

Example structure to implement:

```django
{% include "includes/pattern_header/body.html" %}

<header class="bdr-app-header" aria-label="BDR Uploader Hub">
    <div class="bdr-app-header__inner">
        <h1 class="bdr-app-title">BDR Uploader Hub</h1>
        {% if username %}
            <span class="bdr-welcome-text">
                Welcome {{ username }} /
                <a class="bdr-auth-link" href="{% url 'logout_url' %}">Logout</a>
            </span>
        {% else %}
            <nav class="bdr-auth-links" aria-label="BDR Uploader Hub login links">
                <a class="bdr-auth-link" href="{% url 'pre_login_url' %}?type=student">Student Login</a>
                <a class="bdr-auth-link bdr-auth-link--staff" href="{% url 'pre_login_url' %}?type=staff">Staff Login</a>
            </nav>
        {% endif %}
    </div>
</header>
```

### 5. Update `common.css` carefully

Edit `bdr_uploader_hub_app/static/bdr_student_uploader_hub_app/css/common.css`.

Main CSS goal:

- Remove or stop relying on the generic `header` styles that currently create the maroon bar.
- Replace `.header-content`, `.welcome-text`, `.login_logout`, and `.staff-login` with BDR-specific selectors.
- Avoid styling generic `header`, generic `a`, generic `h1`, or pattern-library IDs/classes.
- Keep existing page/form/container CSS behavior intact unless there is a direct conflict from the imported pattern-header CSS.

Suggested local app-header styling:

- Use a normal white or lightly bordered region below the pattern-header.
- Keep layout simple and responsive.
- Make the title and links readable without assuming a maroon background.
- Use scoped link colors on `.bdr-auth-link`.

Suggested containment approach:

- Keep existing broad font rule if needed, but be aware that `head` in `head, body, form, ...` is not useful.
- If the pattern-library CSS changes `body`, `main`, or global link styling, add narrow reset rules under `main` and `.bdr-app-header` rather than trying to override the pattern-library globally.
- Do not override pattern-header selectors such as `#bul_pl_header_begin` unless a verified collision requires a small targeted fix.

### 6. Add tests

Create `bdr_uploader_hub_app/tests/test_pattern_header.py`.

Copy and adapt the alt-text-maker tests:

- Import from `bdr_uploader_hub_app.management.commands import update_pattern_header`.
- Test that `split_pattern_header()` extracts the `bul_patterns.css` link into head content.
- Test that the body content no longer contains the stylesheet link.
- Test that Django template tags in the upstream body are preserved.
- Test that a query-string version of the CSS URL still extracts correctly.

Add a small template-rendering test if practical:

- Render `base.html` through Django’s template loader with no `username`.
- Assert that `BDR Uploader Hub`, `Student Login`, and `Staff Login` render.
- Assert that the student/staff login query params still appear.

This catches regressions in the dynamic auth links without depending on remote network access.

### 7. Verification

Run from `bdr_uploader_hub_project`:

```shell
uv run ./run_tests.py
```

If implementing the fetch command in the same session and network access is available, also run:

```shell
uv run ./manage.py update_pattern_header --dry-run
uv run ./manage.py update_pattern_header
```

Then manually inspect the rendered app in a browser:

- Public info page shows the pattern-header.
- `BDR Uploader Hub` title appears below it.
- `Student Login` and `Staff Login` appear below the title or aligned with it.
- Staff/student links preserve their `type` query params.
- Authenticated pages still show welcome/logout behavior.
- Existing form layout, container sizing, table styling, and field styling are not visibly changed except for the header/title/login area.

## Risks And Mitigations

- **Pattern-library CSS changes global styles.** Mitigate with BDR-specific classes for the local app header and minimal scoped resets for `main` or form areas only if verified.
- **Missing include files break every template extending `base.html`.** Mitigate by committing generated includes, or at minimum valid placeholder includes, with the management command available for manual refresh.
- **Dynamic links accidentally get embedded into upstream-managed HTML.** Mitigate by keeping staff/student/login/logout markup in `base.html` below the pattern-header include.
- **Network fetch unavailable during implementation.** Mitigate by testing command parsing with local strings and using `--dry-run` when possible; document the manual command for later execution.
- **Font Awesome becomes redundant.** Remove the title icon and stylesheet include unless a later code search shows another template still depends on Font Awesome.

## Expected File Changes

- Add `PATTERN_HEADER_URL` setting:
  - `config/settings.py`
  - `config/settings_run_tests.py`
- Add manual update command:
  - `bdr_uploader_hub_app/management/__init__.py`
  - `bdr_uploader_hub_app/management/commands/__init__.py`
  - `bdr_uploader_hub_app/management/commands/update_pattern_header.py`
- Add generated or placeholder pattern-header artifacts:
  - `bdr_uploader_hub_app/lib/pattern_header_upstream.html`
  - `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/includes/pattern_header/head.html`
  - `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/includes/pattern_header/body.html`
- Update base template:
  - `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/base.html`
- Update scoped header CSS:
  - `bdr_uploader_hub_app/static/bdr_student_uploader_hub_app/css/common.css`
- Add tests:
  - `bdr_uploader_hub_app/tests/test_pattern_header.py`
- Optional example env documentation:
  - `config/dotenv_example_file.txt`

## Original Prompt

Goal: Update the bdr-uploader-hub webapp to have its web-header use the pattern-library, the way that the alt-text-maker webapp works.

Context:

- The existing `<div class="header-content">`, containing the h1 "title" and the staff-login and student-login -- works fine, but doesn't have a conformant style.

- The purpose of this change is to pull pattern-library html/css from a central url -- and have the title and two login links below it.

- The updated "title" and login-links don't have to still be in a big maroon bar.

- Sometimes when I've done this in the past, sometimes the pulled-in pattern-header CSS conflicts a bit with the existing CSS. We must use the pattern-header CSS -- but please try to ensure that (except for updated styling of the h1-"title" and login-links) the existing styling is not affected by the pattern-header styling.

- The bdr-uploader-hub webapp code is at `bdr_uploader_hub_project`

- The alt-text-maker webapp "stuff" code is at `alt_text_maker_stuff_copy` -- and the alt-text-maker webapp code is at `alt_text_maker_stuff_copy/alt_text_project`.

- Note that the alt-text-maker webapp has a `manage.py` helper script that is run manually to pull down the pattern-library html code into a place within the project.

- Note that the alt-text-maker webapp, in the stuff-directory, has a `.env` file, at `alt_text_maker_stuff_copy/.env` -- that contains the patter-header-url. I have replicated the appropriate url for the bdr-uploader-hub in its `.env` file at `.env`

- Note that a significant difference in the two apps is that the bdr-uploader-hub webapp has a staff-login and student-login dynamic link. My plan is to NOT incorporate these into the new pattern-header, but to have those links be below the new pattern header.

- Note that the pattern-header doesn't incorporate and main title of the app -- so the existing bdr-uploader-hub `<h1 ... BDR Uploader Hub</h1>` "title" will go below the new pattern-header.

Tasks:

- Review `bdr_uploader_hub_project/AGENTS.md` for coding-directives to follow.

- Follow the architectural pattern from the `alt_text_maker_stuff_copy/alt_text_project` as much as possible.

- Do not implement the change yet -- inspect all necessary code and make a plan to perform the update, and save that plan to `bdr_uploader_hub_project/PLAN_implement_pattern_header.md`.

- At the bottom of the plan, include this prompt.

- In the plan, use only relative urls, not full-path urls.

### Follow-Up Prompt

- I've reviewed the plan.
- There is no need to keep the font-awesome icon.
- Update the plan accordingly, and append this feedback to the prompt-section with a "follow-up prompt" type sub-heading.

---
