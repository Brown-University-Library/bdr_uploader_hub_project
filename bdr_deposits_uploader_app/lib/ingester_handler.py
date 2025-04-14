## ingester class responsible for preparing and ingesting a submission

import logging

from django.contrib import messages

from bdr_deposits_uploader_app.models import Submission

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

    def prepare_mods(self):
        """
        Prepares the MODS file for ingestion.
        """
        log.debug('prepare_mods called')
        # Logic to prepare MODS file
        # self.submission.mods_file = ...
        pass

    def prepare_rights(self):
        """
        Prepares the rights file for ingestion.
        """
        log.debug('prepare_rights called')
        # Logic to prepare rights file
        # self.submission.rights_file = ...
        pass

    def prepare_ir(self):
        """
        Prepares the IR file for ingestion.
        """
        log.debug('prepare_ir called')
        # Logic to prepare IR file
        # self.submission.ir_file = ...
        pass

    def prepare_rels(self):
        """
        Prepares the RELS file for ingestion.
        """
        log.debug('prepare_rels called')
        # Logic to prepare RELS file
        # self.submission.rels_file = ...
        pass

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
