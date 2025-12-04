# Copyright 2025 NEC Corporation#
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
import json
# oase
from common_libs.oase.const import oaseConst

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
    msg = []
    cmd_type = option.get("cmd_type")

    # 削除時はチェックしない
    # Do not check when deleting
    if cmd_type == "Delete":
        return retBool, msg, option

    # 廃止の場合、バリデーションチェックを行わない。
    if cmd_type == "Discard":
        return retBool, msg, option,

    current_parameter = option.get("current_parameter", {}).get("parameter")
    entry_parameter = option.get("entry_parameter", {}).get("parameter")

    # 「登録」「更新」の場合、entry_parameterから各値を取得
    if cmd_type == "Register" or cmd_type == "Update":
        try:
            event_source_redundancy_group = json.loads(entry_parameter.get("event_source_redundancy_group")).get("id", {})
        except:
            event_source_redundancy_group = []

        condition_labels = json.loads(entry_parameter.get("condition_labels", {})).get("id", {}) if entry_parameter.get("condition_labels") else {}
        condition_expression = entry_parameter.get("condition_expression")
    # 「復活」の場合、currrent_parameterから各値を取得
    elif cmd_type == "Restore":
        try:
            event_source_redundancy_group = json.loads(current_parameter.get("event_source_redundancy_group")).get("id", {})
        except:
            event_source_redundancy_group = []
        condition_labels = json.loads(current_parameter.get("condition_labels", {})).get("id", {}) if current_parameter.get("condition_labels") else {}
        condition_expression = current_parameter.get("condition_expression")
    else:
        return retBool, msg, option

    # 条件のラベルと式は必ずどちらも入力する or どちらも入力しない
    check_link_flag = False
    if condition_labels and condition_expression:
        check_link_flag = True
    elif not condition_labels and not condition_expression:
        pass
    else:
        msg.append(g.appmsg.get_api_message("MSG-160001"))

    if check_link_flag:
        # 条件式が「一致する」の場合
        if condition_expression == "1":
            # ラベル付与設定から、冗長グループの設定それぞれに紐づいているラベルを検索
            link_check_dict = {}  # {イベント収集設定ID: [ラベルキーID...]}の形式で設定
            for event_source in event_source_redundancy_group:
                link_check_dict[event_source] = []
                labeling_settings = objdbca.table_select(
                    "T_OASE_LABELING_SETTINGS",
                    "WHERE EVENT_COLLECTION_SETTINGS_ID = %s AND DISUSE_FLAG='0'",
                    [event_source]
                )
                for record in labeling_settings:
                    link_check_dict[event_source].append(record["LABEL_KEY_ID"])

            for event_collection_settings_id, label_key_ids in link_check_dict.items():
                # メッセージ用にイベント収集設定名を取得
                event_collection_settings_name = get_event_collection_settings_name_by_id(objdbca, event_collection_settings_id)

                # イベント収集設定それぞれにすべての条件ラベルが紐付いているか確認
                for condition_label in condition_labels:
                    if condition_label not in label_key_ids:
                        # メッセージ用にラベルキーの値を取得
                        condition_label_key_name = get_label_key_by_id(objdbca, condition_label)
                        msg.append(g.appmsg.get_api_message("MSG-160002", [event_collection_settings_name, condition_label_key_name]))

        # 条件式が「無視する」の場合
        elif condition_expression == "2":
            # ラベル付与設定から、冗長グループの設定それぞれに紐づいているラベルを検索
            link_check_list = []  # ラベルキーIDをすべてリストに格納
            for event_source in event_source_redundancy_group:
                labeling_settings = objdbca.table_select(
                    "T_OASE_LABELING_SETTINGS",
                    "WHERE EVENT_COLLECTION_SETTINGS_ID = %s AND DISUSE_FLAG='0'",
                    [event_source]
                )
                for item in labeling_settings:
                    link_check_list.append(item["LABEL_KEY_ID"])

            # イベント収集設定のいずれかにすべての条件ラベルが紐付いているか確認
            for condition_label in condition_labels:
                if condition_label not in link_check_list:
                    condition_label_key_name = get_label_key_by_id(objdbca, condition_label)
                    msg.append(g.appmsg.get_api_message("MSG-160003", [condition_label_key_name]))

        else:
            msg.append(g.appmsg.get_api_message("MSG-00032", [condition_expression]))

    if len(msg) > 0:
        retBool = False

    return retBool, msg, option


def get_label_key_by_id(objdbca, id):
    label_key_input = objdbca.table_select(
        oaseConst.V_OASE_LABEL_KEY_GROUP,
        "WHERE LABEL_KEY_ID = %s AND DISUSE_FLAG = '0'",
        [id]
    )
    label_key_name = label_key_input[0]["LABEL_KEY_NAME"]
    return label_key_name


def get_event_collection_settings_name_by_id(objdbca, id):
    event_collection_setting = objdbca.table_select(
        oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS,
        "WHERE EVENT_COLLECTION_SETTINGS_ID = %s AND DISUSE_FLAG='0'",
        [id]
    )
    event_collection_settings_name = event_collection_setting[0]["EVENT_COLLECTION_SETTINGS_NAME"]
    return event_collection_settings_name
