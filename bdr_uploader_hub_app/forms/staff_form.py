import logging

from django import forms
from django.conf import settings

from bdr_uploader_hub_app.forms.staff_form_validation import validate_staff_form
from bdr_uploader_hub_app.lib.department_collection_helper import COLLECTION_ASSIGNMENT_MODE_CHOICES, FIXED_COLLECTION_MODE
from bdr_uploader_hub_app.lib.genre_helper import build_genre_choices, get_default_genre_entry

log = logging.getLogger(__name__)


class StaffForm(forms.Form):
    ## Basics section -----------------------------------------------
    collection_assignment_mode = forms.ChoiceField(
        required=True,
        choices=COLLECTION_ASSIGNMENT_MODE_CHOICES,
        initial=FIXED_COLLECTION_MODE,
        label='Collection Assignment Mode',
    )
    collection_pid = forms.CharField(required=False, label='Collection PID')
    collection_title = forms.CharField(required=False, label='Collection Title', help_text='PID sanity-check')
    staff_to_notify = forms.CharField(
        required=True,
        label='Staff to notify on ingest',
        help_text='email1 | email2 | ...',
    )
    assigned_genre = forms.ChoiceField(required=True, label='Assigned Genre', choices=[])

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
    ask_for_keywords = forms.BooleanField(required=False, label='Ask for keywords')
    keywords_required = forms.BooleanField(
        required=False, label='Keywords required', help_text='auto-selects `Ask...` on save'
    )

    ask_for_concentrations = forms.BooleanField(required=False, label='Ask for concentrations')
    concentrations_required = forms.BooleanField(
        required=False, label='Concentrations required', help_text='auto-selects `Ask...` on save'
    )

    ask_for_degrees = forms.BooleanField(required=False, label='Ask for degrees')
    degrees_required = forms.BooleanField(
        required=False, label='Degrees required', help_text='auto-selects `Ask...` on save'
    )

    invite_supplementary_files = forms.BooleanField(required=False, label='Invite supplementary files')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['license_options'].choices = settings.ALL_LICENSE_OPTIONS
        self.fields['license_default'].choices = [('ERR', 'Unselected')] + settings.ALL_LICENSE_OPTIONS
        self.fields['visibility_options'].choices = settings.ALL_VISIBILITY_OPTIONS
        self.fields['visibility_default'].choices = [('ERR', 'Unselected')] + settings.ALL_VISIBILITY_OPTIONS
        self.fields['assigned_genre'].choices = build_genre_choices()
        assigned_genre_initial = self.initial.get('assigned_genre') if isinstance(self.initial, dict) else None
        if isinstance(assigned_genre_initial, dict):
            assigned_genre_initial = assigned_genre_initial.get(
                'menu_label', get_default_genre_entry().get('menu_label', 'document')
            )
        if not assigned_genre_initial:
            assigned_genre_initial = get_default_genre_entry().get('menu_label', 'document')
        if isinstance(self.initial, dict):
            self.initial['assigned_genre'] = assigned_genre_initial
        self.fields['assigned_genre'].initial = assigned_genre_initial

    def clean(self):
        ## delegate all validation to bdr_uploader_hub_app/forms/staff_form_validation.py
        log.debug('delegating validation to staff_form_validation')
        cleaned_data = super().clean()
        return validate_staff_form(self, cleaned_data)

    ## end class StaffForm()
