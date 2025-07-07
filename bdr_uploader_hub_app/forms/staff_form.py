import logging

from django import forms
from django.conf import settings

from bdr_uploader_hub_app.forms.staff_form_validation import validate_staff_form

log = logging.getLogger(__name__)


class StaffForm(forms.Form):
    ## Basics section -----------------------------------------------
    collection_pid = forms.CharField(required=True, label='Collection PID')
    collection_title = forms.CharField(required=True, label='Collection Title', help_text='PID sanity-check')
    staff_to_notify = forms.CharField(
        required=True,
        label='Staff to notify on ingest',
        help_text='email1 | email2 | ...',
    )

    authorized_student_groups = forms.CharField(
        required=False,
        label='Authorized student groups',
        help_text='group:A | group:B | ...',
        widget=forms.Textarea(
            attrs={'rows': 5}
        ),  # or I could say widget=forms.Textarea(attrs={'class': 'textarea'}), and then style it in css
    )
    authorized_student_emails = forms.CharField(
        required=False,
        label='Authorized student emails',
        help_text='email1 | email2 | ...',
        widget=forms.Textarea(attrs={'rows': 5}),
    )

    ## Form section - Collaborators ---------------------------------
    offer_advisors_and_readers = forms.BooleanField(required=False, label='Offer advisors/readers')
    advisors_and_readers_required = forms.BooleanField(
        required=False, label='Advisors/readers required', help_text='auto-selects `Offer...` on save'
    )

    offer_team_members = forms.BooleanField(required=False, label='Offer team members')
    team_members_required = forms.BooleanField(
        required=False, label='Team members required', help_text='auto-selects `Offer...` on save'
    )

    offer_faculty_mentors = forms.BooleanField(required=False, label='Offer faculty mentors')
    faculty_mentors_required = forms.BooleanField(
        required=False, label='Faculty mentors required', help_text='auto-selects `Offer...` on save'
    )

    offer_authors = forms.BooleanField(required=False, label='Offer authors')
    authors_required = forms.BooleanField(
        required=False, label='Authors required', help_text='auto-selects `Offer...` on save'
    )

    ## Form section - Department ------------------------------------
    offer_department = forms.BooleanField(required=False, label='Offer Department input')
    department_required = forms.BooleanField(
        required=False, label='Department required', help_text='auto-selects `Offer...` on save'
    )

    offer_research_program = forms.BooleanField(required=False, label='Offer Research Program')
    research_program_required = forms.BooleanField(
        required=False, label='Research Program required', help_text='auto-selects `Offer...` on save'
    )

    ## Form section - Access ----------------------------------------
    offer_embargo_access = forms.BooleanField(required=False, label='Offer 2-year embargo')

    offer_license_options = forms.BooleanField(required=False, label='Offer license options')
    license_required = forms.BooleanField(
        required=False, label='License required', help_text='auto-selects `Offer...` on save'
    )
    license_options = forms.MultipleChoiceField(
        required=False, label='License Options', choices=settings.ALL_LICENSE_OPTIONS
    )
    license_default_choices = [('ERR', 'Unselected')] + settings.ALL_LICENSE_OPTIONS
    license_default = forms.ChoiceField(
        choices=license_default_choices,
        label='License default',
        required=False,
        help_text='select default license',
    )

    offer_visibility_options = forms.BooleanField(required=False, label='Offer visibility options')
    visibility_required = forms.BooleanField(
        required=False, label='Visibility required', help_text='auto-selects `Offer...` on save'
    )
    visibility_options = forms.MultipleChoiceField(
        required=False, label='Visibility Options', choices=settings.ALL_VISIBILITY_OPTIONS
    )
    visibility_default_choices = [('ERR', 'Unselected')] + settings.ALL_VISIBILITY_OPTIONS
    visibility_default = forms.ChoiceField(
        choices=visibility_default_choices, label='Visibility Default', required=False, help_text='select default visibility'
    )

    ## Form section - Other -----------------------------------------
    ask_for_concentrations = forms.BooleanField(required=False, label='Ask for concentrations')
    concentrations_required = forms.BooleanField(
        required=False, label='Concentrations required', help_text='auto-selects `Ask...` on save'
    )

    ask_for_degrees = forms.BooleanField(required=False, label='Ask for degrees')
    degrees_required = forms.BooleanField(
        required=False, label='Degrees required', help_text='auto-selects `Ask...` on save'
    )

    invite_supplementary_files = forms.BooleanField(required=False, label='Invite supplementary files')

    def clean(self):
        ## delegate all validation to staff_form_validation.py
        log.debug('delegating validation to staff_form_validation')
        cleaned_data = super().clean()
        return validate_staff_form(self, cleaned_data)

    ## end class StaffForm()
