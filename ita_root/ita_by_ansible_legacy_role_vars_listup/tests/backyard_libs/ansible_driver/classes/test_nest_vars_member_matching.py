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

"""多段変数メンバー管理への反映を段単体で確認する（メンバーの登録・復活・廃止・定義順更新）

入力は「Movement-変数紐付の確定結果（再読込＝有効行だけの辞書）」「解析結果」「刈取開始時点の多段変数メンバー管理の行（有効／廃止）」。
反映は 登録 → 復活（定義順・親メンバーの取り込み込み）→ 廃止 → 再読込 の順。既存行と解析結果は同一性キー 9 項目で突き合わせる。
定義順（VARS_KEY_ID）と親メンバー（PARENT_VARS_KEY_ID＝親の定義順）は同一性キーに含めず、一致した行に解析結果の値を取り込む。
多段変数の構造は YAML を本物の解析器に通して作る。

経緯: Issue #2618 / #3072
"""
import pytest

from common_libs.common.exception import AppException
from tests.common import (
    ATTR_STD, ATTR_LIST, ATTR_M_ARRAY, TEST_USER_ID, OLD_USER_ID,
    TABLE_NESTVAR_MEMBER,
    create_link_row, create_mov_vars_dict, create_nest_variable_from_yaml, create_chain_array_from_yaml,
    create_member_rows_from_chain_array, create_nest_vars_member_table, create_active_link_records,
)


MOVEMENT = 'mv-1'
LINK_ID = 'link-1'

SERVERS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
"""

# ports の後ろ（同じ階層の末尾）に zone を足す。深さ優先の通し番号なので既存メンバーの定義順は変わらない
SERVERS_WITH_ZONE_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
    zone: tokyo
"""

# ports の上に os を 1 行挿入。ports 以降の定義順がずれる
SERVERS_WITH_OS_YAML = """
VAR_servers:
  - name: web01
    os: linux
    ports:
      - http: 80
"""

# ports の後ろに配列 tags を置いた形。ports の中身を増やすと tags 以降の定義順がずれる
SERVERS_WITH_TAGS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
    tags:
      - env: prod
"""

# ports の中（内側ブロックの末尾）に https を追加
SERVERS_WITH_TAGS_AND_HTTPS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
        https: 443
    tags:
      - env: prod
"""


def _links(*rows):
    return create_active_link_records(list(rows))


def _nest_link(var_attr=ATTR_M_ARRAY, disuse_flag='0'):
    return create_link_row(LINK_ID, MOVEMENT, 'VAR_servers', var_attr, disuse_flag=disuse_flag)


def _extraction(*variables):
    return create_mov_vars_dict({MOVEMENT: list(variables)})


def _nest(yaml_text=SERVERS_YAML):
    return create_nest_variable_from_yaml(yaml_text, 'VAR_servers')


def _stored_rows(yaml_text=SERVERS_YAML, disuse_flag='0', link_id=LINK_ID):
    _, chain_array, _ = create_chain_array_from_yaml(yaml_text)
    return create_member_rows_from_chain_array(link_id, chain_array, disuse_flag=disuse_flag)


def _apply(dummy_db, member_rows, link_records, mov_vars_dict):
    table = create_nest_vars_member_table(dummy_db, member_rows)
    table.register_and_discard(mov_vars_dict, link_records)
    return table


def _payloads(dummy_db):
    """多段変数メンバー管理の反映が発行した 登録(INSERT)・復活(UPDATE)・廃止(UPDATE) の data_list を返す"""
    inserts = dummy_db.insert_calls_for(TABLE_NESTVAR_MEMBER)
    updates = dummy_db.update_calls_for(TABLE_NESTVAR_MEMBER)
    assert len(inserts) == 1 and len(updates) == 2
    return inserts[0]['data_list'], updates[0]['data_list'], updates[1]['data_list']


def _paths(rows):
    paths = []
    for row in rows:
        paths.append(str(row['VRAS_NAME_PATH']))     # 解析器は配列階層の階層パスを数値 0 で作る
    return sorted(paths)


