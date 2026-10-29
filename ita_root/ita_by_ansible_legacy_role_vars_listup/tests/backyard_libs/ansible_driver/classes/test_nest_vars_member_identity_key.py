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

"""多段変数メンバー管理の突き合わせで使う同一性キー（9 項目）の境界を確認する（型ゆれ・欠損・重複・並び順）

既存行と解析結果は 9 項目を文字列化して比べ、同じキーの行が複数あれば先に現れた方を採用する（先勝ち）。
定義順と親メンバー（親の定義順）は同一性キーに含めず、一致した行に解析結果の値を取り込む（親メンバーは #3096 で外した）。
期待結果は親メンバー以外は改修前の実装と同じ。最小構成（既存 0〜2 行、解析結果 0〜2 件）を手書きの行で組む。

経緯: Issue #3072
"""
import pytest

from tests.common import (
    ATTR_M_ARRAY, TEST_USER_ID, TABLE_NESTVAR_MEMBER,
    create_link_row, create_mov_vars_dict, create_variable, create_chain_array_item, create_member_row,
    create_nest_vars_member_table, create_active_link_records,
)


MOVEMENT = 'mv-1'
LINK_ID = 'link-1'


def _links():
    return create_active_link_records([create_link_row(LINK_ID, MOVEMENT, 'VAR_x', ATTR_M_ARRAY)])


def _extraction(*items):
    """解析結果のメンバー（CHAIN_ARRAY 要素）から多段変数 1 つ分の解析結果を組む"""
    variable = create_variable('VAR_x', ATTR_M_ARRAY, {'CHAIN_ARRAY': list(items)})
    return create_mov_vars_dict({MOVEMENT: [variable]})


def _item(vars_key_id='1', vars_name='member', **overrides):
    """解析結果のメンバー 1 件。overrides は列名（VRAS_NAME_ALIAS など）で上書きする"""
    item = create_chain_array_item(vars_key_id=vars_key_id, vars_name=vars_name)
    for column, value in overrides.items():
        assert column in item, f"unknown column {column}"
        item[column] = value
    return item


def _stored(member_id, item, disuse_flag='0'):
    return create_member_row(member_id, LINK_ID, item, disuse_flag)


def _apply(dummy_db, stored_rows, *extracted_items):
    table = create_nest_vars_member_table(dummy_db, stored_rows)
    table.register_and_discard(_extraction(*extracted_items), _links())
    inserts = dummy_db.insert_calls_for(TABLE_NESTVAR_MEMBER)
    updates = dummy_db.update_calls_for(TABLE_NESTVAR_MEMBER)
    return inserts[0]['data_list'], updates[0]['data_list'], updates[1]['data_list']


def _ids(records):
    ids = []
    for record in records:
        ids.append(record['ARRAY_MEMBER_ID'])
    return sorted(ids)


def _values(records, column):
    """レコードの並び順のまま 1 列だけ文字列で取り出す（並び順を確認するテスト用）"""
    values = []
    for record in records:
        values.append(str(record[column]))
    return values


def test_missing_alias_equals_string_none(mock_g, dummy_db):
    """表示名が無い（None）既存行と、表示名が文字列 "None" の解析結果は同じメンバー扱い（文字列化して比べるため）

    経緯: Issue #3072
    """
    stored_item = _item(VRAS_NAME_ALIAS=None)
    register, restore, discard = _apply(dummy_db, [_stored('m-1', stored_item)], _item(VRAS_NAME_ALIAS='None'))

    assert (register, discard) == ([], [])
    assert _ids(restore) == ['m-1']


