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

"""刈取メイン処理を本物のまま動かし、Movement-変数紐付 → 多段変数メンバー管理 → 変数ネスト管理 → 展開処理 → 多段変数配列組合せ管理
の波及を最終状態で確認する（通し）

展開処理は、多段変数メンバー管理の行を親子の木に組み、変数ネスト管理の繰返数で多段変数配列組合せ管理の代入欄の候補を作る処理（メニューではない）。

経緯: Issue #2618 / #3072
"""
import copy

import pytest

from tests.common import (
    ATTR_STD, ATTR_LIST, ATTR_M_ARRAY, BACKYARD_USER_ID,
    TABLE_MVMT_VAR_LINK, TABLE_NESTVAR_MEMBER, TABLE_NESTVAR_MEMBER_MAX_COL, TABLE_NESTVAR_MEMBER_COL_COMB,
    create_backyard_db, create_mov_vars_dict, create_nest_variable_from_yaml,
    snapshot_rows, assert_rows_unchanged,
)


MOVEMENT = 'mv-1'

# 配列 servers の各要素が name と ports（配列）を持つ。配列階層が 2 つ（0 と 0.ports.0）
SERVERS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
"""

# ports の上に os を 1 行挿入
SERVERS_WITH_OS_YAML = """
VAR_servers:
  - name: web01
    os: linux
    ports:
      - http: 80
"""

# ports を消した（ports 配下は廃止になる）
SERVERS_WITHOUT_PORTS_YAML = """
VAR_servers:
  - name: web01
"""

# name と ports の並びを入れ替えた
SERVERS_PORTS_FIRST_YAML = """
VAR_servers:
  - ports:
      - http: 80
    name: web01
"""

# ports を配列から辞書に変えた（配列階層の行 0.ports.0 が無くなり、階層パスが 0.ports.http になる）
SERVERS_PORTS_AS_DICT_YAML = """
VAR_servers:
  - name: web01
    ports:
      http: 80
"""

# 配列が 3 段（servers → ports → tags）。tags の要素を辞書にしないと配列階層は 2 段にしかならない
SERVERS_THREE_LEVELS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
        tags:
          - k: t1
"""

# 3 段配列の最上位（name の下）に os を 1 行挿入
SERVERS_THREE_LEVELS_WITH_OS_YAML = """
VAR_servers:
  - name: web01
    os: linux
    ports:
      - http: 80
        tags:
          - k: t1
"""

# 3 段配列の ports の要素の中（http の下）に https を 1 行挿入。後ろに子配列 tags がある
SERVERS_THREE_LEVELS_WITH_HTTPS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
        https: 443
        tags:
          - k: t1
"""


def _extraction(*variables):
    """Movement 1 つ分の解析結果を組み立てる"""
    return create_mov_vars_dict({MOVEMENT: list(variables)})


def _nest(yaml_text=SERVERS_YAML, var_name='VAR_servers'):
    return create_nest_variable_from_yaml(yaml_text, var_name)


def _active(db, table):
    return db.find_rows(table, DISUSE_FLAG='0')


def _discarded(db, table):
    return db.find_rows(table, DISUSE_FLAG='1')


def _conditions(disuse_flag, link_id):
    """廃止フラグと、指定があれば Movement-変数紐付の行 ID で絞る条件を組み立てる"""
    conditions = {}
    conditions['DISUSE_FLAG'] = disuse_flag
    if link_id is not None:
        conditions['MVMT_VAR_LINK_ID'] = link_id
    return conditions


def _members_by_path(db, disuse_flag='0', link_id=None):
    """多段変数メンバー管理の行を階層パスで引ける辞書にして返す（行は深いコピー。刈取前の値を控えるのに使えるよう、DB の実体と切り離す）
    link_id を渡すと、その Movement-変数紐付の行（Movement）に紐付く行だけに絞る
    """
    result = {}
    for row in db.find_rows(TABLE_NESTVAR_MEMBER, **_conditions(disuse_flag, link_id)):
        result[row['VRAS_NAME_PATH']] = copy.deepcopy(row)
    return result


def _aliases(db, disuse_flag='0', link_id=None):
    aliases = []
    for row in db.find_rows(TABLE_NESTVAR_MEMBER_COL_COMB, **_conditions(disuse_flag, link_id)):
        aliases.append(row['COL_COMBINATION_MEMBER_ALIAS'])
    return sorted(aliases)


def _set_repeat_count(db, member, count):
    """利用者が変数ネスト管理で、多段変数メンバー管理の配列階層の行 member に紐付く繰返数を count に変えた"""
    db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=member['ARRAY_MEMBER_ID'])['MAX_COL_SEQ'] = count


def _repeat_count(db, member):
    """多段変数メンバー管理の配列階層の行 member に紐付く変数ネスト管理の行の（廃止フラグ, 繰返数）"""
    max_col = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=member['ARRAY_MEMBER_ID'])
    return (max_col['DISUSE_FLAG'], max_col['MAX_COL_SEQ'])


def _orders(member):
    """多段変数メンバー管理の行の（定義順, 親の定義順）"""
    return (int(member['VARS_KEY_ID']), int(member['PARENT_VARS_KEY_ID']))


def _link_id_of(db, movement_id):
    return db.find_row(TABLE_MVMT_VAR_LINK, MOVEMENT_ID=movement_id)['MVMT_VAR_LINK_ID']


def test_new_nest_variable_reaches_every_menu(run_backyard):
    """Playbook に多段変数を新しく書くと、1 回の刈取で Movement-変数紐付から多段変数配列組合せ管理までの全メニューに行が作られる

    Movement-変数紐付に払い出された行 ID が多段変数メンバー管理の全メンバーに入り、多段変数メンバー管理の配列階層の行 ID が変数ネスト管理に入り、
    展開処理の結果が多段変数配列組合せ管理に登録される。変数ネスト管理の繰返数は 1 で登録される。
    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()

    run_backyard(db, _extraction(_nest()))

    link_rows = db.rows(TABLE_MVMT_VAR_LINK)
    assert len(link_rows) == 1
    link = link_rows[0]
    assert (link['MOVEMENT_ID'], link['VARS_NAME'], link['VARS_ATTRIBUTE_01'], link['DISUSE_FLAG'], link['LAST_UPDATE_USER']) == \
        (MOVEMENT, 'VAR_servers', ATTR_M_ARRAY, '0', BACKYARD_USER_ID)

    members = _members_by_path(db)
    assert sorted(members.keys()) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http']
    for row in members.values():
        assert row['MVMT_VAR_LINK_ID'] == link['MVMT_VAR_LINK_ID']
        assert row['LAST_UPDATE_USER'] == BACKYARD_USER_ID
    assert members['0']['VARS_NAME'] == '0'
    assert members['0.ports.0']['VARS_NAME'] == '0'

    max_col_rows = _active(db, TABLE_NESTVAR_MEMBER_MAX_COL)
    max_col_member_ids = []
    for row in max_col_rows:
        max_col_member_ids.append(row['ARRAY_MEMBER_ID'])
    assert sorted(max_col_member_ids) == sorted([members['0']['ARRAY_MEMBER_ID'], members['0.ports.0']['ARRAY_MEMBER_ID']])
    for row in max_col_rows:
        assert row['MAX_COL_SEQ'] == 1
        assert row['MVMT_VAR_LINK_ID'] == link['MVMT_VAR_LINK_ID']

    assert _aliases(db) == ['[0].name', '[0].ports[0].http']
    comb_http = db.find_row(TABLE_NESTVAR_MEMBER_COL_COMB, COL_COMBINATION_MEMBER_ALIAS='[0].ports[0].http')
    assert comb_http['ARRAY_MEMBER_ID'] == members['0.ports.0.http']['ARRAY_MEMBER_ID']
    assert comb_http['COL_SEQ_VALUE'] == '0000000000000000'

    assert db.committed == 1
    assert db.disconnected == 1
    assert db.rows('T_COMN_PROC_LOADED_LIST')[0]['LOADED_FLG'] == '1'


