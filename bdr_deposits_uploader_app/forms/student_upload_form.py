from django import forms


def make_student_upload_form_class(config_data: dict) -> type[forms.Form]:
    """
    Dynamically creates and returns a StudentUploadForm class based on the staff-config form data.
    """
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
    if config_data.get('offer_advisors_and_readers'):
        fields['advisors_and_readers'] = forms.CharField(
            label='Advisors and Readers',
            required=config_data.get('advisors_and_readers_required', False),
            help_text='Person1 | Persion2 | ...',
        )
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
        # fields['department_options'] = forms.MultipleChoiceField(
        #     choices=[('dept1', 'Department 1'), ('dept2', 'Department 2')],
        #     widget=forms.CheckboxSelectMultiple,
        #     label='Department Options',
        #     required=config_data.get('department_required', False),
        #     help_text='Select one or more departments',
        # )

        fields['department'] = forms.CharField(
            label='Department(s)',
            required=config_data.get('department_required', False),
            help_text='Dept1 | Dept2 | ...',
        )

    if config_data.get('offer_research_program'):
        # fields['research_program_options'] = forms.MultipleChoiceField(
        #     choices=[('prog1', 'Program 1'), ('prog2', 'Program 2')],
        #     widget=forms.CheckboxSelectMultiple,
        #     label='Research Program Options',
        #     required=config_data.get('research_program_required', False),
        #     help_text='Select one or more research programs',
        # )

        fields['research_program'] = forms.CharField(
            label='Research Program(s)',
            required=config_data.get('research_program_required', False),
            help_text='Program1 | Program2 | ...',
        )

    ## Access section ------------------------------------------------
    if config_data.get('offer_license_options'):
        fields['license_options'] = forms.MultipleChoiceField(
            choices=[('license1', 'License 1'), ('license2', 'License 2')],
            label='License Options',
            required=config_data.get('license_required', False),
            help_text='Select at least one license',
        )
        fields['license_default'] = forms.CharField(
            label='License Default',
            required=config_data.get('license_required', False),
            help_text='Enter the default license',
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
