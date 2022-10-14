import inspect
import os

from flask import g

from common_libs.ansible_driver.classes.VarStructAnalJsonConvClass import VarStructAnalJsonConv
from common_libs.ansible_driver.functions.var_struct_analysis import put_var_struct_analysis
from common_libs.ansible_driver.functions.commn_vars_used_list_update import CommnVarsUsedListUpdate, CommnVarsUsedListDisuseSet
from common_libs.ansible_driver.classes.CheckAnsibleRoleFiles import DefaultVarsFileAnalysis, VarStructAnalysisFileAccess

def external_valid_menu_after(objdbca, objtable, option):
    retBool = True
    msg = ''
    boolExecuteContinue = True
    boolSystemErrorFlag = False
    
    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = [{"LOADED_FLG": "0", "ROW_ID": "202"}, {"LOADED_FLG": "0", "ROW_ID": "203"}, {"LOADED_FLG": "0", "ROW_ID": "204"}]
    primary_key_name = "ROW_ID"
    for i in data_list:
        objdbca.table_update(table_name, i, primary_key_name, False)

    if option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        # ----更新前のレコードから、各カラムの値を取得
        strVarsList = option["current_parameter"]["parameter"]["variable_definition"]
        
        strVarName = option["current_parameter"]["parameter"]["template_embedded_variable_name"]
        
        PkeyID = option["current_parameter"]["parameter"]["template_id"]
        # 更新前のレコードから、各カラムの値を取得----
    elif option["cmd_type"] == "Update" or option["cmd_type"] == "Register":
        if "variable_definition" in option["entry_parameter"]["parameter"]:
            strVarsList = option["entry_parameter"]["parameter"]["variable_definition"]
        else:
            strVarsList = ""
        
        if strVarsList is None:
            strVarsList = ""
            
        if "template_embedded_variable_name" in option["entry_parameter"]["parameter"]:
            strVarName = option["entry_parameter"]["parameter"]["template_embedded_variable_name"]
        else:
            strVarName = None
        if option["cmd_type"] == "Update":
            PkeyID = option["current_parameter"]["parameter"]["template_id"]
        else:
            if "uuid" in option:
                PkeyID = option["uuid"]
            else:
                PkeyID = None

    LCA_vars_use = False
    GBL_vars_info = {}
    Array_vars_use = False
    Vars_list = {}
    Array_vars_list = {}
    VarVal_list = {}
    if option["cmd_type"] == "Restore":
        # 変数定義の解析結果をDBから取得
        ret = objdbca.table_select("T_ANSC_TEMPLATE_FILE", "WHERE ANS_TEMPLATE_ID = %s", [PkeyID])
        if len(ret) == 1:
            var_struct_anal_json_string = ret[0]["VAR_STRUCT_ANAL_JSON_STRING"]
        
        # 変数定義の解析結果をデコード
        obj = VarStructAnalJsonConv()
        retAry = obj.TemplateVarStructAnalJsonLoads(var_struct_anal_json_string)
        Vars_list = retAry[0]
        Array_vars_list = retAry[1]
        LCA_vars_use = retAry[2]
        Array_vars_use = retAry[3]
        GBL_vars_info = retAry[4]
        VarVal_list = retAry[5]
        del obj
    elif option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        ret = put_var_struct_analysis(objdbca, option, PkeyID, strVarName, strVarsList, Vars_list, Array_vars_list, LCA_vars_use, Array_vars_use, GBL_vars_info, VarVal_list)
        if ret[0] is False:
            retBool = False
            msg = ret[1]
        if ret[0] is True:
            # 変数解析結果をT_ANSC_TEMPLATE_FILEテーブルに追加
            table_name = "T_ANSC_TEMPLATE_FILE"
            primary_key_name = "ANS_TEMPLATE_ID"
            data_list = {primary_key_name: PkeyID, "VAR_STRUCT_ANAL_JSON_STRING": ret[2]}
            objdbca.table_update(table_name, data_list, primary_key_name, False)
            Vars_list = ret[3]
            Array_vars_list = ret[4]
            LCA_vars_use = ret[5]
            Array_vars_use = ret[6]
            ITA2User_var_list = ret[7]
            GBL_vars_info = ret[8]
            VarVal_list = ret[9]

    if retBool is True:
        if option["cmd_type"] == "Register" or option["cmd_type"] == "Update" or option["cmd_type"] == "Restore":
            # 各テンプレート変数の変数構造解析結果を取得
            table_name = "T_ANSC_TEMPLATE_FILE"
            where_str = "WHERE DISUSE_FLAG = '0'"
            bind_value_list = []
            ret = objdbca.table_select(table_name, where_str, bind_value_list)
            if len(ret) != 0:
                for row in ret:
                    if row["ANS_TEMPLATE_ID"] == PkeyID:
                        continue
                    chk_PkeyID           = row['ANS_TEMPLATE_ID']
                    chk_strVarName       = row['ANS_TEMPLATE_VARS_NAME']
                    chk_strVarsList      = row['VARS_LIST']
                    chk_LCA_vars_use     = False
                    chk_GBL_vars_info    = {}
                    chk_Array_vars_use   = False
                    chk_Vars_list        = {}
                    chk_Array_vars_list  = {}
                    chk_VarVal_list      = {}
                    if row["VAR_STRUCT_ANAL_JSON_STRING"]:
                        obj = VarStructAnalJsonConv()
                        retAry = obj.TemplateVarStructAnalJsonLoads(row["VAR_STRUCT_ANAL_JSON_STRING"])
                        chk_Vars_list        = retAry[0]
                        chk_Array_vars_list  = retAry[1]
                        chk_LCA_vars_use     = retAry[2]
                        chk_Array_vars_use   = retAry[3]
                        chk_GBL_vars_info    = retAry[4]
                        chk_VarVal_list      = retAry[5]
                        if retBool is True:
                            cmp_Vars_list          = {}
                            cmp_Array_vars_list    = {}
                            cmp_Vars_list[chk_strVarName] = {}
                            cmp_Array_vars_list[chk_strVarName] = {}
                            cmp_Vars_list[strVarName] = {}
                            cmp_Array_vars_list[strVarName] = {}
                            # 変数構造解析結果
                            cmp_Vars_list[chk_strVarName]['dummy'] = chk_Vars_list
                            cmp_Array_vars_list[chk_strVarName]['dummy'] = chk_Array_vars_list
    
                            # 自レコードの変数構造解析結果
                            cmp_Vars_list[strVarName]['dummy'] = Vars_list
                            cmp_Array_vars_list[strVarName]['dummy'] = Array_vars_list
        
                            chkObj = DefaultVarsFileAnalysis(None)
    
                            err_vars_list = {}
                            # 変数構造が一致していない変数があるか確認
                            ret = chkObj.chkallVarsStruct(cmp_Vars_list, cmp_Array_vars_list, err_vars_list)
                            if ret[0] is False:
                                err_vars_list = ret[1]
                                for err_var_name, dummy in err_vars_list.items():
                                    if len(msg) != 0:
                                        msg += "\n"
                                    msg += g.appmsg.get_api_message("MSG-10595", [err_var_name, list(dummy.keys())])
                                    retBool = False
                                    boolExecuteContinue = False
                            del chkObj
    # 各テンプレート変数の定義変数で変数の構造に差異がないか確認

    if retBool is True:
        if option["cmd_type"] == "Register" or option["cmd_type"] == "Update" or option["cmd_type"] == "Restore":
            global_vars_master_list = {}
            template_master_list = {}
            table_name = "T_ANSC_TEMPLATE_FILE"
            where_str = "WHERE DISUSE_FLAG = '0'"
            bind_value_list = []
            ret = objdbca.table_select(table_name, where_str, bind_value_list)
            # RolePackageAnalysisは変数構造の取得のみ
            obj = VarStructAnalysisFileAccess(None, objdbca, global_vars_master_list, template_master_list, '', False, True)
            # ロールパッケージで同じ変数を使用している場合に、変数定義が一致しているか判定
            def_vars_list = {}
            def_vars_list["__ITA_DUMMY_ROLE_NAME__"] = Vars_list
            def_array_vars_list = {}
            def_array_vars_list["__ITA_DUMMY_ROLE_NAME__"] = Array_vars_list
            ret = obj.AllRolePackageAnalysis(-1, "__ITA_DUMMY_ROLE_PACKAGE_NAME__", def_vars_list, def_array_vars_list, "MSG-10611")

            if ret is False:
                retBool = False
                msg = obj.GetLastError()[0]
                boolExecuteContinue = False
            del obj
            
    # LCA/多段変数を定義している場合、ロール以外でテンプレートファイルを使用していないか判定
    # 廃止以外は呼び出す
    if retBool is True:
        table_name = "T_ANSC_TEMPLATE_FILE"
        primary_key_name = "ANS_TEMPLATE_ID"
        if option["cmd_type"] == "Register" or option["cmd_type"] == "Update" or option["cmd_type"] == "Restore":
            if Array_vars_use is True or LCA_vars_use is True:
                data_list = {primary_key_name: PkeyID, "ROLE_ONLY_FLAG": "1"}
                objdbca.table_update(table_name, data_list, primary_key_name, False)
                # legacy/pionnerのplaybookでテンプレート変数を使用しているか確認
                table_name = "T_ANSC_COMVRAS_USLIST"
                where_str = "WHERE VAR_NAME= %s AND FILE_ID in ('1','2') AND DISUSE_FLAG='0'"
                bind_value_list = [strVarName]
                ret = objdbca.table_select(table_name, where_str, bind_value_list=[strVarName])
                
                if len(ret) != 0:
                    msg = g.appmsg.get_api_messagee("MSG-10574")
                    retBool = False
                    boolExecuteContinue = False
                    for row in ret:
                        if row['FILE_ID'] == "1":  # Legacy pllaybook
                            msgid = 'MSG-10575'
                        elif row['FILE_ID'] == '2':  # Pioneer 対話ファイル
                            msgid = 'MSG-10576'
                        if len(msg) != 0:
                            msg += "\n"
                        msg += g.appmsg.get_api_message(msgid, [row['CONTENTS_ID']])
                        retBool = False
                        boolExecuteContinue = False
            else:
                data_list = {primary_key_name: PkeyID, "ROLE_ONLY_FLAG": "0"}
                objdbca.table_update(table_name, data_list, primary_key_name, False)

    # グローバル変数が定義されている場合に共通変数利用リストを更新
    FileID = 4
    if retBool is True:
        if option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
            # 0件で廃止するレコードがある場合があるので、CommnVarsUsedListUpdateをCall
            ret = CommnVarsUsedListUpdate(objdbca, option, PkeyID, FileID, GBL_vars_info)

            if ret[0] is False:
                retBool = False
                if len(msg) != 0:
                    msg += "\n"
                msg += ret[1]
        elif option["cmd_type"] == "Restore" or option["cmd_type"] == "Discard":
            # 廃止の場合、関連レコードを廃止
            # 復活の場合、関連レコードを復活
            ret = CommnVarsUsedListDisuseSet(objdbca, option, PkeyID, FileID)
            if ret[0] is False:
                retBool = False
                if len(msg) != 0:
                    msg += "\n"
                msg += ret[1]

    if boolSystemErrorFlag is True:
        retBool = False
        # ----システムエラー
        msg = g.appmsg.get_api_message("MSG-10886")
    return retBool, msg, option,