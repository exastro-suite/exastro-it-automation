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

"""多段変数メンバの突き合わせ処理を高速化した際の「出力が変わらないこと」を固定するテスト

総当たり比較（O(N^2)）を辞書引きに置き換える改修は「速くなること」ではなく
**改修前と改修後で出力が完全に一致すること**が本質なので、
改修前の実装が出した結果を比較の基準として現行実装と突き合わせる。

- 改修前の実装の結果は、移行時に 1 回だけ書き出した期待値ファイル（expected_nest_vars_member_table.py）に
  入力と一緒に記録してある。**製品側を直しても期待値を追随させてはいけない**（追随させると比較の基準としての意味が無くなる）。
  プロダクト側の仕様を変える時に初めて更新する
- 期待値のキーは「テスト関数名から test_ を除いたもの（パラメータ付き）:呼んだ処理」。テスト関数名を変えたら期待値のキーも直す
- #3096 で製品側の同一性キーは `PARENT_VARS_KEY_ID` を外した 9 項目になり、一致行には `PARENT_VARS_KEY_ID` も
  取り込むようになった。期待値は **改修前（10 項目・親メンバーの取り込み無し）の結果のまま据え置く**。
  このモジュールのシナリオは親メンバーが両側で同じ値なので、据え置いたままでも一致する。
  親メンバーが違うシナリオの「意図した差分」は test_nest_vars_member_matching_equivalence.py 側で固定している
- 出力リストの順序は消費先に影響しないが（受け手が dict のキーに畳む / pkey 単位で独立）、
  改修前の実装と比較する分には順序込みで一致するのが自然なので順序も含めて比較している

経緯: Issue #3072
"""
import copy

import pytest

from backyard_libs.ansible_driver.classes.NestVarsMemberTableClass import NestVarsMemberTable
from backyard_libs.ansible_driver.functions import util

from tests.backyard_libs.ansible_driver.classes.expected_nest_vars_member_table import get_expected
from tests.common import (
    create_chain_array_item,
    create_member_row,
)

LINK_ID = "link-0001"
OTHER_LINK_ID = "link-0002"


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# テストデータ・比較ヘルパー
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def create_row(member_id, link_id=LINK_ID, **chain_array_kwargs):
    """T_ANSR_NESTVAR_MEMBER 相当の 1 行（ARRAY_MEMBER_ID で行を識別できるようにする）"""
    return create_member_row(member_id, link_id, create_chain_array_item(**chain_array_kwargs))


def pick_column(records, column_name):
    """レコードリストから 1 カラムだけ順序通りに取り出す"""
    values = []
    for record in records:
        values.append(record[column_name])

    return values


def to_plain_dicts(records):
    """レコードリストを素の dict のリストにする（値まで含めて比較するため）"""
    plain_records = []
    for record in records:
        plain_records.append(dict(record))

    return plain_records


def to_records_dict(rows):
    """行のリストを store_dbdata_in_memory と同じ { pkey: row } の形にする"""
    records = {}
    for row in rows:
        records[row['ARRAY_MEMBER_ID']] = row

    return records


def _expected_case(request, method_name, given):
    """期待値ファイルからこのテストのケースを読み、今作った入力が記録した入力と同じかを確かめてから改修前の結果を返す"""
    case = request.node.name[len('test_'):]
    expected = get_expected(f"{case}:{method_name}")
    assert given == expected['input'], f"input differs from the expected file: {case}:{method_name}"
    return expected['result']


def run_both(request, method_name, list_a, list_b, ignore_vars_key_id=True, **kwargs):
    """改修前の実装の結果（期待値ファイル）と、現行実装を同じ入力で走らせた結果を返す

    現行実装は同一性キーを事前に1回だけ計算する設計なので、
    list_a からキー付きリスト、list_b から索引を作ってから渡す（register_and_discard と同じ手順）。
    `ignore_vars_key_id` は改修前の実装では比較関数の引数、現行実装ではキー付けの引数だった。

    `marge_vars_key_id=True` は record_a を破壊的に書き換えるので、現行実装にはコピーを渡す。
    """
    options = {'ignore_vars_key_id': ignore_vars_key_id}
    for option_name, option_value in kwargs.items():
        options[option_name] = option_value
    expected_result = _expected_case(request, method_name, {'list_a': list_a, 'list_b': list_b, 'options': options})

    table = NestVarsMemberTable.__new__(NestVarsMemberTable)
    new_a, new_b = copy.deepcopy(list_a), copy.deepcopy(list_b)

    keyed_a = table._keyed_records(new_a, ignore_vars_key_id)
    index_b = table._index_by_record_key(table._keyed_records(new_b, ignore_vars_key_id))
    new_result = getattr(table, method_name)(keyed_a, index_b, **kwargs)

    return expected_result, new_result


