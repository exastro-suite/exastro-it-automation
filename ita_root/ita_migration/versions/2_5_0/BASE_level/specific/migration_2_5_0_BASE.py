#   Copyright 2023 NEC Corporation
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
    g.applogger.info("[Trace] migration_2_5_0_BASE")
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')
    header_para = {
        "Content-Type": "application/json",
        "User-Id": "dummy",
    }
    data = [
        {
            "id": "ita.organization.common.upload_file_size_limit",
            "informations": {
                # "description": os.environ.get('ORG_COMMON_UPLOAD_FILE_LIMIT_DESCRIPTION'),
                # "max": os.environ.get('ORG_COMMON_UPLOAD_FILE_LIMIT_MAX'),
                # "default": os.environ.get('ORG_COMMON_UPLOAD_FILE_LIMIT_DEFAULT')
                "description": 'Maximum byte size of upload file for organization default',
                "max": 107374182400,
                "default": 104857600
            }
        }
    ]

    data_encode = json.dumps(data)

    # API呼出
    api_url = "http://{}:{}//internal-api/platform/plan_items".format(host_name, port)
    request_response = requests.post(api_url, data=data_encode, headers=header_para, timeout=(12, 600))

    response_data = json.loads(request_response.text)
    if request_response.status_code not in [200, 409]:
        raise Exception(f'API ERROR. URL=[{api_url}], StatusCode=[{request_response.status_code}], Response-[{str(response_data)}]')

    return 0
