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
import operator
import re
import jmespath
import json


# ラベリング設定内で比較方法として真偽値を使用　value = ラベリング設定内でのtarget_value       value.lowercase()
def returns_bool(_value):
    value = _value.lower()
    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        return None


# 取得してきたJSONデータ内target_valueの正規表現
def bool_RegExp(comparison_method_id, target_value_collection, target_value_setting):

    # ラベリング設定内比較方法が ≠ の場合
    if comparison_method_id == "2":
        # ラベリング設定内で "True" 指定の場合
        if target_value_setting == "True":
            # 取得してきたJSONデータ内target_valueと"False"を正規表現で比較
            bool_check = str(re.search(target_value_collection, "False", flags=re.IGNORECASE))
            # 取得してきたJSONデータとラベリング設定内target_valueが一致しないことを確認
            if bool_check != "<re.Match object; span=(0, 4), match='True'>":
                # 取得してきたJSONデータとラベリング設定内target_valueの対義語("False")が一致することを確認
                if bool_check == "<re.Match object; span=(0, 5), match='False'>":
                    result = "unmatch"
                    return result
                else:
                    return None
            else:
                return None
        # ラベリング設定内で "False" 指定の場合
        elif target_value_setting == "False":
            # 取得してきたJSONデータ内target_valueと"True"を正規表現で比較
            bool_check = str(re.search(target_value_collection, "True", flags=re.IGNORECASE))
            # 取得してきたJSONデータとラベリング設定内target_valueが一致しないことを確認
            if bool_check != "<re.Match object; span=(0, 5), match='False'>":
                # 取得してきたJSONデータとラベリング設定内target_valueの対義語("True")が一致することを確認
                if bool_check == "<re.Match object; span=(0, 4), match='True'>":
                    result = "unmatch"
                    return result
                else:
                    return None
        else:
            return None
    # ラベリング設定内比較方法が ≠ 以外の場合
    else:
        bool_check = str(re.search(target_value_collection, target_value_setting, flags=re.IGNORECASE))

        # ラベリング設定内target_valueが"True"の場合、取得してきたJSONデータとラベリング設定内target_valueが一致することを確認
        if bool_check == "<re.Match object; span=(0, 4), match='True'>":
            result = "match"
            return result
        # ラベリング設定内target_valueが"False"の場合、取得してきたJSONデータとラベリング設定内target_valueが一致することを確認
        elif bool_check == "<re.Match object; span=(0, 5), match='False'>":
            result = "match"
            return result
        else:
            return None


# ラベリング設定内target_valueを取得してきたイベントのタイプに合わせて比較するためのマスタ
target_value_type = {
    "1": str,  # string
    "2": int,  # integer
    "3": float,  # float
    "4": returns_bool,  # bool
    "5": json.loads,  # dict
    "6": json.loads,  # list
    "7": lambda X: X,  # falsey
    "10": lambda X: X  # any
}


# 収取してきたイベントのtarget_valueとラベリング設定内target_valueを比較
def comparison_values(comparison_method_id="1", comparative=None, referent=None):

    comparison_operator = {
        "1": operator.eq,  # ==
        "2": operator.ne,  # ≠
        "3": operator.lt,  # <
        "4": operator.le,  # <=
        "5": operator.gt,  # >
        "6": operator.ge,  # >=
        "7": "Regular expression"
    }

    # 上記comparison_operatorをリストとして取得
    key_list = list(comparison_operator.keys())

    # リストの中にcomparison_method_idが存在するか確認
    if comparison_method_id in key_list:

        # 正規表現処理
        if comparison_method_id == "7":
            regex_pattern = re.compile(referent)
            result = regex_pattern.search(comparative)
        elif comparison_method_id == "2":
            comparison = comparison_operator[comparison_method_id]
            result_unmatch = comparison(comparative, referent)
            if result_unmatch is True:
                if comparative is True:
                    result = True
                elif comparative is False:
                    result = True
                else:
                    result = None

        else:
            comparison = comparison_operator[comparison_method_id]
            result = comparison(comparative, referent)

    else:
        result = None
    return result


# ドット区切りの文字列で辞書を指定して値を取得
def get_value_from_jsonpath(jsonpath, data):
    value = jmespath.search(jsonpath, data)
    return value