def assert_same_output(expected_result, new_result):
    """選ばれたレコードが順序込み・値込みで一致すること"""
    assert len(new_result) == len(expected_result)
    assert pick_column(new_result, 'ARRAY_MEMBER_ID') == pick_column(expected_result, 'ARRAY_MEMBER_ID')
    assert to_plain_dicts(new_result) == to_plain_dicts(expected_result)


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# A. _a_minus_b / _a_and_b が 改修前の実装と一致する
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def test_a_minus_b_matches_legacy_when_a_has_extra_records(request):
    """登録パス相当：list_a にだけある行が選ばれる"""
    common = [create_row('m1', vars_key_id='1', vars_name='member1'),
              create_row('m2', vars_key_id='2', vars_name='member2')]
    only_a = [create_row('m3', vars_key_id='3', vars_name='member3'),
              create_row('m4', vars_key_id='4', vars_name='member4')]

    expected_result, new_result = run_both(request, '_a_minus_b', common + only_a, common)

    assert_same_output(expected_result, new_result)
    assert pick_column(new_result, 'VARS_NAME') == ['member3', 'member4']


def test_a_minus_b_matches_legacy_when_b_has_extra_records(request):
    """廃止パス相当：list_b にしかない行は結果に出ない"""
    common = [create_row('m1', vars_key_id='1', vars_name='member1')]
    only_b = [create_row('m9', vars_key_id='9', vars_name='member9')]

    expected_result, new_result = run_both(request, '_a_minus_b', common, common + only_b)

    assert_same_output(expected_result, new_result)
    assert new_result == []


def test_a_minus_b_matches_legacy_when_nothing_matches(request):
    """全件が差分になるケース（全件登録／全件廃止の事故を検出する）"""
    list_a = [create_row('m1', vars_key_id='1', vars_name='member1'),
              create_row('m2', vars_key_id='2', vars_name='member2')]
    list_b = [create_row('m8', vars_key_id='8', vars_name='other8')]

    expected_result, new_result = run_both(request, '_a_minus_b', list_a, list_b)

    assert_same_output(expected_result, new_result)
    assert len(new_result) == 2


def test_a_minus_b_keeps_duplicated_records_like_legacy(request):
    """list_a 側に重複がある場合、重複したまま出力される（現行と同じ）"""
    row = create_row('m1', vars_key_id='1', vars_name='member1')
    duplicated = create_row('m2', vars_key_id='1', vars_name='member1')

    expected_result, new_result = run_both(request, '_a_minus_b', [row, duplicated], [])

    assert_same_output(expected_result, new_result)
    assert len(new_result) == 2


def test_a_and_b_matches_legacy_for_intersection(request):
    """復活パス相当：両方にある行だけが選ばれる"""
    common = [create_row('m1', vars_key_id='1', vars_name='member1'),
              create_row('m2', vars_key_id='2', vars_name='member2')]
    only_a = [create_row('m3', vars_key_id='3', vars_name='member3')]
    only_b = [create_row('m9', vars_key_id='9', vars_name='member9')]

    expected_result, new_result = run_both(request, '_a_and_b', common + only_a, common + only_b)

    assert_same_output(expected_result, new_result)
    assert pick_column(new_result, 'VARS_NAME') == ['member1', 'member2']


def test_a_and_b_merges_same_vars_key_id_value_as_legacy(request):
    """marge_vars_key_id で **書き込まれる値**が 改修前の実装と一致する

    行の集合（id()）の比較では、書き込まれる値の違いは見えない。
    """
    stored = [create_row('m1', vars_key_id='1', vars_name='member1')]
    # VARS_KEY_ID は比較キーに入っていない（ignore_vars_key_id=True）ので、値が違っても同一行と判定される
    extracted = [create_row('x1', vars_key_id='7', vars_name='member1')]

    expected_result, new_result = run_both(request, '_a_and_b', stored, extracted, marge_vars_key_id=True)

    assert_same_output(expected_result, new_result)
    assert new_result[0]['VARS_KEY_ID'] == '7'


def test_a_and_b_merge_takes_first_match_like_legacy(request):
    """list_b に同一キーの行が複数ある場合、**先に現れた** record_b の VARS_KEY_ID を採用する

    dict への素の代入（後勝ち）にすると壊れる。setdefault（先勝ち）の回帰防止。
    """
    stored = [create_row('m1', vars_key_id='1', vars_name='member1')]
    extracted = [create_row('x1', vars_key_id='5', vars_name='member1'),
                 create_row('x2', vars_key_id='6', vars_name='member1')]

    expected_result, new_result = run_both(request, '_a_and_b', stored, extracted, marge_vars_key_id=True)

    assert_same_output(expected_result, new_result)
    assert new_result[0]['VARS_KEY_ID'] == '5'


