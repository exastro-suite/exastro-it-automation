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

import backyard_main as bm
from common_libs.oase.const import oaseConst
from tests.common import create_rule_row, judge_time
from tests.event import create_events
from tests.filter import f_u_b, f_u_c


def run_test_pattern(
    g,
    ws_db,
    mock_mongo,
    mock_datetime,
    test_events,
    filters,
    rules,
    actions,
):
    """共通テストロジック"""
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = filters
    ws_db.table_data["T_OASE_RULE"] = rules
    ws_db.table_data["T_OASE_ACTION"] = actions

    minimum_fetched_time = min(
        (event["labels"]["_exastro_fetched_time"] for event in test_events),
    )
    maximum_fetched_time = max(
        (event["labels"]["_exastro_fetched_time"] for event in test_events),
    )
    for jt in range(minimum_fetched_time, maximum_fetched_time + 1):
        mock_mongo.test_events = [
            event
            for event in test_events
            if event["labels"]["_exastro_fetched_time"] <= jt
        ]
        mock_datetime.datetime.now.return_value.timestamp.return_value = jt
        bm.backyard_main("org1", "ws1")

    tracebacks = [log for _, log in g.applogger.logs if "Traceback" in log]
    if tracebacks:
        print(tracebacks[0])
    assert not tracebacks

    import pprint

    pprint.pprint(test_events)


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
    filters = [f_u_b, f_u_c]
    rules = [
        create_rule_row(1, "p040:r1", (f_u_b, f_u_c), filter_operator=oaseConst.DF_OPE_AND),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    # TODO: assertの修正を行うこと
    assert (
        len(
            {
                id
                for id in (
                    event.get("exastro_filter_group", {}).get("group_id")
                    for event in test_events
                )
                if id is not None
            }
        )
        == 1
    )


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
    filters = [f_u_b, f_u_c]
    rules = [
        create_rule_row(1, "p041:r1", (f_u_b, f_u_c), filter_operator=oaseConst.DF_OPE_OR),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    # TODO: assertの修正を行うこと
    assert (
        len(
            {
                id
                for id in (
                    event.get("exastro_filter_group", {}).get("group_id")
                    for event in test_events
                )
                if id is not None
            }
        )
        == 1
    )


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
    filters = [f_u_b, f_u_c]
    rules = [
        create_rule_row(1, "p042:r1", (f_u_b, f_u_c), filter_operator=oaseConst.DF_OPE_ORDER),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    # TODO: assertの修正を行うこと
    assert (
        len(
            {
                id
                for id in (
                    event.get("exastro_filter_group", {}).get("group_id")
                    for event in test_events
                )
                if id is not None
            }
        )
        == 1
    )


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
    filters = [f_u_b]
    rules = [
        create_rule_row(1, "p043:r1", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    # TODO: assertの修正を行うこと
    assert (
        len(
            {
                id
                for id in (
                    event.get("exastro_filter_group", {}).get("group_id")
                    for event in test_events
                )
                if id is not None
            }
        )
        == 1
    )


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
    filters = [f_u_b]
    rules = [
        create_rule_row(1, "p044:r1", (f_u_b), filter_operator=oaseConst.DF_OPE_NONE),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    # TODO: assertの修正を行うこと
    assert (
        len(
            {
                id
                for id in (
                    event.get("exastro_filter_group", {}).get("group_id")
                    for event in test_events
                )
                if id is not None
            }
        )
        == 1
    )