def test_first_run_registers_everything(run_backyard):
    """メニューが全部空の初回刈取で、一般変数・複数具体値変数・多段変数がすべて登録される

    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()

    run_backyard(db, _extraction(('VAR_std', ATTR_STD), ('VAR_list', ATTR_LIST), _nest()))

    types = {}
    for row in db.rows(TABLE_MVMT_VAR_LINK):
        types[row['VARS_NAME']] = row['VARS_ATTRIBUTE_01']
    assert types == {'VAR_std': ATTR_STD, 'VAR_list': ATTR_LIST, 'VAR_servers': ATTR_M_ARRAY}
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 5
    assert len(db.rows(TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert len(db.rows(TABLE_NESTVAR_MEMBER_COL_COMB)) == 2


def test_removed_nest_variable_discards_members_and_fields(run_backyard):
    """多段変数を Playbook から消すと、Movement-変数紐付が廃止され、多段変数メンバー管理の全メンバー・変数ネスト管理の繰返数行・多段変数配列組合せ管理の欄も廃止される

    Movement-変数紐付の再読込は有効行だけなので多段変数メンバー管理から見るとその変数は無い扱いになり、多段変数メンバー管理の再読込も有効行だけなので変数ネスト管理・展開処理に廃止行は届かない。
    Movement-変数紐付の備考は消えない。
    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest()))
    db.rows(TABLE_MVMT_VAR_LINK)[0]['NOTE'] = 'user memo'

    run_backyard(db, _extraction())

    link = db.rows(TABLE_MVMT_VAR_LINK)[0]
    assert link['DISUSE_FLAG'] == '1'
    assert link['VARS_ATTRIBUTE_01'] == ATTR_M_ARRAY
    assert link['NOTE'] == 'user memo'
    assert _active(db, TABLE_NESTVAR_MEMBER) == []
    assert len(_discarded(db, TABLE_NESTVAR_MEMBER)) == 5
    assert _active(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    assert len(_discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _aliases(db) == []
    assert _aliases(db, disuse_flag='1') == ['[0].name', '[0].ports[0].http']
    # 廃止だけで、どのメニューにも新しい行は増えない
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 5
    assert len(db.rows(TABLE_NESTVAR_MEMBER_COL_COMB)) == 2


def test_returning_nest_variable_restores_members_and_fields(run_backyard):
    """いちど消した多段変数を同じ構造で Playbook に戻すと、Movement-変数紐付・多段変数メンバー管理・変数ネスト管理・多段変数配列組合せ管理の行がすべて復活し、新しい行は増えない

    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest()))
    run_backyard(db, _extraction())
    assert _active(db, TABLE_NESTVAR_MEMBER) == []

    run_backyard(db, _extraction(_nest()))

    link = db.rows(TABLE_MVMT_VAR_LINK)[0]
    assert (link['DISUSE_FLAG'], link['VARS_ATTRIBUTE_01']) == ('0', ATTR_M_ARRAY)
    assert len(db.rows(TABLE_MVMT_VAR_LINK)) == 1
    assert len(_active(db, TABLE_NESTVAR_MEMBER)) == 5
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 5
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert len(db.rows(TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _aliases(db) == ['[0].name', '[0].ports[0].http']
    assert len(db.rows(TABLE_NESTVAR_MEMBER_COL_COMB)) == 2


@pytest.mark.parametrize('flat_attr, discarded_first', [
    pytest.param(ATTR_STD, False, id='std_active'),
    pytest.param(ATTR_LIST, False, id='list_active'),
    pytest.param(ATTR_STD, True, id='std_discarded'),
    pytest.param(ATTR_LIST, True, id='list_discarded'),
])
def test_flat_variable_becoming_nested_registers_members(run_backyard, flat_attr, discarded_first):
    """一般変数／複数具体値変数だった名前を多段変数として書き直すと、Movement-変数紐付のタイプが 3 に変わり多段変数メンバー管理・変数ネスト管理・多段変数配列組合せ管理に行が作られる

    廃止済みの行を書き直す形（discarded）は Issue #2618 の再現手順そのもの。復活がタイプ更新を巻き戻すと
    多段変数メンバー管理が Movement-変数紐付の行を見つけられず処理が停止していた。
    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(('VAR_servers', flat_attr)))
    if discarded_first:
        run_backyard(db, _extraction())
        assert db.rows(TABLE_MVMT_VAR_LINK)[0]['DISUSE_FLAG'] == '1'
    db.rows(TABLE_MVMT_VAR_LINK)[0]['NOTE'] = 'user memo'

    run_backyard(db, _extraction(_nest()))

    assert len(db.rows(TABLE_MVMT_VAR_LINK)) == 1
    link = db.rows(TABLE_MVMT_VAR_LINK)[0]
    assert (link['VARS_ATTRIBUTE_01'], link['DISUSE_FLAG'], link['NOTE'], link['LAST_UPDATE_USER']) == \
        (ATTR_M_ARRAY, '0', 'user memo', BACKYARD_USER_ID)
    members = _members_by_path(db)
    assert len(members) == 5
    for row in members.values():
        assert row['MVMT_VAR_LINK_ID'] == link['MVMT_VAR_LINK_ID']
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _aliases(db) == ['[0].name', '[0].ports[0].http']


@pytest.mark.parametrize('flat_attr, discarded_first', [
    pytest.param(ATTR_STD, False, id='std_active'),
    pytest.param(ATTR_LIST, False, id='list_active'),
    pytest.param(ATTR_STD, True, id='std_discarded'),
    pytest.param(ATTR_LIST, True, id='list_discarded'),
])
def test_nest_variable_becoming_flat_discards_members(run_backyard, flat_attr, discarded_first):
    """多段変数だった名前を一般変数／複数具体値変数として書き直すと、Movement-変数紐付のタイプが変わり多段変数メンバー管理・変数ネスト管理・多段変数配列組合せ管理の行は全部廃止される

    廃止済みの多段変数を書き直す形（discarded）で巻き戻ると、Movement-変数紐付がタイプ 3 のまま画面に出る（#2618 第二の症状）。
    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest()))
    if discarded_first:
        run_backyard(db, _extraction())
    db.rows(TABLE_MVMT_VAR_LINK)[0]['NOTE'] = 'user memo'
    db.rows(TABLE_NESTVAR_MEMBER)[0]['NOTE'] = 'member memo'

    run_backyard(db, _extraction(('VAR_servers', flat_attr)))

    assert len(db.rows(TABLE_MVMT_VAR_LINK)) == 1
    link = db.rows(TABLE_MVMT_VAR_LINK)[0]
    assert (link['VARS_ATTRIBUTE_01'], link['DISUSE_FLAG'], link['NOTE']) == (flat_attr, '0', 'user memo')
    assert _active(db, TABLE_NESTVAR_MEMBER) == []
    assert len(_discarded(db, TABLE_NESTVAR_MEMBER)) == 5
    assert db.rows(TABLE_NESTVAR_MEMBER)[0]['NOTE'] == 'member memo'
    assert _active(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    assert _aliases(db) == []


def test_unchanged_nest_variable_changes_only_member_timestamps(run_backyard):
    """同じ Playbook でもう一度刈取を回すと、Movement-変数紐付・変数ネスト管理・多段変数配列組合せ管理は一切書き込まれず、多段変数メンバー管理は全行が同じ値で書き直され更新日時だけ動く

    多段変数メンバー管理の共通行全件を UPDATE するのは現状仕様として固定する（直すときはこのテストの UPDATE 件数の期待値だけを変える）。
    1 回目に登録した行を 2 回目に読み直しても（解析器の数値と DB の文字列の違いがあっても）「同じメンバー」と判定される。
    経緯: Issue #2618 / #3072（現状仕様として固定）
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest()))
    snapshots = {}
    for table in (TABLE_MVMT_VAR_LINK, TABLE_NESTVAR_MEMBER, TABLE_NESTVAR_MEMBER_MAX_COL, TABLE_NESTVAR_MEMBER_COL_COMB):
        snapshots[table] = snapshot_rows(db, table)
    db.update_calls.clear()
    db.insert_calls.clear()

    run_backyard(db, _extraction(_nest()))

    # Movement-変数紐付・変数ネスト管理・多段変数配列組合せ管理: 更新日時まで含めて無変化。書き込みは実行済みフラグ以外に無い
    assert_rows_unchanged(snapshots[TABLE_MVMT_VAR_LINK], db.rows(TABLE_MVMT_VAR_LINK), ignore_columns=())
    assert_rows_unchanged(snapshots[TABLE_NESTVAR_MEMBER_MAX_COL], db.rows(TABLE_NESTVAR_MEMBER_MAX_COL), ignore_columns=())
    assert_rows_unchanged(snapshots[TABLE_NESTVAR_MEMBER_COL_COMB], db.rows(TABLE_NESTVAR_MEMBER_COL_COMB), ignore_columns=())
    for table in (TABLE_MVMT_VAR_LINK, TABLE_NESTVAR_MEMBER_MAX_COL, TABLE_NESTVAR_MEMBER_COL_COMB):
        for call in db.update_calls_for(table):
            assert call['data_list'] == []
        for call in db.insert_calls_for(table):
            assert call['data_list'] == []
    # 多段変数メンバー管理: 値は無変化（更新日時は除く）。UPDATE は共通行 5 件が 1 回の呼び出しで流れる（現状仕様）
    assert_rows_unchanged(snapshots[TABLE_NESTVAR_MEMBER], db.rows(TABLE_NESTVAR_MEMBER))
    member_update_counts = []
    for call in db.update_calls_for(TABLE_NESTVAR_MEMBER):
        member_update_counts.append(len(call['data_list']))
    assert member_update_counts == [5, 0]
    for call in db.insert_calls_for(TABLE_NESTVAR_MEMBER):
        assert call['data_list'] == []


