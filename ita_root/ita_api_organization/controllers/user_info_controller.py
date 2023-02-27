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
from libs import user_info
from common_libs.api import api_filter


@api_filter
def get_menu_group_panels(organization_id, workspace_id):  # noqa: E501
    """get_menu_group_panels

    メニューグループの画像を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # ユーザの権限情報を取得
    data = user_info.collect_menu_group_panels(objdbca)

    return data,


@api_filter
def get_user_auth(organization_id, workspace_id):  # noqa: E501
    """get_user_auth

    ユーザの権限情報を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # ユーザの権限情報を取得
    data = user_info.collect_user_auth(objdbca)

    return data,


@api_filter
def get_user_menus(organization_id, workspace_id):  # noqa: E501
    """get_user_menus

    ユーザがアクセス可能なメニューグループ・メニューの一覧を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューのカラム情報を取得
    data = user_info.collect_menus(objdbca)

    return data,


@api_filter
def post_table_settings(organization_id, workspace_id, body=None):  # noqa: E501
    """post_table_settings

    テーブル設定を登録する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    # ユーザの権限情報を取得
    data = user_info.regist_table_settings(objdbca, parameter)

    return data,


@api_filter
def get_widget_settings(organization_id, workspace_id):  # noqa: E501
    """get_widget_settings

    Dashboardのwidget設定を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューのカラム情報を取得
    data = user_info.collect_widget_settings(objdbca)

    return data,


@api_filter
def post_widget_settings(organization_id, workspace_id, body=None):  # noqa: E501
    """post_widget_settings

    Dashboardのwidget設定を登録する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    # ユーザの権限情報を取得
    data = user_info.regist_widget_settings(objdbca, parameter)

    return data,
