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

    try:
        cmd_type = option.get("cmd_type")
        if cmd_type in ["Register", "Update", "Restore"]:
            entry_parameter = option.get('entry_parameter')
            input_order = entry_parameter.get('parameter').get('input_order')
            menu_group_menu_item = entry_parameter.get('parameter').get('menu_group_menu_item')

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
                vertical = row.get('VERTICAL')
                # parameter_sheet * input_order /  bundle * input_order
                if vertical == "0" and input_order is not None:
                    msg = g.appmsg.get_api_message('MSG-10933')
                    raise Exception()
                elif vertical == "1" and input_order is None:
                    msg = g.appmsg.get_api_message('MSG-10934')
                    raise Exception()
    except Exception:
        retBool = False

    return retBool, msg, option,