# ラベリング処理
def label(wsDb, event_collection_data, setting):
    label_key_record = wsDb.table_select(
        "T_EVRL_LABEL_KEY_INPUT",
        "WHERE DISUSE_FLAG=0 AND LABEL_KEY_ID=%s",
        [setting["LABEL_KEY_ID"]]
    )

    # label_key_record = wsDb.table_select(
    #     "V_EVRL_LABEL_KEY_GROUP",
    #     "WHERE DISUSE_FLAG=0 AND LABEL_KEY_ID=%s",
    #     [setting["LABEL_KEY_ID"]]
    # )

    label_key_id = label_key_record[0]["LABEL_KEY_ID"]
    label_key_string = label_key_record[0]["LABEL_KEY"]

    event_collection_data["labels"][label_key_string] = setting["LABEL_VALUE"]
    event_collection_data["exastro_labeling_settings"][label_key_string] = setting["LABELING_SETTINGS_ID"]
    event_collection_data["exastro_label_key_input_ids"][label_key_string] = label_key_id
    return event_collection_data


# ラベリング次第保存処理
def label_event(wsDb, wsMongo, events):  # noqa: C901

    label_result = False
    debug_msg = ""

    labeling_settings = wsDb.table_select(
        "T_EVRL_LABELING_SETTINGS",
        "WHERE DISUSE_FLAG=%s",
        ["0"]
    )

    if labeling_settings is None:
        msg = "ラベリング設定テーブルが取得できませんでした。"
        print(msg)
        # msg = g.appmsg.get_api_message("MSG-80001", [tf_organization_name])
        return labeling_settings

    # そのままのデータを保存するためのコレクション
    event_collection = wsMongo.collection("event_collection")

    # ラベリングしたデータを保存するためのコレクション
    labeled_event_collection = wsMongo.collection("labeled_event_collection")

    # そのままのデータをMongoDBに保存
    try:
        event_collection.insert_many(events)
    except Exception as e:
        debug_msg = "failed to insert events"
        print(debug_msg)
        print(e)
        return label_result

    labeled_events = []

    if events is None:
        msg = "eventsデータが取得できませんでした。"
        print(msg)
        return label_result

    # 取得してきたJSONデータをイベント単位で分割
    for single_event in events:

        # data
        if single_event is None:
            msg = "イベント単位に分割が失敗しました。"
            print(msg)
            # msg = g.appmsg.get_api_message("MSG-80001", [tf_organization_name])
            return labeling_settings

        labeled_event = {}
        original_event = single_event
        labeled_event["event"] = original_event

        # exastro用ラベルを貼る
        exastro_labels = {
            "_exastro_event_collection_settings_id": single_event["_exastro_event_collection_settings_id"],
            "_exastro_fetched_time": single_event["_exastro_fetched_time"],
            "_exastro_end_time": single_event["_exastro_end_time"],
            "_exastro_type": "event",
            "_exastro_evaluated": "0",
            "_exastro_undetected": "0",
            "_exastro_timeout": "0"
        }
        # 重複して不要なexastro用ラベルを削除
        labeled_event["labels"] = exastro_labels
        del labeled_event["event"]["_exastro_event_collection_settings_id"]
        del labeled_event["event"]["_exastro_fetched_time"]
        del labeled_event["event"]["_exastro_end_time"]
        labeled_events.append(labeled_event)

    if labeled_events is None:
        msg = "Exastroラベリングされたイベントを取得失敗しました。"
        print(msg)
        # msg = g.appmsg.get_api_message("MSG-80001", [tf_organization_name])
        return labeling_settings

    # exastro用ラベルを貼った後のデータをイベント単位で再分割
    for event_collection_data in labeled_events:

        if event_collection_data is None:
            msg = "イベント単位の分割が失敗しました。"
            print(msg)
            return labeling_settings
            # msg = g.appmsg.get_api_message("MSG-80001", [tf_organization_name])

        event_collection_data["exastro_labeling_settings"] = {}
        event_collection_data["exastro_label_key_input_ids"] = {}

        # ラベリング設定に該当するデータにはラベルを貼る
        for setting in labeling_settings:

            if event_collection_data is None:
                msg = "ラベリング設定の分割が失敗しました。"
                print(msg)
                # msg = g.appmsg.get_api_message("MSG-80001", [tf_organization_name])
                return label_result

            try:
                # 収集した_exastro_event_collection_settings_idとイベント収集設定IDが一致しないものはスキップ
                if event_collection_data["labels"]["_exastro_event_collection_settings_id"] != setting["EVENT_COLLECTION_SETTINGS_ID"]:
                    continue

                if (setting["TARGET_KEY"] in event_collection_data["event"]):
                    event_inside_key = "event"
                elif (setting["TARGET_KEY"] in event_collection_data["labels"]):
                    event_inside_key = "labels"

                # ラベリング設定内にtarget_keyが存在するか確認(パターンC用)
                if setting["TARGET_KEY"] is None:
                    # ラベリング設定内target_typeが"その他"、かつ取得してきたイベント内"event"のvalueがラベリング設定内target_keyの中に存在しない場合
                    if setting["TARGET_TYPE_ID"] != "7" or get_value_from_jsonpath(setting["TARGET_KEY"], event_collection_data[event_inside_key]) is not False:  # noqa: E501
                        event = label(wsDb, event_collection_data, setting)

                # ラベリング設定内にtarget_keyが存在する、かつ取得してきたJSONデータ内にラベリング設定内で指定したtarget_keyが存在するか確認（パターンA,B,D,E用）
                elif setting["TARGET_KEY"] and setting["TARGET_KEY"] in event_collection_data[event_inside_key]:

                    # ラベリング設定内target_keyが取得してきたイベント,inside_keyの中に存在するか確認(パターンA,B,D,E用)
                    if (setting["TARGET_KEY"] in event_collection_data[event_inside_key]):

                        # ラベリング設定内target_typeが"その他"以外、かつラベリング設定内にtarget_type_id、Target_valueのどちらも存在していない場合(パターンD用)
                        if ((setting["TARGET_TYPE_ID"] and setting["TARGET_VALUE"]) is None) and setting["TARGET_TYPE_ID"] != "7":

                            query = create_jmespath_query(setting["TARGET_KEY"])
                            # queryが取得してきたイベント,inside_keyの中に存在する場合
                            if get_value_from_jsonpath(query, event_collection_data[event_inside_key]):
                                event = label(wsDb, event_collection_data, setting)

                        # パターンA,B,D
                        else:
                            # 取得してきたイベント,event_inside_key内にラベリング設定内target_keyが一致するものを取得
                            target_value_collection = get_value_from_jsonpath(setting["TARGET_KEY"], event_collection_data[event_inside_key])

                            # target_keyに対応する値が取得できたか確認
                            if target_value_collection is None:
                                continue

                            else:  # パターンA,B,D
                                # ラベリング設定内target_valueをラベリング設定内target_typeに合わせて変換
                                target_value_setting = target_value_type[setting["TARGET_TYPE_ID"]](setting["TARGET_VALUE"])

                                if setting["TARGET_TYPE_ID"] == "7":  # 空判定

                                    if setting["COMPARISON_METHOD_ID"] == "1":
                                        # ラベリング設定内target_keyが取得してきたイベント内event_inside_keyの中に存在するものの中でvalueがFalseのものが存在するか確認
                                        if (target_value_collection in ["", [], {}, 0, False]) is True:
                                            event = label(wsDb, event_collection_data, setting)
                                    elif setting["COMPARISON_METHOD_ID"] == "2":
                                        if (target_value_collection in ["", [], {}, 0, False]) is False:
                                            event = label(wsDb, event_collection_data, setting)
                                    else:
                                        continue

                                # 収取したJSONデータのtarget_valueとラベリング設定内target_valueを比較
                                elif comparison_values(setting["COMPARISON_METHOD_ID"], target_value_collection, target_value_setting) is True:
                                    # label_valueが空の場合、target_valueをlabel_valueに流用する（パターンB用）
                                    if setting["LABEL_VALUE"] is None:
                                        setting["LABEL_VALUE"] = setting["TARGET_VALUE"]

                                    event = label(wsDb, event_collection_data, setting)  # noqa: F841

            except Exception as e:
                print(e)
                return label_result

    # ラベリングしたデータをMongoDBに保存
    try:
        labeled_event_collection.insert_many(labeled_events)
    except Exception as e:
        debug_msg = "failed to insert labeled events"
        print(debug_msg)
        print(e)
        return label_result

    label_result = True

    return label_result


def create_jmespath_query(json_path):
    # .に合わせて分割
    key_list = json_path.split(".")
    query = "contains(keys({}), '{}')"
    # key_listの中身が1階層の場合
    if len(key_list) == 1:
        return query.format("@", key_list[0])

    # 要素を連結する
    parent_key = ".".join(key_list[:-1])
    key_to_find = key_list[-1]
    return query.format(parent_key, key_to_find)
