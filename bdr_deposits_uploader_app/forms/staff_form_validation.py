import logging
import pprint

import httpx
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from config.settings import BDR_PUBLIC_API_COLLECTION_ROOT_URL

log = logging.getLogger(__name__)


def validate_staff_form(form, cleaned_data):
    log.debug('starting validate_staff_form()')

    ## field-level validation -----------------------------------

    ## basics fields --------------------------------------------

    ## validate collection PID/title
    generic_pid_collection_error = 'Error validating that collection-pid and collection-title match. Please try again later.'
    if cleaned_data.get('collection_pid', ''):
        collection_pid = cleaned_data.get('collection_pid', '').strip()
        log.debug(f'collection_pid: {collection_pid}')
        # Not sure if this is necessary, because the field is required it can't be blank.
        # Argument for adding might be if there ever becomes an API call that doesn't go through the regular
        # form submission, but I think that's unlikely
        if not collection_pid:
            form.add_error('collection_pid', 'Collection PID is required.')
        else:
            api_url: str = BDR_PUBLIC_API_COLLECTION_ROOT_URL + str(collection_pid) + '/'
            log.debug(f'api_url, ``{api_url}``')
            response: httpx.Response | None = None
            try:  # handes, for example network being down
                response = httpx.get(api_url)
                log.debug(f'Making BDR API call: status code, ``{response.status_code}``')
            except Exception as e:
                log.exception(f'Error making BDR API call: {e}')
                form.add_error('collection_pid', generic_pid_collection_error)
            if response:
                if response.is_success:
                    ## Collection exists in the BDR
                    collection_title = cleaned_data.get('collection_title', '').strip()
                    if collection_title:
                        log.debug(f'collection_title: {collection_title}')
                        ## Now compare the title in the form to the title in the API response
                        api_collection_title = response.json().get('name', '').strip()
                        log.debug(f'api_collection_title: ``{api_collection_title}``')
                        if collection_title.lower() != api_collection_title.lower():
                            form.add_error(
                                'collection_title',
                                f'Collection title does not match the BDR pid-title ``{api_collection_title}``.',
                            )
                    else:
                        # Same thing here, not sure if this is necessary
                        form.add_error('collection_title', 'Collection title is required.')
                elif response.status_code == 404:
                    form.add_error('collection_pid', f'Collection with pid {collection_pid} does not exist.')
                elif response.status_code >= 500:
                    form.add_error('collection_pid', 'Error connecting to the BDR. Please try again later.')
                else:
                    form.add_error('collection_pid', generic_pid_collection_error)

    if cleaned_data.get('staff_to_notify', ''):
        data = cleaned_data.get('staff_to_notify', '')
        emails = [email.strip() for email in data.split('|') if email.strip()]
        if not emails:
            form.add_error('staff_to_notify', 'At least one email is required.')
        invalid_emails = []
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                invalid_emails.append(email)
        if invalid_emails:
            form.add_error('staff_to_notify', f'Invalid email(s): {", ".join(invalid_emails)}')

    if cleaned_data.get('authorized_student_emails', ''):
        data = cleaned_data.get('authorized_student_emails', '')
        emails = [email.strip() for email in data.split('|') if email.strip()]
        if not emails:
            form.add_error('authorized_student_emails', 'At least one email is required.')
        invalid_emails = []
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                invalid_emails.append(email)
        if invalid_emails:
            form.add_error('authorized_student_emails', f'Invalid email(s): {", ".join(invalid_emails)}')

    ## collaborators fields -------------------------------------
    if cleaned_data.get('advisors_and_readers_required') and not cleaned_data.get('offer_advisors_and_readers'):
        cleaned_data['offer_advisors_and_readers'] = True
    if cleaned_data.get('team_members_required') and not cleaned_data.get('offer_team_members'):
        cleaned_data['offer_team_members'] = True
    if cleaned_data.get('faculty_mentors_required') and not cleaned_data.get('offer_faculty_mentors'):
        cleaned_data['offer_faculty_mentors'] = True
    if cleaned_data.get('authors_required') and not cleaned_data.get('offer_authors'):
        cleaned_data['offer_authors'] = True

    ## department/programs fields -------------------------------
    if cleaned_data.get('department_required') and not cleaned_data.get('offer_department'):
        cleaned_data['offer_department'] = True
    if cleaned_data.get('research_program_required') and not cleaned_data.get('offer_research_program'):
        cleaned_data['offer_research_program'] = True

    ## access/license fields ------------------------------------
    if cleaned_data.get('license_required') and not cleaned_data.get('offer_license_options'):
        cleaned_data['offer_license_options'] = True
    ## Ensure at least one license option is selected, regardless of offer_license_options
    if not cleaned_data.get('license_options'):
        form.add_error('license_options', 'At least one license must be selected.')
    if cleaned_data.get('offer_license_options'):
        if not cleaned_data.get('license_default'):
            form.add_error('license_default', 'A default license is required.')
        log.debug(f'selected license options: {cleaned_data.get("license_options", "")}')
        log.debug(f'license_default: {cleaned_data.get("license_default", "")}')
        if cleaned_data.get('license_default', '') not in cleaned_data.get('license_options', ''):
            form.add_error('license_default', 'Default license must be one of the selected license options.')
    # if cleaned_data.get('license_options') and not cleaned_data.get('offer_license_options'):
    #     self.add_error('offer_license_options', 'License options must be offered if selected.')
    if len(cleaned_data.get('license_options', [])) > 1 and not cleaned_data.get('offer_license_options'):
        form.add_error('offer_license_options', 'License options must be offered if more than one is selected.')
    if (
        cleaned_data.get('license_default')
        and cleaned_data.get('license_default') != 'ERR'
        and not cleaned_data.get('offer_license_options')
    ):
        form.add_error('offer_license_options', 'License options must be offered if a default license is selected.')

    ## access/visibility fields ---------------------------------
    if cleaned_data.get('visibility_required') and not cleaned_data.get('offer_visibility_options'):
        cleaned_data['offer_visibility_options'] = True
    ## Ensure at least one visibility option is selected, regardless of offer_visibility_options
    if not cleaned_data.get('visibility_options'):
        form.add_error('visibility_options', 'At least one visibility-option must be selected.')
    if cleaned_data.get('offer_visibility_options'):
        if not cleaned_data.get('visibility_default'):
            form.add_error('visibility_default', 'A default visibility-option is required.')
        if cleaned_data.get('visibility_default', '') not in cleaned_data.get('visibility_options', ''):
            form.add_error('visibility_default', 'Default visibility-option must be one of the selected visibility-options.')
    # if cleaned_data.get('visibility_options') and not cleaned_data.get('offer_visibility_options'):
    #     self.add_error('offer_visibility_options', 'Visibility options must be offered if selected.')
    if len(cleaned_data.get('visibility_options', [])) > 1 and not cleaned_data.get('offer_visibility_options'):
        form.add_error('offer_visibility_options', 'Visibility options must be offered if more than one is selected.')
    if (
        cleaned_data.get('visibility_default')
        and cleaned_data.get('visibility_default') != 'ERR'
        and not cleaned_data.get('offer_visibility_options')
    ):
        form.add_error('offer_visibility_options', 'Visibility options must be offered if a default visibility is selected.')

    ## other fields ---------------------------------------------
    if cleaned_data.get('concentrations_required') and not cleaned_data.get('ask_for_concentrations'):
        cleaned_data['ask_for_concentrations'] = True
    if cleaned_data.get('degrees_required') and not cleaned_data.get('ask_for_degrees'):
        cleaned_data['ask_for_degrees'] = True

    ## other validation -----------------------------------------

    if not cleaned_data.get('authorized_student_groups') and not cleaned_data.get('authorized_student_emails'):
        form.add_error(None, 'At least one student group or email must be provided.')

    ## if nothing is filled out, raise an error
    if not any(
        [
            cleaned_data.get('collection_pid'),
            cleaned_data.get('collection_title'),
            cleaned_data.get('staff_to_notify'),
            cleaned_data.get('authorized_student_groups'),
            cleaned_data.get('authorized_student_emails'),
            cleaned_data.get('offer_advisors_and_readers'),
            cleaned_data.get('offer_team_members'),
            cleaned_data.get('offer_faculty_mentors'),
            cleaned_data.get('offer_authors'),
            cleaned_data.get('offer_department'),
            cleaned_data.get('offer_research_program'),
            cleaned_data.get('offer_embargo_access'),
            cleaned_data.get('offer_license_options'),
            cleaned_data.get('offer_access_options'),
            cleaned_data.get('offer_visibility_options'),
            cleaned_data.get('ask_for_concentrations'),
            cleaned_data.get('ask_for_degrees'),
            cleaned_data.get('invite_supplementary_files'),
            cleaned_data.get('authorized_student_groups'),
            cleaned_data.get('authorized_student_emails'),
        ]
    ):
        form.add_error(None, 'At least one field must be filled out.')

    log.debug(f'cleaned_data: {pprint.pformat(cleaned_data)}')
    return cleaned_data
