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

import connexion
from flask import g
import sys

sys.path.append('../../')
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.api import api_filter
from common_libs.common import menu_maintenance_all
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from common_libs.apply import apply


@api_filter
def post_apply_parameter(organization_id, workspace_id, body=None, **kwargs):  # noqa: E501
    """post_apply_parameter

    オペレーションの生成からパラメータの適用までを行いConductor作業実行する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20011
    """

    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00001"
        raise AppException(status_code, [], [])  # noqa: F405

    # 要求パラメーターのチェック
    request_data = {}
    if connexion.request.is_json:
        request_data = dict(connexion.request.get_json())  # noqa: E501

    apply.check_params(request_data)

    # チェック対象のメニューを抽出
    check_menu_list = ["operation_list", "conductor_class_edit"]
    specify_menu_list = apply.get_specify_menu(request_data)
    check_menu_list = list(set(check_menu_list) | set(specify_menu_list))

    # チェック項目の定義
    check_items = {}
    for menu in check_menu_list:
        if menu not in check_items:
            check_items[menu] = {
                "sheet_type" : None,
                "privilege"  : None,
            }

        if menu == "conductor_class_edit":
            check_items[menu]["sheet_type"] = ["14", "15"]
            check_items[menu]["privilege"]  = ["0", "1", "2"]

        elif menu == "operation_list":
            check_items[menu]["sheet_type"] = ["0", ]
            check_items[menu]["privilege"]  = ["0", "1"]

        elif menu in specify_menu_list:
            check_items[menu]["sheet_type"] = ["0", "1", "2", "3", "4"]
            check_items[menu]["privilege"]  = ["0", "1"]

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # トランザクション開始
        objdbca.db_transaction_start()

        # メニュー存在/シートチェック/権限チェック
        parameter_sheet_list = []
        for menu, v in check_items.items():
            check_menu_info(menu, objdbca)
            sheet_type = check_sheet_type(menu, v["sheet_type"], objdbca)[0].get('SHEET_TYPE')
            privilege = check_auth_menu(menu, objdbca)
            if privilege not in v["privilege"]:
                status_code = "401-00001"
                log_msg_args = [menu]
                api_msg_args = [menu]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

            if sheet_type in ['1', '3', '4']:
                parameter_sheet_list.append(menu)

        # loadTable生成用のメニュー一覧を作成
        loadtable_list = [
            "operation_list", "conductor_instance_list", "conductor_class_edit",
            "conductor_node_instance_list", "movement_list", "conductor_notice_definition",
        ]
        loadtable_list = list(set(specify_menu_list) | set(loadtable_list))

        # Conductor作業実行用のメニューのリストを作成
        conductor_menu_list = [
            "conductor_instance_list", "conductor_class_edit",
            "conductor_node_instance_list", "movement_list", "conductor_notice_definition",
        ]

        # パラメーター適用、および、Conductor作業実行
        status_code, result_data = apply.rest_apply_parameter(
            objdbca, request_data,
            loadtable_list, parameter_sheet_list, conductor_menu_list
        )
        if status_code == "000-00000":
            objdbca.db_transaction_end(True)

        else:
            objdbca.db_transaction_end(False)

    except Exception as e:
        raise e

    finally:
        objdbca.db_transaction_end(False)
        objdbca.db_disconnect()

    return result_data,
