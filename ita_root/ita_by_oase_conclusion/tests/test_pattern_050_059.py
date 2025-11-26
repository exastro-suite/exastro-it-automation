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
from tests.filter import f_a7, f_a13, f_a14


def test_pattern_050(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとグルーピングのAND """
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e004", "e005", "e008", "e009", "e012", "e013", "e014i", "e014b"], "p050")
    e004, e005, e008, e009, e012, e013, e014i, e014b = test_events

    filters = [f_a7, f_a13]
    rules = [
        create_rule_row(1, "p050:r1", (f_a7, f_a13), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, before_epoch_runs=4)

    assert_event_timeout(e014i)
    assert_event_evaluated(e004, e005, e014b)
    assert_event_undetected(e012, e013)
    assert_event_timeout(e008, e009)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e004['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014b['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p050:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, expected_groups=[
        [e004, e005],
        [e014b]
    ])


def test_pattern_050_2(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとグルーピングのAND （P50のフィルタ違い）"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e004", "e005", "e005a", "e005b", "e008", "e009", "e014a", "e014b"], "p050_2")
    e004, e005, e005a, e005b, e008, e009, e014a, e014b = test_events

    filters = [f_a7, f_a14]
    rules = [
        create_rule_row(1, "p050_2:r1", (f_a7, f_a14), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e004, e005, e014a, e014b)
    assert_event_evaluated(e005a, e005b, e008, e009)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e004['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014a['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p050_2:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e005a['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e008['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p050_2:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, expected_groups=[
        [e004, e005],
        [e014a, e014b],
        [e005a, e005b],
        [e008, e009],
    ])


def test_pattern_051(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとグルーピングのXOR"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e004", "e005a", "e005b", "e014b", "e014c", "e014f", "e014g"], "p051")
    e001, e004, e005a, e005b, e014b, e014c, e014f, e014g = test_events

    filters = [f_a7, f_a14]
    rules = [
        create_rule_row(1, "p051:r1", (f_a7, f_a14), filter_operator=oaseConst.DF_OPE_XOR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e014b, e014c)
    assert_event_evaluated(e001, e004)
    assert_event_undetected(e005a, e005b, e014f, e014g)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014b['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p051:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p051:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, expected_groups=[
        [e014b, e014c],
        [e001, e004],
    ])


def test_pattern_052(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングの後にグルーピング"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e003", "e003a", "e004", "e006", "e007", "e014a"], "p052")
    e001, e003, e003a, e004, e006, e007, e014a = test_events

    filters = [f_a14, f_a7]
    rules = [
        create_rule_row(1, "p052:r1", (f_a14, f_a7), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, before_epoch_runs=5)

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert_event_timeout(e014a)
    assert_event_evaluated(e006, e007, e001, e004, e003, e003a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e006['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p052:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, expected_groups=[
        [e006, e007],
        [e001, e004, e003, e003a],
    ])