def test_inserting_member_above_keeps_children_and_repeat_count(run_backyard):
    """Playbook で ports の上に os を 1 行挿入すると、os だけ登録され、ports は定義順、ports 配下の 2 行は定義順と親メンバーが
    同じ行のまま更新される。利用者が変数ネスト管理で 3 に変えていた ports の繰返数はそのまま残り、多段変数配列組合せ管理の欄は繰返数 3 に合わせて増える

    親メンバー（親の定義順）は同一性キーに含まれないので、上位への挿入で番号がずれても配下は別メンバー扱いにならない。
    #3096 より前は配下の 2 行が廃止＋新規登録になり、変数ネスト管理の繰返数が 1 に戻り、多段変数配列組合せ管理の欄も作り直されていた（#3096 で修正）。
    経緯: Issue #2618 / #3072 / #3096（親メンバーを同一性キーから外し、新挙動を固定）
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_YAML)))
    before = _members_by_path(db)
    ports_array_before = before['0.ports.0']
    max_col_ports_before = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=ports_array_before['ARRAY_MEMBER_ID'])
    max_col_ports_before['MAX_COL_SEQ'] = 3    # 利用者が変数ネスト管理で繰返数を 3 に変えた

    run_backyard(db, _extraction(_nest(SERVERS_WITH_OS_YAML)))

    after = _members_by_path(db)
    assert sorted(after.keys()) == ['0', '0.name', '0.os', '0.ports', '0.ports.0', '0.ports.0.http']
    # A・B・C・D・E は同じ行のまま。os だけ新しい行
    for path in ('0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http'):
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID'], path
    # C（ports）は定義順だけ 3 → 4。D・E は定義順と親メンバーが新しい番号に更新される
    assert int(after['0.ports']['VARS_KEY_ID']) == 4
    assert (int(after['0.ports.0']['VARS_KEY_ID']), int(after['0.ports.0']['PARENT_VARS_KEY_ID'])) == (5, 4)
    assert (int(after['0.ports.0.http']['VARS_KEY_ID']), int(after['0.ports.0.http']['PARENT_VARS_KEY_ID'])) == (6, 5)
    assert _members_by_path(db, disuse_flag='1') == {}
    # 変数ネスト管理: ports 配列の行はそのまま。利用者が入れた繰返数 3 が残り、新しい行はできない
    max_col_ports_after = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=ports_array_before['ARRAY_MEMBER_ID'])
    assert (max_col_ports_after['DISUSE_FLAG'], max_col_ports_after['MAX_COL_SEQ']) == ('0', 3)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    # 多段変数配列組合せ管理: os の欄が増え、ports 配下の欄は繰返数 3 に合わせて 3 つ。http の欄は同じ行 ID に紐付いたまま。廃止された欄は無い
    assert _aliases(db) == ['[0].name', '[0].os', '[0].ports[0].http', '[0].ports[1].http', '[0].ports[2].http']
    http_comb = db.find_row(TABLE_NESTVAR_MEMBER_COL_COMB, COL_COMBINATION_MEMBER_ALIAS='[0].ports[0].http', DISUSE_FLAG='0')
    assert http_comb['ARRAY_MEMBER_ID'] == before['0.ports.0.http']['ARRAY_MEMBER_ID']
    assert _aliases(db, disuse_flag='1') == []


def test_removing_member_above_keeps_children_and_repeat_count(run_backyard):
    """Playbook で ports の上にあった os を消すと、os の行と多段変数配列組合せ管理の欄だけ廃止され、ports は定義順、ports 配下の 2 行は定義順と親メンバーが
    同じ行のまま更新される。利用者が変数ネスト管理で 3 に変えていた ports の繰返数はそのまま残り、多段変数配列組合せ管理の http の欄は同じ行 ID に紐付いたまま

    上位の削除でも配下の親メンバー（親の定義順）はずれる（5 → 4、6 → 5 が 4 → 3、5 → 4 に戻る）が、挿入と同じく配下は同じ行のまま。
    経緯: Issue #3072 / #3096
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_WITH_OS_YAML)))
    before = _members_by_path(db)
    ports_array_id = before['0.ports.0']['ARRAY_MEMBER_ID']
    db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=ports_array_id)['MAX_COL_SEQ'] = 3    # 利用者が変数ネスト管理で繰返数を 3 に変えた

    run_backyard(db, _extraction(_nest(SERVERS_YAML)))

    after = _members_by_path(db)
    assert sorted(after.keys()) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http']
    for path in after:
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID'], path
    assert int(after['0.ports']['VARS_KEY_ID']) == 3
    assert (int(after['0.ports.0']['VARS_KEY_ID']), int(after['0.ports.0']['PARENT_VARS_KEY_ID'])) == (4, 3)
    assert (int(after['0.ports.0.http']['VARS_KEY_ID']), int(after['0.ports.0.http']['PARENT_VARS_KEY_ID'])) == (5, 4)
    assert sorted(_members_by_path(db, disuse_flag='1').keys()) == ['0.os']
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 6
    # 変数ネスト管理: ports 配列の行はそのまま。利用者が入れた繰返数 3 が残る
    max_col_ports_after = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=ports_array_id)
    assert (max_col_ports_after['DISUSE_FLAG'], max_col_ports_after['MAX_COL_SEQ']) == ('0', 3)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    # 多段変数配列組合せ管理: os の欄だけ廃止。ports 配下の欄は繰返数 3 に合わせて 3 つで、http の欄は同じ行 ID に紐付いたまま
    assert _aliases(db) == ['[0].name', '[0].ports[0].http', '[0].ports[1].http', '[0].ports[2].http']
    assert _aliases(db, disuse_flag='1') == ['[0].os']
    http_comb = db.find_row(TABLE_NESTVAR_MEMBER_COL_COMB, COL_COMBINATION_MEMBER_ALIAS='[0].ports[0].http', DISUSE_FLAG='0')
    assert http_comb['ARRAY_MEMBER_ID'] == before['0.ports.0.http']['ARRAY_MEMBER_ID']


