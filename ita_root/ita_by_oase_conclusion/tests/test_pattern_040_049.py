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
from tests.common import create_rule_row, run_test_pattern, assert_grouped_events
from tests.event import create_events
from tests.filter import f_u_b, f_u_c


def test_pattern_040(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークとユニークのAND"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e018", "e018b", "e021"], "p040")
    e018, e018b, e021 = test_events

    filters = [f_u_b, f_u_c]
    rules = [
        create_rule_row(1, "p040:r1", (f_u_b, f_u_c), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e018["labels"]["_exastro_evaluated"] == "1"
    assert e021["labels"]["_exastro_evaluated"] == "1"

    assert e018b["labels"]["_exastro_timeout"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e018['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e021['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p040:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_041(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークとユニークのOR"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e018", "e019", "e021", "e023b"], "p041")
    e018, e019, e021, e023b = test_events

    filters = [f_u_b, f_u_c]
    rules = [
        create_rule_row(1, "p041:r1", (f_u_b, f_u_c), filter_operator=oaseConst.DF_OPE_OR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e018["labels"]["_exastro_evaluated"] == "1"
    assert e023b["labels"]["_exastro_evaluated"] == "1"

    assert e019["labels"]["_exastro_undetected"] == "1"
    assert e021["labels"]["_exastro_undetected"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e018['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p041:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"

    assert len(c_2["exastro_events"]) == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e023b['_id'])}')") == 1
    assert c_2["labels"]["_exastro_rule_name"] == "p041:r1"
    assert c_2["labels"]["_exastro_undetected"] == "1"

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_042(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークの後にユニーク"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e019", "e019b", "e023b", "e023b2"], "p042")
    e019, e019b, e023b, e023b2 = test_events

    filters = [f_u_b, f_u_c]
    rules = [
        create_rule_row(1, "p042:r1", (f_u_b, f_u_c), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e019b["labels"]["_exastro_timeout"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e019["labels"]["_exastro_evaluated"] == "1"  # _exastro_undetected == "1" になっている
    assert e023b["labels"]["_exastro_evaluated"] == "1"  # _exastro_undetected == "1" になっている
    assert e023b2["labels"]["_exastro_timeout"] == "1"  # _exastro_undetected == "1" になっている

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 2
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e019['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e023b['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p042:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_043(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニーク単独"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e018"], "p043")
    e018 = test_events[0]

    filters = [f_u_b]
    rules = [
        create_rule_row(1, "p043:r1", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e018["labels"]["_exastro_evaluated"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e018['_id'])}')") == 1
    assert c_1["labels"]["_exastro_rule_name"] == "p043:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"

    # グルーピングの確認
    assert_grouped_events(test_events, [])


def test_pattern_044(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニーク単独でマッチして未知"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e018", "e018a"], "p044")
    e018, e018a = test_events

    filters = [f_u_b]
    rules = [
        create_rule_row(1, "p044:r1", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e018["labels"]["_exastro_undetected"] == "1"
    assert e018a["labels"]["_exastro_undetected"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 0

    # グルーピングの確認
    assert_grouped_events(test_events, [])
