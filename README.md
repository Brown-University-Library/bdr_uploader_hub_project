# BDR Uploader Hub

This webapp allows Library staff to easily configure,
and create, a new BDR (Brown Digital Repository)
upload webapp for users to upload works to the BDR.

## Running locally

Copy `example.env` to `../.env`, and change values as
needed. Note that in the example, most instance files
live in `uploader_hub_files/`

Create a directory called `DBs` in the configured
location (`uploader_hub_files/` by default.

```sh
uv run manage.py makemigrations bdr_student_uploader_hub_app
uv run ./manage.py migrate
```
Based on the example config, this should create a
sqlite file in the DBs directory and set up all
required tables.

Then bring up the app and click "log in as staff" to
trigger the creation of the `admin` profile in
the DB.

Create a superuser and log into the django admin site.
Once there, create a new permissions group with all
permissions from the `submissions` app. Then edit the
`staffperson` profile. Grant staff status and add the
profile to the `submissions_editor` group.
(Alternatively, just grant staff status and all
permissions from the `submissions` app).

At this point, you should be able to log in as staff
and create new apps, edit existing apps and see
student submissions in the admin portal. You should
also be able to log in as a student and upload media.

## Technical note

This webapp is configured to auto-create a UserProfile
record, automatically, whenever a new User record is
created -- whether via code or via the admin.

To enable that:
- `models.UserProfile()` was created.
- `apps.py` was added to the
  `bdr_student_uploader_hub_app` -- specifically to
  load `signals.py`.
- `signals.py` was added to trigger the `UserProfile`
  auto-creation.
- `settings.py` was updated to specify
  `bdr_student_uploader_hub_app.apps.BdrUploaderHubAppConfig`,
  instead of just `bdr_student_uploader_hub_app`.

---
