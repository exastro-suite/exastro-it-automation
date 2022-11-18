#   Copyright 2022 NEC Corporation
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
"""
controller
initial_settings_ansible_controller
"""
from flask import g
import json

from common_libs.api import api_filter
from common_libs.common.exception import AppException
from common_libs.common.dbconnect import *  # noqa: F403
from libs.admin_common import initial_settings_ansible


@api_filter
def get_initial_setting():  # noqa: E501
    """get_initial_setting

    Ansibleの初期データを取得する # noqa: E501


    :rtype: InlineResponse2001
    """

    common_db = DBConnectCommon()  # noqa: F405
    data_list = common_db.table_select('T_COMN_INITIAL_DATA')

    if len(data_list) == 0:
        result_data = ""
    else:
        result_data = data_list[0]['INITIAL_DATA_ANSIBLE_IF']

    return result_data,


@api_filter
def post_initial_setting(body=None):  # noqa: E501
    """post_initial_setting

    Ansibleの初期データを登録・更新する # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """

    # input_limit_settingのチェック
    if 'input_limit_setting' in body.keys():
        if body.get('input_limit_setting') not in [True, False]:
            return '', "key[input_limit_setting] is invalid. Set True or False.", "499-00001", 499

    # execution_engine_listのチェック
    if 'execution_engine_list' in body.keys():
        execution_engine_list = body.get('execution_engine_list')
        if len(execution_engine_list) == 0:
            return '', "key[execution_engine_list] is invalid. Set 'Ansible-Core' or 'Ansible Automation Controller' or both.", "499-00002", 499

        for execution_engine in execution_engine_list:
            if execution_engine not in ['Ansible-Core', 'Ansible Automation Controller']:
                return '', "key[execution_engine_list] is invalid. Set 'Ansible-Core' or 'Ansible Automation Controller' or both.", "499-00002", 499

    # initial_dataのチェック
    if 'initial_data' in body.keys() and 'ansible_automation_controller_host_list' in body.get('initial_data').keys():
        for ansible_automation_controller_host in body.get('initial_data').get('ansible_automation_controller_host_list'):
            if 'parameter' not in ansible_automation_controller_host.keys():
                return '', "key[initial_data.execution_engine_list] is invalid. key[parameter] is required.", "499-00003", 499
            if 'host' not in ansible_automation_controller_host.get('parameter').keys():
                return '', "key[initial_data.execution_engine_list.parameter] is invalid. key[host] is required.", "499-00003", 499

    common_db = DBConnectCommon()  # noqa: F405

    # Organizationの一覧取得
    org_data_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE `DISUSE_FLAG`='0'")

    # Organization分ループ
    for org_data in org_data_list:

        # connect organization-db
        organization_id = org_data["ORGANIZATION_ID"]
        g.ORGANIZATION_ID = organization_id
        g.db_connect_info = {}
        g.db_connect_info["ORGDB_HOST"] = org_data["DB_HOST"]
        g.db_connect_info["ORGDB_PORT"] = str(org_data["DB_PORT"])
        g.db_connect_info["ORGDB_USER"] = org_data["DB_USER"]
        g.db_connect_info["ORGDB_PASSWORD"] = org_data["DB_PASSWORD"]
        g.db_connect_info["ORGDB_ADMIN_USER"] = org_data['DB_ADMIN_USER']
        g.db_connect_info["ORGDB_ADMIN_PASSWORD"] = org_data['DB_ADMIN_PASSWORD']
        g.db_connect_info["ORGDB_DATABASE"] = org_data["DB_DATABASE"]

        org_db = DBConnectOrg(organization_id)  # noqa: F405
        workspace_data_list = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`='0'")

        # Workspace分ループ
        for workspace_data in workspace_data_list:

            # connect workspace-db
            workspace_id = workspace_data["WORKSPACE_ID"]
            g.WORKSPACE_ID = workspace_id
            g.db_connect_info = {}
            g.db_connect_info["WSDB_HOST"] = workspace_data["DB_HOST"]
            g.db_connect_info["WSDB_PORT"] = str(workspace_data["DB_PORT"])
            g.db_connect_info["WSDB_USER"] = workspace_data["DB_USER"]
            g.db_connect_info["WSDB_PASSWORD"] = workspace_data["DB_PASSWORD"]
            g.db_connect_info["WSDB_DATABASE"] = workspace_data["DB_DATABASE"]

            try:
                ws_db = DBConnectWs(workspace_id, organization_id)  # noqa: F405

                ws_db.db_transaction_start()

                # 初期データ設定
                initial_settings_ansible(ws_db, body)

                ws_db.db_commit()
                ws_db.db_disconnect()

            except AppException as e:
                ws_db.db_rollback()
                ws_db.db_disconnect()
                raise AppException(e)

            ws_db.db_disconnect()

        org_db.db_disconnect()

    # 初期設定データを作成
    initial_data = {'PRIMARY_KEY': 1,
                    'INITIAL_DATA_ANSIBLE_IF': json.dumps(body),
                    'DISUSE_FLAG': '0',
                    'LAST_UPDATE_USER': g.get('USER_ID')}

    try:
        common_db.db_transaction_start()
        # 初期設定データを検索
        data_list = common_db.table_select('T_COMN_INITIAL_DATA')

        if len(data_list) == 0:
            common_db.table_insert('T_COMN_INITIAL_DATA', [initial_data], 'PRIMARY_KEY')
        else:
            common_db.table_update('T_COMN_INITIAL_DATA', [initial_data], 'PRIMARY_KEY')
        common_db.db_commit()
        common_db.db_disconnect()

    except AppException as e:
        common_db.db_rollback()
        common_db.db_disconnect()
        raise AppException(e)

    return '',
