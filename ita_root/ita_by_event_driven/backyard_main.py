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
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.common.util import get_timestamp, get_all_execution_limit, get_org_execution_limit
from common_libs.ci.util import log_err
import datetime
import json
import re
import jmespath
import operator

# from libs import common_functions as cm


def backyard_main(organization_id, workspace_id):
    """
    [ita_by_ansible_execute]
    main logicのラッパー
    called 実行君
    """
    g.applogger.debug(g.appmsg.get_log_message("BKY-00001"))

    retBool = main_logic(organization_id, workspace_id)
    if retBool is True:
        # 正常終了
        g.applogger.debug(g.appmsg.get_log_message("BKY-00002"))
    else:
        g.applogger.debug(g.appmsg.get_log_message("BKY-00003"))


def main_logic(organization_id, workspace_id):
    """
    main logic
    """
    g.applogger.debug("organization_id=" + organization_id)
    g.applogger.debug("workspace_id=" + workspace_id)

    ######################################################
    # イベント収集
    ######################################################

    # 仮のイベント収集設定
    gathering_event_settings = [
        {
            "gathering_event_id": "a1a1a1",
            "gathering_event_name": "Zabbix Trigger",
            "monitoring_tool_id": "1",
            "api_url": "sampleZabbixTrigger.json",
            "is_list": 1,
            "list_key": "result"
        },
        {
            "gathering_event_id": "c3c3c3",
            "gathering_event_name": "Prometheus Alert",
            "monitoring_tool_id": "2",
            "api_url": "samplePrometheus.json",
            "is_list": 1,
            "list_key": "data.alerts"
        },
        {
            "gathering_event_id": "b2b2b2",
            "gathering_event_name": "Grafana Alerting",
            "monitoring_tool_id": "3",
            "api_url": "sampleGrafana.json",
            "is_list": 1,
            "list_key": None
        },
    ]

    wsMong = MONGOConnectWs()
    event_collection = wsMong.collection("event_collection")
    g.applogger.debug("mongodb-ws can connet")

    # jsonのパス表記をpython用に変換する
    def convert_path(dict_data, key_string):
        if key_string is None:
            return dict_data
        keys = key_string.split(".")
        with_path = dict_data
        for key in keys:
            with_path = with_path[key]
        return with_path

    events = []
    for setting in gathering_event_settings:
        # APIの呼び出し（実際は専用モジュールみたいなものを使用?）
        with open(setting["api_url"]) as f:
            json_data = json.load(f)
            # レスポンスがリスト形式ではない場合はそのまま保存する
            if setting["is_list"] == 0:
                json_data["monitoring_tool_id"] = setting["monitoring_tool_id"]
                json_data["gathering_event_id"] = setting["gathering_event_id"]
                json_data["gathering_event_name"] = setting["gathering_event_name"]
                json_data["fetch_time"] = datetime.datetime.now()
                event_collection.insert_one(json_data)
            # レスポンスがリスト形式の場合、1つずつ保存
            else:
                json_data = convert_path(json_data, setting["list_key"])
                for data in json_data:
                    data["monitoring_tool_id"] = setting["monitoring_tool_id"]
                    data["gathering_event_id"] = setting["gathering_event_id"]
                    data["gathering_event_name"] = setting["gathering_event_name"]
                    data["fetch_time"] = datetime.datetime.now()
                    # event_collection.insert_one(data)
                    events.append(data)

    ######################################################
    # ラベリング
    ######################################################

    # 仮のラベリング設定
    tmp_labeling_settings = [
        {
            "labeling_id": "xxx",
            "label_name": "DB障害",
            "gathering_event_id": "a1a1a1",
            "target_key": "lastchange",
            "target_value": "1684972724",
            "compare_method_id": "1",
            "ita_status_key": "aaa",
            "ita_status_value": "AAA",
        },
        {
            "labeling_id": "yyy",
            "label_name": "高CPU使用率",
            "gathering_event_id": "b2b2b2",
            "target_key": "evalData.evalMatches[0].metric",
            "target_value": "cpu_usage",
            "compare_method_id": "1",
            "ita_status_key": "bbb",
            "ita_status_value": "BBB"
        },
        {
            "labeling_id": "zzz",
            "label_name": "ディスク残量小",
            "gathering_event_id": "b2b2b2",
            "target_key": "evalData.evalMatches[0].metric",
            "target_value": "disk_space",
            "compare_method_id": "1",
            "ita_status_key": "ccc",
            "ita_status_value": "CCC"
        },
    ]

    # ラベルデータ用コレクション設定
    labeled_event_collection = wsMong.collection("labeled_event_collection")

    # フィルター用クエリ作成
    def create_mongodb_query(jsonpath, value, operator="$eq"):
        if "[]" in jsonpath:
            jsonpath = jsonpath.replace("[]", "")
            query = {jsonpath: {"$elemMatch": {operator: value}}}
        else:
            jsonpath = jsonpath.replace("[", ".").replace("]", "")
            query = {jsonpath: {operator: value}}
        return query

    # ドット区切りで辞書を指定
    def get_value_from_jsonpath(jsonpath, data):
        value = jmespath.search(jsonpath, data)
        return value

    compare_operator = {
        "1": operator.eq,
        "2": operator.ne,
        "3": operator.lt,
        "4": operator.le,
        "5": operator.gt,
        "6": operator.ge,
        "7": "正規表現"
    }

    def compare_value(compare_method_id, comparative, referent):
        key_list = list(compare_operator.keys())
        if compare_method_id in key_list:
            if compare_method_id == "7":
                regex_pattern = re.compile(referent)
                result = regex_pattern.search(comparative)
            else:
                compare = compare_operator[compare_method_id]
                result = compare(comparative, referent)
        return result

    tmp_label_dict = {}
    for event in events:
        for setting in tmp_labeling_settings:
            if setting["ita_status_value"] is False:
                setting["ita_status_value"] = setting["target_value"]
            target_value = get_value_from_jsonpath(setting["target_key"], event)
            if compare_value(setting["compare_method_id"], target_value, setting["target_value"]):
                gathering_event_id = setting["gathering_event_id"]
                if gathering_event_id in tmp_label_dict:
                    tmp_label_dict[gathering_event_id][setting["ita_status_key"]] = setting["ita_status_value"]
                    tmp_label_dict[gathering_event_id]["labeling_setting_ids"].append(setting["labeling_id"])
                    tmp_label_dict[gathering_event_id]["events"].append(event)
                else:
                    tmp_labeled_data = {
                        "labeling_setting_ids": [setting["labeling_id"]],
                        "gathering_event_id": gathering_event_id,
                        "events": [event],
                        "evaluated": 0,
                        setting["ita_status_key"]: setting["ita_status_value"]
                    }
                    tmp_label_dict[gathering_event_id] = tmp_labeled_data

    for labeled_data in list(tmp_label_dict.values()):
        labeled_event_collection.insert_one(labeled_data)

    # events = event_collection.find()
    # labeled_data = {
    #     "labeling_setting_ids": [],
    #     "events": [],
    #     "evaluated": 0
    # }
    # for event in events:
    #     for setting in tmp_labeling_settings:
    #         if setting["ita_status_value"] is False:
    #             setting["ita_status_value"] = setting["target_value"]
    #         target_value = get_value_from_jsonpath(setting["target_key"], event)
    #         if compare_value(setting["compare_method_id"], target_value, setting["target_value"]):
    #             labeled_data[setting["ita_status_key"]] = setting["ita_status_value"]
    #             labeled_data["labeling_setting_ids"].append(setting["labeling_id"])
    #             labeled_data["events"].append(event)
    # labeled_event_collection.insert_one(labeled_data)

    return True
