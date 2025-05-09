import logging

from django.template.loader import get_template
from lxml import etree
from lxml.etree import XMLSyntaxError

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

        ## authors --------------------------------------------------
        author_data: str = self.submission.authors or ''
        authors: list[str] = [author.strip() for author in author_data.split('|')] if author_data else []
        log.debug(f'authors: {authors}')

        ## advisors/readers -----------------------------------------
        advisor_reader_data: str = self.submission.advisors_and_readers or ''
        advisor_reader_names: list[str] = (
            [name.strip() for name in advisor_reader_data.split('|')] if advisor_reader_data else []
        )
        log.debug(f'advisor_reader_names: {advisor_reader_names}')

        ## concentrations -------------------------------------------
        concentration_data: str = self.submission.concentrations or ''
        concentrations: list[str] = (
            [concentration.strip() for concentration in concentration_data.split('|')] if concentration_data else []
        )
        log.debug(f'concentrations: {concentrations}')

        ## degrees --------------------------------------------------
        degree_data: str = self.submission.degrees or ''
        degrees: list[str] = [degree.strip() for degree in degree_data.split('|')] if degree_data else []
        log.debug(f'degrees: {degrees}')

        ## assembling data -------------------------------------------
        context = {
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'advisor_reader_names': advisor_reader_names,
            'concentrations': concentrations,
            'degrees': degrees,
            'year_created': year_created,
            'date_created': date_created,
        }
        ## render the template ---------------------------------------
        template = get_template('mods_base.xml')
        mods_xml: str = template.render(context)
        log.debug(f'mods_xml: ``{mods_xml}``')

        ## validate the xml ------------------------------------------
        self.validate_xml(mods_xml)

        ## format the xml --------------------------------------------
        formatted_xml: str = self.format_xml(mods_xml)
        log.debug(f'formatted_xml: ``{formatted_xml}``')

        ## return the formatted xml ----------------------------------
        return formatted_xml

        ## end def prepare_mods()

    def validate_xml(self, xml: str) -> None:
        """
        Validates the XML string using lxml.

        Args:
            xml: XML string to validate

        Raises:
            ValueError: If the XML is not well-formed
        """
        log.debug(f'validating xml: ``{xml}``')
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            etree.fromstring(xml.encode('utf-8'), parser=parser)
            return True
        except XMLSyntaxError:
            log.exception('XMLSyntaxError')
            return False

    def format_xml(self, xml: str) -> str:
        """Formats the xml string via lxml.
        I tried formatting with BeautifulSoup, and minidom, but they both had issues; this is perfect for my needs.
        Note that the BDR-API _requires_ the typeOfResource element to be in the format: opening-element -> text -> closing-element -- which this formatting ensures.
        Called by manage_item_mods_creation()"""
        from lxml import etree

        xml_bytes: bytes = xml.encode('utf-8')
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_bytes, parser=parser)
        xml_formatted = etree.tostring(tree, pretty_print=True).decode()  # type: ignore
        return xml_formatted
