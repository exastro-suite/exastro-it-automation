# Copyright 2023 NEC Corporation#
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
import inspect
import os

from common_libs.oase.const import oaseConst
from common_libs.common.mongoconnect.const import Const as mongoConst

class ManageEvents:
    def __init__(self, wsMongo, judgeTime):
        self.labeled_event_collection = wsMongo.collection(mongoConst.LABELED_EVENT_COLLECTION)
        # 以下条件のイベントを取得
        undetermined_search_value = {
            "labels._exastro_timeout": "0",
            "labels._exastro_evaluated": "0",
            "labels._exastro_undetected": "0"
        }
        labeled_events = self.labeled_event_collection.find(undetermined_search_value)

        self.labeled_events_dict = {}

        for event in labeled_events:
            event[oaseConst.DF_LOCAL_LABLE_NAME] = {}
            event[oaseConst.DF_LOCAL_LABLE_NAME]["status"] = None

            check_result, event_status = self.check_event_status(
                int(judgeTime),
                int(event["labels"]["_exastro_fetched_time"]),
                int(event["labels"]["_exastro_end_time"]),
            )
            if check_result is False:
                continue

            self.add_local_label(
                event,
                oaseConst.DF_LOCAL_LABLE_NAME,
                oaseConst.DF_LOCAL_LABLE_STATUS,
                event_status
            )
            self.labeled_events_dict[event["_id"]] = event

    # イベント有効期間判定
    def check_event_status(self, judge_time, fetched_time, end_time):
        result = True
        ttl = end_time - fetched_time
        ttl = judge_time - (ttl * 2)
        event_status = oaseConst.DF_PROC_EVENT

        # 不正なイベント
        if fetched_time > end_time:
            result = False
        # 対象外イベント
        elif judge_time < fetched_time:
            event_status = oaseConst.DF_NOT_PROC_EVENT
        # タイムアウト
        elif end_time < ttl:
            event_status = oaseConst.DF_TIMEOUT_EVENT
        # 処理後タイムアウト（処理対象）
        elif ttl <= end_time < judge_time:
            event_status = oaseConst.DF_POST_PROC_TIMEOUT_EVENT
        # 処理対象
        elif judge_time <= end_time:
            pass
        # 想定外のイベント
        else:
            result = False

        return result, event_status

    # 処理で必要なラベルを追加
    def add_local_label(self, event, parent_label, member_label, value):
        if parent_label not in event:
            event[parent_label] = {}
        event[parent_label][member_label] = value
        return event

    def find_events(self, event_judge_list):
        used_event_list = []

        for event_id, event in self.labeled_events_dict.items():
            # タイムアウトイベント判定
            if str(event['labels']['_exastro_timeout']) != '0':
                continue
            # 処理済みイベント判定
            if str(event['labels']['_exastro_evaluated']) != '0':
                continue
            labels = event["labels"]
            judge_result = {}
            judge_result["count"] = 0
            judge_result["True"] = 0
            judge_result["False"] = 0
            for item in event_judge_list:
                judge_result["count"] += 1
                key = item["LabelKey"]
                value = item["LabelValue"]
                condition = item["LabelCondition"]
                hit = False
                if key in labels:
                    if str(condition) == oaseConst.DF_TEST_EQ:
                        if labels[key] == value:
                            hit = True
                    else:
                        if labels[key] != value:
                            hit = True
                judge_result[str(hit)] += 1
                if hit is False:
                    break
            if judge_result["count"] == judge_result["True"]:
                used_event_list.append(event["_id"])

        return True, used_event_list

    def count_events(self):
        return len(self.labeled_events_dict)

    def count_unevaluated_events(self):
        """未評価イベントの総数を返します / Returns the total number of unevaluated events

        Returns:
            int: 未評価イベントの総数
        """
        count = 0
        for event_id, event in self.labeled_events_dict.items():
            if event['labels']['_exastro_evaluated'] == '0' \
            and event['labels']['_exastro_timeout'] == '0' \
            and event['labels']['_exastro_undetected'] == '0':
                count += 1

        return count

    def append_event(self, event):
        self.labeled_events_dict[event["_id"]] = event

    def get_events(self, event_id):
        if event_id not in self.labeled_events_dict:
            return False, {}
        return True, self.labeled_events_dict[event_id]

    def get_timeout_event(self):
        # タイムアウト（TTL*2）
        timeout_event_id_list = []
        for event_id, event in self.labeled_events_dict.items():
            if event[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS] == oaseConst.DF_TIMEOUT_EVENT:
                timeout_event_id_list.append(event_id)
        return timeout_event_id_list

    def get_post_proc_timeout_event(self):
        post_proc_timeout_event_ids = []
        # 処理後にタイムアウトにするイベントを抽出
        for event_id, event in self.labeled_events_dict.items():
            # タイムアウトしたイベントは登録されているのでスキップ
            if event["labels"]["_exastro_timeout"] != "0":
                continue
            # ルールにマッチしているイベント
            if event["labels"]["_exastro_evaluated"] != "0":
                continue
            # 処理後にタイムアウトにするイベント
            if event[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS] == oaseConst.DF_POST_PROC_TIMEOUT_EVENT:
                post_proc_timeout_event_ids.append(event_id)

        return post_proc_timeout_event_ids

    def get_unused_event(self, incident_dict, filterIDMap):
        """
        フィルタにマッチしていないイベントを抽出

        Arguments:
            incident_dict: メモリーに保持している、フィルターID:（マッチした）イベント（id or id-list）、形式のリスト
            filterIDMap:
        Returns:
            unused_event_ids(dict)
        """
        unused_event_ids = []

        # incident_dictに登録されているイベントをfilter_match_listに格納する
        filter_match_list = []
        for filter_id, id_value_list in incident_dict.items():
            if len(id_value_list) > 0:
                filter_match_list += id_value_list

        for event_id, event in self.labeled_events_dict.items():
            # タイムアウトしたイベントは登録されているのでスキップ
            if event["labels"]["_exastro_timeout"] != "0":
                continue
            # ルールにマッチしているイベント
            if event["labels"]["_exastro_evaluated"] != "0":
                continue

            # keyが削除されてincident_dictが空になっている場合（or条件で両方のフィルターにマッチしていた場合）があるのでここで判定する
            if len(incident_dict) == 0:
                unused_event_ids.append(event_id)
                continue

            # フィルターにマッチしなかった
            if event_id not in filter_match_list:
                unused_event_ids.append(event_id)

        return unused_event_ids

    def insert_event(self, dict):
        result = self.labeled_event_collection.insert_one(dict)
        return result.inserted_id

    def update_label_flag(self, event_id_list, update_flag_dict):
        for event_id in event_id_list:
            if event_id not in self.labeled_events_dict:
                return False
            for key, value in update_flag_dict.items():
                self.labeled_events_dict[event_id]["labels"][key] = value
            # MongoDB更新
            self.labeled_event_collection.update_one({"_id": event_id}, {"$set": {f"labels.{key}": value}})

        return True

    def print_event(self):
        for event_id, event in self.labeled_events_dict.items():
            id = str(event['_id'])
            evaluated = str(event['labels']['_exastro_evaluated'])
            undetected = str(event['labels']['_exastro_undetected'])
            timeout = str(event["labels"]["_exastro_timeout"])
            localsts = str(event[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS])
            status = "Unknown"  # 不明
            if evaluated == '0' and undetected == '1' and timeout == '0':
                status = "Undetected        "  # 未知
            elif evaluated == '0' and undetected == '0' and timeout == '1':
                status = "Timeout"  # タイムアウト
            elif evaluated == '0' and undetected == '0' and timeout == '0':
                status = "Currently no action required"  # 今は対応不要
            elif evaluated == '1' and undetected == '0' and timeout == '0':
                status = "Action required      "  # 要対応
            if localsts == oaseConst.DF_PROC_EVENT:
                localsts = "Process target:〇"  # 処理対象:〇
            elif localsts == oaseConst.DF_POST_PROC_TIMEOUT_EVENT:
                localsts = "Process target. Post-process timeout:●"  # 処理対象　処理後タイムアウト:●
            elif localsts == oaseConst.DF_TIMEOUT_EVENT:
                localsts = "Timeout"  # タイムアウト
            elif localsts == oaseConst.DF_NOT_PROC_EVENT:
                localsts = "Not target"  # 対象外
            tmp_msg = "id:{} status:{}  _exastro_evaluated:{}  _exastro_undetected:{}  _exastro_timeout:{} local_status:{}".format(id, status, evaluated, undetected, timeout, localsts)
            g.applogger.info(self.addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    def addline_msg(self, msg=''):
        info = inspect.getouterframes(inspect.currentframe())[1]
        msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
        return msg_line
