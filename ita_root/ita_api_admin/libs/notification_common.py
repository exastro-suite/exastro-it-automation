# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
利用中通知先一覧取得 共通function module
"""
from flask import g

import json
from common_libs.common.exception import AppException


def check_menu(menu, objdbca):
    rows = objdbca.table_select('T_COMN_MENU', 'WHERE `MENU_NAME_REST` = %s AND `DISUSE_FLAG` = %s', [menu, 0])
    if len(rows) == 0:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00002", log_msg_args, api_msg_args)

    return rows[0]


def check_menu_table_link(menu, objdbca, menu_id, column):
    rows = objdbca.table_select('T_COMN_MENU_TABLE_LINK', 'WHERE `MENU_ID` = %s AND `DISUSE_FLAG` = %s', [menu_id, 0])
    if len(rows) == 0:
        log_msg_args = [menu, column]
        api_msg_args = [menu, column]
        raise AppException("499-00006", log_msg_args, api_msg_args)  # noqa: F405

    return rows[0]


def check_menu_column_link(menu, objdbca, menu_id, column):
    rows = objdbca.table_select('T_COMN_MENU_COLUMN_LINK', 'WHERE `MENU_ID` = %s AND `COLUMN_NAME_REST` = %s AND `DISUSE_FLAG` = %s', [menu_id, column, 0])
    if len(rows) == 0:
        log_msg_args = [menu, column]
        api_msg_args = [menu, column]
        raise AppException("499-00006", log_msg_args, api_msg_args)  # noqa: F405

    return rows[0]


def check_target_column(menu, column, menu_column):

    menu_column_id = "{}_{}".format(menu, column)
    if menu_column_id in menu_column:
        return menu_column[menu_column_id]

    log_msg_args = [column, column]
    api_msg_args = [column, column]
    raise AppException("499-00009", log_msg_args, api_msg_args)  # noqa: F405


def rule_notification(objdbca, table_name, column_name):
    used_notification_list = []

    rows = objdbca.table_select(table_name, 'WHERE `DISUSE_FLAG` = %s', [0])

    for row in rows:
        notification_json = row[column_name]
        if not notification_json:
            continue

        notification_list = json.loads(notification_json)

        keys = notification_list["id"]
        for key in keys:
            if used_notification_list.count(key) == 0:
                used_notification_list.append(key)

    return json.dumps(used_notification_list, ensure_ascii=False)
