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

def labeling_setting_valid(objdbca, objtable, option):  # noqa C901

    retBool = True
    msg = []
    cmd_type = option.get("cmd_type") # noqa F841
    entry_parameter = option.get('entry_parameter').get('parameter')

    LANG = g.LANGUAGE.upper()

    target_key = entry_parameter["search_key_name"]
    target_type = entry_parameter["type_name"]
    comparison_method = entry_parameter["comparison_method"]
    target_value = entry_parameter["search_value_name"]
    label_value = entry_parameter["label_value_name"]

    # ターゲットキーがブランクの場合
    if target_key is None:
        if target_type or comparison_method or target_value:
            # If Target is blank, all of Target Type, Comparison Method and Target Value must also be blank.
            msg.append("If Target Key is blank, all of Target Type, Comparison Method and Target Value must also be blank.")
        if label_value is None:
            # If Target Key is blank, Label Value must have an entry.
            msg.append("If Target Key is blank, Label Value must have an entry.")
        # msg に値がある場合は個別バリデエラー
        if len(msg) >= 1:
            retBool = False
            return retBool, msg, option,

    # ターゲットタイプが文字列・数値型の場合
    if target_type in ["1", "2", "3"]:
        if comparison_method == "7":
            # Compare Method cannnot be RegExp unless Target Type is any.
            msg.append("Compare Method cannnot be RegExp unless Target Type is any.")
    # ターゲットタイプが真偽値・オブジェクト・配列・falsyの場合
    elif target_type in ["4", "5", "6", "7"]:
        if comparison_method not in ["1", "2"]:
            # If Target Type is {}, Comparison Method must be == or ≠.
            type = get_target_type(objdbca, target_type, LANG)
            msg.append("If Target Type is {}, Comparison Method must be == or ≠.".format(type))
    else:
        pass

    # ターゲットタイプがfalsyの場合
    if target_type == "7":
        if target_value:
            # If Target Type is Falsy, Target Value must be blank.
            msg.append("If Target Type is Falsy, Target Value must be blank.")

    # ターゲットタイプが整数の場合
    if target_type == "2":
        try:
            int(target_value)
        except Exception:
            # If Target Type is int, Target Value must also be int type.
            msg.append("If Target Type is int, Target Value must also be int type.")

    # ターゲットタイプが小数の場合
    if target_type == "3":
        try:
            float(target_value)
        except Exception:
            # If Target Type is float, Target Value must also be float type.
            msg.append("If Target Type is float, Target Value must also be float type.")

    # ターゲットタイプが真偽値の時
    if target_type == "4":
        try:
            if target_value.lower() not in ["true", "false"]:
                raise
        except Exception:
            # If Target Type is boolean, Target Value must be 'true' or 'false'
            msg.append("If Target Type is boolean, Target Value must be 'true' or 'false'")

    # ターゲットタイプがオブジェクト・配列の場合
    if target_type in ["5", "6"]:
        # ターゲットタイプがオブジェクトの場合
        try:
            if target_type == "5":
                if (target_value.startswith("{") and target_value.endswith("}")) is False:
                    raise
            if target_type == "6":
                if (target_value.startswith("[") and target_value.endswith("]")) is False:
                    raise
            json.loads(target_value)
        except Exception:
            # If Target Type is object or array, Target Value must match the type.
            msg.append("If Target Type is object or array, Target Value must match the type.")

    # ターゲットタイプがその他の時
    if target_type == "10":
        if comparison_method != "7":
            # If Target Type is any, Comparison Method must be RegExp
            msg.append("If Target Type is any, Comparison Method must be RegExp")
        if target_value is None:
            # If Comparison Method is RegExp, Target Value must have an entry.
            msg.append("If Comparison Method is RegExp, Target Value must have an entry.")

    # 比較方法が==もしくは≠の場合
    if comparison_method in ["1", "2"]:
        method = get_comparison_method(objdbca, comparison_method)
        if target_type == "10":
            # If Comparison Method is {}, Target Type cannot be any.
            msg.append("If Comparison Method is {}, Target Type cannot be any.".format(method))
        if target_type is None:
            # If Comparison Method is {}, Target Type cannot be blank.
            msg.append("If Comparison Method is {}, Target Type cannot be blank.".format(method))

    # 比較方法が<, <=, >, >=の場合
    if comparison_method in ["3", "4", "5", "6"]:
        if target_type not in ["1", "2", "3"]:
            # If Comparision Method is {}, Target Type must be string, int or float.
            method = get_comparison_method(objdbca, comparison_method)
            msg.append("If Comparision Method is {}, Target Type must be string, int or float.".format(method))

    # 比較方法が正規表現の時
    if comparison_method == "7":
        if target_type != "10":
            # If Comparison Method is RegExp, Target Type must be any.
            msg.append("If Comparison Method is RegExp, Target Type must be any.")
        if target_value is None:
            # If Target Type is any, Target Value must have an entry.
            msg.append("If Comparison Method RegExp, Target Value must have an entry.")

    # ターゲットタイプ, 比較方法, ターゲットバリューのすべてがブランクの場合
    if target_type is None and comparison_method is None and target_value is None:
        if label_value is None:
            # If Target Type, Comparison Method and Target Value are blank, Label Value must have an entry.
            msg.append("If Target Type, Comparison Method and Target Value are blank, Label Value must have an entry.")

    # ラベルバリューがブランクの場合
    if label_value is None:
        if target_type is None or comparison_method is None:
            # If Label Value is blank, both Target Type and Comparison Method must have entries.
            msg.append("If Label Value is blank, both Target Type and Comparison Method must have entries.")

    # ターゲットタイプがブランクの場合
    if target_type is None:
        if comparison_method or target_value:
            # If Target Type is blank, both Comparison Method and Target Value must also be blank.
            msg.append("If Target Type is blank, both Comparison Method and Target Value must also be blank.")

    # 比較方法がブランクの場合
    if comparison_method is None:
        if target_type or target_value:
            # If Comparison Method is blank, both Target Type and Target Value must also be blank.
            msg.append("If Comparison Method is blank, both Target Type and Target Value must also be blank.")

    # ターゲットバリューがブランクの場合
    if target_value is None:
        if target_type not in ["7", None]:
            # If Target Value is blank, Target Type must be Falsy or blank.
            msg.append("If Target Value is blank, Target Type must be Falsy or blank.")
        if comparison_method not in ["1", "2", None]:
            # If Target Value is blank, Comparison Method must be ==, ≠ or blank.
            msg.append("If Target Value is blank, Comparison Method must be ==, ≠ or blank.")

    # ターゲットタイプがfalsyかつターゲットタイプが≠の場合
    if target_type == "7" and comparison_method == "2":
        if label_value is None:
            # If Target Value is falsy and Comparison Method is ≠, Label Value must have an entry.
            msg.append("If Target Value is falsy and Comparison Method is ≠, Label Value must have an entry.")

    # ターゲットタイプがFalsyもしくは未入力以外かつ比較方法に入力がある場合
    if target_type not in ["7", None] and comparison_method:
        if target_value is None:
            # Target Value cannot be blank.
            msg.append("If Target Type and Comparison Method have an entries, Target Value must also have an entry. (except Comparison Method is falsy.)")

    # msg に値がある場合は個別バリデエラー
    if len(msg) >= 1:
        retBool = False

    return retBool, msg, option,


def get_target_type(objdbca, typeid, lang):
    target_type_table = "t_oase_target_type"
    print(type(typeid))
    record = objdbca.table_select(
        target_type_table,
        "WHERE DISUSE_FLAG=0 AND TYPE_ID=%s",
        [typeid]
    )

    return record[0][f"TYPE_{lang}"]


def get_comparison_method(objdbca, methodid):
    comparison_method_table = "t_oase_comparison_method"
    record = objdbca.table_select(
        comparison_method_table,
        "WHERE DISUSE_FLAG=0 AND COMPARISON_METHOD_ID=%s",
        [methodid]
    )

    return record[0]["COMPARISON_METHOD_SYMBOL"]
