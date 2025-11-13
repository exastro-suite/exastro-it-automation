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
    assert_expected_pattern_results,
    create_rule_row,
    run_test_pattern,
)
from tests.event import create_events
import tests.filter as filter


def test_pattern_105(
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

    test_events = create_events(
        ["e001", "e004", "e012", "e005e", "e005f", "e018c", "e026d", "e028b"], "p105"
    )

    # ルール
    r1 = create_rule_row(
        1,
        "r1",
        (filter.f_a7, filter.f_a10),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_settings=[
            ["excluded_flg", "0"],
            ["service", "Mysqld"],
            ["status", "Down"],
        ],
        conclusion_ttl=20,
    )
    r2 = create_rule_row(
        2,
        "r2",
        (filter.f_a8, filter.f_a15),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_settings=[["type", "a"]],
        conclusion_ttl=20,
    )
    r3 = create_rule_row(
        3,
        "r3",
        (filter.f_u_a, filter.f_u_b),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_settings=[["type", "qa"]],
        conclusion_ttl=20,
    )
    r4 = create_rule_row(
        4,
        "r4",
        (filter.f_q_a, filter.f_q_b),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_settings=[["type", "qa"]],
        conclusion_ttl=20,
    )

    # 必要なテーブルデータを設定
    filters = [
        filter.f_a7,
        filter.f_a10,
        filter.f_a8,
        filter.f_a15,
        filter.f_u_a,
        filter.f_u_b,
        filter.f_q_a,
        filter.f_q_b,
    ]
    rules = [
        r1,
        r2,
        r3,
        r4,
    ]
    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, test_epoch=1760486660 + 5)

    c1 = {
        "type": "conclusion",
        "rule_name": "r1",
        "test_ids": ["e001", "e012"],
    }

    c2 = {
        "type": "conclusion",
        "rule_name": "r2",
        "test_ids": [c1, "e005e"],
    }

    # c3 = {
    #     "type": "conclusion",
    #     "rule_name": "r3",
    #     "test_ids": [c2, "e018c"],
    # }

    expected = [
        ("r1", ["e001", "e004"], ["e012"]),
        ("r2", [c1], ["e005e", "e005f"]),
        ("r3", c2, "e018c"),
        ("r4", "e026d", "e028b"),
    ]

    assert_expected_pattern_results(ws_db, test_events, expected)
