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
from tests.filter import f_q_1, f_q_3, f_q_4, f_q_a, f_q_b, f_q_c, f_q_d


def test_pattern_063(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """キューイングの後にキューイング(→で続く場合と、→で続かない場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e026", "e026a", "e026c", "e026d", "e030b", "e030c", "e031", "e031a"], "p063")
    e026, e026a, e026c, e026d, e030b, e030c, e031, e031a = test_events

    filters = [f_q_c, f_q_d, f_q_3]
    rules = [
        create_rule_row(1, "p063:r1", (f_q_c, f_q_3), filter_operator=oaseConst.DF_OPE_ORDER),
        create_rule_row(2, "p063:r2", (f_q_d, f_q_3), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e030b, e026)
    assert_event_evaluated(e030c, e026c)
    assert_event_evaluated(e031, e026a)
    assert_event_evaluated(e031a, e026d)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 4
    c_1, c_2, c_3, c_4 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e030b['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e026['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p063:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e030c['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e026c['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p063:r1"
    assert_event_undetected(c_2)

    assert len(c_3["exastro_events"]) == 2
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e031['_id'])}')") == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e026a['_id'])}')") == 1
    assert c_3["labels"]["_exastro_rule_name"] == "p063:r2"
    assert_event_undetected(c_3)

    assert len(c_4["exastro_events"]) == 2
    assert list(c_4["exastro_events"]).count(f"ObjectId('{str(e031a['_id'])}')") == 1
    assert list(c_4["exastro_events"]).count(f"ObjectId('{str(e026d['_id'])}')") == 1
    assert c_4["labels"]["_exastro_rule_name"] == "p063:r2"
    assert_event_undetected(c_4)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_065(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """キューイングとキューイングのAND(ANDでマッチする場合とANDでマッチしない場合とr1でマッチしたイベントがr2で再利用されない場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e025", "e026b", "e027", "e027a", "e031", "e031a", "e026e", "e026f"], "p065")
    e025, e026b, e027, e027a, e031, e031a, e026e, e026f = test_events

    filters = [f_q_a, f_q_4, f_q_1]
    rules = [
        create_rule_row(1, "p065:r1", (f_q_a, f_q_4), filter_operator=oaseConst.DF_OPE_AND),
        create_rule_row(2, "p065:r2", (f_q_a, f_q_1), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=6)

    assert_event_evaluated(e025, e027)
    assert_event_evaluated(e026b, e027a)
    assert_event_timeout(e031, e031a, e026e, e026f)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e027['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p065:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e026b['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e027a['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p065:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_066(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """キューイングとキューイングのXOR(XORでマッチする場合とXORでマッチしない場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e025a", "e025b", "e030", "e030a", "e027", "e027a", "e032a", "e032b"], "p066")
    e025a, e025b, e030, e030a, e027, e027a, e032a, e032b = test_events

    filters = [f_q_a, f_q_b, f_q_3, f_q_1]
    rules = [
        create_rule_row(1, "p066:r1", (f_q_a, f_q_3), filter_operator=oaseConst.DF_OPE_XOR),
        create_rule_row(2, "p066:r2", (f_q_b, f_q_1), filter_operator=oaseConst.DF_OPE_XOR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e025a)
    assert_event_evaluated(e025b)
    assert_event_evaluated(e030)
    assert_event_evaluated(e030a)
    assert_event_undetected(e027, e027a, e032a, e032b)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 4
    c_1, c_2, c_3, c_4 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e025a['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p066:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e025b['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p066:r1"
    assert_event_undetected(c_2)

    assert len(c_3["exastro_events"]) == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e030['_id'])}')") == 1
    assert c_3["labels"]["_exastro_rule_name"] == "p066:r1"
    assert_event_undetected(c_3)

    assert len(c_4["exastro_events"]) == 1
    assert list(c_4["exastro_events"]).count(f"ObjectId('{str(e030a['_id'])}')") == 1
    assert c_4["labels"]["_exastro_rule_name"] == "p066:r1"
    assert_event_undetected(c_4)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_067(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """キューイング単独"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e027", "e028"], "p067")
    e027, e028 = test_events

    filters = [f_q_a]
    rules = [
        create_rule_row(1, "p067:r1", (f_q_a), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_undetected(e027, e028)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])
