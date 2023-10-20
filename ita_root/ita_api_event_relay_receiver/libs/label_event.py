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


def label_event(wsDb, wsMongo, events):

    label_result = False
    debug_msg = ""

    labeling_settings = wsDb.table_select(
        "T_EVRL_LABELING_SETTINGS",
        "WHERE DISUSE_FLAG=%s",
        ["0"]
    )

    # そのままのデータ保存コレクション
    event_collection = wsMongo.collection("event_collection")

    # ラベルデータ保存用コレクション
    labeled_event_collection = wsMongo.collection("labeled_event_collection")

    # そのままのデータをMongoDBに保存
    try:
        event_collection.insert_many(events)
    except Exception as e:
        debug_msg = "failed to insert events"
        print(debug_msg)
        print(e)
        return label_result

    comparison_operator = {
        "1": operator.eq,
        "2": operator.ne,
        "3": operator.lt,
        "4": operator.le,
        "5": operator.gt,
        "6": operator.ge,
        "7": "Regular expression"
    }

    def returns_bool(value):
        if value == "true":
            return True
        elif value == "false":
            return False
        else:
            return None

    target_value_type = {
        "1": str,
        "2": int,
        "3": float,
        "4": returns_bool,
        "5": json.loads,
        "6": json.loads,
    }

    # target_value比較用
    def comparison_values(comparison_method_id="1", comparative=None, referent=None):
        key_list = list(comparison_operator.keys())
        if comparison_method_id in key_list:
            if comparison_method_id == "7":
                regex_pattern = re.compile(referent)
                result = regex_pattern.search(comparative)
            else:
                comparison = comparison_operator[comparison_method_id]
                result = comparison(comparative, referent)
        return result

    # ドット区切りの文字列で辞書を指定して値を取得
    def get_value_from_jsonpath(jsonpath, data):
        value = jmespath.search(jsonpath, data)
        return value

    def label(event, setting):
        label_key_record = wsDb.table_select(
            "V_EVRL_LABEL_KEY_GROUP",
            "WHERE DISUSE_FLAG=0 AND LABEL_KEY_ID=%s",
            [setting["LABEL_KEY_ID"]]
        )

        label_key_id = label_key_record[0]["LABEL_KEY_ID"]
        label_key_string = label_key_record[0]["LABEL_KEY"]

        event["labels"]["_exastro_evaluated"] = 0
        event["labels"][label_key_string] = setting["LABEL_VALUE"]
        event["exastro_labeling_settings"][label_key_string] = setting["LABELING_SETTINGS_ID"]
        event["exastro_label_key_input_ids"][label_key_string] = label_key_id
        return event

    labeled_events = []

    for event in events:
        labeled_event = {}
        original_event = event
        labeled_event["event"] = original_event
        exastro_labels = {
            "_exastro_event_collection_settings_id": event["_exastro_event_collection_settings_id"],
            "_exastro_fetched_time": event["_exastro_fetched_time"],
            "_exastro_end_time": event["_exastro_end_time"],
            "_exastro_type": "event",
            "_exastro_evaluated": "0",
            "_exastro_undetected": "0",
            "_exastro_timeout": "0"
        }
        labeled_event["labels"] = exastro_labels
        del labeled_event["event"]["_exastro_event_collection_settings_id"]
        del labeled_event["event"]["_exastro_fetched_time"]
        del labeled_event["event"]["_exastro_end_time"]
        labeled_events.append(labeled_event)

    for event in labeled_events:
        event["exastro_labeling_settings"] = {}
        event["exastro_label_key_input_ids"] = {}

        # ラベリング設定に該当するデータにはラベルを貼る
        for setting in labeling_settings:
            try:
                if setting["LABEL_VALUE"] == "":
                    setting["LABEL_VALUE"] = setting["TARGET_VALUE"]

                same_id_flag = event["labels"]["_exastro_event_collection_settings_id"] == setting["EVENT_COLLECTION_SETTINGS_ID"]

                if setting["TARGET_KEY"] == "" and same_id_flag:
                    if setting["TARGET_TYPE_ID"] == "7" and get_value_from_jsonpath(setting["TARGET_KEY"], event["event"]) is False:
                        event = label(event, setting)
                    event = label(event, setting)

                if setting["TARGET_KEY"] and setting["TARGET_KEY"] in event and same_id_flag:
                    event = label(event, setting)

                if (setting["TARGET_KEY"] and setting["TARGET_VALUE"]) != "" and same_id_flag:
                    target_value = get_value_from_jsonpath(setting["TARGET_KEY"], event["event"])
                    if target_value is None:
                        debug_msg = f"value of TARGET_KEY was not found. TARGET_KEY: {setting['TARGET_KEY']}"
                        raise Exception
                    if setting["TARGET_TYPE_ID"] == "7":
                        debug_msg = "Invalid labeling setting"
                        raise Exception
                    target_value = target_value_type[setting["TARGET_TYPE_ID"]](target_value)

                    if comparison_values(setting["COMPARISON_METHOD_ID"], target_value, setting["TARGET_VALUE"]):

                        event = label(event, setting)
            except Exception as e:
                print(e)
                print(debug_msg)
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
