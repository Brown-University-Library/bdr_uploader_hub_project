import logging
import pprint

from django import forms

log = logging.getLogger(__name__)


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
        help_text='Select one or more departments',
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

    authorized_student_groups = forms.CharField(
        required=False,
        label='Authorized student grouper-groups',
        help_text='Preferred to student-emails. <br>Example: "group:A | group:B"',
        widget=forms.Textarea,
    )
    authorized_student_emails = forms.CharField(
        required=False, label='Authorized student emails', help_text='Example: "email1 | email2"', widget=forms.Textarea
    )

    def clean(self):
        log.debug('starting StaffForm.clean()')
        cleaned_data = super().clean()
        log.debug(f'type(cleaned_data): {type(cleaned_data)}')

        ## if a required field is True but the corresponding offer field is not, update the offer field in cleaned_data to True.

        ## collaborators --------------------------------------------
        if cleaned_data.get('advisors_and_readers_required') and not cleaned_data.get('offer_advisors_and_readers'):
            cleaned_data['offer_advisors_and_readers'] = True
        if cleaned_data.get('team_members_required') and not cleaned_data.get('offer_team_members'):
            cleaned_data['offer_team_members'] = True
        if cleaned_data.get('faculty_mentors_required') and not cleaned_data.get('offer_faculty_mentors'):
            cleaned_data['offer_faculty_mentors'] = True
        if cleaned_data.get('authors_required') and not cleaned_data.get('offer_authors'):
            cleaned_data['offer_authors'] = True
        ## department / programs ------------------------------------
        if cleaned_data.get('department_required') and not cleaned_data.get('offer_department'):
            cleaned_data['offer_department'] = True
        if cleaned_data.get('research_program_required') and not cleaned_data.get('offer_research_program'):
            cleaned_data['offer_research_program'] = True
        ## access ---------------------------------------------------
        if cleaned_data.get('license_required') and not cleaned_data.get('offer_license_options'):
            cleaned_data['offer_license_options'] = True
        if cleaned_data.get('access_required') and not cleaned_data.get('offer_access_options'):
            cleaned_data['offer_access_options'] = True
        if cleaned_data.get('visibility_required') and not cleaned_data.get('offer_visibility_options'):
            cleaned_data['offer_visibility_options'] = True
        ## other ----------------------------------------------------
        if cleaned_data.get('concentrations_required') and not cleaned_data.get('ask_for_concentrations'):
            cleaned_data['ask_for_concentrations'] = True
        if cleaned_data.get('degrees_required') and not cleaned_data.get('ask_for_degrees'):
            cleaned_data['ask_for_degrees'] = True

        ## validate that when options are required, at least one option is selected.

        if cleaned_data.get('offer_department') and cleaned_data.get('department_required'):
            if not cleaned_data.get('department_options'):
                self.add_error('department_options', 'At least one department must be selected.')
        if cleaned_data.get('offer_research_program') and cleaned_data.get('research_program_required'):
            if not cleaned_data.get('research_program_options'):
                self.add_error('research_program_options', 'At least one research program must be selected.')
        if cleaned_data.get('offer_license_options') and cleaned_data.get('license_required'):
            if not cleaned_data.get('license_options'):
                self.add_error('license_options', 'At least one license must be selected.')
            if not cleaned_data.get('license_default'):
                self.add_error('license_default', 'A default license is required.')
        if cleaned_data.get('offer_access_options') and cleaned_data.get('access_required'):
            if not cleaned_data.get('access_options'):
                self.add_error('access_options', 'At least one access option must be selected.')
            if not cleaned_data.get('access_default'):
                self.add_error('access_default', 'A default access option is required.')
        if cleaned_data.get('offer_visibility_options'):
            log.debug('HereA')
            if not cleaned_data.get('visibility_options'):
                self.add_error('visibility_options', 'At least one visibility option must be selected.')
            if not cleaned_data.get('visibility_default'):
                self.add_error('visibility_default', 'A default visibility option is required.')

        log.debug(f'cleaned_data: {pprint.pformat(cleaned_data)}')
        return cleaned_data

        ## end def clean()

    ## end class StaffForm()
