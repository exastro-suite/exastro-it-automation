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

import itertools

from common_libs.oase.const import oaseConst
from tests.common import create_rule_row, run_test_pattern
from tests.event import create_events
import tests.filter as filter


def test_pattern_006(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """「「以外を対象とする」のグルーピング + フィルター条件」が複数ルールある"""
    g = patch_global_g

    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    # イベント
    test_events = create_events(
        [f"e{n:03}" for n in itertools.chain(range(1, 14 + 1), [999])], "p6"
    )

    # ルール
    r1 = create_rule_row(
        1,
        "p6:r1",
        filter.f_a6,
        action_id="action1",
    )
    r2 = create_rule_row(
        2,
        "p6:r2",
        filter.f_a4,
        action_id="action2",
    )
    r3 = create_rule_row(
        3,
        "p6:r3",
        filter.f_a99,
    )

    # 必要なテーブルデータを設定
    filters = [
        filter.f_a6,
        filter.f_a4,
        filter.f_a99,
    ]
    rules = [
        r1,
        r2,
        r3,
    ]
    actions = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0},
        {"ACTION_ID": "action2", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0},
    ]
    run_test_pattern(
        g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions
    )

    # e001～e005が同じグループになることを確認
    group = {}
    for event in mock_mongo.test_events:
        if (event_id := event.get("event", {}).get("event_id")) in {
            "e001",
            "e002",
            "e003",
            "e004",
            "e005",
        }:
            group_id = event.get("exastro_filter_group", {}).get("group_id")
            group.setdefault(group_id, []).append(event_id)
    assert len(group) == 1


def test_pattern_009(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """「「以外を対象とする」のグルーピング + フィルター条件」が複数ルールある"""
    g = patch_global_g

    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(
        itertools.chain(
            [f"e{n:03}" for n in range(10, 16 + 1)], ["e018", "e020", "e021"]
        ),
        "p9",
    )

    # ルール
    r1 = create_rule_row(
        1,
        "p9:r1",
        (filter.f_a7, filter.f_u_a),
        filter_operator=oaseConst.DF_OPE_AND,
    )
    r2 = create_rule_row(
        2,
        "p9:r2",
        (filter.f_a8, filter.f_u_b),
        filter_operator=oaseConst.DF_OPE_OR,
    )
    r3 = create_rule_row(
        3,
        "p9:r3",
        (filter.f_a9, filter.f_u_c),
        filter_operator=oaseConst.DF_OPE_ORDER,
    )
    r4 = create_rule_row(
        4,
        "p9:r4",
        filter.f_a9,
    )

    # 必要なテーブルデータを設定
    filters = [
        filter.f_a7,
        filter.f_a8,
        filter.f_a9,
        filter.f_u_a,
        filter.f_u_b,
        filter.f_u_c,
    ]
    rules = [
        r1,
        r2,
        r3,
        r4,
    ]
    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules)

    # e010、e011、e013、e014が同じグループになることを確認
    group = {}
    for event in mock_mongo.test_events:
        if (event_id := event.get("event", {}).get("event_id")) in {
            "e010",
            "e011",
            "e013",
            "e014",
        }:
            group_id = event.get("exastro_filter_group", {}).get("group_id")
            group.setdefault(group_id, []).append(event_id)
    assert len(group) == 1
