from django.contrib import admin

from .models import AppConfig, Submission, UserProfile

## for django-auth
admin.site.register(UserProfile)

## other models
admin.site.register(AppConfig)
admin.site.register(Submission)
