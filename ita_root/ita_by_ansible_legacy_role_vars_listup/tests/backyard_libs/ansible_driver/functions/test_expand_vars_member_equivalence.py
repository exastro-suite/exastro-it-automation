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

"""展開処理の結果が、改修前の実装と同じになることを確認する（等価性）

展開処理は、多段変数メンバー管理の行を親子の木に組み、変数ネスト管理の繰返数で多段変数配列組合せ管理の代入欄の候補を作る処理（メニューではない）。
#3072 は親探しを「根から木を掘る総当たり」から「生成済み要素を名札で引く」方式に変えた「結果を変えない」修正。
改修前の実装の結果は、移行時に 1 回だけ書き出した期待値ファイル（expected_expand_vars_member.py）に入力と一緒に記録してある。
同じ多段変数メンバー管理・変数ネスト管理の行を改修後の製品コードに渡し、候補行の一覧を順序込みで期待値と一致比較する。
名札が別階層・別親・別の木で衝突する形は製品経路で作れず改修前後で異なるため含めない（展開処理単体の振る舞いは test_expand_vars_member.py で固定）。

経緯: Issue #3072
"""
import copy

import pytest

from backyard_libs.ansible_driver.functions import util
from tests.backyard_libs.ansible_driver.functions.expected_expand_vars_member import get_expected
from tests.common import (
    create_chain_array_item, create_member_row, create_max_col_row, create_chain_array_from_yaml, create_member_rows_from_chain_array,
)


LINK_ID = 'link-1'

SERVERS_WITH_OS_YAML = """
VAR_servers:
  - name: web01
    os: linux
    ports:
      - http: 80
"""


def _member(member_id, vars_key_id, vars_name, parent='0', level='1', disp='1', link_id=LINK_ID, disuse_flag='0'):
    item = create_chain_array_item(vars_key_id=vars_key_id, vars_name=vars_name, parent_vars_key_id=parent,
                                   array_nest_level=level, member_disp=disp)
    return create_member_row(member_id, link_id, item, disuse_flag)


def _array(member_id, vars_key_id, parent='0', level='1', link_id=LINK_ID, disuse_flag='0'):
    return _member(member_id, vars_key_id, '0', parent=parent, level=level, disp='0', link_id=link_id, disuse_flag=disuse_flag)


def _records(rows):
    records = {}
    for row in rows:
        records[row['ARRAY_MEMBER_ID']] = row
    return records


def _max_cols(*specs):
    records = {}
    for idx, spec in enumerate(specs):
        link_id = spec[2] if len(spec) > 2 else LINK_ID
        row = create_max_col_row(f"mc-{idx}", link_id, spec[0], spec[1])
        records[row['MAX_COL_SEQ_ID']] = row
    return records


def _levels(levels, repeats):
    rows = []
    max_col_specs = []
    parent = '0'
    key = 0
    for depth in range(levels):
        key += 1
        rows.append(_array(f"arr-{depth}", str(key), parent=parent, level=str(depth * 2 + 1)))
        max_col_specs.append((f"arr-{depth}", repeats[depth]))
        parent = str(key)
        if depth < levels - 1:
            key += 1
            rows.append(_member(f"grp-{depth}", str(key), 'items', parent=parent, level=str(depth * 2 + 2), disp='0'))
            parent = str(key)
    key += 1
    rows.append(_member('leaf', str(key), 'value', parent=parent, level=str(levels * 2)))
    return _records(rows), _max_cols(*max_col_specs)


def _from_yaml(yaml_text, repeat_by_path):
    """YAML → 多段変数メンバー管理の行（DB 型）と、配列階層ごとの変数ネスト管理の行（repeat_by_path: {階層パス: 繰返数}）"""
    _, chain_array, _ = create_chain_array_from_yaml(yaml_text)
    rows = create_member_rows_from_chain_array(LINK_ID, chain_array)
    max_col_specs = []
    for row in rows:
        if row['VARS_NAME'] == '0':
            max_col_specs.append((row['ARRAY_MEMBER_ID'], repeat_by_path.get(row['VRAS_NAME_PATH'], 1)))
    return _records(rows), _max_cols(*max_col_specs)


