"""
Notes...
- I don't usually use an apps.py file.
- My understanding is that it offers a way to run configuration code when the app is first loaded.
- I'm using what appears to be the default configuration -- even though I'm moving away 
  from working with integers for my models, in favor of UUIDs.
- The reason I'm adding this file is to try a suggestion for having a UserProfile record auto-created when
  a User record is created.
"""

from django.apps import AppConfig


class BdrDepositsUploaderAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bdr_deposits_uploader_app'

    def ready(self):
        import bdr_deposits_uploader_app.signals  # this is the reason for this apps.py file
