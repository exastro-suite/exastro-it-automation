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
                        conclusion_label_inheritance_flag={"event"}, conclusion_label_settings=[{"type": "b"}], conclusion_ttl=20),
        create_rule_row(1, "p090:r2", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e018["labels"]["_exastro_evaluated"] == "1"
    assert e025["labels"]["_exastro_evaluated"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e026["labels"]["_exastro_evaluated"] == "1"

    assert e026a["labels"]["_exastro_evaluated"] == "1"


def test_pattern_091(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ユニークとキューイングをORで判定した結果、結論イベントが生まれる。生まれた結論イベントをまたルールで判定できるか？"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e021", "e022", "e023f", "e026", "e026c"], "p091")
    e021, e022, e023f, e026, e026c = test_events

    filters = [f_u_c, f_q_3, f_u_b]
    rules = [
        create_rule_row(1, "p091:r1", (f_u_c, f_q_3), filter_operator=oaseConst.DF_OPE_OR,
                        conclusion_label_inheritance_flag={"event"}, conclusion_label_settings=[{"type": "b"}], conclusion_ttl=20),
        create_rule_row(1, "p091:r2", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e021["labels"]["_exastro_undetected"] == "1"
    assert e022["labels"]["_exastro_undetected"] == "1"

    assert e023f["labels"]["_exastro_undetected"] == "1"
    assert e026["labels"]["_exastro_undetected"] == "1"

    assert e026c["labels"]["_exastro_undetected"] == "1"


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
                        conclusion_label_inheritance_flag={"event"}, conclusion_label_settings=[{"type": "a"}], conclusion_ttl=20),
        create_rule_row(1, "p092:r2", (f_u_a), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e016["labels"]["_exastro_undetected"] == "1"
    assert e017["labels"]["_exastro_undetected"] == "1"

    assert e026["labels"]["_exastro_timeout"] == "1"
    assert e026a["labels"]["_exastro_timeout"] == "1"


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
                        conclusion_label_inheritance_flag={"event"}, conclusion_label_settings=[{"type": "qb"}], conclusion_ttl=20),
        create_rule_row(1, "p093:r2", (f_q_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=6)

    assert e027["labels"]["_exastro_evaluated"] == "1"
    assert e023c["labels"]["_exastro_evaluated"] == "1"

    assert e023b["labels"]["_exastro_evaluated"] == "1"

    assert e028["labels"]["_exastro_evaluated"] == "1"
    assert e023b2["labels"]["_exastro_evaluated"] == "1"

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e036["labels"]["_exastro_timeout"] == "1"
