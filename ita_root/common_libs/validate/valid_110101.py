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
import json


def agent_setting_valid(objdbca, objtable, option):

    AUTHORIZATION_HEADER = "authorization:"
    retBool = True
    msg = []

    # 削除時はチェックしない
    # Do not check when deleting
    if option.get("cmd_type") == "Delete":
        return retBool, msg, option

    cmd_type = option.get("cmd_type")
    entry_parameter = option.get('entry_parameter').get('parameter')
    LANG = g.LANGUAGE.upper()

    if cmd_type in ["Register", "Update"]:

        connection_method = entry_parameter['connection_method_name']
        access_point = entry_parameter['url']
        request_method = entry_parameter['request_method_name']
        password = entry_parameter.get("password")
        auth_token = entry_parameter.get("auth_token")
        secret_access_key = entry_parameter.get("secret_access_key")

        # 接続方式名取得
        connection_method_name = get_connection_method_name(objdbca, connection_method, LANG)

        # パスワードカラムの入力があるかチェック
        password_entered = False
        if password:
            password_entered = True

        auth_token_entered = False
        if auth_token:
            auth_token_entered = True

        secret_access_key_entered = False
        if secret_access_key:
            secret_access_key_entered = True

        # 接続方式がエージェント不使用以外の場合
        if connection_method != "99":
            if access_point is None:
                msg.append(g.appmsg.get_api_message("MSG-120013", [connection_method_name]))

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

        # 接続方式がBearer認証の場合
        elif connection_method == "1":
            if request_method not in ["1", "2"]:
                msg.append(g.appmsg.get_api_message("MSG-120004", [connection_method_name]))
            if auth_token_entered is False and cmd_type == "Register":
                msg.append(g.appmsg.get_api_message("MSG-120005", [connection_method_name]))
            if entry_parameter['request_header'] is not None and \
               entry_parameter['request_header'].lower().find(AUTHORIZATION_HEADER) > -1:
                msg.append(g.appmsg.get_api_message("MSG-120006", [connection_method_name]))

        # 接続方式がBasic認証の場合
        elif connection_method == "2":
            if request_method not in ["1", "2"]:
                msg.append(g.appmsg.get_api_message("MSG-120004", [connection_method_name]))
            if entry_parameter['username'] is None:
                msg.append(g.appmsg.get_api_message("MSG-120007", [connection_method_name]))
            if password_entered is False and cmd_type == "Register":
                msg.append(g.appmsg.get_api_message("MSG-120008", [connection_method_name]))
            if entry_parameter['request_header'] is not None and \
               entry_parameter['request_header'].lower().find(AUTHORIZATION_HEADER) > -1:
                msg.append(g.appmsg.get_api_message("MSG-120006", [connection_method_name]))

        # 接続方式が、共有鍵認証の場合
        elif connection_method == "3":
            if request_method not in ["1", "2"]:
                msg.append(g.appmsg.get_api_message("MSG-120004", [connection_method_name]))
            if entry_parameter['access_key_id'] is None:
                msg.append(g.appmsg.get_api_message("MSG-120009", [connection_method_name]))
            if secret_access_key_entered is False and cmd_type == "Register":
                msg.append(g.appmsg.get_api_message("MSG-120010", [connection_method_name]))
            if entry_parameter['request_header'] is not None and \
               entry_parameter['request_header'].lower().find(AUTHORIZATION_HEADER) > -1:
                msg.append(g.appmsg.get_api_message("MSG-120006", [connection_method_name]))

        # 接続方式がオプション認証の場合
        elif connection_method == "5":
            if request_method not in ["1", "2"]:
                msg.append(g.appmsg.get_api_message("MSG-120004", [connection_method_name]))

        # JSON形式チェック
        if connection_method in ["1", "2", "3", "5"]:
            # リクエストヘッダー
            if entry_parameter['request_header'] is not None:
                if not isJsonFormat(entry_parameter['request_header']):
                    msg.append(g.appmsg.get_api_message("MSG-120011", [connection_method_name]))
            # パラメーター
            if entry_parameter['parameter'] is not None:
                if not isJsonFormat(entry_parameter['parameter']):
                    msg.append(g.appmsg.get_api_message("MSG-120012", [connection_method_name]))

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


def get_connection_method_name(objdbca, connection_method_id, lang):
    # 接続方式マスタ
    target_type_table = "T_OASE_CONNECTION_METHOD"
    record = objdbca.table_select(
        target_type_table,
        "WHERE DISUSE_FLAG=0 AND CONNECTION_METHOD_ID=%s",
        [connection_method_id]
    )
    if record:
        # 言語に合わせた、接続方式名を返却
        return record[0][f"CONNECTION_METHOD_NAME_{lang}"]
    else:
        return ""


def isJsonFormat(line):
    try:
        json.loads(line)
    except json.JSONDecodeError:
        return False

    except ValueError:
        return False

    except Exception:
        return False
    return True
