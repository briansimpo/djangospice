from pathlib import PurePosixPath
from urllib.parse import urljoin

from django.conf import settings
from djangospice.assets.conf import  get_setting


def asset_url(filename):
    if not filename:
        return None

    prefix = str(settings.STATIC_URL)

    if not prefix.endswith("/"):
        prefix += "/"

    relative = PurePosixPath(get_setting("OUTPUT_DIR") ) / filename

    return urljoin(prefix, str(relative))