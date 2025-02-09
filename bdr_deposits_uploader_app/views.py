import datetime
import json
import logging
import pprint
from urllib import parse
from urllib.parse import quote

import trio
from django.conf import settings as project_settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import text

from bdr_deposits_uploader_app.forms.staff_form import StaffForm
from bdr_deposits_uploader_app.lib import config_new_helper, version_helper
from bdr_deposits_uploader_app.lib.shib_handler import shib_decorator
from bdr_deposits_uploader_app.lib.version_helper import GatherCommitAndBranchData
from bdr_deposits_uploader_app.models import AppConfig

log = logging.getLogger(__name__)


# -------------------------------------------------------------------
# main urls
# -------------------------------------------------------------------


def info(request) -> HttpResponse:
    """
    The "about" view.
    Can get here from 'info' url, and the root-url redirects here.
    """
    log.debug('\n\nstarting info()')
    log.debug(f'user, ``{request.user}``')
    ## prep data ----------------------------------------------------
    # context = { 'message': 'Hello, world.' }
    context = {
        'quote': 'The best life is the one in which the creative impulses play the largest part and the possessive impulses the smallest.',
        'author': 'Bertrand Russell',
    }
    if request.user.is_authenticated:
        context['username'] = request.user.first_name
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


def pre_login(request) -> HttpResponseRedirect:
    """
    Ensures shib actually comes up for user.

    Triggered by clicking "Staff Login" on the public info page.

    Flow:
    - Checks "logout_status" session-key for 'forcing_logout'.
        - If not found (meaning user has come, from, say, the public info page by clicking "Staff Login")...
            - Builds the IDP-shib-logout-url with `return` param set back to here.
            - Sets the "logout_status" session key-val to 'forcing_logout'.
            - Redirects to the IDP-shib-logout-url.
        - If found (meaning we're back here after redirecting to the shib-logout-url)...
            - Clears the "logout_status" session key-val.
            - Builds the IDP-shib-login-url with `next` param set to the `config-new` view.
            - Redirects to the IDP-shib-login-url.
    """
    log.debug('\n\nstarting pre_login()')
    ## get the type-value -------------------------------------------
    type_value = request.GET.get('type', None)
    log.debug(f'type_value from GET, ``{type_value}``')
    if type_value not in ['staff', 'student']:  ## try to get the type from the session
        log.debug('type_value not in [staff, student]')
        type_value = request.session.get('type', None)
        log.debug(f'type_value from session, ``{type_value}``')
    if type_value not in ['staff', 'student']:  ## if still not found, default to 'staff'
        log.warning('type_value not in [staff, student]')
        type_value = 'student'
    request.session['type'] = type_value
    ## check for session "logout_status" ----------------------------
    logout_status = request.session.get('logout_status', None)
    log.debug(f'logout_status, ``{logout_status}``')
    if logout_status != 'forcing_logout':
        ## meaning user has come directly, from, say, the public info page by clicking "Staff Login"
        ## set logout_status ----------------------------------------
        request.session['logout_status'] = 'forcing_logout'
        log.debug(f'logout_status set to ``{request.session["logout_status"]}``')
        ## build IDP-shib-logout-url --------------------------------
        # full_pre_login_url = f'{request.scheme}://{request.get_host()}{reverse("pre_login_url")}'
        full_pre_login_url = f'{request.scheme}://{request.get_host()}{reverse("pre_login_url")}?type={type_value}'
        log.debug(f'full_pre_login_url, ``{full_pre_login_url}``')
        encoded_full_pre_login_url = parse.quote(full_pre_login_url, safe='')
        redirect_url = f'{project_settings.SHIB_IDP_LOGOUT_URL}?return={encoded_full_pre_login_url}'
    else:  # request.session['logout_status'] _is_ found -- meaning user is back after hitting the IDP-shib-logout-url
        ## clear logout_status --------------------------------------
        del request.session['logout_status']
        log.debug('logout_status cleared')
        ## build IDP-shib-login-url ---------------------------------
        if type_value == 'staff':
            full_authenticated_new_url = f'{request.scheme}://{request.get_host()}{reverse("config_new_url")}'
        elif type_value == 'student':
            full_authenticated_new_url = f'{request.scheme}://{request.get_host()}{reverse("upload_url")}'
        log.debug(f'full_config_new_url, ``{full_authenticated_new_url}``')
        if request.get_host() == '127.0.0.1:8000':  # eases local development
            redirect_url = full_authenticated_new_url
        else:
            encoded_full_config_new_url = parse.quote(full_authenticated_new_url, safe='')
            redirect_url = f'{project_settings.SHIB_SP_LOGIN_URL}?target={encoded_full_config_new_url}'
    log.debug(f'redirect_url, ``{redirect_url}``')
    return HttpResponseRedirect(redirect_url)

    ## end def pre_login()


