# Copyright 2025 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import pytest
from unittest.mock import MagicMock
from flask import g, Flask
from common_libs.validate import valid_110111
from common_libs.validate.valid_110111 import external_valid_menu_before, external_valid_menu_after, get_duplicated_event_source_ids


def create_flask_app_context():
    """
    Flask アプリケーションコンテキストを作成するヘルパー関数
    """
    app = Flask(__name__)
    app_context = app.app_context()
    app_context.push()

    # g.appmsg のモックを設定（get_api_message はメッセージコードをそのまま返す）
    class AppMsgMock:
        def get_api_message(self, code, args=None):
            return code

    g.appmsg = AppMsgMock()
    g.LANGUAGE = "ja"

    return app_context


def _redundancy_group_json(ids):
    """冗長グループのカラム値（{"id": [...]} 形式の JSON 文字列）を作るヘルパー"""
    return json.dumps({"id": ids})


@pytest.mark.parametrize(
    "cmd_type, entry_ids, current_ids, other_records_ids, deduplication_setting_id, expected_bool, expected_msg_code",
    [
        # 登録：他レコードと収集設定IDが重複 → NG（MSG-160004）
        ("Register", ["S1", "S2"], None, [["S2", "S3"]], None, False, "MSG-160004"),
        # 登録：他レコードと重複なし → OK
        ("Register", ["S1", "S2"], None, [["S3", "S4"]], None, True, None),
        # 登録：他レコードが1件も無い → OK
        ("Register", ["S1", "S2"], None, [], None, True, None),
        # 更新：自レコード（同じID）は除外されるので誤検知しない → OK
        #   ※ 他レコード集合には自分の分を渡さない（SQLで除外される前提）
        ("Update", ["S1", "S2"], ["S1", "S2"], [], "DUP-SELF", True, None),
        # 更新：自レコード以外と重複 → NG
        ("Update", ["S1"], ["S1"], [["S1", "S9"]], "DUP-SELF", False, "MSG-160004"),
        # 復活：他レコードと重複 → NG（Restore は current から取得）
        ("Restore", None, ["S5"], [["S5"]], "DUP-SELF", False, "MSG-160004"),
        # 復活：重複なし → OK
        ("Restore", None, ["S5"], [["S6"]], "DUP-SELF", True, None),
        # 削除：チェックしない → OK
        ("Delete", ["S1"], ["S1"], [["S1"]], "DUP-SELF", True, None),
        # 廃止：チェックしない → OK
        ("Discard", ["S1"], ["S1"], [["S1"]], "DUP-SELF", True, None),
    ]
)
def test_external_valid_menu_before_duplication(cmd_type,
                                                entry_ids,
                                                current_ids,
                                                other_records_ids,
                                                deduplication_setting_id,
                                                expected_bool,
                                                expected_msg_code,
                                                monkeypatch):
    """
    external_valid_menu_before の冗長グループ重複バリデーションのテスト
    """
    app_context = create_flask_app_context()
    try:
        # 他レコードを返す table_select のモック
        objdbca = MagicMock()
        objdbca.table_select.return_value = [
            {"EVENT_SOURCE_REDUNDANCY_GROUP": _redundancy_group_json(ids)}
            for ids in other_records_ids
        ]

        # イベント収集設定名の解決はメッセージ用途のみなので固定値でモック
        monkeypatch.setattr(
            "common_libs.validate.valid_110111.get_event_collection_settings_name_by_id",
            lambda objdbca, id: f"ECS_{id}"
        )

        current_parameter = {"parameter": {"deduplication_setting_id": deduplication_setting_id}}
        if current_ids is not None:
            current_parameter["parameter"]["event_source_redundancy_group"] = _redundancy_group_json(current_ids)

        entry_parameter = {"parameter": {}}
        if entry_ids is not None:
            entry_parameter["parameter"]["event_source_redundancy_group"] = _redundancy_group_json(entry_ids)

        option = {
            "cmd_type": cmd_type,
            "current_parameter": current_parameter,
            "entry_parameter": entry_parameter,
        }

        retBool, msg, _ = external_valid_menu_before(objdbca, {}, option)
        assert retBool == expected_bool
        if expected_msg_code:
            assert any(expected_msg_code in m for m in msg)
        else:
            assert msg == []
    finally:
        app_context.pop()


@pytest.mark.parametrize(
    "cmd_type, option_extra, expected_key",
    [
        # 登録：新規発番の uuid をロックキーに
        ("Register", {"uuid": "NEW-DEDUP-ID", "current_parameter": {"parameter": {}}}, "OASE_DEDUPLICATION_NEW-DEDUP-ID"),
        # 復活：既存レコードの deduplication_setting_id をロックキーに
        ("Restore", {"current_parameter": {"parameter": {"deduplication_setting_id": "RES-DEDUP-ID"}}}, "OASE_DEDUPLICATION_RES-DEDUP-ID"),
    ]
)
def test_external_valid_menu_after_activation_inserts_lock_key(cmd_type, option_extra, expected_key):
    """
    有効化(Register/Restore)：ロックキーを T_COMN_RECODE_LOCK_TABLE へ INSERT IGNORE する
    """
    objdbca = MagicMock()
    option = {"cmd_type": cmd_type}
    option.update(option_extra)

    retBool, msg, _ = external_valid_menu_after(objdbca, {}, option)

    assert retBool is True
    assert msg == ''
    objdbca.sql_execute.assert_called_once_with(
        "INSERT INTO `T_COMN_RECODE_LOCK_TABLE` (`TABLE_NAME`) VALUES (%s)",
        [expected_key],
    )


