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
from tests.common import create_rule_row, run_test_pattern
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

    test_events = create_events(["e004", "e005", "e008", "e009", "e012", "e013", "e014a", "e014b"], "p050")
    e004, e005, e008, e009, e012, e013, e014a, e014b = test_events

    filters = [f_a7, f_a13]
    rules = [
        create_rule_row(1, "p050:r1", (f_a7, f_a13), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e004["labels"]["_exastro_evaluated"] == "1"
    assert e005["labels"]["_exastro_evaluated"] == "1"
    assert e014b["labels"]["_exastro_evaluated"] == "1"

    assert e012["labels"]["_exastro_undetected"] == "1"
    assert e013["labels"]["_exastro_undetected"] == "1"

    assert e008["labels"]["_exastro_timeout"] == "1"
    assert e009["labels"]["_exastro_timeout"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e014a["labels"]["_exastro_timeout"] == "1"  # _exastro_evaluated == "1" になっている


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

    assert e004["labels"]["_exastro_evaluated"] == "1"
    assert e005["labels"]["_exastro_evaluated"] == "1"
    assert e014a["labels"]["_exastro_evaluated"] == "1"
    assert e014b["labels"]["_exastro_evaluated"] == "1"

    assert e005a["labels"]["_exastro_evaluated"] == "1"
    assert e005b["labels"]["_exastro_evaluated"] == "1"
    assert e008["labels"]["_exastro_evaluated"] == "1"
    assert e009["labels"]["_exastro_evaluated"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e004['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e005['_id'])}')") == 0
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014a['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014b['_id'])}')") == 0
    assert c_1["labels"]["_exastro_rule_name"] == "p050_2:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"

    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e005a['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e005b['_id'])}')") == 0
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e008['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e009['_id'])}')") == 0
    assert c_2["labels"]["_exastro_rule_name"] == "p050_2:r1"
    assert c_2["labels"]["_exastro_undetected"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 8

    assert e004["exastro_filter_group"]["is_first_event"] == "1"
    assert e004["exastro_filter_group"]["group_id"] == e005["exastro_filter_group"]["group_id"]

    assert e014a["exastro_filter_group"]["is_first_event"] == "1"
    assert e014a["exastro_filter_group"]["group_id"] == e014b["exastro_filter_group"]["group_id"]

    assert e005a["exastro_filter_group"]["is_first_event"] == "1"
    assert e005a["exastro_filter_group"]["group_id"] == e005b["exastro_filter_group"]["group_id"]

    assert e008["exastro_filter_group"]["is_first_event"] == "1"
    assert e008["exastro_filter_group"]["group_id"] == e009["exastro_filter_group"]["group_id"]


def test_pattern_051(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとグルーピングのOR"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e004", "e005a", "e005b", "e014b", "e014c", "e014f", "e014g"], "p051")
    e001, e004, e005a, e005b, e014b, e014c, e014f, e014g = test_events

    filters = [f_a7, f_a14]
    rules = [
        create_rule_row(1, "p051:r1", (f_a7, f_a14), filter_operator=oaseConst.DF_OPE_OR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e014b["labels"]["_exastro_evaluated"] == "1"
    assert e014c["labels"]["_exastro_evaluated"] == "1"

    assert e001["labels"]["_exastro_evaluated"] == "1"
    assert e004["labels"]["_exastro_evaluated"] == "1"

    assert e005a["labels"]["_exastro_undetected"] == "1"
    assert e005b["labels"]["_exastro_undetected"] == "1"
    assert e014f["labels"]["_exastro_undetected"] == "1"
    assert e014g["labels"]["_exastro_undetected"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014b['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014c['_id'])}')") == 0
    assert c_1["labels"]["_exastro_rule_name"] == "p051:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"

    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e004['_id'])}')") == 0
    assert c_2["labels"]["_exastro_rule_name"] == "p051:r1"
    assert c_2["labels"]["_exastro_undetected"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 4

    assert e014b["exastro_filter_group"]["is_first_event"] == "1"
    assert e014b["exastro_filter_group"]["group_id"] == e014c["exastro_filter_group"]["group_id"]

    assert e001["exastro_filter_group"]["is_first_event"] == "1"
    assert e001["exastro_filter_group"]["group_id"] == e004["exastro_filter_group"]["group_id"]


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

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e014a["labels"]["_exastro_evaluated"] == "1"
    assert e001["labels"]["_exastro_evaluated"] == "1"
    assert e004["labels"]["_exastro_evaluated"] == "1"
    assert e003["labels"]["_exastro_evaluated"] == "1"
    assert e003a["labels"]["_exastro_evaluated"] == "1"

    assert e006["labels"]["_exastro_timeout"] == "1"
    assert e007["labels"]["_exastro_timeout"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e014a['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e004['_id'])}')") == 0
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e003['_id'])}')") == 0
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e003a['_id'])}')") == 0
    assert c_1["labels"]["_exastro_rule_name"] == "p052:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 5

    assert e014a["exastro_filter_group"]["is_first_event"] == "1"

    assert e001["exastro_filter_group"]["is_first_event"] == "1"
    assert e001["exastro_filter_group"]["group_id"] == e004["exastro_filter_group"]["group_id"]
    assert e001["exastro_filter_group"]["group_id"] == e003["exastro_filter_group"]["group_id"]
    assert e001["exastro_filter_group"]["group_id"] == e003a["exastro_filter_group"]["group_id"]