@shib_decorator
def shib_login(request) -> HttpResponseRedirect:
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


def logout(request) -> HttpResponseRedirect:
    """
    Flow:
    - Clears django-session.
    - Hits IDP shib-logout url.
    - Redirects user to info page.
    """
    log.debug('\n\nstarting logout()')
    ## clear django-session -----------------------------------------
    auth.logout(request)
    ## build redirect-url -------------------------------------------
    redirect_url: str = f'{request.scheme}://{request.get_host()}{reverse("info_url")}'
    if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development  # noqa: E712
        pass  # will redirect right to the info url
    else:
        ## build shib-logout-url -------------------------------------
        encoded_return_param_url: str = quote(redirect_url, safe='')
        redirect_url: str = f'{project_settings.SHIB_IDP_LOGOUT_URL}?return={encoded_return_param_url}'
    log.debug(f'redirect_url, ``{redirect_url}``')
    return HttpResponseRedirect(redirect_url)


@login_required
def config_new(request) -> HttpResponse:
    """
    Enables initial specification of new app name and slug.
    """
    log.debug('\n\nstarting config_new()')
    log.debug(f'user, ``{request.user}``')
    if not request.user.userprofile.can_create_app:
        log.debug(f'user ``{request.user}`` does not have permissions to create an app')
        return HttpResponse('You do not have permissions to create an app.')
    # dummy_data: list = config_new_helper.get_recent_configs()
    # log.debug(f'dummy_data, ``{pprint.pformat(dummy_data)}``')
    apps_data: list = config_new_helper.get_configs()
    log.debug(f'apps_data, ``{pprint.pformat(apps_data)}``')
    hlpr_check_name_and_slug_url = reverse('hlpr_check_name_and_slug_url')
    hlpr_generate_slug_url = reverse('hlpr_generate_slug_url')
    context = {
        'hlpr_check_name_and_slug_url': hlpr_check_name_and_slug_url,
        'hlpr_generate_slug_url': hlpr_generate_slug_url,
        # 'recent_apps': dummy_data,
        'recent_apps': apps_data,
        'username': request.user.first_name,
    }
    return render(request, 'config_new.html', context)


