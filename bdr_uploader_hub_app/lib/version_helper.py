import datetime
import logging
import pathlib
import pprint
import subprocess

import trio
from django.conf import settings

log = logging.getLogger(__name__)


def make_context(request, rq_now, info_txt, mount_check_txt):
    """
    Assembles data-dct.
    Called by views.version()
    """
    context = {
        'request': {
            'url': '%s://%s%s'
            % (
                request.scheme,
                request.META.get('HTTP_HOST', '127.0.0.1'),  # HTTP_HOST doesn't exist for client-tests
                request.META.get('REQUEST_URI', request.META['PATH_INFO']),
            ),
            'timestamp': str(rq_now),
        },
        'response': {
            'ip': request.META.get('REMOTE_ADDR', 'unknown'),
            'version': info_txt,
            'timetaken': str(datetime.datetime.now() - rq_now),
            'mount_check': mount_check_txt,
        },
    }
    return context


class GatherCommitAndBranchData:
    """
    Note:
    - Originally this class made two separate asyncronous subprocess calls to git.
    - Now it reads the `.git/HEAD` file to get the commit and branch data, so it doesn't need to be asyncronous.
    """

    def __init__(self):
        self.commit_data = ''
        self.branch_data = ''
        self.mount_data = ''

    async def manage_git_calls(self):
        """
        Triggers separate version and commit preparation concurrently.
        - Originally this class made two separate asyncronous subprocess calls to git.
        - Now it reads the `.git/HEAD` file to get both the commit and branch data (to avoid the `dubious ownership` issues),
          so it no longer benefits from asyncronous calls, but keeping for reference.
        Called by views.version()
        """
        log.debug('manage_git_calls')
        results_holder_dct = {}  # receives git responses as they're produced
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self.fetch_commit_data, results_holder_dct)
            nursery.start_soon(self.fetch_branch_data, results_holder_dct)
        log.debug(f'git-info results_holder_dct, ```{pprint.pformat(results_holder_dct)}```')
        self.commit = results_holder_dct['commit']
        self.branch = results_holder_dct['branch']
        non_async_mount_data = self.fetch_mount_data(settings.MOUNT_POINT)
        self.mount_data = non_async_mount_data
        log.debug(f'self.branch, ``{self.branch}``')
        return

    async def fetch_commit_data(self, results_holder_dct):
        """
        Fetches commit-data by reading the `.git/HEAD` file (avoiding calling git via subprocess due to `dubious ownership` issue).
        Called by manage_git_calls()
        """
        log.debug('startingfetch_commit_data')
        git_dir = pathlib.Path(settings.BASE_DIR) / '.git'
        try:
            ## read the HEAD file to find the current branch ------------
            head_file: pathlib.Path = git_dir / 'HEAD'
            ref_line: str = head_file.read_text().strip()
            if ref_line.startswith('ref:'):
                ref_path = ref_line.split(' ')[1]  # extract the ref path
                commit_file: pathlib.Path = git_dir / ref_path
                commit: str = commit_file.read_text().strip()
            else:  # if it's a detached HEAD, the commit hash is directly in the HEAD file
                commit: str = ref_line
        except FileNotFoundError:
            log.error('no `.git` directory or HEAD file found.')
            commit = 'commit_not_found'
        except Exception:
            log.exception('other problem fetching commit data')
            commit = 'commit_not_found'
        log.debug(f'commit, ``{commit}``')
        ## update holder --------------------------------------------
        results_holder_dct['commit'] = commit
        return

    async def fetch_branch_data(self, results_holder_dct):
        """
        Fetches branch-data by reading the `.git/HEAD` file (avoiding calling git via subprocess due to `dubious ownership` issue).
        Called by manage_git_calls()
        """
        log.debug('starting fetch_branch_data')
        git_dir = pathlib.Path(settings.BASE_DIR) / '.git'
        try:
            ## read the HEAD file to find the current branch ------------
            head_file = git_dir / 'HEAD'
            ref_line = head_file.read_text().strip()
            if ref_line.startswith('ref:'):
                branch = ref_line.split('/')[-1]  # extract the branch name
            else:
                branch = 'detached'
        except FileNotFoundError:
            log.error('no `.git` directory or HEAD file found.')
            branch = 'branch_not_found'
        except Exception:
            log.exception('other problem fetching branch data')
            branch = 'branch_not_found'
        ## update holder --------------------------------------------
        results_holder_dct['branch'] = branch
        return

    def fetch_mount_data(self, mount_point: str) -> str:
        """
        Fetches mount-data by running `df -h` and checking the output.
        Notes:
        - not async because django's 5.2x docs say async-caching is coming, but not supported yet.
        - using caching to ensure hammering doesn't negatively affect server.

        Args:
            mount_point (str): The mount point to check.
        Returns:
            str: 'all good' if the mount_point is found; `not-mounted` otherwise.

        Called by manage_git_calls()
        """
        from django.core.cache import cache

        log.debug('starting fetch_mount_data')
        ## try cache ------------------------------------------------
        cache_key: str = f'mount_data_{mount_point}'
        ok_status: str | None = cache.get(cache_key)
        if ok_status is not None:
            log.debug(f'using cache for {cache_key}')
        else:
            ## not using cache --------------------------------------
            log.debug(f'not using cache for {cache_key}')

            ## checks if mount_point is in the output
            ok: bool = False
            err: str | None = None
            try:
                ## runs df -h and captures its output
                df_result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
                ## checks if mount_point is in the output
                if mount_point in df_result.stdout:
                    ok = True
                else:
                    err = f'`{mount_point}` not found in disk usage call'
            except subprocess.CalledProcessError as e:
                err = f'Error running df command: {str(e)}'
            except Exception as e:
                err = f'Unexpected error: {str(e)}'
            log.debug(f'ok, ``{ok}``; err, ``{err}``')
            ok_status: str = 'all good' if ok else 'not-mounted'
            ## update cache -------------------------------------------
            log.debug(f'updating cache for {cache_key}')
            cache.set(cache_key, ok_status)
        return ok_status


## end class GatherCommitAndBranchData
