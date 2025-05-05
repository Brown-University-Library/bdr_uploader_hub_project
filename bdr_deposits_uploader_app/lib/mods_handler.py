import logging

from django.template.loader import get_template

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
        title = self.submission.title
        abstract = self.submission.abstract
        ## originInfo -----------------------------------------------
        year_created = str(self.submission.created_at.year)  # W3CDTF year
        date_created = self.submission.created_at.strftime('%Y-%m-%d')  # W3CDTF date
        ## assembling data -------------------------------------------
        context = {
            'title': title,
            'abstract': abstract,
            'year_created': year_created,
            'date_created': date_created,
        }
        ## render the template ---------------------------------------
        template = get_template('mods_base.xml')
        mods_xml: str = template.render(context)
        log.debug(f'mods_xml: ``{mods_xml}``')
        return mods_xml
