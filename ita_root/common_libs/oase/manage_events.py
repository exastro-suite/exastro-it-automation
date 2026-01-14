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

import inspect
import json
import os
import re
from typing import Any, Literal, NewType, Required, TypedDict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from bson import ObjectId
from flask import g

from common_libs.oase.const import oaseConst
from common_libs.common.mongoconnect.const import Const as mongoConst
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.notification.sub_classes.oase import OASENotificationType, OASE
from libs.common_functions import getIDtoLabelName, deduplication_timeout_filter
from libs.writer_process import WriterProcessManager

AttributeKey = NewType("AttributeKey", frozenset[tuple[str, Any]])
"""属性集約キー"""


class GroupingInformation(TypedDict):
    group_id: ObjectId
    """グループID"""

    filter_id: str
    """フィルターID"""

    is_first_event: Literal["0", "1"]
    """先頭イベントフラグ"""


class Event(TypedDict, total=False):
    """イベント"""

    _id: Required[ObjectId]
    """イベントID"""

    __exastro_local_labels__: dict[str, dict[str, Any]]
    """ローカルラベル"""

    exastro_filter_group: GroupingInformation
    """グルーピング情報"""

    labels: dict[str, str]
    """ラベル情報"""


class TtlGroup(TypedDict):
    """時間集約グループ"""

    fetched_time: int
    """グループの先頭イベントのイベント取得日時"""

    end_time: int
    """グループの最大イベント有効日時"""

    first_event: Event
    """グループの先頭イベント"""

    remaining_events: list[Event]
    """グループの後続イベント"""


