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
#

def agent_setting_valid(objdbca, objtable, option):

    retBool = True
    msg = []
    cmd_type = option.get("cmd_type")
    entry_parameter = option.get('entry_parameter').get('parameter')

    if cmd_type == "Restore":
        entry_parameter = option.get("current_parameter").get("parameter")

    if cmd_type in ["Register", "Update", "Restore"]:

        connection_method = entry_parameter['connection_method']
        request_method = entry_parameter['request_method']
        password = entry_parameter.get("password")

        # パスワードに入力があるかチェック
        password_entered = False
        if password:
            password_entered = True

        # 接続方式がIMAPパスワードの場合
        if connection_method == "4":
            if request_method not in ["3", "4", "5"]:
                msg.append("Request method must be IMAP method if Connection method is IMAP Auth.")
            if entry_parameter['username'] is None:
                msg.append("Username is required if Connection method is IMAP Password Auth.")
            if password_entered is False and cmd_type == "Register":
                msg.append("Password is required if Connection method is IMAP Password Auth.")
            # レスポンスリストフラグをTrueに自動設定
            entry_parameter["response_list_flag"] = "1"

        # msg に値がある場合は個別バリデエラー
        if len(msg) >= 1:
            retBool = False

    return retBool, msg, option,