def test_missing_alias_differs_from_empty_string(mock_g, dummy_db):
    """表示名が無い（None）既存行と、表示名が空文字の解析結果は別メンバー扱い

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [_stored('m-1', _item(VRAS_NAME_ALIAS=None))], _item(VRAS_NAME_ALIAS=''))

    assert len(register) == 1
    assert restore == []
    assert _ids(discard) == ['m-1']


@pytest.mark.parametrize('column', [
    pytest.param('ARRAY_NEST_LEVEL', id='level'),
    pytest.param('ASSIGN_SEQ_NEED', id='assign_seq'),
    pytest.param('COL_SEQ_NEED', id='col_seq'),
    pytest.param('MEMBER_DISP', id='disp'),
    pytest.param('MAX_COL_SEQ', id='max_col'),
])
def test_int_and_str_are_same_member(mock_g, dummy_db, column):
    """DB の数値列（階層・代入順序有無・列順序有無・表示有無・最大繰返数）が数値で、解析結果が文字列でも同じメンバー扱い

    文字列化を外すと全行が別扱い（全廃止＋全登録）になる。
    親メンバーも数値列だが同一性キーに含まれないので、ここではなく test_parent_order_is_not_part_of_identity_key で確認する。
    経緯: Issue #3072
    """
    stored_item = _item()
    stored_item[column] = 7
    extracted_item = _item()
    extracted_item[column] = '7'
    register, restore, discard = _apply(dummy_db, [_stored('m-1', stored_item)], extracted_item)

    assert (register, discard) == ([], [])
    assert _ids(restore) == ['m-1']


@pytest.mark.parametrize('stored_parent, extracted_parent', [
    pytest.param(7, '7', id='same_value_int_str'),
    pytest.param(7, '9', id='different_value'),
])
def test_parent_order_is_not_part_of_identity_key(mock_g, dummy_db, stored_parent, extracted_parent):
    """親メンバー（親の定義順）は同一性キーに含まれないので、型が違っても値が違っても同じメンバー扱いになり、
    既存行の親メンバーは解析結果の値に書き換わる

    #3096 より前は親メンバーが同一性キーに入っていたため、値が違うと廃止＋登録になっていた（#3096 で修正）。
    経緯: Issue #3072
    """
    stored_item = _item()
    stored_item['PARENT_VARS_KEY_ID'] = stored_parent
    extracted_item = _item()
    extracted_item['PARENT_VARS_KEY_ID'] = extracted_parent
    register, restore, discard = _apply(dummy_db, [_stored('m-1', stored_item)], extracted_item)

    assert (register, discard) == ([], [])
    assert _ids(restore) == ['m-1']
    assert restore[0]['PARENT_VARS_KEY_ID'] == extracted_parent
    assert dummy_db.find_row(TABLE_NESTVAR_MEMBER, ARRAY_MEMBER_ID='m-1')['PARENT_VARS_KEY_ID'] == extracted_parent


def test_member_name_is_case_sensitive(mock_g, dummy_db):
    """メンバー名の大文字小文字が違えば別メンバー扱い

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [_stored('m-1', _item(vars_name='Name'))], _item(vars_name='name'))

    assert (len(register), restore, _ids(discard)) == (1, [], ['m-1'])


def test_trailing_space_is_different_member(mock_g, dummy_db):
    """メンバー名の末尾空白が違えば別メンバー扱い

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [_stored('m-1', _item(vars_name='name '))], _item(vars_name='name'))

    assert (len(register), restore, _ids(discard)) == (1, [], ['m-1'])


def test_bool_and_str_flags_are_different(mock_g, dummy_db):
    """表示有無が真偽値 False の行と文字列 "0" の行は別メンバー扱い（"False" と "0" は違う文字列）

    経緯: Issue #3072
    """
    stored_item = _item()
    stored_item['MEMBER_DISP'] = False
    register, restore, discard = _apply(dummy_db, [_stored('m-1', stored_item)], _item(MEMBER_DISP='0'))

    assert (len(register), restore, _ids(discard)) == (1, [], ['m-1'])


def test_two_stored_duplicates_kept_for_one_extracted(mock_g, dummy_db):
    """同一キーの既存行が 2 行あり解析結果が 1 件なら、2 行とも廃止されず、どちらも解析結果の定義順になる。登録は 0

    重複が自然に減らないのは改修前と同じ（等価性優先）。
    経緯: Issue #3072（等価性優先）
    """
    register, restore, discard = _apply(
        dummy_db, [_stored('m-1', _item(vars_key_id='1')), _stored('m-2', _item(vars_key_id='7'))], _item(vars_key_id='3'))

    assert (register, discard) == ([], [])
    assert _ids(restore) == ['m-1', 'm-2']
    for record in restore:
        assert str(record['VARS_KEY_ID']) == '3'


def test_first_extracted_duplicate_decides_order(mock_g, dummy_db):
    """既存行 1 行に同一キーの解析結果が 2 件（定義順 5 と 6）あると、既存行の定義順は先に現れた 5 になる。登録は 0

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [_stored('m-1', _item(vars_key_id='1'))], _item(vars_key_id='5'), _item(vars_key_id='6'))

    assert (register, discard) == ([], [])
    assert _values(restore, 'VARS_KEY_ID') == ['5']


