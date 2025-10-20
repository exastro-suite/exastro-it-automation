from collections.abc import Iterable, Set
import datetime
import json
from typing import Literal, overload
import uuid
import pytest
import os
from unittest.mock import patch, Mock

from bson import ObjectId
from flask import Flask, g

import backyard_main as bm
from common_libs.notification.sub_classes.oase import OASENotificationType
import common_libs.oase.manage_events as clome
from common_libs.oase.manage_events import ManageEvents
from common_libs.oase.const import oaseConst
import libs.action as la
from libs.action import Action

# ===== ダミーデータ作成関数 =====


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
    fetched_time: int,
    end_time: int,
    *,
    id: ObjectId | bytes | str | None = None,
    exastro_type: str = "event",
    undetected: Literal["0", "1"] = "0",
    evaluated: Literal["0", "1"] = "0",
    timeout: Literal["0", "1"] = "0",
    custom_labels: dict | None = None,
    grouping_filter: str | dict | None = None,
):
    """テスト用イベントデータを作成"""
    labels = {"test_case": test_case, "event_id": event_id, **(custom_labels or {})}
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
        "event": labels,
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
    conditions: Iterable[tuple[str, Literal["1", "2"], str]],
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
        "FILTER_CONDITION_JSON": json.dumps(
            [create_filter_condition(*condition) for condition in conditions]
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
    filter: str,
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
    filter: tuple[str, str],
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
                {get_label_key_id(label_name): template}
                for label_name, template in conclusion_label_settings
            ]
            if conclusion_label_settings
            else []
        ),
        "TTL": conclusion_ttl,
        "RULE_LABEL_NAME": rule_name,
    }


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
}


# ===== 共通ダミー =====


class DummyDB:
    """データベース接続(DBConnectWs)のダミークラス"""

    def __init__(self, workspace_id):
        self.workspace_id = workspace_id
        self.ended = False
        self.disconnected = False
        self.args_end = None

        # テーブル別のカスタムデータ（テストでオーバーライド可能）
        self.table_data = {}

        # マスタ類の初期値
        self.table_data["V_OASE_LABEL_KEY_GROUP"] = [
            {
                "LABEL_KEY_ID": label_key_id,
                "LABEL_KEY_NAME": label_key_name,
                "DISUSE_FLAG": 0,
            }
            for label_key_name, label_key_id in V_OASE_LABEL_KEY_GROUP.items()
        ]

    def db_transaction_end(self, flag):
        """トランザクション終了"""
        self.ended = True
        self.args_end = flag

    def db_disconnect(self):
        """データベース切断"""
        self.disconnected = True

    def table_select(self, table, where, params):
        """テーブル選択"""
        return self.table_data[table]


class MockMONGOConnectWs:
    """MONGOConnectWsのモッククラス"""

    def __init__(self, test_events=None):
        """
        コンストラクタ
        Args:
            test_events: テスト用イベントデータ
        """
        self.test_events = test_events or {}
        self.update_calls = []
        self.insert_calls = []
        self.disconnected = False

    def disconnect(self):
        """接続切断"""
        self.disconnected = True

    def collection(self, collection_name):
        """コレクション取得"""
        return MockCollection(collection_name, self)


class MockCollection:
    """MongoDBコレクションのモッククラス"""

    def __init__(self, collection_name, mongo_instance):
        self.collection_name = collection_name
        self.mongo_instance = mongo_instance

    def find(self, query=None, projection=None):
        """find操作のモック"""
        return MockCursor(self.mongo_instance.test_events, query)

    def update_one(self, query, update_data):
        """update_one操作のモック"""
        self.mongo_instance.update_calls.append((query, update_data))
        return True

    def insert_one(self, document):
        """insert_one操作のモック"""
        self.mongo_instance.insert_calls.append(document)
        return True


class MockCursor:
    """MongoDBカーソルのモッククラス"""

    def __init__(self, test_events, query=None):
        self.test_events = test_events
        self.query = query or {}
        if isinstance(test_events, dict):
            self._events = list(test_events.values())
        elif isinstance(test_events, list):
            self._events = test_events
        else:
            self._events = []

    def sort(self, field, direction):
        """ソート処理のモック"""
        # 簡単なソート実装（実際のテストではより詳細な実装が必要な場合もある）
        if field == "labels._exastro_fetched_time":
            self._events.sort(
                key=lambda x: int(x.get("labels", {}).get("_exastro_fetched_time", 0))
            )
        return self

    def __iter__(self):
        """イテレータ"""
        return iter(self._filter_events())

    def _filter_events(self):
        """クエリに基づいてイベントをフィルタリング"""
        filtered_events = []
        for event in self._events:
            if self._matches_query(event, self.query):
                filtered_events.append(event)
        return filtered_events

    def _matches_query(self, event, query):
        """イベントがクエリにマッチするかチェック"""
        if not query:
            return True

        for joined_key, expression in query.items():
            remain_keys = joined_key.split(".")
            target = event
            # キーがネストされている場合に対応
            while remain_keys:
                key, *remain_keys = remain_keys
                if not isinstance(target, dict) or key not in target:
                    return False
                target = target[key]
                if not remain_keys and not self._match_query_expression(
                    target, expression
                ):
                    return False

        return True

    @staticmethod
    def _match_query_expression(value, expression):
        """クエリ表現にマッチするかチェック"""
        if not isinstance(expression, dict):
            return value == expression
        if expression.get("$in"):
            return value in expression["$in"]
        if expression.get("$gte"):
            return value >= expression["$gte"]
        return False


