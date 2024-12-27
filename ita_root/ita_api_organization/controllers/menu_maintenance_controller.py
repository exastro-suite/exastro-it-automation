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
import datetime

sys.path.append('../../')
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.api import api_filter
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import menu_maintenance


@api_filter
def maintenance_register(organization_id, workspace_id, menu, body=None, **kwargs):  # noqa: E501
    """maintenance_register

    レコードを登録する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2005
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00001"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        tmp_path = '/tmp/' + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4']
        # 28 : 作業管理のシートタイプ追加
        sheet_type_list.append('28')
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        privilege = check_auth_menu(menu, objdbca)
        if privilege == '2':
            status_code = "401-00001"
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        cmd_type = 'Register'
        target_uuid = ''
        parameter = {}
        os.mkdir(tmp_path)
        retBool, parameter, file_paths = menu_maintenance.create_maintenance_parameters(connexion.request, cmd_type, tmp_path, menu)
        if retBool is False:
            status_code = "400-00003"
            request_content_type = connexion.request.content_type.lower()
            log_msg_args = [request_content_type]
            api_msg_args = [request_content_type]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405
        parameter.setdefault('type', cmd_type)
        result_data = menu_maintenance.rest_maintenance(objdbca, menu, parameter, target_uuid, file_paths)
    except Exception as e:
        raise e
    finally:
        if os.path.isdir(tmp_path):
            shutil.rmtree(tmp_path)
        objdbca.db_disconnect()
    return result_data,


@api_filter
def maintenance_update(organization_id, workspace_id, menu, uuid, body=None, **kwargs):  # noqa: E501
    """maintenance_update

    レコードを更新/廃止/復活する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param uuid: 対象のUUID
    :type uuid: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2005
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00001"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        tmp_path = '/tmp/' + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

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

        cmd_type = 'Update'
        target_uuid = uuid
        parameter = {}
        os.mkdir(tmp_path)
        retBool, parameter, file_paths = menu_maintenance.create_maintenance_parameters(connexion.request, cmd_type, tmp_path)
        if retBool is False:
            status_code = "400-00003"
            request_content_type = connexion.request.content_type.lower()
            log_msg_args = [request_content_type]
            api_msg_args = [request_content_type]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        result_data = menu_maintenance.rest_maintenance(objdbca, menu, parameter, target_uuid, file_paths)
    except Exception as e:
        raise e
    finally:
        if os.path.isdir(tmp_path):
            shutil.rmtree(tmp_path)
        objdbca.db_disconnect()
    return result_data,
