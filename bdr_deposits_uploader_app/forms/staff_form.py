from django import forms


class StaffForm(forms.Form):
    ## Form section - Collaborators ---------------------------------
    offer_advisors_and_readers = forms.BooleanField(required=False, label='Offer advisors and readers')
    advisors_and_readers_required = forms.BooleanField(required=False, label='Advisors and readers required')

    offer_team_members = forms.BooleanField(required=False, label='Offer team members')
    team_members_required = forms.BooleanField(required=False, label='Team members required')

    offer_faculty_mentors = forms.BooleanField(required=False, label='Offer faculty mentors')
    faculty_mentors_required = forms.BooleanField(required=False, label='Faculty mentors required')

    offer_authors = forms.BooleanField(required=False, label='Offer authors')
    authors_required = forms.BooleanField(required=False, label='Authors required')

    ## Form section - Department ------------------------------------
    offer_department = forms.BooleanField(required=False, label='Offer Department')
    department_required = forms.BooleanField(required=False, label='Department required')
    department_options = forms.MultipleChoiceField(
        required=False,
        label='Department Options',
        choices=[('dept1', 'Department 1'), ('dept2', 'Department 2')],
        widget=forms.CheckboxSelectMultiple,
    )

    offer_research_program = forms.BooleanField(required=False, label='Offer Research Program')
    research_program_required = forms.BooleanField(required=False, label='Research Program required')
    research_program_options = forms.MultipleChoiceField(
        required=False,
        label='Research Program Options',
        choices=[('prog1', 'Program 1'), ('prog2', 'Program 2')],
        widget=forms.CheckboxSelectMultiple,
    )

    ## Form section - Access ----------------------------------------
    offer_embargo_access = forms.BooleanField(required=False, label='Offer embargo-access for two years')

    offer_license_options = forms.BooleanField(required=False, label='Offer license options')
    license_required = forms.BooleanField(required=False, label='License required')
    license_options = forms.MultipleChoiceField(
        required=False, label='License Options', choices=[('license1', 'License 1'), ('license2', 'License 2')]
    )
    license_default = forms.CharField(required=False, label='License Default')

    offer_access_options = forms.BooleanField(required=False, label='Offer access options')
    access_required = forms.BooleanField(required=False, label='Access required')
    access_options = forms.MultipleChoiceField(
        required=False, label='Access Options', choices=[('access1', 'Access 1'), ('access2', 'Access 2')]
    )
    access_default = forms.CharField(required=False, label='Access Default')

    offer_visibility_options = forms.BooleanField(required=False, label='Offer visibility options')
    visibility_required = forms.BooleanField(required=False, label='Visibility required')
    visibility_options = forms.MultipleChoiceField(
        required=False, label='Visibility Options', choices=[('vis1', 'Visibility 1'), ('vis2', 'Visibility 2')]
    )
    visibility_default = forms.CharField(required=False, label='Visibility Default')

    ## Form section - Other -----------------------------------------
    ask_for_concentrations = forms.BooleanField(required=False, label='Ask for concentrations')
    concentrations_required = forms.BooleanField(required=False, label='Concentrations required')

    ask_for_degrees = forms.BooleanField(required=False, label='Ask for degrees')
    degrees_required = forms.BooleanField(required=False, label='Degrees required')

    invite_supplementary_files = forms.BooleanField(required=False, label='Invite supplementary files')

    ## end class StaffForm()