class DummyAppMsg:
    def get_log_message(self, code, params):
        # ログ本文はテストで詳細検証しないので簡略
        return f"{code}:{params}"


class DummyLogger:
    def __init__(self):
        self.logs = []

    def debug(self, msg):
        self.logs.append(("debug", msg))

    def info(self, msg):
        self.logs.append(("info", msg))

    def warning(self, msg):
        self.logs.append(("warning", msg))


class DummyAction:
    """Actionクラスのダミー実装"""

    def __init__(self, ws_db=None, event_obj=None):
        """コンストラクタ"""
        self.ws_db = ws_db
        self.event_obj = event_obj


class DummyActionStatusMonitor:
    """ActionStatusMonitorクラスのダミー実装"""

    def __init__(self, ws_db=None, event_obj=None):
        """コンストラクタ"""
        self.called = []
        self.ws_db = ws_db
        self.event_obj = event_obj
        self.match_called = False
        self.exec_called = False

    def check_rule_match(self, action_obj):
        """ルールマッチチェック"""
        self.called.append("match")
        self.match_called = True
        return None

    def check_executing(self):
        """実行中チェック"""
        self.called.append("exec")
        self.exec_called = True
        return None

    def checkRuleMatch(self, action_obj):
        """ルールマッチチェック（キャメルケース版）"""
        return self.check_rule_match(action_obj)

    def checkExecuting(self):
        """実行中チェック（キャメルケース版）"""
        return self.check_executing()

    def __getattr__(self, name):
        """属性アクセス対応"""
        if name == "checkRuleMatch":
            return self.check_rule_match
        if name == "checkExecuting":
            return self.check_executing
        raise AttributeError(name)


# ===== フィクスチャー =====


@pytest.fixture
def patch_global_g(monkeypatch):
    """グローバル変数gをパッチ（Flaskアプリケーションコンテキスト付き）"""
    # Flaskアプリのコンテキストを作成
    flask_app = Flask(__name__)
    with flask_app.app_context():
        # gオブジェクト全体をモックする
        monkeypatch.setattr("flask.g", g, raising=False)

        # gの属性を個別に設定する
        g.LANGUAGE = "ja"
        g.USER_ID = "mock_user_id"
        g.SERVICE_NAME = "mock_service"
        g.WORKSPACE_ID = "mock_workspace_id"
        g.ORGANIZATION_ID = "mock_org_id"

        # g.apploggerとg.appmsgをモックする
        g.applogger = DummyLogger()
        g.appmsg = DummyAppMsg()

        # g.get()メソッドをモックし、キーに応じて値を返すようにする
        def mock_get(key):
            return {
                "ORGANIZATION_ID": g.ORGANIZATION_ID,
                "WORKSPACE_ID": g.WORKSPACE_ID,
                "USER_ID": g.USER_ID,
                "LANGUAGE": g.LANGUAGE,
            }.get(key)

        g.get = mock_get

        yield g


@pytest.fixture
def patch_datetime(monkeypatch):
    """datetime.datetime.nowをパッチして固定値を返す"""
    mock_datetime = Mock()
    mock_datetime.now.return_value.timestamp.return_value = (
        1640995200  # 2022-01-01 00:00:00
    )
    monkeypatch.setattr(bm, "datetime", mock_datetime)
    return mock_datetime


