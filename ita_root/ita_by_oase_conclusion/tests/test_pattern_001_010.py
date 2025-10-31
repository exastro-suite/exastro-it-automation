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
    e001 = create_event(
        "pattern",
        "e001",
        judge_time - 15,
        ttl=20,
        custom_labels={
            "node": "z01",
            "msg": "[systemA] Httpd Down",
            "_exastro_host": "systemA",
            "service": "Httpd",
            "status": "Down",
            "severity": "3",
            "excluded_flg": "0",
        },
    )
    e002 = create_event(
        "pattern",
        "e002",
        judge_time - 10,
        ttl=20,
        custom_labels={
            "node": "z01",
            "msg": "[systemA] Httpd Down",
            "_exastro_host": "systemA",
            "service": "Httpd",
            "status": "Down",
            "severity": "3",
            "excluded_flg": "0",
        },
    )
    e003 = create_event(
        "pattern",
        "e003",
        judge_time - 5,
        ttl=20,
        custom_labels={
            "node": "z01",
            "msg": "[systemA] Httpd Down",
            "_exastro_host": "systemA",
            "service": "Httpd",
            "status": "Down",
            "severity": "3",
            "excluded_flg": "0",
        },
    )
    e004 = create_event(
        "pattern",
        "e004",
        judge_time - 15,
        ttl=20,
        custom_labels={
            "node": "z01",
            "msg": "[systemA] Httpd Down",
            "_exastro_host": "systemB",
            "service": "Httpd",
            "status": "Down",
            "severity": "3",
            "excluded_flg": "0",
        },
    )
    e005 = create_event(
        "pattern",
        "e005",
        judge_time - 10,
        ttl=20,
        custom_labels={
            "node": "z01",
            "msg": "[systemA] Httpd Down",
            "_exastro_host": "systemB",
            "service": "Httpd",
            "status": "Down",
            "severity": "3",
            "excluded_flg": "0",
        },
    )
    test_events = [e001, e002, e003, e004, e005]

    # フィルター
    f_a6 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("excluded_flg", oaseConst.DF_TEST_EQ, "0"),
            ("_exastro_host", oaseConst.DF_TEST_NE, "systemZ"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET,
        ["node", "msg", "clock", "eventid"],
    )
    f_a4 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("excluded_flg", oaseConst.DF_TEST_EQ, "0"),
            ("service", oaseConst.DF_TEST_EQ, "Httpd"),
            ("status", oaseConst.DF_TEST_EQ, "Down"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET,
        ["node", "msg", "clock", "eventid", "_exastro_host"],
    )

    # ルール
    r1 = create_rule_row(
        1,
        "p6:r1",
        f_a6,
        action_id="action1",
    )
    r2 = create_rule_row(
        2,
        "p6:r2",
        f_a4,
        action_id="action2",
    )

    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        f_a6,
        f_a4,
    ]
    ws_db.table_data["T_OASE_RULE"] = [
        r1,
        r2,
    ]
    ws_db.table_data["T_OASE_ACTION"] = [
        {"ACTION_ID": "action1", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0},
        {"ACTION_ID": "action2", "CONCLUSION_LABEL_SETTINGS": "{}", "DISUSE_FLAG": 0},
    ]
    minimum_fetched_time = min(
        (event["labels"]["_exastro_fetched_time"] for event in test_events),
        default=judge_time,
    )
    maximum_fetched_time = max(
        (event["labels"]["_exastro_fetched_time"] for event in test_events),
        default=judge_time,
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

    # 全てのイベントが同じグループになることを確認
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

    # イベント
    e010 = create_event(
        "p9",
        "e010",
        judge_time - 30,
        ttl=20,
        custom_labels={
            "node": "Z02",
            "msg": "[systemC] Disk Full",
            "_exastro_host": "systemC",
            "service": "Disk",
            "status": "Full",
            "severity": "3",
            "excluded_flg": "0",
        },
    )
    e011 = create_event(
        "p9",
        "e011",
        judge_time - 25,
        ttl=20,
        custom_labels={
            "node": "Z02",
            "msg": "[systemC] Disk Full (95%)",
            "_exastro_host": "systemC",
            "service": "Disk",
            "status": "Full",
            "severity": "3",
            "used_space": "95%",
            "excluded_flg": "0",
        },
    )
    e012 = create_event(
        "p9",
        "e012",
        judge_time - 10,
        ttl=20,
        custom_labels={
            "node": "Z02",
            "msg": "[systemC] Disk Full (95%) -exclude",
            "_exastro_host": "systemC",
            "service": "Disk",
            "status": "Full",
            "severity": "3",
            "used_space": "95%",
            "excluded_flg": "1",
        },
    )
    e013 = create_event(
        "p9",
        "e013",
        judge_time - 5,
        ttl=20,
        custom_labels={
            "node": "Z02",
            "msg": "[systemC] Disk Full (95%)",
            "_exastro_host": "systemC",
            "service": "Disk",
            "status": "Full",
            "severity": "3",
            "used_space": "95%",
            "excluded_flg": "0",
        },
    )
    e014 = create_event(
        "p9",
        "e014",
        judge_time,
        ttl=20,
        custom_labels={
            "node": "Z02",
            "msg": "[systemC] Disk Full",
            "_exastro_host": "systemC",
            "service": "Disk",
            "status": "Full",
            "severity": "3",
            "excluded_flg": "0",
        },
    )
    e021 = create_event(
        "p9",
        "e021",
        judge_time - 5,
        ttl=20,
        custom_labels={
            "node": "z11",
            "type": "c",
        },
    )
    test_events = [e010, e011, e012, e013, e014, e021]

    # フィルター
    f_a7 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("excluded_flg", oaseConst.DF_TEST_EQ, "0"),
            ("service", oaseConst.DF_TEST_EQ, "Httpd"),
            ("status", oaseConst.DF_TEST_EQ, "Down"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["service", "status", "severity"],
    )
    f_a8 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("excluded_flg", oaseConst.DF_TEST_EQ, "0"),
            ("service", oaseConst.DF_TEST_EQ, "Mysqld"),
            ("status", oaseConst.DF_TEST_EQ, "Down"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET,
        ["node", "msg", "clock", "eventid"],
    )
    f_a9 = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        [
            ("excluded_flg", oaseConst.DF_TEST_EQ, "0"),
            ("service", oaseConst.DF_TEST_EQ, "Disk"),
            ("status", oaseConst.DF_TEST_EQ, "Full"),
        ],
        oaseConst.DF_GROUP_CONDITION_ID_TARGET,
        ["_exastro_host", "severity", "service", "status", "severity"],
    )
    f_u_a = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_UNIQUE,
        [
            ("type", oaseConst.DF_TEST_EQ, "a"),
        ],
    )
    f_u_b = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_UNIQUE,
        [
            ("type", oaseConst.DF_TEST_EQ, "b"),
        ],
    )
    f_u_c = create_filter_row(
        oaseConst.DF_SEARCH_CONDITION_UNIQUE,
        [
            ("type", oaseConst.DF_TEST_EQ, "c"),
        ],
    )

    # ルール
    r1 = create_rule_row(
        1,
        "p9:r1",
        (f_a7, f_u_a),
        filter_operator=oaseConst.DF_OPE_AND,
    )
    r2 = create_rule_row(
        2,
        "p9:r2",
        (f_a8, f_u_b),
        filter_operator=oaseConst.DF_OPE_OR,
    )
    r3 = create_rule_row(
        3,
        "p9:r3",
        (f_a9, f_u_c),
        filter_operator=oaseConst.DF_OPE_ORDER,
    )
    r4 = create_rule_row(
        4,
        "p9:r4",
        f_a9,
    )

    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)
    # 必要なテーブルデータを設定
    ws_db.table_data["T_OASE_FILTER"] = [
        f_a7,
        f_a8,
        f_a9,
        f_u_a,
        f_u_b,
        f_u_c,
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
    maximum_fetched_time = max(
        (event["labels"]["_exastro_fetched_time"] for event in test_events),
        default=judge_time,
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

    # 全てのイベントが同じグループになることを確認
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
