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

from flask import g


def menu_column_group_valid(objdbca, objtable, option):
    retBool = True
    msg = ''

    user_env = g.LANGUAGE.upper()
    entry_parameter = option.get('entry_parameter').get('parameter')
    current_parameter = option.get('current_parameter').get('parameter')
    cmd_type = option.get("cmd_type")
    column_group_name_ja = entry_parameter.get('column_group_name_ja') if entry_parameter.get('column_group_name_ja') else ""
    column_group_name_en = entry_parameter.get('column_group_name_en') if entry_parameter.get('column_group_name_en') else ""
    # ---------親カラムグループ---------
    parent_column_group = entry_parameter.get("parent_column_group")
    entry_uuid = entry_parameter.get("uuid")
    column_group_id = current_parameter.get("uuid")
    # 更新時、自分のカラムグループを選択していないかどうか確認
    if parent_column_group and column_group_id and parent_column_group == column_group_id:
        retBool = False
        msg = g.appmsg.get_api_message("MSG-20011", [])
    if not retBool:
        return retBool, msg, option

    # 親ディレクトリがループ関係かどうかチェック
    table_name = "T_MENU_COLUMN_GROUP"
    if cmd_type == "Update":
        if parent_column_group:
            if entry_uuid:
                uuid = entry_uuid
            else:
                uuid = column_group_id
        where_str = "WHERE CREATE_COL_GROUP_ID = %s"
        
        while True:
            bind_value_list = [parent_column_group]
            return_values = objdbca.table_select(table_name, where_str, bind_value_list)
            if len(return_values) == 0:
                break
            else:
                if uuid == return_values[0].get("PA_COL_GROUP_ID"):
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20012", [])
                    break
                elif not return_values[0].get("PA_COL_GROUP_ID"):
                    break
                else:
                    parent_column_group = return_values[0].get("PA_COL_GROUP_ID")
        if not retBool:
            return retBool, msg, option
    # ---------親カラムグループ---------

    # ---------カラムグループ名---------
    # 廃止対象が親になっている場合はエラー
    if cmd_type == "Discard":
        where_str = "WHERE DISUSE_FLAG = '0'"
        return_values = objdbca.table_select(table_name, where_str, [])
        matcharray = []
        for data in return_values:
            if column_group_id == data.get("PA_COL_GROUP_ID"):
                matcharray.append(data.get("CREATE_COL_GROUP_ID"))
        if len(matcharray) > 0:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20013", [matcharray])
    
    # 復活時、親カラムグループが廃止されていたらエラー
    if cmd_type == "Restore":
        where_str = "WHERE CREATE_COL_GROUP_ID = %s"
        current_parent_column_group = current_parameter.get("parent_column_group")
        bind_value_list = [current_parent_column_group]
        return_values = objdbca.table_select(table_name, where_str, bind_value_list)
        
        if return_values:
            if return_values[0].get("DISUSE_FLAG") == "1":
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20014", [return_values[0].get("CREATE_COL_GROUP_ID")])
    # ---------カラムグループ名---------
    
    # ---------フルカラムグループ名---------
    if parent_column_group:
        where_str = "WHERE DISUSE_FLAG = '0' AND CREATE_COL_GROUP_ID = %s"
        bind_value_list = [parent_column_group]
        return_values = objdbca.table_select(table_name, where_str, bind_value_list)
        if 0 < len(return_values):
            entry_parameter['full_column_group_name_ja'] = return_values[0].get('FULL_COL_GROUP_NAME_JA') + "/" + column_group_name_ja
            entry_parameter['full_column_group_name_en'] = return_values[0].get('FULL_COL_GROUP_NAME_EN') + "/" + column_group_name_en
        else:
            entry_parameter['full_column_group_name_ja'] = column_group_name_ja
            entry_parameter['full_column_group_name_en'] = column_group_name_en
    else:
        entry_parameter['parent_column_group'] = parent_column_group
        entry_parameter['full_column_group_name_ja'] = column_group_name_ja
        entry_parameter['full_column_group_name_en'] = column_group_name_en
    
    if cmd_type == "Update":
        full_column_group_name_ja = entry_parameter['full_column_group_name_ja']
        full_column_group_name_en = entry_parameter['full_column_group_name_en']
        oid_full_column_group_name_ja = current_parameter['full_column_group_name_ja']
        oid_full_column_group_name_en = current_parameter['full_column_group_name_en']
        where_str = "WHERE PA_COL_GROUP_ID = %s"
        uuid = option.get('uuid')
        if full_column_group_name_ja != oid_full_column_group_name_ja or full_column_group_name_en != oid_full_column_group_name_en:
            while True:
                bind_value_list = [uuid]
                return_values = objdbca.table_select(table_name, where_str, bind_value_list)
                if len(return_values) == 0:
                    break
                else:
                    uuid = return_values[0].get('CREATE_COL_GROUP_ID')
                    data_list = {
                        'CREATE_COL_GROUP_ID': uuid,
                        'FULL_COL_GROUP_NAME_JA': full_column_group_name_ja + "/" + return_values[0].get('COL_GROUP_NAME_JA'),
                        'FULL_COL_GROUP_NAME_EN': full_column_group_name_en + "/" + return_values[0].get('COL_GROUP_NAME_EN')
                    }
                    ret = objdbca.table_update(table_name, data_list, "CREATE_COL_GROUP_ID", False)
                    if not ret:
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-20015", [])
                        break
                    full_column_group_name_ja = full_column_group_name_ja + "/" + return_values[0].get('COL_GROUP_NAME_JA')
                    full_column_group_name_en = full_column_group_name_en + "/" + return_values[0].get('COL_GROUP_NAME_EN')

    # ---------フルカラムグループ名---------
    return retBool, msg, option