@pytest.fixture
def patch_notification_and_writer(monkeypatch):
    """通知とライタープロセスをパッチ"""

    def deep_merged(dict1: dict, dict2: dict):
        merged = dict1.copy()
        for key2, value2 in dict2.items():
            value1 = merged.get(key2)
            if isinstance(value1, dict) and isinstance(value2, dict):
                merged[key2] = deep_merged(value1, value2)
            else:
                merged[key2] = value2
        return merged

    calls = {
        "notification_start_ws": 0,
        "notification_finish_ws": 0,
        "writer_start_ws": 0,
        "writer_finish_ws": 0,
        "notifications": [],
        "insert_action_log": [],
        "update_action_log": [],
        "insert_events": [],
        "update_events": {},
    }

    class DummyNotificationPM:
        @classmethod
        def start_workspace_processing(cls, org, ws):
            calls["notification_start_ws"] += 1

        @classmethod
        def finish_workspace_processing(cls):
            calls["notification_finish_ws"] += 1

        @classmethod
        def start_process(cls):
            return None

        @classmethod
        def stop_process(cls):
            return None

        @classmethod
        def send_notification(cls, event_list, info):
            calls["notifications"].append((list(event_list), dict(info)))

    class DummyWriterPM:
        @classmethod
        def start_workspace_processing(cls, org, ws):
            calls["writer_start_ws"] += 1

        @classmethod
        def finish_workspace_processing(cls):
            calls["writer_finish_ws"] += 1

        @classmethod
        def insert_labeled_event_collection(cls, event):
            if "_id" not in event:
                event["_id"] = ObjectId()
            calls["insert_events"].append(event)
            return event["_id"]  # 戻り値はイベントID

        @classmethod
        def update_labeled_event_collection(cls, filter, update):
            update_events = calls["update_events"]
            key = frozenset(filter.items())
            events = update_events.get(key, {})
            update_events[key] = deep_merged(events, update)

        @classmethod
        def insert_oase_action_log(cls, data):
            data["ACTION_LOG_ID"] = str(uuid.uuid4())
            calls["insert_action_log"].append(data)
            return [data]  # 戻り値はリストでラップ

        @classmethod
        def update_oase_action_log(cls, data):
            calls["update_action_log"].append(data)

        @classmethod
        def start_process(cls):
            return None

        @classmethod
        def stop_process(cls):
            return None

    monkeypatch.setattr(bm, "NotificationProcessManager", DummyNotificationPM)
    monkeypatch.setattr(la, "NotificationProcessManager", DummyNotificationPM)
    monkeypatch.setattr(bm, "WriterProcessManager", DummyWriterPM)
    monkeypatch.setattr(clome, "WriterProcessManager", DummyWriterPM)
    monkeypatch.setattr(la, "WriterProcessManager", DummyWriterPM)

    return calls


@pytest.fixture
def patch_common_functions(monkeypatch):
    """共通関数をパッチ"""

    def dummy_addline_msg(msg):
        return f"[ADDLINE] {msg}"

    monkeypatch.setattr(bm, "addline_msg", dummy_addline_msg)

    return {
        "addline_msg": dummy_addline_msg,
    }


# ===== テストケース =====


def test_backyard_main_no_events(
    patch_global_g, patch_notification_and_writer, monkeypatch
):
    """正常系: イベント0件の場合"""
    calls = patch_notification_and_writer

    # データベースとMongoDBをモック化
    mock_mongo = MockMONGOConnectWs()
    ws_db = DummyDB("ws1")

    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    monkeypatch.setattr(bm, "Action", DummyAction)
    monkeypatch.setattr(bm, "ActionStatusMonitor", DummyActionStatusMonitor)

    bm.backyard_main("org1", "ws1")

    # 呼び出し確認
    assert calls["notification_start_ws"] == 1
    assert calls["writer_start_ws"] == 1
    assert calls["writer_finish_ws"] >= 1
    assert calls["notification_finish_ws"] == 1
    assert ws_db.ended is True and ws_db.args_end is False
    assert ws_db.disconnected is True
    assert mock_mongo.disconnected is True


def test_backyard_main_exception_path(
    patch_global_g, patch_notification_and_writer, monkeypatch
):
    """異常系: ManageEvents生成時の例外"""
    calls = patch_notification_and_writer

    # データベースをモック化
    mock_mongo = MockMONGOConnectWs()
    ws_db = DummyDB("ws1")

    # 例外を発生させる専用のダミークラス
    class DummyManageEventsWithException:
        def __init__(self, ws_mongo, judge_time):
            raise RuntimeError("init error")

    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    monkeypatch.setattr(bm, "ManageEvents", DummyManageEventsWithException)
    monkeypatch.setattr(bm, "Action", DummyAction)
    monkeypatch.setattr(bm, "ActionStatusMonitor", DummyActionStatusMonitor)

    # 例外は内部で捕捉されるので発生しない
    bm.backyard_main("org2", "ws2")

    # finally ブロックの呼び出し確認
    assert calls["writer_finish_ws"] >= 1
    assert calls["notification_finish_ws"] == 1
    assert ws_db.disconnected is True
    assert mock_mongo.disconnected is True


