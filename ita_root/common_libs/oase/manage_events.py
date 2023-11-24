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


class ManageEvents:
    def __init__(self, WsMongo, judgeTime):
        self.labeled_event_collection = WsMongo.collection("labeled_event_collection")
        # 以下条件のイベントを取得
        undetermined_search_value = {
            "labels._exastro_timeout": "0",
            "labels._exastro_evaluated": "0",
            "labels._exastro_undetected": "0"
        }
        labeled_events = self.labeled_event_collection.find(undetermined_search_value)
        self.rule_const = {
            # イベントデータに一時的に追加する項目定期
            # 親ラベル
            "DF_LOCAL_LABLE_NAME": "__local_labels__",
            # 子ラベル イベント状態
            "DF_LOCAL_LABLE_STATUS": "status",
            # DF_LOCAL_LABLE_STATUSの状態
            "DF_PROC_EVENT": '0',             # 処理対象:〇
            "DF_POST_PROC_TIMEOUT_EVENT": '1',  # 処理対象　処理後タイムアウト:●
            "DF_TIMEOUT_EVENT": '2',           # タイムアウト
            "DF_NOT_PROC_EVENT": '3',       # 対象外
            # ルール・フィルタ管理　JSON内の演算子・条件
            # 条件
            "DF_TEST_EQ": '1',  # =
            "DF_TEST_NE": '2',  # !=
            # 演算子
            "DF_OPE_NONE": '',  # None
            "DF_OPE_OR": '1',  # OR
            "DF_OPE_AND": '2',  # AND
            "DF_OPE_ORDER": '3'  # ->
        }
        self.labeled_events_dict = {}

        for event in labeled_events:
            event[self.rule_const["DF_LOCAL_LABLE_NAME"]] = {}
            event[self.rule_const["DF_LOCAL_LABLE_NAME"]]["status"] = None

            check_result, event_status = self.check_event_status(
                int(judgeTime),
                int(event["labels"]["_exastro_fetched_time"]),
                int(event["labels"]["_exastro_end_time"]),
            )
            if check_result is False:
                continue

            self.add_local_label(
                event,
                self.rule_const["DF_LOCAL_LABLE_NAME"],
                self.rule_const["DF_LOCAL_LABLE_STATUS"],
                event_status
            )
            self.labeled_events_dict[event["_id"]] = event

    # イベント有効期間判定
    def check_event_status(self, judge_time, fetched_time, end_time):
        result = True
        ttl = end_time - fetched_time
        ttl = judge_time - (ttl * 2)
        event_status = self.rule_const["DF_PROC_EVENT"]

        # 不正なイベント
        if fetched_time > end_time:
            result = False
        # 対象外イベント
        elif judge_time < fetched_time:
            event_status = self.rule_const["DF_NOT_PROC_EVENT"]
        # タイムアウト
        elif end_time < ttl:
            event_status = self.rule_const["DF_TIMEOUT_EVENT"]
        # 処理後タイムアウト（処理対象）
        elif ttl <= end_time < judge_time:
            event_status = self.rule_const["DF_POST_PROC_TIMEOUT_EVENT"]
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
                    if str(condition) == self.rule_const["DF_TEST_EQ"]:
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

    def append_event(self, event):
        self.labeled_events_dict[event["_id"]] = event

    def get_events(self, event_id):
        if event_id not in self.labeled_events_dict:
            return False, {}
        return True, self.labeled_events_dict[event_id]

    def get_timeout_event(self):
        timeout_event_id_list = []
        for event_id, event in self.labeled_events_dict.items():
            if event[self.rule_const["DF_LOCAL_LABLE_NAME"]][self.rule_const["DF_LOCAL_LABLE_STATUS"]] == self.rule_const["DF_TIMEOUT_EVENT"]:
                timeout_event_id_list.append(event_id)
        return timeout_event_id_list

    def update_label_flag(self, event_id_list, update_flag_dict):
        for event_id in event_id_list:
            if event_id not in self.labeled_events_dict:
                return False
            for key, value in update_flag_dict.items():
                self.labeled_events_dict[event_id]["labels"][key] = value
            # MongoDB更新
            self.labeled_event_collection.update_one({"_id": event_id}, {"$set": {f"labels.{key}": value}})

        return True

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
            if event[self.rule_const["DF_LOCAL_LABLE_NAME"]][self.rule_const["DF_LOCAL_LABLE_STATUS"]] == self.rule_const["DF_TIMEOUT_EVENT"]:
                post_proc_timeout_event_ids.append(event_id)

        return post_proc_timeout_event_ids

    def get_unused_event(self, incident_dict):
        unused_event_ids = []
        # フィルタにマッチしていないイベントを抽出
        for event_id, event in self.labeled_events_dict.items():
            # タイムアウトしたイベントは登録されているのでスキップ
            if event["labels"]["_exastro_timeout"] != "0":
                continue
            # ルールにマッチしているイベント
            if event["labels"]["_exastro_evaluated"] != "0":
                continue
            # フィルタにマッチしていないイベント
            if event["_id"] not in incident_dict.values():
                unused_event_ids.append(event["_id"])
        return unused_event_ids

    def insert_event(self, dict):
        result = self.labeled_event_collection.insert_one(dict)
        return result.inserted_id
