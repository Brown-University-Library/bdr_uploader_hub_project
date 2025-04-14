import logging

from django.contrib import admin, messages

from .lib.emailer import send_ingest_success_email
from .lib.ingester_handler import Ingester
from .models import AppConfig, Submission, UserProfile

log = logging.getLogger(__name__)


## for django-auth --------------------------------------------------
admin.site.register(UserProfile)


## other models -----------------------------------------------------


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'title', 'short_app_slug', 'status', 'bdr_pid', 'updated_at')
    list_filter = ('app', 'status', 'created_at', 'updated_at')
    search_fields = ('title', 'bdr_pid', 'app', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'staff_ingester', 'ingest_error_message', 'bdr_pid')

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
        ## confirm submissions are ready to ingest ------------------
        ok: bool
        err: str | None
        ingester = Ingester()
        (ok, err) = ingester.validate_queryset(request, queryset)  # ensures that all submissions are ready to ingest
        if not ok:
            return
        ## ingest the selected submissions --------------------------
        for submission in queryset:
            """
            attempt to ingest
            - on failure:
                - log problem
                - change status to `ingest_error`
                - save bdr-pid if I have it
                - save
            - on success:
                - change status to `ingested`
                - save bdr-pid
                - save
            """
            ## happy path, for logic --------------------------------
            ingester.submission = submission
            ingester.prepare_mods()
            ingester.prepare_rights()
            ingester.prepare_ir()
            ingester.prepare_rels()
            ingester.prepare_file()
            ingester.parameterize()
            result: tuple[str | None, str | None] = ingester.post()
            (pid, error_message) = result
            log.info(f'ingested submission: {submission}')
            submission.bdr_pid = pid
            submission.status = 'ingested'
            submission.ingest_error_message = None
            submission.save()
            send_ingest_success_email(
                submission.first_name, submission.email, submission.title, submission.bdr_url
            )  # bdr_url will be a property based on bdr_pid
            log.info('sent_ingestion_confirmation email')
        messages.success(request, 'Submissions ingested')
        return

    ingest.short_description = 'Ingest selected submissions'

    # ## ingest action ------------------------------------------------
    # def ingest(self, request, queryset):
    #     log.debug('ingest-action called')
    #     log.debug(f'queryset: ``{queryset}``')
    #     ## confirm that all selections are ready to ingest ----------
    #     errors: list = []
    #     for submission in queryset:
    #         log.debug(f'processing submission.title: ``{submission.title}``')
    #         log.debug(f'submission.status: ``{submission.status}``')
    #         if not submission.status == 'ready_to_ingest':
    #             errors.append(f'`{str(submission.id)[0:4]}...--{str(submission)}`')
    #             log.warning(
    #                 f'`{str(submission.id)[0:4]}...--{str(submission)}` not ready to ingest; status: {submission.status}'
    #             )
    #         if errors:
    #             messages.warning(request, f'Invalid selections: {", ".join(errors)}')
    #             return
    #     ## ingest the selected submissions --------------------------
    #     for submission in queryset:
    #         """
    #         attempt to ingest
    #         - on failure:
    #             - log problem
    #             - change status to `ingest_error`
    #             - save bdr-pid if I have it
    #             - save
    #         - on success:
    #             - change status to `ingested`
    #             - save bdr-pid
    #             - save
    #         """
    #         ## happy path, for logic --------------------------------
    #         ingester = Ingester(submission)
    #         ingester.prepare_mods()
    #         ingester.prepare_rights()
    #         ingester.prepare_ir()
    #         ingester.prepare_rels()
    #         ingester.prepare_file()
    #         ingester.parameterize()
    #         result: tuple[str | None, str | None] = ingester.post()
    #         (pid, error_message) = result
    #         log.info(f'ingested submission: {submission}')
    #         submission.bdr_pid = pid
    #         submission.status = 'ingested'
    #         submission.ingest_error_message = None
    #         submission.save()
    #         send_ingest_success_email(
    #             submission.first_name, submission.email, submission.title, submission.bdr_url
    #         )  # bdr_url will be a property based on bdr_pid
    #         log.info('sent_ingestion_confirmation email')
    #     messages.success(request, 'Submissions ingested')
    #     return

    # ingest.short_description = 'Ingest selected submissions'


admin.site.register(AppConfig)
admin.site.register(Submission, SubmissionAdmin)