SCENARIOS = {
    'orphan': lambda: (_records([_member('m-1', '5', 'lonely', parent='99', level='2')]), {}),
    'parent_deeper': lambda: (_records([
        _member('child', '2', 'child', parent='1', level='1'),
        _member('parent', '1', 'parent', parent='0', level='2'),
    ]), {}),
    'skipped_level': lambda: (_records([_array('root', '1'), _member('leaf', '2', 'x', parent='1', level='3')]), _max_cols(('root', 2))),
    'dup_same_parent': lambda: (_records([
        _array('root', '1'),
        _member('grp-a', '2', 'grp', parent='1', level='2', disp='0'),
        _member('grp-b', '2', 'grp', parent='1', level='2', disp='0'),
        _member('leaf', '3', 'leaf', parent='2', level='3'),
    ]), _max_cols(('root', 1))),
    'dup_roots': lambda: (_records([
        _array('root-a', '1'),
        _array('root-b', '1'),
        _member('leaf', '2', 'x', parent='1', level='2'),
    ]), _max_cols(('root-a', 2), ('root-b', 5))),
    'discarded_parent': lambda: (_records([
        _array('root', '1', disuse_flag='1'),
        _member('leaf', '2', 'x', parent='1', level='2'),
    ]), _max_cols(('root', 2))),
    'two_links': lambda: (_records([
        _array('a-root', '1', link_id='link-a'),
        _member('a-leaf', '2', 'x', parent='1', level='2', link_id='link-a'),
        _array('b-root', '1', link_id='link-b'),
        _member('b-leaf', '2', 'y', parent='1', level='2', link_id='link-b'),
    ]), _max_cols(('a-root', 1, 'link-a'), ('b-root', 2, 'link-b'))),
    'no_max_col_row': lambda: (_records([_array('root', '1'), _member('leaf', '2', 'x', parent='1', level='2')]), {}),
    'none_order': lambda: (_records([
        _member('root', None, 'r', parent='0', level='1', disp='0'),
        _member('leaf', '2', 'child', parent=None, level='2'),
    ]), {}),
    'hidden_and_discarded': lambda: (_records([
        _array('root', '1'),
        _member('hidden', '2', 'hidden', parent='1', level='2', disp='0'),
        _member('shown', '3', 'shown', parent='1', level='2'),
        _member('gone', '4', 'gone', parent='1', level='2', disuse_flag='1'),
    ]), _max_cols(('root', 1))),
    'level1': lambda: _levels(1, (2,)),
    'level2': lambda: _levels(2, (2, 3)),
    'level3': lambda: _levels(3, (2, 3, 4)),
    'insert_upper_member_after': lambda: _from_yaml(SERVERS_WITH_OS_YAML, {'0': 2, '0.ports.0': 3}),
}


@pytest.mark.parametrize('scenario', sorted(SCENARIOS.keys()))
def test_expansion_equals_previous_implementation(mock_g, scenario):
    """同じ多段変数メンバー管理・変数ネスト管理の行を渡したとき、多段変数配列組合せ管理の欄の候補（表示名・列順序・対象メンバー）の一覧が順序まで含めて改修前の実装と一致する

    経緯: Issue #3072
    """
    records, max_cols = SCENARIOS[scenario]()
    expected = get_expected(scenario)
    # 今作った入力が期待値ファイルに記録した入力と同じか（入力を作るヘルパーが変わったら、期待値が古いと分かる）
    given = {'nest_vars_mem_records': records, 'mem_max_col_records': max_cols}
    assert given == expected['input'], f"input differs from the expected file: {scenario}"

    current = util.expand_vars_member(copy.deepcopy(records), copy.deepcopy(max_cols))
    previous = expected['result']

    assert current == previous
    if scenario not in ('discarded_parent', 'no_max_col_row'):
        assert len(current) > 0
