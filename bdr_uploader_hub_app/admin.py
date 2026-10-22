import logging

from django.contrib import admin

from .lib.ingester_handler import Ingester
from .lib.mods_handler import ModsMaker
from .models import AppConfig, Submission, UserProfile
from django.http import HttpResponse

log = logging.getLogger(__name__)


## for django-auth --------------------------------------------------
class UserProfileAdmin(admin.ModelAdmin):
    exclude = (
        'can_configure_these_apps',
        'can_view_these_apps',
    )  # not currently using these fields, so hiding them from the form to avoid confusion.


## other models -----------------------------------------------------


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'title', 'short_app_slug', 'status', 'bdr_pid', 'updated_at')
    list_filter = ('app', 'status', 'created_at', 'updated_at')
    search_fields = ('title', 'bdr_pid', 'app', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'staff_ingester', 'ingest_error_message', 'bdr_pid')

    actions = ['ingest', 'preview_mods']

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
        """
        Validates submissions to ensure they're all ready for ingestion.
        - on failure, admin is updated with items not ready, and the action is aborted.
        Ingests the selected submissions into the BDR.
        - on failure
            - submission.status is set to `ingest_error`
            - submission.ingest_error_message is set to the error message
        - on success
            - submission.status is set to `ingested`
            - submission.bdr_pid is set to the BDR PID
            - email is sent to the user confirming ingestion
        """
        log.debug('ingest-action called')
        log.debug(f'queryset: ``{queryset}``')
        ## confirm submissions are ready to ingest ------------------
        ok: bool
        err: str | None
        ingester = Ingester()
        (ok, err) = ingester.validate_queryset(request, queryset)  # ensures that all submissions are ready to ingest
        if not ok:
            return
        ## ingest the selected submissions --------------------------
        ingester.manage_ingest(request, queryset)
        return

    ingest.short_description = 'Ingest selected submissions'

    ## preview mods action -------------------------------------------
    def preview_mods(self, request, queryset):
        """
        Previews the MODS for a submission
        """
        log.debug('MODS preview requested')
        log.debug(f'queryset: ``{queryset}``')
        maker = ModsMaker(request)

        self.mods = ""
        self.is_xml = True
        for submission in queryset:
            self.submission = submission
            if self.mods:
                self.mods = self.mods+"\n\n---\n\n"
                self.is_xml = False
            try:
                self.mods: str = self.mods + ModsMaker(submission).prepare_mods()
            except Exception as e:
                log.exception(f'Error previewing submission: {submission}, Error: {e}')
                errors.append(message_error)
        httptype = "text/xml" if self.is_xml else "text"
        response = HttpResponse(self.mods,content_type=httptype)
        return response

    preview_mods.short_description = 'Preview the MODS to be generated'


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(AppConfig)  # using default admin-view
admin.site.register(Submission, SubmissionAdmin)
