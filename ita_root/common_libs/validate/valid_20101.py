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
import os
import inspect

from common_libs.ansible_driver.classes.menu_required_check import AuthTypeParameterRequiredCheck
from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.functions.util import getSpecialColumnVaule
from common_libs.ansible_driver.functions.util import get_OSTmpPath
from common_libs.ansible_driver.functions.util import addAnsibleCreateFilesPath
from common_libs.ansible_driver.functions.util import rmAnsibleCreateFiles
from common_libs.common.exception import AppException

def external_valid_menu_before(objdbca, objtable, option):
    """
    ARGS:
        objdbca :DB接続クラスインスタンス
        objtable :メニュー情報、カラム紐付、関連情報
        option :パラメータ、その他設定値

    RETRUN:
        retBoo :True/ False
        msg :エラーメッセージ
        option :受け取ったもの
    """
    # /tmpに作成したファイル・ディレクトリパスを保存するファイル名
    g.AnsibleCreateFilesPath = "{}/{}_{}".format(get_OSTmpPath(), os.path.basename(inspect.currentframe().f_code.co_filename), os.getpid())

    retBool = True
    msg = ''
    ret_str_body = ''
    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = [{"LOADED_FLG": "0", "ROW_ID": "202"}, {"LOADED_FLG": "0", "ROW_ID": "203"}, {"LOADED_FLG": "0", "ROW_ID": "204"}]
    primary_key_name = "ROW_ID"
    for i in data_list:
        objdbca.table_update(table_name, i, primary_key_name, False)
    # option["entry_parameter"]["parameter"]はUI入力ベースの情報
    # option["current_parameter"]["parameter"]はDBに登録済みの情報
    if option["cmd_type"] == "Register":
        # ホスト名
        if "host_name" in option["entry_parameter"]["parameter"]:
            str_host_name = option["entry_parameter"]["parameter"]["host_name"]
        else:
            str_host_name = None

        # 認証方式の設定値取得
        if "authentication_method" in option["entry_parameter"]["parameter"]:
            str_auth_mode = option["entry_parameter"]["parameter"]["authentication_method"]
        else:
            str_auth_mode = None

        # ユーザーIDの設定値取得
        if "login_user" in option["entry_parameter"]["parameter"]:
            str_login_user = option["entry_parameter"]["parameter"]["login_user"]
        else:
            str_login_user = None

        # パスワードの設定値取得
        if "login_password" in option["entry_parameter"]["parameter"]:
            str_passwd = option["entry_parameter"]["parameter"]["login_password"]
        else:
            str_passwd = None

        # パスフレーズの設定値取得
        if "passphrase" in option["entry_parameter"]["parameter"]:
            str_passphrase = option["entry_parameter"]["parameter"]["passphrase"]
        else:
            str_passphrase = None

        # 公開鍵ファイルの設定値取得
        if "ssh_private_key_file" in option["entry_parameter"]["parameter"]:
            str_ssh_key_file = option["entry_parameter"]["parameter"]["ssh_private_key_file"]
        else:
            str_ssh_key_file = None

        # インベントリファイル追加オプション取得
        if "inventory_file_additional_option" in option["entry_parameter"]["parameter"]:
            in_string = option["entry_parameter"]["parameter"]["inventory_file_additional_option"]
        else:
            in_string = ""

        # Pioneerプロトコルの設定値取得
        # if "protocol" in option["entry_parameter"]["parameter"]:
        #     str_protocol_id = option["entry_parameter"]["parameter"]["protocol"]
        # else:
        #     str_protocol_id = ""

    elif option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        # ホスト名
        str_host_name = option["current_parameter"]["parameter"]["host_name"]

        # 認証方式の設定値取得
        str_auth_mode = option["current_parameter"]["parameter"]["authentication_method"]

        # ユーザーIDの設定値取得
        str_login_user = option["current_parameter"]["parameter"]["host_name"]

        # パスワードの設定値取得
        str_passwd = option["current_parameter"]["parameter"]["login_password"]

        # パスフレーズの設定値取得
        str_passphrase = option["current_parameter"]["parameter"]["passphrase"]

        # 公開鍵ファイルの設定値取得
        str_ssh_key_file = option["current_parameter"]["parameter"]["ssh_private_key_file"]

        # インベントリファイル追加オプション取得
        in_string = option["current_parameter"]["parameter"]["inventory_file_additional_option"]
        if not in_string:
            in_string = ""
        # Pioneerプロトコルの設定値取得
        # str_protocol_id = option["current_parameter"]["parameter"]["protocol"]

    elif option["cmd_type"] == "Update":
        # ホスト名
        if "host_name" in option["entry_parameter"]["parameter"]:
            str_host_name = option["entry_parameter"]["parameter"]["host_name"]
        else:
            str_host_name = None

        # 認証方式の設定値取得
        if "authentication_method" in option["entry_parameter"]["parameter"]:
            str_auth_mode = option["entry_parameter"]["parameter"]["authentication_method"]
        else:
            str_auth_mode = None

        # ユーザーIDの設定値取得
        if "login_user" in option["entry_parameter"]["parameter"]:
            str_login_user = option["entry_parameter"]["parameter"]["login_user"]
        else:
            str_login_user = None

        if "inventory_file_additional_option" in option["entry_parameter"]["parameter"]:
            in_string = option["entry_parameter"]["parameter"]["inventory_file_additional_option"]
        else:
            in_string = ""

        # パスワードの設定値取得
        str_passwd = getSpecialColumnVaule("login_password", option)

        # パスフレーズの設定値取得
        str_passphrase = getSpecialColumnVaule("passphrase", option)

        # 公開鍵ファイルの設定値取得
        str_ssh_key_file = getSpecialColumnVaule("ssh_private_key_file", option)

        # Pioneerプロトコルの設定値取得
        # str_protocol_id = option["current_parameter"]["parameter"]["protocol"]

    if option["cmd_type"] == "Register" or option["cmd_type"] == "Update" or option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        # 選択されている認証方式に応じた必須入力をチェック
        # 但し、パスワード管理・パスワードは既存のチェック処理で必須入力判定
        err_msg_parameter_ary = []
        driver_id = ""
        chkobj = AuthTypeParameterRequiredCheck()
        ret_str_body = chkobj.DeviceListAuthTypeRequiredParameterCheck(AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList, err_msg_parameter_ary, str_auth_mode, str_login_user, str_passwd, str_ssh_key_file, str_passphrase, driver_id)   # str_protocol_idを後で引数に追加

    if ret_str_body[0] is True:
        msg = ""
    else:
        retBool = False
        msg = ret_str_body[1]

    # ホスト名が数値文字列か判定
    if str_host_name:
        if str_host_name.isdecimal():
            retBool = False
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message("MSG-10879")

    if in_string is None:
        in_string = ""

    try:
        # YAMLcheck処理
        tmpFile = "{}/InventryFileAddOptionYamlParse_{}".format(get_OSTmpPath(), os.getpid())
        # /tmpに作成したファイルはゴミ掃除リストに追加
        addAnsibleCreateFilesPath(tmpFile)
        with open(tmpFile, "w") as fd:
            fd.write(in_string)
        obj = YamlParse()
        ret = obj.Parse(tmpFile)
        os.remove(tmpFile)
        if ret is False:
            retBool = False
            if len(msg) != 0:
                msg += "\n"
            error_detail = obj.GetLastError()
            msg += g.appmsg.get_api_message("MSG-10887", [error_detail])
        return retBool, msg, option
    except AppException as e:
        raise AppException(e)
    except Exception as e:
        raise Exception(e)
    finally:
        # /tmpをゴミ掃除
        rmAnsibleCreateFiles()
