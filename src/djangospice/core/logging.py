
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def log_error(exception: Exception):
    debug = getattr(settings, "DEBUG")
    if debug:
        logger.error(str(exception))