def test_restoring_members_while_inserting_above_takes_new_orders(run_backyard):
    """Playbook から ports を消して刈取（ports 配下は廃止）したあと、name の下に os を足すのと同時に ports を戻すと、ports 配下は元の行のまま
    復活し、定義順と親メンバー（親の定義順）が両方とも新しい番号になる。利用者が変数ネスト管理で 3 に変えていた ports の繰返数も戻り、多段変数配列組合せ管理の欄は 3 つ

    復活と番号の更新が同時に起きても、親メンバーが古いまま残ると展開処理で親が見つからず多段変数配列組合せ管理の欄が出なくなる。親メンバーまで新しい値になることを見る。
    経緯: Issue #3072 / #3096
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_YAML)))
    before = _members_by_path(db)
    _set_repeat_count(db, before['0.ports.0'], 3)    # 利用者が変数ネスト管理で繰返数を 3 に変えた

    run_backyard(db, _extraction(_nest(SERVERS_WITHOUT_PORTS_YAML)))

    assert sorted(_members_by_path(db, disuse_flag='1').keys()) == ['0.ports', '0.ports.0', '0.ports.0.http']
    assert _repeat_count(db, before['0.ports.0']) == ('1', 3)
    assert _aliases(db, disuse_flag='1') == ['[0].ports[0].http']

    run_backyard(db, _extraction(_nest(SERVERS_WITH_OS_YAML)))

    after = _members_by_path(db)
    assert sorted(after.keys()) == ['0', '0.name', '0.os', '0.ports', '0.ports.0', '0.ports.0.http']
    for path in before:
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID'], path
    # 復活した 3 行は定義順・親メンバーとも新しい番号。os だけ新しい行
    assert _orders(after['0.os']) == (3, 1)
    assert _orders(after['0.ports']) == (4, 1)
    assert _orders(after['0.ports.0']) == (5, 4)
    assert _orders(after['0.ports.0.http']) == (6, 5)
    assert _members_by_path(db, disuse_flag='1') == {}
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 6
    # 変数ネスト管理: ports 配列の行が元の ID で復活し、利用者が入れた繰返数 3 が戻る
    assert _repeat_count(db, before['0.ports.0']) == ('0', 3)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    # 多段変数配列組合せ管理: ports 配下の欄は繰返数 3 に合わせて 3 つ。http の欄は元の行に紐付いたまま。廃止された欄は無い
    assert _aliases(db) == ['[0].name', '[0].os', '[0].ports[0].http', '[0].ports[1].http', '[0].ports[2].http']
    http_comb = db.find_row(TABLE_NESTVAR_MEMBER_COL_COMB, COL_COMBINATION_MEMBER_ALIAS='[0].ports[0].http', DISUSE_FLAG='0')
    assert http_comb['ARRAY_MEMBER_ID'] == before['0.ports.0.http']['ARRAY_MEMBER_ID']
    assert _aliases(db, disuse_flag='1') == []


def test_inserting_member_above_three_level_array_keeps_every_level(run_backyard):
    """配列が 3 段（servers → ports → tags）の Playbook で、最上位の name の下に os を 1 行挿入すると、os だけ登録され、元の 8 行は
    3 段とも同じ行のまま定義順と親メンバーが更新される。利用者が変数ネスト管理で入れた ports の 2・tags の 3 が両方残り、tags の欄は 2×3＝6 つ

    番号のずれが 2 段目・3 段目の親メンバーまで正しく伝わるかは、2 段のテストでは見えない。
    経緯: Issue #3072 / #3096
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_THREE_LEVELS_YAML)))
    before = _members_by_path(db)
    assert sorted(before.keys()) == [
        '0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http', '0.ports.0.tags', '0.ports.0.tags.0', '0.ports.0.tags.0.k']
    _set_repeat_count(db, before['0.ports.0'], 2)         # 利用者が変数ネスト管理で ports の繰返数を 2 に変えた
    _set_repeat_count(db, before['0.ports.0.tags.0'], 3)  # 同じく tags を 3 に変えた

    run_backyard(db, _extraction(_nest(SERVERS_THREE_LEVELS_WITH_OS_YAML)))

    after = _members_by_path(db)
    assert len(after) == 9
    for path in before:
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID'], path
    assert _orders(after['0.os']) == (3, 1)
    assert _orders(after['0.ports']) == (4, 1)
    assert _orders(after['0.ports.0']) == (5, 4)
    assert _orders(after['0.ports.0.http']) == (6, 5)
    assert _orders(after['0.ports.0.tags']) == (7, 5)
    assert _orders(after['0.ports.0.tags.0']) == (8, 7)
    assert _orders(after['0.ports.0.tags.0.k']) == (9, 8)
    assert _members_by_path(db, disuse_flag='1') == {}
    # 変数ネスト管理: 2 段目・3 段目とも行はそのまま。利用者が入れた繰返数が残る
    assert _repeat_count(db, before['0.ports.0']) == ('0', 2)
    assert _repeat_count(db, before['0.ports.0.tags.0']) == ('0', 3)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 3
    assert _discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    # 多段変数配列組合せ管理: tags の k の欄は ports 2 × tags 3 = 6 つで、すべて元の k の行に紐付く
    assert _aliases(db) == [
        '[0].name', '[0].os',
        '[0].ports[0].http', '[0].ports[0].tags[0].k', '[0].ports[0].tags[1].k', '[0].ports[0].tags[2].k',
        '[0].ports[1].http', '[0].ports[1].tags[0].k', '[0].ports[1].tags[1].k', '[0].ports[1].tags[2].k',
    ]
    for comb in _active(db, TABLE_NESTVAR_MEMBER_COL_COMB):
        if comb['COL_COMBINATION_MEMBER_ALIAS'].endswith('.k'):
            assert comb['ARRAY_MEMBER_ID'] == before['0.ports.0.tags.0.k']['ARRAY_MEMBER_ID'], comb['COL_COMBINATION_MEMBER_ALIAS']
    assert _aliases(db, disuse_flag='1') == []