@pytest.mark.parametrize(
    "cmd_type, expected_key",
    [
        # 削除：既存レコードの deduplication_setting_id に対応する行を DELETE
        ("Delete", "DEL-DEDUP-ID"),
        # 廃止：同上（無効化なので DELETE）
        ("Discard", "DIS-DEDUP-ID"),
    ]
)
def test_external_valid_menu_after_deactivation_removes_lock_key(cmd_type, expected_key):
    """
    無効化(Discard/Delete)：current_parameter の deduplication_setting_id に対応する
    ロックキー行を DELETE する
    """
    objdbca = MagicMock()
    option = {
        "cmd_type": cmd_type,
        "current_parameter": {"parameter": {"deduplication_setting_id": expected_key}},
    }

    retBool, msg, _ = external_valid_menu_after(objdbca, {}, option)

    assert retBool is True
    assert msg == ''
    objdbca.sql_execute.assert_called_once_with(
        "DELETE FROM `T_COMN_RECODE_LOCK_TABLE` WHERE `TABLE_NAME` = %s",
        [f"OASE_DEDUPLICATION_{expected_key}"],
    )


def test_external_valid_menu_after_update_is_no_op():
    """
    更新(Update)はロックテーブルを操作しない（キーは有効化時のまま）
    """
    objdbca = MagicMock()
    option = {
        "cmd_type": "Update",
        "uuid": "X",
        "current_parameter": {"parameter": {"deduplication_setting_id": "X"}},
    }

    retBool, msg, _ = external_valid_menu_after(objdbca, {}, option)

    assert retBool is True
    assert msg == ''
    objdbca.sql_execute.assert_not_called()


def test_external_valid_menu_after_register_without_uuid_is_safe():
    """
    Register でも uuid が無い異常系では INSERT を実行しない（落ちない）
    """
    objdbca = MagicMock()
    option = {"cmd_type": "Register", "entry_parameter": {"parameter": {}}}

    retBool, msg, _ = external_valid_menu_after(objdbca, {}, option)

    assert retBool is True
    objdbca.sql_execute.assert_not_called()


@pytest.mark.parametrize(
    "event_source_redundancy_group, deduplication_setting_id, other_records, expected_ids, expected_where, expected_param",
    [
        # 新規登録：自レコード除外句なし。重複あり
        (
            ["S1", "S2"], None,
            [{"EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["S2", "S3"]}'}],
            ["S2"],
            "WHERE DISUSE_FLAG='0'", [],
        ),
        # 更新：自レコード除外句あり。重複なし
        (
            ["S1"], "SELF-ID",
            [{"EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["S9"]}'}],
            [],
            "WHERE DISUSE_FLAG='0' AND DEDUPLICATION_SETTING_ID != %s", ["SELF-ID"],
        ),
        # 入力が空 → table_select を呼ばず即空リスト
        (
            [], None,
            [{"EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["S1"]}'}],
            [],
            None, None,
        ),
        # 複数レコードにまたがる重複を入力順・重複なしで返す
        (
            ["S1", "S2", "S3"], None,
            [
                {"EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["S3"]}'},
                {"EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["S1"]}'},
            ],
            ["S1", "S3"],
            "WHERE DISUSE_FLAG='0'", [],
        ),
        # 他レコードのカラムが壊れた JSON でも落ちない（無視して継続）
        (
            ["S1"], None,
            [{"EVENT_SOURCE_REDUNDANCY_GROUP": "not-json"}],
            [],
            "WHERE DISUSE_FLAG='0'", [],
        ),
    ]
)
def test_get_duplicated_event_source_ids(event_source_redundancy_group,
                                         deduplication_setting_id,
                                         other_records,
                                         expected_ids,
                                         expected_where,
                                         expected_param):
    """
    get_duplicated_event_source_ids のテスト（自レコード除外句・積集合ロジック）
    """
    objdbca = MagicMock()
    objdbca.table_select.return_value = other_records

    result = get_duplicated_event_source_ids(objdbca, event_source_redundancy_group, deduplication_setting_id)

    assert result == expected_ids

    if expected_where is None:
        # 入力が空の場合は DB 参照しない
        objdbca.table_select.assert_not_called()
    else:
        objdbca.table_select.assert_called_once_with(
            valid_110111.oaseConst.T_OASE_DEDUPLICATION_SETTINGS,
            expected_where,
            expected_param,
        )
