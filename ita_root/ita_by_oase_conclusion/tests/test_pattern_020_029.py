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


def test_pattern_020(
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

    test_events = create_events(["e018", "e018b", "e021"], "p20")

    # ルール
    r1 = create_rule_row(
        1,
        "r1",
        (filter.f_u_b, filter.f_u_c),
        filter_operator=oaseConst.DF_OPE_AND,
    )

    # 必要なテーブルデータを設定
    filters = [
        filter.f_u_b,
        filter.f_u_c,
    ]
    rules = [
        r1,
    ]
    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules)

    expected = [
        ("r1", "e018", "e021"),
        ("timeout", "e018b", None),
    ]

    assert_expected_pattern_results(ws_db, test_events, expected)