def test_swapping_siblings_keeps_children_and_repeat_count(run_backyard):
    """Playbook で name と ports の並びを入れ替えると、5 行とも同じ行のまま定義順（ports 配下は親メンバーも）が入れ替わる。
    利用者が変数ネスト管理で 3 に変えていた ports の繰返数は残り、多段変数配列組合せ管理の欄も 3 つのまま同じ行に紐付く

    入れ替えで変数ネスト管理の行が作り直されると繰返数が 1 に戻る。これは変数ネスト管理・多段変数配列組合せ管理まで流す通しでしか見られない。
    経緯: Issue #3072 / #3096
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_YAML)))
    before = _members_by_path(db)
    _set_repeat_count(db, before['0.ports.0'], 3)    # 利用者が変数ネスト管理で繰返数を 3 に変えた

    run_backyard(db, _extraction(_nest(SERVERS_PORTS_FIRST_YAML)))

    after = _members_by_path(db)
    assert sorted(after.keys()) == sorted(before.keys())
    for path in before:
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID'], path
    assert _orders(after['0.ports']) == (2, 1)
    assert _orders(after['0.ports.0']) == (3, 2)
    assert _orders(after['0.ports.0.http']) == (4, 3)
    assert _orders(after['0.name']) == (5, 1)
    assert _members_by_path(db, disuse_flag='1') == {}
    # 変数ネスト管理: ports 配列の行はそのまま。繰返数 3 が残る
    assert _repeat_count(db, before['0.ports.0']) == ('0', 3)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    # 多段変数配列組合せ管理: 欄の並びは変わらず、http の欄は元の行に紐付いたまま
    assert _aliases(db) == ['[0].name', '[0].ports[0].http', '[0].ports[1].http', '[0].ports[2].http']
    http_comb = db.find_row(TABLE_NESTVAR_MEMBER_COL_COMB, COL_COMBINATION_MEMBER_ALIAS='[0].ports[0].http', DISUSE_FLAG='0')
    assert http_comb['ARRAY_MEMBER_ID'] == before['0.ports.0.http']['ARRAY_MEMBER_ID']
    assert _aliases(db, disuse_flag='1') == []


def test_adding_member_inside_array_keeps_following_child_array(run_backyard):
    """3 段配列の ports の要素の中（http の下）に https を 1 行挿入すると、https だけ登録され、後ろの子配列 tags 配下は同じ行のまま
    定義順と親メンバーが更新される。利用者が変数ネスト管理で 3 に変えていた tags の繰返数は残る

    経緯: Issue #3072 / #3096
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_THREE_LEVELS_YAML)))
    before = _members_by_path(db)
    _set_repeat_count(db, before['0.ports.0.tags.0'], 3)    # 利用者が変数ネスト管理で tags の繰返数を 3 に変えた

    run_backyard(db, _extraction(_nest(SERVERS_THREE_LEVELS_WITH_HTTPS_YAML)))

    after = _members_by_path(db)
    assert len(after) == 9
    for path in before:
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID'], path
    # https より前は番号も変わらない。後ろの tags 配下だけ 1 つずれる
    assert _orders(after['0.ports.0.http']) == (5, 4)
    assert _orders(after['0.ports.0.https']) == (6, 4)
    assert _orders(after['0.ports.0.tags']) == (7, 4)
    assert _orders(after['0.ports.0.tags.0']) == (8, 7)
    assert _orders(after['0.ports.0.tags.0.k']) == (9, 8)
    assert _members_by_path(db, disuse_flag='1') == {}
    # 変数ネスト管理: tags の行はそのまま繰返数 3。ports は初期値の 1
    assert _repeat_count(db, before['0.ports.0.tags.0']) == ('0', 3)
    assert _repeat_count(db, before['0.ports.0']) == ('0', 1)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 3
    assert _discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    # 多段変数配列組合せ管理: https の欄だけ増え、tags の k の欄 3 つは元の k の行に紐付いたまま
    assert _aliases(db) == [
        '[0].name', '[0].ports[0].http', '[0].ports[0].https',
        '[0].ports[0].tags[0].k', '[0].ports[0].tags[1].k', '[0].ports[0].tags[2].k',
    ]
    for comb in _active(db, TABLE_NESTVAR_MEMBER_COL_COMB):
        if comb['COL_COMBINATION_MEMBER_ALIAS'].endswith('.k'):
            assert comb['ARRAY_MEMBER_ID'] == before['0.ports.0.tags.0.k']['ARRAY_MEMBER_ID'], comb['COL_COMBINATION_MEMBER_ALIAS']
    assert _aliases(db, disuse_flag='1') == []


