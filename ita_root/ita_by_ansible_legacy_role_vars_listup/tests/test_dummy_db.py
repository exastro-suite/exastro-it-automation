#   Copyright 2026 NEC Corporation
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

"""DB の代役（DummyDB）が本物の DB 接続と同じ癖を持つことを確認する
経緯: Issue #2618 / #3072
"""
import pytest

from tests.dummy_db import DummyDB


TABLE = 'T_TEST'


def _row(row_id, **extra):
    row = {'ROW_ID': row_id, 'NAME': 'name', 'DISUSE_FLAG': '0', 'LAST_UPDATE_TIMESTAMP': 'old'}
    row.update(extra)
    return row


def test_update_sets_every_passed_column():
    """更新に 3 項目渡すと 3 項目全部が書かれ、渡していない項目は元のまま残る

    経緯: Issue #2618
    """
    db = DummyDB({TABLE: [_row('1', TYPE='1')]})

    db.table_update(TABLE, [{'ROW_ID': '1', 'TYPE': '3', 'DISUSE_FLAG': '1'}], 'ROW_ID')

    row = db.find_row(TABLE, ROW_ID='1')
    assert row['TYPE'] == '3'
    assert row['DISUSE_FLAG'] == '1'
    assert row['NAME'] == 'name'


def test_update_without_primary_key_raises_key_error():
    """主キーを含めずに更新すると失敗する（本物と同じ KeyError）

    経緯: Issue #2618
    """
    db = DummyDB({TABLE: [_row('1')]})

    with pytest.raises(KeyError):
        db.table_update(TABLE, [{'NAME': 'changed'}], 'ROW_ID')


def test_update_touches_timestamp_of_target_rows_only():
    """更新した行だけ更新日時が付け替わり、触っていない行の更新日時は動かない

    経緯: Issue #2618
    """
    db = DummyDB({TABLE: [_row('1'), _row('2')]}, timestamp='new')

    db.table_update(TABLE, [{'ROW_ID': '1', 'NAME': 'changed'}], 'ROW_ID')

    assert db.find_row(TABLE, ROW_ID='1')['LAST_UPDATE_TIMESTAMP'] == 'new'
    assert db.find_row(TABLE, ROW_ID='2')['LAST_UPDATE_TIMESTAMP'] == 'old'


def test_select_active_only_excludes_discarded_and_null_flag():
    """有効行だけの検索は、廃止フラグが 1 の行も、廃止フラグが空（None）の行も返さない

    経緯: Issue #2618 / #3072
    """
    db = DummyDB({TABLE: [_row('1'), _row('2', DISUSE_FLAG='1'), _row('3', DISUSE_FLAG=None)]})

    active_rows = db.table_select(TABLE, "WHERE DISUSE_FLAG = '0'", [])
    all_rows = db.table_select(TABLE, "", [])

    active_ids = []
    for row in active_rows:
        active_ids.append(row['ROW_ID'])
    assert active_ids == ['1']
    assert len(all_rows) == 3


def test_select_returns_independent_copies():
    """検索結果を書き換えても DB の中身は変わらない（本物の DB と同じ）

    経緯: Issue #2618
    """
    db = DummyDB({TABLE: [_row('1')]})

    rows = db.table_select(TABLE, "", [])
    rows[0]['NAME'] = 'changed in memory'

    assert db.find_row(TABLE, ROW_ID='1')['NAME'] == 'name'


def test_insert_assigns_sequential_ids():
    """登録時に主キーが無ければ連番で払い出し、渡した辞書にも書き戻す（本物の INSERT と同じ）

    経緯: Issue #3072
    """
    db = DummyDB()
    data_list = [{'NAME': 'a'}, {'NAME': 'b'}]

    db.table_insert(TABLE, data_list, 'ROW_ID')

    assert data_list[0]['ROW_ID'] == 'generated-uuid-1'
    assert data_list[1]['ROW_ID'] == 'generated-uuid-2'
    assert len(db.rows(TABLE)) == 2


def test_insert_stores_numbers_as_strings_in_string_columns():
    """文字列列（メンバー名・階層パス・表示名）に数値を登録すると、本物の DB と同じく文字列で保存される

    解析器は配列階層の名前と階層パスを数値 0 で作るが、DB から読み直すと '0' になる。
    経緯: Issue #3072
    """
    db = DummyDB()

    db.table_insert('T_ANSR_NESTVAR_MEMBER', [{'VARS_NAME': 0, 'VRAS_NAME_PATH': 0, 'ARRAY_NEST_LEVEL': 1}], 'ARRAY_MEMBER_ID')

    row = db.rows('T_ANSR_NESTVAR_MEMBER')[0]
    assert row['VARS_NAME'] == '0'
    assert row['VRAS_NAME_PATH'] == '0'
    assert row['ARRAY_NEST_LEVEL'] == 1


def test_table_count_reports_unloaded_flag():
    """実行要否フラグの件数取得は、指定行の実行済みフラグが '1' 以外のときだけ 1 を返す

    経緯: Issue #3072
    """
    where = " WHERE  ROW_ID = %s AND (LOADED_FLG is NULL OR LOADED_FLG <> '1')"
    db = DummyDB({'T_COMN_PROC_LOADED_LIST': [{'ROW_ID': 204, 'LOADED_FLG': '0'}]})

    assert db.table_count('T_COMN_PROC_LOADED_LIST', where, [204]) == 1

    db.table_update('T_COMN_PROC_LOADED_LIST', {'ROW_ID': 204, 'LOADED_FLG': '1'}, 'ROW_ID')
    assert db.table_count('T_COMN_PROC_LOADED_LIST', where, [204]) == 0
