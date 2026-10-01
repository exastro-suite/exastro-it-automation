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

"""Movement-変数紐付への反映を段単体で確認する（既存行の状態 × 変数タイプの遷移、更新項目の絞り込み）

入力は「刈取開始時点の Movement-変数紐付の行（有効／廃止）」と「解析結果（変数名とタイプ）」。
反映は 型更新 → 登録 → 復活 → 廃止 → 再読込 の順で走り、UPDATE は渡した項目が全部書かれる（DB の癖）ため、
復活・廃止で全項目を渡すと直前の型更新が巻き戻る（Issue #2618）。

経緯: Issue #2618 / #3072
"""
import pytest

from common_libs.common.exception import AppException
from tests.common import (
    ATTR_STD, ATTR_LIST, ATTR_M_ARRAY, TEST_USER_ID, OLD_USER_ID, OLD_TIMESTAMP,
    TABLE_MVMT_VAR_LINK,
    create_link_row, create_mov_vars_dict, create_mov_vars_link_table, create_nest_var_struct,
)


MOVEMENT = 'mv-1'
VAR = 'VAR_x'

TYPE_IDS = {ATTR_STD: 'std', ATTR_LIST: 'list', ATTR_M_ARRAY: 'nest'}
ALL_TYPES = []
for _attr, _name in TYPE_IDS.items():
    ALL_TYPES.append(pytest.param(_attr, id=_name))
TYPE_CHANGES = []
for _from in (ATTR_STD, ATTR_LIST, ATTR_M_ARRAY):
    for _to in (ATTR_STD, ATTR_LIST, ATTR_M_ARRAY):
        if _from != _to:
            TYPE_CHANGES.append(pytest.param(_from, _to, id=f"{TYPE_IDS[_from]}_to_{TYPE_IDS[_to]}"))


def _extraction(*specs):
    """Movement 1 つ分の解析結果。specs は (変数名, タイプ)。多段は構造付きにする"""
    var_specs = []
    for var_name, var_attr in specs:
        if var_attr == ATTR_M_ARRAY:
            var_specs.append((var_name, var_attr, create_nest_var_struct()))
        else:
            var_specs.append((var_name, var_attr))
    return create_mov_vars_dict({MOVEMENT: var_specs})


def _apply(dummy_db, link_rows, *specs):
    """Movement-変数紐付のテーブルを用意して反映を 1 回実行し、テーブルオブジェクトを返す"""
    table = create_mov_vars_link_table(dummy_db, link_rows)
    table.register_and_discard(_extraction(*specs))
    return table


def _update_payloads(dummy_db):
    """Movement-変数紐付の反映が発行した 3 回の UPDATE（型更新・復活・廃止）の data_list を順に返す"""
    payloads = []
    for call in dummy_db.update_calls_for(TABLE_MVMT_VAR_LINK):
        payloads.append(call['data_list'])
    assert len(payloads) == 3
    return payloads


@pytest.mark.parametrize('var_attr', ALL_TYPES)
def test_new_variable_is_registered(mock_g, dummy_db, var_attr):
    """Playbook に新しい変数が現れると、そのタイプ・有効・実行ユーザで Movement-変数紐付に 1 行登録され、更新は 1 件も出ない

    経緯: Issue #2618 / #3072
    """
    _apply(dummy_db, [], (VAR, var_attr))

    inserted = dummy_db.insert_calls_for(TABLE_MVMT_VAR_LINK)[0]['data_list']
    assert inserted == [{
        'MOVEMENT_ID': MOVEMENT, 'VARS_NAME': VAR, 'VARS_ATTRIBUTE_01': var_attr,
        'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': TEST_USER_ID,
    }]
    assert _update_payloads(dummy_db) == [[], [], []]
    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, VARS_NAME=VAR)
    assert row['MVMT_VAR_LINK_ID'].startswith('generated-uuid-')


