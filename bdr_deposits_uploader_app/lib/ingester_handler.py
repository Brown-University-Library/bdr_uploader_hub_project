## ingester class responsible for preparing and ingesting a submission

import json
import logging
import pprint
from datetime import datetime
from pathlib import Path

import httpx
from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from lxml import etree

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
        self.mods = ''
        self.rights = {}
        self.ir = {}
        self.rels = {}
        self.file_data = {}

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
            log.debug(f'submission details:\n{pprint.pformat(submission.__dict__, indent=2)}')
            self.submission = submission
            try:
                f = submission.primary_file
                log.debug(f'type of f, ``{type(f)}``')
                self.mods: str = self.prepare_mods(submission.title)
                self.rights: dict = self.prepare_rights(submission.student_eppn, submission.visibility_options)
                self.ir: dict = self.prepare_ir(submission.student_eppn, submission.student_email)
                # self.rels: dict = self.prepare_rels(submission.app.temp_config_json)  # temp_config_json loads as a dict
                temp_config_data: dict = submission.app.temp_config_json  # loads as a dict
                self.rels: dict = self.prepare_rels(temp_config_data)  # temp_config_json loads as a dict
                self.file_data: dict = self.prepare_file(
                    submission.checksum_type,
                    submission.checksum,
                    submission.primary_file.path,
                    submission.original_file_name,
                )
                params: dict = self.parameterize()
                result: tuple[str | None, str | None] = self.post(params)
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
        xml_initial_str = render_to_string('xml_mods.xml', {'title': title, 'iso8601_creation_date': year})
        log.debug(f'\nmods xml_initial_str: {xml_initial_str}')
        xml_formatted_str = self.format_mods(xml_initial_str)
        log.debug(f'\nmods xml_formatted_str: {xml_formatted_str}')
        return xml_formatted_str

    def format_mods(self, unformatted_mods_string: str) -> str:
        """
        Formats the item_mods object via lxml.
        I tried formatting with BeautifulSoup, and minidom, but they both had issues; this is perfect for my needs.
        Note that the BDR-API _requires_ the typeOfResource element to be in the format: opening-element -> text -> closing-element -- which this formatting ensures.
        Called by manage_item_mods_creation()
        """
        log.debug('starting format_mods()')
        unformatted_mods_bytes: bytes = unformatted_mods_string.encode('utf-8')
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(unformatted_mods_bytes, parser=parser)
        formatted_mods_string = etree.tostring(tree, pretty_print=True).decode()  # type: ignore
        return formatted_mods_string

    def prepare_rights(self, student_eppn: str, visibility: str) -> dict:
        """
        Prepares the `rightsMetadata` data file for ingestion.

        ALL_VISIBILITY_OPTIONS_JSON = '[
            ["public", "Public"],
            ["private", "Private"],
            ["brown_only_discoverable", "Brown Only but discoverable"],
            ["brown_only_not_discoverable", "Brown Only not discoverable"]
        ]'

        From theses app: ```additional_rights =  f'{brown_group}#{main_rights}+{public_group}#discover'```
        """
        log.debug('prepare_rights called')
        ## populate the four strings --------------------------------
        owner_string = f'{student_eppn}#discover,display'
        admin_string = f'{settings.BDR_MANAGER_GROUP}#discover,display'
        public_string = ''
        brown_string = ''
        if visibility == 'public':
            public_string = f'{settings.BDR_PUBLIC_GROUP}#discover,display'
            brown_string = f'{settings.BDR_BROWN_GROUP}#discover,display'
        elif visibility == 'private':
            pass
        elif visibility == 'brown_only_discoverable':
            brown_string = f'{settings.BDR_BROWN_GROUP}#discover,display'
        elif visibility == 'brown_only_not_discoverable':
            brown_string = f'{settings.BDR_BROWN_GROUP}#display'
        else:  # shouldn't get here
            error_message = f'invalid visibility option: {visibility}'
            raise Exception(error_message)
        ## create the additional-rights string ----------------------
        if public_string:
            additional_rights = f'{admin_string}+{public_string}+{brown_string}'
        elif brown_string:
            additional_rights = f'{admin_string}+{brown_string}'
        else:  # private
            additional_rights = admin_string
        log.debug(f'owner_string: {owner_string}')
        ## create the rights json -----------------------------------
        rights: dict = {
            'owner_id': owner_string,
            'additional_rights': additional_rights,
        }
        log.debug(f'rights: {pprint.pformat(rights)}')
        return rights

    def prepare_ir(self, student_eppn: str, student_email: str) -> dict:
        """
        Prepares the IR data for ingestion.
        """
        log.debug('prepare_ir called')
        ir_params = {}
        ir_params['depositor_eppn'] = student_eppn
        ir_params['depositor_email'] = student_email
        log.debug(f'ir_params: {pprint.pformat(ir_params)}')
        return ir_params

    def prepare_rels(self, app_config_dict_from_json: dict) -> dict:
        """
        Prepares the RELS-EXT data for ingestion.
        All the api call needs is a simple json dict with the collection_pid.
        """
        log.debug('prepare_rels called')
        collection_pid: str = app_config_dict_from_json['collection_pid']
        rels_ext = {'isMemberOfCollection': collection_pid}
        log.debug(f'rels_ext: {rels_ext}')
        return rels_ext

    def prepare_file(
        self, submission_checksum_type: str, submission_checksum: str, file_path: str, original_file_name: str
    ) -> dict:
        """
        Prepares file-data ingestion.
        """
        log.debug('prepare_file called')
        ## get bdr-api-filepath -------------------------------------
        saved_file_path: Path = Path(file_path)
        rslt: tuple[Path, str] = (saved_file_path.parent, saved_file_path.name)
        (path, filename) = rslt
        log.debug(f'path: ``{path}``, filename: ``{filename}``')
        bdr_api_file_path_root: Path = Path(settings.BDR_API_FILE_PATH_ROOT)
        bdr_api_file_path: Path = bdr_api_file_path_root / filename
        log.debug(f'bdr_api_file_path: ``{bdr_api_file_path}``')
        bdr_api_file_path_str: str = str(bdr_api_file_path)
        ## prepare file-data ------------------------------------------
        file_data = {
            'checksum_type': submission_checksum_type,
            'checksum': submission_checksum,
            'file_name': original_file_name,
            'path': bdr_api_file_path_str,
        }
        log.debug(f'file_data: {pprint.pformat(file_data)}')
        return file_data

    # def prepare_file(
    #     self, submission_checksum_type: str, submission_checksum: str, file_path: str, original_file_name: str
    # ) -> dict:
    #     """
    #     Prepares file-data ingestion.
    #     """
    #     log.debug('prepare_file called')
    #     file_data = {
    #         'checksum_type': submission_checksum_type,
    #         'checksum': submission_checksum,
    #         'file_name': original_file_name,
    #         'path': file_path,
    #     }
    #     log.debug(f'file_data: {pprint.pformat(file_data)}')
    #     return file_data

    def parameterize(self) -> dict:
        """
        Parameterizes the submission data for ingestion.
        """
        log.debug('parameterize() called')
        ## prep data ------------------------------------------------
        mods_param = json.dumps({'xml_data': self.mods})
        rights_param = json.dumps({'parameters': self.rights})
        ir_param = json.dumps({'parameters': self.ir})
        rels_param = json.dumps(self.rels)
        file_param = json.dumps([self.file_data])  # bdr-api requires list

        ## assemble main params -------------------------------------
        params = {}
        params['mods'] = mods_param
        params['rights'] = rights_param
        params['ir'] = ir_param
        params['rels'] = rels_param
        params['content_streams'] = file_param
        ## assemble other params ------------------------------------
        # permission_ids_param_a: list = [settings.BDR_MANAGER_GROUP]
        # permission_ids_param_b: str = json.dumps(permission_ids_param_a)
        params['permission_ids'] = json.dumps([settings.BDR_MANAGER_GROUP])
        params['agent_name'] = 'BDR_UPLOAD_HUB'
        # params['agent_address'] = ''
        log.debug(f'params: {pprint.pformat(params)}')
        return params

    def post(self, params) -> tuple[str | None, str | None]:
        """
        Posts the submission to the BDR for ingestion.
        """
        log.debug('post called')
        error_message = ''
        resp = httpx.post(settings.BDR_PRIVATE_API_ROOT_URL, data=params)
        log.debug(f'type(resp), ``{type(resp)}``; resp.status_code, ``{resp.status_code}``')
        if resp.status_code == 200:
            data_dict = resp.json()
            self.bdr_pid = data_dict['pid']
        else:
            error_message = f'bad bdr-api response; status_code, ``{resp.status_code}``; text, ``{resp.text}``'
            raise Exception(error_message)
        log.exception(error_message)
        return (self.bdr_pid, error_message)
