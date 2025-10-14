"""
Contains functions for calling and processing the OCLC FastAPI service."
"""

import logging
import pprint
import time

import httpx

log = logging.getLogger(__name__)

_CLIENT: httpx.Client | None = None


def get_client() -> httpx.Client:
    """
    Return a process-wide httpx.Client with pooling enabled.
    """
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.Client(
            http2=True,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            ),
            headers={'User-Agent': 'brown_u_library_fast_lookup_1.0'},
        )
    return _CLIENT


def call_oclc_fastapi(param: str) -> dict:
    """
    Calls the OCLC FastAPI service with the given string.
    Returns the json response.
    Called by... TBD.
    """
    log.debug('starting call_oclc_fastapi()')
    params = {
        'query': param,
        'queryIndex': 'suggestall',
        'queryReturn': 'idroot,auth,type,suggestall',
        'suggest': 'autoSubject',
    }
    log.debug(f'params, ``{pprint.pformat(params)}``')
    # url = f'{settings.FASTAPI_URL}/{param}'
    url = 'https://fast.oclc.org/searchfast/fastsuggest'
    log.debug(f'url, ``{url}``')
    client = get_client()

    total_timeout: float = 3.0
    io_timeout: float = 2.0
    deadline = time.monotonic() + total_timeout
    # Compute a per-request timeout bounded by the remaining budget.
    remaining = max(0.1, deadline - time.monotonic())
    per_req = min(io_timeout, remaining)
    timeout = httpx.Timeout(connect=per_req, read=per_req, write=per_req, pool=per_req)

    request = client.build_request('GET', url, params=params, timeout=timeout)
    log.debug(f'final url, `{request.url}`')
    response: httpx.Response = client.send(request)
    return_val: dict = response.json()
    log.debug(f'return_val, ``{pprint.pformat(return_val)}``')
    return return_val