@pytest.mark.parametrize('var_attr', ALL_TYPES)
def test_missing_variable_is_discarded_with_only_flag_columns(mock_g, dummy_db, var_attr):
    """Playbook から消えた有効な変数は廃止される。UPDATE に載るのは行 ID・廃止フラグ・更新者だけで、タイプ・備考は変わらない

    経緯: Issue #2618
    """
    _apply(dummy_db, [create_link_row('link-1', MOVEMENT, VAR, var_attr, note='keep me')])

    type_update, restore, discard = _update_payloads(dummy_db)
    assert (type_update, restore) == ([], [])
    assert discard == [{'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '1', 'LAST_UPDATE_USER': TEST_USER_ID}]
    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-1')
    assert (row['DISUSE_FLAG'], row['VARS_ATTRIBUTE_01'], row['NOTE']) == ('1', var_attr, 'keep me')
    assert dummy_db.insert_calls_for(TABLE_MVMT_VAR_LINK)[0]['data_list'] == []


@pytest.mark.parametrize('var_attr', ALL_TYPES)
def test_missing_variable_already_discarded_is_left_alone(mock_g, dummy_db, var_attr):
    """Playbook に無い変数が既に廃止済みなら、何も更新されず更新者・更新日時も動かない

    経緯: Issue #2618
    """
    _apply(dummy_db, [create_link_row('link-1', MOVEMENT, VAR, var_attr, disuse_flag='1')])

    assert _update_payloads(dummy_db) == [[], [], []]
    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-1')
    assert (row['LAST_UPDATE_USER'], row['LAST_UPDATE_TIMESTAMP']) == (OLD_USER_ID, OLD_TIMESTAMP)


@pytest.mark.parametrize('var_attr', ALL_TYPES)
def test_unchanged_variable_causes_no_write(mock_g, dummy_db, var_attr):
    """有効な変数が同じタイプで Playbook にあれば、登録も更新も 1 件も出ず、更新者・更新日時は元のまま

    経緯: Issue #2618
    """
    _apply(dummy_db, [create_link_row('link-1', MOVEMENT, VAR, var_attr)], (VAR, var_attr))

    assert _update_payloads(dummy_db) == [[], [], []]
    assert dummy_db.insert_calls_for(TABLE_MVMT_VAR_LINK)[0]['data_list'] == []
    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-1')
    assert (row['LAST_UPDATE_USER'], row['LAST_UPDATE_TIMESTAMP']) == (OLD_USER_ID, OLD_TIMESTAMP)


@pytest.mark.parametrize('from_attr, to_attr', TYPE_CHANGES)
def test_type_change_on_active_row_updates_only_type(mock_g, dummy_db, from_attr, to_attr):
    """有効な変数のタイプが Playbook で変わると、型更新の UPDATE だけが出る。載る項目は行 ID・タイプ・更新者だけで廃止フラグは 0 のまま

    経緯: Issue #2618 / #3072
    """
    _apply(dummy_db, [create_link_row('link-1', MOVEMENT, VAR, from_attr, note='keep me')], (VAR, to_attr))

    type_update, restore, discard = _update_payloads(dummy_db)
    assert type_update == [{'MVMT_VAR_LINK_ID': 'link-1', 'VARS_ATTRIBUTE_01': to_attr, 'LAST_UPDATE_USER': TEST_USER_ID}]
    assert (restore, discard) == ([], [])
    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-1')
    assert (row['VARS_ATTRIBUTE_01'], row['DISUSE_FLAG'], row['NOTE']) == (to_attr, '0', 'keep me')


@pytest.mark.parametrize('var_attr', ALL_TYPES)
def test_returning_variable_is_restored_with_only_flag_columns(mock_g, dummy_db, var_attr):
    """廃止していた変数が同じタイプで Playbook に戻ると復活する。UPDATE に載るのは行 ID・廃止フラグ・更新者だけで型更新は出ない

    経緯: Issue #2618
    """
    _apply(dummy_db, [create_link_row('link-1', MOVEMENT, VAR, var_attr, disuse_flag='1', note='keep me')], (VAR, var_attr))

    type_update, restore, discard = _update_payloads(dummy_db)
    assert type_update == []
    assert restore == [{'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': TEST_USER_ID}]
    assert discard == []
    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-1')
    assert (row['DISUSE_FLAG'], row['VARS_ATTRIBUTE_01'], row['NOTE']) == ('0', var_attr, 'keep me')


@pytest.mark.parametrize('from_attr, to_attr', TYPE_CHANGES)
def test_returning_variable_with_new_type_keeps_type_and_restore(mock_g, dummy_db, from_attr, to_attr):
    """廃止していた変数を別のタイプで Playbook に書き直すと、型更新と復活の両方が最終状態に残る（復活が型更新を巻き戻さない）

    Issue #2618 の構造そのもの。std_to_nest / list_to_nest が Issue の再現手順。
    経緯: Issue #2618 / #3072
    """
    table = _apply(dummy_db, [create_link_row('link-1', MOVEMENT, VAR, from_attr, disuse_flag='1', note='keep me')], (VAR, to_attr))

    type_update, restore, discard = _update_payloads(dummy_db)
    assert type_update == [{'MVMT_VAR_LINK_ID': 'link-1', 'VARS_ATTRIBUTE_01': to_attr, 'LAST_UPDATE_USER': TEST_USER_ID}]
    assert restore == [{'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': TEST_USER_ID}]
    assert discard == []
    row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-1')
    assert (row['VARS_ATTRIBUTE_01'], row['DISUSE_FLAG'], row['NOTE']) == (to_attr, '0', 'keep me')
    # 再読込後のメモリ（多段変数メンバー管理が受け取る姿）にも両方が反映されている
    reloaded = table.get_stored_records()['link-1']
    assert (reloaded['VARS_ATTRIBUTE_01'], reloaded['DISUSE_FLAG']) == (to_attr, '0')


def test_reload_after_apply_contains_active_rows_only(mock_g, dummy_db):
    """反映後の再読込には有効行だけが入り、今回廃止した行も元から廃止の行も多段変数メンバー管理には渡らない

    経緯: Issue #2618 / #3072
    """
    table = _apply(dummy_db, [
        create_link_row('link-keep', MOVEMENT, 'VAR_keep', ATTR_STD),
        create_link_row('link-gone', MOVEMENT, 'VAR_gone', ATTR_M_ARRAY),
        create_link_row('link-old', MOVEMENT, 'VAR_old', ATTR_M_ARRAY, disuse_flag='1'),
    ], ('VAR_keep', ATTR_STD))

    assert sorted(table.get_stored_records().keys()) == ['link-keep']


def test_movements_with_same_variable_name_are_independent(mock_g, dummy_db):
    """別の Movement に同名の変数があっても Movement-変数紐付は Movement ごとに別行で、片方の変更が他方に波及しない

    経緯: Issue #2618 / #3072
    """
    table = create_mov_vars_link_table(dummy_db, [
        create_link_row('link-mv1', 'mv-1', VAR, ATTR_STD),
        create_link_row('link-mv2', 'mv-2', VAR, ATTR_M_ARRAY),
    ])
    table.register_and_discard(create_mov_vars_dict({
        'mv-1': [(VAR, ATTR_LIST)],
        'mv-2': [],
    }))

    row_mv1 = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-mv1')
    row_mv2 = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID='link-mv2')
    assert (row_mv1['VARS_ATTRIBUTE_01'], row_mv1['DISUSE_FLAG']) == (ATTR_LIST, '0')
    assert (row_mv2['VARS_ATTRIBUTE_01'], row_mv2['DISUSE_FLAG']) == (ATTR_M_ARRAY, '1')


def test_register_restore_discard_and_type_change_in_one_run(mock_g, dummy_db):
    """登録・無変更・型更新・復活・型更新＋復活・廃止 が 1 回の刈取に混在しても、それぞれの行に正しい結果だけが残る

    経緯: Issue #2618 / #3072
    """
    _apply(dummy_db, [
        create_link_row('link-same', MOVEMENT, 'VAR_same', ATTR_STD),
        create_link_row('link-retype', MOVEMENT, 'VAR_retype', ATTR_STD),
        create_link_row('link-restore', MOVEMENT, 'VAR_restore', ATTR_LIST, disuse_flag='1'),
        create_link_row('link-both', MOVEMENT, 'VAR_both', ATTR_STD, disuse_flag='1'),
        create_link_row('link-gone', MOVEMENT, 'VAR_gone', ATTR_LIST),
    ], ('VAR_new', ATTR_LIST), ('VAR_same', ATTR_STD), ('VAR_retype', ATTR_M_ARRAY),
        ('VAR_restore', ATTR_LIST), ('VAR_both', ATTR_M_ARRAY))

    expected = {
        'VAR_same': (ATTR_STD, '0', OLD_USER_ID),
        'VAR_retype': (ATTR_M_ARRAY, '0', TEST_USER_ID),
        'VAR_restore': (ATTR_LIST, '0', TEST_USER_ID),
        'VAR_both': (ATTR_M_ARRAY, '0', TEST_USER_ID),
        'VAR_gone': (ATTR_LIST, '1', TEST_USER_ID),
        'VAR_new': (ATTR_LIST, '0', TEST_USER_ID),
    }
    actual = {}
    for row in dummy_db.rows(TABLE_MVMT_VAR_LINK):
        actual[row['VARS_NAME']] = (row['VARS_ATTRIBUTE_01'], row['DISUSE_FLAG'], row['LAST_UPDATE_USER'])
        if row['VARS_NAME'] != 'VAR_new':
            assert row['NOTE'] == 'initial note'
    assert actual == expected


@pytest.mark.parametrize('failing_call, result_code', [
    pytest.param(('update', 1), 'BKY-30011', id='type_update'),
    pytest.param(('insert', 1), 'BKY-30003', id='register'),
    pytest.param(('update', 2), 'BKY-30004', id='restore'),
    pytest.param(('update', 3), 'BKY-30005', id='discard'),
])
def test_db_failure_raises_app_exception(mock_g, dummy_db, failing_call, result_code):
    """型更新・登録・復活・廃止の書き込みが失敗すると、段ごとのエラーコードで処理が止まる

    経緯: Issue #2618
    """
    kind, index = failing_call
    if kind == 'update':
        dummy_db.fail_update_on_call = index
    else:
        dummy_db.fail_insert_on_call = index

    with pytest.raises(AppException) as raised:
        _apply(dummy_db, [
            create_link_row('link-retype', MOVEMENT, 'VAR_retype', ATTR_STD),
            create_link_row('link-restore', MOVEMENT, 'VAR_restore', ATTR_STD, disuse_flag='1'),
            create_link_row('link-gone', MOVEMENT, 'VAR_gone', ATTR_STD),
        ], ('VAR_new', ATTR_STD), ('VAR_retype', ATTR_LIST), ('VAR_restore', ATTR_STD))

    assert raised.value.args[0] == result_code


def test_updates_do_not_mutate_rows_loaded_in_memory(mock_g, dummy_db):
    """復活・廃止・型更新は UPDATE 用の新しい辞書を作って渡し、刈取開始時に読み込んだメモリ上の行は書き換えない

    経緯: Issue #2618
    """
    link_rows = [
        create_link_row('link-restore', MOVEMENT, 'VAR_restore', ATTR_STD, disuse_flag='1'),
        create_link_row('link-gone', MOVEMENT, 'VAR_gone', ATTR_STD),
    ]
    table = create_mov_vars_link_table(dummy_db, link_rows)
    loaded = table.get_stored_records()
    loaded_restore = loaded['link-restore']
    loaded_gone = loaded['link-gone']

    table.register_and_discard(_extraction(('VAR_restore', ATTR_LIST)))

    assert (loaded_restore['DISUSE_FLAG'], loaded_restore['VARS_ATTRIBUTE_01'], loaded_restore['LAST_UPDATE_USER']) == ('1', ATTR_STD, OLD_USER_ID)
    assert (loaded_gone['DISUSE_FLAG'], loaded_gone['LAST_UPDATE_USER']) == ('0', OLD_USER_ID)


@pytest.mark.parametrize('with_stored_rows', [
    pytest.param(True, id='stored_rows_exist'),
    pytest.param(False, id='nothing_stored'),
])
def test_empty_extraction_discards_all_active_rows(mock_g, dummy_db, with_stored_rows):
    """Movement が 0 件（解析結果が空）でも例外にならず、Movement-変数紐付の有効行は全部廃止される。既存行も無ければ空のまま正常終了する

    経緯: Issue #2618 / #3072
    """
    link_rows = []
    if with_stored_rows:
        link_rows = [
            create_link_row('link-1', MOVEMENT, 'VAR_a', ATTR_STD),
            create_link_row('link-2', 'mv-2', 'VAR_b', ATTR_M_ARRAY),
            create_link_row('link-3', 'mv-2', 'VAR_c', ATTR_LIST, disuse_flag='1'),
        ]
    table = create_mov_vars_link_table(dummy_db, link_rows)

    table.register_and_discard({})

    type_update, restore, discard = _update_payloads(dummy_db)
    assert (type_update, restore) == ([], [])
    if with_stored_rows:
        discarded_link_ids = []
        for record in discard:
            discarded_link_ids.append(record['MVMT_VAR_LINK_ID'])
        assert sorted(discarded_link_ids) == ['link-1', 'link-2']
    else:
        assert discard == []
    assert dummy_db.insert_calls_for(TABLE_MVMT_VAR_LINK)[0]['data_list'] == []
    assert table.get_stored_records() == {}


def test_null_disuse_flag_row_is_not_updated(mock_g, dummy_db):
    """廃止フラグが空（None）の行は復活にも廃止にも当たらず、そのまま残る。再読込（有効行だけ）からも外れる

    経緯: Issue #2618
    """
    table = _apply(dummy_db, [
        create_link_row('link-present', MOVEMENT, 'VAR_present', ATTR_STD, disuse_flag=None),
        create_link_row('link-absent', MOVEMENT, 'VAR_absent', ATTR_STD, disuse_flag=None),
    ], ('VAR_present', ATTR_STD))

    assert _update_payloads(dummy_db) == [[], [], []]
    for link_id in ('link-present', 'link-absent'):
        row = dummy_db.find_row(TABLE_MVMT_VAR_LINK, MVMT_VAR_LINK_ID=link_id)
        assert (row['DISUSE_FLAG'], row['LAST_UPDATE_USER']) == (None, OLD_USER_ID)
    assert table.get_stored_records() == {}


def test_int_and_str_type_values_count_as_change(mock_g, dummy_db):
    """既存行の変数タイプが数値 3、解析結果が文字列 '3' だと（DB 列は文字列なので通常混在しないが）型更新が走る

    経緯: Issue #2618
    """
    stored = create_link_row('link-1', MOVEMENT, VAR, 3)
    _apply(dummy_db, [stored], (VAR, ATTR_M_ARRAY))

    type_update, _, _ = _update_payloads(dummy_db)
    assert type_update == [{'MVMT_VAR_LINK_ID': 'link-1', 'VARS_ATTRIBUTE_01': ATTR_M_ARRAY, 'LAST_UPDATE_USER': TEST_USER_ID}]


def test_none_movement_id_and_variable_name_are_accepted(mock_g, dummy_db):
    """Movement ID や変数名が None でも、(None, 変数名) の組で突き合わされ例外にならない

    経緯: Issue #2618
    """
    table = create_mov_vars_link_table(dummy_db, [
        create_link_row('link-none-mv', None, VAR, ATTR_STD),
        create_link_row('link-none-name', MOVEMENT, None, ATTR_STD),
    ])

    table.register_and_discard(create_mov_vars_dict({None: [(VAR, ATTR_STD)], MOVEMENT: [(None, ATTR_LIST)]}))

    type_update, restore, discard = _update_payloads(dummy_db)
    assert type_update == [{'MVMT_VAR_LINK_ID': 'link-none-name', 'VARS_ATTRIBUTE_01': ATTR_LIST, 'LAST_UPDATE_USER': TEST_USER_ID}]
    assert (restore, discard) == ([], [])