@login_required
def config_slug(request, slug) -> HttpResponse | HttpResponseRedirect:
    """
    Enables coniguration of existing app.
    """
    log.debug('\n\nstarting config_slug()')
    log.debug(f'slug, ``{slug}``')
    ## check permissions --------------------------------------------
    if not request.user.userprofile.can_create_app:
        log.debug('user does not have permissions to create an app')
        resp = HttpResponse('You do not have permissions to configure this app.')
    else:
        log.debug('user has permissions to configure app')
        ## get the app_config ---------------------------------------
        app_config = get_object_or_404(AppConfig, slug=slug)
        log.debug(f'app_config, ``{app_config}``')
        if request.method == 'POST':  # process submitted form
            log.debug(f'POST data, ``{request.POST}``')
            form = StaffForm(request.POST)
            log.debug('about to call is_valid()')
            if form.is_valid():
                cd = form.cleaned_data

                # Collaborators
                app_config.offer_advisors_and_readers = cd.get('offer_advisors_and_readers', False)
                app_config.advisors_and_readers_required = cd.get('advisors_and_readers_required', False)
                app_config.offer_team_members = cd.get('offer_team_members', False)
                app_config.team_members_required = cd.get('team_members_required', False)
                app_config.offer_faculty_mentors = cd.get('offer_faculty_mentors', False)
                app_config.faculty_mentors_required = cd.get('faculty_mentors_required', False)
                app_config.offer_authors = cd.get('offer_authors', False)
                app_config.authors_required = cd.get('authors_required', False)

                # Department / Programs
                app_config.offer_department = cd.get('offer_department', False)
                app_config.department_required = cd.get('department_required', False)
                dept_opts = cd.get('department_options')
                app_config.department_options = ','.join(dept_opts) if dept_opts else ''
                app_config.offer_research_program = cd.get('offer_research_program', False)
                app_config.research_program_required = cd.get('research_program_required', False)
                research_opts = cd.get('research_program_options')
                app_config.research_program_options = ','.join(research_opts) if research_opts else ''

                # Access Options
                app_config.offer_embargo_access = cd.get('offer_embargo_access', False)
                app_config.offer_license_options = cd.get('offer_license_options', False)
                app_config.license_required = cd.get('license_required', False)
                license_opts = cd.get('license_options')
                app_config.license_options = ','.join(license_opts) if license_opts else ''
                app_config.license_default = cd.get('license_default', '')
                app_config.offer_access_options = cd.get('offer_access_options', False)
                app_config.access_required = cd.get('access_required', False)
                access_opts = cd.get('access_options')
                app_config.access_options = ','.join(access_opts) if access_opts else ''
                app_config.access_default = cd.get('access_default', '')
                app_config.offer_visibility_options = cd.get('offer_visibility_options', False)
                app_config.visibility_required = cd.get('visibility_required', False)
                vis_opts = cd.get('visibility_options')
                app_config.visibility_options = ','.join(vis_opts) if vis_opts else ''
                app_config.visibility_default = cd.get('visibility_default', '')

                # Other Options
                app_config.ask_for_concentrations = cd.get('ask_for_concentrations', False)
                app_config.concentrations_required = cd.get('concentrations_required', False)
                app_config.ask_for_degrees = cd.get('ask_for_degrees', False)
                app_config.degrees_required = cd.get('degrees_required', False)
                app_config.invite_supplementary_files = cd.get('invite_supplementary_files', False)
                app_config.authorized_student_groups = cd.get('authorized_student_groups', '')
                app_config.authorized_student_emails = cd.get('authorized_student_emails', '')

                # Save the updated configuration
                app_config.save()

                resp = redirect(reverse('staff_form_success_url'))
            else:
                log.debug('form is not valid')

                ## log any errors, whether at form-level or at field-level
                log.debug(f'form.errors, ``{form.errors}``')
                log.debug(f'form.non_field_errors, ``{form.non_field_errors}``')
                ## when logging field errors, be sure the log-message includes the field-name
                for field in form:
                    if field.errors:
                        log.debug(f'field.errors, ``{field.errors}``')
                        log.debug(f'field label, ``{field.label}``')

                resp = render(request, 'staff_form.html', {'form': form, 'slug': slug, 'username': request.user.first_name})
        else:  # GET will display empty form
            form = StaffForm()
            resp = render(request, 'staff_form.html', {'form': form, 'slug': slug, 'username': request.user.first_name})
    return resp


@login_required
def staff_form_success(request) -> HttpResponse:
    """
    Displays a success message after a staff form is submitted.
    """
    log.debug('\n\nstarting staff_form_success()')
    return HttpResponse('Form submitted successfully; option to view the student form will be available here.')


@login_required
def upload(request) -> HttpResponse:
    """
    Displays the upload app.
    """
    log.debug('\n\nstarting upload()')
    log.debug(f'user, ``{request.user}``')
    context = {
        'username': request.user.first_name,
    }
    return render(request, 'uploader_select.html', context)


