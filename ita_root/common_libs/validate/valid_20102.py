from flask import g

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    
    if option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        
        # 更新前のレコードから、各カラムの値を取得
        str_exec_mode    = option["current_parameter"]["parameter"]["execution_engine"]

        str_twr_host_id   = option["current_parameter"]["parameter"]["representative_server"]
        
        str_twr_protocol = option["current_parameter"]["parameter"]['ansible_automation_controller_protocol']
        
        str_twr_port     = option["current_parameter"]["parameter"]['ansible_automation_controller_port']
        
        str_org_name     = option["current_parameter"]["parameter"]['organization_name']
        
        str_token       = option["current_parameter"]["parameter"]['authentication_token']

        # 更新前のレコードから、各カラムの値を取得
    elif option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        if "execution_engine" in option["entry_parameter"]["parameter"]:
            str_exec_mode = option["entry_parameter"]["parameter"]["execution_engine"]
        else:
            str_exec_mode = None
        
        if "representative_server" in option["entry_parameter"]["parameter"]:
            str_twr_host_id = option["entry_parameter"]["parameter"]["representative_server"]
        else:
            str_twr_host_id = None
        
        if "ansible_automation_controller_protocol" in option["entry_parameter"]["parameter"]:
            str_twr_protocol = option["entry_parameter"]["parameter"]['ansible_automation_controller_protocol']
        else:
            str_twr_protocol = None
        
        if "ansible_automation_controller_port" in option["entry_parameter"]["parameter"]:
            str_twr_port = option["entry_parameter"]["parameter"]['ansible_automation_controller_port']
        else:
            str_twr_port = None
        
        if "organization_name" in option["entry_parameter"]["parameter"]:
            str_org_name = option["entry_parameter"]["parameter"]['organization_name']
        else:
            str_org_name = None
        
        # PasswordColumn
        str_token = option["current_parameter"]["parameter"]['authentication_token']
        if not str_token:
            if "authentication_token" in option["entry_parameter"]["parameter"]:
                str_token = option["entry_parameter"]["parameter"]['authentication_token']

    if option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        pass
    elif option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        ret_str_body = ''
        ary = []
        ary.append({"VALUE": str_twr_host_id, "MSG_CODE": "MSG-10881"})
        ary.append({"VALUE": str_twr_protocol, "MSG_CODE": "MSG-10882"})
        ary.append({"VALUE": str_twr_port, "MSG_CODE": "MSG-10883"})
        ary.append({"VALUE": str_org_name, "MSG_CODE": "MSG-10884"})
        ary.append({"VALUE": str_token, "MSG_CODE": "MSG-10885"})
        # 実行エンジンがTowerの場合の、Ansible Towerインターフェースの必須入力チェック
        if str_exec_mode != AnscConst.DF_EXEC_MODE_ANSIBLE:
            for i in ary:
                # nullまたはNoneの場合空文字と同じ扱いにする
                if i["VALUE"] is None:
                    i["VALUE"] = ""
                if len(str(i["VALUE"]).strip()) == 0:
                    msg1 = g.appmsg.get_api_message(i['MSG_CODE'])
                    if len(ret_str_body) != 0:
                        ret_str_body += "\n"
                    ret_str_body += g.appmsg.get_api_message("MSG-10880", [msg1])
        if len(ret_str_body) != 0:
            retBool = False
    if retBool is False:
        msg = ret_str_body
    
    return retBool, msg, option,
