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

from flask import g
import requests
import json
from urllib.parse import urlparse
import datetime
from http.client import HTTPResponse

from common_libs.common.exception import AppException

class APIClientCommon:
    """
        メールおよびAPI呼び出し用共通クラス
    """
    # 必要項目定義
    def __init__(self, event_settings):
        self.event_collection_settings_id = event_settings["EVENT_COLLECTION_SETTINGS_ID"]
        self.event_collection_settings_name = event_settings["EVENT_COLLECTION_SETTINGS_NAME"]

        self.request_methods = {
            "1": "GET",
            "2": "POST"
        }

        self.request_method = self.request_methods[event_settings["REQUEST_METHOD_ID"]] if event_settings["REQUEST_METHOD_ID"] in ["1", "2"] else None
        self.url = event_settings["URL"]
        self.port = event_settings["PORT"]
        self.headers = json.loads(event_settings["REQUEST_HEADER"]) if event_settings["REQUEST_HEADER"] else None
        parsed_url = urlparse(event_settings["PROXY"]) if event_settings["PROXY"] else None
        self.proxy_host = parsed_url.hostname if parsed_url else None
        self.proxy_port = parsed_url.port if parsed_url else None
        self.auth_token = event_settings["AUTH_TOKEN"]
        self.username = event_settings["USERNAME"]
        self.password = event_settings["PASSWORD"]
        self.access_key_id = event_settings["ACCESS_KEY_ID"]
        self.secret_access_key = event_settings["SECRET_ACCESS_KEY"]
        self.mailbox_name = event_settings["MAILBOXNAME"]
        self.password = event_settings["PASSWORD"]
        self.parameter = event_settings["PARAMETER"]
        self.last_fetched_timestamp = event_settings["LAST_FETCHED_TIMESTAMP"] if event_settings["LAST_FETCHED_TIMESTAMP"] else None
        self.saved_ids = event_settings["SAVED_IDS"] if "SAVED_IDS" in event_settings else None

    def call_api(self, parameter):
        API_response = None
        self.parameter = parameter  # APIのパラメータ
        if self.parameter is not None:
            # パラメータ中の"EXSASTRO_LAST_FETCHED_TIME"を前回イベント収集日時に置換
            last_fetched_time = datetime.datetime.utcfromtimestamp(self.last_fetched_timestamp)
            last_fetched_ymd = last_fetched_time.strftime('%Y/%m/%d %H:%M:%S')
            last_fetched_dmy = last_fetched_time.strftime('%d/%m/%y %H:%M:%S')
            last_fetched_timestamp = str(int(datetime.datetime.timestamp(last_fetched_time)))

            for key, value in self.parameter.items():
                if type(value) is str:
                    value = value.replace("EXSASTRO_LAST_FETCHED_YY_MM_DD", last_fetched_ymd)
                    value = value.replace("EXSASTRO_LAST_FETCHED_DD_MM_YY", last_fetched_dmy)
                    value = value.replace("EXSASTRO_LAST_FETCHED_TIMESTAMP", last_fetched_timestamp)
                    self.parameter[key] = value

        try:
            proxies = None
            if self.proxy_host is not None and self.proxy_port is not None:
                proxies = {
                    "http": f"{self.proxy_host}:{self.proxy_port}",
                    "https": f"{self.proxy_host}:{self.proxy_port}"
                }

            response = requests.request(
                method=self.request_method,
                url=self.url,
                headers=self.headers,
                params=parameter if self.request_method == "GET" else None,
                data=json.dumps(self.parameter).encode() if self.request_method == "POST" else None,
                proxies=proxies
            )
            API_response = response.json()

            g.applogger.debug("HTTP STATUS {}".format(response.status_code))
            g.applogger.debug("Respons: {}\n".format(API_response))

            if response.status_code < 200 or response.status_code > 299:
                status_description = ""
                if response.status_code in HTTPResponse:
                    status_description = HTTPResponse[response.status_code]
                http_status = "{} {}".format(response.status_code, status_description)
                raise AppException("AGT-10029", [http_status])

            return API_response

        except requests.exceptions.InvalidJSONError:
            g.applogger.info("Failed to login to mailserver. Check login settings.")
            return API_response

        except requests.exceptions.JSONDecodeError:
            g.applogger.info("Converting the response to JSON failed with a JSON error.")
            return API_response

        except Exception as e:
            raise AppException("AGT-10029", [e])
