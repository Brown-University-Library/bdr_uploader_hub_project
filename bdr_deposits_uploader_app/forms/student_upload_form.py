import logging
import pprint

from django import forms

log = logging.getLogger(__name__)

ALL_LICENSES: list[tuple[str, str]] = [
    ('license1', 'License 1'),
    ('license2', 'License 2'),
    ('license3', 'License 3'),
    ('license4', 'License 4'),
    ('license5', 'License 5'),
    ('license6', 'License 6'),
]


def make_student_upload_form_class(config_data: dict) -> type[forms.Form]:
    """
    Dynamically creates and returns a StudentUploadForm class based on the staff-config form data.
    """
    log.debug('starting make_student_upload_form_class()')
    log.debug(f'config_data: {pprint.pformat(config_data)}')

    fields = {}

    ## Basic Information section ------------------------------------
    fields['title'] = forms.CharField(
        label='Title',
        required=config_data.get('title_required', False),
        help_text='(required)',
    )
    fields['abstract'] = forms.CharField(
        label='Abstract',
        required=config_data.get('abstract_required', False),
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
        selected_license_keys = config_data.get('license_options', [])
        selected_choices = [choice for choice in ALL_LICENSES if choice[0] in selected_license_keys]
        fields['license_options'] = forms.ChoiceField(
            choices=selected_choices,
            label='License Options',
            required=config_data.get('license_required', False),
            help_text='select a license',
            initial='license5',
        )

    if config_data.get('offer_access_options'):
        fields['access_options'] = forms.MultipleChoiceField(
            choices=[('access1', 'Access 1'), ('access2', 'Access 2')],
            label='Access Options',
            required=config_data.get('access_required', False),
            help_text='Select at least one access option',
        )
        fields['access_default'] = forms.CharField(
            label='Access Default',
            required=config_data.get('access_required', False),
            help_text='Enter the default access option',
        )
    if config_data.get('offer_visibility_options'):
        fields['visibility_options'] = forms.MultipleChoiceField(
            choices=[('vis1', 'Visibility 1'), ('vis2', 'Visibility 2')],
            label='Visibility Options',
            required=config_data.get('visibility_required', False),
            help_text='Select at least one visibility option',
        )
        fields['visibility_default'] = forms.CharField(
            label='Visibility Default',
            required=config_data.get('visibility_required', False),
            help_text='Enter the default visibility',
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