def _ids(rows):
    ids = []
    for row in rows:
        ids.append(row['ARRAY_MEMBER_ID'])
    return sorted(ids)


def _row_by_path(rows, path):
    for row in rows:
        if str(row['VRAS_NAME_PATH']) == path:
            return row
    raise AssertionError(f"no row for path {path}")


def test_new_nest_variable_members_are_registered_under_link_id(mock_g, dummy_db):
    """新しい多段変数のメンバー全件が、Movement-変数紐付で払い出された行 ID に紐付いて登録される。解析結果だけが持つ列順序候補フラグは落とされる

    経緯: Issue #3072
    """
    _apply(dummy_db, [], _links(_nest_link()), _extraction(_nest()))

    register, restore, discard = _payloads(dummy_db)
    assert _paths(register) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http']
    for record in register:
        assert record['MVMT_VAR_LINK_ID'] == LINK_ID
        assert record['DISUSE_FLAG'] == '0'
        assert record['LAST_UPDATE_USER'] == TEST_USER_ID
        assert 'COL_SEQ_MEMBER' not in record
    assert (restore, discard) == ([], [])
    assert len(dummy_db.rows(TABLE_NESTVAR_MEMBER)) == 5


def test_unchanged_members_are_rewritten_with_same_values(mock_g, dummy_db):
    """構成が変わらない多段変数では、登録 0・廃止 0。共通行は全件が同じ値で UPDATE され、更新者は元のまま

    共通行全件の UPDATE は現状仕様として固定する（直すときはこのテストの復活件数の期待値だけを変える）。
    経緯: Issue #3072（現状仕様として固定）
    """
    stored = _stored_rows()
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest()))

    register, restore, discard = _payloads(dummy_db)
    assert (register, discard) == ([], [])
    assert len(restore) == 5
    for record in restore:
        original = _row_by_path(stored, record['VRAS_NAME_PATH'])
        for column, value in original.items():
            assert str(record[column]) == str(value), column
        assert record['LAST_UPDATE_USER'] == OLD_USER_ID


def test_added_member_is_registered_alone(mock_g, dummy_db):
    """Playbook にメンバーを 1 つ足すと、その 1 行だけ登録され、他の行は廃止されない

    経緯: Issue #3072
    """
    _apply(dummy_db, _stored_rows(SERVERS_YAML), _links(_nest_link()), _extraction(_nest(SERVERS_WITH_ZONE_YAML)))

    register, restore, discard = _payloads(dummy_db)
    assert _paths(register) == ['0.zone']
    assert register[0]['MVMT_VAR_LINK_ID'] == LINK_ID
    assert len(restore) == 5
    assert discard == []
    assert len(dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='0')) == 6


def test_removed_member_is_discarded_alone(mock_g, dummy_db):
    """Playbook からメンバーを 1 つ消すと、その 1 行だけ廃止され、他の行は登録も廃止もされない。廃止行の備考は読込時の値のまま

    経緯: Issue #3072
    """
    stored = _stored_rows(SERVERS_WITH_ZONE_YAML)
    _row_by_path(stored, '0.zone')['NOTE'] = 'zone memo'
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest(SERVERS_YAML)))

    register, restore, discard = _payloads(dummy_db)
    assert register == []
    assert len(restore) == 5
    assert _paths(discard) == ['0.zone']
    assert (discard[0]['DISUSE_FLAG'], discard[0]['LAST_UPDATE_USER'], discard[0]['NOTE']) == ('1', TEST_USER_ID, 'zone memo')
    assert _paths(dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='1')) == ['0.zone']


def test_discarded_members_are_restored_without_reinsert(mock_g, dummy_db):
    """廃止していたメンバーが同じ構造で戻ると全行が復活し、新しい行は登録されない

    経緯: Issue #3072
    """
    _apply(dummy_db, _stored_rows(disuse_flag='1'), _links(_nest_link()), _extraction(_nest()))

    register, restore, discard = _payloads(dummy_db)
    assert (register, discard) == ([], [])
    assert len(restore) == 5
    for record in restore:
        assert (record['DISUSE_FLAG'], record['LAST_UPDATE_USER']) == ('0', TEST_USER_ID)
    assert len(dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='0')) == 5
    assert len(dummy_db.rows(TABLE_NESTVAR_MEMBER)) == 5


