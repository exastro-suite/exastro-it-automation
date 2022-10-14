import os
import re
from flask import g

from common_libs.ansible_driver.functions.util import get_AnsibleDriverTmpPath
from common_libs.ansible_driver.classes.CheckAnsibleRoleFiles import YAMLFileAnalysis
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.VarStructAnalJsonConvClass import VarStructAnalJsonConv


def put_var_struct_analysis(objdbca, option, pkey_id, TPF_var_name, var_struct_string, vars_list, array_vars_list, LCA_vars_use, array_vars_use, GBL_vars_info, var_val_list):
    retBool = True
    msg = ""
    jsonStr = ''

    vars_list       = []
    array_vars_list = []
    GBL_vars_info   = {}
    GBL_vars_info = {}
    var_val_list     = []
    LCA_vars_use    = False
    array_vars_use  = False
    # 変数定義を一時ファイルに保存
    tmp_file_name = "{}/TemplateVarList_{}.yaml".format(get_AnsibleDriverTmpPath(), os.getpid())
    fd = open(tmp_file_name, 'w')
    fd.write(var_struct_string)
    fd.close()

    chkObj = YAMLFileAnalysis(None)
    role_pkg_name = TPF_var_name
    rolename = 'dummy'
    display_file_name = ''
    ITA2User_var_list = []
    User2ITA_var_list = []
    parent_vars_list = []
    
    # 変数定義を解析
    ret = chkObj.VarsFileAnalysis(AnscConst.LC_RUN_MODE_VARFILE, tmp_file_name, parent_vars_list, vars_list, array_vars_list, var_val_list, role_pkg_name, rolename, display_file_name, ITA2User_var_list, User2ITA_var_list)
    parent_vars_list = ret[1]
    vars_list = ret[2]
    array_vars_list = ret[3]
    var_val_list = ret[4]
    if isinstance(parent_vars_list, dict):
        parent_vars_list = parent_vars_list.items()
    # 解析結果にエラーがある場合
    if ret[0] is False:
        retBool = False
        msg = chkObj.GetLastError()[0]
    else:
        for vars_info in parent_vars_list:
            var_name = vars_info[1]["VAR_NAME"]
            # グローバル変数の場合
            ret = re.search(AnscConst.GBL_parent_VarName, var_name)
            if ret is not None:
                # 多段定義の場合
                if vars_list.get(var_name) is None:
                    msg = g.appmsg.get_api_message("MSG-10572", [var_name])
                    retBool = False
                else:
                    if vars_list[var_name] == 0:
                        if ("1" in GBL_vars_info.keys()) is False:
                            GBL_vars_info["1"] = {}
                        GBL_vars_info['1'][var_name] = '0'
                    else:
                        # 複数具体値定義の場合
                        msg = g.appmsg.get_api_message("MSG-10572", [var_name])
                        retBool = False
            else:
                ret = re.search(AnscConst.VAR_parent_VarName, var_name)
                if ret is not None:
                    # 多段変数の場合
                    if array_vars_list.get(var_name) is not None:
                        if array_vars_list[var_name] is not None:
                            array_vars_use = True
                else:
                    # 変数名がastrollで扱えない場合
                    msg = g.appmsg.get_api_message("MSG-'10569", [var_name])
                    retBool = False
    
    # 一時ファイル削除
    os.remove(tmp_file_name)
    if retBool is True:
        obj = VarStructAnalJsonConv()
        jsonStr = obj.TemplateVarStructAnalJsonDumps(vars_list, array_vars_list, LCA_vars_use, array_vars_use, ITA2User_var_list, GBL_vars_info, var_val_list)
    return retBool, msg, jsonStr, vars_list, array_vars_list, LCA_vars_use, array_vars_use, ITA2User_var_list, GBL_vars_info, var_val_list
