import logging
import pprint
from functools import wraps

from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponseServerError

log = logging.getLogger(__name__)


def shib_decorator(func):
    """
    Decorator for views that require Shibboleth authentication.
    Flow:
    - If user is already authenticated, the view is called as normal.
    - If user is not authenticated, attempts to provision a new user based on Shibboleth metadata.
    - If user creation fails, redirects to login page.
    - If user is successfully provisioned, logs user in and calls view.
    Called by views.abc()
    """

    @wraps(func)  # all this does is preserves function metadata
    def wrapper(request, *args, **kwargs):
        log.debug('starting shib_decorator wrapper()')
        log.debug(f'type(func), ``{type(func)}``')
        if request.user.is_authenticated:
            log.debug('user already authenticated.')
            return func(request, *args, **kwargs)

        shib_metadata: dict = prep_shib_meta(request.META)
        user = provision_user(shib_metadata)
        if not user:
            log.error('User creation failed; raising Exception.')
            return HttpResponseServerError('Sorry, problem with authentication; ask developers to check the logs.')

        auth.login(request, user)
        log.info(f'user {user.username} logged in.')
        return func(request, *args, **kwargs)

    return wrapper


def prep_shib_meta(shib_metadata: dict) -> dict:
    """
    Extracts Shib metadata from WSGI environ.
    Returns extracted metadata as a dictionary.
    Called by shib_login().
    """
    log.debug('starting prep_shib_meta()')
    log.debug(f'type(shib_metadata), ``{type(shib_metadata)}``')
    log.debug(f'request.META: ``{pprint.pformat(shib_metadata)}``')
    sanitized_meta = {key: val for key, val in shib_metadata.items() if 'wsgi.' not in key}
    return sanitized_meta


def provision_user(shib_metadata: dict) -> User:
    """
    Creates or updates User object based on Shibboleth metadata.
    Returns User object.
    Called by shib_login().
    """
    username = shib_metadata.get('Shibboleth-eppn')
    if not username:
        return None
    defaults = {
        'email': shib_metadata.get('Shibboleth-mail', f'{username}@example.com'),
        'first_name': shib_metadata.get('Shibboleth-givenName', ''),
        'last_name': shib_metadata.get('Shibboleth-sn', ''),
    }
    user, created = User.objects.update_or_create(username=username, defaults=defaults)
    user.save()
    return user
