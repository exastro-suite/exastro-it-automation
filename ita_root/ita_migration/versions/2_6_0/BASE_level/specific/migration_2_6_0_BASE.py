#   Copyright 2025 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import g
import os
import json
import requests

def main(work_dir_path, db_conn):

    ###################################
    # Organizationのファイルアップロードサイズ最大値の設定
    ###################################
    g.applogger.info("[Trace] migration_2_6_0_BASE")
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')
    header_para = {
        "Content-Type": "application/json",
        "User-Id": "dummy",
    }
    data = [
        {
            "id": "ita.organization.common.maintenance_records_limit",
            "informations": {
                "description": os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DESCRIPTION'),
                "max": os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_MAX'),
                "default": os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DEFAULT')
            }
        }
    ]

    data_encode = json.dumps(data)

    # API呼出
    api_url = "http://{}:{}//internal-api/platform/plan_items".format(host_name, port)
    request_response = requests.post(api_url, data=data_encode, headers=header_para)

    response_data = json.loads(request_response.text)
    if request_response.status_code not in [200, 409]:
        raise Exception(f'API ERROR. URL=[{api_url}], StatusCode=[{request_response.status_code}], Response-[{str(response_data)}]')

    return 0
