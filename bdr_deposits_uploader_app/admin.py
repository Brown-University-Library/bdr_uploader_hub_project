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
        # messages.info(request, 'Theses approved')
        ## confirm that all selections are ready to ingest ----------
        errors: list = []
        for submission in queryset:
            log.debug(f'processing submission.title: ``{submission.title}``')
            log.debug(f'submission.status: ``{submission.status}``')
            if not submission.status == 'ready_to_ingest':
                # errors.append(str(submission))
                errors.append(f'`{str(submission.id)[0:4]}...--{str(submission)}`')
                # messages.warning(request, f'Submission ``{submission.title}`` not ready to ingest')
            if errors:
                messages.warning(request, f'Invalid selections: {", ".join(errors)}')
                return
        ## ingest the selected submissions --------------------------
        messages.success(request, 'Submissions ingested')
        return

    ingest.short_description = 'Ingest selected submissions'


admin.site.register(AppConfig)
admin.site.register(Submission, SubmissionAdmin)