def test_reversed_extracted_duplicates_decide_order(mock_g, dummy_db):
    """解析結果の同一キー 2 件の並びを逆（6, 5）にすると、既存行の定義順は 6 になる（並び順に依存する。改修前と同じ）

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [_stored('m-1', _item(vars_key_id='1'))], _item(vars_key_id='6'), _item(vars_key_id='5'))

    assert (register, discard) == ([], [])
    assert _values(restore, 'VARS_KEY_ID') == ['6']


def test_extracted_duplicates_all_registered(mock_g, dummy_db):
    """既存行が無く同一キーの解析結果が 2 件なら、2 件とも登録される（1 件に畳まれない。改修前と同じ）

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [], _item(vars_key_id='5'), _item(vars_key_id='6'))

    assert _values(register, 'VARS_KEY_ID') == ['5', '6']
    assert (restore, discard) == ([], [])


def test_stored_duplicates_all_discarded(mock_g, dummy_db):
    """同一キーの既存行が 2 行あり解析結果に無ければ、2 行とも廃止される

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [_stored('m-1', _item()), _stored('m-2', _item(vars_key_id='7'))])

    assert (register, restore) == ([], [])
    assert _ids(discard) == ['m-1', 'm-2']


def test_empty_both_sides_completes(mock_g, dummy_db):
    """既存行 0・解析結果 0 でも、登録・復活・廃止が空リストで呼ばれ正常終了する

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [])

    assert (register, restore, discard) == ([], [], [])


def test_all_registered_when_nothing_stored(mock_g, dummy_db):
    """既存行が無ければ解析結果の N 件が全部登録される

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [], _item('1', 'a'), _item('2', 'b'), _item('3', 'c'))

    assert _values(register, 'VARS_NAME') == ['a', 'b', 'c']
    assert (restore, discard) == ([], [])


def test_all_discarded_when_nothing_extracted(mock_g, dummy_db):
    """解析結果が無ければ有効な既存行 N 件が全部廃止される

    経緯: Issue #3072
    """
    register, restore, discard = _apply(dummy_db, [_stored('m-1', _item('1', 'a')), _stored('m-2', _item('2', 'b'))])

    assert (register, restore) == ([], [])
    assert _ids(discard) == ['m-1', 'm-2']
    for record in discard:
        assert (record['DISUSE_FLAG'], record['LAST_UPDATE_USER']) == ('1', TEST_USER_ID)


def test_order_aware_key_separates_different_orders(mock_g, dummy_db):
    """定義順まで比較する照合方式（現在どこからも呼ばれない）では、定義順が違えば別扱いになる

    経緯: Issue #3072
    """
    from backyard_libs.ansible_driver.classes.NestVarsMemberTableClass import NestVarsMemberTable

    table = NestVarsMemberTable(dummy_db)
    stored = [_stored('m-1', _item(vars_key_id='1'))]
    extracted = [_item(vars_key_id='2')]
    extracted[0]['MVMT_VAR_LINK_ID'] = LINK_ID     # 反映処理が付ける親変数 ID をここでは手で付ける

    keyed_stored = table._keyed_records(stored, ignore_vars_key_id=False)
    index_extracted = table._index_by_record_key(table._keyed_records(extracted, ignore_vars_key_id=False))
    assert _ids(table._a_minus_b(keyed_stored, index_extracted)) == ['m-1']
    assert table._a_and_b(keyed_stored, index_extracted) == []

    keyed_stored_default = table._keyed_records(stored)
    index_extracted_default = table._index_by_record_key(table._keyed_records(extracted))
    assert table._a_minus_b(keyed_stored_default, index_extracted_default) == []


def test_result_keeps_input_order_and_duplicates(mock_g, dummy_db):
    """登録・廃止の結果は入力の並び順のままで、重複も潰されない（集合化しない）

    経緯: Issue #3072
    """
    register, restore, discard = _apply(
        dummy_db,
        [_stored('m-3', _item('1', 'c')), _stored('m-1', _item('2', 'a')), _stored('m-2', _item('3', 'a'))],
        _item('1', 'z'), _item('2', 'y'), _item('3', 'y'),
    )

    assert _values(register, 'VARS_NAME') == ['z', 'y', 'y']
    assert _values(discard, 'ARRAY_MEMBER_ID') == ['m-3', 'm-1', 'm-2']
    assert restore == []
