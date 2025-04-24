import logging

log = logging.getLogger(__name__)


def send_ingest_success_email(
    first_name: str,
    email: str,
    title: str,
    bdr_url: str,
) -> None:
    """
    Send an email to the user indicating that their submission was successful.
    Called by the ingest action in the admin interface.
    Args:
        first_name (str): The first name of the user.
        email (str): The email address of the user.
        title (str): The title of the submission.
        bdr_url (str): The URL of the BDR submission.
    """
    log.debug('send_ingest_success_email called')
    log.debug(f'first_name: {first_name}')
    log.debug(f'email: {email}')
    log.debug(f'title: {title}')
    log.debug(f'bdr_url: {bdr_url}')
    # Logic to send email
    # Example:
    # send_mail(
    #     subject='Submission Successful',
    #     message=f'Hello {first_name},\n\nYour submission "{title}" was successful.\n\nYou can view it here: {bdr_url}',
    return
