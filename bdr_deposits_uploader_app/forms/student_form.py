import logging
import pprint

from django import forms
from django.conf import settings

log = logging.getLogger(__name__)


def make_student_form_class(config_data: dict) -> type[forms.Form]:
    """
    Dynamically creates and returns a StudentUploadForm class based on the staff-config form data.
    """
    log.debug('starting make_student_form_class()')
    log.debug(f'config_data: {pprint.pformat(config_data)}')

    fields = {}

    ## Basic Information section ------------------------------------
    fields['title'] = forms.CharField(
        label='Title',
        required=True,
        help_text='(required)',
    )
    fields['abstract'] = forms.CharField(
        label='Abstract',
        required=True,
        help_text='(required)',
        widget=forms.Textarea,
    )

    ## Collaborators section ----------------------------------------
    rq_AR = config_data.get('advisors_and_readers_required', False)
    log.debug(f'rq_AR, ``{rq_AR}``')
    if config_data.get('offer_advisors_and_readers'):
        fields['advisors_and_readers'] = forms.CharField(
            label='Advisors and Readers',
            required=config_data.get('advisors_and_readers_required', False),
            help_text='Person1 | Person2 | ...',
        )
        log.debug(f'AR-field after adding field: ``{pprint.pformat(fields["advisors_and_readers"].__dict__)}``')

    if config_data.get('offer_team_members'):
        fields['team_members'] = forms.CharField(
            label='Team Members',
            required=config_data.get('team_members_required', False),
            help_text='Enter names or identifiers for team members',
        )
    if config_data.get('offer_faculty_mentors'):
        fields['faculty_mentors'] = forms.CharField(
            label='Faculty Mentors',
            required=config_data.get('faculty_mentors_required', False),
            help_text='Enter names or identifiers for faculty mentors',
        )
    if config_data.get('offer_authors'):
        fields['authors'] = forms.CharField(
            label='Authors', required=config_data.get('authors_required', False), help_text='Enter author names'
        )

    ## Department & Research Program section ------------------------
    if config_data.get('offer_department'):
        fields['department'] = forms.CharField(
            label='Department(s)',
            required=config_data.get('department_required', False),
            help_text='Dept1 | Dept2 | ...',
        )

    rq_RP = config_data.get('research_program_required', False)
    log.debug(f'rq_RP, ``{rq_RP}``')
    if config_data.get('offer_research_program'):
        fields['research_program'] = forms.CharField(
            label='Research Program(s)',
            required=config_data.get('research_program_required', False),
            help_text='Program1 | Program2 | ...',
        )
        log.debug(f'RP-field after adding field: ``{pprint.pformat(fields["research_program"].__dict__)}``')

    ## Access section ------------------------------------------------
    if config_data.get('offer_license_options'):
        selected_license_keys: list[str] = config_data.get('license_options', [])
        selected_license_choices: list[tuple[str, str]] = [
            choice for choice in settings.ALL_LICENSE_OPTIONS if choice[0] in selected_license_keys
        ]
        selected_license_default: str = config_data.get('license_default')
        fields['license_options'] = forms.ChoiceField(
            choices=selected_license_choices,
            label='License Options',
            required=config_data.get('license_required', False),
            help_text='select, or leave default',
            initial=selected_license_default,
        )

    if config_data.get('offer_visibility_options'):
        selected_visibility_keys: list[str] = config_data.get('visibility_options', [])
        selected_visibility_choices: list[tuple[str, str]] = [
            choice for choice in settings.ALL_VISIBILITY_OPTIONS if choice[0] in selected_visibility_keys
        ]
        selected_visibility_default: str = config_data.get('visibility_default')
        fields['visibility_options'] = forms.ChoiceField(
            choices=selected_visibility_choices,
            label='Visibility Options',
            required=config_data.get('visibility_required', False),
            help_text='select, or leave default',
            initial=selected_visibility_default,
        )

    ## Other section -------------------------------------------------
    if config_data.get('ask_for_concentrations'):
        fields['concentrations'] = forms.CharField(
            label='Concentrations',
            required=config_data.get('concentrations_required', False),
            help_text='Enter concentration information',
        )
    if config_data.get('ask_for_degrees'):
        fields['degrees'] = forms.CharField(
            label='Degrees', required=config_data.get('degrees_required', False), help_text='Enter degree information'
        )
    if config_data.get('invite_supplementary_files'):
        fields['supplementary_files'] = forms.FileField(
            label='Supplementary Files', required=False, help_text='Upload supplementary files if needed'
        )

    ## dynamically create new Form class ----------------------------
    StudentUploadForm = type('StudentUploadForm', (forms.Form,), fields)

    return StudentUploadForm
