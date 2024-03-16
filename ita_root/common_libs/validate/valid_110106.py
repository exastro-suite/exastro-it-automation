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
import re

def labeling_setting_valid(objdbca, objtable, option):  # noqa C901

    retBool = True
    msg = []
    cmd_type = option.get("cmd_type") # noqa F841
    entry_parameter = option.get('entry_parameter').get('parameter')
    LANG = g.LANGUAGE.upper()

    # 廃止の場合、バリデーションチェックを行わない。
    if cmd_type == 'Discard':
        return retBool, msg, option,

    if cmd_type in ["Register", "Update"]:
        # 必要なキーの存在チェック
        required_keys = [
            "search_key_name",
            "type_name",
            "comparison_method",
            "search_value_name",
            "label_value_name"
        ]
        missing_keys = []
        for key in required_keys:
            if key not in entry_parameter:
                missing_keys.append(key)
        if len(missing_keys) > 0:
            if len(missing_keys) == 1:
                missing_str = f"Required key '{missing_keys[0]}' is"
            else:
                missing_str = f"Required keys {str(missing_keys)} are"

            msg.append(f"{missing_str} missing.")

        # msg に値がある場合は個別バリデエラー
        if len(msg) >= 1:
            retBool = False
            return retBool, msg, option,

        setting_name = entry_parameter["labeling_settings_name"]
        search_key = entry_parameter["search_key_name"]
        target_type = entry_parameter["type_name"]
        comparison_method = entry_parameter["comparison_method"]
        search_value = entry_parameter["search_value_name"]
        label_value = entry_parameter["label_value_name"]

        # ターゲットキーがブランクの場合
        if search_key is None:
            if target_type or comparison_method or search_value:
                msg.append(g.appmsg.get_api_message("MSG-130001", [setting_name]))
            if label_value is None:
                msg.append(g.appmsg.get_api_message("MSG-130002", [setting_name]))
            # msg に値がある場合は個別バリデエラー
            if len(msg) >= 1:
                retBool = False
                return retBool, msg, option,

        if target_type in ["4", "5", "6", "7"]:
            if comparison_method not in ["1", "2"]:
                type = get_target_type(objdbca, target_type, LANG)
                msg.append(g.appmsg.get_api_message("MSG-130003", [setting_name, type]))
        else:
            pass

        # ターゲットタイプがfalsyの場合
        if target_type == "7":
            if search_value:
                msg.append(g.appmsg.get_api_message("MSG-130004", [setting_name]))

        # ターゲットタイプが整数の場合
        if target_type == "2":
            try:
                int(search_value)
            except Exception:
                msg.append(g.appmsg.get_api_message("MSG-130005", [setting_name]))

        # ターゲットタイプが小数の場合
        if target_type == "3":
            try:
                float(search_value)
            except Exception:
                msg.append(g.appmsg.get_api_message("MSG-130006", [setting_name]))

        # ターゲットタイプが真偽値の時
        if target_type == "4":
            try:
                if search_value.lower() not in ["true", "false"]:
                    raise
            except Exception:
                msg.append(g.appmsg.get_api_message("MSG-130007", [setting_name]))

        # ターゲットタイプがオブジェクト・配列の場合
        if target_type in ["5", "6"]:
            # ターゲットタイプがオブジェクトの場合
            try:
                if target_type == "5":
                    if (search_value.startswith("{") and search_value.endswith("}")) is False:
                        raise
                if target_type == "6":
                    if (search_value.startswith("[") and search_value.endswith("]")) is False:
                        raise
                json.loads(search_value)
            except Exception:
                msg.append(g.appmsg.get_api_message("MSG-130008", [setting_name]))

        # ターゲットタイプがその他の時、比較方法は正規表現のみ
        if target_type == "10":
            if comparison_method not in ["7", "8", "9"]:
                msg.append(g.appmsg.get_api_message("MSG-130009", [setting_name]))
            if search_value is None:
                msg.append(g.appmsg.get_api_message("MSG-130010", [setting_name]))

        # 比較方法が==もしくは≠の場合
        if comparison_method in ["1", "2"]:
            method = get_comparison_method(objdbca, comparison_method)
            if target_type == "10":
                msg.append(g.appmsg.get_api_message("MSG-130011", [setting_name, method]))
            if target_type is None:
                msg.append(g.appmsg.get_api_message("MSG-130012", [setting_name, method]))

        # 比較方法が<, <=, >, >=の場合
        if comparison_method in ["3", "4", "5", "6"]:
            if target_type not in ["1", "2", "3"]:
                method = get_comparison_method(objdbca, comparison_method)
                msg.append(g.appmsg.get_api_message("MSG-130013", [setting_name, method]))

        # 比較方法が正規表現の時、ターゲットタイプはその他のみ
        if comparison_method in ["7", "8", "9"]:
            if target_type != "10":
                msg.append(g.appmsg.get_api_message("MSG-130014", [setting_name]))
            if search_value is None:
                msg.append(g.appmsg.get_api_message("MSG-130015", [setting_name]))
            # 正規表現の文法チェック
            try:
                pattern = re.compile(r'{}'.format(search_value))
            except Exception:
                msg.append(g.appmsg.get_api_message("MSG-130016", [setting_name]))

        # # ターゲットタイプ, 比較方法, ターゲットバリューのすべてがブランクの場合
        # if target_type is None and comparison_method is None and search_value is None:
        #     if label_value is None:
        #         msg.append(g.appmsg.get_api_message("MSG-130017", [setting_name]))

        # # ラベルバリューがブランクの場合
        # if label_value is None:
        #     if target_type is None or comparison_method is None:
        #         msg.append(g.appmsg.get_api_message("MSG-130018", [setting_name]))

        # ターゲットタイプがブランクの場合
        if target_type is None:
            if comparison_method or search_value:
                msg.append(g.appmsg.get_api_message("MSG-130019", [setting_name]))

        # 比較方法がブランクの場合
        if comparison_method is None:
            if target_type or search_value:
                msg.append(g.appmsg.get_api_message("MSG-130020", [setting_name]))

        # ターゲットバリューがブランクの場合
        if search_value is None:
            if target_type not in ["7", None]:
                msg.append(g.appmsg.get_api_message("MSG-130021", [setting_name]))
            if comparison_method not in ["1", "2", None]:
                msg.append(g.appmsg.get_api_message("MSG-130022", [setting_name]))

        # ターゲットタイプがfalsyかつターゲットタイプが≠の場合
        if target_type == "7" and comparison_method == "2":
            if label_value is None:
                msg.append(g.appmsg.get_api_message("MSG-130023", [setting_name]))

        # ターゲットタイプがFalsyもしくは未入力以外かつ比較方法に入力がある場合
        if target_type not in ["7", None] and comparison_method:
            if search_value is None:
                msg.append(g.appmsg.get_api_message("MSG-130024", [setting_name]))

        # msg に値がある場合は個別バリデエラー
        if len(msg) >= 1:
            retBool = False

    return retBool, msg, option,


def get_target_type(objdbca, typeid, lang):
    target_type_table = "t_oase_target_type"
    record = objdbca.table_select(
        target_type_table,
        "WHERE DISUSE_FLAG=0 AND TYPE_ID=%s",
        [typeid]
    )

    return record[0][f"TYPE_NAME_{lang}"]


def get_comparison_method(objdbca, methodid):
    comparison_method_table = "t_oase_comparison_method"
    record = objdbca.table_select(
        comparison_method_table,
        "WHERE DISUSE_FLAG=0 AND COMPARISON_METHOD_ID=%s",
        [methodid]
    )

    return record[0]["COMPARISON_METHOD_SYMBOL"]
