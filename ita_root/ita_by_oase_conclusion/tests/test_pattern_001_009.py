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

import backyard_main as bm
from common_libs.oase.const import oaseConst
from tests.common import create_rule_row, judge_time
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
    ws_db.table_data["T_OASE_FILTER"] = [
        filter.f_a6,
        filter.f_a4,
        filter.f_a99,
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        r1,
        r2,
        r3,
    ]
    ws_db.table_data["T_OASE_ACTION"] = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0},
        {"ACTION_ID": "action2", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0},
    ]
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

    # e001～e005が同じグループになることを確認
    assert (
        len(
            {
                event.get("exastro_filter_group", {}).get("group_id")
                for event in test_events
                if event["event"]["event_id"]
                in ["e001", "e002", "e003", "e004", "e005"]
            }
        )
        == 1
    )


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

    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        filter.f_a7,
        filter.f_a8,
        filter.f_a9,
        filter.f_u_a,
        filter.f_u_b,
        filter.f_u_c,
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        r1,
        r2,
        r3,
        r4,
    ]
    ws_db.table_data["T_OASE_ACTION"] = []
    minimum_fetched_time = min(
        (event["labels"]["_exastro_fetched_time"] for event in test_events),
        default=judge_time,
    )
    maximum_end_time = max(
        (event["labels"]["_exastro_end_time"] for event in test_events),
        default=judge_time,
    )
    for jt in range(minimum_fetched_time, maximum_end_time + 2):
        mock_mongo.test_events = [
            event
            for event in test_events
            if event["labels"]["_exastro_fetched_time"] <= jt
        ]
        mock_datetime.datetime.now.return_value.timestamp.return_value = jt
        bm.backyard_main("org1", "ws1")

    # エラーがないことを確認
    tracebacks = [log for _, log in g.applogger.logs if "Traceback" in log]
    if tracebacks:
        print(tracebacks[0])
    assert not tracebacks

    import pprint

    pprint.pprint(test_events)

    # e010、e011、e013、e014が同じグループになることを確認
    assert (
        len(
            {
                event.get("exastro_filter_group", {}).get("group_id")
                for event in test_events
                if event["event"]["event_id"] in ["e010", "e011", "e013", "e014"]
            }
        )
        == 1
    )
