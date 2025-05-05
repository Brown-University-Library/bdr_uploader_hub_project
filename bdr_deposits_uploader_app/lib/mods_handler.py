import logging
from bdr_deposits_uploader_app.models import Submission

log = logging.getLogger(__name__)


class ModsMaker:
    def __init__(self, submission: Submission):
        self.submission: Submission = submission

    def prepare_mods(self) -> str:
        """
        Manages the creation of the mods xml file.
        """
        log.debug('prepare_mods called')