def test_a_and_b_without_merge_does_not_touch_vars_key_id(request):
    """marge_vars_key_id=False なら VARS_KEY_ID は書き換わらない"""
    stored = [create_row('m1', vars_key_id='1', vars_name='member1')]
    extracted = [create_row('x1', vars_key_id='7', vars_name='member1')]

    expected_result, new_result = run_both(request, '_a_and_b', stored, extracted)

    assert_same_output(expected_result, new_result)
    assert new_result[0]['VARS_KEY_ID'] == '1'


@pytest.mark.parametrize('method_name', ['_a_minus_b', '_a_and_b'])
def test_matches_legacy_with_ignore_vars_key_id_false(method_name, request):
    """ignore_vars_key_id=False の経路（現状どこからも呼ばれていない）も一致する"""
    list_a = [create_row('m1', vars_key_id='1', vars_name='member1')]
    list_b = [create_row('x1', vars_key_id='7', vars_name='member1')]

    expected_result, new_result = run_both(request, method_name, list_a, list_b, ignore_vars_key_id=False)

    assert_same_output(expected_result, new_result)
    # VARS_KEY_ID が比較対象に入るので別レコード扱いになる
    assert len(new_result) == (1 if method_name == '_a_minus_b' else 0)


@pytest.mark.parametrize('stored_value, extracted_value', [
    (1, '1'),
    ('1', 1),
    (10, 10),
], ids=['db_int_vs_str', 'str_vs_db_int', 'both_int'])
def test_type_difference_is_absorbed_like_legacy(stored_value, extracted_value, request):
    """型ゆれ（DB由来の int と解析結果由来の str）を str() で吸収する

    タプルキーから str() を落とすと型違いで全件不一致 = 全件廃止＋全件登録の事故になる。
    """
    stored = [create_row('m1', vars_key_id='1', vars_name='member1', max_col_seq=stored_value)]
    extracted = [create_row('x1', vars_key_id='1', vars_name='member1', max_col_seq=extracted_value)]

    expected_minus, new_minus = run_both(request, '_a_minus_b', stored, extracted)
    expected_and, new_and = run_both(request, '_a_and_b', stored, extracted)

    assert_same_output(expected_minus, new_minus)
    assert_same_output(expected_and, new_and)
    # 同じレコードと見なされるので、差分なし・共通ありになる
    assert new_minus == []
    assert len(new_and) == 1


def test_missing_column_is_treated_as_none_like_legacy(request):
    """比較キーが欠けている行も .get() で None 扱いになり 改修前の実装と一致する"""
    full = create_row('m1', vars_key_id='1', vars_name='member1')
    lacking = create_row('x1', vars_key_id='1', vars_name='member1')
    del lacking['VRAS_NAME_ALIAS']

    expected_result, new_result = run_both(request, '_a_minus_b', [full], [lacking])

    assert_same_output(expected_result, new_result)
    assert len(new_result) == 1


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# B. util.expand_vars_member が 改修前の実装と一致する
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def create_nest_tree_records(link_ids=(LINK_ID,), member_names=('member1', 'member2'), max_col_seq=2):
    """「配列階層(level1) + メンバ変数(level2)」の木を link 単位で組み立てる

    Returns:
        (nest_vars_mem_records, mem_max_col_records)
    """
    nest_vars_mem_records = {}
    mem_max_col_records = {}

    for link_index, link_id in enumerate(link_ids):
        array_member_id = f"array-{link_index}"
        nest_vars_mem_records[array_member_id] = create_row(
            array_member_id, link_id=link_id, vars_key_id='1', vars_name='0',
            parent_vars_key_id='0', array_nest_level='1', member_disp='0')
        mem_max_col_records[array_member_id] = {
            'MVMT_VAR_LINK_ID': link_id,
            'ARRAY_MEMBER_ID': array_member_id,
            'MAX_COL_SEQ': max_col_seq,
        }

        for member_index, member_name in enumerate(member_names):
            member_id = f"member-{link_index}-{member_index}"
            nest_vars_mem_records[member_id] = create_row(
                member_id, link_id=link_id, vars_key_id=str(member_index + 2), vars_name=member_name,
                parent_vars_key_id='1', array_nest_level='2')

    return nest_vars_mem_records, mem_max_col_records


def canonical(records):
    """順序に依存しない比較のための正規化（受け手はタプルキーの dict に畳むので順序は無関係）"""
    comparable_keys = []
    for record in records:
        comparable_keys.append((record['MVMT_VAR_LINK_ID'], record['ARRAY_MEMBER_ID'],
                                record['COL_COMBINATION_MEMBER_ALIAS'], record['COL_SEQ_VALUE']))

    return sorted(comparable_keys)


