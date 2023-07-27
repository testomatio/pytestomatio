import logging
from contextlib import contextmanager

log = logging.getLogger(__name__)


def safe_request(message: str = None):
    try:
        yield message
    except Exception as e:
        log.error(f'{message}. Exception: {e}')
