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

"""多段変数メンバー管理の突き合わせ（登録・復活・廃止の 3 リスト）が、改修前の実装と同じ結果になることを確認する（等価性）

#3072 は総当たり比較を辞書引きに変えた「結果を変えない」修正。同じ入力を改修前の実装の写し（tests/legacy_impl）と
改修後の製品コードに渡し、3 リストを順序・重複・定義順の取り込みまで含めて一致比較する。
同一性キーの境界（表4 E）と、メンバー差分の業務シナリオ（表3 K）の両方を入力にする。

例外は「親メンバー（親の定義順）」だけが違うシナリオ。#3096 で親メンバーを同一性キーから外したため、
改修前の実装（廃止＋登録）と改修後（同じ行のまま親メンバーを更新）で結果が意図的に変わる。
その 6 シナリオは PARENT_ORDER_SCENARIOS に分け、差分の形を専用テストで固定する。

経緯: Issue #3072
"""
import copy

import pytest

from backyard_libs.ansible_driver.classes.NestVarsMemberTableClass import NestVarsMemberTable
from tests.legacy_impl.nest_vars_member_compare import LegacyNestVarsMemberCompare
from tests.common import (
    create_chain_array_item, create_member_row, create_chain_array_from_yaml, create_member_rows_from_chain_array,
)


LINK_ID = 'link-1'

SERVERS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
"""
SERVERS_WITH_OS_YAML = """
VAR_servers:
  - name: web01
    os: linux
    ports:
      - http: 80
"""
SERVERS_WITH_ZONE_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
    zone: tokyo
"""
SERVERS_SWAPPED_YAML = """
VAR_servers:
  - ports:
      - http: 80
    name: web01
"""
SERVERS_WITH_TAGS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
    tags:
      - env: prod
"""
SERVERS_WITH_TAGS_AND_HTTPS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
        https: 443
    tags:
      - env: prod
"""


def _item(vars_key_id='1', vars_name='member', **overrides):
    item = create_chain_array_item(vars_key_id=vars_key_id, vars_name=vars_name)
    for column, value in overrides.items():
        assert column in item, f"unknown column {column}"
        item[column] = value
    item['MVMT_VAR_LINK_ID'] = LINK_ID      # 反映処理が解析結果に付ける親変数 ID
    return item


def _stored(member_id, item, disuse_flag='0'):
    row = create_member_row(member_id, LINK_ID, item, disuse_flag)
    return row


def _yaml_stored(yaml_text):
    _, chain_array, _ = create_chain_array_from_yaml(yaml_text)
    return create_member_rows_from_chain_array(LINK_ID, chain_array)


def _yaml_extracted(yaml_text):
    _, chain_array, _ = create_chain_array_from_yaml(yaml_text)
    records = []
    for item in chain_array:
        record = dict(item)
        record['MVMT_VAR_LINK_ID'] = LINK_ID
        records.append(record)
    return records


def _attr_changed(column):
    """既存行の 1 項目だけ違う"""
    stored = _yaml_stored(SERVERS_YAML)
    target = stored[-1]
    if column == 'MVMT_VAR_LINK_ID':
        target[column] = 'link-other'
    elif column in ('VARS_NAME', 'VRAS_NAME_PATH', 'VRAS_NAME_ALIAS'):
        target[column] = str(target[column]) + '_old'
    else:
        target[column] = int(target[column]) + 10
    return stored, _yaml_extracted(SERVERS_YAML)


def _int_str(column):
    stored_item = _item()
    stored_item[column] = 7
    extracted_item = _item()
    extracted_item[column] = '7'
    return [_stored('m-1', stored_item)], [extracted_item]


def _order_changed():
    stored = _yaml_stored(SERVERS_YAML)
    stored[1]['VARS_KEY_ID'] = 9
    return stored, _yaml_extracted(SERVERS_YAML)