@login_required
def upload_slug(request, slug) -> HttpResponse:
    """
    Displays the upload app.
    """
    log.debug('\n\nstarting upload_slug()')
    log.debug(f'slug, ``{slug}``')

    # if slug not in request.user.userprofile.can_view_these_apps:
    #     return HttpResponse('You do not have permissions to view this app.')

    context = {
        'slug': slug,
        'username': request.user.first_name,
    }
    return render(request, 'uploader_slug.html', context)


# -------------------------------------------------------------------
# htmx helpers
# -------------------------------------------------------------------


def hlpr_generate_slug(request) -> HttpResponse:
    """
    Generates a url slug for given incoming text.
    """
    log.debug('\n\nstarting hlpr_generate_slug()')
    app_name = request.POST.get('new_app_name', '')
    slug = text.slugify(app_name)
    html = f"""<input 
        id="url-slug" 
        name="url_slug" 
        type="text" 
        value="{slug}" 
        placeholder="Auto-generated or enter manually"
         >"""
    log.debug(f'html, ``{html}``')
    return HttpResponse(html)


def hlpr_check_name_and_slug(request) -> HttpResponse | JsonResponse:
    """
    Validates that the incoming app-name and slug are unique.
    """
    log.debug('\n\nstarting hlpr_check_name_and_slug()')

    ## get the incoming data
    app_name: str = request.POST.get('new_app_name', '').strip()
    log.debug(f'app_name, ``{app_name}``')
    slug: str = request.POST.get('url_slug', '').strip()
    log.debug(f'slug, ``{slug}``')

    ## if either are empty, return an error
    if not app_name or not slug:
        # Return an error message for missing inputs
        html = 'Both name and slug are required.'
        log.debug(f'html, ``{html}``')
        return HttpResponse(html)

    ## check for existing names and slugs
    name_already_exists: bool = AppConfig.objects.filter(name__iexact=app_name).exists()
    slug_already_exists: bool = AppConfig.objects.filter(slug__iexact=slug).exists()
    name_problem: str = '' if not name_already_exists else 'Name already exists.'
    slug_problem: str = '' if not slug_already_exists else 'Slug already exists.'

    ## create html to show any problems
    if name_problem or slug_problem:
        html = f'{name_problem} {slug_problem}'
        log.debug(f'html, ``{html}``')
        return HttpResponse(html)

    ## getting here means life is good; use HX-Redirect to handle the redirection
    log.debug('saving data')
    try:
        app_config = AppConfig(name=app_name, slug=slug)
        app_config.save()
    except Exception as e:
        message = f'problem saving data, ``{e}``'
        log.exception(message)
        raise Exception(message)
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


def error_check(request) -> HttpResponse:
    """
    Offers an easy way to check that admins receive error-emails (in development).
    To view error-emails in runserver-development:
    - run, in another terminal window: `python -m smtpd -n -c DebuggingServer localhost:1026`,
    - (or substitue your own settings for localhost:1026)
    """
    log.debug('\n\nstarting error_check()')
    log.debug(f'project_settings.DEBUG, ``{project_settings.DEBUG}``')
    if project_settings.DEBUG is True:  # localdev and dev-server; never production
        log.debug('triggering exception')
        raise Exception('Raising intentional exception to check email-admins-on-error functionality.')
    else:
        log.debug('returning 404')
        return HttpResponseNotFound('<div>404 / Not Found</div>')


def version(request) -> HttpResponse:
    """
    Returns basic branch and commit data.
    """
    log.debug('\n\nstarting version()')
    rq_now = datetime.datetime.now()
    gatherer = GatherCommitAndBranchData()
    trio.run(gatherer.manage_git_calls)
    info_txt = f'{gatherer.branch} {gatherer.commit}'
    context = version_helper.make_context(request, rq_now, info_txt)
    output = json.dumps(context, sort_keys=True, indent=2)
    log.debug(f'output, ``{output}``')
    return HttpResponse(output, content_type='application/json; charset=utf-8')


def root(request) -> HttpResponseRedirect:
    """
    Redirects to the info page.
    """
    log.debug('\n\nstarting root()')
    return HttpResponseRedirect(reverse('info_url'))