def test_members_registered_when_variable_becomes_nested(mock_g, dummy_db):
    """一般変数／複数具体値変数だった名前が多段変数になり Movement-変数紐付がタイプ 3 で確定していれば、既存メンバー無しから全件登録される

    Movement-変数紐付のタイプが巻き戻っていると辞書引きで停止する（別テストで確認）。ここはタイプが正しく確定した後の多段変数メンバー管理の振る舞い。
    経緯: Issue #2618 / #3072
    """
    _apply(dummy_db, [], _links(_nest_link()), _extraction(_nest()))

    register, restore, discard = _payloads(dummy_db)
    assert len(register) == 5
    assert (restore, discard) == ([], [])


@pytest.mark.parametrize('flat_attr, stored_flag', [
    pytest.param(ATTR_STD, '0', id='to_std'),
    pytest.param(ATTR_LIST, '0', id='to_list'),
    pytest.param(ATTR_STD, '1', id='to_std_already_discarded'),
])
def test_members_discarded_when_variable_stops_being_nested(mock_g, dummy_db, flat_attr, stored_flag):
    """多段変数だった名前が一般変数／複数具体値変数になると、多段変数メンバー管理の既存メンバーは全部廃止される。備考は残る。
    既に廃止なら値は変わらない（ただし現状は同じ値で UPDATE が流れる。復活側の無変更行と同じ現状仕様）

    経緯: Issue #2618 / #3072（現状仕様として固定）
    """
    stored = _stored_rows(disuse_flag=stored_flag)
    stored[0]['NOTE'] = 'member memo'
    _apply(dummy_db, stored, _links(_nest_link(var_attr=flat_attr)), _extraction(('VAR_servers', flat_attr)))

    register, restore, discard = _payloads(dummy_db)
    assert (register, restore) == ([], [])
    assert len(discard) == 5
    assert _row_by_path(discard, '0')['NOTE'] == 'member memo'
    for record in discard:
        assert record['DISUSE_FLAG'] == '1'
        assert record['LAST_UPDATE_USER'] == (TEST_USER_ID if stored_flag == '0' else OLD_USER_ID)
    assert dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='0') == []


@pytest.mark.parametrize('link_rows', [
    pytest.param([], id='link_discarded_and_reloaded_out'),
    pytest.param([create_link_row(LINK_ID, MOVEMENT, 'VAR_servers', ATTR_M_ARRAY, disuse_flag='1')], id='link_discarded_but_passed'),
])
def test_members_discarded_when_link_row_is_missing_or_discarded(mock_g, dummy_db, link_rows):
    """Movement-変数紐付の行が廃止された（再読込で多段変数メンバー管理に渡らない）変数のメンバーは、解析結果に無い扱いで全部廃止される。
    Movement-変数紐付が廃止で多段変数メンバー管理が有効のまま残っていた不整合データも同じく廃止される

    経緯: Issue #2618 / #3072
    """
    _apply(dummy_db, _stored_rows(), _links(*link_rows), _extraction())

    register, restore, discard = _payloads(dummy_db)
    assert (register, restore) == ([], [])
    assert len(discard) == 5
    assert dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='0') == []


def test_flat_variables_do_not_touch_member_table(mock_g, dummy_db):
    """一般変数・複数具体値変数だけの刈取では多段変数メンバー管理は何もしない（Movement-変数紐付の辞書を引かないので停止もしない）

    経緯: Issue #2618 / #3072
    """
    _apply(dummy_db, [], _links(
        create_link_row('link-std', MOVEMENT, 'VAR_std', ATTR_STD),
        create_link_row('link-list', MOVEMENT, 'VAR_list', ATTR_LIST),
    ), _extraction(('VAR_std', ATTR_LIST), ('VAR_list', ATTR_STD)))

    assert _payloads(dummy_db) == ([], [], [])


