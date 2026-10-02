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

"""展開処理の親探しと展開の境界を確認する

展開処理は、多段変数メンバー管理の行を親子の木に組み、変数ネスト管理の繰返数で多段変数配列組合せ管理の代入欄の候補を作る処理（メニューではない）。
多段変数メンバー管理の行は階層の昇順に並べ、要素を「親変数ID-定義順」の名札で控え（先勝ち）、子は「親変数ID-親メンバー」で親を引く。
入力は多段変数メンバー管理の再読込結果（有効行の辞書）と変数ネスト管理の行の辞書。

経緯: Issue #3072
"""
import pytest

from backyard_libs.ansible_driver.functions import util
from tests.common import create_chain_array_item, create_member_row, create_max_col_row


LINK_ID = 'link-1'


def _member(member_id, vars_key_id, vars_name, parent='0', level='1', disp='1', link_id=LINK_ID, disuse_flag='0'):
    item = create_chain_array_item(vars_key_id=vars_key_id, vars_name=vars_name, parent_vars_key_id=parent,
                                   array_nest_level=level, member_disp=disp)
    return create_member_row(member_id, link_id, item, disuse_flag)


def _array(member_id, vars_key_id, parent='0', level='1', link_id=LINK_ID, disuse_flag='0'):
    return _member(member_id, vars_key_id, '0', parent=parent, level=level, disp='0', link_id=link_id, disuse_flag=disuse_flag)


def _records(*rows):
    records = {}
    for row in rows:
        records[row['ARRAY_MEMBER_ID']] = row
    return records


def _max_cols(*specs):
    """(配列階層の行 ID, 繰返数[, 親変数 ID]) から変数ネスト管理の辞書を組む"""
    records = {}
    for idx, spec in enumerate(specs):
        link_id = spec[2] if len(spec) > 2 else LINK_ID
        row = create_max_col_row(f"mc-{idx}", link_id, spec[0], spec[1])
        records[row['MAX_COL_SEQ_ID']] = row
    return records


def _aliases(result):
    aliases = []
    for record in result:
        aliases.append(record['COL_COMBINATION_MEMBER_ALIAS'])
    return aliases


def test_orphan_member_is_treated_as_root(mock_g):
    """親メンバーが指す行が存在しないメンバーは根として扱われ、その欄は作られる（例外にならない）

    経緯: Issue #3072
    """
    result = util.expand_vars_member(_records(_member('m-1', '5', 'lonely', parent='99', level='2')), {})

    assert _aliases(result) == ['lonely']


def test_duplicate_roots_first_takes_children(mock_g):
    """名札が同じ根（配列階層）が 2 行あり繰返数が違うとき、先に処理された根に子が付く（後勝ちだと欄の数が変わる）

    経緯: Issue #3072
    """
    records = _records(
        _array('root-a', '1'),
        _array('root-b', '1'),
        _member('leaf', '2', 'x', parent='1', level='2'),
    )
    result = util.expand_vars_member(records, _max_cols(('root-a', 2), ('root-b', 5)))

    assert _aliases(result) == ['[0].x', '[1].x']


def test_variables_do_not_mix(mock_g):
    """別の親変数（別の Movement-変数紐付の行）に同じ定義順のメンバーがあっても、木が混ざらず欄はそれぞれの変数に付く

    経緯: Issue #3072
    """
    records = _records(
        _array('a-root', '1', link_id='link-a'),
        _member('a-leaf', '2', 'x', parent='1', level='2', link_id='link-a'),
        _array('b-root', '1', link_id='link-b'),
        _member('b-leaf', '2', 'y', parent='1', level='2', link_id='link-b'),
    )
    result = util.expand_vars_member(records, _max_cols(('a-root', 1, 'link-a'), ('b-root', 2, 'link-b')))

    by_link = {}
    for record in result:
        by_link.setdefault(record['MVMT_VAR_LINK_ID'], []).append(record['COL_COMBINATION_MEMBER_ALIAS'])
    assert by_link == {'link-a': ['[0].x'], 'link-b': ['[0].y', '[1].y']}


@pytest.mark.parametrize('levels, repeats, expected_count', [
    pytest.param(1, (2,), 2, id='one_level'),
    pytest.param(2, (2, 3), 6, id='two_levels'),
    pytest.param(3, (2, 3, 4), 24, id='three_levels'),
])
def test_fields_multiply_by_repeat_counts(mock_g, levels, repeats, expected_count):
    """配列階層が 1〜3 段のとき、末端メンバーの欄の数は各段の繰返数の掛け算になる

    経緯: Issue #3072
    """
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

    result = util.expand_vars_member(_records(*rows), _max_cols(*max_col_specs))

    assert len(result) == expected_count
    assert len(set(_aliases(result))) == expected_count


def test_parent_at_same_or_deeper_level_leaves_both_as_roots(mock_g):
    """親の階層番号が子と同じか大きい（データ不整合）と、子が先に処理されて親を見つけられず、親も子も根として扱われる

    経緯: Issue #3072
    """
    records = _records(
        _member('child', '2', 'child', parent='1', level='1'),
        _member('parent', '1', 'parent', parent='0', level='2'),
    )
    result = util.expand_vars_member(records, {})

    assert _aliases(result) == ['child', 'parent']


