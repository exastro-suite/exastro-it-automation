#   Copyright 2024 NEC Corporation
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

from flask import g


def main(work_dir_path, wsdb):
    g.applogger.info("[Trace] Begin Menu Ref migrate(specific). #issue2501")

    data_list = wsdb.table_select('t_comn_menu_table_link', 'WHERE HOSTGROUP = %s AND SHEET_TYPE IN (%s, %s)', ['1', '5', '6'])

    for data in data_list:
        cmdb_table_name = data["TABLE_NAME"]
        if cmdb_table_name[0:7] == 'T_CMDB_' and cmdb_table_name[-3:] == '_SV':
            continue

        update_data = {
            "TABLE_DEFINITION_ID": data["TABLE_DEFINITION_ID"],
            "TABLE_NAME": cmdb_table_name + '_SV',
            "VIEW_NAME": data["VIEW_NAME"] + '_SV'
        }
        wsdb.table_update('t_comn_menu_table_link', update_data, "TABLE_DEFINITION_ID", True)

    wsdb.db_commit()

    return 0