def test_backyard_main_with_successful_judge_main(
    patch_global_g, patch_notification_and_writer, patch_datetime, monkeypatch
):
    """正常系: JudgeMainが成功する場合"""
    calls = patch_notification_and_writer

    # イベントありのManageEventsを設定
    mock_mongo = MockMONGOConnectWs()
    mock_mongo.test_events = [
        {
            "_id": "event1",
            "labels": {
                "_exastro_type": "raw",
                "_exastro_timeout": "0",
                "_exastro_evaluated": "0",
                "_exastro_undetected": "0",
                "_exastro_fetched_time": "1000000",
                "_exastro_end_time": "2000000",
            },
        }
    ]
    dummy_manage_events = ManageEvents(mock_mongo, 1000000)
    ws_db = DummyDB("ws1")

    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    monkeypatch.setattr(
        bm, "ManageEvents", lambda ws_mongo, judge_time: dummy_manage_events
    )
    monkeypatch.setattr(bm, "Action", DummyAction)
    monkeypatch.setattr(bm, "ActionStatusMonitor", DummyActionStatusMonitor)

    # JudgeMainをモック化してTrueを返す
    def mock_judge_main(ws_db, judge_time, event_obj, action_obj):
        return True

    monkeypatch.setattr(bm, "JudgeMain", mock_judge_main)

    bm.backyard_main("org1", "ws1")

    # 正常終了パスの確認
    assert calls["notification_start_ws"] == 1
    assert calls["writer_start_ws"] == 1
    assert calls["writer_finish_ws"] >= 1
    assert calls["notification_finish_ws"] == 1


def test_backyard_main_action_status_monitor_exception(
    patch_global_g, patch_notification_and_writer, monkeypatch
):
    """異常系: ActionStatusMonitor処理中の例外"""
    # イベントありのManageEventsを設定
    mock_mongo = MockMONGOConnectWs()
    mock_mongo.test_events = [
        create_event("test_case", "event1", judge_time, judge_time + 1000000),
    ]
    dummy_manage_events = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")

    # 例外を発生させるActionStatusMonitor
    class DummyActionStatusMonitorWithException:
        def __init__(self, ws_db, event_obj):
            # Mock initialization
            pass

        def checkRuleMatch(self, action_obj):
            raise RuntimeError("ActionStatusMonitor checkRuleMatch error")

        def checkExecuting(self):
            # Mock implementation
            pass

    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    monkeypatch.setattr(
        bm, "ManageEvents", lambda ws_mongo, judge_time: dummy_manage_events
    )
    monkeypatch.setattr(bm, "Action", DummyAction)
    monkeypatch.setattr(
        bm, "ActionStatusMonitor", DummyActionStatusMonitorWithException
    )

    def mock_judge_main(ws_db, judge_time, event_obj, action_obj):
        return True

    monkeypatch.setattr(bm, "JudgeMain", mock_judge_main)

    # 例外は内部で捕捉される
    bm.backyard_main("org1", "ws1")

    # finally処理が実行されることを確認
    assert ws_db.disconnected is True
    assert mock_mongo.disconnected is True


def test_judge_main_no_events(patch_global_g):
    """JudgeMain: イベント0件の場合"""
    # 共通ダミークラスを使用（イベント0件）
    mock_mongo = MockMONGOConnectWs()
    ev_obj = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")
    action_obj = Action(ws_db, ev_obj)

    ret = bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)
    assert ret is False


def test_judge_main_with_timeout_events(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: タイムアウトイベントがある場合"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter_row := create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, []),
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule1_name", filter_row, action_id="action1")
    ]
    ws_db.table_data["T_OASE_ACTION"] = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0}
    ]
    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)

    # タイムアウト用のテストデータを設定したManageEventsを使用
    mock_mongo = MockMONGOConnectWs()
    mock_mongo.test_events = [
        create_event(
            "timeout_event", "event_timeout_1", judge_time - 9999, judge_time - 7999
        ),
    ]

    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    ev_obj = ManageEvents(mock_mongo, judge_time)
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    # タイムアウト通知が送信されていることを確認
    timeout_notifications = [
        n
        for _, n in calls["notifications"]
        if n.get("notification_type") == OASENotificationType.TIMEOUT
    ]
    assert len(timeout_notifications) > 0


