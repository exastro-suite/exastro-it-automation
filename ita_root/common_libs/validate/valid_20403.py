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
import os
import base64
from flask import g
from common_libs.ansible_driver.functions.commn_vars_used_list_update import CommnVarsUsedListUpdate, CommnVarsUsedListDisuseSet
from common_libs.ansible_driver.functions.util import get_AnsibleDriverTmpPath
from common_libs.ansible_driver.classes.CheckAnsibleRoleFiles import VarStructAnalysisFileAccess
from common_libs.ansible_driver.classes.VarStructAnalJsonConvClass import VarStructAnalJsonConv


def external_valid_menu_after(objDBCA, objtable, option):
    """
    登録前ホストネームバリデーション(登録/更新/廃止)
    ARGS:
        objdbca :DB接続クラスインスタンス
        objtabl :メニュー情報、カラム紐付、関連情報
        option :パラメータ、その他設定値
        
    RETRUN:
        retBoo :True/ False
        msg :エラーメッセージ
        option :受け取ったもの
    """
    retBool = True
    retStrBody = ""
    zip_data = None
    zip_file_path = ""
    role_package_name = ""
    PkeyID = option['uuid']

    zipFileName = "{}/20403_zip_format_role_package_file_{}.zip"
    if option["cmd_type"] == "Register":
        zip_data = option["entry_parameter"]["file"]["zip_format_role_package_file"]
        role_package_name = option["entry_parameter"]["parameter"]["role_package_name"]

    if option["cmd_type"] == "Update":
        if option["entry_parameter"]["file"]["zip_format_role_package_file"] != \
           option["current_parameter"]["file"]["zip_format_role_package_file"]:
            zip_data = option["entry_parameter"]["file"]["zip_format_role_package_file"]

    # ロールパッケージの変更判定
    if zip_data:
        # zipファイルを生成
        zip_file_path = zipFileName.format(get_AnsibleDriverTmpPath(), os.getpid())
        fd = open(zip_file_path, "wb")
        fd.write(base64.b64decode(zip_data))
        fd.close()

    def_vars_list = {}
    def_varsval_list = {}
    def_array_vars_list = {}
    cpf_vars_list = {}
    tpf_vars_list = {}
    gbl_vars_list = {}
    ITA2User_var_list = {}
    User2ITA_var_list = {}
    save_vars_array = {}
    disuse_role_chk = True

    global_vars_master_list = {}
    template_master_list = {}
    objMTS = ""
    FileID = "3"
    obj = VarStructAnalysisFileAccess(objMTS,
                                      objDBCA,
                                      global_vars_master_list,
                                      template_master_list,
                                      '',
                                      False,
                                      False)
    JsonObj = VarStructAnalJsonConv()
    if option["cmd_type"] == "Register" or option["cmd_type"] == "Update" or option["cmd_type"] == "Restore":
        # ロールパッケージzipが変更されているか判定
        if zip_data:
            retAry = obj.RolePackageAnalysis(zip_file_path,
                                             role_package_name,
                                             PkeyID,
                                             disuse_role_chk,
                                             def_vars_list,
                                             def_varsval_list,
                                             def_array_vars_list,
                                             True,
                                             cpf_vars_list,
                                             True,
                                             tpf_vars_list,
                                             gbl_vars_list,
                                             ITA2User_var_list,
                                             User2ITA_var_list,
                                             save_vars_array)
            retBool = retAry[0][0]
            # intErrorType = retAry[0][1]
            # aryErrMsgBody = retAry[0][2]
            retStrBody = retAry[0][3]
            def_vars_list = retAry[1]
            def_varsval_list = retAry[2]
            def_array_vars_list = retAry[3]
            cpf_vars_list = retAry[4]
            tpf_vars_list = retAry[5]
            gbl_vars_list = retAry[6]
            ITA2User_var_list = retAry[7]
            User2ITA_var_list = retAry[8]
            save_vars_array = retAry[9]
            Role_name_list = retAry[10]
            
            if retBool is False:
                return retBool, retStrBody, option

            if retBool is True:
                # 変数構造解析結果を退避
                JsonStr = JsonObj.VarStructAnalJsonDumps(def_vars_list,
                                                         def_array_vars_list,
                                                         tpf_vars_list,
                                                         ITA2User_var_list,
                                                         gbl_vars_list,
                                                         Role_name_list)
                UpData = {}
                UpData["ROLE_PACKAGE_ID"] = PkeyID
                UpData["VAR_STRUCT_ANAL_JSON_STRING"] = JsonStr
                objDBCA.table_update("T_ANSR_MATL_COLL", UpData, "ROLE_PACKAGE_ID", False)

            # 復活の場合はテンプレート管理で定義されている変数構造と一致していない変数があるかのチェックまで行う。
            if option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
                if retBool is True:
                    retAry = CommnVarsUsedListUpdate(objDBCA, option, PkeyID, FileID, save_vars_array)
                    retBool = retAry[0]
                    retStrBody = retAry[1]
                    if retBool is False:
                        return retBool, retStrBody, option

    if option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
            
        # 廃止の場合、関連レコードを廃止
        # 復活の場合、関連レコードを復活
        retAry = CommnVarsUsedListDisuseSet(objDBCA, option, PkeyID, FileID)
        retBool = retAry[0]
        retStrBody = retAry[1]
        if retBool is False:
            return retBool, retStrBody, option

    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": "204"}
    primary_key_name = "ROW_ID"
    objDBCA.table_update(table_name, data_list, primary_key_name, False)

    return retBool, retStrBody, option
