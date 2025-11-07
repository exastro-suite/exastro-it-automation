#   Copyright 2025 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from collections.abc import Iterable
import datetime
import json
from typing import Literal, Set, overload
import uuid
from bson import ObjectId

from common_libs.oase.const import oaseConst

# ===== グローバル変数 =====

judge_time = 1760486660

# V_OASE_LABEL_KEY_GROUPのラベルキー名からラベルキーIDへのマッピング
V_OASE_LABEL_KEY_GROUP = {
    # システム固定ラベル（T_OASE_LABEL_KEY_FIXED より）
    "_exastro_event_collection_settings_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01",
    "_exastro_fetched_time": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02",
    "_exastro_end_time": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx03",
    "_exastro_undetected": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx04",
    "_exastro_evaluated": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx05",
    "_exastro_timeout": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx06",
    "_exastro_type": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07",
    "_exastro_rule_name": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx08",
    "_exastro_host": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09",
    "_exastro_agent_name": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10",
    "_exastro_agent_version": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx11",
    # 「新規イベント通知済み」だがT_OASE_LABEL_KEY_FIXEDに存在しない
    # "_exastro_checked": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx12",
    # テスト用カスタムラベル
    "event_id": "cfaaf25d-a97e-4f8c-a76d-2ef04b250448",
    "grp_label_1": "de17423c-c75b-4efa-af0f-1779b56f65f2",
    "grp_label_2": "8120ba46-2c66-43d3-9e4c-2eab00c85630",
    "grp_label_3": "b274a4a0-0522-44f6-9ed3-85e57ab37a0d",
    "test_case": "4ae00b24-b194-40b8-a6a8-e57951181959",
    "A_event_id": "f03dc6d8-25ba-4296-89e5-08342b615a66",
    "type": "e2f3d1f2-4a5f-2e4f-2e4f-4a8f4a8f4a8f",
    "mode": "f4a8f4a8-f4a8-f4a8-f4a8-f4a8f4a8f4a8",
    "clock": "7de41b08-3df7-4e5a-80df-f26fdb520578",
    "eventid": "d40efb31-3080-40e3-88c4-df9cf452dce4",
    "excluded_flg": "bd4c4bb0-ed6f-4fe1-ab80-1459bcdb11cd",
    "msg": "9909015e-845e-4e5f-a397-d73441c1043f",
    "node": "9db8ef62-f915-424c-af3a-7a731a3c5f13",
    "service": "a7418cae-5029-4580-997f-f41a1b2a14d6",
    "severity": "ef992af9-4079-49bf-b9ca-eed079ebfed3",
    "status": "0a6ded16-7f3b-4c9d-9fde-781b5609acc2",
}

# ===== ダミーデータ作成関数 =====


def deep_merged(dict1: dict, dict2: dict):
    merged = dict1.copy()
    for key2, value2 in dict2.items():
        value1 = merged.get(key2)
        if isinstance(value1, dict) and isinstance(value2, dict):
            merged[key2] = deep_merged(value1, value2)
        else:
            merged[key2] = value2
    return merged


def _get_filter_id(filter_id_or_row: str | dict) -> str:
    return (
        filter_id_or_row
        if isinstance(filter_id_or_row, str)
        else filter_id_or_row["FILTER_ID"]
    )


def get_label_key_id(label_name: str) -> str:
    """ラベル名からラベルキーを逆引き"""
    return V_OASE_LABEL_KEY_GROUP.get(label_name, f"unknown_label_{label_name}")


