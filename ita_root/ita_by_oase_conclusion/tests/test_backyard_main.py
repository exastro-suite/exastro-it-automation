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

import os
from unittest.mock import patch

from bson import ObjectId

import backyard_main as bm
from common_libs.notification.sub_classes.oase import OASENotificationType
from common_libs.oase.manage_events import ManageEvents
from common_libs.oase.const import oaseConst
from libs.action import Action
from tests.common import (
    create_event,
    create_filter_condition,
    create_filter_row,
    create_rule_row,
    judge_time,
    run_test_pattern,
)
from tests.test_double import DummyAction, DummyActionStatusMonitor

# ===== テストケース =====


def test_backyard_main_no_events(
    patch_global_g,
    patch_notification_and_writer,
    monkeypatch,
    patch_database_connections,
):
    """正常系: イベント0件の場合"""
    calls = patch_notification_and_writer
    ws_db, mock_mongo = patch_database_connections

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
    patch_global_g,
    patch_notification_and_writer,
    monkeypatch,
    patch_database_connections,
):
    """異常系: ManageEvents生成時の例外"""
    calls = patch_notification_and_writer
    ws_db, mock_mongo = patch_database_connections

    # 例外を発生させる専用のダミークラス
    class DummyManageEventsWithException:
        def __init__(self, ws_mongo, judge_time):
            raise RuntimeError("init error")

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
    patch_global_g,
    patch_notification_and_writer,
    patch_datetime,
    monkeypatch,
    patch_database_connections,
):
    """正常系: JudgeMainが成功する場合"""
    calls = patch_notification_and_writer

    # イベントありのManageEventsを設定
    _, mock_mongo = patch_database_connections
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
    patch_global_g,
    patch_notification_and_writer,
    monkeypatch,
    patch_database_connections,
):
    """異常系: ActionStatusMonitor処理中の例外"""
    # イベントありのManageEventsを設定
    ws_db, mock_mongo = patch_database_connections
    mock_mongo.test_events = [
        create_event("test_case", "event1", judge_time, ttl=1000000),
    ]
    dummy_manage_events = ManageEvents(mock_mongo, judge_time)

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


def test_judge_main_no_events(patch_global_g, patch_database_connections):
    """JudgeMain: イベント0件の場合"""
    # 共通ダミークラスを使用（イベント0件）
    ws_db, mock_mongo = patch_database_connections
    ev_obj = ManageEvents(mock_mongo, judge_time)
    action_obj = Action(ws_db, ev_obj)

    ret = bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)
    assert ret is False


