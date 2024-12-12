import datetime
import json
import logging

import trio
from django.conf import settings as project_settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify

from bdr_deposits_uploader_app.lib import config_new_helper, version_helper
from bdr_deposits_uploader_app.lib.shib_handler import shib_decorator
from bdr_deposits_uploader_app.lib.version_helper import GatherCommitAndBranchData

log = logging.getLogger(__name__)


# -------------------------------------------------------------------
# main urls
# -------------------------------------------------------------------


def info(request):
    """
    The "about" view.
    Can get here from 'info' url, and the root-url redirects here.
    """
    log.debug('starting info()')
    ## prep data ----------------------------------------------------
    # context = { 'message': 'Hello, world.' }
    context = {
        'quote': 'The best life is the one in which the creative impulses play the largest part and the possessive impulses the smallest.',
        'author': 'Bertrand Russell',
    }
    ## prep response ------------------------------------------------
    if request.GET.get('format', '') == 'json':
        log.debug('building json response')
        resp = HttpResponse(
            json.dumps(context, sort_keys=True, indent=2),
            content_type='application/json; charset=utf-8',
        )
    else:
        log.debug('building template response')
        resp = render(request, 'info.html', context)
    return resp


@shib_decorator
def login(request) -> HttpResponseRedirect:
    """
    Handles authentication and initial authorization via shib.
    Then:
    - On successful further UserProfile authorization, logs user in and redirects to the `next_url`.
        - If no `next_url`, redirects to the `info` page.
    Called automatically by attempting to access an `@login_required` view.
    """
    log.debug('\n\nstarting login()')
    next_url: str | None = request.GET.get('next', None)
    log.debug(f'next_url, ```{next_url}```')
    if not next_url:
        redirect_url = reverse('info_url')
    else:
        redirect_url = request.GET['next']  # may be same page
    log.debug('redirect_url, ```%s```' % redirect_url)
    return HttpResponseRedirect(redirect_url)


def logout(request):
    """
    Will log user out and redirect to the `info` page.
    """
    log.debug('starting logout()')
    return HttpResponseRedirect(reverse('info_url'))


## template to implement above
# def shib_logout( request ):
#     """ Clears session, hits shib logout, and redirects user to landing page. """
#     log.debug( 'request.__dict__, ```%s```' % request.__dict__ )
#     request.session[u'authz_info'][u'authorized'] = False
#     logout( request )
#     scheme = u'https' if request.is_secure() else u'http'
#     redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'request_url') )
#     if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:  # eases local development
#         pass
#     else:
#         encoded_redirect_url =  urlquote( redirect_url )  # django's urlquote()
#         redirect_url = u'%s?return=%s' % ( os.environ[u'EZSCAN__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
#     log.debug( u'in views.shib_logout(); redirect_url, `%s`' % redirect_url )
#     return HttpResponseRedirect( redirect_url )


@login_required
def config_new(request):
    """
    Enables coniguration of new app.
    """
    log.debug('starting config_new()')

    if not request.user.userprofile.can_create_app:
        return HttpResponse('You do not have permissions to create an app.')
    dummy_data: list = config_new_helper.get_recent_configs()
    hlpr_check_name_and_slug_url = reverse('hlpr_check_name_and_slug_url')
    hlpr_generate_slug_url = reverse('hlpr_generate_slug_url')
    context = {
        'hlpr_check_name_and_slug_url': hlpr_check_name_and_slug_url,
        'hlpr_generate_slug_url': hlpr_generate_slug_url,
        'recent_apps': dummy_data,
        'username': request.user.first_name,
    }
    return render(request, 'config_new.html', context)


@login_required
def config_slug(request, slug):
    """
    Enables coniguration of existing app.
    """
    log.debug('starting config_slug()')
    log.debug(f'slug, ``{slug}``')

    if slug not in request.user.userprofile.can_configure_these_apps:
        return HttpResponse('You do not have permissions to configure this app.')

    # return HttpResponse(f'config_slug view for slug: {slug}')
    context = {'slug': slug}
    return render(request, 'config_slug.html', context)


