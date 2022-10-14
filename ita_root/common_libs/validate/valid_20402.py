import os
import inspect
from flask import g

from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.functions.util import get_AnsibleDriverTmpPath


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    
    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": "204"}
    primary_key_name = "ROW_ID"
    ret = objdbca.table_update(table_name, data_list, primary_key_name, False)
    if ret is False:
        msg = g.appmsg.get_api_message("MSG-10888", [os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno])
    # 入力値取得
    entry_parameter = option.get('entry_parameter').get('parameter')
    current_parameter = option.get('current_parameter').get('parameter')
    cmd_type = option.get("cmd_type")

    if cmd_type == "Register":
        option["entry_parameter"]["parameter"]["orchestrator"] = 3
        in_string = entry_parameter.get('header_section')
    
    if cmd_type == "Update":
        in_string = entry_parameter.get('header_section')
        
    if cmd_type == "Restore" or cmd_type == "Discard":
        in_string = current_parameter.get('header_section')
    
    if in_string is None:
        in_string = ""
    # YAMLチェック
    tmpFile = "{}/HeaderSectionYamlParse_{}".format(get_AnsibleDriverTmpPath(), os.getpid())
    fd = open(tmpFile, 'w')
    fd.write(in_string)
    fd.close()
    obj = YamlParse()
    ret = obj.Parse(tmpFile)
    os.remove(tmpFile)
    if ret is False:
        retBool = False
        error_detail = obj.GetLastError()
        if len(msg) != 0:
            msg += "\n"
        msg = g.appmsg.get_api_message("MSG-10888", [error_detail])

    return retBool, msg, option,
