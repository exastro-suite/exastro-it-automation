# Copyright 2023 NEC Corporation#
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
from requests_toolbelt.multipart.encoder import MultipartEncoder
from requests_toolbelt.streaming_iterator import StreamingIterator
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

from common_libs.common.exception import AppException


class Exastro_API:
    grant_type = ""
    headers = {}
    username = None
    password = None
    refresh_token = None
    access_token = None
    roles = None
    userid = None

    def __init__(self, base_url, username=None, password=None, refresh_token=None, roles=None, userid=None):
        self.base_url = base_url

        self.grant_type = "refresh_token" if refresh_token else "password"
        if self.grant_type == "password":
        # ID/PASS認証（BAISC）
            self.username = username if username else None
            self.password = password if password else None
        else:
        # Barer認証
            self.refresh_token = refresh_token

        # 開発時の内部通信用
        if self.roles is not None:
            self.roles = roles
            self.headers["Roles"] = self.roles
        if self.userid is not None:
            self.userid = userid
            self.headers["User-Id"] = self.userid

    def api_request(self, method, endpoint, body=None, query=None):
        """
            method: "GET" or "POST"
            Content-Type: "application/json"(json引数に辞書を挿入するとデフォルトでContent-Typeがapplication/jsonになる)
        """
        response = None
        status_code = None

        headers = self.headers.copy()
        auth = None
        if self.access_token:
        # Barer認証
            headers["Authorization"] = f"Bearer {self.access_token}"
        else:
        # ID/PASS認証（BAISC）
            auth = (self.username, self.password)

        try:
            response = requests.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=headers,
                auth=auth,
                json=body,
                params=query,
                verify=False,
                timeout=(12, 600)
            )

            status_code = response.status_code

            if status_code != 200:
                return status_code, response.text
        except Exception as e:
            raise AppException("AGT-00004", [e])

        return status_code, response.json()

    def api_request_formdata(self, method, endpoint, body=None, query=None, files=None, data=None):
        """
            method: "GET" or "POST"
            Content-Type: "multipart/form-data"
        """
        response = None
        status_code = None

        headers = self.headers.copy()

        auth = None
        if self.access_token:
        # Barer認証
            headers["Authorization"] = f"Bearer {self.access_token}"
        else:
        # ID/PASS認証（BAISC）
            auth = (self.username, self.password)

        try:
            response = requests.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=headers,
                auth=auth,
                json=body,
                files=files,
                params=query,
                verify=False,
                timeout=(12, 600)
            )

            status_code = response.status_code

            if status_code != 200:
                return status_code, response
        except Exception as e:
            raise AppException("AGT-00004", [e])

        return status_code, response.json()

    def api_request_stream(self, method, endpoint, body=None, query=None, files=None, data=None):
        """
            method: "GET" or "POST"
            stream: True
            ファイルの保存は、呼び元で実施。
        """
        response = None
        status_code = None

        headers = self.headers.copy()
        auth = None
        if self.access_token:
        # Barer認証
            headers["Authorization"] = f"Bearer {self.access_token}"
        else:
        # ID/PASS認証（BAISC）
            auth = (self.username, self.password)

        try:
            response = requests.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=headers,
                auth=auth,
                json=body,
                files=files,
                params=query,
                data=data,
                verify=False,
                stream=True,
                timeout=(12, 600)
            )
            status_code = response.status_code

            if status_code != 200:
                return status_code, response
        except Exception as e:
            raise AppException("AGT-00004", [e])

        return status_code, response

    def api_request_formdata_stream_file(self, method, endpoint, query=None, fields=None):

        """
            method: "POST"
            Content-Type: "multipart/form-data"
        """
        response = None
        status_code = None

        headers = self.headers.copy()
        auth = None
        if self.access_token:
        # Barer認証
            headers["Authorization"] = f"Bearer {self.access_token}"
        else:
        # ID/PASS認証（BAISC）
            auth = (self.username, self.password)

        # パラメーター設定
        multipart_data = MultipartEncoder(
            fields=fields
        )
        data_size = multipart_data.len
        stream = StreamingIterator(data_size, multipart_data)
        headers["Content-Type"] = multipart_data.content_type

        try:
            response = requests.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=headers,
                params=query,
                auth=auth,
                data=stream,
                verify=False,
                timeout=(12, 600)
            )

            status_code = response.status_code

            if status_code != 200:
                return status_code, response.text
        except Exception as e:
            raise AppException("AGT-00004", [e])

        return status_code, response.json()

    def get_access_token(self, organization_id, refresh_token=None):
        endpoint = f"/auth/realms/{organization_id}/protocol/openid-connect/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {
            "client_id": f"_{organization_id}-api",
            "grant_type": self.grant_type,
            "scope": "openid email profile offline_access" if self.grant_type == "password" else None,
            "username": self.username if self.grant_type == "password" else None,
            "password": self.password if self.grant_type == "password" else None,
            "refresh_token": refresh_token if self.grant_type == "refresh_token" else None
        }

        try:
            response = requests.request(
                method="POST",
                url=f"{self.base_url}{endpoint}",
                headers=headers,
                data=body,
                verify=False,
                timeout=(12, 600)
            )

            status_code = response.status_code

            if response.status_code == 200:
                response_json = response.json()
                # print(response_json["expires_in"])
                # print(response_json["refresh_expires_in"])
                self.access_token = response_json["access_token"]

                return True
            else:
                raise AppException("AGT-00004", [(status_code, response.text)])
        except Exception as e:
            raise AppException("AGT-00004", [e])
