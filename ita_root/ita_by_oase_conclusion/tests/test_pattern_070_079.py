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

    assert e001["labels"]["_exastro_evaluated"] == "1"
    assert e004["labels"]["_exastro_evaluated"] == "1"
    assert e024["labels"]["_exastro_evaluated"] == "1"

    assert e005a["labels"]["_exastro_evaluated"] == "1"
    assert e005b["labels"]["_exastro_evaluated"] == "1"
    assert e025["labels"]["_exastro_evaluated"] == "1"

    assert e037["labels"]["_exastro_timeout"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 4

    assert e001["exastro_filter_group"]["is_first_event"] is True
    assert e001["exastro_filter_group"]["group_id"] == e004["exastro_filter_group"]["group_id"]

    assert e005a["exastro_filter_group"]["is_first_event"] is True
    assert e005a["exastro_filter_group"]["group_id"] == e005b["exastro_filter_group"]["group_id"]


def test_pattern_071(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとキューイングのOR(グルーピングとキューイングがマッチしない場合とキューイングしたイベントが使われる場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e006", "e007", "e014b", "e014c", "e027", "e027a"], "p071")
    e006, e007, e014b, e014c, e027, e027a = test_events

    filters = [f_a8, f_q_b]
    rules = [
        create_rule_row(1, "p071:r1", (f_a8, f_q_b), filter_operator=oaseConst.DF_OPE_OR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e014b["labels"]["_exastro_evaluated"] == "1"
    assert e014c["labels"]["_exastro_evaluated"] == "1"
    assert e006["labels"]["_exastro_evaluated"] == "1"
    assert e007["labels"]["_exastro_evaluated"] == "1"

    assert e027["labels"]["_exastro_evaluated"] == "1"
    assert e027a["labels"]["_exastro_evaluated"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 4

    assert e014b["exastro_filter_group"]["is_first_event"] is True
    assert e014b["exastro_filter_group"]["group_id"] == e014c["exastro_filter_group"]["group_id"]
    assert e014b["exastro_filter_group"]["group_id"] == e006["exastro_filter_group"]["group_id"]
    assert e014b["exastro_filter_group"]["group_id"] == e007["exastro_filter_group"]["group_id"]


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

    assert e011["labels"]["_exastro_evaluated"] == "1"
    assert e012["labels"]["_exastro_evaluated"] == "1"
    assert e025["labels"]["_exastro_evaluated"] == "1"

    assert e026b["labels"]["_exastro_timeout"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 2

    assert e011["exastro_filter_group"]["is_first_event"] is True
    assert e011["exastro_filter_group"]["group_id"] == e012["exastro_filter_group"]["group_id"]


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

    assert e024["labels"]["_exastro_timeout"] == "1"
    assert e011["labels"]["_exastro_timeout"] == "1"
    assert e012["labels"]["_exastro_timeout"] == "1"

    assert e027["labels"]["_exastro_undetected"] == "1"
    assert e027a["labels"]["_exastro_undetected"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 0


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

    assert e014a["labels"]["_exastro_timeout"] == "1"
    assert e014b["labels"]["_exastro_timeout"] == "1"
    assert e014c["labels"]["_exastro_timeout"] == "1"

    assert e006["labels"]["_exastro_evaluated"] == "1"
    assert e007["labels"]["_exastro_evaluated"] == "1"
    assert e025["labels"]["_exastro_evaluated"] == "1"

    assert e008["labels"]["_exastro_evaluated"] == "1"
    assert e026["labels"]["_exastro_evaluated"] == "1"

    assert e009["labels"]["_exastro_undetected"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 3

    assert e006["exastro_filter_group"]["is_first_event"] is True
    assert e006["exastro_filter_group"]["group_id"] == e007["exastro_filter_group"]["group_id"]

    assert e008["exastro_filter_group"]["is_first_event"] is True


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

    assert e027["labels"]["_exastro_evaluated"] == "1"
    assert e002["labels"]["_exastro_evaluated"] == "1"
    assert e003["labels"]["_exastro_evaluated"] == "1"
    assert e003a["labels"]["_exastro_evaluated"] == "1"
    assert e005["labels"]["_exastro_evaluated"] == "1"

    assert e005a["labels"]["_exastro_evaluated"] == "1"
    assert e005b["labels"]["_exastro_evaluated"] == "1"

    assert e028["labels"]["_exastro_timeout"] == "1"
    assert e028a["labels"]["_exastro_timeout"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e027a["labels"]["_exastro_evaluated"] == "1"  # _exastro_timeout == "1" になっている

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 3

    assert e002["exastro_filter_group"]["is_first_event"] is True
    assert e002["exastro_filter_group"]["group_id"] == e003["exastro_filter_group"]["group_id"]
    assert e002["exastro_filter_group"]["group_id"] == e003a["exastro_filter_group"]["group_id"]
    assert e002["exastro_filter_group"]["group_id"] == e005["exastro_filter_group"]["group_id"]

    assert e005a["exastro_filter_group"]["is_first_event"] is True
    assert e005a["exastro_filter_group"]["group_id"] == e005b["exastro_filter_group"]["group_id"]
