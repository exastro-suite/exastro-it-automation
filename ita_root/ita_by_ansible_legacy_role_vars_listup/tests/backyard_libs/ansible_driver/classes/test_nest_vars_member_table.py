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

"""NestVarsMemberTable.register_and_discard() のテスト

Issue #2618 で症状が顕在化した場所（NestVarsMemberTableClass.py:59 の KeyError）の現状仕様を固定する。
このクラスは「解析結果が多段変数なら、対応する T_ANSR_MVMT_VAR_LINK の行も多段変数である」ことを
無条件に前提にしている。前提が崩れると KeyError で処理全体が止まる。

この KeyError は #2618 の原因ではなく症状（原因は MovementVarsLinkTable 側の UPDATE）。
将来 `.get()` + warning の防御（案 D）を入れる場合は、test_attr_mismatch_raises_key_error の
期待値を差し替えることになる。
"""
import pytest

from common_libs.common.exception import AppException

from tests.common import (
    ATTR_LIST,
    ATTR_M_ARRAY,
    ATTR_STD,
    OLD_USER_ID,
    TABLE_NESTVAR_MEMBER,
    TEST_USER_ID,
    create_nest_vars_member_table,
    create_link_row,
    create_member_row,
    create_mov_vars_dict,
    create_nest_var_struct,
)

MOVEMENT_ID = "movement-0001"
VAR_NAME = "VAR_nest"
LINK_ID = "link-0001"

# table_update の呼び出し順（register_and_discard 内）
UPDATE_CALL_RESTORE = 0
UPDATE_CALL_DISCARD = 1


def create_link_records(var_attr, disuse_flag='0'):
    """MovementVarsLinkTable.get_stored_records() 相当の dict を組み立てる"""
    return {LINK_ID: create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, var_attr, disuse_flag=disuse_flag)}


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# H. KeyError の顕在化条件
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

@pytest.mark.parametrize('db_attr', [ATTR_STD, ATTR_LIST], ids=['db_std', 'db_list'])
def test_attr_mismatch_raises_key_error(mock_g, dummy_db, db_attr):
    """解析結果が多段変数なのに Movement変数側が多段変数でない場合、KeyError になる（現状仕様）

    #2618 では MovementVarsLinkTable の attr が巻き戻ることでこの状態が作られていた。
    """
    var_struct = create_nest_var_struct(member_names=('member1',))
    table = create_nest_vars_member_table(dummy_db, [])
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY, var_struct)]})

    with pytest.raises(KeyError) as excinfo:
        table.register_and_discard(mov_vars_dict, create_link_records(db_attr))

    assert excinfo.value.args[0] == (MOVEMENT_ID, VAR_NAME)


def test_attr_matched_registers_members(mock_g, dummy_db):
    """両者とも多段変数なら例外なくメンバが登録される"""
    var_struct = create_nest_var_struct(member_names=('member1', 'member2'))
    table = create_nest_vars_member_table(dummy_db, [])
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY, var_struct)]})

    table.register_and_discard(mov_vars_dict, create_link_records(ATTR_M_ARRAY))

    inserted = dummy_db.insert_data_list(0)
    assert len(inserted) == 2
    assert {record['VARS_NAME'] for record in inserted} == {'member1', 'member2'}
    assert all(record['MVMT_VAR_LINK_ID'] == LINK_ID for record in inserted)
    assert all(record['DISUSE_FLAG'] == '0' for record in inserted)
    assert all(record['LAST_UPDATE_USER'] == TEST_USER_ID for record in inserted)
    # COL_SEQ_MEMBER は T_ANSR_NESTVAR_MEMBER のカラムではないので落とされる
    assert all('COL_SEQ_MEMBER' not in record for record in inserted)


def test_flat_variable_is_ignored_entirely(mock_g, dummy_db):
    """解析結果が多段変数でない場合、Movement変数側の attr を引かないので KeyError にならない"""
    table = create_nest_vars_member_table(dummy_db, [])
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_STD)]})

    table.register_and_discard(mov_vars_dict, create_link_records(ATTR_STD))

    assert dummy_db.insert_data_list(0) == []
    assert dummy_db.update_data_list(UPDATE_CALL_RESTORE) == []
    assert dummy_db.update_data_list(UPDATE_CALL_DISCARD) == []


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# I. 多段変数 → 多段変数以外に変わった場合のメンバ廃止
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

