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
import six  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.api import api_filter
from common_libs.common import menu_info
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import compare_controll, menu_filter


@api_filter
def get_compares_info(organization_id, workspace_id, menu):  # noqa: E501
    """get_compares_info

    比較実行の基本情報取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['17']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    result_data = {}
    result_data = compare_controll.get_compares_data(objdbca, menu)

    #
    # 標準メニュー関連情報
    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 作業実行関連のメニューの基本情報および項目情報の取得
    tmp_data = get_compare_execute_info(organization_id, workspace_id, menu)
    result_data.setdefault("menu_info", tmp_data[0]["data"])

    return result_data,


@api_filter
def post_compare_execute(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_compare_execute

    比較実行 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['17']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    result_data = {}
    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    options = {}
    options.setdefault("compare_mode", "normal")
    result_data = compare_controll.compare_execute(objdbca, menu, parameter, options)

    return result_data,


@api_filter
def post_compare_execute_output(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_compare_execute_output

    比較実行ファイル出力 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20021
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['17']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    result_data = {}
    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    options = {}
    options.setdefault("compare_mode", "nomal")
    options.setdefault("output_flg", True)
    result_data = compare_controll.compare_execute(objdbca, menu, parameter, options)

    return result_data,


@api_filter
def post_compare_execute_file(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_compare_execute

    比較実行(ファイル) # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['17']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    result_data = {}
    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    options = {}
    options.setdefault("compare_mode", "file")
    result_data = compare_controll.compare_execute(objdbca, menu, parameter, options)

    return result_data,


# 標準のmenu_info相当
@api_filter
def get_compare_execute_info(organization_id, workspace_id, menu):  # noqa: E501
    """get_compare_execute_info

    Compare,Deviceのメニューの基本情報および項目情報を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse20013
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['17']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 作業実行関連のメニューの基本情報および項目情報の取得
    target_menus = ['compare_list', 'device_list']
    data = {}
    for target in target_menus:
        data[target] = menu_info.collect_menu_info(objdbca, target)

    return data,


# 標準のsearch_candidates相当
@api_filter
def get_compare_execute_search_candidates(organization_id, workspace_id, menu, target, column):  # noqa: E501
    """get_execute_search_candidates

    表示フィルタで利用するプルダウン検索の候補一覧を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param target: conductor_list or operation_list
    :type target: str
    :param column: REST用項目名
    :type column: str

    :rtype: InlineResponse2003
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['17']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # targetのチェック
    target_menus = ['compare_list', 'device_list']
    if target not in target_menus:
        log_msg_args = []
        api_msg_args = []
        raise AppException("499-00008", log_msg_args, api_msg_args)  # noqa: F405

    # 対象項目のプルダウン検索候補一覧を取得
    data = menu_info.collect_search_candidates(objdbca, target, column)
    return data,


# 標準のfilter相当
@api_filter
def post_copmare_execute_filter(organization_id, workspace_id, menu, target, body=None):  # noqa: E501
    """post_copmare_execute_filter

    Compare,Deviceを対象に、検索条件を指定し、レコードを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param target: conductor_list or operation_list
    :type target: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['17']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # targetのチェック
    target_menus = ['compare_list', 'device_list']
    if target not in target_menus:
        log_msg_args = []
        api_msg_args = []
        raise AppException("499-00008", log_msg_args, api_msg_args)  # noqa: F405

    filter_parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        filter_parameter = body

    # メニューのカラム情報を取得
    result_data = menu_filter.rest_filter(objdbca, target, filter_parameter)
    return result_data,
