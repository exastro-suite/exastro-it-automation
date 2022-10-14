from flask import g


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    # バックヤード起動フラグ
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": "204"}
    primary_key_name = "ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, False)
    
    # 登録および更新の際ロールパッケージ名取得
    if option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        role_id = option["entry_parameter"]["parameter"]["role_package_name_role_name"]
        table_name = "T_ANSR_ROLE_NAME"
        sql = "WHERE ROLE_ID = %s"
        ret = objdbca.table_select(table_name, sql, [role_id])
        if len(ret) == 1:
            option["entry_parameter"]["parameter"]["role_package_name"] = ret[0]["ROLE_PACKAGE_ID"]

    return retBool, msg, option,


def external_valid_menu_after(objdbca, objtable, option):
    retBool = True
    msg = ''
    
    # ----同一Movementに複数のロールパッケージが登録されていないか判定
    if option["cmd_type"] == "Register" or option["cmd_type"] == "Update" or option["cmd_type"] == "Restore":
        table_name = "T_ANSR_MVMT_MATL_LINK"
        where_str = "WHERE MVMT_MATL_LINK_ID <> %s AND MOVEMENT_ID = %s AND ROLE_PACKAGE_ID <> %s  AND DISUSE_FLAG = 0 "
        aryForBind = {}
        aryForBind['MVMT_MATL_LINK_ID'] = option["uuid"]
        if option["cmd_type"] == "Restore":
            aryForBind['MOVEMENT_ID'] = option["current_parameter"]["parameter"]["movement"]
            aryForBind['ROLE_PACKAGE_ID'] = option["current_parameter"]["parameter"]["role_package_name"]
        else:
            aryForBind['MOVEMENT_ID'] = option["entry_parameter"]["parameter"]["movement"]
            aryForBind['ROLE_PACKAGE_ID'] = option["entry_parameter"]["parameter"]["role_package_name"]
        ret = objdbca.table_count(table_name, where_str, bind_value_list=[aryForBind['MVMT_MATL_LINK_ID'], aryForBind['MOVEMENT_ID'], aryForBind['ROLE_PACKAGE_ID']])
        if ret == 0:
            retBool = True
        else:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-10400")
    # 同一Movementに複数のロールパッケージが登録されていないか判定----
    return retBool, msg, option,