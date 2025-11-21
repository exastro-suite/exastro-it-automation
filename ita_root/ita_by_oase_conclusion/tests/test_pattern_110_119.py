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

from common_libs.oase.const import oaseConst
from tests.common import (
    create_rule_row,
    run_test_pattern,
    assert_grouped_events,
    assert_event_timeout,
    assert_event_evaluated,
    assert_event_undetected
)
from tests.event import create_events
from tests.filter import f_q_c, f_q_3


def test_pattern_110(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """AB両方のフィルタにマッチする場合(→)１"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e030", "e030a"], "p110")
    e030, e030a = test_events

    filters = [f_q_c, f_q_3]
    rules = [
        create_rule_row(1, "p110:r1", (f_q_c, f_q_3), filter_operator=oaseConst.DF_OPE_ORDER)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_timeout(e030, e030a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_111(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """AB両方のフィルタにマッチする場合(→)２"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e030", "e030a", "e026", "e026c"], "p111")
    e030, e030a, e026, e026c = test_events

    filters = [f_q_c, f_q_3]
    rules = [
        create_rule_row(1, "p111:r1", (f_q_c, f_q_3), filter_operator=oaseConst.DF_OPE_ORDER)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_timeout(e030, e030a, e026, e026c)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_112(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """AB両方のフィルタにマッチする場合(AND)１"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e030", "e030a"], "p112")
    e030, e030a = test_events

    filters = [f_q_c, f_q_3]
    rules = [
        create_rule_row(1, "p112:r1", (f_q_c, f_q_3), filter_operator=oaseConst.DF_OPE_AND)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e030, e030a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e030['_id'])}')") == 2
    assert c_1["labels"]["_exastro_rule_name"] == "p112:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e030a['_id'])}')") == 2
    assert c_2["labels"]["_exastro_rule_name"] == "p112:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_113(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """AB両方のフィルタにマッチする場合(→)２"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e030", "e030a", "e026", "e026c"], "p113")
    e030, e030a, e026, e026c = test_events

    filters = [f_q_c, f_q_3]
    rules = [
        create_rule_row(1, "p113:r1", (f_q_c, f_q_3), filter_operator=oaseConst.DF_OPE_AND)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e030, e030a)
    assert_event_timeout(e026, e026c)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e030['_id'])}')") == 2
    assert c_1["labels"]["_exastro_rule_name"] == "p113:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e030a['_id'])}')") == 2
    assert c_2["labels"]["_exastro_rule_name"] == "p113:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_114(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """AB両方のフィルタにマッチする場合(AND)１"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e030", "e030a"], "p114")
    e030, e030a = test_events

    filters = [f_q_c, f_q_3]
    rules = [
        create_rule_row(1, "p114:r1", (f_q_c, f_q_3), filter_operator=oaseConst.DF_OPE_XOR)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_undetected(e030, e030a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_115(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """AB両方のフィルタにマッチする場合(XOR)２"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e030", "e030a", "e026", "e026c"], "p115")
    e030, e030a, e026, e026c = test_events

    filters = [f_q_c, f_q_3]
    rules = [
        create_rule_row(1, "p115:r1", (f_q_c, f_q_3), filter_operator=oaseConst.DF_OPE_XOR)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_undetected(e030, e030a)
    assert_event_evaluated(e026, e026c)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e026['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p115:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e026c['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p115:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [])
