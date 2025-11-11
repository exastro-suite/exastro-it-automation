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
from tests.common import (
    assert_expected_pattern_results,
    create_rule_row,
    run_test_pattern,
)
from tests.event import create_events
import tests.filter as filter


def test_pattern_010(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピングとユニークの組み合わせ条件_2"""
    g = patch_global_g

    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(
        itertools.chain(
            [f"e{n:03}" for n in range(1, 12 + 1)],
            ["e014", "e014h", "e015", "e017", "e019", "e022", "e023"],
        ),
        "p10",
    )

    # ルール
    r1 = create_rule_row(
        1,
        "r1",
        (filter.f_a7, filter.f_u_a),
        filter_operator=oaseConst.DF_OPE_AND,
    )
    r2 = create_rule_row(
        2,
        "r2",
        (filter.f_a8, filter.f_u_b),
        filter_operator=oaseConst.DF_OPE_OR,
    )
    r3 = create_rule_row(
        3,
        "r3",
        (filter.f_u_c, filter.f_a9),
        filter_operator=oaseConst.DF_OPE_ORDER,
    )
    r4 = create_rule_row(
        4,
        "r4",
        (filter.f_a9, filter.f_u_d),
        filter_operator=oaseConst.DF_OPE_AND,
    )

    # 必要なテーブルデータを設定
    filters = [
        filter.f_a7,
        filter.f_a8,
        filter.f_a9,
        filter.f_u_a,
        filter.f_u_b,
        filter.f_u_c,
        filter.f_u_d,
    ]
    rules = [
        r1,
        r2,
        r3,
        r4,
    ]
    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules)

    expected = [
        ("r1", ["e001", "e002", "e003", "e004", "e005"], "e015"),
        ("timeout", None, "e017"),
        ("r2", ["e006", "e007"], None),
        ("r2", None, "e019"),
        ("r2", ["e008"], None),
        ("undetected", "e009", None),
        ("r3", "e022", ["e014", "e014h"]),
        ("r4", ["e010", "e011"], "e023"),
        ("undetected", "e012", None),
    ]

    assert_expected_pattern_results(ws_db, test_events, expected)