def test_judge_main_with_new_events_notification(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: 新規イベント通知のケース"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter_row := create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, [])
    ]
    ws_db.table_data["T_OASE_RULE"] = [create_rule_row(1, "rule1_name", filter_row)]
    ws_db.table_data["T_OASE_ACTION"] = []
    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)

    # 新規イベント用のテストデータを設定したManageEventsを使用
    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        e1 := create_event("ne", "ne1", judge_time, judge_time + 3600),
        e2 := create_event(
            "ne",
            "ne2",
            judge_time,
            judge_time + 3599,
            exastro_type="conclusion",
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    # 新規イベント通知が送信されることを確認
    new_notifications = [
        (e, n)
        for e, n in calls["notifications"]
        if n.get("notification_type") == OASENotificationType.NEW
    ]
    assert len(new_notifications) > 0

    # 結論イベントが通知対象外であることを確認
    event_ids_notified = [event["_id"] for event in new_notifications[0][0]]
    assert e1["_id"] in event_ids_notified  # exastroイベントは通知される
    assert e2["_id"] not in event_ids_notified  # conclusionイベントは通知されない


def test_judge_main_with_undetected_events(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: 未知イベント処理のケース"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter_row := create_filter_row(
            1,
            [
                create_filter_condition(
                    "specific_label", oaseConst.DF_TEST_EQ, "matching_value"
                )
            ],
        ),
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule1_name", filter_row, action_id="action1")
    ]
    ws_db.table_data["T_OASE_ACTION"] = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0}
    ]
    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)

    # 未知イベント用のテストデータを設定したManageEventsを使用
    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        create_event(
            "undetected_event",
            "event_undetected_1",
            judge_time - 999,
            judge_time + 2001,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    # 未知イベント通知が送信されることを確認
    undetected_notifications = [
        n
        for _, n in calls["notifications"]
        if n.get("notification_type") == OASENotificationType.UNDETECTED
    ]
    assert len(undetected_notifications) > 0


def test_judge_main_filter_id_map_failure(patch_global_g, monkeypatch):
    """JudgeMain: getFilterIDMapが失敗する場合"""

    def failing_get_filter_id_map(ws_db):
        return False

    monkeypatch.setattr(bm, "getFilterIDMap", failing_get_filter_id_map)

    # 共通ダミークラスを使用
    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        create_event("event1", "event1", judge_time, judge_time + 1000000),
    ]
    ev_obj = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")
    action_obj = Action(ws_db, ev_obj)

    ret = bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)
    assert ret is False


def test_judge_main_rule_list_failure(patch_global_g, monkeypatch):
    """JudgeMain: getRuleListが失敗する場合"""

    def failing_get_rule_list(ws_db, sort):
        return False, "Error message"

    monkeypatch.setattr(bm, "getRuleList", failing_get_rule_list)

    # 共通ダミークラスを使用
    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        create_event("event1", "event1", judge_time, judge_time + 1000000),
    ]
    ev_obj = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, [])
    ]
    action_obj = Action(ws_db, ev_obj)

    ret = bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)
    assert ret is False


def test_judge_main_with_action_records(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: アクションレコードがある場合"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter_row := create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, [])
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule1_name", filter_row, action_id="action1"),
    ]
    ws_db.table_data["T_OASE_ACTION"] = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0}
    ]
    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)

    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        create_event("event1", "event1", judge_time, judge_time + 1000000),
    ]
    ev_obj = ManageEvents(mock_mongo, judge_time)
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    assert len(calls["insert_action_log"]) > 0
    assert calls["insert_action_log"][0]["ACTION_ID"] == "action1"

    # 既知イベント通知が送信されることを確認
    evaluated_notifications = [
        n
        for _, n in calls["notifications"]
        if n.get("notification_type") == OASENotificationType.EVALUATED
    ]
    assert len(evaluated_notifications) > 0


def test_judge_main_with_post_proc_timeout_events(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: 処理後タイムアウトイベントがある場合"""
    calls = patch_notification_and_writer

    # 処理後タイムアウトイベント用のテストデータを設定したManageEventsを使用
    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        create_event(
            "post_proc_timeout_event",
            "event_post_proc_timeout_1",
            judge_time - 1800,
            judge_time - 900,
        ),
        create_event(
            "post_proc_timeout_event",
            "event_post_proc_timeout_2",
            judge_time - 1800,
            judge_time - 900,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter_row := create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, [])
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule1_name", filter_row, action_id="action1")
    ]
    ws_db.table_data["T_OASE_ACTION"] = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0}
    ]
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    # 処理後タイムアウトイベントが正しく処理されることを確認

    assert all(
        event["labels"].get("_exastro_timeout") == "1"
        for event in ev_obj.labeled_events_dict.values()
    )

    # タイムアウトイベント通知が送信されないことを確認
    timeout_notifications = [
        n
        for _, n in calls["notifications"]
        if n.get("notification_type") == OASENotificationType.TIMEOUT
    ]
    assert len(timeout_notifications) == 0


@patch.dict(os.environ, {"EVALUATE_LATENT_INFINITE_LOOP_LIMIT": "5"})
def test_judge_main_with_environment_variable(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: 環境変数EVALUATE_LATENT_INFINITE_LOOP_LIMITのテスト"""
    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        {
            "_id": "event1",
            "labels": {
                "_exastro_type": "raw",
                "_exastro_checked": "0",
                "_exastro_timeout": "0",
                "_exastro_evaluated": "0",
                "_exastro_undetected": "0",
                "_exastro_fetched_time": "1000000",
                "_exastro_end_time": "2000000",
            },
        }
    ]
    ev_obj = ManageEvents(mock_mongo, 1000000)
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        {
            "FILTER_ID": "filter1",
            "DISUSE_FLAG": 0,
            "AVAILABLE_FLAG": 1,
            "SEARCH_CONDITION_ID": 1,
            "FILTER_CONDITION_JSON": "{}",
        }
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        {
            "RULE_ID": "rule1",
            "DISUSE_FLAG": 0,
            "AVAILABLE_FLAG": 1,
            "RULE_PRIORITY": 1,
            "FILTER_A": "filter1",
            "RULE_NAME": "rule1_name",
            "FILTER_OPERATOR": "AND",
            "FILTER_B": "filter1",
            "ACTION_ID": "action1",
            "CONCLUSION_LABEL_SETTINGS": "{}",
        }
    ]
    ws_db.table_data["T_OASE_ACTION"] = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0}
    ]
    action_obj = Action(ws_db, ev_obj)

    # 環境変数が正しく読み込まれることを確認
    bm.JudgeMain(ws_db, 999999, ev_obj, action_obj)