def test_nest_variable_without_members_discards_existing(mock_g, dummy_db):
    """多段変数なのに解析結果のメンバーが 0 件なら、登録 0 で既存メンバーは全部廃止され、例外は出ない

    経緯: Issue #3072
    """
    from tests.common import create_variable
    empty_nest = create_variable('VAR_servers', ATTR_M_ARRAY, {'CHAIN_ARRAY': []})
    _apply(dummy_db, _stored_rows(), _links(_nest_link()), _extraction(empty_nest))

    register, restore, discard = _payloads(dummy_db)
    assert (register, restore) == ([], [])
    assert len(discard) == 5


@pytest.mark.parametrize('column', [
    pytest.param('MVMT_VAR_LINK_ID', id='link_id'),
    pytest.param('VARS_NAME', id='name'),
    pytest.param('ARRAY_NEST_LEVEL', id='level'),
    pytest.param('ASSIGN_SEQ_NEED', id='assign_seq'),
    pytest.param('COL_SEQ_NEED', id='col_seq'),
    pytest.param('MEMBER_DISP', id='disp'),
    pytest.param('VRAS_NAME_PATH', id='path'),
    pytest.param('VRAS_NAME_ALIAS', id='alias'),
    pytest.param('MAX_COL_SEQ', id='max_col'),
])
def test_changed_attribute_makes_new_member(mock_g, dummy_db, column):
    """同一性キー 9 項目のうち 1 つでも既存行と違えば別メンバー扱いになり、旧行は廃止・新行が登録される（更新にはならない）

    定義が違うものは新しい変数として登録し直すのが仕様。
    親メンバー（親の定義順）は同一性キーに含まれないのでここには無い（test_order_change_updates_order_only[parent_order]）。
    経緯: Issue #3072
    """
    stored = _stored_rows()
    target = _row_by_path(stored, '0.ports.0.http')
    if column == 'MVMT_VAR_LINK_ID':
        target[column] = 'link-other'
    elif column in ('VARS_NAME', 'VRAS_NAME_PATH', 'VRAS_NAME_ALIAS'):
        target[column] = target[column] + '_old'
    else:
        target[column] = int(target[column]) + 10

    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest()))

    register, restore, discard = _payloads(dummy_db)
    assert _paths(register) == ['0.ports.0.http']
    assert register[0]['MVMT_VAR_LINK_ID'] == LINK_ID
    assert len(restore) == 4
    assert _ids(discard) == [target['ARRAY_MEMBER_ID']]
    assert discard[0]['DISUSE_FLAG'] == '1'


@pytest.mark.parametrize('path, column, expected', [
    pytest.param('0.name', 'VARS_KEY_ID', '2', id='order'),
    pytest.param('0.ports.0.http', 'PARENT_VARS_KEY_ID', '4', id='parent_order'),
])
def test_order_change_updates_order_only(mock_g, dummy_db, path, column, expected):
    """同一性キーが一致し定義順（または親メンバー＝親の定義順）だけ違うメンバーは、その値が解析結果の値に更新されるだけで登録・廃止は出ない

    親メンバーは #2622 で定義順が同一性キーから外れたのと同じ理由で、#3096 で同一性キーから外した。
    経緯: Issue #2622 / #3072 / #3096
    """
    stored = _stored_rows()
    target = _row_by_path(stored, path)
    target[column] = 9
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest()))

    register, restore, discard = _payloads(dummy_db)
    assert (register, discard) == ([], [])
    assert len(restore) == 5
    assert str(_row_by_path(restore, path)[column]) == expected
    assert _row_by_path(restore, path)['ARRAY_MEMBER_ID'] == target['ARRAY_MEMBER_ID']
    assert _row_by_path(restore, path)['DISUSE_FLAG'] == '0'
    stored_row = dummy_db.find_row(TABLE_NESTVAR_MEMBER, VRAS_NAME_PATH=path)
    assert str(stored_row[column]) == expected


