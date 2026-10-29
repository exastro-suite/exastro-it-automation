# Copyright 2023 NEC Corporation#
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

from flask import g

import textwrap


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''

    cmd_type = option.get("cmd_type")
    if cmd_type in ["Register", "Update", "Restore"]:
        # 「復活」時や一部の項目のみを指定した「更新」時はentry_parameterに対象の項目が含まれないため、current_parameterで補完する
        current_parameter = (option.get('current_parameter') or {}).get('parameter') or {}
        entry_parameter = (option.get('entry_parameter') or {}).get('parameter') or {}
        parameter = {**current_parameter, **entry_parameter}

        input_order = parameter.get('input_order')
        menu_group_menu_item = parameter.get('menu_group_menu_item')

        sql_str = textwrap.dedent("""
            SELECT * FROM `T_COMN_MENU_COLUMN_LINK` TAB_A
                LEFT JOIN `T_COMN_MENU_TABLE_LINK` TAB_B ON ( TAB_A.`MENU_ID` = TAB_B.`MENU_ID`)
            WHERE TAB_A.`COLUMN_DEFINITION_ID` = %s
            AND TAB_A.`DISUSE_FLAG`='0'
            AND TAB_B.`DISUSE_FLAG`='0'
        """).strip()
        rows = objdbca.sql_execute(sql_str, [menu_group_menu_item])

        if len(rows) == 1:
            row = rows[0]
            # Issue2828対応まではホストグループ利用のパラメータシートを選択させないようにする
            hostgroup = row.get('HOSTGROUP')
            if hostgroup == "1":
                msg = g.appmsg.get_api_message('499-00921')
                return False, msg, option,

            vertical = row.get('VERTICAL')
            # parameter_sheet * input_order /  bundle * input_order
            if vertical == "0" and input_order is not None:
                msg = g.appmsg.get_api_message('MSG-10933')
                return False, msg, option,
            elif vertical == "1" and input_order is None:
                msg = g.appmsg.get_api_message('MSG-10934')
                return False, msg, option,

    return retBool, msg, option,