def test_on_start_process(patch_notification_and_writer):
    """on_start_process関数のテスト"""
    bm.on_start_process()
    # NotificationProcessManager.start_process()とWriterProcessManager.start_process()が呼ばれる
    # この関数はvoidなので、例外が発生しないことを確認


def test_on_exit_process(patch_notification_and_writer):
    """on_exit_process関数のテスト"""
    bm.on_exit_process()
    # NotificationProcessManager.stop_process()とWriterProcessManager.stop_process()が呼ばれる
    # この関数はvoidなので、例外が発生しないことを確認


# ===== テストケース(複雑なシナリオ) =====


def test_scenario_grouping_target_2_same_label_events_to_1_group(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: グルーピング・「を対象とする」: 同じラベルのイベントが1グループにまとめられることを確認"""
    # 結論イベントフィルタリング用のテストデータを設定したManageEventsを使用
    head_event_ids = (ObjectId(),)
    group1_labels = {
        "grp_label_1": "grp1_label_1",
        "grp_label_2": "grp1_label_2",
        "grp_label_3": "grp1_label_3",
    }
    judge_time = 1760486660

    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)
    mock_mongo.test_events = [
        create_event(
            "case1",
            "case1-grp1-ev-01",
            judge_time - 9,
            judge_time + 1,
            custom_labels=group1_labels,
            id=head_event_ids[0],
        ),
        create_event(
            "case1",
            "case1-grp1-ev-02",
            judge_time - 8,
            judge_time + 2,
            custom_labels=group1_labels,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, 1760486660)
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        grouping_filter := create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_GROUPING,
            [
                ("test_case", oaseConst.DF_TEST_EQ, "case1"),
                ("_exastro_type", oaseConst.DF_TEST_NE, "conclusion"),
            ],
            oaseConst.DF_GROUP_CONDITION_ID_TARGET,
            ["grp_label_2", "grp_label_3", "grp_label_1"],
        ),
        # 結論イベント対策
        create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_QUEUING,
            [("_exastro_type", oaseConst.DF_TEST_EQ, "conclusion")],
        ),
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule_case1", grouping_filter),
    ]
    ws_db.table_data["T_OASE_ACTION"] = []
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, 1760486660, ev_obj, action_obj)

    # グルーピングが正しく行われることの確認

    group_ids = set()
    first_exastro_end_time = 0
    max_exastro_end_time = 0
    for i, event in enumerate(ev_obj.labeled_events_dict.values()):
        if event["labels"]["_exastro_type"] == "conclusion":
            continue

        group_info = event.get("exastro_filter_group")
        assert group_info is not None
        assert group_info["filter_id"] == grouping_filter["FILTER_ID"]

        if event["_id"] in head_event_ids:
            assert group_info["group_id"] == repr(event["_id"])
            assert group_info["is_first_event"]
            first_group_id = event["_id"]
            first_exastro_end_time = event["labels"]["_exastro_end_time"]
        else:
            assert group_info["group_id"] == repr(first_group_id)
            assert not group_info["is_first_event"]
            max_exastro_end_time = max(
                max_exastro_end_time, event["labels"]["_exastro_end_time"]
            )

        group_ids.add(group_info["group_id"])

    assert first_exastro_end_time == max_exastro_end_time
    assert len(group_ids) == 1

    # 結論イベントが1つ追加されていることを確認
    assert len(ev_obj.labeled_events_dict) == len(mock_mongo.test_events) + 1


def test_scenario_grouping_target_2_different_label_events_to_2_groups(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: グルーピング・「を対象とする」: ラベルが異なる2つのイベントが、2つのグループに分かれることを確認"""
    # 結論イベントフィルタリング用のテストデータを設定したManageEventsを使用
    head_event_ids = (ObjectId(), ObjectId())
    group1_labels = {
        "grp_label_1": "grp1_label_1",
        "grp_label_2": "grp1_label_2",
        "grp_label_3": "grp1_label_3",
    }
    group2_labels = {
        "grp_label_1": "grp2_label_1",
        "grp_label_2": "grp2_label_2",
    }
    judge_time = 1760486660

    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)

    mock_mongo.test_events = [
        create_event(
            "case1",
            "case1-grp1-ev-01",
            judge_time - 9,
            judge_time + 1,
            custom_labels=group1_labels,
            id=head_event_ids[0],
        ),
        create_event(
            "case1",
            "case1-grp2-ev-01",
            judge_time - 9,
            judge_time + 1,
            custom_labels=group2_labels,
            id=head_event_ids[1],
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        grouping_filter := create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_GROUPING,
            [
                ("test_case", oaseConst.DF_TEST_EQ, "case1"),
                ("_exastro_type", oaseConst.DF_TEST_NE, "conclusion"),
            ],
            oaseConst.DF_GROUP_CONDITION_ID_TARGET,
            ["grp_label_2", "grp_label_3", "grp_label_1"],
        ),
        # 結論イベント対策
        create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_QUEUING,
            [("_exastro_type", oaseConst.DF_TEST_EQ, "conclusion")],
        ),
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule_case1", grouping_filter),
    ]
    ws_db.table_data["T_OASE_ACTION"] = []
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    # グルーピングが正しく行われることの確認

    group_ids = set()
    for event in ev_obj.labeled_events_dict.values():
        if event["labels"]["_exastro_type"] == "conclusion":
            continue

        group_info = event.get("exastro_filter_group")
        assert group_info is not None
        assert group_info["group_id"] == repr(event["_id"])
        assert group_info["filter_id"] == grouping_filter["FILTER_ID"]
        assert group_info["is_first_event"]

        group_ids.add(group_info["group_id"])

    assert len(group_ids) == 2

    # 結論イベントが2つ追加されていることを確認
    assert len(ev_obj.labeled_events_dict) == len(mock_mongo.test_events) + 2


