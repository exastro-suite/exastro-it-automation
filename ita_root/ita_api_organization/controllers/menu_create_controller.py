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
from common_libs.api import api_filter, check_request_body
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import menu_create as menu_create_lib
from flask import g


@api_filter
def define_and_execute_menu_create(organization_id, workspace_id, body=None):  # noqa: E501
    """define_and_execute_menu_create

    パラメータシート定義および作成の実行 # noqa: E501

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
        status_code = "498-00004"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'menu_definition_and_creation'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['13']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # bodyのjson形式チェック
    check_request_body()

    create_param = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        create_param = body

    result_data = menu_create_lib.menu_create_define(objdbca, create_param)
    return result_data,


@api_filter
def get_exist_menu_create_data(organization_id, workspace_id, menu_create):  # noqa: E501
    """get_exist_menu_create_data

    パラメータシート定義・作成(既存)用の情報取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu_create: 「パラメータシート定義一覧」の「メニュー名(REST)」
    :type menu_create: str

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'menu_definition_and_creation'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['13']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # メニューの存在確認
    menu = 'menu_definition_list'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # パラメータシート定義・作成(既存)用の情報取得
    data = menu_create_lib.collect_exist_menu_create_data(objdbca, menu_create)

    return data,


@api_filter
def get_menu_create_data(organization_id, workspace_id):  # noqa: E501
    """get_menu_create_data

    パラメータシート定義・作成(新規)用の情報取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'menu_definition_and_creation'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['13']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # パラメータシート定義・作成(新規)用の情報取得
    data = menu_create_lib.collect_menu_create_data(objdbca)

    return data,


@api_filter
def get_pulldown_initial(organization_id, workspace_id, menu, column):  # noqa: E501
    """get_pulldown_initial

    「プルダウン選択」項目で選択した対象の「初期値」候補一覧取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: 「プルダウン選択」で指定した対象のメニュー名(rest用)
    :type menu: str
    :param column: 「プルダウン選択」で指定した対象のカラム名(rest用)
    :type column: str

    :rtype: InlineResponse20011
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu_def_and_cre = 'menu_definition_and_creation'
    check_menu_info(menu_def_and_cre, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['13']
    check_sheet_type(menu_def_and_cre, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu_def_and_cre, objdbca)

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 権限チェックスキップ対象メニュー
    skip_check_auth_list = ["selection_1", "selection_2"]

    data = {}
    if menu not in skip_check_auth_list:
        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4']
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        # 権限が無かったらdataを空で返す
        try:
            check_auth_menu(menu)
        except AppException as e:  # noqa: F405
            if e.args[0] == '401-00001':
                return data,
            else:
                raise e

    data = menu_create_lib.collect_pulldown_initial_value(objdbca, menu, column)

    return data,


@api_filter
def get_reference_item(organization_id, workspace_id, menu, column):  # noqa: E501
    """get_reference_item

    「プルダウン選択」項目で選択した対象の「参照項目」候補一覧取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: 「プルダウン選択」で指定した対象のメニュー名(rest用)
    :type menu: str
    :param column: 「プルダウン選択」で指定した対象のカラム名(rest用)
    :type column: str

    :rtype: InlineResponse20011
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu_def_and_cre = 'menu_definition_and_creation'
    check_menu_info(menu_def_and_cre, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['13']
    check_sheet_type(menu_def_and_cre, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu_def_and_cre, objdbca)

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 権限チェックスキップ対象メニュー
    skip_check_auth_list = ["selection_1", "selection_2"]

    data = {}
    if menu not in skip_check_auth_list:
        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4']
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        # 権限が無かったらdataを空で返す
        try:
            check_auth_menu(menu)
        except AppException as e:  # noqa: F405
            if e.args[0] == '401-00001':
                return data,
            else:
                raise e

    data = menu_create_lib.collect_pulldown_reference_item(objdbca, menu, column)

    return data,


@api_filter
def get_parameter_collection(organization_id, workspace_id):  # noqa: E501
    """get_parameter_collection

    パラメータシートの一覧を取得する

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2001
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # 「パラメーター集」メニューに対するロール権限をチェック
    check_auth_menu('parameter_collection', objdbca)

    # パラメータシートの一覧を取得する
    data = menu_create_lib.collect_parameter_list(objdbca)

    return data,


@api_filter
def get_parameter_collection_filter_terms_get(organization_id, workspace_id):
    """get_parameter_collection_filter_terms_get

    パラメータシートの検索条件を取得する

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2001
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # 「パラメーター集」メニューに対するロール権限をチェック
    check_auth_menu('parameter_collection', objdbca)

    # パラメータシートの検索条件を取得する
    data = menu_create_lib.collect_filter_terms(objdbca)

    return data,


@api_filter
def get_parameter_collection_filter_terms_update(organization_id, workspace_id, body):
    """get_parameter_collection_filter_terms_get

    パラメータシートの検索条件を登録・更新する

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2001
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00020"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # 「パラメーター集」メニューに対するロール権限をチェック
    check_auth_menu('parameter_collection', objdbca)

    # bodyのjson形式チェック
    check_request_body()

    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    # パラメータシートの検索条件を取得する
    data = menu_create_lib.update_filter_terms(objdbca, parameter)

    return data,


@api_filter
def get_parameter_collection_filter_terms_delete(organization_id, workspace_id, uuid):
    """get_parameter_collection_filter_terms_get

    パラメータシートの検索条件を削除する

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2001
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00021"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # 「パラメーター集」メニューに対するロール権限をチェック
    check_auth_menu('parameter_collection', objdbca)

    # パラメータシートの検索条件を取得する
    data = menu_create_lib.delete_filter_terms(objdbca, uuid)

    return data,