@pytest.mark.parametrize('new_attr', [ATTR_STD, ATTR_LIST], ids=['to_std', 'to_list'])
def test_members_are_discarded_when_var_is_no_longer_nested(mock_g, dummy_db, new_attr):
    """多段変数をやめた場合、既存のメンバ行が廃止される（例外は出ない）"""
    var_struct = create_nest_var_struct(member_names=('member1',))
    member_rows = [create_member_row('member-0001', LINK_ID, var_struct['CHAIN_ARRAY'][0])]
    table = create_nest_vars_member_table(dummy_db, member_rows)
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, new_attr)]})

    table.register_and_discard(mov_vars_dict, create_link_records(new_attr))

    row = dummy_db.find_row(TABLE_NESTVAR_MEMBER, ARRAY_MEMBER_ID='member-0001')
    assert row['DISUSE_FLAG'] == '1'
    assert row['LAST_UPDATE_USER'] == TEST_USER_ID


def test_discarded_member_is_restored(mock_g, dummy_db):
    """廃止済みのメンバが解析結果に再登場したら復活する"""
    var_struct = create_nest_var_struct(member_names=('member1',))
    member_rows = [create_member_row('member-0001', LINK_ID, var_struct['CHAIN_ARRAY'][0], disuse_flag='1')]
    table = create_nest_vars_member_table(dummy_db, member_rows)
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY, var_struct)]})

    table.register_and_discard(mov_vars_dict, create_link_records(ATTR_M_ARRAY))

    assert dummy_db.insert_data_list(0) == [], "既存メンバが重複登録されている"
    row = dummy_db.find_row(TABLE_NESTVAR_MEMBER, ARRAY_MEMBER_ID='member-0001')
    assert row['DISUSE_FLAG'] == '0'


def test_unchanged_member_is_not_modified(mock_g, dummy_db):
    """変化の無いメンバは値が書き換わらない（更新者も変わらない）"""
    var_struct = create_nest_var_struct(member_names=('member1',))
    member_rows = [create_member_row('member-0001', LINK_ID, var_struct['CHAIN_ARRAY'][0])]
    table = create_nest_vars_member_table(dummy_db, member_rows)
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY, var_struct)]})

    table.register_and_discard(mov_vars_dict, create_link_records(ATTR_M_ARRAY))

    assert dummy_db.insert_data_list(0) == []
    row = dummy_db.find_row(TABLE_NESTVAR_MEMBER, ARRAY_MEMBER_ID='member-0001')
    assert row['DISUSE_FLAG'] == '0'
    assert row['LAST_UPDATE_USER'] == OLD_USER_ID


def test_discarded_movement_var_link_record_is_skipped(mock_g, dummy_db):
    """Movement変数側が多段変数でも、解析結果に無ければメンバは登録されない"""
    table = create_nest_vars_member_table(dummy_db, [])

    table.register_and_discard(create_mov_vars_dict({MOVEMENT_ID: []}), create_link_records(ATTR_M_ARRAY))

    assert dummy_db.insert_data_list(0) == []


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# 異常系
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

@pytest.mark.parametrize('fail_update_on_call,fail_insert_on_call,expected_code', [
    (None, 1, "BKY-30003"),   # 登録
    (1, None, "BKY-30004"),   # 更新・復活
    (2, None, "BKY-30005"),   # 廃止
], ids=['insert', 'restore', 'discard'])
def test_db_failure_raises_app_exception(mock_g, dummy_db, fail_update_on_call, fail_insert_on_call, expected_code):
    """DB 操作が False を返したら、該当のエラーコードで AppException が上がる"""
    var_struct = create_nest_var_struct(member_names=('member1', 'member2'))
    member_rows = [create_member_row('member-0001', LINK_ID, var_struct['CHAIN_ARRAY'][0])]
    table = create_nest_vars_member_table(dummy_db, member_rows)
    dummy_db.fail_update_on_call = fail_update_on_call
    dummy_db.fail_insert_on_call = fail_insert_on_call

    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY, var_struct)]})

    with pytest.raises(AppException) as excinfo:
        table.register_and_discard(mov_vars_dict, create_link_records(ATTR_M_ARRAY))

    assert excinfo.value.args[0] == expected_code
    assert excinfo.value.args[1] == [TABLE_NESTVAR_MEMBER]