def test_scenario_grouping_multiple_groups_has_multiple_subsequent_events(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: グルーピング: 複数のグループがそれぞれ複数の後続イベントを持つ場合に正しくグルーピングされることを確認"""
    # 結論イベントフィルタリング用のテストデータを設定したManageEventsを使用
    head_event_ids = (ObjectId(), ObjectId())
    group1_labels = {
        "grp_label_1": "grp1_label_1",
        "grp_label_2": "grp1_label_2",
        "grp_label_3": "grp1_label_3",
    }
    group2_labels = {
        "grp_label_1": "grp2_label_1",
        "grp_label_2": "grp2_label_2",
    }
    judge_time = 1760486660

    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)

    mock_mongo.test_events = [
        # グループ1
        create_event(
            "case1",
            "case1-grp1-ev-01",
            judge_time - 9,
            judge_time + 1,
            custom_labels=group1_labels,
            id=head_event_ids[0],
        ),
        create_event(
            "case1",
            "case1-grp1-ev-02",
            judge_time - 4,
            judge_time + 6,
            custom_labels=group1_labels,
        ),
        create_event(
            "case1",
            "case1-grp1-ev-03",
            judge_time + 6,
            judge_time + 16,
            custom_labels=group1_labels,
        ),
        # グループ2
        create_event(
            "case1",
            "case1-grp2-ev-01",
            judge_time - 8,
            judge_time - 2,
            custom_labels=group2_labels,
            id=head_event_ids[1],
        ),
        create_event(
            "case1",
            "case1-grp2-ev-02",
            judge_time - 7,
            judge_time - 1,
            custom_labels=group2_labels,
        ),
        create_event(
            "case1",
            "case1-grp2-ev-03",
            judge_time - 6,
            judge_time - 4,
            custom_labels=group2_labels,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        grouping_filter := create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_GROUPING,
            [
                ("test_case", oaseConst.DF_TEST_EQ, "case1"),
                ("_exastro_type", oaseConst.DF_TEST_NE, "conclusion"),
            ],
            oaseConst.DF_GROUP_CONDITION_ID_TARGET,
            ["grp_label_2", "grp_label_3", "grp_label_1"],
        ),
        # 結論イベント対策
        create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_QUEUING,
            [("_exastro_type", oaseConst.DF_TEST_EQ, "conclusion")],
        ),
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule_case1", grouping_filter),
    ]
    ws_db.table_data["T_OASE_ACTION"] = []
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    # グルーピングが正しく行われることの確認

    group_ids = set()
    first_group_state_map = {}
    for event in ev_obj.labeled_events_dict.values():
        if event["labels"]["_exastro_type"] == "conclusion":
            continue

        group_info = event.get("exastro_filter_group")
        assert group_info is not None
        assert group_info["filter_id"] == grouping_filter["FILTER_ID"]

        if event["_id"] in head_event_ids:
            assert group_info["group_id"] == repr(event["_id"])
            assert group_info["is_first_event"]

            first_group_state_map[group_info["group_id"]] = {
                "first_exastro_end_time": event["labels"]["_exastro_end_time"],
                "max_exastro_end_time": event["labels"]["_exastro_end_time"],
            }

        else:
            assert group_info["group_id"] in first_group_state_map.keys()
            assert not group_info["is_first_event"]

            first_group_state = first_group_state_map[group_info["group_id"]]
            first_group_state["max_exastro_end_time"] = max(
                first_group_state["max_exastro_end_time"],
                event["labels"]["_exastro_end_time"],
            )

        group_ids.add(event["exastro_filter_group"]["group_id"])

    for group_state in first_group_state_map.values():
        assert (
            group_state["first_exastro_end_time"] == group_state["max_exastro_end_time"]
        )

    assert len(group_ids) == 2

    # 結論イベントが2つ追加されていることを確認
    assert len(ev_obj.labeled_events_dict) == len(mock_mongo.test_events) + 2


def test_scenario_grouping_evaluated_first_events(
    patch_global_g, patch_notification_and_writer, patch_common_functions, monkeypatch
):
    """JudgeMain: グルーピング: 有効な判定済み先頭イベントが正しくグルーピングされることを確認"""
    # 結論イベントフィルタリング用のテストデータを設定したManageEventsを使用
    group1_labels = {
        "grp_label_1": "grp1_label_1",
        "grp_label_2": "grp1_label_2",
        "grp_label_3": "grp1_label_3",
    }

    mock_mongo = MockMONGOConnectWs()
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)

    grouping_filter = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("test_case", oaseConst.DF_TEST_EQ, "case1"),
            ("_exastro_type", oaseConst.DF_TEST_NE, "conclusion"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["grp_label_2", "grp_label_3", "grp_label_1"],
    )
    mock_mongo.test_events = [
        # グループ1
        evaluated_first_event := create_event(
            "case1",
            "case1-grp1-ev-01",
            judge_time - 9,
            judge_time + 1,
            custom_labels=group1_labels,
            evaluated="1",
            grouping_filter=grouping_filter,
        ),
        subsequent_event_1 := create_event(
            "case1",
            "case1-grp1-ev-02",
            judge_time - 4,
            judge_time + 6,
            custom_labels=group1_labels,
        ),
        subsequent_event_2 := create_event(
            "case1",
            "case1-grp1-ev-03",
            judge_time + 6,
            judge_time + 16,
            custom_labels=group1_labels,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
    ws_db = DummyDB("ws1")
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        grouping_filter,
        # 結論イベント対策
        create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_QUEUING,
            [("_exastro_type", oaseConst.DF_TEST_EQ, "conclusion")],
        ),
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(1, "rule_case1", grouping_filter),
    ]
    ws_db.table_data["T_OASE_ACTION"] = []
    action_obj = Action(ws_db, ev_obj)

    bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)

    # グルーピングが正しく行われることの確認

    # 有効な判定済み先頭イベントに更新が走っている
    assert (
        frozenset({("_id", evaluated_first_event["_id"])})
        in patch_notification_and_writer["update_events"]
    )

    # 有効な判定済み先頭イベントはグルーピング情報を持つ
    first_event_group = evaluated_first_event.get("exastro_filter_group")
    assert first_event_group is not None

    # 後続イベントが有効な判定済み先頭イベントにグルーピングされていることを確認
    grouping_info_1 = subsequent_event_1.get("exastro_filter_group")
    assert grouping_info_1 is not None
    assert grouping_info_1["group_id"] == first_event_group["group_id"]

    grouping_info_2 = subsequent_event_2.get("exastro_filter_group")
    assert grouping_info_2 is not None
    assert grouping_info_2["group_id"] == first_event_group["group_id"]

    # 結論イベントが追加されていないことを確認
    assert [
        event["labels"]["_exastro_type"]
        for event in ev_obj.labeled_events_dict.values()
    ].count("conclusion") == 0
