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
from tests.filter import f_q_a, f_q_b, f_u_a, f_u_b


def test_pattern_080(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークとキューイングのAND"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e016", "e017", "e025", "e026", "e034"], "p080")
    e016, e017, e025, e026, e034 = test_events

    filters = [f_u_a, f_q_a]
    rules = [
        create_rule_row(1, "p080:r1", (f_u_a, f_q_a), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_timeout(e034)
    assert_event_evaluated(e016, e025)
    assert_event_evaluated(e017, e026)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e016['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p080:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e017['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e026['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p080:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_082(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークとキューイングのOR(ユニークまたはキューイング）"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e018", "e018c", "e026", "e026a", "e026g"], "p082")
    e018, e018c, e026, e026a, e026g = test_events

    filters = [f_u_b, f_q_a]
    rules = [
        create_rule_row(1, "p082:r1", (f_u_b, f_q_a), filter_operator=oaseConst.DF_OPE_OR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e018)
    assert_event_evaluated(e026)
    assert_event_evaluated(e026g)
    assert_event_undetected(e018c, e026a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 3
    c_1, c_2, c_3 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e018['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p082:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e026['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p082:r1"
    assert_event_undetected(c_2)

    assert len(c_3["exastro_events"]) == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e026g['_id'])}')") == 1
    assert c_3["labels"]["_exastro_rule_name"] == "p082:r1"
    assert_event_undetected(c_3)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_083(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークの後にキューイング"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e018", "e018c", "e025", "e026", "e026b"], "p083")
    e018, e018c, e025, e026, e026b = test_events

    filters = [f_u_b, f_q_a]
    rules = [
        create_rule_row(1, "p083:r1", (f_u_b, f_q_a), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e018, e025)
    assert_event_timeout(e026b, e018c, e026)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e018['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p083:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_084(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """キューイングの後にユニーク"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e015b", "e017a", "e028", "e028c"], "p084")
    e015b, e017a, e028, e028c = test_events

    filters = [f_q_b, f_u_a]
    rules = [
        create_rule_row(1, "p084:r1", (f_q_b, f_u_a), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_timeout(e015b)
    assert_event_evaluated(e028, e017a)
    assert_event_timeout(e028c)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e028['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e017a['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p084:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, [])