def test_restore_and_order_update_share_one_update(mock_g, dummy_db):
    """廃止していたメンバーが定義順を変えて戻ると、復活と定義順更新が同じ 1 つの UPDATE に入る

    経緯: Issue #3072
    """
    stored = _stored_rows(disuse_flag='1')
    _row_by_path(stored, '0.name')['VARS_KEY_ID'] = 9
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest()))

    register, restore, discard = _payloads(dummy_db)
    assert (register, discard) == ([], [])
    name_record = _row_by_path(restore, '0.name')
    assert (str(name_record['VARS_KEY_ID']), name_record['DISUSE_FLAG'], name_record['LAST_UPDATE_USER']) == ('2', '0', TEST_USER_ID)
    stored_name = dummy_db.find_row(TABLE_NESTVAR_MEMBER, VRAS_NAME_PATH='0.name')
    assert (str(stored_name['VARS_KEY_ID']), stored_name['DISUSE_FLAG']) == ('2', '0')


def test_discarded_member_missing_from_playbook_is_left_alone(mock_g, dummy_db):
    """既に廃止済みのメンバーが Playbook に無くても、廃止フラグ・更新者は書き換わらない
    （現状は同じ値のまま廃止側の UPDATE に載り、更新日時だけ動く）

    経緯: Issue #3072（現状仕様として固定）
    """
    stored = _stored_rows(SERVERS_WITH_ZONE_YAML)
    _row_by_path(stored, '0.zone')['DISUSE_FLAG'] = '1'
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest(SERVERS_YAML)))

    register, restore, discard = _payloads(dummy_db)
    assert register == []
    assert len(restore) == 5
    assert _paths(discard) == ['0.zone']
    assert (discard[0]['DISUSE_FLAG'], discard[0]['LAST_UPDATE_USER']) == ('1', OLD_USER_ID)
    zone = dummy_db.find_row(TABLE_NESTVAR_MEMBER, VRAS_NAME_PATH='0.zone')
    assert (zone['DISUSE_FLAG'], zone['LAST_UPDATE_USER']) == ('1', OLD_USER_ID)


