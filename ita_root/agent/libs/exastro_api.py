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
from common_libs.common.exception import AppException


class Exastro_API:
    def __init__(self, username, password, roles=None, userid=None, token=None):
        self.headers = {
            "Roles": roles,
            "User-Id": userid,
            "Authorization": f"Bearer {token}"
        }
        self.username = username
        self.password = password

    def api_request(self, method, url, body=None):
        """
            method: "GET" or "POST"
        """
        response = None
        status_code = None

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                auth=(self.username, self.password),
                json=body
            )

            status_code = response.status_code

            if status_code != 200:
                return status_code, response.text
        except Exception as e:
            raise AppException("AGT-00004", [e])

        return status_code, response.json()

    def get_access_token(self, url, organization_id, grant_type, refresh_token=None):
        token_url = f"{url}/auth/realms/{organization_id}/protocol/openid-connect/token"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {
            "client_id": f"_{organization_id}-api",
            "grant_type": grant_type,
            "scope": "openid email profile offline_access" if grant_type == "password" else None,
            "username": self.username if grant_type == "password" else None,
            "password": self.password if grant_type == "password" else None,
            "refresh_token": refresh_token if grant_type == "refresh_token" else None
        }
        response = self.api_request("POST", token_url, body)

        return response