def test_judge_main_with_timeout_events(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: タイムアウトイベントがある場合"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db, mock_mongo = patch_database_connections
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

    # タイムアウト用のテストデータを設定したManageEventsを使用
    mock_mongo.test_events = [
        create_event("timeout_event", "event_timeout_1", judge_time - 9999, ttl=2000),
    ]

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
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: 新規イベント通知のケース"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db, mock_mongo = patch_database_connections
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter_row := create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, [])
    ]
    ws_db.table_data["T_OASE_RULE"] = [create_rule_row(1, "rule1_name", filter_row)]
    ws_db.table_data["T_OASE_ACTION"] = []

    # 新規イベント用のテストデータを設定したManageEventsを使用
    mock_mongo.test_events = [
        e1 := create_event("ne", "ne1", judge_time, ttl=3600),
        e2 := create_event(
            "ne",
            "ne2",
            judge_time,
            ttl=3599,
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
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: 未知イベント処理のケース"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db, mock_mongo = patch_database_connections
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

    # 未知イベント用のテストデータを設定したManageEventsを使用
    mock_mongo.test_events = [
        create_event(
            "undetected_event",
            "event_undetected_1",
            judge_time - 999,
            ttl=3000,
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


def test_judge_main_filter_id_map_failure(
    patch_global_g, monkeypatch, patch_database_connections
):
    """JudgeMain: getFilterIDMapが失敗する場合"""

    def failing_get_filter_id_map(ws_db):
        return False

    monkeypatch.setattr(bm, "getFilterIDMap", failing_get_filter_id_map)

    # 共通ダミークラスを使用
    ws_db, mock_mongo = patch_database_connections
    mock_mongo.test_events = [
        create_event("event1", "event1", judge_time, ttl=1000000),
    ]
    ev_obj = ManageEvents(mock_mongo, judge_time)
    action_obj = Action(ws_db, ev_obj)

    ret = bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)
    assert ret is False


def test_judge_main_rule_list_failure(
    patch_global_g, monkeypatch, patch_database_connections
):
    """JudgeMain: getRuleListが失敗する場合"""

    def failing_get_rule_list(ws_db, sort):
        return False, "Error message"

    monkeypatch.setattr(bm, "getRuleList", failing_get_rule_list)

    # 共通ダミークラスを使用
    ws_db, mock_mongo = patch_database_connections
    mock_mongo.test_events = [
        create_event("event1", "event1", judge_time, ttl=1000000),
    ]
    ev_obj = ManageEvents(mock_mongo, judge_time)
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, [])
    ]
    action_obj = Action(ws_db, ev_obj)

    ret = bm.JudgeMain(ws_db, judge_time, ev_obj, action_obj)
    assert ret is False


def test_judge_main_with_action_records(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: アクションレコードがある場合"""
    calls = patch_notification_and_writer

    # データベースをモック化
    ws_db, mock_mongo = patch_database_connections
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

    mock_mongo.test_events = [
        create_event("event1", "event1", judge_time, ttl=1000000),
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
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: 処理後タイムアウトイベントがある場合"""
    calls = patch_notification_and_writer

    # 処理後タイムアウトイベント用のテストデータを設定したManageEventsを使用
    ws_db, mock_mongo = patch_database_connections
    mock_mongo.test_events = [
        create_event(
            "post_proc_timeout_event",
            "event_post_proc_timeout_1",
            judge_time - 1800,
            ttl=900,
        ),
        create_event(
            "post_proc_timeout_event",
            "event_post_proc_timeout_2",
            judge_time - 1800,
            ttl=900,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
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
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: 環境変数EVALUATE_LATENT_INFINITE_LOOP_LIMITのテスト"""
    ws_db, mock_mongo = patch_database_connections
    mock_mongo.test_events = [
        create_event(
            "env_var_test_event",
            "event_env_var_1",
            judge_time,
            ttl=1000000,
        )
    ]
    ev_obj = ManageEvents(mock_mongo, judge_time)
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter_row := create_filter_row(oaseConst.DF_SEARCH_CONDITION_UNIQUE, []),
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        create_rule_row(
            1,
            "rule1_name",
            [filter_row, filter_row],
            filter_operator=oaseConst.DF_OPE_AND,
            action_id="action1",
        )
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
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
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

    ws_db, mock_mongo = patch_database_connections
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
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        grouping_filter := create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_GROUPING,
            [
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
    assert (
        len(
            [
                event
                for event in mock_mongo.test_events
                if event["labels"].get("_exastro_type") == "conclusion"
            ]
        )
        == 1
    )


def test_scenario_grouping_target_2_different_label_events_to_2_groups(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
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

    ws_db, mock_mongo = patch_database_connections
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
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        grouping_filter := create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_GROUPING,
            [
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
    assert (
        len(
            [
                event
                for event in mock_mongo.test_events
                if event["labels"].get("_exastro_type") == "conclusion"
            ]
        )
        == 2
    )


def test_scenario_grouping_multiple_groups_has_multiple_subsequent_events(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
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

    ws_db, mock_mongo = patch_database_connections

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
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        grouping_filter := create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_GROUPING,
            [
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
    assert (
        len(
            [
                event
                for event in mock_mongo.test_events
                if event["labels"].get("_exastro_type") == "conclusion"
            ]
        )
        == 2
    )


def test_scenario_grouping_evaluated_first_events(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: グルーピング: 有効な判定済み先頭イベントが正しくグルーピングされることを確認"""
    calls = patch_notification_and_writer
    group1_labels = {
        "grp_label_1": "grp1_label_1",
        "grp_label_2": "grp1_label_2",
        "grp_label_3": "grp1_label_3",
    }

    ws_db, mock_mongo = patch_database_connections

    grouping_filter = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
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
    assert frozenset({("_id", evaluated_first_event["_id"])}) in calls["update_events"]

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


def test_scenario_grouping_without_filter_condition(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: グルーピング: フィルター条件なしでグルーピングが正しく行われることを確認"""
    calls = patch_notification_and_writer
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

    ws_db, mock_mongo = patch_database_connections

    mock_mongo.test_events = [
        create_event(
            "case1",
            "case1-grp1-ev-01",
            judge_time - 9,
            judge_time + 1,
            custom_labels=group1_labels,
        ),
        create_event(
            "case1",
            "case1-grp2-ev-01",
            judge_time - 9,
            judge_time + 1,
            custom_labels=group2_labels,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
    # 必要なテーブルデータを設定（イベントがマッチしないフィルター条件）
    ws_db.table_data["T_OASE_FILTER"] = [
        # 結論イベント対策
        create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_QUEUING,
            [("_exastro_type", oaseConst.DF_TEST_EQ, "conclusion")],
        ),
        grouping_filter := create_filter_row(
            oaseConst.DF_SEARCH_CONDITION_GROUPING,
            None,  # フィルター条件なし
            oaseConst.DF_GROUP_CONDITION_ID_TARGET,
            ["grp_label_2", "grp_label_3", "grp_label_1"],
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

    # 正しくグルーピング、結論イベント追加がされていることを確認

    # 結論以外のイベントレコード
    without_conclusion_event_records = [
        event
        for event in ev_obj.labeled_events_dict.values()
        if event["labels"]["_exastro_type"] != "conclusion"
    ]
    # 結論イベントレコード
    conclusion_event_records = [
        event
        for event in ev_obj.labeled_events_dict.values()
        if event["labels"]["_exastro_type"] == "conclusion"
    ]
    # 実質的な結論以外のイベント
    without_conclusion_events = [
        event
        for event in without_conclusion_event_records
        if "exastro_filter_group" not in event
        or event["exastro_filter_group"]["is_first_event"]
    ]
    # 実質的な結論イベント
    conclusion_events = [
        event
        for event in conclusion_event_records
        if "exastro_filter_group" not in event
        or event["exastro_filter_group"]["is_first_event"]
    ]

    # 1. 1件目のイベント処理(F_A1にヒット→グループ1先頭イベント)
    # 2. 1件目の結論イベント作成
    # 3. 2件目のイベント処理(F_A1にヒット→グループ2先頭イベント)
    # 4. 2件目の結論イベント作成
    # 5. 1件目の結論イベント処理(F_A1にヒット→グループ3先頭イベント)
    # 6. 3件目の結論イベント(1件目の結論イベントの結論イベント)作成
    # 7. 2件目の結論イベント処理(F_A1にヒット→グループ3後続イベント)
    # 8. 3件目の結論イベント処理(F_A1にヒット→グループ3後続イベント)
    # 9. 処理できるイベントがなくなったため終了
    #     → 結論以外のイベントがレコード2件、実質2件(先頭イベント2件)
    #       結論イベントがレコード3件、実質1件(先頭イベント1件、後続イベント2件)

    assert len(without_conclusion_event_records) == 2
    assert len(without_conclusion_events) == 2
    assert len(conclusion_event_records) == 3
    assert len(conclusion_events) == 1

    # MongoDB上作成される結論イベントにDF_LOCAL_LABLE_NAMEが存在しないことを確認
    for event in calls["insert_events"]:
        assert oaseConst.DF_LOCAL_LABLE_NAME not in event


def test_scenario_grouping_timeout_and_evaluated_first_event_in_conclusion_period(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: グルーピング: 評価対象期間内ならばタイムアウトしている判定済み先頭イベントが正しくグルーピングされることを確認"""
    calls = patch_notification_and_writer
    group1_labels = {
        "grp_label_1": "grp1_label_1",
        "grp_label_2": "grp1_label_2",
        "grp_label_3": "grp1_label_3",
    }
    original_ttl = 11

    ws_db, mock_mongo = patch_database_connections

    grouping_filter = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
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
            judge_time - 15,
            ttl=original_ttl,
            custom_labels=group1_labels,
            evaluated="1",
            grouping_filter=grouping_filter,
        ),
        subsequent_event_1 := create_event(
            "case1",
            "case1-grp1-ev-02",
            judge_time - 6,
            ttl=original_ttl,
            custom_labels=group1_labels,
        ),
        subsequent_event_2 := create_event(
            "case1",
            "case1-grp1-ev-03",
            judge_time + 3,
            ttl=original_ttl,
            custom_labels=group1_labels,
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
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
    assert frozenset({("_id", evaluated_first_event["_id"])}) in calls["update_events"]

    # 有効な判定済み先頭イベントはグルーピング情報を持つ
    first_event_group = evaluated_first_event.get("exastro_filter_group")
    assert first_event_group is not None
    # original_ttlが設定されていて、元のTTLが設定されていることを確認
    assert "original_ttl" in first_event_group
    assert first_event_group["original_ttl"] == original_ttl

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


def test_scenario_grouping_not_target_can_handle_exastro_host_label(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
):
    """JudgeMain: グルーピング・「以外を対象とする」: _exastro_host ラベルが正しく処理されることを確認"""
    group1_labels = {
        "grp_label_1": "grp1_label_1",
        "grp_label_2": "grp1_label_2",
        "grp_label_3": "grp1_label_3",
    }
    original_ttl = 11

    ws_db, mock_mongo = patch_database_connections

    grouping_filter = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("_exastro_type", oaseConst.DF_TEST_NE, "conclusion"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET,
        ["grp_label_2", "grp_label_3", "grp_label_1"],
    )
    mock_mongo.test_events = [
        # グループ1
        e1 := create_event(
            "case1",
            "case1-grp1-ev-01",
            judge_time - 7,
            ttl=original_ttl,
            custom_labels={**group1_labels, "_exastro_host": "host1"},
            evaluated="1",
            grouping_filter=grouping_filter,
        ),
        e2 := create_event(
            "case1",
            "case1-grp1-ev-02",
            judge_time - 6,
            ttl=original_ttl,
            custom_labels={**group1_labels, "_exastro_host": "host1"},
        ),
        e3 := create_event(
            "case1",
            "case1-grp2-ev-01",
            judge_time - 3,
            ttl=original_ttl,
            custom_labels={**group1_labels, "_exastro_host": "host2"},
        ),
    ]

    ev_obj = ManageEvents(mock_mongo, judge_time)
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

    # 有効な判定済み先頭イベントはグルーピング情報を持つ
    grouping_info_1 = e1.get("exastro_filter_group")
    assert grouping_info_1 is not None
    assert grouping_info_1["group_id"] == repr(e1["_id"])

    # _exastro_host ラベルが同じイベントは同じグループになることを確認
    grouping_info_2 = e2.get("exastro_filter_group")
    assert grouping_info_2 is not None
    assert grouping_info_2["group_id"] == grouping_info_1["group_id"]

    # _exastro_host ラベルが異なるイベントは別グループになることを確認
    grouping_info_3 = e3.get("exastro_filter_group")
    assert grouping_info_3 is not None
    assert grouping_info_3["group_id"] != grouping_info_1["group_id"]


def test_scenario_order_b_only(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """JudgeMain: A → B の順序ルールで、Bのイベントのみが判定される場合に"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    # イベント
    event_b = create_event(
        "p92",
        "e026",
        ttl=20,
        custom_labels={"node": "z11", "type": "qa", "mode": "q3"},
    )
    test_events = [event_b]

    # フィルター
    f_u_a = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_UNIQUE,
        [
            ("type", oaseConst.DF_TEST_EQ, "a"),
        ],
    )
    f_q_a = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_QUEUING,
        [
            ("type", oaseConst.DF_TEST_EQ, "qa"),
        ],
    )

    # ルール
    r1 = create_rule_row(
        1,
        "p92:r1",
        (f_u_a, f_q_a),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_inheritance_flag={"action"},
        conclusion_label_settings=[
            {"type": "a"},
            {"B_eventid": "{{B.eventid}}"},
            {"A_eventid": "{{A.eventid}}"},
        ],
        conclusion_ttl=20,
    )
    r2 = create_rule_row(
        2,
        "p92:r2",
        f_u_a,
        conclusion_label_inheritance_flag={"action"},
        conclusion_label_settings=[
            {"A_eventid": "{{A.eventid}}"},
        ],
        conclusion_ttl=20,
    )

    # 必要なテーブルデータを設定
    filters = [
        f_u_a,
        f_q_a,
    ]
    rules = [
        r1,
        r2,
    ]

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules)

    # 未判定、既知、タイムアウトであることを確認
    assert event_b["labels"]["_exastro_evaluated"] == "0"
    assert event_b["labels"]["_exastro_undetected"] == "0"
    assert event_b["labels"]["_exastro_timeout"] == "1"

    # 新規イベント通知済みであることを確認
    assert event_b["labels"]["_exastro_checked"] == "1"


@patch.dict(os.environ, {"EVALUATE_LATENT_INFINITE_LOOP_LIMIT": "5"})
def test_scenario_loop_limit_over(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """大量データで1ループに収まらなかった場合の動作確認"""
    g = patch_global_g

    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime
    ttl = 10

    # フィルター
    f1 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("_exastro_type", oaseConst.DF_TEST_NE, "conclusion"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["node"],
    )

    # ルール
    r1 = create_rule_row(
        1,
        "limit_over",
        f1,
        conclusion_label_settings=[{"event_id": "c-{{A.event_id}}"}],
    )

    # 必要なテーブルデータを設定
    filters = [
        f1,
    ]
    rules = [
        r1,
    ]
    test_events = [
        create_event(
            "limit_over",
            f"e{n:03}",
            custom_labels={"node": "z01", "event_id": f"e{n:03}"},
            ttl=ttl,
        )
        for n in range(int(os.getenv("EVALUATE_LATENT_INFINITE_LOOP_LIMIT")) * 10 + 1)
    ]

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules)

    # タイムアウト、結論イベントを除くすべてが同じグループになることを確認
    import itertools

    group = {
        k: [e.get("event", e["labels"]).get("event_id") for e in v]
        for k, v in itertools.groupby(
            (
                event
                for event in test_events
                if event["labels"]["_exastro_timeout"] == "0"
                and event["labels"]["_exastro_type"] != "conclusion"
            ),
            key=lambda e: e.get("exastro_filter_group", {}).get("group_id"),
        )
    }

    __import__("pprint").pprint(group)

    assert len(group) == 1


def test_scenario_filtering_wildcard_pattern(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """「*」でのフィルタリングが正しく動作することを確認"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    # フィルター
    f1 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("node", oaseConst.DF_TEST_EQ, "*"),
            ("type", oaseConst.DF_TEST_EQ, "grouping"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["node"],
    )
    f2 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_UNIQUE,
        [
            ("node", oaseConst.DF_TEST_EQ, "*"),
            ("type", oaseConst.DF_TEST_EQ, "unique"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["node"],
    )
    f3 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_QUEUING,
        [
            ("node", oaseConst.DF_TEST_EQ, "*"),
            ("type", oaseConst.DF_TEST_EQ, "queuing"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["node"],
    )
    f4 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["node"],
    )

    # ルール
    r1 = create_rule_row(
        1,
        "grouping_wildcard",
        f1,
        conclusion_label_settings=[{"type": "grouping"}],
    )
    r2 = create_rule_row(
        2,
        "unique_wildcard",
        f2,
        conclusion_label_settings=[{"type": "unique"}],
    )
    r3 = create_rule_row(
        3,
        "queuing_wildcard",
        f3,
        conclusion_label_settings=[{"type": "queuing"}],
    )
    r4 = create_rule_row(
        4,
        "all",
        f4,
    )

    # 必要なテーブルデータを設定
    filters = [
        f1,
        f2,
        f3,
        f4,
    ]
    rules = [
        r1,
        r2,
        r3,
        r4,
    ]
    test_events = [
        grouping_event := create_event(
            "wildcard",
            "grouping_wildcard",
            custom_labels={"node": "z01", "type": "grouping"},
        ),
        unique_event := create_event(
            "wildcard",
            "unique_wildcard",
            custom_labels={"node": "z02", "type": "unique"},
        ),
        queuing_event := create_event(
            "wildcard",
            "queuing_wildcard",
            custom_labels={"node": "z03", "type": "queuing"},
        ),
    ]

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules)

    # グルーピングが正しく行われることの確認
    conclusions = [
        event
        for event in mock_mongo.test_events
        if event not in [grouping_event, unique_event, queuing_event]
    ]

    # グルーピング: ワイルドカードルールにマッチする
    grouping_info = grouping_event.get("exastro_filter_group")
    assert grouping_info is not None
    assert grouping_info["group_id"] == repr(grouping_event["_id"])
    assert grouping_info["filter_id"] == f1["FILTER_ID"]
    assert grouping_info["is_first_event"]
    assert grouping_event["labels"]["_exastro_evaluated"] == "1"
    assert [
        action_log
        for action_log in ws_db.table_data[oaseConst.T_OASE_ACTION_LOG]
        if repr(grouping_event["_id"]) in action_log["EVENT_ID_LIST"]
        and action_log["RULE_ID"] == r1["RULE_ID"]
    ]

    # ユニーク: ワイルドカードルールにマッチする
    assert "exastro_filter_group" not in unique_event
    assert unique_event["labels"]["_exastro_evaluated"] == "1"
    assert [
        action_log
        for action_log in ws_db.table_data[oaseConst.T_OASE_ACTION_LOG]
        if repr(unique_event["_id"]) in action_log["EVENT_ID_LIST"]
        and action_log["RULE_ID"] == r2["RULE_ID"]
    ]

    # キューイング: ワイルドカードルールにマッチする
    assert "exastro_filter_group" not in queuing_event
    assert queuing_event["labels"]["_exastro_evaluated"] == "1"
    assert [
        action_log
        for action_log in ws_db.table_data[oaseConst.T_OASE_ACTION_LOG]
        if repr(queuing_event["_id"]) in action_log["EVENT_ID_LIST"]
        and action_log["RULE_ID"] == r3["RULE_ID"]
    ]

    # 無条件: ワイルドカードルールにはマッチしないが、無条件ルールにはマッチする
    for conclusion in conclusions:
        conclusion_grouping_info = conclusion.get("exastro_filter_group")
        assert conclusion_grouping_info is not None
        assert conclusion_grouping_info["filter_id"] == f4["FILTER_ID"]
        assert conclusion["labels"]["_exastro_evaluated"] == "1"
