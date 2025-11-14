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
from tests.filter import f_a7, f_a10, f_a8, f_a15, f_u_a, f_u_b, f_q_a, f_q_b


def test_pattern_100(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """単体で結論イベントが生まれ、結論イベントがフィルタが効いて親イベントにグルーピングされる(結論イベント生成無限ループにはならない)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e002"], "p100")
    e001, e002 = test_events

    filters = [f_a7]
    rules = [
        create_rule_row(1, "p100:r1", (f_a7), filter_operator=oaseConst.DF_OPE_NONE,
                        conclusion_label_settings=[{"excluded_flg": "0"}, {"service": "Httpd"}, {"status": "Down"}, {"severity": "3"}], conclusion_ttl=20)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e001["labels"]["_exastro_evaluated"] == "1"
    assert e002["labels"]["_exastro_evaluated"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e002['_id'])}')") == 0
    assert c_1["labels"]["excluded_flg"] == "0"
    assert c_1["labels"]["service"] == "Httpd"
    assert c_1["labels"]["status"] == "Down"
    assert c_1["labels"]["severity"] == "3"
    assert c_1["labels"]["_exastro_rule_name"] == "p100:r1"
    assert c_1["labels"]["_exastro_evaluated"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 3

    assert e001["exastro_filter_group"]["is_first_event"] == "1"
    assert e001["exastro_filter_group"]["group_id"] == e002["exastro_filter_group"]["group_id"]
    assert e001["exastro_filter_group"]["group_id"] == c_1["exastro_filter_group"]["group_id"]


def test_pattern_100_2(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """単体で結論イベントが生まれ再帰的にr1にマッチ(結論イベント生成無限ループにはならない)"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e001", "e002"], "p100_2")
    e001, e002 = test_events

    filters = [f_a7]
    rules = [
        create_rule_row(1, "p100_2:r1", (f_a7), filter_operator=oaseConst.DF_OPE_NONE,
                        conclusion_label_settings=[{"excluded_flg": "0"}, {"service": "Httpd"}, {"status": "Down"}, {"severity": "99"}], conclusion_ttl=20)
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions)

    assert e001["labels"]["_exastro_evaluated"] == "1"
    assert e002["labels"]["_exastro_evaluated"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 2
    c_1, c_2 = conclusion_events

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e001['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e002['_id'])}')") == 0
    assert c_1["labels"]["excluded_flg"] == "0"
    assert c_1["labels"]["service"] == "Httpd"
    assert c_1["labels"]["status"] == "Down"
    assert c_1["labels"]["severity"] == "99"
    assert c_1["labels"]["_exastro_rule_name"] == "p100_2:r1"
    assert c_1["labels"]["_exastro_evaluated"] == "1"

    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(c_1['_id'])}')") == 1
    assert c_2["labels"]["excluded_flg"] == "0"
    assert c_2["labels"]["service"] == "Httpd"
    assert c_2["labels"]["status"] == "Down"
    assert c_2["labels"]["severity"] == "99"
    assert c_1["labels"]["_exastro_rule_name"] == "p100_2:r1"
    assert c_2["labels"]["_exastro_evaluated"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 4

    assert e001["exastro_filter_group"]["is_first_event"] == "1"
    assert e001["exastro_filter_group"]["group_id"] == e002["exastro_filter_group"]["group_id"]

    assert c_1["exastro_filter_group"]["is_first_event"] == "1"
    assert c_1["exastro_filter_group"]["group_id"] == c_2["exastro_filter_group"]["group_id"]


def test_pattern_101(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ANDで結論イベントが生まれr2以降でマッチする"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e003", "e003a", "e012", "e013", "e005c", "e005d", "e018e", "e026e", "e028b"], "p101")
    e003, e003a, e012, e013, e005c, e005d, e018e, e026e, e028b = test_events

    filters = [f_a7, f_a10, f_a8, f_a15, f_u_a, f_u_b, f_q_a, f_q_b]
    rules = [
        create_rule_row(1, "p101:r1", (f_a7, f_a10), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"excluded_flg": "0"}, {"service": "Mysqld"}, {"status": "Down"}], conclusion_ttl=20),
        create_rule_row(2, "p101:r2", (f_a8, f_a15), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"type": "a"}], conclusion_ttl=20),
        create_rule_row(3, "p101:r3", (f_u_a, f_u_b), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"type": "qa"}], conclusion_ttl=20),
        create_rule_row(4, "p101:r4", (f_q_a, f_q_b), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"type": "qa"}], conclusion_ttl=20),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=6)

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e003["labels"]["_exastro_evaluated"] == "1"
    assert e003a["labels"]["_exastro_evaluated"] == "1"
    assert e012["labels"]["_exastro_evaluated"] == "1"
    assert e013["labels"]["_exastro_evaluated"] == "1"

    assert e005c["labels"]["_exastro_evaluated"] == "1"
    assert e005d["labels"]["_exastro_evaluated"] == "1"

    assert e018e["labels"]["_exastro_evaluated"] == "1"

    assert e028b["labels"]["_exastro_evaluated"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 4
    c_1, c_2, c_3, c_4 = conclusion_events

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e003['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e012['_id'])}')") == 1
    assert c_1["labels"]["excluded_flg"] == "0"
    assert c_1["labels"]["service"] == "Mysqld"
    assert c_1["labels"]["status"] == "Down"
    assert c_1["labels"]["_exastro_rule_name"] == "p101:r1"
    assert c_1["labels"]["_exastro_evaluated"] == "1"

    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(c_1['_id'])}')") == 1
    assert list(c_2["exastro_events"]).count(f"ObjectId('{str(e005c['_id'])}')") == 1
    assert c_2["labels"]["type"] == "a"
    assert c_2["labels"]["_exastro_rule_name"] == "p101:r2"
    assert c_2["labels"]["_exastro_evaluated"] == "1"

    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(c_2['_id'])}')") == 1
    assert list(c_3["exastro_events"]).count(f"ObjectId('{str(e018e['_id'])}')") == 1
    assert c_3["labels"]["type"] == "qa"
    assert c_3["labels"]["_exastro_rule_name"] == "p101:r3"

    assert list(c_4["exastro_events"]).count(f"ObjectId('{str(e028b['_id'])}')") == 1
    assert c_4["labels"]["type"] == "qa"
    assert c_4["labels"]["_exastro_rule_name"] == "p101:r4"
    assert c_4["labels"]["_exastro_timeout"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 7

    assert e003["exastro_filter_group"]["is_first_event"] == "1"
    assert e003["exastro_filter_group"]["group_id"] == e003a["exastro_filter_group"]["group_id"]

    assert e012["exastro_filter_group"]["is_first_event"] == "1"
    assert e012["exastro_filter_group"]["group_id"] == e013["exastro_filter_group"]["group_id"]

    assert e005c["exastro_filter_group"]["is_first_event"] == "1"
    assert e005c["exastro_filter_group"]["group_id"] == e005d["exastro_filter_group"]["group_id"]

    assert e026e["labels"]["_exastro_timeout"] == "1"  # _exastro_evaluated == "1" になっている
    assert c_3["labels"]["_exastro_evaluated"] == "1"  # e026e が _exastro_evaluated になった為、_exastro_timeout == 1 になっている
    assert list(c_4["exastro_events"]).count(f"ObjectId('{str(c_3['_id'])}')") == 1  # e026e が _exastro_evaluated になった為、そのIDが入っている


def test_pattern_102(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ANDで結論イベントがr2で未知になる１"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e003", "e003a", "e012", "e013"], "p102")
    e003, e003a, e012, e013 = test_events

    filters = [f_a7, f_a10, f_u_a, f_u_b]
    rules = [
        create_rule_row(1, "p102:r1", (f_a7, f_a10), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"type": "a"}], conclusion_ttl=20),
        create_rule_row(2, "p102:r2", (f_u_a, f_u_b), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"type": "qa"}], conclusion_ttl=20),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=6)

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e003["labels"]["_exastro_evaluated"] == "1"
    assert e003a["labels"]["_exastro_evaluated"] == "1"
    assert e012["labels"]["_exastro_evaluated"] == "1"
    assert e013["labels"]["_exastro_evaluated"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e003['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e012['_id'])}')") == 1
    assert c_1["labels"]["type"] == "a"
    assert c_1["labels"]["_exastro_rule_name"] == "p102:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"  # _exastro_timeout == 1 になっている

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 4

    assert e003["exastro_filter_group"]["is_first_event"] == "1"
    assert e003["exastro_filter_group"]["group_id"] == e003a["exastro_filter_group"]["group_id"]

    assert e012["exastro_filter_group"]["is_first_event"] == "1"
    assert e012["exastro_filter_group"]["group_id"] == e013["exastro_filter_group"]["group_id"]


def test_pattern_103(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ANDで結論イベントがr2で未知になる2"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e003", "e003a", "e012", "e013", "e019"], "p103")
    e003, e003a, e012, e013, e019 = test_events

    filters = [f_a7, f_a10, f_u_a, f_u_b]
    rules = [
        create_rule_row(1, "p103:r1", (f_a7, f_a10), filter_operator=oaseConst.DF_OPE_AND,
                        conclusion_label_settings=[{"type": "a"}], conclusion_ttl=20),
        create_rule_row(2, "p103:r2", (f_u_a, f_u_b), filter_operator=oaseConst.DF_OPE_OR,
                        conclusion_label_settings=[{"type": "qa"}], conclusion_ttl=20),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=6)

    # TODO: 結果の確認が必要
    import pprint
    pprint.pprint(test_events)

    assert e003["labels"]["_exastro_evaluated"] == "1"
    assert e003a["labels"]["_exastro_evaluated"] == "1"
    assert e012["labels"]["_exastro_evaluated"] == "1"
    assert e013["labels"]["_exastro_evaluated"] == "1"

    assert e019["labels"]["_exastro_undetected"] == "1"  # r2に該当して _exastro_evaluated == "1" になっている

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 1
    c_1 = conclusion_events[0]

    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e003['_id'])}')") == 1
    assert list(c_1["exastro_events"]).count(f"ObjectId('{str(e012['_id'])}')") == 1
    assert c_1["labels"]["type"] == "a"
    assert c_1["labels"]["_exastro_rule_name"] == "p103:r1"
    assert c_1["labels"]["_exastro_undetected"] == "1"  # _exastro_timeout == 1 になっている

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 4

    assert e003["exastro_filter_group"]["is_first_event"] == "1"
    assert e003["exastro_filter_group"]["group_id"] == e003a["exastro_filter_group"]["group_id"]

    assert e012["exastro_filter_group"]["is_first_event"] == "1"
    assert e012["exastro_filter_group"]["group_id"] == e013["exastro_filter_group"]["group_id"]


