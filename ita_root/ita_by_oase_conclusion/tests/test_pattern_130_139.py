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
    create_rule_row,
    run_test_pattern,
    assert_grouped_events,
    assert_event_timeout,
    assert_event_evaluated,
    assert_event_undetected
)
from tests.event import create_events_p130
from tests.filter import f_a16


def test_pattern_130(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """グルーピング対象のラベル有無によるグルーピング"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    event_num = 2000
    test_events = create_events_p130(event_num)

    filters = [f_a16]
    rules = [
        create_rule_row(1, "p130:r1", (f_a16), filter_operator=oaseConst.DF_OPE_NONE,
                        conclusion_label_settings=[["status", "true"]], conclusion_ttl=30)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    for i in range(0, event_num):
        e = test_events[i]
        assert_event_evaluated(e)

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert len(c_1["exastro_events"]) == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(test_events[0]['_id'])}')") == 1
    assert c_1["labels"]["status"] == "true"
    assert c_1["labels"]["_exastro_rule_name"] == "p130:r1"
    assert_event_undetected(c_1)

    # グルーピングの確認
    assert_grouped_events(test_events, [
        test_events[:-1]  # 最後の結論イベント1個を除いたリスト
    ])
