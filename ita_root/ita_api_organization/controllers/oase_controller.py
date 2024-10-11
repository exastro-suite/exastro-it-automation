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
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.api import api_filter
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import oase


@api_filter
def get_oase_filter(organization_id, workspace_id, menu):  # noqa: E501
    """get_oase_filter

    OASEのレコードを全件取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        filter_parameter = {}
        result_data = oase.rest_filter(objdbca, menu, filter_parameter)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def post_oase_filter(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_oase_filter

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

    try:
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

        result_data = oase.rest_filter(objdbca, menu, filter_parameter)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def post_oase_history(organization_id, workspace_id, body=None):  # noqa: E501
    """post_oase_history

    検索条件を指定し、イベントフローで扱う履歴情報（イベント履歴、アクション履歴）を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20025
    """

    wsDb = DBConnectWs(workspace_id=workspace_id)
    wsMongo = MONGOConnectWs()

    try:
        parameter = {}
        if connexion.request.is_json:
            parameter = dict(connexion.request.get_json())

        event_history = oase.collect_event_history(wsMongo, parameter)
        action_history = oase.collect_action_log(wsDb, parameter)

        history_data = oase.create_history_list(event_history, action_history)
    except Exception as e:
        raise e
    finally:
        wsDb.db_disconnect()
        wsMongo.disconnect()

    return history_data,
