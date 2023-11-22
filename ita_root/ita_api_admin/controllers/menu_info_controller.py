#   Copyright 2023 NEC Corporation
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
"""
controller
menu_info_controller
"""
from flask import g

from common_libs.common.dbconnect import *
from libs.notification_common import check_menu, check_menu_column_link, check_menu_table_link, check_target_column, rule_notification
from common_libs.api import api_filter_admin


@api_filter_admin
def get_notification_destination(organization_id, workspace_id, menu, column):  # noqa: E501
    """get_notification_destination

    指定のメニューのカラムで利用している通知先を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param column: REST用項目名
    :type column: str

    :rtype: InlineResponse2005
    """
    g.ORGANIZATION_ID = organization_id

    menu_column_list = {}
    menu_column_list['rule_before_notification_destination'] = "ID1"
    menu_column_list['rule_after_notification_destination'] = "ID1"

    # DB接続
    objdbca = DBConnectWs(workspace_id)

    # T_COMN_MENUの存在確認
    menu_row = check_menu(menu, objdbca)

    # T_COMN_MENU_TABLE_LINKの存在確認
    menu_table_link_row = check_menu_table_link(menu, objdbca, menu_row['MENU_ID'], column)

    # T_COMN_MENU_COLUMN_LINKの存在確認
    menu_table_column_link_row = check_menu_column_link(menu, objdbca, menu_row['MENU_ID'], column)

    # menuとcolumnの組合せ確認
    id = check_target_column(menu, column, menu_column_list)

    if id == "ID1":
        table_name = menu_table_link_row['TABLE_NAME']
        column_name = menu_table_column_link_row['COL_NAME']
        result = rule_notification(objdbca, table_name, column_name)

    return result,