class ManageEvents:
    def __init__(self, ws_mongo: MONGOConnectWs, judge_time: int) -> None:
        self._label_master: dict[str, str] = {}
        """ラベルマスタ"""

        self.evaluated_event_groups: dict[str, dict[AttributeKey, list[TtlGroup]]] = {}
        """ルール確定グループ"""

        self.labeled_event_collection = ws_mongo.collection(
            mongoConst.LABELED_EVENT_COLLECTION
        )

        # イベントキャッシュの作成

        # 以下条件のイベントを取得
        undetermined_search_value = {
            "labels._exastro_timeout": "0",
            "labels._exastro_evaluated": "0",
            "labels._exastro_undetected": "0",
        }
        labeled_events = self.labeled_event_collection.find(
            undetermined_search_value
        ).sort(
            # 取得日時昇順にしておかないとグルーピングで先頭イベントが決定できなくなる
            "labels._exastro_fetched_time",
            1,
        )

        self.labeled_events_dict: dict[ObjectId, Event] = {}
        self.unevaluated_event_ids = set()

        for event in labeled_events:
            event[oaseConst.DF_LOCAL_LABLE_NAME] = {}
            event[oaseConst.DF_LOCAL_LABLE_NAME]["status"] = None

            check_result, event_status = self.check_event_status(
                int(judge_time),
                int(event["labels"]["_exastro_fetched_time"]),
                int(event["labels"]["_exastro_end_time"]),
            )
            if check_result is False:
                continue

            self.add_local_label(
                event,
                oaseConst.DF_LOCAL_LABLE_NAME,
                oaseConst.DF_LOCAL_LABLE_STATUS,
                event_status,
            )
            self.labeled_events_dict[event["_id"]] = event

            self.collect_unevaluated_event(event["_id"], event, initial=True)

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
            if str(event["labels"]["_exastro_timeout"]) != "0":
                continue
            # 処理済みイベント判定
            if str(event["labels"]["_exastro_evaluated"]) != "0":
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
                        # 「*」はワイルドカードとして扱う
                        if labels[key] == value or value == "*":
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
        count = len(self.unevaluated_event_ids)

        return count

    def collect_unevaluated_event(
        self, event_id: object, event: dict | None = None, *, initial: bool = False
    ):
        """未評価イベントを収集する。

        Args:
            event_id (Any): 収集するイベントのID。収集判定を行い評価不可能または評価済の場合収集結果から除外する。
            event (dict | None, optional): 収集判定に使うイベント。Noneの場合はキャッシュからイベントIDを取得する。デフォルトはNone。
            initial (bool, optional): Trueの場合初期化時と判断して収集対象外。デフォルトはFalse。
        """
        target_event = self.labeled_events_dict[event_id] if event is None else event
        match (target_event, initial):
            case (
                {
                    "labels": {
                        "_exastro_evaluated": "0",
                        "_exastro_timeout": "0",
                        "_exastro_undetected": "0",
                    }
                },
                _,
            ):
                # 評価可能(未タイムアウトかつ既知)で、未評価のものを集約
                self.unevaluated_event_ids.add(event_id)
            case (_, False):
                # 評価不可能または評価済の場合、初期化時以外は集約から除外
                self.unevaluated_event_ids.discard(event_id)
            case _:
                # 評価不可能または評価済の場合、初期化時以外はなにもしない
                pass

    def append_event(self, event):
        self.add_local_label(
            event,
            oaseConst.DF_LOCAL_LABLE_NAME,
            oaseConst.DF_LOCAL_LABLE_STATUS,
            oaseConst.DF_PROC_EVENT,
        )
        # キャッシュに保存
        self.labeled_events_dict[event["_id"]] = event
        self.collect_unevaluated_event(event["_id"], event)

    def get_events(self, event_id):
        if event_id not in self.labeled_events_dict:
            return False, {}
        return True, self.labeled_events_dict[event_id]

    def get_timeout_event(self):
        # タイムアウト（TTL*2）
        timeout_event_id_list = []
        for event_id, event in self.labeled_events_dict.items():
            if (
                event[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS]
                == oaseConst.DF_TIMEOUT_EVENT
            ):
                timeout_event_id_list.append(event_id)
        return timeout_event_id_list

    def get_post_proc_timeout_event(self):
        post_proc_timeout_event_ids: list[ObjectId] = []
        # イベント情報を通知用に返却する
        post_proc_timeout_event_rows = []
        # 処理後にタイムアウトにするイベントを抽出
        for event_id, event in self.labeled_events_dict.items():
            # タイムアウトしたイベントは登録されているのでスキップ
            if event["labels"]["_exastro_timeout"] != "0":
                continue
            # ルールにマッチしているイベント
            if event["labels"]["_exastro_evaluated"] != "0":
                continue
            # 処理後にタイムアウトにするイベント
            if (
                event[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS]
                == oaseConst.DF_POST_PROC_TIMEOUT_EVENT
            ):
                post_proc_timeout_event_ids.append(event_id)
                # 通知用には labels._exastro_timeout: 1 に変更したものを返す
                event["labels"]["_exastro_timeout"] = "1"
                post_proc_timeout_event_rows.append(event)

        return post_proc_timeout_event_ids, post_proc_timeout_event_rows

    def get_unused_event(self, incident_dict: dict, filterIDMap):
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
        filter_match_list = frozenset(
            id_value
            for id_value_list in incident_dict.values()
            for id_value in id_value_list
        )

        for event_id, event in self.labeled_events_dict.items():
            # タイムアウトしたイベントは登録されているのでスキップ
            if event["labels"]["_exastro_timeout"] != "0":
                continue
            # ルールにマッチしているイベント
            if event["labels"]["_exastro_evaluated"] != "0":
                continue

            # keyが削除されてincident_dictが空になっている場合（xor条件で両方のフィルターにマッチしていた場合）があるのでここで判定する
            if len(incident_dict) == 0:
                unused_event_ids.append(event_id)
                continue

            # フィルターにマッチしなかった
            if event_id not in filter_match_list:
                unused_event_ids.append(event_id)

        return unused_event_ids

    def insert_event(self, dict):
        return WriterProcessManager.insert_labeled_event_collection(dict)

    def update_label_flag(self, event_id_list, update_flag_dict):
        for event_id in event_id_list:
            if event_id not in self.labeled_events_dict:
                return False
            for key, value in update_flag_dict.items():
                self.labeled_events_dict[event_id]["labels"][key] = value

            self.collect_unevaluated_event(event_id)

            # MongoDB更新
            WriterProcessManager.update_labeled_event_collection(
                {"_id": event_id}, {"$set": {f"labels.{key}": value}}
            )

        return True

    def _update_label_force(
        self, event_id_list: list[str], update_labels_dict: dict[str]
    ):
        """イベントキャッシュに存在しないイベントでも強制的にラベルの更新を行う

        Args:
            event_id_list (list[str]): 更新対象のイベントIDリスト
            update_labels_dict (dict): 更新するラベル辞書
        """
        for event_id in event_id_list:
            # キャッシュに存在する場合はキャッシュも更新
            event = self.labeled_events_dict.get(event_id)
            if event:
                event["labels"].update(update_labels_dict)
                self.collect_unevaluated_event(event_id, event)

            # MongoDB更新
            WriterProcessManager.update_labeled_event_collection(
                {"_id": event_id},
                {
                    "$set": {
                        f"labels.{key}": value
                        for key, value in update_labels_dict.items()
                    }
                },
            )

    def init_label_master(self, label_master: dict[str, str]) -> None:
        """ラベルマスタを初期化する

        Args:
            label_master_dict (dict[str, str]): ラベルIDをキー、ラベル名を値とする辞書
        """
        self._label_master = label_master

    def init_grouping(self, judge_time: int, filter_map: dict[str, dict[str]]) -> None:
        """グルーピングの初期処理を行う

        有効な判定済み先頭イベントを取得し、ルール確定グループを初期化する

        Args:
            judge_time (int): 判定日時のタイムスタンプ
            filter_map (dict[str, dict[str, str]]): フィルターIDをキー、フィルター情報を値とする辞書
        """

        # フィルターに検索条件が「グルーピング」または「グルーピング（期間延長なし）」のものが含まれていない場合は処理しない
        if not any(
            filter_row["SEARCH_CONDITION_ID"]
            in (
                oaseConst.DF_SEARCH_CONDITION_GROUPING,
                oaseConst.DF_SEARCH_CONDITION_GROUPING_NO_PERIOD_EXTENSION,
            )
            for filter_row in filter_map.values()
        ):
            return

        # 有効な判定済み先頭イベントを取得
        evaluated_first_events = self.labeled_event_collection.find(
            {
                "$and": [
                    {
                        "labels._exastro_timeout": "0",
                        "labels._exastro_evaluated": "1",
                        "labels._exastro_undetected": "0",
                        "exastro_filter_group.is_first_event": "1",
                        "exastro_filter_group.filter_id": {
                            "$in": list(filter_map.keys())
                        },
                    },
                    # labels._exastro_end_time + TTL*2 > judge_time
                    {
                        "$expr": {
                            "$gt": [
                                {
                                    "$add": [
                                        "$labels._exastro_end_time",
                                        {
                                            "$multiply": [
                                                {
                                                    # 元のTTLが存在しない場合は、イベントの有効期間をTTLとして使用する
                                                    "$ifNull": [
                                                        "$exastro_filter_group.original_ttl",
                                                        {
                                                            "$subtract": [
                                                                "$labels._exastro_end_time",
                                                                "$labels._exastro_fetched_time",
                                                            ]
                                                        },
                                                    ]
                                                },
                                                2,
                                            ]
                                        },
                                    ]
                                },
                                judge_time,
                            ]
                        }
                    },
                ]
            }
        ).sort("labels._exastro_fetched_time", 1)

        for evaluated_first_event in evaluated_first_events:

            filter_row = filter_map[
                evaluated_first_event["exastro_filter_group"]["filter_id"]
            ]
            ttl_groups = self._get_ttl_groups(evaluated_first_event, filter_row)

            # 有効な判定済み先頭イベントなので必ず新規グループになる
            ttl_groups.append(self._create_new_ttl_group(evaluated_first_event))

    def grouping_event(self, event: Event, filter_row: dict[str]) -> bool:
        """イベントをグルーピングする

        ルール確定グループに対して以下の処理を行う
        - グルーピング条件に従って属性集約グループを作成・更新する
        - イベントの取得日時と有効期間に従って時間集約グループを作成・更新する

        Args:
            event (Event): グルーピング対象のイベント
            filter_row (dict[str]): フィルター情報

        Returns:
            bool:
                - True: イベントが先頭イベントになった場合
                - False: イベントが後続イベントになった場合
        """
        # ルール確定グループからフィルターIDでフィルター別属性集約グループを取得・作成する

        ttl_groups = self._get_ttl_groups(event, filter_row)

        # 既にグループに存在する場合はイベントが持つ情報を返し、何もしない
        if any(
            event["_id"] == group["first_event"]["_id"]
            or any(
                event["_id"] == remaining_event["_id"]
                for remaining_event in group["remaining_events"]
            )
            for group in ttl_groups
        ):
            return event["exastro_filter_group"]["is_first_event"]

        match ttl_groups:
            case [*_, _ as latest_group] if (
                event["labels"]["_exastro_fetched_time"] <= latest_group["end_time"]
            ):
                # 最新グループが取得でき、イベントがTTL内の場合は、後続イベントとして最新グループにイベントを追加
                self._append_ttl_group(latest_group, event, filter_row)
                is_first_event = False
            case _:
                # グループが空の場合、またはイベントがTTL外の場合は新規グループを作成
                latest_group = ManageEvents._create_new_ttl_group(event)
                ttl_groups.append(latest_group)
                is_first_event = True

        # イベントのグループ情報を追加
        group_info = event.setdefault("exastro_filter_group", GroupingInformation({}))
        group_info["filter_id"] = filter_row["FILTER_ID"]
        group_info["group_id"] = repr(
            latest_group["first_event"]["_id"]
        )  # exastro_eventsに合わせてシリアライズ
        group_info["is_first_event"] = "1" if is_first_event else "0"
        group_info["original_ttl"] = (
            event["labels"]["_exastro_end_time"]
            - event["labels"]["_exastro_fetched_time"]
        )
        # MongoDB更新
        WriterProcessManager.update_labeled_event_collection(
            {"_id": event["_id"]}, {"$set": {"exastro_filter_group": group_info}}
        )

        return is_first_event

    def set_timeout(self, events: Event | ObjectId | list[Event | ObjectId]) -> None:
        """イベントをタイムアウトに設定する"""
        self._disable_events(events, "timeout")

    def set_undetected(self, events: Event | ObjectId | list[Event | ObjectId]) -> None:
        """イベントを未知に設定する"""
        self._disable_events(events, "undetected")

    def _disable_events(
        self,
        events: Event | ObjectId | list[Event | ObjectId],
        disable_type: Literal["timeout", "undetected"],
    ) -> None:
        """イベントを無効(タイムアウトまたは未知)に設定する"""
        match events:
            case list():
                self.update_label_flag(
                    (
                        (event if isinstance(event, ObjectId) else event["_id"])
                        for event in events
                    ),
                    {f"_exastro_{disable_type}": "1"},
                )
                for e in events:
                    self._disable_event(e, disable_type)
            case event:
                self.update_label_flag(
                    (event,) if isinstance(event, ObjectId) else (event["_id"],),
                    {f"_exastro_{disable_type}": "1"},
                )
                self._disable_event(event, disable_type)

    def _disable_event(
        self,
        event_or_id: Event | ObjectId,
        disable_type: Literal["timeout", "undetected"],
    ) -> None:
        """イベントを無効(タイムアウトまたは未知)にする

        Args:
            event (Event): タイムアウトまたは未知に設定するイベント
            disable_type (Literal["timeout", "undetected"]): 無効化の種類
        """
        match event_or_id:
            # 必ずIDを見て管理下にあるイベントを取得する
            case (ObjectId() as event_id) | {"_id": event_id}:
                match self.get_events(event_id):
                    case False, _:
                        return
                    case True, target:
                        event = target
            case _:
                return

        # グルーピング情報が存在する場合はグルーピングを処理する
        if (grouping_info := event.get("exastro_filter_group")) is None:
            return
        group_id = grouping_info["group_id"]

        # 属性集約キーキャッシュが存在する場合は、ルール確定グループ側を削除する
        if (
            oaseConst.DF_LOCAL_LABLE_NAME in event
            and oaseConst.DF_LOCAL_LABLE_ATTRIBUTE_KEY
            in event[oaseConst.DF_LOCAL_LABLE_NAME]
        ):
            filter_row = {"FILTER_ID": grouping_info["filter_id"]}
            ttl_groups = self._get_ttl_groups(event, filter_row)
            for ttl_group in ttl_groups:
                # グループIDが一致しない場合はスキップ
                if (
                    group_id
                    != ttl_group["first_event"]["exastro_filter_group"]["group_id"]
                ):
                    continue
                # グループ削除
                ttl_groups.remove(ttl_group)
                # グループに含まれる後続イベントの無効化
                for remaining_event in ttl_group["remaining_events"]:
                    remaining_event["labels"][f"_exastro_{disable_type}"] = "1"
                    del remaining_event["exastro_filter_group"]
                break

        # グルーピング情報削除、無効のMongoDB更新
        WriterProcessManager.update_labeled_event_collection(
            {
                "exastro_filter_group.group_id": group_id,
                # イベントのTTL(先頭イベントの場合、グループのTTL相当)内のものに限定
                "labels._exastro_fetched_time": {
                    "$gte": event["labels"]["_exastro_fetched_time"],
                    "$lte": event["labels"]["_exastro_end_time"],
                },
                "labels._exastro_end_time": {
                    "$gte": event["labels"]["_exastro_fetched_time"],
                    "$lte": event["labels"]["_exastro_end_time"],
                },
            },
            {
                "$unset": {"exastro_filter_group": ""},
                "$set": {
                    f"labels._exastro_{disable_type}": "1",
                },
            },
        )

    @staticmethod
    def _create_new_ttl_group(event: Event) -> TtlGroup:
        """新しいグループを作成する

        Args:
            event (Event): グループに追加するイベント

        Returns:
            Group: 新しいグループ
        """
        return {
            "fetched_time": event["labels"]["_exastro_fetched_time"],
            "end_time": event["labels"]["_exastro_end_time"],
            "first_event": event,
            "remaining_events": [],
        }

    def _append_ttl_group(self, ttl_group: TtlGroup, event: Event, filter_row: dict[str]) -> None:
        """グループにイベントを追加する

        Args:
            ttl_group (Group): グループ
            event (Event): グループに追加するイベント
        """
        ttl_group["remaining_events"].append(event)

        # 「グルーピング（期間延長なし）」の場合は終了時間の更新を行わない
        if filter_row["SEARCH_CONDITION_ID"] == oaseConst.DF_SEARCH_CONDITION_GROUPING_NO_PERIOD_EXTENSION:
            return

        # グループの終了時間の変更を確認
        new_end_time = event["labels"]["_exastro_end_time"]
        if new_end_time > ttl_group["end_time"]:
            # グループの終了時間を更新
            ttl_group["end_time"] = new_end_time
            # 先頭イベントの終了時間を更新(イベントキャッシュに存在しないケースも強制更新)
            self._update_label_force(
                [ttl_group["first_event"]["_id"]], {"_exastro_end_time": new_end_time}
            )

    def _get_attribute_key(self, event: Event, filter_row: dict[str]) -> AttributeKey:
        """イベントから属性集約キーを取得する

        Args:
            event (Event): イベント
            filter_row (dict[str]): フィルター情報

        Returns:
            AttributeKey: 属性集約キー
        """

        # グループキーがキャッシュに存在する場合そこから取り出す
        local_label: dict[str, dict[str, AttributeKey]] = event.setdefault(
            oaseConst.DF_LOCAL_LABLE_NAME, {}
        )
        attribute_key_filter_map = local_label.setdefault(
            oaseConst.DF_LOCAL_LABLE_ATTRIBUTE_KEY, {}
        )
        attribute_key = attribute_key_filter_map.get(filter_row["FILTER_ID"])
        if attribute_key:
            return attribute_key

        # キャッシュに存在しない場合はイベントのラベルから生成する
        if filter_row is None:
            raise ValueError("filter_row is required when attribute_key is not cached")
        labels: dict[str] | None = event.get("labels")
        if labels is None:
            # IncidentDictに未登録のフィルターは空イベントを返すので、
            return None
        group_condition_labels: list[str] = [
            getIDtoLabelName(self._label_master, label_key)
            for label_key in json.loads(filter_row["GROUP_LABEL_KEY_IDS"])["id"]
        ]
        if filter_row["GROUP_CONDITION_ID"] == oaseConst.DF_GROUP_CONDITION_ID_TARGET:
            # 「を対象とする」の場合、ラベルに含まれる属性のみをキーとする
            attribute_key = frozenset(
                (key, value)
                for (key, value) in labels.items()
                if key in group_condition_labels
            )
        else:
            # 「以外を対象とする」の場合、ラベルに含まれない属性のみをキーとする
            attribute_key = frozenset(
                (key, value)
                for (key, value) in labels.items()
                # システム属性である_exastroで始まる属性は除外する(_exastro_hostは除外対象外)
                if not (
                    key in group_condition_labels
                    or re.match("^_exastro(?!_host$)", key)
                )
            )
        # キャッシュに保存
        attribute_key_filter_map[filter_row["FILTER_ID"]] = attribute_key
        return attribute_key

    def is_first_event_when_grouping(self, event: Event, filter_row: dict[str]) -> bool:
        """イベントをグルーピングした際に先頭イベントになるか判定する

        Args:
            event (Event): グルーピングするイベント
            group_condition_id (Literal[&quot;1&quot;, &quot;2&quot;]): グルーピング条件ID
            group_condition_labels (list[str]): グルーピング条件ラベル

        Returns:
            bool: 先頭イベントになる場合True、ならない場合False
        """

        ttl_groups = self._get_ttl_groups(event, filter_row)

        # 既にグループに存在する場合はイベントが持つ情報を返す
        if any(
            event["_id"] == group["first_event"]["_id"]
            or any(event["_id"] == e["_id"] for e in group["remaining_events"])
            for group in ttl_groups
        ):
            return event["exastro_filter_group"]["is_first_event"] == "1"

        match ttl_groups:
            case [*_, _ as latest_group] if (
                event["labels"]["_exastro_fetched_time"] <= latest_group["end_time"]
            ):
                return False
            case _:
                return True

    def _get_ttl_groups(self, event: Event, filter_row: dict[str]) -> list[TtlGroup]:
        """イベントとフィルターに対応する時間集約グループリストを取得する

        Args:
            event (Event): イベント
            filter_row (dict[str]): フィルター

        Returns:
            list[Group]: 時間集約グループリスト
        """

        filter_id = filter_row["FILTER_ID"]

        filter_groups = self.evaluated_event_groups.setdefault(filter_id, {})

        # イベントから属性集約グループキーを取得
        attribute_group_key = self._get_attribute_key(event, filter_row)

        ttl_groups = filter_groups.setdefault(attribute_group_key, [])
        return ttl_groups

    def print_event(self):
        for event_id, event in self.labeled_events_dict.items():
            id = str(event["_id"])
            evaluated = str(event["labels"]["_exastro_evaluated"])
            undetected = str(event["labels"]["_exastro_undetected"])
            timeout = str(event["labels"]["_exastro_timeout"])
            localsts = str(
                event[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS]
            )
            status = "Unknown"  # 不明
            if evaluated == "0" and undetected == "1" and timeout == "0":
                status = "Undetected        "  # 未知
            elif evaluated == "0" and undetected == "0" and timeout == "1":
                status = "Timeout"  # タイムアウト
            elif evaluated == "0" and undetected == "0" and timeout == "0":
                status = "Currently no action required"  # 今は対応不要
            elif evaluated == "1" and undetected == "0" and timeout == "0":
                status = "Action required      "  # 要対応
            if localsts == oaseConst.DF_PROC_EVENT:
                localsts = "Process target:〇"  # 処理対象:〇
            elif localsts == oaseConst.DF_POST_PROC_TIMEOUT_EVENT:
                localsts = "Process target. Post-process timeout:●"  # 処理対象　処理後タイムアウト:●
            elif localsts == oaseConst.DF_TIMEOUT_EVENT:
                localsts = "Timeout"  # タイムアウト
            elif localsts == oaseConst.DF_NOT_PROC_EVENT:
                localsts = "Not target"  # 対象外
            tmp_msg = "id:{} status:{}  _exastro_evaluated:{}  _exastro_undetected:{}  _exastro_timeout:{} local_status:{}".format(
                id, status, evaluated, undetected, timeout, localsts
            )
            g.applogger.info(self.addline_msg("{}".format(tmp_msg)))  # noqa: F405

    def addline_msg(self, msg=""):
        info = inspect.getouterframes(inspect.currentframe())[1]
        msg_line = "{} ({}:{})".format(
            msg, os.path.basename(info.filename), info.lineno
        )
        return msg_line

    def get_dudup_eventrow(self, wsDb, judge_time: int) -> list[dict]:
        """新規(統合時) TTL切れの通知対象となるイベントをフィルタする

        Args:
            wsDb (DBConnectWs): MariaDBのコネクション
            judge_time (int): 判定日時のタイムスタンプ

        Returns:
            List: 新規(統合時) TTL切れの通知対象となるイベントを要素に持つリスト
        """
        # 新規(統合時)の通知が必要かどうかを確認する
        organization_id = g.get('ORGANIZATION_ID')
        workspace_id = g.get('WORKSPACE_ID')
        host_name = os.environ.get('PLATFORM_API_HOST')
        port = os.environ.get('PLATFORM_API_PORT')
        user_id = g.get('USER_ID')
        language = g.get('LANGUAGE')

        header_para = {
            "User-Id": user_id,
            "Language": language
        }
        # 新規(統合時)が有効な通知先のみ取得するようにクエリ指定
        query_params = {}
        query_params["event_type_true"] = OASE.DESTINATION_ID_FETCH_CONDITION[OASENotificationType.DUPLICATE]
        # API呼出
        api_url = f"http://{host_name}:{port}/internal-api/{organization_id}/platform/workspaces/{workspace_id}/settings/notifications"
        s = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.5)
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))
        # 後続処理遅延につながるためタイムアウトは1秒と短めに設定
        request_response = s.request(method='GET', url=api_url, timeout=1, headers=header_para, params=query_params)
        response_data = request_response.json()
        if request_response.status_code != 200:
            # 200応答が来なかったら処理スキップ(次回処理で実行することを期待)
            g.applogger.info(g.appmsg.get_log_message('999-00005', [api_url, response_data]))
            return []
        else:
            # 該当する通知先が無ければ処理スキップ
            if 'data' in response_data and len(response_data['data']) == 0:
                g.applogger.debug("No Notification settings for new_consolidated events. Skipping.")
                return []
        # 冗長グループを確認するため重複排除設定を確認
        deduplication_settings = wsDb.table_select(
            oaseConst.T_OASE_DEDUPLICATION_SETTINGS,
            "WHERE DISUSE_FLAG='0' ORDER BY SETTING_PRIORITY, DEDUPLICATION_SETTING_NAME"
        )
        # 重複排除設定が無いなら処理自体をスキップ
        if len(deduplication_settings) == 0:
            g.applogger.debug("No records for deduplication settings. Skipping.")
            return []

        # イベント検索処理
        eventrow = []
        # TTLを確認するためにイベント収集設定を取得
        collection_settings = wsDb.table_select(
            oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS,
            "WHERE DISUSE_FLAG='0'"
        )
        # collection_settings_ttlはイベント収集設定のUUIDをキー、TTLを値とする辞書
        collection_settings_ttl = {}
        for collection_setting in collection_settings:
            collection_settings_ttl[collection_setting["EVENT_COLLECTION_SETTINGS_ID"]] = collection_setting["TTL"]
        # Mongoクエリに使用する辞書準備：TTL値をキーとし、該当のイベント収集設定UUIDリストを値とする
        ttl_unique_dict = {}
        for deduplication_setting in deduplication_settings:
            # redundancy_idsは重複排除設定の同一冗長グループの、イベント収集設定のUUIDのリスト
            redundancy_ids = json.loads(deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"])["id"]
            # 重複排除設定の冗長グループに2つ以上のイベント収集設定が登録されている場合のみ、通知対象となるため処理
            if len(redundancy_ids) > 1:
                for uuid in redundancy_ids:
                    # イベント収集設定のUUIDからTTL取得
                    # 不正なUUID(ID連携失敗)の場合は取得しない
                    if uuid in collection_settings_ttl:
                        ttl_unique_dict.setdefault(int(collection_settings_ttl[uuid]), []).append(uuid)
        # TTL値で昇順ソート
        ttl_unique_dict_asc = {key: ttl_unique_dict[key] for key in sorted(ttl_unique_dict.keys())}
        # TTL値で昇順ソートにした後、20秒以上TTLが空いてないなら間引きする(収集設定は前の要素に詰める)
        ttl_unique_dict_keys = list(ttl_unique_dict_asc.keys())
        ttl_merged_dict = {}
        if len(ttl_unique_dict_keys) > 0:
            # 最初の要素は基準点として登録
            first_key = ttl_unique_dict_keys[0]
            ttl_merged_dict[first_key] = ttl_unique_dict_asc[first_key]
            last_merged_key = first_key
            for i in range(1, len(ttl_unique_dict_keys)):
                current_key = ttl_unique_dict_keys[i]
                # 前回登録したTTLキーから20秒以上空いている場合のみ登録
                if (current_key - last_merged_key) >= 20:
                    ttl_merged_dict[current_key] = ttl_unique_dict_asc[current_key]
                    last_merged_key = current_key
                else:
                    # 20秒未満の場合は前回登録したTTLキーにマージする
                    ttl_merged_dict[last_merged_key].extend(ttl_unique_dict_asc[current_key])
        # TTL値毎にMongoで検索→更新を実施する
        for ttl, collection_settings_IdList in ttl_merged_dict.items():
            event_ids = []
            # 以下の条件のイベントを取得
            deduplication_search_value = {
                "exastro_duplicate_collection_settings_ids": {"$exists": True, "$not": {"$size": 0}},
                "labels._exastro_end_time": {"$gte": (int(judge_time) - int(ttl) * 2), "$lte": int(judge_time)},
                "exastro_dup_notification_queue": {"$exists": False},
                "labels._exastro_event_collection_settings_id": {"$in": collection_settings_IdList}
            }
            # 最低限、重複排除に関係あるイベントを取得
            # 遅延書き込みが終了してから取得
            WriterProcessManager.flush_buffer()
            target_events = self.labeled_event_collection.find(
                deduplication_search_value
            ).sort("labels._exastro_fetched_time", 1)  # 取得日時昇順

            for event in target_events:
                if deduplication_timeout_filter(deduplication_settings, event) is True:
                    # MongoDBの更新対象にする
                    event_ids.append(event["_id"])
                    # 通知用に返却するイベントデータも labels._exastro_dup_notification_queue: 1 に変更する
                    event["exastro_dup_notification_queue"] = "1"
                    eventrow.append(event)
            # TTL設定値毎にupdateManyしてMongo側も更新かける
            if len(event_ids) > 0:
                # WriterProcess経由で更新
                WriterProcessManager.update_many_labeled_event_collection(
                    {"_id": {"$in": event_ids}},
                    {"$set": {"exastro_dup_notification_queue": "1"}},
                )
        return eventrow
