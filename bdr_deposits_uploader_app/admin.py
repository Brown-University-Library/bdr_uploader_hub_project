import logging

from django.contrib import admin, messages

from .models import AppConfig, Submission, UserProfile

log = logging.getLogger(__name__)


## for django-auth --------------------------------------------------
admin.site.register(UserProfile)


## other models -----------------------------------------------------


class SubmissionAdmin(admin.ModelAdmin):
    # list_display = ('short_id', 'title', 'app', 'status', 'created_at', 'updated_at')
    list_display = ('short_id', 'title', 'short_app_slug', 'status', 'created_at', 'updated_at')
    list_filter = ('app', 'status', 'created_at', 'updated_at')
    search_fields = ('title', 'app', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')

    actions = ['ingest']

    ## id field -------------------------------------------------====
    def short_id(self, obj):
        uuid_str = str(obj.id)
        sh_id: str = f'{uuid_str[:4]}...'
        return sh_id

    short_id.short_description = 'UUID'

    ## short app-config slug display ---------------------------------------
    def short_app_slug(self, obj):
        slug = obj.app.slug
        return slug if len(slug) <= 10 else f'{slug[:4]}...{slug[-4:]}'

    short_app_slug.short_description = 'App Slug'

    ## ingest action ------------------------------------------------
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
