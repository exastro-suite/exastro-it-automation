# Copyright 2022 NEC Corporation#
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

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.functions.util import getSpecialColumnVaule

def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''

    # 削除時はチェックしない
    # Do not check when deleting
    if option.get("cmd_type") == "Delete":
        return retBool, msg, option

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
            exist_str_twr_host_id = True
        else:
            str_twr_host_id = None
            exist_str_twr_host_id = False

        if "ansible_automation_controller_protocol" in option["entry_parameter"]["parameter"]:
            str_twr_protocol = option["entry_parameter"]["parameter"]['ansible_automation_controller_protocol']
            exist_str_twr_protocol = True
        else:
            str_twr_protocol = None
            exist_str_twr_protocol = False

        if "ansible_automation_controller_port" in option["entry_parameter"]["parameter"]:
            str_twr_port = option["entry_parameter"]["parameter"]['ansible_automation_controller_port']
            exist_str_twr_port = True
        else:
            str_twr_port = None
            exist_str_twr_port = False

        if "organization_name" in option["entry_parameter"]["parameter"]:
            str_org_name = option["entry_parameter"]["parameter"]['organization_name']
        else:
            str_org_name = None

        # PasswordColumn
        str_token = getSpecialColumnVaule("authentication_token", option)

    if option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        pass
    elif option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        ret_str_body = ''
        ary = []
        ary.append({"VALUE": str_twr_host_id, "MSG_CODE": "MSG-10881", "EXIST": exist_str_twr_host_id})
        ary.append({"VALUE": str_twr_protocol, "MSG_CODE": "MSG-10882", "EXIST": exist_str_twr_protocol})
        ary.append({"VALUE": str_twr_port, "MSG_CODE": "MSG-10883", "EXIST": exist_str_twr_port})
        # 組織名は必須項目から外す。
        ary.append({"VALUE": str_token, "MSG_CODE": "MSG-10885", "EXIST": True})

        # 実行エンジンがAAP, AAP(Cloud)の場合、Ansible Automation Platformインターフェースの必須入力チェック
        if  str_exec_mode in [AnscConst.DF_EXEC_MODE_AAC, AnscConst.DF_EXEC_MODE_AAP_CLOUD]:
            for i in ary:
                # nullまたはNoneの場合空文字と同じ扱いにする
                if i["VALUE"] is None:
                    i["VALUE"] = ""
                if i["EXIST"] and len(str(i["VALUE"]).strip()) == 0:
                    msg1 = g.appmsg.get_api_message(i['MSG_CODE'])
                    if len(ret_str_body) != 0:
                        ret_str_body += "\n"
                    ret_str_body += g.appmsg.get_api_message("MSG-10880", [msg1])
        if len(ret_str_body) != 0:
            retBool = False

        # 実行エンジンがAAPの場合に、AAPホスト一覧の、パスワード認証方式・ユーザーのチェック処理
        # AAP on cloud 対応で、AAPホスト一覧のパスワード認証方式,ユーザの必須を廃止したので、こちらでホスト一覧の簡易チェックを行う。
        if str_exec_mode == AnscConst.DF_EXEC_MODE_AAC:
            _ret, _msg = _check_aap_host_list_nodes(objdbca)
            if not _ret:
                retBool = False
                if len(ret_str_body) != 0:
                    ret_str_body += "\n"
                ret_str_body += _msg

    if retBool is False:
        msg = ret_str_body

    return retBool, msg, option,


def _check_aap_host_list_nodes(objdbca):
    """AAPホスト一覧のパスワード認証方式,ユーザの確認。

    Args:
        objdbca (_type_): DB接クラス  DBConnectWs()

    Returns:
        bool: True: 正常、False: 異常
        str: メッセージ
    """
    _msg = ""
    chk_node = []
    g.applogger.debug("Check AAP host list nodes.")
    rows = objdbca.table_select("t_ansc_tower_host", "WHERE DISUSE_FLAG = %s", ["0"])
    for row in rows:
        host_id = row.get("ANSTWR_HOST_ID")
        host_name = row.get("ANSTWR_HOSTNAME")
        auth_type = row.get("ANSTWR_LOGIN_AUTH_TYPE")
        user = row.get("ANSTWR_LOGIN_USER")
        if not (user and auth_type):
            chk_node.append(f"{host_name}({host_id})")

    if chk_node:
        # Ansible Automation Platform ホスト一覧のノードに、認証方式またはユーザが未設定のホストがあります。ホスト一覧のノードを確認してください。
        _msg = g.appmsg.get_api_message("MSG-11016", [", ".join(chk_node)])

        return False, _msg

    return True, ""
