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

"""MovementVarsLinkTable.register_and_discard() のテスト

register_and_discard() は 1 回の呼び出しで
  1. 変数タイプ更新 UPDATE（extracted ∩ stored のうち VARS_ATTRIBUTE_01 が変わったもの）
  2. 新規登録 INSERT（extracted - stored）
  3. 復活 UPDATE（extracted ∩ stored のうち DISUSE_FLAG='1' のもの）
  4. 廃止 UPDATE（stored - extracted のうち DISUSE_FLAG='0' のもの）
を発行する。1 と 3 の母集合は完全に同一（extracted ∩ stored）なので同じ行に 2 回 UPDATE が走りうる。

DummyDB.table_update は本物と同じく「渡された data の全キーを SET する」ので、
3 が更新対象外のカラムまで渡すと 1 の結果が巻き戻る。
"""
import pytest

from common_libs.common.exception import AppException

from tests.common import (
    ATTR_LIST,
    ATTR_M_ARRAY,
    ATTR_STD,
    OLD_USER_ID,
    TABLE_MVMT_VAR_LINK,
    TEST_USER_ID,
    create_mov_vars_link_table,
    create_link_row,
    create_mov_vars_dict,
)

MOVEMENT_ID = "movement-0001"
VAR_NAME = "VAR_target"
LINK_ID = "link-0001"

# 変数タイプの全遷移パターン
ATTR_TRANSITIONS = [
    (ATTR_STD, ATTR_LIST),
    (ATTR_STD, ATTR_M_ARRAY),
    (ATTR_LIST, ATTR_STD),
    (ATTR_LIST, ATTR_M_ARRAY),
    (ATTR_M_ARRAY, ATTR_STD),
    (ATTR_M_ARRAY, ATTR_LIST),
]
ATTR_TRANSITION_IDS = [f"{old}to{new}" for old, new in ATTR_TRANSITIONS]

# table_update の呼び出し順（register_and_discard 内）
UPDATE_CALL_TYPE_CHANGE = 0
UPDATE_CALL_RESTORE = 1
UPDATE_CALL_DISCARD = 2

# 復活/廃止 UPDATE が渡してよいカラム（これ以外を渡すと他の更新を巻き戻す）
DISUSE_FLAG_UPDATE_COLUMNS = {'MVMT_VAR_LINK_ID', 'DISUSE_FLAG', 'LAST_UPDATE_USER'}


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# A. 変数タイプ遷移 6 パターン × 廃止経由の有無 2 パターン
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

@pytest.mark.parametrize('initial_disuse_flag', ['0', '1'], ids=['not_discarded', 'discarded'])
@pytest.mark.parametrize('old_attr,new_attr', ATTR_TRANSITIONS, ids=ATTR_TRANSITION_IDS)
def test_attr_transition_is_not_rolled_back(mock_g, dummy_db, old_attr, new_attr, initial_disuse_flag):
    """変数タイプの変更が、同時に走る復活 UPDATE で巻き戻らない（#2618 の回帰 assert）"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, old_attr, disuse_flag=initial_disuse_flag)]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, new_attr)]}))

    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=LINK_ID)
    assert row['VARS_ATTRIBUTE_01'] == new_attr
    assert row['DISUSE_FLAG'] == '0'
    assert row['LAST_UPDATE_USER'] == TEST_USER_ID


@pytest.mark.parametrize('old_attr,new_attr', ATTR_TRANSITIONS, ids=ATTR_TRANSITION_IDS)
def test_attr_transition_updates_memory_snapshot(mock_g, dummy_db, old_attr, new_attr):
    """再読み込み後のメモリ上のレコードも新しい変数タイプになっている

    backyard_main.py はこの get_stored_records() の結果を NestVarsMemberTable に渡すため、
    DB だけでなくメモリ側も正しい必要がある。
    """
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, old_attr, disuse_flag='1')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, new_attr)]}))

    stored = table.get_stored_records()
    assert list(stored.keys()) == [LINK_ID]
    assert stored[LINK_ID]['VARS_ATTRIBUTE_01'] == new_attr
    assert stored[LINK_ID]['DISUSE_FLAG'] == '0'


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# B. 変数タイプ変化なし
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def test_no_attr_change_with_restore_only_flips_disuse_flag(mock_g, dummy_db):
    """変数タイプが同じで廃止済みの場合、DISUSE_FLAG だけが戻り、タイプ更新 UPDATE は空"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_STD, disuse_flag='1')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_STD)]}))

    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=LINK_ID)
    assert row['DISUSE_FLAG'] == '0'
    assert row['VARS_ATTRIBUTE_01'] == ATTR_STD
    assert row['NOTE'] == 'initial note'

    assert dummy_db.update_data_list(UPDATE_CALL_TYPE_CHANGE) == []
    assert len(dummy_db.update_data_list(UPDATE_CALL_RESTORE)) == 1
    assert dummy_db.update_data_list(UPDATE_CALL_DISCARD) == []


