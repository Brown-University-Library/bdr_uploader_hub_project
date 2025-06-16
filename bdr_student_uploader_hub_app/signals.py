"""
Implements signals for the bdr_deposits_uploader_app.
Enables auto-creation of a UserProfile record when a new User record is created.
See the README for more info.
"""

import logging
from typing import Any, Type

from django.conf import settings
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

from bdr_deposits_uploader_app.models import UserProfile

log = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    if created:
        log.debug('created was True, so getting or creating a UserProfile record')
        UserProfile.objects.get_or_create(user=instance)  # check if a UserProfile already exists to avoid duplication-error
    else:
        log.debug('created was False, so updating the existing UserProfile record')
        instance.userprofile.save()  # update or save existing UserProfile
