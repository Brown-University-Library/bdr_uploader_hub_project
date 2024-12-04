from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    extra_field_a = models.CharField(max_length=20, unique=True)
    extra_field_b = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