def test_no_change_at_all_is_noop(mock_g, dummy_db):
    """変数タイプも DISUSE_FLAG も変化が無い場合、3 つの UPDATE と INSERT がすべて空"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_STD, disuse_flag='0')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_STD)]}))

    assert [call['data_list'] for call in dummy_db.update_calls] == [[], [], []]
    assert [call['data_list'] for call in dummy_db.insert_calls] == [[]]

    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=LINK_ID)
    assert row['LAST_UPDATE_USER'] == OLD_USER_ID, "no-op なのに更新者が書き換わっている"


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# C. 新規登録
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def test_new_variable_is_inserted(mock_g, dummy_db):
    """stored に無い変数は INSERT される"""
    table = create_mov_vars_link_table(dummy_db, [])

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY)]}))

    inserted = dummy_db.insert_data_list(0)
    assert len(inserted) == 1
    assert inserted[0]['MOVEMENT_ID'] == MOVEMENT_ID
    assert inserted[0]['VARS_NAME'] == VAR_NAME
    assert inserted[0]['VARS_ATTRIBUTE_01'] == ATTR_M_ARRAY
    assert inserted[0]['DISUSE_FLAG'] == '0'
    assert inserted[0]['LAST_UPDATE_USER'] == TEST_USER_ID


def test_new_variable_is_excluded_from_attr_update(mock_g, dummy_db):
    """新規変数は変数タイプ更新の対象外（stored を引くと KeyError になるため skip されている）"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, 'VAR_existing', ATTR_STD, disuse_flag='0')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [
        ('VAR_existing', ATTR_STD),
        ('VAR_brand_new', ATTR_LIST),
    ]}))

    assert dummy_db.update_data_list(UPDATE_CALL_TYPE_CHANGE) == []
    assert len(dummy_db.insert_data_list(0)) == 1
    assert dummy_db.insert_data_list(0)[0]['VARS_NAME'] == 'VAR_brand_new'


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# D. 廃止
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def test_missing_variable_is_discarded_without_touching_other_columns(mock_g, dummy_db):
    """解析結果に無い変数は廃止される。その際 NOTE 等の更新対象外カラムは保持される"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_M_ARRAY, disuse_flag='0', note='keep me')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: []}))

    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=LINK_ID)
    assert row['DISUSE_FLAG'] == '1'
    assert row['NOTE'] == 'keep me'
    assert row['VARS_ATTRIBUTE_01'] == ATTR_M_ARRAY
    assert row['LAST_UPDATE_USER'] == TEST_USER_ID


def test_already_discarded_variable_is_not_updated_again(mock_g, dummy_db):
    """既に廃止済みの変数は廃止 UPDATE の対象にならない"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_STD, disuse_flag='1')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: []}))

    assert dummy_db.update_data_list(UPDATE_CALL_DISCARD) == []


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# E. 契約テスト（UPDATE の SET カラム集合）
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def test_restore_update_sets_only_disuse_flag_columns(mock_g, dummy_db):
    """復活 UPDATE が SET するカラムは DISUSE_FLAG 関連のみ

    table_update は data のキー全部を SET するので、ここに VARS_ATTRIBUTE_01 や NOTE が
    混ざると直前/別処理の更新を巻き戻す（Issue #2618 の直接原因）。
    """
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_STD, disuse_flag='1')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY)]}))

    restore_data_list = dummy_db.update_data_list(UPDATE_CALL_RESTORE)
    assert len(restore_data_list) == 1
    assert set(restore_data_list[0].keys()) == DISUSE_FLAG_UPDATE_COLUMNS
    assert restore_data_list[0]['DISUSE_FLAG'] == '0'


