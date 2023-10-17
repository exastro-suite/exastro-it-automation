from .api_client_common import APIClientCommon  # noqa: F401
from .auth_method.auth_basic import BasicAuthAPIClient  # noqa: F401
from .auth_method.auth_bearer import BearerAuthAPIClient  # noqa: F401
from .auth_method.auth_sharedKeyLite import SharedKeyLiteAuthAPIClient  # noqa: F401
from .auth_method.auth_imap import IMAPAuthClient  # noqa: F401
from .auth_method.auth_optional import OptionalAuthAPIClient  # noqa: F401


def get_auth_client(setting):
    methods = {
        "1": BearerAuthAPIClient,
        "2": BasicAuthAPIClient,
        "3": SharedKeyLiteAuthAPIClient,
        "4": IMAPAuthClient,
        "5": OptionalAuthAPIClient
    }

    if setting["CONNECTION_METHOD_ID"] not in methods:
        return None

    method = methods[setting["CONNECTION_METHOD_ID"]]

    return method(setting)
