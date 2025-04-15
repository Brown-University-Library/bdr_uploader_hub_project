## ingester class responsible for preparing and ingesting a submission

import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string

from bdr_deposits_uploader_app.models import Submission

from .emailer import send_ingest_success_email

log = logging.getLogger(__name__)


class Ingester:
    """
    Handles the ingestion of submission into the BDR.
    """

    def __init__(self):
        self.submission: Submission | None = None
        self.ingest_error_message: str | None = None
        self.bdr_pid: str | None = None

    def validate_queryset(self, request, queryset):
        """
        Validates the queryset to ensure all submissions are ready for ingestion.
        The `messages.warning(request, err)` displays a warning message on the admin-page.
        Called by the `ingest` action in the SubmissionAdmin class.
        """
        log.debug('validate_queryset called')
        errors: list = []
        ok: bool = False
        err: str | None = None
        for submission in queryset:
            log.debug(f'processing submission.title: ``{submission.title}``')
            log.debug(f'submission.status: ``{submission.status}``')
            if not submission.status == 'ready_to_ingest':
                errors.append(f'`{str(submission.id)[0:4]}...--{str(submission)}`')
                log.warning(
                    f'`{str(submission.id)[0:4]}...--{str(submission)}` not ready to ingest; status: {submission.status}'
                )
        if errors:
            err = f'Invalid selections: {", ".join(errors)}'
            messages.warning(request, err)
        else:
            ok = True
            log.debug('All submissions are ready to ingest.')
        log.debug(f'ok, ``{ok}``; err, ``{err}``')
        return (ok, err)

    def manage_ingest(self, request, queryset) -> None:
        """
        Manages the ingestion of the selected submissions into the BDR.
        Called by the `ingest` action in the SubmissionAdmin class.
        """
        log.debug('manage_ingest called')
        errors = []
        for submission in queryset:
            self.submission = submission
            try:
                self.prepare_mods(submission.title)
                self.prepare_rights(submission.student_eppn)
                self.prepare_ir(submission.student_eppn, submission.student_email)
                self.prepare_rels(submission.app.temp_config_json)  # temp_config_json loads as a dict
                self.prepare_file()
                self.parameterize()
                result: tuple[str | None, str | None] = self.post()
                (pid, err) = result
                submission.bdr_pid = pid
                submission.status = 'ingested'
                submission.ingest_error_message = None
                submission.save()
                send_ingest_success_email(
                    request.user.first_name, submission.student_email, submission.title, submission.bdr_url
                )  # bdr_url will be a property based on bdr_pid
                log.info('sent_ingestion_confirmation email')
            except Exception as e:
                log.exception(f'Error ingesting submission: {submission}, Error: {e}')
                submission.status = 'ingest_error'
                submission.ingest_error_message = str(e)
                submission.save()
                message_error = f'`{str(submission.id)[0:4]}...--{str(submission)}`'
                errors.append(message_error)
        if errors:
            messages.error(request, f'Some errors occurred during ingestion, for items: {", ".join(errors)}')
        else:
            messages.success(request, 'Submissions ingested')

    def prepare_mods(self, title: str) -> str:
        """
        Renders the xml_mods.xml template using the given title and returns it as a string.
        """
        log.debug('prepare_mods called')
        year: str = str(datetime.now().year)
        xml_str = render_to_string('xml_mods.xml', {'title': title, 'iso8601_creation_date': year})
        log.debug(f'\nmods xml_str: {xml_str}')
        return xml_str

    def prepare_rights(self, user_eppn: str) -> str:
        """
        Prepares the `rightsMetadata` xml file for ingestion.
        """
        log.debug('prepare_rights called')
        xml_str = render_to_string(
            'xml_rights.xml',
            {
                'BDR_MANAGER_GROUP': settings.BDR_MANAGER_GROUP,
                'individual': user_eppn,
                'BDR_BROWN_GROUP': settings.BDR_BROWN_GROUP,
                'BDR_PUBLIC_GROUP': settings.BDR_PUBLIC_GROUP,
            },
        )
        log.debug(f'\nrights xml_str: {xml_str}')
        return xml_str

    def prepare_ir(self, student_eppn: str, student_email: str) -> str:
        """
        Prepares the IR data for ingestion.
        """
        log.debug('prepare_ir called')
        ir_params = {}
        ir_params['depositor_eppn'] = student_eppn
        ir_params['depositor_email'] = student_email
        ir_json = json.dumps(ir_params)
        log.debug(f'ir json: {ir_json}')
        return ir_json

    def prepare_rels(self, app_config_dict_from_json: dict) -> str:
        """
        Prepares the RELS-EXT data for ingestion.
        All the api call needs is a simple json dict with the collection_pid.
        """
        log.debug('prepare_rels called')
        collection_pid: str = app_config_dict_from_json['collection_pid']
        rels_ext_json = json.dumps({'isMemberOfCollection': collection_pid})
        log.debug(f'rels_ext json: {rels_ext_json}')
        return rels_ext_json

    def prepare_file(self):
        """
        Prepares the file for ingestion.
        """
        log.debug('prepare_file called')
        # Logic to prepare file
        # self.submission.file = ...
        pass

    def parameterize(self):
        """
        Parameterizes the submission for ingestion.
        """
        log.debug('parameterize called')
        # Logic to parameterize submission
        # self.submission.parameterized = ...
        pass

    def post(self) -> tuple[str | None, str | None]:
        """
        Posts the submission to the BDR for ingestion.
        """
        log.debug('post called')
        # Logic to post submission
        # self.submission.posted = ...
        # return (self.bdr_pid, self.ingest_error_message)
        return (self.bdr_pid, self.ingest_error_message)