def test_discard_update_sets_only_disuse_flag_columns(mock_g, dummy_db):
    """廃止 UPDATE が SET するカラムも DISUSE_FLAG 関連のみ（復活側と対称にした予防的修正の固定）"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_STD, disuse_flag='0')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: []}))

    discard_data_list = dummy_db.update_data_list(UPDATE_CALL_DISCARD)
    assert len(discard_data_list) == 1
    assert set(discard_data_list[0].keys()) == DISUSE_FLAG_UPDATE_COLUMNS
    assert discard_data_list[0]['DISUSE_FLAG'] == '1'


def test_attr_change_update_sets_only_attr_columns(mock_g, dummy_db):
    """変数タイプ更新 UPDATE が SET するカラムは変数タイプ関連のみ"""
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_STD, disuse_flag='0')]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY)]}))

    type_data_list = dummy_db.update_data_list(UPDATE_CALL_TYPE_CHANGE)
    assert len(type_data_list) == 1
    assert set(type_data_list[0].keys()) == {'MVMT_VAR_LINK_ID', 'VARS_ATTRIBUTE_01', 'LAST_UPDATE_USER'}
    assert 'DISUSE_FLAG' not in type_data_list[0]


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# F. 複合ケース
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def test_register_restore_discard_and_type_change_at_once(mock_g, dummy_db):
    """1 回の呼び出しで登録/復活/廃止/タイプ変更が同時発生しても互いに干渉しない

    (MOVEMENT_ID, VARS_NAME) のタプルキーで集合が分離されているため、
    別 Movement の同名変数も独立に扱われる。
    """
    other_movement_id = "movement-0002"
    link_rows = [
        create_link_row('link-keep', MOVEMENT_ID, 'VAR_keep', ATTR_STD, disuse_flag='0'),
        create_link_row('link-type', MOVEMENT_ID, 'VAR_type_change', ATTR_STD, disuse_flag='0'),
        create_link_row('link-both', MOVEMENT_ID, 'VAR_restore_and_change', ATTR_STD, disuse_flag='1'),
        create_link_row('link-restore', MOVEMENT_ID, 'VAR_restore_only', ATTR_LIST, disuse_flag='1'),
        create_link_row('link-discard', MOVEMENT_ID, 'VAR_discard', ATTR_LIST, disuse_flag='0', note='keep me'),
        # 別 Movement の同名変数（VAR_keep）はタプルキーで分離されるので独立に更新される
        create_link_row('link-other', other_movement_id, 'VAR_keep', ATTR_STD, disuse_flag='0'),
    ]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard(create_mov_vars_dict({
        MOVEMENT_ID: [
            ('VAR_keep', ATTR_STD),
            ('VAR_type_change', ATTR_M_ARRAY),
            ('VAR_restore_and_change', ATTR_M_ARRAY),
            ('VAR_restore_only', ATTR_LIST),
            ('VAR_brand_new', ATTR_LIST),
        ],
        other_movement_id: [
            ('VAR_keep', ATTR_LIST),
        ],
    }))

    expected = {
        'link-keep': (ATTR_STD, '0'),
        'link-type': (ATTR_M_ARRAY, '0'),
        'link-both': (ATTR_M_ARRAY, '0'),
        'link-restore': (ATTR_LIST, '0'),
        'link-discard': (ATTR_LIST, '1'),
        'link-other': (ATTR_LIST, '0'),
    }
    for link_id, (expected_attr, expected_disuse) in expected.items():
        row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=link_id)
        assert (row['VARS_ATTRIBUTE_01'], row['DISUSE_FLAG']) == (expected_attr, expected_disuse), \
            f"{link_id} の状態が期待と異なる"

    # 廃止された行の更新対象外カラムは保持される
    assert dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-discard')['NOTE'] == 'keep me'

    # 新規変数は INSERT される
    inserted = dummy_db.insert_data_list(0)
    assert len(inserted) == 1
    assert inserted[0]['VARS_NAME'] == 'VAR_brand_new'


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# G. 異常系
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

@pytest.mark.parametrize('fail_update_on_call,fail_insert_on_call,expected_code', [
    (1, None, "BKY-30011"),   # 変数タイプ更新
    (None, 1, "BKY-30003"),   # 新規登録
    (2, None, "BKY-30004"),   # 復活
    (3, None, "BKY-30005"),   # 廃止
], ids=['attr_update', 'insert', 'restore', 'discard'])
def test_db_failure_raises_app_exception(mock_g, dummy_db, fail_update_on_call, fail_insert_on_call, expected_code):
    """DB 操作が False を返したら、該当のエラーコードで AppException が上がる"""
    link_rows = [
        create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_STD, disuse_flag='1'),
        create_link_row('link-0002', MOVEMENT_ID, 'VAR_to_discard', ATTR_STD, disuse_flag='0'),
    ]
    table = create_mov_vars_link_table(dummy_db, link_rows)
    dummy_db.fail_update_on_call = fail_update_on_call
    dummy_db.fail_insert_on_call = fail_insert_on_call

    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [
        (VAR_NAME, ATTR_M_ARRAY),
        ('VAR_brand_new', ATTR_STD),
    ]})

    with pytest.raises(AppException) as excinfo:
        table.register_and_discard(mov_vars_dict)

    assert excinfo.value.args[0] == expected_code
    assert excinfo.value.args[1] == [TABLE_MVMT_VAR_LINK]
