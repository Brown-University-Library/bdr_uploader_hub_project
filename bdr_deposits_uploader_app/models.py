from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    This extends the User object to include additional fields.

    This webapp is set up to create a UserProfile record automatically when a User record is created.
    See the README for more info about that.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_create_app = models.BooleanField(default=False)
    can_configure_these_apps = models.JSONField(default=list, blank=True)
    can_view_these_apps = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class AppConfig(models.Model):
    """
    This model represents an app that can be configured by staff.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    temp_config_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.slug
