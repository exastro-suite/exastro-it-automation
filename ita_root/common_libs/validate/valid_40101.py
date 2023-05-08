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

from flask import g  # noqa: F401
import textwrap


def compare_validate(objdbca, objtable, option):
    """
        {
            'compare_name': '',
            'target_menu_1': '',
            'target_menu_2': '',
            'detail_flg': '0' or '1',
        }
    """
    retBool = True
    msg = ""

    try:
        language = g.get('LANGUAGE').upper()
        cmd_type = option.get('cmd_type')
        if cmd_type != "Discard":

            entry_parameter = option.get("entry_parameter").get("parameter")
            if cmd_type == "Restore":
                entry_parameter = option.get("current_parameter").get("parameter")

            detail_flg = entry_parameter.get("detail_flg")
            if cmd_type == "Register":
                # set default value: detail_flg
                option["entry_parameter"]["parameter"].setdefault("detail_flg", "0")
            elif cmd_type == "Update" and (detail_flg is None or detail_flg not in ["0", "1"]):
                option["entry_parameter"]["parameter"]["detail_flg"] = "0"

            target_menus = {}
            target_menus_data = {}
            target_menus.setdefault("target_menu_1", entry_parameter.get("target_menu_1"))
            target_menus.setdefault("target_menu_2", entry_parameter.get("target_menu_2"))
            target_column_names = {}
            # get target menu + vertical
            for target_key, target_menu in target_menus.items():
                sql_str = textwrap.dedent("""
                    SELECT
                        `TAB_A`.*,
                        `TAB_B`.`VERTICAL`
                    FROM
                        `T_COMN_MENU` `TAB_A`
                    LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TAB_B` ON ( `TAB_A`.`MENU_ID` = `TAB_B`.`MENU_ID` )
                    WHERE `TAB_A`.`MENU_ID` = %s
                    AND `TAB_A`.`DISUSE_FLAG` <> 1
                    AND `TAB_B`.`DISUSE_FLAG` <> 1
                """).format().strip()

                bind_list = [target_menu]
                rows = objdbca.sql_execute(sql_str, bind_list)
                tmp_row = {}
                if len(rows) == 1:
                    tmp_row = rows[0]
                target_menus_data.setdefault(target_key, tmp_row)

            if entry_parameter.get("detail_flg") == "0":
                for target_key, target_menu in target_menus.items():
                    sql_str = textwrap.dedent("""
                        SELECT *
                        FROM
                            `T_COMN_MENU_COLUMN_LINK` `TAB_A`
                        WHERE `TAB_A`.`MENU_ID` = %s
                        AND `TAB_A`.`DISUSE_FLAG` <> 1
                    """).format().strip()
                    bind_list = [target_menu]
                    rows = objdbca.sql_execute(sql_str, bind_list)
                    tmp_row = {}
                    column_name_rest = []
                    if len(rows) >= 1:
                        column_name_rest = list(set([row.get("COLUMN_NAME_" + language) for row in rows]))
                        column_name_rest.sort()
                    target_column_names.setdefault(target_key, column_name_rest)

                target_menu1_columns = target_column_names.get("target_menu_1")
                target_menu2_columns = target_column_names.get("target_menu_2")

                if target_menu1_columns != target_menu2_columns:
                    retBool = False
                    status_code = "MSG-60032"
                    msg_args = []
                    msg = g.appmsg.get_api_message(status_code, msg_args)

            target_menu1_vertical = target_menus_data.get("target_menu_1").get("VERTICAL")
            target_menu2_vertical = target_menus_data.get("target_menu_2").get("VERTICAL")

            # check target menu constraint: [OK:0-0,1-1 , NG:0-1,1-0]
            if target_menu1_vertical == "1":
                if target_menu2_vertical == "0":
                    retBool = False
                    # target menu constraint nomal * vertical
                    status_code = "MSG-60001"
                    msg_args = []
                    msg = g.appmsg.get_api_message(status_code, msg_args)
            elif target_menu1_vertical == "0":
                if target_menu2_vertical == "1":
                    retBool = False
                    # target menu constraint nomal * vertical
                    status_code = "MSG-60001"
                    msg_args = []
                    msg = g.appmsg.get_api_message(status_code, msg_args)

    except Exception as e:
        retBool = False
        # except
        status_code = "MSG-60001"
        msg_args = []
        msg = g.appmsg.get_api_message(status_code, msg_args)
        g.applogger.debug(e)

    return retBool, msg, option
