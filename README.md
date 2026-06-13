# BDR Uploader Hub

This webapp:
- Allows users to stage their uploads.
- Allows Library staff to easily configure, and create, a new BDR (Brown Digital Repository) upload webapp for users to upload works for ingest into the BDR. It also allows staff to ingest users' staged items.


## Running locally

Copy `example.env` to `../.env`, and change values as needed. Note that in the example, most instance files live in `uploader_hub_files/`

Create the directories `DBs` and `logs` in the configured location (`uploader_hub_files/` by default.)

```sh
uv run manage.py makemigrations bdr_student_uploader_hub_app
uv run ./manage.py migrate
```
Based on the example config, this should create a sqlite file in the DBs directory and set up all required tables.

Run the app with
```sh
uv run manage.py runserver
```

Then bring up the app and click "log in as staff" to trigger the creation of the `admin` profile in the DB.

When running on localhost, the app uses `TEST_SHIB_META_DCT_JSON` to spoof a shibboleth account for your sessions. This account needs to be granted staff access through the admin.

Create a superuser for yourself
```sh
uv run manage.py createsuperuser
```
and log into `/admin`

Go to User profiles, and check "Can create app" for the shib-spoofed profile.

At this point, you should be able to log in as staff and create new apps, edit existing apps and see student submissions in the admin portal. If your new apps grant access to one of the configured groups, or to `foo@bar.baz`, you'll also be able to log in as a student and see those apps.


## Technical notes

### UserProfiles

This webapp is configured to auto-create a UserProfile record, automatically, whenever a new User record is created -- whether via code or via the admin.

To enable that:
- `models.UserProfile()` was created.
- `apps.py` was added to the `bdr_student_uploader_hub_app` -- specifically to load `signals.py`.
- `signals.py` was added to trigger the `UserProfile` auto-creation.
- `settings.py` was updated to specify `bdr_student_uploader_hub_app.apps.BdrUploaderHubAppConfig`, instead of just `bdr_student_uploader_hub_app`.

### Updating pattern-header

The Brown Library pattern-header HTML and CSS are stored locally in template and static files, but are updated manually from the central pattern-library URL configured as `PATTERN_HEADER_URL` in `../.env`.

To check that the configured URL can be fetched without changing files:

```sh
uv run ./manage.py update_pattern_header --dry-run
```

To refresh the local pattern-header files:

```sh
uv run ./manage.py update_pattern_header
```

The command:
- saves a full upstream snapshot to `bdr_uploader_hub_app/lib/pattern_header_upstream.html`
- downloads the pattern-header CSS to `bdr_uploader_hub_app/static/bdr_student_uploader_hub_app/css/bul_patterns.css`
- rewrites the stylesheet link in `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/includes/pattern_header/head.html` to use the local static CSS file
- saves the body/header markup to `bdr_uploader_hub_app/bdr_uploader_hub_app_templates/includes/pattern_header/body.html`.

This is intentionally not automatic. Run it when the central pattern-header changes, then review the rendered pages for CSS conflicts before committing the refreshed files.

---