def test_inserting_member_above_in_one_movement_leaves_other_movement_alone(run_backyard):
    """同じ構造の多段変数を持つ 2 つの Movement のうち、mv-1 の Playbook だけ name の下に os を挿入すると、mv-1 だけ os が登録され
    配下の番号が更新される。mv-2 の多段変数メンバー管理は更新日時以外なにも変わらない。両方とも利用者が変数ネスト管理で入れた繰返数 3 が残る

    mv-2 の多段変数配列組合せ管理の欄が 1 つから 3 つに増えるのは、このテストで変数ネスト管理の繰返数を 3 に変えたため（多段変数メンバー管理が無変化であることとは別）。
    経緯: Issue #3072 / #3096
    """
    db = create_backyard_db()
    run_backyard(db, create_mov_vars_dict({'mv-1': [_nest(SERVERS_YAML)], 'mv-2': [_nest(SERVERS_YAML)]}))
    link_1 = _link_id_of(db, 'mv-1')
    link_2 = _link_id_of(db, 'mv-2')
    before_1 = _members_by_path(db, link_id=link_1)
    before_2 = _members_by_path(db, link_id=link_2)
    _set_repeat_count(db, before_1['0.ports.0'], 3)    # 利用者が両方の Movement の変数ネスト管理で繰返数を 3 に変えた
    _set_repeat_count(db, before_2['0.ports.0'], 3)
    rows_2_before = copy.deepcopy(db.find_rows(TABLE_NESTVAR_MEMBER, MVMT_VAR_LINK_ID=link_2))

    run_backyard(db, create_mov_vars_dict({'mv-1': [_nest(SERVERS_WITH_OS_YAML)], 'mv-2': [_nest(SERVERS_YAML)]}))

    # mv-1: os だけ新しい行。配下は同じ行のまま番号が更新される
    after_1 = _members_by_path(db, link_id=link_1)
    assert sorted(after_1.keys()) == ['0', '0.name', '0.os', '0.ports', '0.ports.0', '0.ports.0.http']
    for path in before_1:
        assert after_1[path]['ARRAY_MEMBER_ID'] == before_1[path]['ARRAY_MEMBER_ID'], path
    assert _orders(after_1['0.ports']) == (4, 1)
    assert _orders(after_1['0.ports.0']) == (5, 4)
    assert _orders(after_1['0.ports.0.http']) == (6, 5)
    # mv-2: 件数も中身も変わらない（更新日時だけ動く）
    assert_rows_unchanged(rows_2_before, db.find_rows(TABLE_NESTVAR_MEMBER, MVMT_VAR_LINK_ID=link_2))
    assert _members_by_path(db, disuse_flag='1') == {}
    # 変数ネスト管理: 両方の Movement で繰返数 3 が残る
    assert _repeat_count(db, before_1['0.ports.0']) == ('0', 3)
    assert _repeat_count(db, before_2['0.ports.0']) == ('0', 3)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 4
    # 多段変数配列組合せ管理: mv-1 は os の欄が増える。mv-2 は繰返数 3 に合わせた欄だけ
    assert _aliases(db, link_id=link_1) == ['[0].name', '[0].os', '[0].ports[0].http', '[0].ports[1].http', '[0].ports[2].http']
    assert _aliases(db, link_id=link_2) == ['[0].name', '[0].ports[0].http', '[0].ports[1].http', '[0].ports[2].http']
    assert _aliases(db, disuse_flag='1') == []


