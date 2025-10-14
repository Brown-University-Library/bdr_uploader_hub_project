"""
Contains functions for calling and processing the OCLC FastAPI service."
"""

import logging
import pprint

import httpx

log = logging.getLogger(__name__)


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
    with httpx.Client() as client:
        request = client.build_request("GET", url, params=params)
        log.debug(f'final url, `{request.url}`')
        response: httpx.Response = client.send(request)
    return_val: dict = response.json()
    log.debug(f'return_val, ``{pprint.pformat(return_val)}``')
    return return_val