SCENARIOS = {
    # 表4 E: 同一性キーの境界
    'none_vs_string_none': lambda: ([_stored('m-1', _item(VRAS_NAME_ALIAS=None))], [_item(VRAS_NAME_ALIAS='None')]),
    'none_vs_empty': lambda: ([_stored('m-1', _item(VRAS_NAME_ALIAS=None))], [_item(VRAS_NAME_ALIAS='')]),
    'int_str_level': lambda: _int_str('ARRAY_NEST_LEVEL'),
    'int_str_assign_seq': lambda: _int_str('ASSIGN_SEQ_NEED'),
    'int_str_col_seq': lambda: _int_str('COL_SEQ_NEED'),
    'int_str_disp': lambda: _int_str('MEMBER_DISP'),
    'int_str_max_col': lambda: _int_str('MAX_COL_SEQ'),
    'case': lambda: ([_stored('m-1', _item(vars_name='Name'))], [_item(vars_name='name')]),
    'trailing_space': lambda: ([_stored('m-1', _item(vars_name='name '))], [_item(vars_name='name')]),
    'bool_vs_str': lambda: ([_stored('m-1', _item(MEMBER_DISP=False))], [_item(MEMBER_DISP='0')]),
    'stored_dup2_extracted1': lambda: ([_stored('m-1', _item(vars_key_id='1')), _stored('m-2', _item(vars_key_id='7'))], [_item(vars_key_id='3')]),
    'extracted_dup_first_wins': lambda: ([_stored('m-1', _item(vars_key_id='1'))], [_item(vars_key_id='5'), _item(vars_key_id='6')]),
    'extracted_dup_reversed': lambda: ([_stored('m-1', _item(vars_key_id='1'))], [_item(vars_key_id='6'), _item(vars_key_id='5')]),
    'extracted_dup_register': lambda: ([], [_item(vars_key_id='5'), _item(vars_key_id='6')]),
    'stored_dup_discard': lambda: ([_stored('m-1', _item()), _stored('m-2', _item(vars_key_id='7'))], []),
    'register_all': lambda: ([], [_item('1', 'a'), _item('2', 'b'), _item('3', 'c')]),
    'discard_all': lambda: ([_stored('m-1', _item('1', 'a')), _stored('m-2', _item('2', 'b'))], []),
    'both_empty': lambda: ([], []),
    'mixed_order_and_duplicates': lambda: (
        [_stored('m-3', _item('1', 'c')), _stored('m-1', _item('2', 'a')), _stored('m-2', _item('3', 'a'))],
        [_item('1', 'z'), _item('2', 'y'), _item('3', 'y')]),
    # 表3 K: メンバー差分の業務シナリオ（YAML を本物の解析器に通す）
    'order_change': _order_changed,
    'attr_link_id': lambda: _attr_changed('MVMT_VAR_LINK_ID'),
    'attr_name': lambda: _attr_changed('VARS_NAME'),
    'attr_level': lambda: _attr_changed('ARRAY_NEST_LEVEL'),
    'attr_assign_seq': lambda: _attr_changed('ASSIGN_SEQ_NEED'),
    'attr_col_seq': lambda: _attr_changed('COL_SEQ_NEED'),
    'attr_disp': lambda: _attr_changed('MEMBER_DISP'),
    'attr_path': lambda: _attr_changed('VRAS_NAME_PATH'),
    'attr_alias': lambda: _attr_changed('VRAS_NAME_ALIAS'),
    'attr_max_col': lambda: _attr_changed('MAX_COL_SEQ'),
    'added_member': lambda: (_yaml_stored(SERVERS_YAML), _yaml_extracted(SERVERS_WITH_ZONE_YAML)),
    'removed_member': lambda: (_yaml_stored(SERVERS_WITH_ZONE_YAML), _yaml_extracted(SERVERS_YAML)),
    'unchanged': lambda: (_yaml_stored(SERVERS_YAML), _yaml_extracted(SERVERS_YAML)),
}

# 親メンバー（親の定義順）だけが既存行と違うシナリオ。改修前の実装と結果が意図的に変わるのはこの 6 つだけ
PARENT_ORDER_SCENARIOS = {
    'int_str_parent': lambda: _int_str('PARENT_VARS_KEY_ID'),                                                    # 型だけ違う
    'attr_parent': lambda: _attr_changed('PARENT_VARS_KEY_ID'),                                                  # 値が違う
    'insert_upper_member': lambda: (_yaml_stored(SERVERS_YAML), _yaml_extracted(SERVERS_WITH_OS_YAML)),        # 上位への挿入
    'remove_upper_member': lambda: (_yaml_stored(SERVERS_WITH_OS_YAML), _yaml_extracted(SERVERS_YAML)),        # 上位の削除
    'add_inner_member': lambda: (_yaml_stored(SERVERS_WITH_TAGS_YAML), _yaml_extracted(SERVERS_WITH_TAGS_AND_HTTPS_YAML)),  # 内側ブロックへの追加
    'swap_siblings': lambda: (_yaml_stored(SERVERS_YAML), _yaml_extracted(SERVERS_SWAPPED_YAML)),              # 兄弟の入れ替え
}