def test_array_turned_into_dict_and_back_restores_old_rows(run_backyard):
    """Playbook で ports を配列から辞書に変えると、配列側の 2 行（要素と http）と変数ネスト管理の行が廃止され、辞書側の http が新しい行になる。
    配列に戻すと配列側の 2 行と変数ネスト管理の行が元の ID で復活し、利用者が入れた繰返数 3 も戻る。辞書側の行は廃止され、重複行は残らない

    配列と辞書では階層パス（0.ports.0.http と 0.ports.http）が違うので、別のメンバーとして扱われる。
    経緯: Issue #3072 / #3096
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_YAML)))
    before = _members_by_path(db)
    _set_repeat_count(db, before['0.ports.0'], 3)    # 利用者が変数ネスト管理で繰返数を 3 に変えた

    run_backyard(db, _extraction(_nest(SERVERS_PORTS_AS_DICT_YAML)))

    as_dict = _members_by_path(db)
    assert sorted(as_dict.keys()) == ['0', '0.name', '0.ports', '0.ports.http']
    assert as_dict['0.ports']['ARRAY_MEMBER_ID'] == before['0.ports']['ARRAY_MEMBER_ID']
    assert _orders(as_dict['0.ports.http']) == (4, 3)
    assert sorted(_members_by_path(db, disuse_flag='1').keys()) == ['0.ports.0', '0.ports.0.http']
    assert _repeat_count(db, before['0.ports.0']) == ('1', 3)
    assert _aliases(db) == ['[0].name', '[0].ports.http']
    assert _aliases(db, disuse_flag='1') == ['[0].ports[0].http']
    dict_http_id = as_dict['0.ports.http']['ARRAY_MEMBER_ID']

    run_backyard(db, _extraction(_nest(SERVERS_YAML)))

    after = _members_by_path(db)
    assert sorted(after.keys()) == sorted(before.keys())
    for path in before:
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID'], path
    assert _orders(after['0.ports.0']) == (4, 3)
    assert _orders(after['0.ports.0.http']) == (5, 4)
    discarded = _members_by_path(db, disuse_flag='1')
    assert sorted(discarded.keys()) == ['0.ports.http']
    assert discarded['0.ports.http']['ARRAY_MEMBER_ID'] == dict_http_id
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 6
    # 変数ネスト管理: ports 配列の行が元の ID で復活し、利用者が入れた繰返数 3 が戻る
    assert _repeat_count(db, before['0.ports.0']) == ('0', 3)
    assert len(_active(db, TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _discarded(db, TABLE_NESTVAR_MEMBER_MAX_COL) == []
    # 多段変数配列組合せ管理: 配列側の欄が繰返数 3 に合わせて 3 つ。辞書側の欄は廃止
    assert _aliases(db) == ['[0].name', '[0].ports[0].http', '[0].ports[1].http', '[0].ports[2].http']
    http_comb = db.find_row(TABLE_NESTVAR_MEMBER_COL_COMB, COL_COMBINATION_MEMBER_ALIAS='[0].ports[0].http', DISUSE_FLAG='0')
    assert http_comb['ARRAY_MEMBER_ID'] == before['0.ports.0.http']['ARRAY_MEMBER_ID']
    assert _aliases(db, disuse_flag='1') == ['[0].ports.http']


def test_member_added_and_removed_in_playbook(run_backyard):
    """Playbook にメンバーを 1 つ足すとその行と多段変数配列組合せ管理の欄だけ増え、消すとその行と欄だけ廃止される。他の行は無変化

    経緯: Issue #3072
    """
    with_zone_yaml = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
    zone: tokyo
"""
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_YAML)))
    before_members = snapshot_rows(db, TABLE_NESTVAR_MEMBER)

    run_backyard(db, _extraction(_nest(with_zone_yaml)))

    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 6
    assert _members_by_path(db)['0.zone']['DISUSE_FLAG'] == '0'
    assert _aliases(db) == ['[0].name', '[0].ports[0].http', '[0].zone']
    unchanged_after_add = []
    for row in db.rows(TABLE_NESTVAR_MEMBER):
        if row['VRAS_NAME_PATH'] != '0.zone':
            unchanged_after_add.append(row)
    assert_rows_unchanged(before_members, unchanged_after_add)

    run_backyard(db, _extraction(_nest(SERVERS_YAML)))

    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 6
    assert _members_by_path(db, disuse_flag='1') .keys() == {'0.zone'}
    assert _aliases(db) == ['[0].name', '[0].ports[0].http']
    assert _aliases(db, disuse_flag='1') == ['[0].zone']


def test_leaf_attribute_change_keeps_repeat_count(run_backyard):
    """末端メンバーの名前だけ変える（name → hostname）と、その行は廃止＋新規登録になるが、配列階層の行は残るので
    利用者が変数ネスト管理で変えた繰返数はそのまま。多段変数配列組合せ管理は旧欄が廃止され新しい欄が登録される

    経緯: Issue #3072
    """
    renamed_yaml = """
VAR_servers:
  - hostname: web01
    ports:
      - http: 80
"""
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_YAML)))
    root_before = _members_by_path(db)['0']
    root_max_col = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=root_before['ARRAY_MEMBER_ID'])
    root_max_col['MAX_COL_SEQ'] = 3

    run_backyard(db, _extraction(_nest(renamed_yaml)))

    after = _members_by_path(db)
    assert sorted(after.keys()) == ['0', '0.hostname', '0.ports', '0.ports.0', '0.ports.0.http']
    assert after['0']['ARRAY_MEMBER_ID'] == root_before['ARRAY_MEMBER_ID']
    assert sorted(_members_by_path(db, disuse_flag='1').keys()) == ['0.name']
    root_max_col_after = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=root_before['ARRAY_MEMBER_ID'])
    assert (root_max_col_after['DISUSE_FLAG'], root_max_col_after['MAX_COL_SEQ']) == ('0', 3)
    assert len(db.rows(TABLE_NESTVAR_MEMBER_MAX_COL)) == 2
    assert _aliases(db) == ['[0].hostname', '[0].ports[0].http', '[1].hostname', '[1].ports[0].http', '[2].hostname', '[2].ports[0].http']
    assert _aliases(db, disuse_flag='1') == ['[0].name']


def test_sample_count_change_rebuilds_array_row(run_backyard):
    """Role の defaults でサンプル配列の要素数だけ変えると（構造は同じ）、配列階層の行が作り直され、
    利用者が変数ネスト管理で変えていた繰返数は新しい行で 1 に戻る。末端メンバーの行と多段変数配列組合せ管理の欄は変わらない

    経緯: Issue #3072
    """
    two_samples_yaml = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
  - name: web02
    ports:
      - http: 80
"""
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest(SERVERS_YAML)))
    before = _members_by_path(db)
    root_max_col = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=before['0']['ARRAY_MEMBER_ID'])
    root_max_col['MAX_COL_SEQ'] = 3
    comb_before = snapshot_rows(db, TABLE_NESTVAR_MEMBER_COL_COMB)

    run_backyard(db, _extraction(_nest(two_samples_yaml)))

    after = _members_by_path(db)
    assert after['0']['ARRAY_MEMBER_ID'] != before['0']['ARRAY_MEMBER_ID']
    assert int(after['0']['MAX_COL_SEQ']) == 2
    for path in ('0.name', '0.ports', '0.ports.0', '0.ports.0.http'):
        assert after[path]['ARRAY_MEMBER_ID'] == before[path]['ARRAY_MEMBER_ID']
    assert sorted(_members_by_path(db, disuse_flag='1').keys()) == ['0']
    old_max_col = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=before['0']['ARRAY_MEMBER_ID'])
    new_max_col = db.find_row(TABLE_NESTVAR_MEMBER_MAX_COL, ARRAY_MEMBER_ID=after['0']['ARRAY_MEMBER_ID'])
    assert (old_max_col['DISUSE_FLAG'], old_max_col['MAX_COL_SEQ']) == ('1', 3)
    assert (new_max_col['DISUSE_FLAG'], new_max_col['MAX_COL_SEQ']) == ('0', 1)
    assert_rows_unchanged(comb_before, db.rows(TABLE_NESTVAR_MEMBER_COL_COMB), ignore_columns=())


def test_flat_only_changes_leave_member_menus_alone(run_backyard):
    """一般変数と複数具体値変数だけの刈取（登録・型変更・廃止）では、多段変数メンバー管理・変数ネスト管理・多段変数配列組合せ管理に行は作られず書き込みも出ない

    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(('VAR_a', ATTR_STD), ('VAR_b', ATTR_LIST)))
    run_backyard(db, _extraction(('VAR_a', ATTR_LIST), ('VAR_c', ATTR_STD)))

    assert db.rows(TABLE_NESTVAR_MEMBER) == []
    assert db.rows(TABLE_NESTVAR_MEMBER_MAX_COL) == []
    assert db.rows(TABLE_NESTVAR_MEMBER_COL_COMB) == []
    for table in (TABLE_NESTVAR_MEMBER, TABLE_NESTVAR_MEMBER_MAX_COL, TABLE_NESTVAR_MEMBER_COL_COMB):
        for call in db.update_calls_for(table) + db.insert_calls_for(table):
            assert call['data_list'] == []
    link_types = {}
    for row in db.rows(TABLE_MVMT_VAR_LINK):
        link_types[row['VARS_NAME']] = (row['VARS_ATTRIBUTE_01'], row['DISUSE_FLAG'])
    assert link_types == {'VAR_a': (ATTR_LIST, '0'), 'VAR_b': (ATTR_LIST, '1'), 'VAR_c': (ATTR_STD, '0')}