def test_inserting_member_above_updates_children_orders(mock_g, dummy_db):
    """ports の上に os を挿入すると、os だけ登録され、ports は定義順、ports 配下の 2 行は定義順と親メンバーが更新される。廃止は出ない

    子の「親メンバー」（親の定義順）は同一性キーに含まれないので、上位への挿入で番号がずれても配下は同じ行のまま。
    #3096 より前は配下の 2 行が旧行廃止＋新行登録になっていた（#3096 で修正）。
    経緯: Issue #2622 / #3072 / #3096（親メンバーを同一性キーから外し、新挙動を固定）
    """
    stored = _stored_rows(SERVERS_YAML)
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest(SERVERS_WITH_OS_YAML)))

    register, restore, discard = _payloads(dummy_db)
    assert _paths(register) == ['0.os']
    assert (str(_row_by_path(register, '0.os')['VARS_KEY_ID']), str(_row_by_path(register, '0.os')['PARENT_VARS_KEY_ID'])) == ('3', '1')
    assert _paths(restore) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http']
    assert _ids(restore) == _ids(stored)
    assert str(_row_by_path(restore, '0.ports')['VARS_KEY_ID']) == '4'
    assert (str(_row_by_path(restore, '0.ports.0')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0')['PARENT_VARS_KEY_ID'])) == ('5', '4')
    assert (str(_row_by_path(restore, '0.ports.0.http')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0.http')['PARENT_VARS_KEY_ID'])) == ('6', '5')
    assert discard == []
    assert len(dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='0')) == 6
    assert dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='1') == []


def test_removing_member_above_updates_children_orders(mock_g, dummy_db):
    """ports の上にあった os を Playbook から消すと、os だけ廃止され、ports は定義順、ports 配下の 2 行は定義順と親メンバーが
    同じ行のまま更新される。登録は出ない

    上位の削除でも配下の親メンバー（親の定義順）はずれるが、同一性キーに含まれないので配下は同じ行のまま（挿入の逆向き）。
    経緯: Issue #3072 / #3096
    """
    stored = _stored_rows(SERVERS_WITH_OS_YAML)
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest(SERVERS_YAML)))

    register, restore, discard = _payloads(dummy_db)
    assert register == []
    assert _paths(restore) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http']
    kept_ids = []
    for row in stored:
        if str(row['VRAS_NAME_PATH']) != '0.os':
            kept_ids.append(row['ARRAY_MEMBER_ID'])
    assert _ids(restore) == sorted(kept_ids)
    assert str(_row_by_path(restore, '0.ports')['VARS_KEY_ID']) == '3'
    assert (str(_row_by_path(restore, '0.ports.0')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0')['PARENT_VARS_KEY_ID'])) == ('4', '3')
    assert (str(_row_by_path(restore, '0.ports.0.http')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0.http')['PARENT_VARS_KEY_ID'])) == ('5', '4')
    assert _paths(discard) == ['0.os']
    assert discard[0]['DISUSE_FLAG'] == '1'
    assert len(dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='0')) == 5
    assert _paths(dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='1')) == ['0.os']


def test_adding_member_inside_inner_array_updates_following_siblings(mock_g, dummy_db):
    """ports の中（配列の内側）に https を足すと、https だけ登録され、ports 配下の既存 2 行は変わらず、
    ports の後ろに並ぶ tags とその配下 2 行は同じ行のまま定義順と親メンバーが更新される。廃止は出ない

    内側ブロックの末尾への追加でも、そのブロックより後ろに並ぶメンバーの定義順（と配下の親メンバー）はずれる。
    経緯: Issue #3072 / #3096
    """
    stored = _stored_rows(SERVERS_WITH_TAGS_YAML)
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest(SERVERS_WITH_TAGS_AND_HTTPS_YAML)))

    register, restore, discard = _payloads(dummy_db)
    assert _paths(register) == ['0.ports.0.https']
    assert (str(register[0]['VARS_KEY_ID']), str(register[0]['PARENT_VARS_KEY_ID'])) == ('6', '4')
    assert _paths(restore) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http', '0.tags', '0.tags.0', '0.tags.0.env']
    assert _ids(restore) == _ids(stored)
    # ports 側（https より前）は定義順・親メンバーとも変わらない
    assert (str(_row_by_path(restore, '0.ports.0')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0')['PARENT_VARS_KEY_ID'])) == ('4', '3')
    assert (str(_row_by_path(restore, '0.ports.0.http')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0.http')['PARENT_VARS_KEY_ID'])) == ('5', '4')
    # tags 側（https より後）は 1 つずつ後ろにずれる
    assert str(_row_by_path(restore, '0.tags')['VARS_KEY_ID']) == '7'
    assert (str(_row_by_path(restore, '0.tags.0')['VARS_KEY_ID']), str(_row_by_path(restore, '0.tags.0')['PARENT_VARS_KEY_ID'])) == ('8', '7')
    assert (str(_row_by_path(restore, '0.tags.0.env')['VARS_KEY_ID']), str(_row_by_path(restore, '0.tags.0.env')['PARENT_VARS_KEY_ID'])) == ('9', '8')
    assert discard == []
    assert len(dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='0')) == 9
    assert dummy_db.find_rows(TABLE_NESTVAR_MEMBER, DISUSE_FLAG='1') == []


def test_every_level_is_registered(mock_g, dummy_db):
    """配列階層が 3 段（配列の中の配列の中の配列）でも、全メンバーが登録される

    経緯: Issue #3072
    """
    deep_yaml = """
VAR_deep:
  - groups:
      - hosts:
          - name: h1
"""
    variable = create_nest_variable_from_yaml(deep_yaml)
    link = create_link_row(LINK_ID, MOVEMENT, 'VAR_deep', ATTR_M_ARRAY)
    _apply(dummy_db, [], _links(link), _extraction(variable))

    register, _, _ = _payloads(dummy_db)
    assert _paths(register) == ['0', '0.groups', '0.groups.0', '0.groups.0.hosts', '0.groups.0.hosts.0', '0.groups.0.hosts.0.name']


def test_shared_role_registers_members_per_movement(mock_g, dummy_db):
    """同じ Role を 2 つの Movement が使うと、多段変数メンバー管理にはそれぞれの Movement-変数紐付の行 ID 配下に同じメンバー一式が別行で登録される

    経緯: Issue #3072
    """
    links = _links(
        create_link_row('link-mv1', 'mv-1', 'VAR_servers', ATTR_M_ARRAY),
        create_link_row('link-mv2', 'mv-2', 'VAR_servers', ATTR_M_ARRAY),
    )
    mov_vars = create_mov_vars_dict({'mv-1': [_nest()], 'mv-2': [_nest()]})
    _apply(dummy_db, [], links, mov_vars)

    register, _, _ = _payloads(dummy_db)
    assert len(register) == 10
    per_link = {}
    for record in register:
        per_link.setdefault(record['MVMT_VAR_LINK_ID'], []).append(str(record['VRAS_NAME_PATH']))
    assert sorted(per_link.keys()) == ['link-mv1', 'link-mv2']
    assert sorted(per_link['link-mv1']) == sorted(per_link['link-mv2'])


@pytest.mark.parametrize('link_rows', [
    pytest.param([create_link_row(LINK_ID, MOVEMENT, 'VAR_servers', ATTR_STD)], id='type_std'),
    pytest.param([create_link_row(LINK_ID, MOVEMENT, 'VAR_servers', ATTR_LIST)], id='type_list'),
    pytest.param([create_link_row(LINK_ID, MOVEMENT, 'VAR_servers', ATTR_M_ARRAY, disuse_flag='1')], id='discarded'),
])
def test_link_row_not_nested_raises_key_error(mock_g, dummy_db, link_rows):
    """解析結果は多段変数なのに Movement-変数紐付側がタイプ 3 の有効行になっていないと、辞書引きに失敗して処理が止まる（Issue #2618 の症状）

    経緯: Issue #2618
    """
    with pytest.raises(KeyError):
        _apply(dummy_db, [], _links(*link_rows), _extraction(_nest()))


@pytest.mark.parametrize('failing_call, result_code', [
    pytest.param(('insert', 1), 'BKY-30003', id='register'),
    pytest.param(('update', 1), 'BKY-30004', id='restore'),
    pytest.param(('update', 2), 'BKY-30005', id='discard'),
])
def test_db_failure_raises_app_exception(mock_g, dummy_db, failing_call, result_code):
    """登録・復活・廃止の書き込みが失敗すると、段ごとのエラーコードで処理が止まる

    経緯: Issue #3072
    """
    kind, index = failing_call
    if kind == 'update':
        dummy_db.fail_update_on_call = index
    else:
        dummy_db.fail_insert_on_call = index

    with pytest.raises(AppException) as raised:
        _apply(dummy_db, _stored_rows(SERVERS_YAML), _links(_nest_link()), _extraction(_nest(SERVERS_WITH_OS_YAML)))

    assert raised.value.args[0] == result_code


def test_swapping_siblings_updates_orders_of_children_too(mock_g, dummy_db):
    """兄弟メンバー（name と ports）の並びを Playbook で入れ替えると、2 行とも同じメンバーとして定義順だけ更新され、
    ports 配下の 2 行も同じ行のまま定義順と親メンバーが更新される。登録・廃止は出ない

    #3096 より前は ports 配下の 2 行が親メンバーの変化で廃止＋新規登録になっていた（#3096 で修正）。
    経緯: Issue #2622 / #3072
    """
    swapped_yaml = """
VAR_servers:
  - ports:
      - http: 80
    name: web01
"""
    stored = _stored_rows(SERVERS_YAML)
    _apply(dummy_db, stored, _links(_nest_link()), _extraction(_nest(swapped_yaml)))

    register, restore, discard = _payloads(dummy_db)
    assert (register, discard) == ([], [])
    assert _paths(restore) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http']
    assert _ids(restore) == _ids(stored)
    assert str(_row_by_path(restore, '0.ports')['VARS_KEY_ID']) == '2'
    assert str(_row_by_path(restore, '0.name')['VARS_KEY_ID']) == '5'
    assert (str(_row_by_path(restore, '0.ports.0')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0')['PARENT_VARS_KEY_ID'])) == ('3', '2')
    assert (str(_row_by_path(restore, '0.ports.0.http')['VARS_KEY_ID']), str(_row_by_path(restore, '0.ports.0.http')['PARENT_VARS_KEY_ID'])) == ('4', '3')


def test_same_name_under_different_parents_both_registered(mock_g, dummy_db):
    """同名のメンバー（name）が別の親（web と db）の下にあると、階層パスが違うので別行として両方登録される。親メンバーはそれぞれの親の定義順

    経緯: Issue #3072
    """
    yaml_text = """
VAR_servers:
  - web:
      name: w1
    db:
      name: d1
"""
    _apply(dummy_db, [], _links(_nest_link()), _extraction(_nest(yaml_text)))

    register, _, _ = _payloads(dummy_db)
    assert _paths(register) == ['0', '0.db', '0.db.name', '0.web', '0.web.name']
    names = []
    for record in register:
        if record['VARS_NAME'] == 'name':
            names.append((str(record['VRAS_NAME_PATH']), str(record['PARENT_VARS_KEY_ID'])))
    assert sorted(names) == [('0.db.name', '4'), ('0.web.name', '2')]


def test_member_without_col_seq_flag_raises_key_error(mock_g, dummy_db):
    """解析結果のメンバーに列順序候補フラグが無いと（解析器は常に付けるので通常ありえない）、登録時に停止する

    経緯: Issue #3072
    """
    variable = _nest()
    for item in variable.var_struct['CHAIN_ARRAY']:
        item.pop('COL_SEQ_MEMBER')

    with pytest.raises(KeyError):
        _apply(dummy_db, [], _links(_nest_link()), _extraction(variable))


def test_member_without_order_raises_on_match(mock_g, dummy_db):
    """解析結果のメンバーに定義順が無いと、既存行と一致した時点で定義順の取り込みに失敗して停止する（一致しなければ登録される）

    経緯: Issue #3072
    """
    variable = _nest()
    for item in variable.var_struct['CHAIN_ARRAY']:
        item.pop('VARS_KEY_ID')

    with pytest.raises(KeyError):
        _apply(dummy_db, _stored_rows(), _links(_nest_link()), _extraction(variable))


def test_null_var_struct_raises_type_error(mock_g, dummy_db):
    """多段変数なのに構造が None だと停止する（改修前も同じ）

    経緯: Issue #3072
    """
    from tests.common import create_variable
    variable = create_variable('VAR_servers', ATTR_M_ARRAY, None)

    with pytest.raises(TypeError):
        _apply(dummy_db, [], _links(_nest_link()), _extraction(variable))


@pytest.mark.parametrize('present_in_playbook', [
    pytest.param(True, id='present'),
    pytest.param(False, id='absent'),
])
def test_null_disuse_flag_member_is_not_updated(mock_g, dummy_db, present_in_playbook):
    """廃止フラグが空（None）のメンバー行は、Playbook にあっても無くても廃止フラグ・更新者が書き換わらず、再読込（有効行だけ）からも外れる

    経緯: Issue #3072
    """
    stored = _stored_rows(disuse_flag=None)
    variables = []
    if present_in_playbook:
        variables.append(_nest())
    table = _apply(dummy_db, stored, _links(_nest_link()), _extraction(*variables))

    register, restore, discard = _payloads(dummy_db)
    assert register == []
    touched = restore if present_in_playbook else discard
    assert len(touched) == 5
    for record in touched:
        assert (record['DISUSE_FLAG'], record['LAST_UPDATE_USER']) == (None, OLD_USER_ID)
    assert table.get_stored_records() == {}
