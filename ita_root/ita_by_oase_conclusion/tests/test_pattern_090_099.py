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
from tests.filter import f_u_b, f_q_a, f_u_c, f_q_3, f_u_a, f_q_b


def test_pattern_090(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークとキューイングをANDで判定した結果、結論イベントが生まれる。生まれた結論イベントをまたルールで判定できるか？ """
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e018", "e025", "e026", "e026a"], "p090")
    e018, e025, e026, e026a = test_events

    filters = [f_u_b, f_q_a]
    rules = [
        create_rule_row(1, "p090:r1", (f_u_b, f_q_a), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"type": "b"}], conclusion_ttl=20),
        create_rule_row(2, "p090:r2", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=5)

    assert_event_evaluated(e018, e025)
    assert_event_evaluated(e026, e026a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 4
    c_1, c_2, c_3, c_4 = conclusion_events

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e018['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert c_1["labels"]["type"] == "b"
    assert c_1["labels"]["_exastro_rule_name"] == "p090:r1"
    assert_event_evaluated(c_1)

    assert len(c_2["exastro_events"]) == 2
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(c_1['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e026['_id'])}')") == 1
    assert c_2["labels"]["type"] == "b"
    assert c_2["labels"]["_exastro_rule_name"] == "p090:r1"
    assert_event_evaluated(c_2)

    assert len(c_3["exastro_events"]) == 2
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(c_2['_id'])}')") == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e026a['_id'])}')") == 1
    assert c_3["labels"]["type"] == "b"
    assert c_3["labels"]["_exastro_rule_name"] == "p090:r1"
    assert_event_evaluated(c_3)

    assert len(c_4["exastro_events"]) == 1
    assert list(c_4["exastro_events"]).count(f"ObjectId('{str(c_3['_id'])}')") == 1
    assert c_4["labels"]["_exastro_rule_name"] == "p090:r2"
    assert_event_undetected(c_4)

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_091(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークとキューイングをXORで判定した結果、結論イベントが生まれる。生まれた結論イベントをまたルールで判定できるか？"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e021", "e022", "e023f", "e026", "e026c"], "p091")
    e021, e022, e023f, e026, e026c = test_events

    filters = [f_u_c, f_q_3, f_u_b]
    rules = [
        create_rule_row(1, "p091:r1", (f_u_c, f_q_3), filter_operator=oaseConst.DF_OPE_XOR,
                        conclusion_label_settings=[{"type": "b"}], conclusion_ttl=20),
        create_rule_row(2, "p091:r2", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_undetected(e021, e022, e023f, e026, e026c)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_092(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニーク→キューイングで判定した結果、結論イベントが生まれる。生まれた結論イベントをまたルールで判定できるか？"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e016", "e017", "e026", "e026a"], "p092")
    e016, e017, e026, e026a = test_events

    filters = [f_u_a, f_q_a]
    rules = [
        create_rule_row(1, "p092:r1", (f_u_a, f_q_a), filter_operator=oaseConst.DF_OPE_ORDER,
                        conclusion_label_settings=[{"type": "a"}], conclusion_ttl=20),
        create_rule_row(2, "p092:r2", (f_u_a), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert_event_undetected(e016, e017)
    assert_event_timeout(e026, e026a)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_093(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """キューイング→ユニークで判定した結果、結論イベントが生まれる。生まれた結論イベントをまたルールで判定できるか？"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e023b", "e023b2", "e023c", "e027", "e028", "e036"], "p093")
    e023b, e023b2, e023c, e027, e028, e036 = test_events

    filters = [f_q_b, f_u_c]
    rules = [
        create_rule_row(1, "p093:r1", (f_q_b, f_u_c), filter_operator=oaseConst.DF_OPE_ORDER,
                        conclusion_label_settings=[{"type": "qb"}], conclusion_ttl=20),
        create_rule_row(2, "p093:r2", (f_q_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=6)

    assert_event_evaluated(e027, e023c)
    assert_event_evaluated(e023b)
    assert_event_evaluated(e028, e023b2)
    assert_event_evaluated(e036)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 6
    r1c_1, r1c_2, r1c_3, r2c_1, r2c_2, r2c_3 = conclusion_events

    assert len(r1c_1["exastro_events"]) == 2
    assert list(r1c_1["exastro_events"]).count(f"ObjectId('{str(e027['_id'])}')") == 1
    assert list(r1c_1["exastro_events"]).count(f"ObjectId('{str(e023c['_id'])}')") == 1
    assert r1c_1["labels"]["type"] == "qb"
    assert r1c_1["labels"]["_exastro_rule_name"] == "p093:r1"
    assert_event_evaluated(r1c_1)

    assert len(r1c_2["exastro_events"]) == 2
    assert list(r1c_2["exastro_events"]).count(f"ObjectId('{str(r1c_1['_id'])}')") == 1
    assert list(r1c_2["exastro_events"]).count(f"ObjectId('{str(e023b['_id'])}')") == 1
    assert r1c_2["labels"]["type"] == "qb"
    assert r1c_2["labels"]["_exastro_rule_name"] == "p093:r1"
    assert_event_evaluated(r1c_2)

    assert len(r1c_3["exastro_events"]) == 2
    assert list(r1c_3["exastro_events"]).count(f"ObjectId('{str(e028['_id'])}')") == 1
    assert list(r1c_3["exastro_events"]).count(f"ObjectId('{str(e023b2['_id'])}')") == 1
    assert r1c_3["labels"]["type"] == "qb"
    assert r1c_3["labels"]["_exastro_rule_name"] == "p093:r1"
    assert_event_evaluated(r1c_3)

    assert len(r2c_1["exastro_events"]) == 1
    assert list(r2c_1["exastro_events"]).count(f"ObjectId('{str(r1c_2['_id'])}')") == 1
    assert r2c_1["labels"]["_exastro_rule_name"] == "p093:r2"
    assert_event_undetected(r2c_1)

    assert len(r2c_2["exastro_events"]) == 1
    assert list(r2c_2["exastro_events"]).count(f"ObjectId('{str(e036['_id'])}')") == 1
    assert r2c_2["labels"]["_exastro_rule_name"] == "p093:r2"
    assert_event_undetected(r2c_2)

    assert len(r2c_3["exastro_events"]) == 1
    assert list(r2c_3["exastro_events"]).count(f"ObjectId('{str(r1c_3['_id'])}')") == 1
    assert r2c_3["labels"]["_exastro_rule_name"] == "p093:r2"
    assert_event_undetected(r2c_3)

    # グルーピングの確認
    assert_grouped_events(test_events, [])
