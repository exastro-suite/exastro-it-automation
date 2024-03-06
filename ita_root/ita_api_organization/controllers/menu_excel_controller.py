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

from flask import g
import connexion
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common import menu_excel
from common_libs.api import api_filter, check_request_body
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type


@api_filter
def get_excel_filter(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """get_excel_filter

    全件のExcelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse2004
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        menu_record = check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        filter_parameter = {'discard': {'NORMAL': ''}}
        result_data = menu_excel.collect_excel_filter(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record, filter_parameter)
    except Exception as e:
        objdbca.db_disconnect()
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def get_excel_format(organization_id, workspace_id, menu):  # noqa: E501
    """get_excel_format

    新規登録用Excelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse2004
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        menu_record = check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        result_data = menu_excel.collect_excel_filter(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record)
    except Exception as e:
        objdbca.db_disconnect()
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def get_excel_journal(organization_id, workspace_id, menu):  # noqa: E501
    """get_excel_journal

    変更履歴のExcelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse2004
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        menu_record = check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        result_data = menu_excel.collect_excel_journal(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record)
    except Exception as e:
        objdbca.db_disconnect()
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def post_excel_filter(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_excel_filter

    検索条件を指定し、Excelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2004
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        menu_record = check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        filter_parameter = {}
        if connexion.request.is_json:
            body = dict(connexion.request.get_json())
            filter_parameter = body

        # メニューのカラム情報を取得
        result_data = menu_excel.collect_excel_filter(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record, filter_parameter)
    except Exception as e:
        objdbca.db_disconnect()
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def post_excel_maintenance(organization_id, workspace_id, menu, body=None, **kwargs):  # noqa: E501
    """post_excel_maintenance

    Excelでレコードを登録/更新/廃止/復活する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2004
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00001"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        menu_record = check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        privilege = check_auth_menu(menu, objdbca)
        if privilege == '2':
            status_code = "401-00001"
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # bodyのjson形式チェック
        check_request_body()

        excel_data = {}
        retBool, excel_data = menu_excel.create_upload_parameters(connexion.request)
        if retBool is False:
            status_code = "400-00003"
            request_content_type = connexion.request.content_type.lower()
            log_msg_args = [request_content_type]
            api_msg_args = [request_content_type]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # メニューのカラム情報を取得
        result_data = menu_excel.execute_excel_maintenance(objdbca, organization_id, workspace_id, menu, menu_record, excel_data)
    except Exception as e:
        objdbca.db_disconnect()
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,