def create_event(
    test_case: str,
    event_id: str,
    fetched_time: int = judge_time,
    end_time: int | None = None,
    *,
    fetched_time_offset: int = 0,
    ttl: int = 10,
    id: ObjectId | bytes | str | None = None,
    exastro_type: str = "event",
    undetected: Literal["0", "1"] = "0",
    evaluated: Literal["0", "1"] = "0",
    timeout: Literal["0", "1"] = "0",
    custom_labels: dict | None = None,
    grouping_filter: str | dict | None = None,
):
    """テスト用イベントデータを作成"""
    fetched_time += fetched_time_offset
    if end_time is None:
        end_time = fetched_time + ttl
    event_content = {"test_case": test_case, "event_id": event_id}
    labels = custom_labels or {}
    labels_and_system_labels = {
        "_exastro_event_collection_settings_id": str(uuid.uuid4()),
        "_exastro_checked": "0",
        "_exastro_type": exastro_type,
        "_exastro_timeout": timeout,
        "_exastro_evaluated": evaluated,
        "_exastro_undetected": undetected,
        "_exastro_fetched_time": fetched_time,
        "_exastro_end_time": end_time,
        "_exastro_agent_name": "Unknown",
        "_exastro_agent_version": "Unknown",
        **labels,
    }

    event = {
        "_id": id if id else ObjectId(id),
        "event": event_content,
        "labels": labels_and_system_labels,
        "exastro_created_at": datetime.datetime.now(datetime.timezone.utc),
        "exastro_labeling_settings": (
            {label_name: str(uuid.uuid4()) for label_name in labels}
        ),
        "exastro_label_key_inputs": (
            {label_name: get_label_key_id(label_name) for label_name in labels}
        ),
    }

    # グルーピングを作る場合は必ず先頭イベント
    if grouping_filter is not None:
        event["exastro_filter_group"] = {
            "filter_id": _get_filter_id(grouping_filter),
            "group_id": repr(event["_id"]),
            "is_first_event": True,
            "original_ttl": end_time - fetched_time,
        }
    return event


def create_filter_condition(
    label_name: str, condition_type: Literal["1", "2"], condition_value: str
) -> dict:
    return {
        "label_name": get_label_key_id(label_name),
        "condition_type": condition_type,
        "condition_value": condition_value,
    }


@overload
def create_filter_row(
    search_condition_id: Literal["1", "2"],
    conditions: Iterable[tuple[str, Literal["1", "2"], str]],
    *,
    filter_id: str | None = None,
) -> dict:
    """テスト用フィルタデータを作成"""
    pass


@overload
def create_filter_row(
    search_condition_id: Literal["3"],
    conditions: Iterable[tuple[str, Literal["1", "2"], str]],
    group_condition_id: Literal["1", "2"],
    group_label_names: list[str],
    *,
    filter_id: str | None = None,
) -> dict:
    """テスト用フィルタデータを作成"""
    pass


def create_filter_row(
    search_condition_id: Literal["1", "2", "3"],
    search_conditions: Iterable[tuple[str, Literal["1", "2"], str]] | None,
    group_condition_id: Literal["1", "2"] | None = None,
    group_label_names: list[str] | None = None,
    *,
    filter_id: str | None = None,
) -> dict:
    """テスト用フィルタデータを作成"""
    return {
        "FILTER_ID": filter_id or str(uuid.uuid4()),
        "DISUSE_FLAG": 0,
        "AVAILABLE_FLAG": 1,
        "FILTER_CONDITION_JSON": (
            json.dumps(
                [create_filter_condition(*condition) for condition in search_conditions]
            )
            if search_conditions
            else None
        ),
        "SEARCH_CONDITION_ID": search_condition_id,
        # GROUP_LABEL_KEY_IDSのデータ形式はidフィールドにLABEL_KEY_IDのリストを持つ辞書をJSON文字列化したもの
        "GROUP_LABEL_KEY_IDS": json.dumps(
            {"id": [get_label_key_id(label_name) for label_name in group_label_names]}
            if group_label_names
            else {}
        ),
        "GROUP_CONDITION_ID": group_condition_id,
    }


@overload
def create_rule_row(
    priority: int,
    rule_name: str,
    filter: str | dict,
    /,
    action_id: str | None = None,
    rule_id: str | None = None,
    before_notification: tuple[str, str] | None = None,
    after_notification: tuple[str, str] | None = None,
    conclusion_label_inheritance_flag: Set[Literal["action", "event"]] = frozenset(),
    conclusion_label_settings: list[dict[str, str]] | None = None,
    conclusion_ttl: int = 10,
) -> dict:
    """テスト用ルールデータを作成"""
    pass


@overload
def create_rule_row(
    priority: int,
    rule_name: str,
    filter: tuple[str | dict, str | dict],
    /,
    filter_operator: Literal["1", "2", "3"],
    action_id: str | None = None,
    rule_id: str | None = None,
    before_notification: tuple[str, str] | None = None,
    after_notification: tuple[str, str] | None = None,
    conclusion_label_inheritance_flag: Set[Literal["action", "event"]] = frozenset(),
    conclusion_label_settings: list[dict[str, str]] | None = None,
    conclusion_ttl: int = 10,
) -> dict:
    """テスト用ルールデータを作成"""
    pass


