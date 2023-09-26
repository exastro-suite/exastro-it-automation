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
import sys

sys.path.append('../../')
from common_libs.common import *  # noqa: F403
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.loadtable.load_table import loadTable
from common_libs.api import api_filter
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import event_relay

@api_filter
def get_event_relay_filter(organization_id, workspace_id, menu):  # noqa: E501
    """get_event_relay_filter

    イベント連携のレコードを全件取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :param menu: メニュー名
    :type workspace_id: str

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    filter_parameter = {}
    result_data = event_relay.rest_filter(objdbca, menu, filter_parameter)
    return result_data,


@api_filter
def post_event_relay_filter(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_event_relay_filter

    検索条件を指定し、レコードを取得する # noqa: E501

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
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'filter_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    filter_parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        filter_parameter = body

    result_data = event_relay.rest_filter(objdbca, menu, filter_parameter)
    return result_data,


@api_filter
def post_check_monitoring_software(organization_id, workspace_id, body=None):  # noqa: E501
    """post_check_monitoring_software

    対象の監視ソフトの連携状態を確認する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """

    result_data = {}

    return result_data,


@api_filter
def post_event_flow(organization_id, workspace_id, body=None):  # noqa: E501
    """post_event_flow

    検索条件を指定し、イベントフローで扱う履歴情報（イベント履歴、アクション履歴）を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20022
    """

    result_data = {}

    return result_data,


@api_filter
def post_event_flow_history(organization_id, workspace_id, body=None):  # noqa: E501
    """post_event_flow_history

    検索条件を指定し、イベントフロー画面に描画する情報を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20022
    """

    wsDb = DBConnectWs(workspace_id=workspace_id)
    wsMongo = MONGOConnectWs()

    parameter = {}
    if connexion.request.is_json:
        parameter = dict(connexion.request.get_json())

    event_history = event_relay.collect_event_history(wsMongo, parameter)
    action_history = event_relay.collect_action_log(wsDb, parameter)

    history_data = event_relay.create_history_list(event_history, action_history)

    return history_data,


@api_filter
def get_event_flow_definition(organization_id, workspace_id):  # noqa: E501
    """get_event_flow_definition

    イベントフローで扱う定義情報（ラベル、アクション、ルール）を取得する

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse20023
    """

    wsDb = DBConnectWs(workspace_id=workspace_id)

    result_data = {}

    result_data["filter"] = event_relay.collect_filter(wsDb)
    result_data["action"] = event_relay.collect_action(wsDb)
    result_data["rule"] = event_relay.collect_rule(wsDb)

    return result_data,
