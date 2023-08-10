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


def label_event(mariaDB, mongoDB, events):

    label_result = True
    debug_msg = ""

    wsMongoDB = mongoDB
    g.applogger.debug("mongodb-ws can connet")
    # 仮のラベリング設定
    tmp_labeling_settings = [
        {
            "exastro_labeling_settings_id": "xxx",
            "label_name": "ラベル設定1",
            "exastro_event_collection_settings_id": "a1a1a1",
            "target_key": "host",
            "target_value": "target-support",
            "compare_method_id": "1",
            "label_key": "ラベルキー1",
            "label_value": "ラベル値1",
        },
        {
            "exastro_labeling_settings_id": "yyy",
            "label_name": "ラベル設定2",
            "exastro_event_collection_settings_id": "b1b1b1",
            "target_key": "name",
            "target_value": "Zabbix agent active",
            "compare_method_id": "7",
            "label_key": "ラベルキー2",
            "label_value": "ラベル値2",
        },
        {
            "exastro_labeling_settings_id": "zzz",
            "label_name": "ラベル設定3",
            "exastro_event_collection_settings_id": "b1b1b1",
            "target_key": "name",
            "target_value": "Zabbix agent active",
            "compare_method_id": "7",
            "label_key": "ラベルキー3",
            "label_value": "ラベル値3",
        },
        {
            "exastro_labeling_settings_id": "qqq",
            "label_name": "ラベル設定4",
            "exastro_event_collection_settings_id": "a1a1a1",
            "target_key": "",
            "target_value": "",
            "compare_method_id": "1",
            "label_key": "ラベルキー4",
            "label_value": "ラベル値4",
        }
    ]

    # ラベルデータ保存用コレクション
    labeled_event_collection = wsMongoDB.collection("labeled_event_collection")

    compare_operator = {
        "1": operator.eq,
        "2": operator.ne,
        "3": operator.lt,
        "4": operator.le,
        "5": operator.gt,
        "6": operator.ge,
        "7": "Regular expression"
    }

    # target_value比較用
    def compare_values(compare_method_id="1", comparative=None, referent=None):
        key_list = list(compare_operator.keys())
        if compare_method_id in key_list:
            if compare_method_id == "7":
                regex_pattern = re.compile(referent)
                result = regex_pattern.search(comparative)
            else:
                compare = compare_operator[compare_method_id]
                result = compare(comparative, referent)
        return result

    # ドット区切りの文字列でで辞書を指定して値を取得
    def get_value_from_jsonpath(jsonpath, data):
        value = jmespath.search(jsonpath, data)
        return value

    def label(event, setting):
        event["labels"]["_exastro_evaluated"] = 0
        event["labels"][setting["label_key"]] = setting["label_value"]
        event["exastro_labeling_settings_ids"][setting["label_key"]] = setting["exastro_labeling_settings_id"]
        # event["exastro_labeling_settings_ids"].append({setting["label_key"]: setting["exastro_labeling_settings_id"]})

    labeled_events = []

    for event in events:
        labeled_event = {}
        original_event = event
        labeled_event["event"] = original_event
        exastro_labels = {
            "_exastro_event_collection_settings_id": event["_exastro_event_collection_settings_id"],
            "_exastro_fetched_time": event["_exastro_fetched_time"],
            "_exastro_end_time": event["_exastro_end_time"]
        }
        labeled_event["labels"] = exastro_labels
        del labeled_event["event"]["_exastro_event_collection_settings_id"]
        del labeled_event["event"]["_exastro_fetched_time"]
        del labeled_event["event"]["_exastro_end_time"]
        labeled_events.append(labeled_event)

    for event in labeled_events:
        event["exastro_labeling_settings_ids"] = {}

        # ラベリング設定に該当するデータにはラベルを貼る
        for setting in tmp_labeling_settings:
            if setting["label_value"] == "":
                setting["label_value"] = setting["target_value"]

            same_id_flag = event["labels"]["_exastro_event_collection_settings_id"] == setting["exastro_event_collection_settings_id"]

            if setting["target_key"] == "" and same_id_flag:
                label(event, setting)

            if setting["target_key"] and setting["target_key"] in event and same_id_flag:
                label(event, setting)

            if (setting["target_key"] and setting["target_value"]) != "" and same_id_flag:
                target_value = get_value_from_jsonpath(setting["target_key"], event["event"])
                if target_value is None:
                    debug_msg = f"value of TARGET_KEY was not found. TARGET_KEY: {setting['target_key']}"
                if compare_values(setting["compare_method_id"], target_value, setting["target_value"]):
                    label(event, setting)

    # ラベルされていないものは除外
    labeled_events = [item for item in labeled_events if item["exastro_labeling_settings_ids"] != {}]
    # labeled_events = [item for item in labeled_events if item["exastro_labeling_settings_ids"] != []]
    # print(labeled_events)
    # print(len(labeled_events))
    try:
        labeled_event_collection.insert_many(labeled_events)
    except Exception as e:
        debug_msg = "failed to insert labeled events"
        # print(debug_msg)
        # print(e)

    return label_result
