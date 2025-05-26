#   Copyright 2025 NEC Corporation
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

from common_libs.ansible_driver.functions.util import gbl_variable_unique_check


def external_valid_menu_before(objdbca, objtable, option):
    """
    メニューバリデーション
        - グローバル変数の一意制約
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

    # entry_parameterはUI入力ベースの情報
    # current_parameterはDBに登録済みの情報
    global_variable_name = None
    if option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        global_variable_name =  option["entry_parameter"]["parameter"]["global_variable_name"]\
            if "global_variable_name" in option["entry_parameter"]["parameter"] else None
    elif option["cmd_type"] == "Restore":
        global_variable_name =  option["current_parameter"]["parameter"]["global_variable_name"]\
            if "global_variable_name" in option["current_parameter"]["parameter"] else None

    if global_variable_name:
        # グローバル変数の一意制約
        retBool, msg = gbl_variable_unique_check(objdbca, global_variable_name, menu_id="20104")

    return retBool, msg, option,