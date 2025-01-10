from django.contrib import admin

from .models import AppConfig, Submission, UserProfile

## for django-auth --------------------------------------------------
admin.site.register(UserProfile)


## other models -----------------------------------------------------


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'app', 'created_at', 'updated_at')
    list_filter = ('app', 'created_at', 'updated_at')
    search_fields = ('title', 'app', 'created_at', 'updated_at')
    ordering = ('-created_at',)


admin.site.register(AppConfig)
admin.site.register(Submission, SubmissionAdmin)