def test_role_shared_by_two_movements_registers_members_per_movement(run_backyard):
    """同じ多段変数を 2 つの Movement が持つと、Movement-変数紐付は 2 行、多段変数メンバー管理・変数ネスト管理・多段変数配列組合せ管理はそれぞれの Movement 分が別行で作られる

    経緯: Issue #3072
    """
    db = create_backyard_db()

    run_backyard(db, create_mov_vars_dict({'mv-1': [_nest()], 'mv-2': [_nest()]}))

    assert len(db.rows(TABLE_MVMT_VAR_LINK)) == 2
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 10
    assert len(db.rows(TABLE_NESTVAR_MEMBER_MAX_COL)) == 4
    assert len(db.rows(TABLE_NESTVAR_MEMBER_COL_COMB)) == 4
    for link in db.rows(TABLE_MVMT_VAR_LINK):
        assert len(db.find_rows(TABLE_NESTVAR_MEMBER, MVMT_VAR_LINK_ID=link['MVMT_VAR_LINK_ID'])) == 5
        assert len(db.find_rows(TABLE_NESTVAR_MEMBER_COL_COMB, MVMT_VAR_LINK_ID=link['MVMT_VAR_LINK_ID'])) == 2


def test_empty_extraction_discards_everything(run_backyard):
    """Movement が 1 つも無い（解析結果が空）刈取では、Movement-変数紐付・多段変数メンバー管理・変数ネスト管理・多段変数配列組合せ管理の有効行が全部廃止され、例外は出ない

    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(('VAR_std', ATTR_STD), _nest()))

    run_backyard(db, {})

    for table in (TABLE_MVMT_VAR_LINK, TABLE_NESTVAR_MEMBER, TABLE_NESTVAR_MEMBER_MAX_COL, TABLE_NESTVAR_MEMBER_COL_COMB):
        assert _active(db, table) == [], table
    assert len(_discarded(db, TABLE_MVMT_VAR_LINK)) == 2
    assert len(_discarded(db, TABLE_NESTVAR_MEMBER)) == 5


def test_failure_in_link_stage_stops_before_member_stage(run_backyard):
    """Movement-変数紐付の登録で DB 書き込みが失敗すると、多段変数メンバー管理以降は実行されず、コミットも呼ばれない（切断だけ行われる）。実行済みフラグも立たない

    経緯: Issue #2618 / #3072
    """
    from common_libs.common.exception import AppException

    db = create_backyard_db()
    run_backyard(db, _extraction(('VAR_old', ATTR_STD)))
    db.committed = 0
    db.disconnected = 0
    db.insert_calls.clear()
    db.update_calls.clear()
    # 2 回目の刈取で走る INSERT は Role 名管理 → Movement-変数紐付の順。Movement-変数紐付の INSERT（2 回目）を失敗させる
    db.fail_insert_on_call = 2

    with pytest.raises(AppException) as raised:
        run_backyard(db, _extraction(('VAR_old', ATTR_STD), _nest()))

    assert raised.value.args[0] == 'BKY-30003'
    assert db.insert_calls_for(TABLE_NESTVAR_MEMBER) == []
    assert db.update_calls_for(TABLE_NESTVAR_MEMBER) == []
    assert db.rows(TABLE_NESTVAR_MEMBER) == []
    assert (db.committed, db.disconnected) == (0, 1)
    assert db.rows('T_COMN_PROC_LOADED_LIST')[0]['LOADED_FLG'] == '0'


def test_discarded_link_is_hidden_from_member_stage(run_backyard):
    """Movement-変数紐付で廃止された変数のメンバー行が有効のまま残っていても（不整合）、Movement-変数紐付の再読込は有効行だけなので
    多段変数メンバー管理はその変数を解析結果に無い扱いにし、メンバー行を廃止する

    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()
    run_backyard(db, _extraction(_nest()))
    run_backyard(db, _extraction())
    for row in db.rows(TABLE_NESTVAR_MEMBER):
        row['DISUSE_FLAG'] = '0'       # 画面から手で復活させた不整合データ

    run_backyard(db, _extraction())

    assert db.rows(TABLE_MVMT_VAR_LINK)[0]['DISUSE_FLAG'] == '1'
    assert _active(db, TABLE_NESTVAR_MEMBER) == []
    assert len(_discarded(db, TABLE_NESTVAR_MEMBER)) == 5


def test_reload_reads_through_same_connection_after_update(run_backyard):
    """Movement-変数紐付の更新と再読込は同じ DB 接続で順に行われ、再読込は自分の書き込みを見る（別接続で見えない、が起きない）

    経緯: Issue #2618 / #3072
    """
    db = create_backyard_db()

    run_backyard(db, _extraction(_nest()))

    log = db.call_log
    link_events = []
    for kind, table in log:
        if table == TABLE_MVMT_VAR_LINK:
            link_events.append(kind)
    # 読込 → 型更新 → 登録 → 復活 → 廃止 → 再読込（全部同じ代役に記録される）
    assert link_events == ['select', 'update', 'insert', 'update', 'update', 'select']
    reloaded_link_id = db.rows(TABLE_NESTVAR_MEMBER)[0]['MVMT_VAR_LINK_ID']
    assert reloaded_link_id == db.rows(TABLE_MVMT_VAR_LINK)[0]['MVMT_VAR_LINK_ID']
