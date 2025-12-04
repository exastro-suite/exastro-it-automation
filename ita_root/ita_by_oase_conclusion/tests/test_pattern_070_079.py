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
from tests.filter import f_a7, f_a8, f_a10, f_q_a, f_q_b


def test_pattern_070(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとキューイングのAND(グルーピングとキューイングがマッチする場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e004", "e005a", "e005b", "e024", "e025", "e037"], "p070")
    e001, e004, e005a, e005b, e024, e025, e037 = test_events

    filters = [f_a7, f_q_a]
    rules = [
        create_rule_row(1, "p070:r1", (f_a7, f_q_a), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e001, e004, e024)
    assert_event_evaluated(e005a, e005b, e025)
    assert_event_timeout(e037)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e024['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p070:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e005a['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p070:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e001, e004],
        [e005a, e005b],
    ])


def test_pattern_071(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとキューイングのXOR(グルーピングとキューイングがマッチしない場合とキューイングしたイベントが使われる場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e006", "e007", "e014b", "e014c", "e027", "e027a"], "p071")
    e006, e007, e014b, e014c, e027, e027a = test_events

    filters = [f_a8, f_q_b]
    rules = [
        create_rule_row(1, "p071:r1", (f_a8, f_q_b), filter_operator=oaseConst.DF_OPE_XOR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e014b, e014c, e006, e007)
    assert_event_evaluated(e027)
    assert_event_evaluated(e027a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 3
    c_1, c_2, c_3 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014b['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p071:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e027['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p071:r1"
    assert_event_undetected(c_2)

    assert len(c_3["exastro_events"]) == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e027a['_id'])}')") == 1
    assert c_3["labels"]["_exastro_rule_name"] == "p071:r1"
    assert_event_undetected(c_3)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e014b, e014c, e006, e007]
    ])


def test_pattern_072(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングの後にキューイング(→で続く場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e011", "e012", "e025", "e026b"], "p072")
    e011, e012, e025, e026b = test_events

    filters = [f_a10, f_q_a]
    rules = [
        create_rule_row(1, "p072:r1", (f_a10, f_q_a), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e011, e012, e025)
    assert_event_timeout(e026b)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e011['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p072:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e011, e012]
    ])


def test_pattern_073(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングの後にキューイング(→で続かない場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e011", "e012", "e024", "e027", "e027a"], "p073")
    e011, e012, e024, e027, e027a = test_events

    filters = [f_a10, f_q_a]
    rules = [
        create_rule_row(1, "p073:r1", (f_a10, f_q_a), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_timeout(e024, e011, e012)
    assert_event_undetected(e027, e027a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_077(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとキューイングのAND(グルーピングの組み合わせ条件が「以外を対象とする」)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e006", "e007", "e008", "e009", "e014a", "e014b", "e014c", "e025", "e026"], "p077")
    e006, e007, e008, e009, e014a, e014b, e014c, e025, e026 = test_events

    filters = [f_a8, f_q_a]
    rules = [
        create_rule_row(1, "p077:r1", (f_a8, f_q_a), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_timeout(e014a, e014b, e014c)
    assert_event_evaluated(e006, e007, e025)
    assert_event_evaluated(e008, e026)
    assert_event_undetected(e009)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e006['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p077:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e008['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e026['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p077:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e006, e007],
        [e008]
    ])


def test_pattern_079(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとキューイングのAND(グルーピングの組み合わせ条件が「以外を対象とする」)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e002", "e003", "e003a", "e005", "e005a", "e005b", "e027", "e027a", "e028", "e028a"], "p079")
    e002, e003, e003a, e005, e005a, e005b, e027, e027a, e028, e028a = test_events

    filters = [f_q_b, f_a7]
    rules = [
        create_rule_row(1, "p079:r1", (f_q_b, f_a7), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e027, e002, e003, e003a, e005, e005a, e005b)
    assert_event_timeout(e027a, e028, e028a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e027['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e002['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p079:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e002, e003, e003a, e005, e005a, e005b]
    ])
