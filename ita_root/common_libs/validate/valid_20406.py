def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": "204"}
    primary_key_name = "ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, False)
    return retBool, msg, option,
