import logging

from django.contrib import admin, messages

from .models import AppConfig, Submission, UserProfile

log = logging.getLogger(__name__)


## for django-auth --------------------------------------------------
admin.site.register(UserProfile)


## other models -----------------------------------------------------


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'app', 'created_at', 'updated_at')
    list_filter = ('app', 'created_at', 'updated_at')
    search_fields = ('title', 'app', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    actions = ['ingest']

    def ingest(self, request, queryset):
        log.debug('ingest-action called')
        log.debug(f'queryset: ``{queryset}``')
        messages.info(request, 'Theses approved')
        for submission in queryset:
            log.debug(f'processing submission: ``{submission}``')
        return

    ingest.short_description = 'Ingest selected submissions'


admin.site.register(AppConfig)
admin.site.register(Submission, SubmissionAdmin)