def test_pattern_104(
    patch_global_g,
    patch_notification_and_writer,
    patch_common_functions,
    patch_action_using_modules,
    monkeypatch,
    patch_database_connections,
    patch_datetime,
):
    """ORで結論イベントが生まれr2以降でマッチする"""
    g = patch_global_g
    ws_db, mock_mongo = patch_database_connections
    mock_datetime = patch_datetime

    test_events = create_events(["e003", "e003a", "e014d", "e025"], "p104")
    e003, e003a, e014d, e025 = test_events

    filters = [f_a7, f_a10, f_a8, f_a15, f_u_a, f_u_b, f_q_a, f_q_b]
    rules = [
        create_rule_row(1, "p104:r1", (f_a7, f_a10), filter_operator=oaseConst.DF_OPE_OR,
                        conclusion_label_settings=[{"excluded_flg": "0"}, {"service": "Mysqld"}, {"status": "Down"}], conclusion_ttl=20),
        create_rule_row(2, "p104:r2", (f_a8, f_a15), filter_operator=oaseConst.DF_OPE_OR,
                        conclusion_label_settings=[{"type": "qa"}], conclusion_ttl=20),
        create_rule_row(3, "p104:r3", (f_q_a, f_q_b), filter_operator=oaseConst.DF_OPE_OR,
                        conclusion_label_settings=[{"type": "a"}], conclusion_ttl=20),
        create_rule_row(4, "p104:r4", (f_u_a, f_u_b), filter_operator=oaseConst.DF_OPE_OR,
                        conclusion_label_settings=[{"type": "x"}], conclusion_ttl=20),
    ]
    actions = []

    run_test_pattern(g, ws_db, mock_mongo, mock_datetime, test_events, filters, rules, actions, after_epoch_runs=6)

    assert e003["labels"]["_exastro_evaluated"] == "1"
    assert e003a["labels"]["_exastro_evaluated"] == "1"

    assert e014d["labels"]["_exastro_evaluated"] == "1"

    assert e025["labels"]["_exastro_evaluated"] == "1"

    # 結論イベントの確認
    conclusion_events = [e for e in test_events if e["labels"]["_exastro_type"] == "conclusion"]
    assert len(conclusion_events) == 6
    r1_c_1, r2_c_1, r3_c_1, r2_c_2, r3_c_2, r3_c_3 = conclusion_events

    assert list(r1_c_1["exastro_events"]).count(f"ObjectId('{str(e003['_id'])}')") == 1
    assert r1_c_1["labels"]["excluded_flg"] == "0"
    assert r1_c_1["labels"]["service"] == "Mysqld"
    assert r1_c_1["labels"]["status"] == "Down"
    assert r1_c_1["labels"]["_exastro_rule_name"] == "p104:r1"
    assert r1_c_1["labels"]["_exastro_evaluated"] == "1"

    assert list(r2_c_1["exastro_events"]).count(f"ObjectId('{str(e014d['_id'])}')") == 1
    assert r2_c_1["labels"]["type"] == "qa"
    assert r2_c_1["labels"]["_exastro_rule_name"] == "p104:r2"
    assert r2_c_1["labels"]["_exastro_evaluated"] == "1"

    assert list(r3_c_1["exastro_events"]).count(f"ObjectId('{str(e025['_id'])}')") == 1
    assert r3_c_1["labels"]["type"] == "a"
    assert r3_c_1["labels"]["_exastro_rule_name"] == "p104:r3"
    assert r3_c_1["labels"]["_exastro_undetected"] == "1"

    assert list(r2_c_2["exastro_events"]).count(f"ObjectId('{str(r1_c_1['_id'])}')") == 1
    assert r2_c_2["labels"]["type"] == "qa"
    assert r2_c_2["labels"]["_exastro_rule_name"] == "p104:r2"
    assert r2_c_2["labels"]["_exastro_evaluated"] == "1"

    assert list(r3_c_2["exastro_events"]).count(f"ObjectId('{str(r2_c_1['_id'])}')") == 1
    assert r3_c_2["labels"]["type"] == "a"
    assert r3_c_2["labels"]["_exastro_rule_name"] == "p104:r3"
    assert r3_c_2["labels"]["_exastro_undetected"] == "1"

    assert list(r3_c_3["exastro_events"]).count(f"ObjectId('{str(r2_c_2['_id'])}')") == 1
    assert r3_c_3["labels"]["type"] == "a"
    assert r3_c_3["labels"]["_exastro_rule_name"] == "p104:r3"
    assert r3_c_3["labels"]["_exastro_undetected"] == "1"

    # グルーピングの確認
    grouped_events = [e for e in test_events if e.get("exastro_filter_group")]
    assert len(grouped_events) == 4

    assert e003["exastro_filter_group"]["is_first_event"] == "1"
    assert e003["exastro_filter_group"]["group_id"] == e003a["exastro_filter_group"]["group_id"]

    assert e014d["exastro_filter_group"]["is_first_event"] == "1"

    assert r1_c_1["exastro_filter_group"]["is_first_event"] == "1"


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
        (f_a7, f_a10),
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
        (f_a8, f_a15),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_settings=[["type", "a"]],
        conclusion_ttl=20,
    )
    r3 = create_rule_row(
        3,
        "r3",
        (f_u_a, f_u_b),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_settings=[["type", "qa"]],
        conclusion_ttl=20,
    )
    r4 = create_rule_row(
        4,
        "r4",
        (f_q_a, f_q_b),
        filter_operator=oaseConst.DF_OPE_ORDER,
        conclusion_label_settings=[["type", "qa"]],
        conclusion_ttl=20,
    )

    # 必要なテーブルデータを設定
    filters = [
        f_a7,
        f_a10,
        f_a8,
        f_a15,
        f_u_a,
        f_u_b,
        f_q_a,
        f_q_b,
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
