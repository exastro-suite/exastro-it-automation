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
from tests.common import create_event, create_filter_row, create_rule_row, judge_time


def test_pattern_092(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    monkeypatch,
    patch_database_connections,
    mock_datetime,
):
    """ユニーク→キューイングで判定した結果、結論イベントが生まれる。生まれた結論イベントをまたルールで判定できるか？"""

    ws_db, mock_mongo = patch_database_connections

    # イベント
    e016 = create_event(
        "p92",
        "e016",
        judge_time - 5,
        ttl=20,
        custom_labels={"node": "z11", "type": "a"},
    )
    e017 = create_event(
        "p92",
        "e017",
        judge_time + 7,
        ttl=20,
        custom_labels={"node": "z11", "type": "a"},
    )
    e026 = create_event(
        "p92",
        "e026",
        judge_time + 7,
        ttl=20,
        custom_labels={"node": "z11", "type": "qa", "mode": "q3"},
    )
    e026a = create_event(
        "p92",
        "e026a",
        judge_time + 16,
        ttl=20,
        custom_labels={"node": "z11", "type": "qa", "mode": "q3"},
    )
    test_events = [e016, e017, e026, e026a]

    # フィルター
    f_u_a = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_UNIQUE,
        [
            ("type", oaseConst.DF_TEST_EQ, "a"),
        ],
    )
    f_q_a = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_QUEUING,
        [
            ("type", oaseConst.DF_TEST_EQ, "qa"),
        ],
    )

    # ルール
    r1 = create_rule_row(
        1,
        "p92:r1",
        (f_u_a, f_q_a),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_inheritance_flag={"action"},
        conclusion_label_settings=[
            {"type": "a"},
            {"B_eventid": "{{B.eventid}}"},
            {"A_eventid": "{{A.eventid}}"},
        ],
        conclusion_ttl=20,
    )
    r2 = create_rule_row(
        2,
        "p92:r2",
        f_u_a,
        conclusion_label_inheritance_flag={"action"},
        conclusion_label_settings=[
            {"A_eventid": "{{A.eventid}}"},
        ],
        conclusion_ttl=20,
    )

    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        f_u_a,
        f_q_a,
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        r1,
        r2,
    ]
    ws_db.table_data["T_OASE_ACTION"] = []
    for jt in range(judge_time, judge_time + 30):
        mock_mongo.test_events = [
            event
            for event in test_events
            if event["labels"]["_exastro_fetched_time"] <= jt
        ]
        mock_datetime.datetime.now.return_value.timestamp.return_value = jt
        bm.backyard_main("org1", "ws1")

    import pprint

    pprint.pprint(test_events)

    # 結論イベントが正しく作成されていることを確認
    # conclusion_events = [
    #     event
    #     for event in ev_obj.labeled_events_dict.values()
    #     if event["labels"].get("_exastro_type") == "conclusion"
    # ]
    # assert len(conclusion_events) == 4
