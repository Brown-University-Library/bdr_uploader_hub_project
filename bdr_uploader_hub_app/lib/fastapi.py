"""
Contains functions for calling and processing the OCLC FastAPI service.

Helper functions are followed by the manager function that calls them.

Possible TODOs:
- add tests for all functions where possible.
- move timeout values to settings
- move "limits" to settings
- move "User-Agent" to settings
- since the base url and most of the params are constant -- consider refactoring to not recreate them each time.
    Maybe in class.
- consider adding a month-long cache to avoid network calls for common queries.
"""

import logging
import pprint

import httpx

log = logging.getLogger(__name__)

_CLIENT: httpx.Client | None = None


## helper functions -------------------------------------------------


def get_client() -> httpx.Client:
    """
    Return a process-wide httpx.Client with pooling enabled.

    The `limits` are optimized for the purpose of receiving quick inputs of letters from a web keyword form,
      and take into account that the OCLC FastAPI service tends to respond quickly, and uses HTTP/2.
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
    Sends the request and returns response-dict, handling errors gracefully.
    """
    try:
        response: httpx.Response = client.send(request)
        log.debug(f'response.http_version, ``{response.http_version}``')
        if response.status_code != 200:
            log.warning(f'non-200 from OCLC FastAPI: {response.status_code}')
            return {'response': {'docs': []}}
        return_val: dict = response.json()
        log.debug(f'return_val, ``{pprint.pformat(return_val)}``')
        return return_val
    except httpx.TimeoutException as exc:
        log.warning(f'timeout calling OCLC FastAPI: {exc}')
        return {'response': {'docs': []}}
    except httpx.RequestError as exc:
        log.warning(f'request error calling OCLC FastAPI: {exc}')
        return {'response': {'docs': []}}
    except ValueError as exc:
        log.warning(f'error parsing JSON from OCLC FastAPI: {exc}')
        return {'response': {'docs': []}}


def parse_response(response_dict: dict) -> list[dict[str, str]]:
    """
    Parses OCLC FAST Suggest response into a normalized suggestions list.

    Returns a list of dicts: [{'label': str, 'fast_id': str, 'type': str}, ...].
    """
    log.debug('starting parse_response()')
    docs = response_dict.get('response', {}).get('docs', [])
    if not isinstance(docs, list):
        return []

    suggestions: list[dict[str, str]] = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        raw_id = doc.get('idroot', '')
        fast_id = str(raw_id).strip() if raw_id is not None else ''
        # Prefer 'auth'; fall back to 'suggestall'
        raw_auth = doc.get('auth', '')
        if isinstance(raw_auth, list):
            label = str(raw_auth[0]).strip() if raw_auth else ''
        else:
            label = str(raw_auth).strip() if raw_auth is not None else ''
        if not label:
            raw_suggest = doc.get('suggestall', '')
            if isinstance(raw_suggest, list):
                label = str(raw_suggest[0]).strip() if raw_suggest else ''
            else:
                label = str(raw_suggest).strip() if raw_suggest is not None else ''
        raw_type = doc.get('type', '')
        if isinstance(raw_type, list):
            type_val = str(raw_type[0]).strip() if raw_type else ''
        else:
            type_val = str(raw_type).strip() if raw_type is not None else ''
        if label and fast_id:
            suggestions.append({'label': label, 'fast_id': fast_id, 'type': type_val})
    log.debug(f'normalized suggestions, ``{pprint.pformat(suggestions)}``')
    return suggestions


## manager function -------------------------------------------------


def manage_oclc_fastapi_call(param: str) -> dict:
    """
    Manager function -- Calls the OCLC FastAPI service with the given query-string.
    Returns the json response.
    Called by... TBD.
    """
    log.debug('starting manage_oclc_fastapi_call()')

    ## prep url and params ------------------------------------------
    (url, params) = prep_url_params(param)  # (str, dict)

    ## prepare client -----------------------------------------------
    httpx_client: httpx.Client = get_client()
    timeout = httpx.Timeout(connect=0.4, read=0.8, write=0.4, pool=0.2)
    request: httpx.Request = httpx_client.build_request('GET', url, params=params, timeout=timeout)
    log.debug(f'final url, ``{request.url}``')

    ## make request -------------------------------------------------
    response_dict: dict = make_request(httpx_client, request)

    ## parse response -----------------------------------------------
    parsed_response: dict = {'suggestions': parse_response(response_dict)}

    ## return -------------------------------------------------------
    return parsed_response
