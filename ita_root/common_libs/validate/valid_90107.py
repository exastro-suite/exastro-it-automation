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
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst


def external_valid_menu_before(objdbca, objtable, option):  # noqa: C901
    retBool = True
    msg = ''
    cmd_type = option.get('cmd_type')

    # 廃止の場合、バリデーションチェックを行わない。
    if cmd_type == 'Discard':
        return retBool, msg, option,

    current_parameter = option.get('current_parameter', {}).get('parameter')
    entry_parameter = option.get('entry_parameter', {}).get('parameter')

    # 「登録」「更新」の場合、entry_parameterから各値を取得
    if cmd_type == 'Register' or cmd_type == 'Update':
        item_no = entry_parameter.get('item_no')
        menu_group_menu_item = entry_parameter.get('menu_group_menu_item')
        column_substitution_order = entry_parameter.get('column_substitution_order')
        registration_method = entry_parameter.get('registration_method')
        movement_name = entry_parameter.get('movement_name')
        variable_name = entry_parameter.get('variable_name')
        hcl_setting = entry_parameter.get('hcl_setting')
        member_variable_name = entry_parameter.get('member_variable_name')
        substitution_order = entry_parameter.get('substitution_order')

    # 「復活」の場合、currrent_parameterから各値を取得
    elif cmd_type == 'Restore':
        item_no = entry_parameter.get('item_no')
        menu_group_menu_item = current_parameter.get('menu_group_menu_item')
        column_substitution_order = current_parameter.get('column_substitution_order')
        registration_method = current_parameter.get('registration_method')
        movement_name = current_parameter.get('movement_name')
        variable_name = current_parameter.get('variable_name')
        hcl_setting = current_parameter.get('hcl_setting')
        member_variable_name = current_parameter.get('member_variable_name')
        substitution_order = current_parameter.get('substitution_order')

    else:
        return retBool, msg, option

    # 必須項目が入力されていない場合、loadTable側のエラーに渡す。
    if not menu_group_menu_item:
        return retBool, msg, option,
    if not registration_method:
        return retBool, msg, option,
    if not movement_name:
        return retBool, msg, option,
    if not variable_name:
        return retBool, msg, option,
    if not hcl_setting:
        return retBool, msg, option,

    # 「メニューグループ:メニュー:項目(menu_group_menu_item)」で選択したメニューがバンドルが有効かどうかを判定
    where_str = 'WHERE COLUMN_DEFINITION_ID = %s AND DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCLIConst.V_COLUMN_LIST, where_str, [menu_group_menu_item, 0])
    if not ret:
        # IDColumnに選択不可能な値であるため、loadTable側でエラー判定させる。
        return retBool, msg, option
    # メニューIDを取得
    cmdb_menu_id = ret[0].get('MENU_ID')

    # メニューIDをもとにメニュー-テーブル紐付管理のレコードを特定
    where_str = 'WHERE MENU_ID = %s AND DISUSE_FLAG = %s'
    ret = objdbca.table_select('T_COMN_MENU_TABLE_LINK', where_str, [cmdb_menu_id, 0])
    if not ret:
        # IDColumnに選択不可能な値であるため、loadTable側でエラー判定させる。
        return retBool, msg, option
    # 縦型フラグを取得
    vertical_flag = ret[0].get('VERTICAL')

    # バンドルが有効である場合「代入順序(column_substitution_order)」の値があること、バンドルが有効でない場合「代入順序(column_substitution_order)」の値がないことを判定
    if str(vertical_flag) == "0":
        # バンドルが有効ではない(0)場合に、「代入順序(column_substitution_order)」に値があればバリデーションエラー
        if column_substitution_order:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80008")
            return retBool, msg, option,
    else:
        # バンドルが有効(1)の場合に、「代入順序(column_substitution_order)」に値が無ければバリデーションエラー
        if not column_substitution_order:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80009")
            return retBool, msg, option,

    # 登録方式(registration_method)が2:Key型の場合、HCL設定(hcl_setting)が0:Falseであるかどうかを判定
    if registration_method == TFCLIConst.COL_TYPE_KEY and not str(hcl_setting) == "0":
        retBool = False
        msg = g.appmsg.get_api_message("MSG-80010")
        return retBool, msg, option,

    # Movement名(movement_name), Movement名:変数名(variable_name), Movement名:変数名:メンバー変数(member_variable_name)の値は、すべてMovementが同一であるかどうかを判定
    movment_id = movement_name
    mvmt_var_link_movement_id = None
    mvmt_var_member_link_movement_id = None

    # 「Movement-変数紐付」テーブルより、variable_nameから対象のMovementIDを取得
    where_str = 'WHERE MVMT_VAR_LINK_ID = %s AND DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCLIConst.T_MOVEMENT_VAR, where_str, [variable_name, 0])
    if not ret:
        # IDColumnに選択不可能な値であるため、loadTable側でエラー判定させる。
        return retBool, msg, option
    t_movement_var_record = ret[0]
    mvmt_var_link_movement_id = t_movement_var_record.get('MOVEMENT_ID')
    mvmt_var_module_vars_link_id = t_movement_var_record.get('MODULE_VARS_LINK_ID')

    # 「Movement-メンバー変数紐付」member_variable_nameから対象のMovementIDを取得(member_variable_nameの値がある場合のみ)
    if member_variable_name:
        where_str = 'WHERE MVMT_VAR_MEMBER_LINK_ID = %s AND DISUSE_FLAG = %s'
        ret = objdbca.table_select(TFCLIConst.T_MOVEMENT_VAR_MEMBER, where_str, [member_variable_name, 0])
        if not ret:
            # IDColumnに選択不可能な値であるため、loadTable側でエラー判定させる。
            return retBool, msg, option
        t_movement_var_member_record = ret[0]
        mvmt_var_member_link_movement_id = t_movement_var_member_record.get('MOVEMENT_ID')

    if not mvmt_var_member_link_movement_id:
        if not movment_id == mvmt_var_link_movement_id:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80011")
            return retBool, msg, option,
    else:
        if not movment_id == mvmt_var_link_movement_id or not movment_id == mvmt_var_member_link_movement_id or not mvmt_var_link_movement_id == mvmt_var_member_link_movement_id:  # noqa: E501
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80012")
            return retBool, msg, option,

    # Movement名:変数名(variable_name), Movement名:変数名:メンバー変数(member_variable_name)の値は、変数名が同一であるかどうかを判定
    if member_variable_name:
        mvmt_var_member_module_vars_link_id = t_movement_var_member_record.get('MODULE_VARS_LINK_ID')
        if not mvmt_var_module_vars_link_id == mvmt_var_member_module_vars_link_id:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80013")
            return retBool, msg, option,

    # Movement名:変数名(variable_name)の変数タイプを取得
    where_str = 'WHERE MODULE_VARS_LINK_ID = %s AND DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCLIConst.T_MODULE_VAR, where_str, [mvmt_var_module_vars_link_id, 0])
    if not ret:
        # IDColumnに選択不可能な値であるため、loadTable側でエラー判定させる。
        return retBool, msg, option
    t_movement_module_record = ret[0]
    var_type_id = t_movement_module_record.get('TYPE_ID')

    # var_type_idの指定がない(None)の場合はStringタイプとして扱う。
    if not var_type_id:
        var_type_id = '1'  # 1(String)

    # タイプマスターテーブルから、タイプIDのMEMBER_VARS_FLAGとASSIGN_SEQ_FLAGを取得する
    where_str = 'WHERE TYPE_ID = %s AND DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCLIConst.T_TYPE_MASTER, where_str, [var_type_id, 0])
    if not ret:
        retBool = False
        msg = g.appmsg.get_api_message("MSG-80014")
        return retBool, msg, option,
    t_type_master_record = ret[0]
    var_member_vars_flag = t_type_master_record.get('MEMBER_VARS_FLAG')
    var_assign_seq_flag = t_type_master_record.get('ASSIGN_SEQ_FLAG')

    # HCL設定(hcl_setting)が1:Trueの場合、Movement名:変数名:メンバー変数(member_variable_name)、代入順序(substitution_order)は入力不可
    if str(hcl_setting) == "1":
        if member_variable_name or substitution_order:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80019")
            return retBool, msg, option,

    # 以下、「HCL設定」がOFFの場合のみ判定
    if str(hcl_setting) == "0":
        # 変数のタイプがmap(7)の場合はバリデーションエラー
        if var_type_id == "7":
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80021")
            return retBool, msg, option,

        # Movement名:変数名(variable_name)の変数タイプから、メンバー変数(member_variable_name)に値が必要かどうかを判定
        if str(var_member_vars_flag) == "1":
            if not member_variable_name:
                # var_member_vars_flagがTrue(1)かつMovement名:変数名:メンバー変数(member_variable_name)がない場合はバリデーションエラー
                retBool = False
                msg = g.appmsg.get_api_message("MSG-80015")
                return retBool, msg, option,
            else:
                # Movement名:変数名:メンバー変数(member_variable_name)から、代入順序に値が必要かどうかを判断するため、変数のタイプを取得する
                # Movement-メンバー変数ビューからレコードを特定
                where_str = 'WHERE MVMT_VAR_MEMBER_LINK_ID = %s AND DISUSE_FLAG = %s'
                ret = objdbca.table_select(TFCLIConst.V_MOVEMENT_VAR_MEMBER, where_str, [member_variable_name, 0])
                if not ret:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-80022")
                    return retBool, msg, option,
                child_member_vars_id = ret[0].get('CHILD_MEMBER_VARS_ID')

                # メンバー変数管理テーブルからレコードを特定
                where_str = 'WHERE CHILD_MEMBER_VARS_ID = %s AND DISUSE_FLAG = %s'
                ret = objdbca.table_select(TFCLIConst.T_VAR_MEMBER, where_str, [child_member_vars_id, 0])
                if not ret:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-80022")
                    return retBool, msg, option,

                # メンバー変数のタイプを特定
                member_var_type_id = ret[0].get('CHILD_VARS_TYPE_ID')

                # var_type_idの指定がない(None)の場合はStringタイプとして扱う。
                if not member_var_type_id:
                    member_var_type_id = '1'  # 1(String)

                # タイプマスターテーブルから、タイプIDのASSIGN_SEQ_FLAGを取得する
                where_str = 'WHERE TYPE_ID = %s AND DISUSE_FLAG = %s'
                ret = objdbca.table_select(TFCLIConst.T_TYPE_MASTER, where_str, [member_var_type_id, 0])
                if not ret:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-80014")
                    return retBool, msg, option,
                t_type_master_record = ret[0]
                member_var_assign_seq_flag = t_type_master_record.get('ASSIGN_SEQ_FLAG')

                # member_var_assign_seq_flagから代入順序が必要かどうかを判断し、値の有無でバリデーションエラー判定を行う
                if str(member_var_assign_seq_flag) == "1":
                    if not substitution_order:
                        # var_assign_seq_flagがTrue(1)かつ代入順序(substitution_order)がない場合はバリデーションエラー
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-80023")
                        return retBool, msg, option,
                else:
                    if substitution_order:
                        # var_assign_seq_flagがFalse(0)かつ代入順序(substitution_order)がある場合はバリデーションエラー
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-80024")
                        return retBool, msg, option,

        else:
            if member_variable_name:
                # var_member_vars_flagがFalse(0)かつMovement名:変数名:メンバー変数(member_variable_name)がある場合はバリデーションエラー
                retBool = False
                msg = g.appmsg.get_api_message("MSG-80016")
                return retBool, msg, option,
            else:
                # Movement名:変数名(variable_name)の変数タイプから、代入順序(substitution_order)に値が必要かどうかを判定
                if str(var_assign_seq_flag) == "1":
                    if not substitution_order:
                        # var_assign_seq_flagがTrue(1)かつ代入順序(substitution_order)がない場合はバリデーションエラー
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-80017")
                        return retBool, msg, option,
                else:
                    if substitution_order:
                        # var_assign_seq_flagがFalse(0)かつ代入順序(substitution_order)がある場合はバリデーションエラー
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-80018")
                        return retBool, msg, option,

    # Movement名:変数名(variable_name)が一致するレコードがほかにある場合、HCL設定(hcl_setting)の値が統一になっているかどうかを判定
    if cmd_type == 'Update':
        # 「更新」の場合、検索条件にて自分自身のIDを除外する
        where_str = 'WHERE MVMT_VAR_LINK_ID = %s AND DISUSE_FLAG = %s AND VALUE_AUTOREG_ID <> %s'
        ret = objdbca.table_select(TFCLIConst.T_VALUE_AUTOREG, where_str, [variable_name, 0, item_no])
    else:
        # 「登録」「復活」の場合の検索条件
        where_str = 'WHERE MVMT_VAR_LINK_ID = %s AND DISUSE_FLAG = %s'
        ret = objdbca.table_select(TFCLIConst.T_VALUE_AUTOREG, where_str, [variable_name, 0])

    t_value_autoreg_records = ret
    if t_value_autoreg_records:
        hcl_check_flag = True
        # 同一の「Movement名:変数名」のレコードからHCL設定の値をチェックする
        for record in t_value_autoreg_records:
            if not str(hcl_setting) == str(record.get('HCL_FLAG')):
                hcl_check_flag = False

        # HCL設定(hcl_setting)の値に差異があればバリデーションエラー
        if not hcl_check_flag:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-80020")
            return retBool, msg, option,

    return retBool, msg, option,
