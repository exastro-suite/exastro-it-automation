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

from flask import g


def agent_setting_valid(objdbca, objtable, option):

    retBool = True
    msg = []
    cmd_type = option.get("cmd_type")
    entry_parameter = option.get('entry_parameter').get('parameter')

    if cmd_type in ["Register", "Update"]:

        connection_method = entry_parameter['connection_method_name']
        request_method = entry_parameter['request_method_name']
        password = entry_parameter.get("password")

        # パスワードカラムの入力があるかチェック
        password_entered = False
        if password:
            password_entered = True

        # 接続方式がIMAPパスワードの場合
        if connection_method == "4":
            if request_method not in ["3", "4", "5"]:
                msg.append(g.appmsg.get_api_message("MSG-120001"))
            if entry_parameter['username'] is None:
                msg.append(g.appmsg.get_api_message("MSG-120002"))
            if password_entered is False and cmd_type == "Register":
                msg.append(g.appmsg.get_api_message("MSG-120003"))
            # レスポンスリストフラグをTrueに自動設定
            entry_parameter["response_list_flag"] = "1"

        # 編集時に対象レコードの接続方式が変更され、パスワードカラムに入力が無い場合、値をnullに設定
        if cmd_type == "Update":
            setting_id = entry_parameter["event_collection_settings_id"]
            record = objdbca.table_select(
                "T_OASE_EVENT_COLLECTION_SETTINGS",
                "WHERE EVENT_COLLECTION_SETTINGS_ID=%s",
                [setting_id]
            )
            if connection_method != record[0]["CONNECTION_METHOD_ID"]:
                if password_entered is False:
                    entry_parameter["password"] = None

        # msg に値がある場合は個別バリデエラー
        if len(msg) >= 1:
            retBool = False

    return retBool, msg, option,