@login_required
def upload_slug(request, slug):
    """
    Displays the upload app.
    """
    log.debug('starting upload_slug()')
    log.debug(f'slug, ``{slug}``')

    if slug not in request.user.userprofile.can_view_these_apps:
        return HttpResponse('You do not have permissions to view this app.')

    # context = { 'slug': slug }
    return HttpResponse(f'upload_slug view for slug: {slug}')
    # return render(request, 'config_slug.html', context)


# -------------------------------------------------------------------
# htmx helpers
# -------------------------------------------------------------------


def hlpr_generate_slug(request):
    """
    Generates a url slug for given incoming text.
    """
    app_name = request.POST.get('new_app_name', '')
    slug = slugify(app_name)
    html = f"""<input 
        id="url-slug" 
        name="url_slug" 
        type="text" 
        value="{slug}" 
        placeholder="Auto-generated or enter manually"
         >"""
    log.debug(f'html, ``{html}``')
    return HttpResponse(html)


def hlpr_check_name_and_slug(request):
    """
    Validates that the incoming app-name and slug are unique.
    """
    ## get the incoming data
    app_name: str = request.POST.get('new_app_name', '')
    log.debug(f'app_name, ``{app_name}``')
    slug: str = request.POST.get('url_slug', '')
    log.debug(f'slug, ``{slug}``')

    ## if either are empty, return an error
    if not app_name or not slug:
        # Return an error message for missing inputs
        html = 'Both name and slug are required.'
        log.debug(f'html, ``{html}``')
        return HttpResponse(html)

    DUMMY_TAKEN_NAMES = ['Theses & Dissertations']
    DUMMY_TAKEN_SLUGS = ['theses-dissertations']
    name_problem = ''
    slug_problem = ''
    if app_name in DUMMY_TAKEN_NAMES:
        name_problem = 'Name already exists.'
    if slug in DUMMY_TAKEN_SLUGS:
        slug_problem = 'Slug already exists.'

    ## create html to show any problems
    if name_problem or slug_problem:
        html = f'{name_problem} {slug_problem}'
        log.debug(f'html, ``{html}``')
        return HttpResponse(html)

    ## if either are in the dummy-taken-list, return an error
    if app_name in DUMMY_TAKEN_NAMES or slug in DUMMY_TAKEN_SLUGS:
        # Return an error message for invalid inputs
        html = 'Name and slug are not unique.'
        log.debug(f'html, ``{html}``')
        return HttpResponse(html)

    ## getting here means life is good; use HX-Redirect to handle the redirection
    log.debug('returning redirect')
    # redirect_url = '/version/'
    redirect_url = reverse('config_slug_url', args=[slug])
    log.debug(f'redirect_url, ``{redirect_url}``')

    response = JsonResponse({'redirect': redirect_url})
    response['HX-Redirect'] = redirect_url
    return response


# -------------------------------------------------------------------
# support urls
# -------------------------------------------------------------------


def error_check(request):
    """
    Offers an easy way to check that admins receive error-emails (in development).
    To view error-emails in runserver-development:
    - run, in another terminal window: `python -m smtpd -n -c DebuggingServer localhost:1026`,
    - (or substitue your own settings for localhost:1026)
    """
    log.debug('starting error_check()')
    log.debug(f'project_settings.DEBUG, ``{project_settings.DEBUG}``')
    if project_settings.DEBUG is True:  # localdev and dev-server; never production
        log.debug('triggering exception')
        raise Exception('Raising intentional exception to check email-admins-on-error functionality.')
    else:
        log.debug('returning 404')
        return HttpResponseNotFound('<div>404 / Not Found</div>')


def version(request):
    """
    Returns basic branch and commit data.
    """
    log.debug('starting version()')
    rq_now = datetime.datetime.now()
    gatherer = GatherCommitAndBranchData()
    trio.run(gatherer.manage_git_calls)
    info_txt = f'{gatherer.branch} {gatherer.commit}'
    context = version_helper.make_context(request, rq_now, info_txt)
    output = json.dumps(context, sort_keys=True, indent=2)
    log.debug(f'output, ``{output}``')
    return HttpResponse(output, content_type='application/json; charset=utf-8')


def root(request):
    return HttpResponseRedirect(reverse('info_url'))