def run_both_expand(request, nest_vars_mem_records, mem_max_col_records):
    """改修前の実装の結果（期待値ファイル）と、現行実装を同じ入力（独立したコピー）で走らせた結果を返す"""
    given = {'nest_vars_mem_records': nest_vars_mem_records, 'mem_max_col_records': mem_max_col_records}
    expected_result = _expected_case(request, 'expand_vars_member', given)
    new_result = util.expand_vars_member(
        copy.deepcopy(nest_vars_mem_records), copy.deepcopy(mem_max_col_records))

    return expected_result, new_result


def test_expand_vars_member_matches_legacy_for_two_levels(mock_g, request):
    """基本形（配列階層 + メンバ変数）で生成結果が一致する"""
    records, max_cols = create_nest_tree_records()

    expected_result, new_result = run_both_expand(request, records, max_cols)

    assert canonical(new_result) == canonical(expected_result)
    # メンバ2種 × 繰返2回
    assert len(new_result) == 4


def test_expand_vars_member_matches_legacy_for_multiple_links(mock_g, request):
    """複数の変数リンク（＝複数の木）があっても一致する"""
    records, max_cols = create_nest_tree_records(link_ids=(LINK_ID, OTHER_LINK_ID))

    expected_result, new_result = run_both_expand(request, records, max_cols)

    assert canonical(new_result) == canonical(expected_result)
    assert len(new_result) == 8


def test_expand_vars_member_matches_legacy_for_three_levels(mock_g, request):
    """3段ネスト（level3 が level2 を親に持つ）でも木の形が一致する

    NEST_LEVEL は解析結果から入るので 3 段以上にもなり得る。
    """
    array_row = create_row('array-0', vars_key_id='1', vars_name='0',
                           parent_vars_key_id='0', array_nest_level='1', member_disp='0')
    inner_array_row = create_row('array-1', vars_key_id='2', vars_name='0',
                                 parent_vars_key_id='1', array_nest_level='2', member_disp='0')
    leaf_row = create_row('leaf-0', vars_key_id='3', vars_name='member1',
                          parent_vars_key_id='2', array_nest_level='3')

    records = to_records_dict([array_row, inner_array_row, leaf_row])
    max_cols = {
        'array-0': {'MVMT_VAR_LINK_ID': LINK_ID, 'ARRAY_MEMBER_ID': 'array-0', 'MAX_COL_SEQ': 2},
        'array-1': {'MVMT_VAR_LINK_ID': LINK_ID, 'ARRAY_MEMBER_ID': 'array-1', 'MAX_COL_SEQ': 2},
    }

    expected_result, new_result = run_both_expand(request, records, max_cols)

    assert canonical(new_result) == canonical(expected_result)
    # 2 × 2 の組合せ
    assert len(new_result) == 4


def test_expand_vars_member_picks_first_element_on_own_key_collision(mock_g, request):
    """own_key（MVMT_VAR_LINK_ID + VARS_KEY_ID）が衝突しても、親は **先に生成された** 要素になる

    衝突する行が最下層にしか無いと後勝ちでも結果が一致してしまうので、上の階層で衝突させて先勝ちを確かめる。
    dict への素の代入（後勝ち）にすると壊れる回帰防止。
    """
    # level1 に own_key が衝突する配列階層を 2 つ作る（繰返数を変えて区別できるようにする）
    first_array = create_row('array-first', vars_key_id='1', vars_name='0',
                             parent_vars_key_id='0', array_nest_level='1', member_disp='0')
    second_array = create_row('array-second', vars_key_id='1', vars_name='0',
                              parent_vars_key_id='0', array_nest_level='1', member_disp='0')
    leaf_row = create_row('leaf-0', vars_key_id='2', vars_name='member1',
                          parent_vars_key_id='1', array_nest_level='2')

    records = to_records_dict([first_array, second_array, leaf_row])
    max_cols = {
        'array-first': {'MVMT_VAR_LINK_ID': LINK_ID, 'ARRAY_MEMBER_ID': 'array-first', 'MAX_COL_SEQ': 1},
        'array-second': {'MVMT_VAR_LINK_ID': LINK_ID, 'ARRAY_MEMBER_ID': 'array-second', 'MAX_COL_SEQ': 3},
    }

    expected_result, new_result = run_both_expand(request, records, max_cols)

    assert canonical(new_result) == canonical(expected_result)
    # 先に処理された array-first（繰返1回）に紐づくので 1 件。後勝ちだと 3 件になる
    assert len(new_result) == 1