def create_rule_row(
    priority: int,
    rule_name: str,
    filter: str | dict | tuple[str | dict, str | dict],
    /,
    filter_operator: Literal["", "1", "2", "3"] = oaseConst.DF_OPE_NONE,
    action_id: str | None = None,
    rule_id: str | None = None,
    before_notification: tuple[str, str] | None = None,
    after_notification: tuple[str, str] | None = None,
    conclusion_label_inheritance_flag: Set[Literal["action", "event"]] = frozenset(),
    conclusion_label_settings: list[dict[str, str]] | None = None,
    conclusion_ttl: int = 10,
) -> dict:
    """テスト用ルールデータを作成"""

    return {
        "RULE_ID": rule_id or str(uuid.uuid4()),
        "DISUSE_FLAG": 0,
        "AVAILABLE_FLAG": 1,
        "RULE_PRIORITY": priority,
        "RULE_NAME": rule_name,
        "FILTER_A": (
            _get_filter_id(filter)
            if filter_operator == oaseConst.DF_OPE_NONE
            else _get_filter_id(filter[0])
        ),
        "FILTER_OPERATOR": filter_operator,
        "FILTER_B": (
            None
            if filter_operator == oaseConst.DF_OPE_NONE
            else _get_filter_id(filter[1])
        ),
        "ACTION_ID": action_id,
        "BEFORE_NOTIFICATION": before_notification[0] if before_notification else None,
        "BEFORE_NOTIFICATION_DESTINATION": (
            before_notification[1] if before_notification else None
        ),
        "AFTER_NOTIFICATION": after_notification[0] if after_notification else None,
        "AFTER_NOTIFICATION_DESTINATION": (
            after_notification[1] if after_notification else None
        ),
        "ACTION_LABEL_INHERITANCE_FLAG": (
            "1" if "action" in conclusion_label_inheritance_flag else "0"
        ),
        "EVENT_LABEL_INHERITANCE_FLAG": (
            "1" if "event" in conclusion_label_inheritance_flag else "0"
        ),
        "CONCLUSION_LABEL_SETTINGS": json.dumps(
            [
                {"label_key": get_label_key_id(label_name), "label_value": label_value}
                for label_setting in conclusion_label_settings
                for label_name, label_value in label_setting.items()
            ]
            if conclusion_label_settings
            else []
        ),
        "TTL": conclusion_ttl,
        "RULE_LABEL_NAME": rule_name,
    }


def run_test_pattern(
    g,
    ws_db,
    mock_mongo,
    mock_datetime,
    test_events,
    filters,
    rules,
    actions: list[dict] | None = None,
    # テストの基準時間
    test_epoch: int = judge_time,
    # 実行間隔
    interval: int = 10,
    # 前方の実行回数
    before_epoch_runs: int = 3,
    # 後方の実行回数
    after_epoch_runs: int = 4,
    # 一時情報の集約(デバッグ用)
    local_label_collection: dict[int, dict[ObjectId, dict[str] | None]] | None = None,
):
    """共通テストロジック"""
    import backyard_main as bm

    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = filters
    ws_db.table_data["T_OASE_RULE"] = rules
    ws_db.table_data["T_OASE_ACTION"] = actions or []

    start_time = test_epoch - interval * before_epoch_runs
    end_time = test_epoch + interval * after_epoch_runs
    for jt in range(start_time, end_time + 1, interval):
        mock_mongo.test_events = [
            event
            for event in test_events
            if event["labels"]["_exastro_fetched_time"] <= jt
        ]
        mock_datetime.datetime.now.return_value.timestamp.return_value = jt
        bm.backyard_main("org1", "ws1")
        for event in mock_mongo.test_events:
            # 一時情報が残っているので削除する
            local_label_data = event.pop(oaseConst.DF_LOCAL_LABLE_NAME, None)
            if local_label_collection is not None:
                local_label_collection.setdefault(jt, {})[
                    event["_id"]
                ] = local_label_data
            # 追加された結論イベントをテストイベントに含める
            if event not in test_events:
                test_events.append(event)

    # エラーログが出ていないことを確認
    tracebacks = [log for _, log in g.applogger.logs if "Traceback" in log]
    for traceback in tracebacks:
        print(traceback)
    assert not tracebacks