def _scenario(name):
    if name in SCENARIOS:
        return SCENARIOS[name]()
    return PARENT_ORDER_SCENARIOS[name]()


def _paths(records):
    paths = []
    for record in records:
        paths.append(str(record['VRAS_NAME_PATH']))
    return sorted(paths)


def _member_ids(records):
    ids = []
    for record in records:
        ids.append(record['ARRAY_MEMBER_ID'])
    return sorted(ids)


def _record_by_path(records, path):
    for record in records:
        if str(record['VRAS_NAME_PATH']) == str(path):
            return record
    raise AssertionError(f"no record for path {path}")


def _parent_as_str(record):
    """親メンバーだけ文字列化した辞書（型の違いを無視して他の全列を比べるため）"""
    result = {}
    for column, value in record.items():
        if column == 'PARENT_VARS_KEY_ID':
            result[column] = str(value)
        else:
            result[column] = value
    return result


def _current_lists(dummy_db, stored, extracted, ignore_vars_key_id=True):
    """改修後の製品コードで 登録・復活・廃止 の 3 リストを作る（NestVarsMemberTable.register_and_discard と同じ組み立て）"""
    table = NestVarsMemberTable(dummy_db)
    keyed_stored = table._keyed_records(stored, ignore_vars_key_id)
    keyed_extracted = table._keyed_records(extracted, ignore_vars_key_id)
    stored_by_key = table._index_by_record_key(keyed_stored)
    extracted_by_key = table._index_by_record_key(keyed_extracted)
    register = table._a_minus_b(keyed_a=keyed_extracted, index_b=stored_by_key)
    restore = table._a_and_b(keyed_a=keyed_stored, index_b=extracted_by_key, marge_vars_key_id=True)
    discard = table._a_minus_b(keyed_a=keyed_stored, index_b=extracted_by_key)
    return register, restore, discard


def _legacy_lists(stored, extracted, ignore_vars_key_id=True):
    """改修前の実装（写し）で同じ 3 リストを作る"""
    legacy = LegacyNestVarsMemberCompare()
    register = legacy._a_minus_b(list_a=extracted, list_b=stored, ignore_vars_key_id=ignore_vars_key_id)
    restore = legacy._a_and_b(stored, extracted, ignore_vars_key_id=ignore_vars_key_id, marge_vars_key_id=True)
    discard = legacy._a_minus_b(list_a=stored, list_b=extracted, ignore_vars_key_id=ignore_vars_key_id)
    return register, restore, discard


@pytest.mark.parametrize('scenario', sorted(SCENARIOS.keys()))
def test_matching_equals_previous_implementation(mock_g, dummy_db, scenario):
    """同じ既存行・解析結果を渡したとき、登録・復活（定義順の取り込み込み）・廃止の 3 リストが改修前の実装と一致する

    親メンバーだけが違うシナリオは意図的に結果が変わるので対象外（test_parent_order_scenarios_update_instead_of_reregistering）。
    経緯: Issue #3072
    """
    stored, extracted = SCENARIOS[scenario]()

    current = _current_lists(dummy_db, copy.deepcopy(stored), copy.deepcopy(extracted))
    legacy = _legacy_lists(copy.deepcopy(stored), copy.deepcopy(extracted))

    assert current == legacy


