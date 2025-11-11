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
    """ユニークとユニークのAND"""
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
    """ユニークとユニークのOR"""
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


def test_pattern_051(
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


def test_pattern_052(
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
