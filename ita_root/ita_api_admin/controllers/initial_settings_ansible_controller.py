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

from common_libs.api import api_filter_admin
from common_libs.common.exception import AppException
from common_libs.common.dbconnect import *  # noqa: F403
from libs.admin_common import initial_settings_ansible


@api_filter_admin
def get_all_initial_setting_ansible():  # noqa: E501
    """get_all_initial_setting_ansible

    すべてのorganizationのAnsibleの初期データを取得する # noqa: E501


    :rtype: InlineResponse2001
    """
    try:
        common_db = DBConnectCommon()  # noqa: F405
        where_str = "WHERE `DISUSE_FLAG`='0'"
        org_db_info_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", where_str)

        if len(org_db_info_list) == 0:
            result_data = ""
        else:
            result_data = {}
            for org_db_info in org_db_info_list:
                initial_data_ansible_if = org_db_info.get('INITIAL_DATA_ANSIBLE_IF')
                if (initial_data_ansible_if is not None) and (len(initial_data_ansible_if) > 0):
                    result_data[org_db_info['ORGANIZATION_ID']] = json.loads(initial_data_ansible_if)
                else:
                    result_data[org_db_info['ORGANIZATION_ID']] = None
    finally:
        if "common_db" in locals():
            common_db.db_disconnect()
    return result_data,


@api_filter_admin
def get_initial_setting_ansible(organization_id):  # noqa: E501
    """get_initial_setting_ansible

    Ansibleの初期データを取得する # noqa: E501

    :param organization_id: organizationID
    :type organization_id: str

    :rtype: InlineResponse2002
    """

    try:
        common_db = DBConnectCommon()  # noqa: F405
        where_str = "WHERE `ORGANIZATION_ID`=%s AND `DISUSE_FLAG`='0'"
        bind_value_list = [organization_id]
        org_db_info_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", where_str, bind_value_list)

        if len(org_db_info_list) == 0:
            # Organization_id[{}] does not exist.
            return '', g.appmsg.get_api_message("490-02001", [organization_id]), "490-02001", 490
        else:
            initial_data_ansible_if = org_db_info_list[0].get('INITIAL_DATA_ANSIBLE_IF')
            if (initial_data_ansible_if is not None) and (len(initial_data_ansible_if) > 0):
                result_data = json.loads(initial_data_ansible_if)
            else:
                result_data = None
    finally:
        if "common_db" in locals():
            common_db.db_disconnect()
    return result_data,


@api_filter_admin
def post_initial_setting_ansible(organization_id, body=None):  # noqa: E501
    """post_initial_setting_ansible

    Ansibleの初期データを登録・更新する # noqa: E501

    :param organization_id: organizationID
    :type organization_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """

    try:
        # organization_idのチェック
        common_db = DBConnectCommon()  # noqa: F405
        where_str = "WHERE `ORGANIZATION_ID`=%s AND `DISUSE_FLAG`='0'"
        bind_value_list = [organization_id]
        org_db_info_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", where_str, bind_value_list)

        if len(org_db_info_list) == 0:
            # Organization_id[{}] does not exist.
            return '', g.appmsg.get_api_message("490-02001", [organization_id]), "490-02001", 490

        org_db_info = org_db_info_list[0]

        # input_limit_settingのチェック
        if 'input_limit_setting' in body.keys():
            if body.get('input_limit_setting') not in [True, False]:
                # Key[{}] is invalid. Set either True or False.
                return '', g.appmsg.get_api_message("490-02002", ["input_limit_setting"]), "490-02002", 490

        # execution_engine_listのチェック
        if 'execution_engine_list' in body.keys():
            execution_engine_list = body.get('execution_engine_list')
            if len(execution_engine_list) == 0:
                # Key[{}] is invalid. Set 'Ansible-Core',  'Ansible Automation Controller' or both.
                return '', g.appmsg.get_api_message("490-02003", ["execution_engine_list"]), "490-02003", 490

            for execution_engine in execution_engine_list:
                if execution_engine not in ['Ansible-Core', 'Ansible Automation Controller', 'Ansible Execution Agent']:
                    # Key[{}] is invalid. Set 'Ansible-Core',  'Ansible Automation Controller' or both.
                    return '', g.appmsg.get_api_message("490-02003", ["execution_engine_list"]), "490-02003", 490

        # initial_dataのチェック
        if 'initial_data' in body.keys() and 'ansible_automation_controller_host_list' in body.get('initial_data').keys():
            for ansible_automation_controller_host in body.get('initial_data').get('ansible_automation_controller_host_list'):
                if 'parameter' not in ansible_automation_controller_host.keys():
                    # Key[{}] is invalid. Key[{}] is required.
                    return '', g.appmsg.get_api_message("490-02004", ["initial_data.execution_engine_list", "parameter"]), "490-02004", 490
                if 'host' not in ansible_automation_controller_host.get('parameter').keys():
                    # Key[{}] is invalid. Key[{}] is required.
                    return '', g.appmsg.get_api_message("490-02004", ["initial_data.execution_engine_list.parameter", "host"]), "490-02004", 490

        # connect organization-db
        g.ORGANIZATION_ID = organization_id
        g.db_connect_info = {}
        g.db_connect_info['ORGDB_HOST'] = org_db_info.get('DB_HOST')
        g.db_connect_info['ORGDB_PORT'] = str(org_db_info.get('DB_PORT'))
        g.db_connect_info['ORGDB_USER'] = org_db_info.get('DB_USER')
        g.db_connect_info['ORGDB_PASSWORD'] = org_db_info.get('DB_PASSWORD')
        g.db_connect_info['ORGDB_ADMIN_USER'] = org_db_info.get('DB_ADMIN_USER')
        g.db_connect_info['ORGDB_ADMIN_PASSWORD'] = org_db_info.get('DB_ADMIN_PASSWORD')
        g.db_connect_info['ORGDB_DATABASE'] = org_db_info.get('DB_DATABASE')
        g.db_connect_info['INITIAL_DATA_ANSIBLE_IF'] = org_db_info.get('INITIAL_DATA_ANSIBLE_IF')

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
        update_org_db_info = org_db_info
        update_org_db_info['INITIAL_DATA_ANSIBLE_IF'] = json.dumps(body)

        try:
            common_db.db_transaction_start()
            common_db.table_update('T_COMN_ORGANIZATION_DB_INFO', [update_org_db_info], 'PRIMARY_KEY')

            common_db.db_commit()
            common_db.db_disconnect()

        except AppException as e:
            common_db.db_rollback()
            common_db.db_disconnect()
            raise AppException(e)
    finally:
        if "common_db" in locals():
            common_db.db_disconnect()
        if "org_db" in locals():
            org_db.db_disconnect()
        if "ws_db" in locals():
            ws_db.db_disconnect()

    return '',
