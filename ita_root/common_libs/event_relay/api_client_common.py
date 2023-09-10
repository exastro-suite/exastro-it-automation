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

import requests
import json
from common_libs.common.util import ky_decrypt


class APIClientCommon:

    def __init__(self, event_settings, last_fetched_timestamp):
        self.request_methods = {
            "1": "GET",
            "2": "POST",
            "3": "SSL/TLS",
            "4": "StartTLS",
            "5": "Plaintext"
        }

        self.request_method = self.request_methods[event_settings["REQUEST_METHOD"]]
        self.url = event_settings["URL"]
        self.port = event_settings["PORT"]
        self.headers = json.loads(event_settings["REQUEST_HEADER"]) if event_settings["REQUEST_HEADER"] else None
        self.proxy = {
            "http": event_settings["PROXY"],
            "https": event_settings["PROXY"]
        }
        self.auth_token = ky_decrypt(event_settings["AUTH_TOKEN"])
        self.username = event_settings["USERNAME"]
        self.password = ky_decrypt(event_settings["PASSWORD"])
        self.access_key_id = event_settings["ACCESS_KEY_ID"]
        self.secret_access_key = ky_decrypt(event_settings["SECRET_ACCESS_KEY"])
        self.mailbox_name = event_settings["MAILBOXNAME"]
        self.last_fetched_timestamp = last_fetched_timestamp

    def call_api(self, parameter):
        result = True
        API_response = None
        self.parameter = parameter  # APIのパラメータ
        try:
            response = requests.request(
                method=self.request_method,
                url=self.url,
                headers=self.headers,
                params=parameter if self.request_method == "1" else None,
                data=json.dumps(self.parameter) if self.request_method == "2" else None,
                proxies=self.proxy
            )
            # ステータス400系500系は例外へ
            response.raise_for_status()
            API_response = response.json()

        except requests.exceptions.HTTPError as e:
            http_error = f"HTTP Error: {e}"
            error_message = f"Error Message: {e.response.text}"
            print(http_error)
            print(error_message)
            result = False

        return result, API_response
