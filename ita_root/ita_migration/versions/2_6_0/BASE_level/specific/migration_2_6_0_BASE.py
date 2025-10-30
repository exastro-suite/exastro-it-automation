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

    #############################################################################
    # Organization毎のメニューエクスポート・インポートのレコード操作上限値の設定
    # Organizationのファイルアップロードサイズ最大値の設定
    #############################################################################
    g.applogger.info(f"migration_2_6_0_BASE - main: {work_dir_path=}, {db_conn=}.")

    #############################################################################
    # システム全体のメニューエクスポート・インポートのレコード操作上限値の設定
    #############################################################################
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')
    header_para = {
        "Content-Type": "application/json",
        "User-Id": "dummy",
    }
    api_url = "http://{}:{}/internal-api/platform/settings/common".format(host_name, port)

    # ENVから値を取得
    try:
        data = [
            {
                "key": "ita.system.menu_export_import.buffer_size",
                "value": str(os.environ.get('SYSTEM_MENU_EXPORT_IMPORT_BUFFER_SIZE')),
                "description": str(os.environ.get('SYSTEM_MENU_EXPORT_IMPORT_BUFFER_SIZE_DESCRIPTION')),
            }
        ]
        data_encode = json.dumps(data)
    except Exception as e:
        g.applogger.info(f"[Trace] data.value : os.environ.get('SYSTEM_MENU_EXPORT_IMPORT_BUFFER_SIZE')={os.environ.get('SYSTEM_MENU_EXPORT_IMPORT_BUFFER_SIZE')}")
        g.applogger.info(f"[Trace] data.description : os.environ.get('SYSTEM_MENU_EXPORT_IMPORT_BUFFER_SIZE_DESCRIPTION')={os.environ.get('SYSTEM_MENU_EXPORT_IMPORT_BUFFER_SIZE_DESCRIPTION')}")
        raise Exception(f'PARAMETER ENCODE ERROR. URL=[{api_url}], Exception={e}')  # NOSONAR : 20250522 To prevent interruptions to processing

    g.applogger.info(f"[Trace] data=[{data_encode}]")

    # API呼出
    request_response = requests.post(api_url, data=data_encode, headers=header_para, timeout=(12, 600))

    response_data = json.loads(request_response.text)
    if request_response.status_code not in [200, 409]:
        raise Exception(f'API ERROR. URL=[{api_url}], StatusCode=[{request_response.status_code}], Response-[{str(response_data)}]')  # NOSONAR : 20250522 To prevent interruptions to processing
    else:
        g.applogger.info(f"[Trace] URL=[{api_url}], StatusCode=[{request_response.status_code}], Response-[{str(response_data)}]")

    # API呼出
    api_url = "http://{}:{}//internal-api/platform/plan_items".format(host_name, port)

    # ENVから値を取得
    try:
        data = [
            {
                "id": "ita.organization.menu_export_import.buffer_size",
                "informations": {
                    "description": os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_DESCRIPTION'),
                    "max": int(os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_MAX')),
                    "default": int(os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_DEFAULT')),
                }
            },
            {
                "id": "ita.organization.common.maintenance_records_limit",
                "informations": {
                    "description": os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DESCRIPTION'),
                    "max": int(os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_MAX')),
                    "default": int(os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DEFAULT'))
                }
            }
        ]
        data_encode = json.dumps(data)
    except Exception as e:
        g.applogger.info(f"[Trace] data.informations.description : os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_DESCRIPTION')={os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_DESCRIPTION')}")
        g.applogger.info(f"[Trace] data.informations.max : os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_MAX')={os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_MAX')}")
        g.applogger.info(f"[Trace] data.informations.default : os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_DEFAULT')={os.environ.get('ORG_MENU_EXPORT_IMPORT_BUFFER_SIZE_DEFAULT')}")
        g.applogger.info(f"[Trace] data.informations.description : os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DESCRIPTION')={os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DESCRIPTION')}")
        g.applogger.info(f"[Trace] data.informations.max : os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_MAX')={os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_MAX')}")
        g.applogger.info(f"[Trace] data.informations.default : os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DEFAULT')={os.environ.get('ORG_COMMON_MAINTENANCE_RECORDS_LIMIT_DEFAULT')}")
        raise Exception(f'PARAMETER ENCODE ERROR. URL=[{api_url}], Exception={e}')  # NOSONAR : 20250522 To prevent interruptions to processing

    g.applogger.info(f"[Trace] data=[{data_encode}]")

    # API呼出
    request_response = requests.post(api_url, data=data_encode, headers=header_para, timeout=(12, 600))

    response_data = json.loads(request_response.text)
    if request_response.status_code not in [200, 409]:
        raise Exception(f'API ERROR. URL=[{api_url}], StatusCode=[{request_response.status_code}], Response-[{str(response_data)}]')  # NOSONAR : 20250522 To prevent interruptions to processing
    else:
        g.applogger.info(f"[Trace] URL=[{api_url}], StatusCode=[{request_response.status_code}], Response-[{str(response_data)}]")

    return 0