def test_skipped_level_still_links_to_parent(mock_g):
    """階層が飛んでいても（階層 1 の配列の直下に階層 3 のメンバー）、親メンバーの指す要素に紐付く

    経緯: Issue #3072
    """
    records = _records(
        _array('root', '1'),
        _member('leaf', '2', 'x', parent='1', level='3'),
    )
    result = util.expand_vars_member(records, _max_cols(('root', 2)))

    assert _aliases(result) == ['[0].x', '[1].x']


def test_duplicate_rows_under_same_parent_first_becomes_parent(mock_g):
    """名札が同じ行が同じ階層・同じ親の下に 2 つあると（多段変数メンバー管理に同じメンバーの重複行が残っている場合）、先に生成された方だけが子を持ち、欄は 1 組だけ出る

    経緯: Issue #3072
    """
    records = _records(
        _array('root', '1'),
        _member('grp-a', '2', 'grp', parent='1', level='2', disp='0'),
        _member('grp-b', '2', 'grp', parent='1', level='2', disp='0'),
        _member('leaf', '3', 'leaf', parent='2', level='3'),
    )
    result = util.expand_vars_member(records, _max_cols(('root', 1)))

    assert _aliases(result) == ['[0].grp.leaf']


@pytest.mark.parametrize('rows, expected_alias', [
    pytest.param([
        _array('root', '1'),
        _member('shallow', '2', 'a', parent='1', level='2', disp='0'),
        _member('deep', '2', 'b', parent='1', level='3', disp='0'),
        _member('leaf', '3', 'leaf', parent='2', level='4'),
    ], '[0].a.leaf', id='other_level'),
    pytest.param([
        _array('root', '1'),
        _member('g1', '2', 'g1', parent='1', level='2', disp='0'),
        _member('g2', '3', 'g2', parent='1', level='2', disp='0'),
        _member('under-g2', '4', 'y', parent='3', level='3', disp='0'),
        _member('under-g1', '4', 'x', parent='2', level='3', disp='0'),
        _member('leaf', '5', 'leaf', parent='4', level='4'),
    ], '[0].g2.y.leaf', id='other_parent'),
    pytest.param([
        _array('root', '1'),
        _member('second-root', '9', 'r2', parent='0', level='1', disp='0'),
        _member('under-r2', '4', 'b', parent='9', level='2', disp='0'),
        _member('under-root', '4', 'a', parent='1', level='2', disp='0'),
        _member('leaf', '5', 'leaf', parent='4', level='3'),
    ], 'r2.b.leaf', id='other_tree'),
])
def test_colliding_labels_pick_first_generated(mock_g, rows, expected_alias):
    """名札が別の階層・別の親・別の木で衝突したとき、子は「先に生成された（階層が浅い、または読込順が先の）要素」に付く

    製品の処理経路ではこの形は作れない（有効行の定義順は通し番号で一意）。展開処理単体の振る舞いとして改修後の挙動を固定する。
    経緯: Issue #3072（改修後の挙動を固定）
    """
    result = util.expand_vars_member(_records(*rows), _max_cols(('root', 1)))

    assert _aliases(result) == [expected_alias]


def test_discarded_parent_yields_no_fields(mock_g):
    """親が廃止行だと（製品経路では届かないが）親ごと欄は作られず、有効な子の欄だけが出ることもない

    経緯: Issue #3072
    """
    records = _records(
        _array('root', '1', disuse_flag='1'),
        _member('leaf', '2', 'x', parent='1', level='2'),
    )
    result = util.expand_vars_member(records, _max_cols(('root', 2)))

    assert result == []


def test_mixed_level_types_raise_type_error(mock_g):
    """階層番号が数値と文字列で混在していると並べ替えで停止する（改修前も同じ）

    経緯: Issue #3072
    """
    records = _records(
        _member('a', '1', 'a', level=1),
        _member('b', '2', 'b', level='2'),
    )

    with pytest.raises(TypeError):
        util.expand_vars_member(records, {})


def test_array_level_without_repeat_row_yields_no_fields(mock_g):
    """配列階層の行に対応する変数ネスト管理の行が無い（変数ネスト管理で廃止済み）と、繰返数 0 で欄は作られない

    経緯: Issue #3072
    """
    records = _records(
        _array('root', '1'),
        _member('leaf', '2', 'x', parent='1', level='2'),
    )
    result = util.expand_vars_member(records, {})

    assert result == []


def test_none_order_label_still_links_children(mock_g):
    """定義順が欠損（None）の行でも名札「親変数ID-None」が作られ、親メンバー None を指す子はそこに付く

    経緯: Issue #3072
    """
    records = _records(
        _member('root', None, 'r', parent='0', level='1', disp='0'),
        _member('leaf', '2', 'child', parent=None, level='2'),
    )
    result = util.expand_vars_member(records, {})

    assert _aliases(result) == ['r.child']


def test_hidden_member_yields_no_field(mock_g):
    """表示有無が 0 のメンバーは欄を作らず、その配下だけが欄になる。廃止行のメンバーも欄を作らない

    経緯: Issue #3072
    """
    records = _records(
        _array('root', '1'),
        _member('hidden', '2', 'hidden', parent='1', level='2', disp='0'),
        _member('shown', '3', 'shown', parent='1', level='2'),
        _member('gone', '4', 'gone', parent='1', level='2', disuse_flag='1'),
    )
    result = util.expand_vars_member(records, _max_cols(('root', 1)))

    assert _aliases(result) == ['[0].shown']
