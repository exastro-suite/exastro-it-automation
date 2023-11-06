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


# イベントにラベルを付与し、MongDBに保存する
def label_event(wsDb, wsMongo, events):  # noqa: C901
    # 返却値
    err_code = ""
    err_msg = ""

    # ラベル付与の設定を取得
    labeling_settings = wsDb.table_select(
        "T_OASE_LABELING_SETTINGS",
        "WHERE DISUSE_FLAG=%s",
        ["0"]
    )
    if len(labeling_settings) == 0:
        err_code = "499-00000"
        err_msg = "ラベル付与設定を取得できませんでした。"
        g.applogger.error(err_msg)
        return err_code, err_msg

    # ラベルのマスタを取得
    label_keys = wsDb.table_select(
        "T_OASE_LABEL_KEY_INPUT",
        "WHERE DISUSE_FLAG=0"
    )
    if len(label_keys) == 0:
        err_code = "499-00000"
        err_msg = "ラベルのマスタを取得できませんでした。"
        g.applogger.error(err_msg)
        return err_code, err_msg
    # ラベルのマスタデータをIDで引けるように整形
    label_key_map = {}
    for label_key in label_keys:
        label_key_map[label_key["LABEL_KEY_ID"]] = label_key

    # そのままのイベントデータを保存するためのコレクション
    event_collection = wsMongo.collection("event_collection")
    # MongoDBに保存
    event_collection.insert_many(events)

    # ラベル付与したイベントデータを保存するためのコレクション
    labeled_event_collection = wsMongo.collection("labeled_event_collection")
    # ラベル付与されたイベント配列（MongoDBに保存予定）
    labeled_events = []

    # 取得してきたJSONデータをイベント単位でループ（exastro用ラベルのみ付与する）
    for single_event in events:
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

    # exastro用ラベルを貼った後のデータをイベント単位でループ
    for event_collection_data in labeled_events:
        event_collection_data["exastro_labeling_settings"] = {}
        event_collection_data["exastro_label_key_input_ids"] = {}

        # ラベル付与設定に該当するデータにはラベルを貼る
        # パターンの説明
        #
        #
        #
        for setting in labeling_settings:
            try:
                # 収集した_exastro_event_collection_settings_idとイベント収集設定IDが一致しないものはスキップ
                if event_collection_data["labels"]["_exastro_event_collection_settings_id"] != setting["EVENT_COLLECTION_SETTINGS_ID"]:
                    continue

                if (setting["TARGET_KEY"] in event_collection_data["event"]):
                    settings = event_collection_data["event"]
                    setting_flag = True
                elif (setting["TARGET_KEY"] in event_collection_data["labels"]):
                    settings = event_collection_data["labels"]
                    setting_flag = True
                else:
                    if setting["TARGET_KEY"] is None:
                        setting_flag = False
                    else:
                        query = create_jmespath_query(setting["TARGET_KEY"])
                        if query is None:
                            setting_flag = None
                            continue
                        settings = event_collection_data["event"]
                        setting_flag = True
                # ラベル付与設定内にtarget_keyが存在するか確認(パターンC用)
                if setting_flag is False:

                    # ラベル付与設定内target_typeが"空関数"、かつ取得してきたイベント内"event"のvalueがラベル付与設定内target_keyの中に存在しない場合
                    if setting["TARGET_TYPE_ID"] is None and setting["TARGET_VALUE"] is None:
                        event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンC

                # ラベル付与設定内にtarget_keyが存在する、かつ取得してきたJSONデータ内にラベル付与設定内で指定したtarget_keyが存在するか確認（パターンA,B,D,E用）
                if setting["TARGET_KEY"] and setting_flag is True:

                    # ラベル付与設定内target_typeが"空関数"以外、かつラベル付与設定内にtarget_type_id、Target_valueのどちらも存在しない場合(パターンD用)
                    if ((setting["TARGET_TYPE_ID"] and setting["TARGET_VALUE"]) is None) and setting["TARGET_TYPE_ID"] != "7":

                        if setting_flag is True:
                            event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンD

                        elif setting_flag is False:
                            # queryが取得してきたイベント,inside_keyの中に存在する場合
                            if get_value_from_jsonpath(query, settings):
                                event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンD

                    # パターンA,B,E
                    else:
                        # 取得してきたイベント,event_inside_key内にラベル付与設定内target_keyが一致するものを取得
                        target_value_collection = get_value_from_jsonpath(setting["TARGET_KEY"], settings)

                        # target_keyに対応する値が取得できたか確認
                        if target_value_collection is None:
                            # queryが取得してきたイベント,inside_keyの中に存在する場合
                            if get_value_from_jsonpath(query, settings) is not True:
                                continue
                            event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンD

                        else:  # パターンA,B,E
                            # ラベル付与設定内target_valueをラベル付与設定内target_typeに合わせて変換
                            target_value_setting = target_value_type[setting["TARGET_TYPE_ID"]](setting["TARGET_VALUE"])

                            if setting["TARGET_TYPE_ID"] == "7":  # 空判定(パターンE用)
                                if setting["COMPARISON_METHOD_ID"] == "1":  # ==
                                    # ラベル付与設定内target_keyが取得してきたイベント内event_inside_keyの中に存在するものの中でvalueがFalseのものが存在するか確認
                                    if (target_value_collection in ["", [], {}, 0, False, None]) is True:
                                        event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンE(比較方法が'==')
                                elif setting["COMPARISON_METHOD_ID"] == "2":  # ≠
                                    # ラベル付与設定内target_keyが取得してきたイベント内event_inside_keyの中に存在するものの中でvalueがFalseのものが存在しないか確認
                                    if (target_value_collection in ["", [], {}, 0, False, None]) is False:
                                        event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンE(比較方法が'≠')
                                else:
                                    continue

                            # 収取したJSONデータのtarget_valueとラベル付与設定内target_valueを比較
                            elif comparison_values(setting["COMPARISON_METHOD_ID"], target_value_collection, target_value_setting) is True:
                                # label_valueが空の場合、target_valueをlabel_valueに流用する（パターンB用）
                                if setting["LABEL_VALUE"] is None:
                                    setting["LABEL_VALUE"] = setting["TARGET_VALUE"]
                                event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンA,B

            except Exception as e:
                err_msg = "ラベル付与に失敗しました"
                g.applogger.error(e)
                g.applogger.error(event_collection_data)
                g.applogger.error(setting)
                return err_code, err_msg

    # ラベル付与したデータをMongoDBに保存
    labeled_event_collection.insert_many(labeled_events)

    return err_code, err_msg


