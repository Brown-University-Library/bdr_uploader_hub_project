"""
Contains functions for calling and processing the OCLC FastAPI service."
"""

import logging

from django.conf import settings

log = logging.getLogger(__name__)


def call_oclc_fastapi(param: str) -> str:
    """
    Calls the OCLC FastAPI service with the given string.
    Returns the json response.
    Called by... TBD.
    """
    log.debug('starting call_oclc_fastapi()')
    url = f'{settings.FASTAPI_URL}/{param}'
    log.debug(f'url, ``{url}``')
    return_val = 'zzz'
    log.debug(f'return_val, ``{return_val}``')
    return return_val
