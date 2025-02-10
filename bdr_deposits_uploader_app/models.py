import uuid

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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    temp_config_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.slug


class Submission(models.Model):
    """
    This model represents a user's submission of a deposit.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(AppConfig, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    upload = models.FileField(blank=True)
    original_file_name = models.CharField(max_length=255, blank=True, null=True)
    checksum_type = models.CharField(max_length=100, null=True, blank=True)
    checksum = models.CharField(max_length=255, null=True, blank=True)
    student_eppn = models.CharField(max_length=255, null=True, blank=True)
    student_email = models.CharField(max_length=255, null=True, blank=True)
    temp_submission_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        title_short = self.title
        if len(self.title) > 10:
            title_short = f'{self.title[0:10]}...'
        return title_short
