## ingester class responsible for preparing and ingesting a submission

import logging

log = logging.getLogger(__name__)


class Ingester:
    """
    Handles the ingestion of submission into the BDR.
    """

    def __init__(self, submission):
        self.submission = submission
        self.ingest_error_message: str | None = None
        self.bdr_pid: str | None = None

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
