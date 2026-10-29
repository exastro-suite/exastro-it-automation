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

"""MovementVarsLinkTable → NestVarsMemberTable を backyard_main の順に通す結合テスト

各クラス単体のテスト（test_movement_vars_link_table.py / test_nest_vars_member_table.py）では
拾えない「前段の UPDATE 結果を後段がそのまま使う」流れを、DummyDB 1 個で再現して固定する。

対象シナリオは「同名変数の変数タイプが変わった状態で復活する」ケース。
  - 一般変数 / 複数具体値変数 → 廃止 → 同名を多段変数として再登録
  - 多段変数 → 廃止 → 同名を一般変数 / 複数具体値変数として再登録

MovementVarsLinkTable.register_and_discard() 内では
  1. 変数タイプ更新 UPDATE（VARS_ATTRIBUTE_01）
  2. 復活 UPDATE（DISUSE_FLAG '1' → '0'）
が同一行に走る。2 が古いスナップショットの全カラムを渡すと 1 が巻き戻り、
NestVarsMemberTable.register_and_discard() が mov_vars_link_id_dict を引けず KeyError になる。
このファイルは「KeyError が出ないこと」「VARS_ATTRIBUTE_01 が新しい値になること」を確認する。

経緯: Issue #2618（再現手順は Issue 記載）。
"""
import pytest

from tests.common import (
    ATTR_LIST,
    ATTR_M_ARRAY,
    ATTR_STD,
    TABLE_MVMT_VAR_LINK,
    TABLE_NESTVAR_MEMBER,
    create_mov_vars_link_table,
    create_nest_vars_member_table,
    create_link_row,
    create_member_row,
    create_mov_vars_dict,
    create_nest_var_struct,
)

MOVEMENT_ID = "movement-0001"
VAR_NAME = "VAR_reused_name"
LINK_ID = "link-0001"


def run_backyard_main_sequence(dummy_db, link_rows, member_rows, mov_vars_dict):
    """backyard_main.py:105-111 の呼び出し順を再現する

    Returns:
        (mov_vars_link_table, nest_vars_mem_table)
    """
    mov_vars_link_table = create_mov_vars_link_table(dummy_db, link_rows)
    nest_vars_mem_table = create_nest_vars_member_table(dummy_db, member_rows)

    # Movement変数 登録・廃止
    mov_vars_link_table.register_and_discard(mov_vars_dict)
    registerd_mov_vars_link_records = mov_vars_link_table.get_stored_records()

    # メンバ変数 登録・廃止
    nest_vars_mem_table.register_and_discard(mov_vars_dict, registerd_mov_vars_link_records)

    return mov_vars_link_table, nest_vars_mem_table


@pytest.mark.parametrize('old_attr', [ATTR_STD, ATTR_LIST], ids=['from_std', 'from_list'])
def test_discarded_var_rebuilt_as_nest_var_does_not_raise(mock_g, dummy_db, old_attr):
    """廃止済みの一般変数/複数具体値変数を多段変数として再登録しても KeyError にならない"""
    var_struct = create_nest_var_struct(member_names=('member1', 'member2'))
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, old_attr, disuse_flag='1')]
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, ATTR_M_ARRAY, var_struct)]})

    # KeyError が出ないこと自体が assert（前段の UPDATE 巻き戻りがあるとここで落ちる）
    run_backyard_main_sequence(dummy_db, link_rows, [], mov_vars_dict)

    link_row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=LINK_ID)
    assert link_row['VARS_ATTRIBUTE_01'] == ATTR_M_ARRAY, "変数タイプ更新が復活UPDATEで巻き戻っている"
    assert link_row['DISUSE_FLAG'] == '0'

    # 多段変数メンバが登録される
    member_rows = dummy_db.rows(TABLE_NESTVAR_MEMBER)
    assert len(member_rows) == 2
    assert {row['VARS_NAME'] for row in member_rows} == {'member1', 'member2'}
    assert all(row['MVMT_VAR_LINK_ID'] == LINK_ID for row in member_rows)
    assert all(row['DISUSE_FLAG'] == '0' for row in member_rows)


@pytest.mark.parametrize('new_attr', [ATTR_STD, ATTR_LIST], ids=['to_std', 'to_list'])
def test_discarded_nest_var_rebuilt_as_flat_var_discards_members(mock_g, dummy_db, new_attr):
    """廃止済みの多段変数を一般変数/複数具体値変数として再登録した場合（第二の症状）

    KeyError にはならないが、修正前は VARS_ATTRIBUTE_01 が '3' のまま巻き戻り、
    メニュー上の変数タイプが実態と食い違う。
    """
    var_struct = create_nest_var_struct(member_names=('member1',))
    link_rows = [create_link_row(LINK_ID, MOVEMENT_ID, VAR_NAME, ATTR_M_ARRAY, disuse_flag='1')]
    member_rows = [create_member_row('member-0001', LINK_ID, var_struct['CHAIN_ARRAY'][0])]
    mov_vars_dict = create_mov_vars_dict({MOVEMENT_ID: [(VAR_NAME, new_attr)]})

    run_backyard_main_sequence(dummy_db, link_rows, member_rows, mov_vars_dict)

    link_row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=LINK_ID)
    assert link_row['VARS_ATTRIBUTE_01'] == new_attr, "変数タイプ更新が復活UPDATEで巻き戻っている"
    assert link_row['DISUSE_FLAG'] == '0'

    # 多段変数ではなくなったのでメンバ行は廃止される
    member_row = dummy_db.find_row(TABLE_NESTVAR_MEMBER, ARRAY_MEMBER_ID='member-0001')
    assert member_row['DISUSE_FLAG'] == '1'
