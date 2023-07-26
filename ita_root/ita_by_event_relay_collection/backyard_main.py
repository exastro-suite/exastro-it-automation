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

    wsDb = DBConnectWs(workspace_id)

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
            "list_key": "result",
            "ttl": 300
        },
        {
            "gathering_event_id": "c3c3c3",
            "gathering_event_name": "Prometheus Alert",
            "monitoring_tool_id": "2",
            "api_url": "samplePrometheus.json",
            "is_list": 1,
            "list_key": "data.alerts",
            "ttl": 200
        },
        {
            "gathering_event_id": "b2b2b2",
            "gathering_event_name": "Grafana Alerting",
            "monitoring_tool_id": "3",
            "api_url": "sampleGrafana.json",
            "is_list": 1,
            "list_key": None,
            "ttl": 180
        },
    ]

    wsMong = MONGOConnectWs()
    g.applogger.debug("mongodb-ws can connet")

    # 生データ保存用コレクション
    event_collection = wsMong.collection("event_collection")

    # jsonのパス表記をpython用に変換する
    def convert_path(dict_data, key_string):
        if key_string is None:
            return dict_data
        keys = key_string.split(".")
        with_path = dict_data
        for key in keys:
            with_path = with_path[key]
        return with_path

    events = []  # ラベル付きの保存用データ

    for setting in gathering_event_settings:
        tmp_polling_interval = 10  # 仮のポーリング間隔
        # APIの呼び出し（実際は専用モジュールみたいなものを使用?）
        with open(setting["api_url"]) as f:
            json_data = json.load(f)
            fetched_time = datetime.datetime.now()
            # レスポンスがリスト形式ではない場合はそのまま保存する
            if setting["is_list"] == 0:
                event = {}
                event["ita_event"] = json_data
                event["ita_gathering_event_id"] = setting["gathering_event_id"]
                event["ita_fetched_time"] = fetched_time.timestamp()
                event["ita_start_time"] = fetched_time
                event["ita_start_time"] = (fetched_time + datetime.timedelta(seconds=tmp_polling_interval)).timestamp()
                event["ita_end_time"] = (fetched_time + datetime.timedelta(seconds=setting["ttl"])).timestamp()
                events.append(event)
            # レスポンスがリスト形式の場合、1つずつ保存
            else:
                json_data = convert_path(json_data, setting["list_key"])
                for data in json_data:
                    event = {}
                    event["ita_event"] = data
                    event["ita_gathering_event_id"] = setting["gathering_event_id"]
                    event["ita_fetched_time"] = fetched_time.timestamp()
                    event["ita_start_time"] = (fetched_time + datetime.timedelta(seconds=tmp_polling_interval)).timestamp()
                    event["ita_end_time"] = (fetched_time + datetime.timedelta(seconds=setting["ttl"])).timestamp()
                    events.append(event)
    print(events)
    # event_collection.insert_many(events)

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
            "ita_label_key": "aaa",
            "ita_label_value": "AAA",
        },
        {
            "labeling_id": "yyy",
            "label_name": "高CPU使用率",
            "gathering_event_id": "b2b2b2",
            "target_key": "evalData.evalMatches[0].metric",
            "target_value": "cpu_usage",
            "compare_method_id": "1",
            "ita_label_key": "bbb",
            "ita_label_value": "BBB"
        },
        {
            "labeling_id": "zzz",
            "label_name": "高CPU使用率",
            "gathering_event_id": "b2b2b2",
            "target_key": "name",
            "target_value": "High CPU Usage",
            "compare_method_id": "7",
            "ita_label_key": "ccc",
            "ita_label_value": "CCC"
        },
    ]

    # ラベルデータ保存用コレクション
    labeled_event_collection = wsMong.collection("labeled_event_collection")

    # ドット区切りで辞書を指定して値を取得
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
        "7": "Regular expression"
    }

    # target_value比較用
    def compare_values(compare_method_id, comparative, referent):
        key_list = list(compare_operator.keys())
        if compare_method_id in key_list:
            if compare_method_id == "7":
                regex_pattern = re.compile(referent)
                result = regex_pattern.search(str(comparative))
            else:
                compare = compare_operator[compare_method_id]
                result = compare(comparative, referent)
        return result

    for event in events:
        event["ita_labeling_ids"] = []
        event["ita_labels"] = {}
        # ラベリング設定に該当するデータにはラベルを貼る
        for setting in tmp_labeling_settings:
            if setting["ita_label_value"] is False:
                setting["ita_label_value"] = setting["target_value"]
            target_value = get_value_from_jsonpath(setting["target_key"], event["ita_event"])
            if compare_values(setting["compare_method_id"], target_value, setting["target_value"]):
                event["ita_evaluated"] = 0
                event["ita_labels"][setting["ita_label_key"]] = setting["ita_label_value"]
                event["ita_labeling_ids"].append(setting["labeling_id"])

    # ラベルされていないものは除外
    labeled_events = [item for item in events if item["ita_labels"] != {}]
    print(labeled_events)
    # labeled_event_collection.insert_many(labeled_events)

    return True
