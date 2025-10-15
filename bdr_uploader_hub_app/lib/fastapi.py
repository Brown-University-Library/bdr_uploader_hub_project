"""
Contains functions for calling and processing the OCLC FastAPI service."
"""

import logging
import pprint

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
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=60.0,
            ),
            headers={'User-Agent': 'brown_u_library_fast_lookup_1.0'},
        )
    return _CLIENT


def prep_url_params(param: str) -> tuple[str, dict]:
    """
    Prepares the url and params for the OCLC FastAPI service.
    Returns a tuple of (url, params).
    Called by... TBD.
    """
    log.debug('starting prep_url_params()')
    url: str = 'https://fast.oclc.org/searchfast/fastsuggest'
    log.debug(f'url, ``{url}``')
    params: dict = {
        'query': param,
        'queryIndex': 'suggestall',
        'queryReturn': 'idroot,auth,type,suggestall',
        'suggest': 'autoSubject',
    }
    log.debug(f'params, ``{pprint.pformat(params)}``')
    return (url, params)


def make_request(client: httpx.Client, request: httpx.Request) -> dict:
    """
    Sends the request and returns JSON, handling errors gracefully.
    """
    try:
        response: httpx.Response = client.send(request)
        log.debug(f'response.http_version, ``{response.http_version}``')
        if response.status_code != 200:
            log.warning(f'non-200 from OCLC FastAPI: {response.status_code}')
            return {"response": {"docs": []}}

        return_val: dict = response.json()
        log.debug(f'return_val, ``{pprint.pformat(return_val)}``')
        return return_val
    except httpx.TimeoutException as exc:
        log.warning(f'timeout calling OCLC FastAPI: {exc}')
        return {"response": {"docs": []}}
    except httpx.RequestError as exc:
        log.warning(f'request error calling OCLC FastAPI: {exc}')
        return {"response": {"docs": []}}
    except ValueError as exc:
        log.warning(f'error parsing JSON from OCLC FastAPI: {exc}')
        return {"response": {"docs": []}}


def call_oclc_fastapi(param: str) -> dict:
    """
    Calls the OCLC FastAPI service with the given string.
    Returns the json response.
    Called by... TBD.
    """
    log.debug('starting call_oclc_fastapi()')

    ## prep url and params ------------------------------------------
    (url, params) = prep_url_params(param)  # (str, dict)

    ## prepare client -----------------------------------------------
    client: httpx.Client = get_client()
    timeout = httpx.Timeout(connect=0.4, read=0.8, write=0.4, pool=0.2)
    request: httpx.Request = client.build_request('GET', url, params=params, timeout=timeout)
    log.debug(f'final url, ``{request.url}``')

    ## make request -------------------------------------------------
    response_json: dict = make_request(client, request)
    return response_json
