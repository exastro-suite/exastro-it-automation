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

    test_events = create_events(["e016", "e017", "e025", "e033", "e034"], "p080")
    e016, e017, e025, e033, e034 = test_events

    filters = [f_u_a, f_q_a]
    rules = [
        create_rule_row(1, "p080:r1", (f_u_a, f_q_a), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e016["labels"]["_exastro_evaluated"] == "1"

    assert e017["labels"]["_exastro_evaluated"] == "1"
    assert e025["labels"]["_exastro_evaluated"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e034["labels"]["_exastro_evaluated"] == "1"  # _exastro_timeout == "1" になっている
    assert e033["labels"]["_exastro_timeout"] == "1"  # _exastro_evaluated == "1" になっている


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

    test_events = create_events(["e018", "e018c", "e026", "e026a", "e026c"], "p082")
    e018, e018c, e026, e026a, e026c = test_events

    filters = [f_u_b, f_q_a]
    rules = [
        create_rule_row(1, "p082:r1", (f_u_b, f_q_a), filter_operator=oaseConst.DF_OPE_OR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e018["labels"]["_exastro_evaluated"] == "1"
    assert e026["labels"]["_exastro_evaluated"] == "1"

    assert e018c["labels"]["_exastro_undetected"] == "1"
    assert e026a["labels"]["_exastro_undetected"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e026c["labels"]["_exastro_evaluated"] == "1"  # _exastro_undetected == "1" になっている


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

    assert e018["labels"]["_exastro_evaluated"] == "1"
    assert e025["labels"]["_exastro_evaluated"] == "1"

    assert e026b["labels"]["_exastro_timeout"] == "1"  # _exastro_timeout == "1" になっている
    assert e018c["labels"]["_exastro_timeout"] == "1"
    assert e026["labels"]["_exastro_timeout"] == "1"


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

    test_events = create_events(["e015", "e017a", "e028", "e028a"], "p084")
    e015, e017a, e028, e028a = test_events

    filters = [f_q_b, f_u_a]
    rules = [
        create_rule_row(1, "p084:r1", (f_q_b, f_u_a), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e015["labels"]["_exastro_timeout"] == "1"

    assert e028a["labels"]["_exastro_timeout"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e028["labels"]["_exastro_evaluated"] == "1"    # _exastro_timeout == "1" になっている
    assert e017a["labels"]["_exastro_evaluated"] == "1"    # _exastro_undetected == "1" になっている