@pytest.mark.parametrize('scenario', sorted(PARENT_ORDER_SCENARIOS.keys()))
def test_parent_order_scenarios_update_instead_of_reregistering(mock_g, dummy_db, scenario):
    """親メンバー（親の定義順）だけが違う既存行は、改修前の実装では廃止＋登録だったが、改修後は同じ行のまま復活側に入り親メンバーが更新される

    改修前の実装との差はこの 6 シナリオに限られる（他の全シナリオは test_matching_equals_previous_implementation で一致を確認）。
    - 改修後: 登録は Playbook に新しく増えたメンバー（os / https）だけ、廃止は Playbook から消えたメンバー（remove_upper_member の os）だけ。
      Playbook に残っている既存行は全件が同じ行のまま復活側に入り、親メンバーは同じ階層パスの解析結果の値になる
    - 改修前: 親メンバーの値が違う行は登録側と廃止側に同じ階層パスで現れ、復活側には残らない。
      型だけ違う（int_str_parent）場合は改修前も一致するが、親メンバーの取り込みが無いので数値のまま残る
    復活側に両方残った行は、親メンバー以外の全列が改修前と同じ。
    経緯: Issue #3072 / #3096（親メンバーを同一性キーから外し、新挙動を固定）
    """
    stored, extracted = PARENT_ORDER_SCENARIOS[scenario]()

    current_register, current_restore, current_discard = _current_lists(dummy_db, copy.deepcopy(stored), copy.deepcopy(extracted))
    legacy_register, legacy_restore, legacy_discard = _legacy_lists(copy.deepcopy(stored), copy.deepcopy(extracted))

    new_paths = sorted(set(_paths(extracted)) - set(_paths(stored)))      # Playbook に増えたメンバー
    gone_paths = sorted(set(_paths(stored)) - set(_paths(extracted)))     # Playbook から消えたメンバー
    kept_ids = []
    for record in stored:
        if str(record['VRAS_NAME_PATH']) not in gone_paths:
            kept_ids.append(record['ARRAY_MEMBER_ID'])

    # 改修後: 登録は増えたメンバーだけ、廃止は消えたメンバーだけ。残った既存行は全件が復活側で、親メンバーは解析結果の値
    assert _paths(current_register) == new_paths
    assert _paths(current_discard) == gone_paths
    assert _member_ids(current_restore) == sorted(kept_ids)
    for record in current_restore:
        assert record['PARENT_VARS_KEY_ID'] == _record_by_path(extracted, record['VRAS_NAME_PATH'])['PARENT_VARS_KEY_ID']

    # 改修前: 消えたメンバーの廃止は同じ。親メンバーが違う行はさらに同じ階層パスで廃止＋登録になり、復活側に残らない
    legacy_reregistered_paths = []
    for path in _paths(legacy_discard):
        if path not in gone_paths:
            legacy_reregistered_paths.append(path)
    assert _paths(legacy_register) == sorted(new_paths + legacy_reregistered_paths)
    assert len(legacy_restore) + len(legacy_discard) == len(stored)
    legacy_restore_ids = _member_ids(legacy_restore)
    for record in current_restore:
        if record['ARRAY_MEMBER_ID'] in legacy_restore_ids:
            legacy_record = _record_by_path(legacy_restore, record['VRAS_NAME_PATH'])
            assert _parent_as_str(record) == _parent_as_str(legacy_record)
        else:
            assert str(record['VRAS_NAME_PATH']) in legacy_reregistered_paths
    if scenario == 'int_str_parent':
        assert legacy_reregistered_paths == []
    else:
        assert len(legacy_reregistered_paths) > 0
    # このシナリオ群は「改修前と結果が変わる」ものだけ。変わらないものが混ざれば SCENARIOS 側へ移す
    assert (current_register, current_restore, current_discard) != (legacy_register, legacy_restore, legacy_discard)


@pytest.mark.parametrize('scenario', ['order_change', 'insert_upper_member', 'extracted_dup_first_wins', 'unchanged'])
def test_order_aware_matching_equals_previous_implementation(mock_g, dummy_db, scenario):
    """定義順まで比較する照合方式（現在どこからも呼ばれない）でも、3 リストが改修前の実装と一致する

    経緯: Issue #3072
    """
    stored, extracted = _scenario(scenario)

    current = _current_lists(dummy_db, copy.deepcopy(stored), copy.deepcopy(extracted), ignore_vars_key_id=False)
    legacy = _legacy_lists(copy.deepcopy(stored), copy.deepcopy(extracted), ignore_vars_key_id=False)

    assert current == legacy
