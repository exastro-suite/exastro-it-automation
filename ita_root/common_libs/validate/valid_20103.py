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

from flask import g

from common_libs.ansible_driver.classes.menu_required_check import AuthTypeParameterRequiredCheck

# ITAのメッセージの引き取り
def external_valid_menu_before(objdbca, objtable, option):
    """
    メニューバリデーション(登録/更新)
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
    msg = ''
    ret_str_body = ''
    # entry_parameterはUI入力ベースの情報
    # current_parameterはDBに登録済みの情報
    # 登録処理の場合
    if option["cmd_type"] == "Register":
        # host名取得
        if "host" in option["entry_parameter"]["parameter"]:
            host_name = option["entry_parameter"]["parameter"]["host"]
        else:
            host_name = None
        # 認証方式の設定値取得
        if "authentication_method" in option["entry_parameter"]["parameter"]:
            str_auth_mode = option["entry_parameter"]["parameter"]["authentication_method"]
        else:
            str_auth_mode = None
        # パスワードの設定値取得
        if "password" in option["entry_parameter"]["parameter"]:
            str_passwd = option["entry_parameter"]["parameter"]["password"]
        else:
            str_passwd = None
        # パスフレーズの設定値取得passphrase
        if "passphrase" in option["entry_parameter"]["parameter"]:
            str_passphrase = option["entry_parameter"]["parameter"]["passphrase"]
        else:
            str_passphrase = None
        # 公開鍵ファイルの設定値取得
        if "ssh_private_key_file" in option["entry_parameter"]["parameter"]:
            str_ssh_key_file = option["entry_parameter"]["parameter"]["ssh_private_key_file"]
        else:
            str_ssh_key_file = None
    elif option["cmd_type"] == "Update":
        # host名取得
        if "host" in option["entry_parameter"]["parameter"]:
            host_name = option["entry_parameter"]["parameter"]["host"]
        else:
            host_name = None
        # 認証方式の設定値取得
        if "authentication_method" in option["entry_parameter"]["parameter"]:
            str_auth_mode = option["entry_parameter"]["parameter"]["authentication_method"]
        else:
            str_auth_mode = None
        # パスワードの設定値取得
        # PasswordColumnはデータの更新がないとoption["entry_parameter"]["parameter"]["password"]の設定は空になっているので
        # パスワードが更新されているか判定
        # 更新されていない場合は設定済みのパスワード(["current_parameter"]["parameter"]["password"])取得
        if "password" in option["entry_parameter"]["parameter"]:
            str_passwd = option["entry_parameter"]["parameter"]["password"]
        else:
            str_passwd = None
            
        if str_passwd is None:
            str_passwd = option["current_parameter"]["parameter"]["password"]
        # パスフレーズの設定値取得
        # PasswordColumnはデータの更新がないとoption["entry_parameter"]["parameter"]["passphrase"]の設定は空になっているので
        # パスフレーズが更新されているか判定
        # 更新されていない場合は設定済みのパスフレーズ(option["current_parameter"]["parameter"]["passphrase"])取得
        if "passphrase" in option["entry_parameter"]["parameter"]:
            str_passphrase = option["entry_parameter"]["parameter"]["passphrase"]
        else:
            str_passphrase = None
        
        if str_passphrase is None:
            str_passphrase = option["current_parameter"]["parameter"]["passphrase"]
        # 公開鍵ファイルの設定値取得
        # FileUploadColumnはファイルの更新がないと$arrayRegDataの設定は空になっているので
        # ダウンロード済みのファイルが削除されていると$arrayRegData['del_flag_COL_IDSOP_xx']がonになる
        # 更新されていない場合は設定済みのファイル名($arrayVariant['edit_target_row'])を取得
        if "ssh_private_key_file" in option["entry_parameter"]["parameter"]:
            str_ssh_key_file = option["entry_parameter"]["parameter"]["ssh_private_key_file"]
        else:
            str_ssh_key_file = None

        if str_ssh_key_file is None:
            str_ssh_key_file = option["current_parameter"]["parameter"]["ssh_private_key_file"]
    elif option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        host_name = option["current_parameter"]["parameter"]["host"]

    if option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        err_msg_parameter_ary = []
        chkobj = AuthTypeParameterRequiredCheck()

        ret_str_body = chkobj.TowerHostListAuthTypeRequiredParameterCheck(AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList, err_msg_parameter_ary, str_auth_mode, str_passwd, str_ssh_key_file, str_passphrase)
        
        if ret_str_body[0] is True:
            msg = ""
        else:
            retBool, msg = False, ret_str_body[1]
    # ホスト名が数値文字列か判定
    if host_name:
        if host_name.isdecimal():
            retBool = False
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message("MSG-10879")
    return retBool, msg, option,