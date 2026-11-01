from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_SEARCH_PARAM = "q"
DEFAULT_PAGE_PARAM = "page"
DEFAULT_PAGE_SIZE_PARAM = "page_size"

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_PAGE_SIZE = 100

DEFAULT_WIDGET_TOKEN_HEADER = "X-Lookup-Token"
DEFAULT_WIDGET_TOKEN_SALT = "djangospice.lookup.widget"
DEFAULT_WIDGET_TOKEN_MAX_AGE = 300
DEFAULT_REQUIRE_AUTHENTICATION = False

APP_NAME_KEY = "app_name"
MODEL_NAME_KEY = "model_name"
APP_NAME_URL_KEY = "<slug:app_name>"
MODEL_NAME_URL_KEY = "<slug:model_name>"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class LookupConfig:
    """
    Resolved configuration for djangospice.lookup.

    Values are resolved once from package defaults and Django settings.
    """

    # Request
    search_param: str
    page_param: str
    page_size_param: str

    # Pagination
    page: int
    page_size: int
    max_page_size: int

    # Widget capability
    widget_token_header: str
    widget_token_salt: str
    widget_token_max_age: int

    # Security
    require_authentication: bool


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def get_lookup_config() -> LookupConfig:
    """
    Resolve and validate djangospice.lookup configuration.

    Precedence:

        Django setting
            ↓
        package default
    """

    search_param = DEFAULT_SEARCH_PARAM
    page_param = DEFAULT_PAGE_PARAM
    page_size_param = DEFAULT_PAGE_SIZE_PARAM
    page = DEFAULT_PAGE
    page_size = DEFAULT_PAGE_SIZE
    max_page_size = DEFAULT_MAX_PAGE_SIZE
    widget_token_header = DEFAULT_WIDGET_TOKEN_HEADER
    widget_token_salt =  DEFAULT_WIDGET_TOKEN_SALT
    widget_token_max_age = DEFAULT_WIDGET_TOKEN_MAX_AGE
    require_authentication = DEFAULT_REQUIRE_AUTHENTICATION
   

    return LookupConfig(
        search_param=search_param,
        page_param=page_param,
        page_size_param=page_size_param,
        page=page,
        page_size=page_size,
        max_page_size=max_page_size,
        widget_token_header=widget_token_header,
        widget_token_salt=widget_token_salt,
        widget_token_max_age=widget_token_max_age,
        require_authentication=require_authentication,
    )


lookup_config = get_lookup_config()