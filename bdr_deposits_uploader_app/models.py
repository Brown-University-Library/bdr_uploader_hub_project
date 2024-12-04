from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    This extends the User object to include additional fields.

    This webapp is set up to create a UserProfile record automatically when a User record is created.
    See the README for more info about that.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    extra_field_a = models.CharField(max_length=20, unique=False, null=True, blank=True)
    extra_field_b = models.CharField(max_length=20, unique=False, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
