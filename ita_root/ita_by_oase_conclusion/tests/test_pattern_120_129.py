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
from tests.filter import f_a20, f_a17, f_a18, f_a19


def test_pattern_120(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピング対象のラベル有無によるグルーピング"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e004", "e007", "e042", "e043"], "p120")
    e001, e004, e007, e042, e043 = test_events

    filters = [f_a20]
    rules = [
        create_rule_row(1, "p120:r1", (f_a20), filter_operator=oaseConst.DF_OPE_NONE,
                        conclusion_label_settings=[["status", "true"]], conclusion_ttl=20)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e001, e004)
    assert_event_evaluated(e007)
    assert_event_evaluated(e042, e043)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 3
    c_1, c_2, c_3 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert c_1["labels"]["status"] == "true"
    assert c_1["labels"]["_exastro_rule_name"] == "p120:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e007['_id'])}')") == 1
    assert c_2["labels"]["status"] == "true"
    assert c_2["labels"]["_exastro_rule_name"] == "p120:r1"
    assert_event_undetected(c_2)

    assert len(c_3["exastro_events"]) == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e042['_id'])}')") == 1
    assert c_3["labels"]["status"] == "true"
    assert c_3["labels"]["_exastro_rule_name"] == "p120:r1"
    assert_event_undetected(c_3)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e001, e004],
        [e007],
        [e042, e043]
    ])


def test_pattern_121(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """「==*」のフィルタ条件を指定した場合のグルーピング"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e004", "e007", "e042", "e043"], "p121")
    e001, e004, e007, e042, e043 = test_events

    filters = [f_a17]
    rules = [
        create_rule_row(1, "p121:r1", (f_a17), filter_operator=oaseConst.DF_OPE_NONE,
                        conclusion_label_settings=[["status", "none"]], conclusion_ttl=20)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e001, e004)
    assert_event_evaluated(e007)
    assert_event_undetected(e042, e043)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert c_1["labels"]["status"] == "none"
    assert c_1["labels"]["_exastro_rule_name"] == "p121:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e007['_id'])}')") == 1
    assert c_2["labels"]["status"] == "none"
    assert c_2["labels"]["_exastro_rule_name"] == "p121:r1"
    assert_event_undetected(c_2)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e001, e004],
        [e007]
    ])


def test_pattern_122(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """「==*」を含む複数のフィルタ条件を指定した場合のグルーピング"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e004", "e007", "e042", "e043"], "p122")
    e001, e004, e007, e042, e043 = test_events

    filters = [f_a18]
    rules = [
        create_rule_row(1, "p122:r1", (f_a18), filter_operator=oaseConst.DF_OPE_NONE,
                        conclusion_label_settings=[{"status": "true"}], conclusion_ttl=20)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e001, e004)
    assert_event_undetected(e007, e042, e043)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert c_1["labels"]["status"] == "true"
    assert c_1["labels"]["_exastro_rule_name"] == "p122:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e001, e004]
    ])


def test_pattern_123(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピング対象のラベル有無とフィルタ条件のラベル有無によるグルーピング"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e004", "e007", "e040", "e042"], "p123")
    e001, e004, e007, e040, e042 = test_events

    filters = [f_a19]
    rules = [
        create_rule_row(1, "p123:r1", (f_a19), filter_operator=oaseConst.DF_OPE_NONE,
                        conclusion_label_settings=[{"status": "true"}], conclusion_ttl=20)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_evaluated(e001, e004)
    assert_event_evaluated(e007)
    assert_event_undetected(e040)
    assert_event_evaluated(e042)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 3
    c_1, c_2, c_3 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert c_1["labels"]["status"] == "true"
    assert c_1["labels"]["_exastro_rule_name"] == "p123:r1"
    assert_event_undetected(c_1)

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e007['_id'])}')") == 1
    assert c_2["labels"]["status"] == "true"
    assert c_2["labels"]["_exastro_rule_name"] == "p123:r1"
    assert_event_undetected(c_2)

    assert len(c_3["exastro_events"]) == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e042['_id'])}')") == 1
    assert c_3["labels"]["status"] == "true"
    assert c_3["labels"]["_exastro_rule_name"] == "p123:r1"
    assert_event_undetected(c_3)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        [e001, e004],
        [e007],
        [e042]
    ])
