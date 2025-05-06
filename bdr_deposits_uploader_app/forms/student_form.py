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
    fields['main_file'] = forms.FileField(label='Upload File', required=True, help_text='(required)')

    ## Collaborators section ----------------------------------------
    rq_AR = config_data.get('advisors_and_readers_required', False)
    log.debug(f'rq_AR, ``{rq_AR}``')
    if config_data.get('offer_advisors_and_readers'):
        if config_data.get('advisors_and_readers_required'):
            help_text = '(required) Person1 | Person2 | ...'
        else:
            help_text = 'Person1 | Person2 | ...'
        fields['advisors_and_readers'] = forms.CharField(
            label='Advisors and Readers',
            required=config_data.get('advisors_and_readers_required', False),
            help_text=help_text,
        )
        log.debug(f'AR-field after adding field: ``{pprint.pformat(fields["advisors_and_readers"].__dict__)}``')

    if config_data.get('offer_team_members'):
        if config_data.get('team_members_required'):
            help_text = '(required) Member1 | Member2 | ...'
        else:
            help_text = 'Member1 | Member2 | ...'
        fields['team_members'] = forms.CharField(
            label='Team Members',
            required=config_data.get('team_members_required', False),
            help_text=help_text,
        )
    if config_data.get('offer_faculty_mentors'):
        if config_data.get('faculty_mentors_required'):
            help_text = '(required) Mentor1 | Mentor2 | ...'
        else:
            help_text = 'Mentor1 | Mentor2 | ...'
        fields['faculty_mentors'] = forms.CharField(
            label='Faculty Mentors',
            required=config_data.get('faculty_mentors_required', False),
            help_text='Enter names or identifiers for faculty mentors',
        )
    if config_data.get('offer_authors'):
        if config_data.get('authors_required'):
            help_text = '(required) Author1 | Author2 | ...'
        else:
            help_text = 'Author1 | Author2 | ...'
        fields['authors'] = forms.CharField(
            label='Authors', required=config_data.get('authors_required', False), help_text=help_text
        )

    ## Department & Research Program section ------------------------
    if config_data.get('offer_department'):
        if config_data.get('department_required'):
            help_text = '(required) Dept1 | Dept2 | ...'
        else:
            help_text = 'Dept1 | Dept2 | ...'
        fields['department'] = forms.CharField(
            label='Department(s)',
            required=config_data.get('department_required', False),
            help_text=help_text,
        )

    if config_data.get('offer_research_program'):
        if config_data.get('research_program_required'):
            help_text = '(required) Program1 | Program2 | ...'
        else:
            help_text = 'Program1 | Program2 | ...'
        fields['research_program'] = forms.CharField(
            label='Research Program(s)',
            required=config_data.get('research_program_required', False),
            help_text=help_text,
        )
        log.debug(f'RP-field after adding field: ``{pprint.pformat(fields["research_program"].__dict__)}``')

    ## Access/license section ---------------------------------------
    if config_data.get('offer_license_options'):
        selected_license_keys: list[str] = config_data.get('license_options', [])
        selected_license_choices: list[tuple[str, str]] = [
            choice for choice in settings.ALL_LICENSE_OPTIONS if choice[0] in selected_license_keys
        ]
        selected_license_default: str = config_data.get('license_default')
        fields['license_options'] = forms.ChoiceField(
            choices=selected_license_choices,
            label='License Options',
            required=True,
            help_text='(required) select, or leave default',
            initial=selected_license_default,
        )
    fields['license_default'] = 'foo'

    ## Access/visibility section ------------------------------------
    if config_data.get('offer_visibility_options'):
        selected_visibility_keys: list[str] = config_data.get('visibility_options', [])
        selected_visibility_choices: list[tuple[str, str]] = [
            choice for choice in settings.ALL_VISIBILITY_OPTIONS if choice[0] in selected_visibility_keys
        ]
        selected_visibility_default: str = config_data.get('visibility_default')
        fields['visibility_options'] = forms.ChoiceField(
            choices=selected_visibility_choices,
            label='Visibility Options',
            required=True,
            help_text='(required) select, or leave default',
            initial=selected_visibility_default,
        )

    ## Other section -------------------------------------------------
    if config_data.get('ask_for_concentrations'):
        if config_data.get('concentrations_required'):
            help_text = '(required) Concentration1 | Concentration2 | ...'
        else:
            help_text = 'Concentration1 | Concentration2 | ...'
        fields['concentrations'] = forms.CharField(
            label='Concentrations',
            required=config_data.get('concentrations_required', False),
            help_text=help_text,
        )
    if config_data.get('ask_for_degrees'):
        if config_data.get('degrees_required'):
            help_text = '(required) Degree1 | Degree2 | ...'
        else:
            help_text = 'Degree1 | Degree2 | ...'
        fields['degrees'] = forms.CharField(
            label='Degrees', required=config_data.get('degrees_required', False), help_text=help_text
        )
    if config_data.get('invite_supplementary_files'):
        fields['supplementary_files'] = forms.FileField(
            label='Supplementary Files', required=False, help_text='Upload supplementary files if needed'
        )

    ## dynamically create new Form class ----------------------------
    StudentUploadForm = type('StudentUploadForm', (forms.Form,), fields)

    return StudentUploadForm
