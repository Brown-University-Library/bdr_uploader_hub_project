# purpose

This webapp will allow Library staff to configure a new BDR (Brown Digital Repository) deposits-upload url for students to be able to upload works to the BDR.

---

Technical note: this webapp is configured to auto-create a UserProfile record, automatically, whenever a new User record is created -- whether via code or via the admin.

To enable that:
- models.UserProfile() was created
- apps.py was added to the bdr_deposits_uploader_app -- specifically to load signals.py
- signals.py was added to trigger the UserProfile auto-creation.
- settings.py was updated to specify `bdr_deposits_uploader_app.apps.BdrDepositsUploaderAppConfig`, instead of just `bdr_deposits_uploader_app`

---

# Running Locally
Create a `.env` file in the outer directory based on `sample_dotenv.txt`. You will need to update the `MEDIA_ROOT` setting to a real path. Additionally, change the `SHIB_IDP_LOGOUT_URL` to use the real SSO domain. `SHIB_SP_LOGIN_URL` is not used locally and doesn't need to be updated.

Create a virtual environment using python 3.12 (anything earlier than 3.10 will cause an error due to syntax updates) and install requirements.

Create a directory called `DBs` in the outer directory. Then from the project root run `python manage.py makemigrations bdr_deposits_uploader_app`. Then run `python manage.py migrate`. This should create a sqlite file in the DBs directory and set up all required tables. 

Then bring up the app and log in as staff to trigger the creation of the `staffperson` profile in the DB. 

Create a superuser and log into the django admin site. Once there, create a new permissions group with all permissions from the `submissions` app. Then edit the `staffperson` profile. Grant staff status and add the profile to the `submissions_editor` group. (Alternatively, just grant staff status and all permissions from the `submissions` app).

At this point, you should be able to log in as staff and create new apps, edit existing apps and see student submissions in the admin portal. You should also be able to log in as a student and upload media.