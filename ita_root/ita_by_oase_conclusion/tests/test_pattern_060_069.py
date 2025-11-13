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

    assert e030b["labels"]["_exastro_evaluated"] == "1"
    assert e030c["labels"]["_exastro_evaluated"] == "1"
    assert e026["labels"]["_exastro_evaluated"] == "1"
    assert e026c["labels"]["_exastro_evaluated"] == "1"

    assert e026a["labels"]["_exastro_evaluated"] == "1"
    assert e031["labels"]["_exastro_evaluated"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e026d["labels"]["_exastro_evaluated"] == "1"  # _exastro_timeout == "1" になっている
    assert e031a["labels"]["_exastro_evaluated"] == "1"  # _exastro_timeout == "1" になっている


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

    assert e025["labels"]["_exastro_evaluated"] == "1"
    assert e027["labels"]["_exastro_evaluated"] == "1"
    assert e026b["labels"]["_exastro_evaluated"] == "1"
    assert e027a["labels"]["_exastro_evaluated"] == "1"

    assert e031["labels"]["_exastro_timeout"] == "1"
    assert e031a["labels"]["_exastro_timeout"] == "1"

    assert e026e["labels"]["_exastro_timeout"] == "1"
    assert e026f["labels"]["_exastro_timeout"] == "1"


def test_pattern_066(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """キューイングとキューイングのOR(ORでマッチする場合とORでマッチしない場合)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e024", "e024a", "e030", "e030a", "e027", "e027a", "e032a", "e032b"], "p066")
    e024, e024a, e030, e030a, e027, e027a, e032a, e032b = test_events

    filters = [f_q_a, f_q_b, f_q_3, f_q_1]
    rules = [
        create_rule_row(1, "p066:r1", (f_q_a, f_q_3), filter_operator=oaseConst.DF_OPE_OR),
        create_rule_row(2, "p066:r2", (f_q_b, f_q_1), filter_operator=oaseConst.DF_OPE_OR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e024["labels"]["_exastro_evaluated"] == "1"
    assert e024a["labels"]["_exastro_evaluated"] == "1"
    assert e030["labels"]["_exastro_evaluated"] == "1"
    assert e030a["labels"]["_exastro_evaluated"] == "1"

    assert e027["labels"]["_exastro_undetected"] == "1"
    assert e027a["labels"]["_exastro_undetected"] == "1"
    assert e032a["labels"]["_exastro_undetected"] == "1"
    assert e032b["labels"]["_exastro_undetected"] == "1"


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

    assert e027["labels"]["_exastro_undetected"] == "1"
    assert e028["labels"]["_exastro_undetected"] == "1"
