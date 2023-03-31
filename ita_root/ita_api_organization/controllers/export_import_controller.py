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
from common_libs.common import *  # noqa: F403
from common_libs.api import api_filter, check_request_body, check_request_body_key
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import export_import

@api_filter
def execute_excel_bulk_export(organization_id, workspace_id, body=None):  # noqa: E501
    """execute_excel_bulk_export

    Excel一括エクスポート実行 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'bulk_excel_export'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['22']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # bodyのjson形式チェック
    check_request_body()

    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        check_request_body_key(body, 'menu')  # keyが無かったら400-00002エラー
        check_request_body_key(body, 'abolished_type')

    result_data = export_import.execute_excel_bulk_export(objdbca, menu, body)

    return result_data,

@api_filter
def execute_excel_bulk_import(organization_id, workspace_id, body=None):  # noqa: E501
    """execute_excel_bulk_import

    Excel一括インポート実行 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'bulk_excel_export'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['22']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # bodyのjson形式チェック
    check_request_body()

    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        check_request_body_key(body, 'upload_id')  # keyが無かったら400-00002エラー
        check_request_body_key(body, 'data_portability_upload_file_name')

    result_data = export_import.execute_excel_bulk_import(objdbca, menu, body)

    return result_data,

@api_filter
def execute_menu_bulk_export(organization_id, workspace_id, body=None):  # noqa: E501
    """execute_menu_bulk_export

    メニュー一括エクスポート実行 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'menu_export'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['20']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # bodyのjson形式チェック
    check_request_body()

    body_menu = {}
    body_mode = {}
    body_abolished_type = {}
    body_specified_time = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        body_menu = check_request_body_key(body, 'menu')  # keyが無かったら400-00002エラー
        body_mode = check_request_body_key(body, 'mode')
        body_abolished_type = check_request_body_key(body, 'abolished_type')
        if body_mode == "2":
            body_specified_time = check_request_body_key(body, 'specified_timestamp')

    result_data = export_import.execute_menu_bulk_export(objdbca, menu, body)

    return result_data,

@api_filter
def execute_menu_import(organization_id, workspace_id, body=None):  # noqa: E501
    """execute_menu_import

    メニューインポート実行 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'menu_import'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['21']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # bodyのjson形式チェック
    check_request_body()

    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        check_request_body_key(body, 'menu')  # keyが無かったら400-00002エラー
        check_request_body_key(body, 'upload_id')
        check_request_body_key(body, 'file_name')

    result_data = export_import.execute_menu_import(objdbca, organization_id, workspace_id, menu, body)

    return result_data,

@api_filter
def get_excel_bulk_export_list(organization_id, workspace_id):  # noqa: E501
    """get_excel_bulk_export_list

    Excel一括エクスポート対象メニュー一覧取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse200
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'bulk_excel_export'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['22']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    result_data = export_import.get_excel_bulk_export_list(objdbca, organization_id, workspace_id)

    return result_data,

@api_filter
def post_excel_bulk_upload(organization_id, workspace_id, body=None):  # noqa: E501
    """post_excel_bulk_upload

    Excel一括インポートのアップロード # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'bulk_excel_export'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['22']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # bodyのjson形式チェック
    check_request_body()

    if connexion.request.is_json:
        body = dict(connexion.request.get_json())

    result_data = export_import.execute_excel_bulk_upload(organization_id, workspace_id, body, objdbca)

    return result_data,

@api_filter
def get_menu_export_list(organization_id, workspace_id):  # noqa: E501
    """get_menu_export_list

    メニューエクスポート対象メニュー一覧取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse200
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'menu_export'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['20']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    result_data = export_import.get_menu_export_list(objdbca, organization_id, workspace_id)

    return result_data,

@api_filter
def post_menu_import_upload(organization_id, workspace_id, body=None):  # noqa: E501
    """post_menu_import_upload

    メニューインポートのアップロード # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'menu_import'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['21']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # bodyのjson形式チェック
    check_request_body()

    body_file = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        body_file = check_request_body_key(body, 'file')  # keyが無かったら400-00002エラー
        check_request_body_key(body_file, 'name')
        check_request_body_key(body_file, 'base64')

    result_data = export_import.post_menu_import_upload(objdbca, organization_id, workspace_id, menu, body_file)

    return result_data,
