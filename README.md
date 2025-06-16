# Purpose

This webapp will allow Library staff to easily configure, and create, a new BDR (Brown Digital Repository) deposits-upload webapp for students to be able to upload works to the BDR.

---


# Running locally

Create a `.env` file in the outer directory based on `sample_dotenv.txt`. You will need to update the `MEDIA_ROOT` setting to a real path. 

Create a virtual environment using python 3.12 (anything earlier than 3.10 will cause an error due to syntax updates) and install requirements.

Create a directory called `DBs` in the outer directory. Then from the project root run `python manage.py makemigrations bdr_student_uploader_hub_app`. Then run `python manage.py migrate`. This should create a sqlite file in the DBs directory and set up all required tables. 

Then bring up the app and log in as staff to trigger the creation of the `staffperson` profile in the DB. 

Create a superuser and log into the django admin site. Once there, create a new permissions group with all permissions from the `submissions` app. Then edit the `staffperson` profile. Grant staff status and add the profile to the `submissions_editor` group. (Alternatively, just grant staff status and all permissions from the `submissions` app).

At this point, you should be able to log in as staff and create new apps, edit existing apps and see student submissions in the admin portal. You should also be able to log in as a student and upload media.

--- 

# Technical note

This webapp is configured to auto-create a UserProfile record, automatically, whenever a new User record is created -- whether via code or via the admin.

To enable that:
- `models.UserProfile()` was created.
- `apps.py` was added to the `bdr_student_uploader_hub_app` -- specifically to load `signals.py`.
- `signals.py` was added to trigger the `UserProfile` auto-creation.
- `settings.py` was updated to specify `bdr_student_uploader_hub_app.apps.BdrDepositsUploaderAppConfig`, instead of just `bdr_student_uploader_hub_app`.

---