# json構造を検索するためのクエリを生成
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


# ラベル付与設定内で比較方法として真偽値を使用した場合に、値をpythonで解釈できるようにする
# _value ラベル付与設定内でのtarget_value
def returns_bool(_value):
    value = _value.lower()
    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        return None


# ラベル付与設定内target_valueを取得してきたイベントのタイプに合わせて比較するためのマスタ
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


# 収取してきたイベントのtarget_valueとラベル付与設定内target_valueを比較
def comparison_values(comparison_method_id="1", comparative=None, referent=None):
    result = False

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
            if result is not None:
                result = True
        else:
            comparison = comparison_operator[comparison_method_id]
            result = comparison(comparative, referent)

    return result


# ドット区切りの文字列で辞書を指定して値を取得
def get_value_from_jsonpath(jsonpath, data):
    value = jmespath.search(jsonpath, data)
    return value


# ラベル付与処理
def add_label(label_key_map, event_collection_data, setting):
    # ラベルのマスタを引く
    label_key_data = label_key_map[setting["LABEL_KEY_ID"]]

    label_key_id = label_key_data["LABEL_KEY_ID"]
    label_key_string = label_key_data["LABEL_KEY"]

    event_collection_data["labels"][label_key_string] = setting["LABEL_VALUE"]
    event_collection_data["exastro_labeling_settings"][label_key_string] = setting["LABELING_SETTINGS_ID"]
    event_collection_data["exastro_label_key_input_ids"][label_key_string] = label_key_id
    return event_collection_data
