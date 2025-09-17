# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from .api_client_common import APIClientCommon  # noqa: F401
from .auth_method.auth_basic import BasicAuthAPIClient  # noqa: F401
from .auth_method.auth_bearer import BearerAuthAPIClient  # noqa: F401
from .auth_method.auth_sharedKeyLite import SharedKeyLiteAuthAPIClient  # noqa: F401
from .auth_method.auth_imap import IMAPAuthClient  # noqa: F401
from .auth_method.auth_optional import OptionalAuthAPIClient  # noqa: F401


def get_auth_client(setting, last_fetched_event):
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

    return method(setting, last_fetched_event)
