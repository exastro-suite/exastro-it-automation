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


def compare_detail_validate(objdbca, objtable, option):
    """
        {
            'compare_detail_id': '',
            'compare': '',
            'compare_col_title': '',
            'target_column_1': '',
            'target_column_2': '',
            'display_order': 10,
            'remarks': ''
        }
    """

    retBool = True
    msg = ""
    try:
        cmd_type = option.get('cmd_type')
        if cmd_type != "Discard":
            entry_parameter = option.get("entry_parameter").get("parameter")
            if cmd_type == "Restore":
                entry_parameter = option.get("current_parameter").get("parameter")

            # check compare target menus discard
            compare_id = entry_parameter.get("compare")
            target_column_1 = entry_parameter.get("target_column_1")
            target_column_2 = entry_parameter.get("target_column_2")
            sql_str = textwrap.dedent("""
                SELECT
                    `TAB_A`.*
                FROM
                    `T_COMPARE_CONFG_LIST` `TAB_A`
                LEFT JOIN `T_COMN_MENU` `TAB_B` ON ( `TAB_A`.`TARGET_MENU_1` = `TAB_B`.`MENU_ID` )
                LEFT JOIN `T_COMN_MENU` `TAB_C` ON ( `TAB_A`.`TARGET_MENU_2` = `TAB_C`.`MENU_ID` )
                LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TAB_D` ON ( `TAB_A`.`TARGET_MENU_1` = `TAB_D`.`MENU_ID` )
                LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TAB_E` ON ( `TAB_A`.`TARGET_MENU_2` = `TAB_E`.`MENU_ID` )
                WHERE `TAB_A`.`COMPARE_ID` = %s
                AND `TAB_A`.`DISUSE_FLAG` <> 1
                AND `TAB_B`.`DISUSE_FLAG` <> 1
                AND `TAB_C`.`DISUSE_FLAG` <> 1
                AND `TAB_D`.`DISUSE_FLAG` <> 1
                AND `TAB_E`.`DISUSE_FLAG` <> 1
            """).format().strip()
            bind_list = [compare_id]

            rows = objdbca.sql_execute(sql_str, bind_list)

            if len(rows) == 1:
                tmp_row = rows[0]
                detail_flg = tmp_row.get("DETAIL_FLAG")
                target_menu_1 = tmp_row.get("TARGET_MENU_1")
                target_menu_2 = tmp_row.get("TARGET_MENU_2")
                if detail_flg == "0":
                    retBool = False
                    # target compare is detail_flg false
                    status_code = "MSG-60003"
                    msg_args = []
                    msg = g.appmsg.get_api_message(status_code, msg_args)
                else:
                    # check: target menu id
                    sql_str = textwrap.dedent("""
                        SELECT
                            *
                        FROM
                            `T_COMN_MENU` `TAB_A`
                        WHERE `TAB_A`.`MENU_ID` IN ( %s , %s )
                        AND `TAB_A`.`DISUSE_FLAG` <> 1
                    """).format().strip()

                    bind_list = [target_menu_1, target_menu_2]
                    rows = objdbca.sql_execute(sql_str, bind_list)
                    if len(rows) not in [1, 2]:
                        retBool = False
                        # target manu discard error
                        status_code = "MSG-60004"
                        msg_args = []
                        msg = g.appmsg.get_api_message(status_code, msg_args)

                    # check: target column id
                    target_list = {target_menu_1: target_column_1, target_menu_2: target_column_2}
                    count_n = 1
                    for mid, cid in target_list.items():
                        sql_str = textwrap.dedent("""
                            SELECT
                                *
                            FROM
                                `T_COMN_MENU_COLUMN_LINK` `TAB_A`
                            WHERE `TAB_A`.`MENU_ID` = %s
                            AND `TAB_A`.`COLUMN_DEFINITION_ID` = %s
                            AND `TAB_A`.`DISUSE_FLAG` <> 1
                        """).format().strip()

                        bind_list = [mid, cid]
                        rows = objdbca.sql_execute(sql_str, bind_list)
                        if len(rows) != 1:
                            retBool = False
                            # target column_1 / column_2 error: menu-column
                            status_code = "MSG-60027"
                            if count_n == 1:
                                msg_args = [g.appmsg.get_api_message("MSG-60025")]
                            elif count_n == 2:
                                msg_args = [g.appmsg.get_api_message("MSG-60026")]
                            msg = g.appmsg.get_api_message(status_code, msg_args)
                            continue
                        count_n = count_n + 1
            else:
                retBool = False
                # target compare error
                status_code = "MSG-60002"
                msg_args = []
                msg = g.appmsg.get_api_message(status_code, msg_args)
    except Exception as e:
        retBool = False
        # except
        status_code = "MSG-60002"
        msg_args = []
        msg = g.appmsg.get_api_message(status_code, msg_args)
        g.applogger.debug(e)

    return retBool, msg, option
