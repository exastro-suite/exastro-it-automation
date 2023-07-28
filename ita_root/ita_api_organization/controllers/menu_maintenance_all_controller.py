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
from flask import jsonify, g
import sys
import base64
import json

sys.path.append('../../')
from common_libs.common import *  # noqa: F403
from common_libs.loadtable.load_table import loadTable
from common_libs.api import api_filter
from common_libs.common import menu_maintenance_all
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type


@api_filter
def maintenance_all(organization_id, workspace_id, menu, body=None, **kwargs):  # noqa: E501
    """maintenance_all

    レコードを一括で登録/更新/廃止/復活する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: list | bytes

    :rtype: InlineResponse2005
    """
    # if connexion.request.is_json:
    #    body = object.from_dict(connexion.request.get_json())  # noqa: E501
    # return 'do some magic!'

    # メンテナンスモードのチェック
    if g.maintenance_mode.get('DATA_UPDATE_STOP') == '1':
        status_code = "498-00001"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0', '1', '2', '3', '4']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    privilege = check_auth_menu(menu, objdbca)
    if privilege == '2':
        status_code = "401-00001"
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    retBool, parameters, = menu_maintenance_all.create_maintenance_parameters(connexion.request)
    if retBool is False:
        status_code = "400-00003"
        request_content_type = connexion.request.content_type.lower()
        log_msg_args = [request_content_type]
        api_msg_args = [request_content_type]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    result_data = menu_maintenance_all.rest_maintenance_all(objdbca, menu, parameters)
    return result_data,
