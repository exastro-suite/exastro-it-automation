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

def parent_menu_group_name_valid_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    user_env = g.LANGUAGE.upper().lower()
    
    if option["cmd_type"] == "Update" or option["cmd_type"] == "Register":
        # 更新後レコードから値を取得
        # メニューグループ名
        entry_menu_group_name = option["entry_parameter"]["parameter"]["menu_group_name_{}".format(user_env)]
        # 親メニューグループ名
        entry_parent_menu_group_name = option["entry_parameter"]["parameter"]["parent_menu_group_name"]
        
        # 自分自身を親メニューに設定している場合はエラー
        if entry_menu_group_name == entry_parent_menu_group_name:
            retBool = False
            # 自分自身を親メニューに設定できません。
            msg = g.appmsg.get_api_message('MSG-50001')
        elif entry_parent_menu_group_name != None:
            # 既に親が設定されているかチェック
            # メニューグループ名
            t_menu_column_group = "T_COMN_MENU_GROUP"
            entry_menu_group_result = objdbca.table_select(t_menu_column_group, 'WHERE MENU_GROUP_NAME_{} = %s AND DISUSE_FLAG = %s'.format(user_env.upper()), [entry_menu_group_name, 0])
            if len(entry_menu_group_result) > 0:
                menu_group_id = entry_menu_group_result[0].get('MENU_GROUP_ID')
                if menu_group_id != None:
                    # 子がいるかチェック
                    tmp_result = objdbca.table_select(t_menu_column_group, 'WHERE PARENT_MENU_GROUP_ID = %s AND DISUSE_FLAG = %s', [menu_group_id, 0])
                    if len(tmp_result) > 0:
                        retBool = False
                        # 既に親メニューに設定されているメニューグループです。
                        msg = g.appmsg.get_api_message('MSG-50002')
            
            # 親メニューグループ名
            entry_parent_menu_group_result = objdbca.table_select(t_menu_column_group, 'WHERE MENU_GROUP_NAME_{} = %s AND DISUSE_FLAG = %s'.format(user_env.upper()), [entry_parent_menu_group_name, 0])
            parent_menu_group_id = entry_parent_menu_group_result[0].get('PARENT_MENU_GROUP_ID')
            # 親がいるかチェック
            if parent_menu_group_id != None:
                retBool = False
                # 既に親メニューに設定されているメニューグループです。
                msg = g.appmsg.get_api_message('MSG-50002')
    
    return retBool, msg, option,
