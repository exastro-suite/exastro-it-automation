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

"""解析工程（Role パッケージの解析結果 JSON・Movement-Role 紐付・Movement の追加オプションから変数を取り出す）も本物で動かし、
複数 Movement・複数 Role・同名変数の扱いを Movement-変数紐付・多段変数メンバー管理の最終状態で確認する（解析からの通し）

経緯: Issue #3072
"""
from tests.common import (
    ATTR_STD, ATTR_LIST, ATTR_M_ARRAY,
    TABLE_MVMT_VAR_LINK, TABLE_NESTVAR_MEMBER, TABLE_MOVEMENT, TABLE_MVMT_MATL_LINK, TABLE_ROLE_NAME, TABLE_MATL_COLL,
    create_backyard_db, create_movement_row, create_matl_link_row, create_role_name_row, create_role_pkg_row,
)


SERVERS_YAML = """
VAR_servers:
  - name: web01
    ports:
      - http: 80
"""

PKG = 'pkg-1'


def _db(role_defs, movements, links):
    """Role パッケージ 1 つ・Movement・Movement-Role 紐付 から通し用 DB を組む

    Arguments:
        role_defs: create_role_pkg_row の role_defs
        movements: [(movement_id, header_def, disuse_flag), ...]
        links: [(movement_id, role_name), ...]
    """
    role_rows = []
    role_ids = {}
    for idx, role_name in enumerate(role_defs.keys()):
        role_id = f"role-{idx + 1}"
        role_ids[role_name] = role_id
        role_rows.append(create_role_name_row(role_id, PKG, role_name))

    movement_rows = []
    for movement_id, header_def, disuse_flag in movements:
        movement_rows.append(create_movement_row(movement_id, header_def, disuse_flag))

    link_rows = []
    for idx, (movement_id, role_name) in enumerate(links):
        link_rows.append(create_matl_link_row(f"matl-{idx + 1}", movement_id, PKG, role_ids[role_name], include_seq=idx + 1))

    return create_backyard_db({
        TABLE_MATL_COLL: [create_role_pkg_row(PKG, role_defs)],
        TABLE_ROLE_NAME: role_rows,
        TABLE_MOVEMENT: movement_rows,
        TABLE_MVMT_MATL_LINK: link_rows,
    })


def _link_types(db):
    """{(Movement, 変数名): (タイプ, 廃止フラグ)}"""
    result = {}
    for row in db.rows(TABLE_MVMT_VAR_LINK):
        result[(row['MOVEMENT_ID'], row['VARS_NAME'])] = (row['VARS_ATTRIBUTE_01'], row['DISUSE_FLAG'])
    return result


def test_same_variable_name_in_two_movements_are_separate_rows(run_backyard):
    """別の Movement が別の Role を使い、その Role に同名でタイプの違う変数があると、Movement-変数紐付は Movement ごとに別行で別タイプになる

    経緯: Issue #2618 / #3072
    """
    db = _db(
        {'role_flat': {'vars': {'VAR_x': 0}}, 'role_nest': {'array_vars': {'VAR_x': SERVERS_YAML.replace('VAR_servers', 'VAR_x')}}},
        [('mv-1', None, '0'), ('mv-2', None, '0')],
        [('mv-1', 'role_flat'), ('mv-2', 'role_nest')],
    )

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_x'): (ATTR_STD, '0'), ('mv-2', 'VAR_x'): (ATTR_M_ARRAY, '0')}
    members = db.rows(TABLE_NESTVAR_MEMBER)
    assert len(members) == 5
    link_mv2 = db.find_row(TABLE_MVMT_VAR_LINK, MOVEMENT_ID='mv-2')
    for row in members:
        assert row['MVMT_VAR_LINK_ID'] == link_mv2['MVMT_VAR_LINK_ID']


def test_same_role_in_two_movements_duplicates_members(run_backyard):
    """同じ Role を 2 つの Movement が使うと、Movement-変数紐付は 2 行、多段変数メンバー管理はそれぞれの行 ID 配下に同じメンバー一式が別行で登録される

    経緯: Issue #3072
    """
    db = _db(
        {'role_nest': {'array_vars': {'VAR_servers': SERVERS_YAML}}},
        [('mv-1', None, '0'), ('mv-2', None, '0')],
        [('mv-1', 'role_nest'), ('mv-2', 'role_nest')],
    )

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_servers'): (ATTR_M_ARRAY, '0'), ('mv-2', 'VAR_servers'): (ATTR_M_ARRAY, '0')}
    members_by_link = {}
    for row in db.rows(TABLE_NESTVAR_MEMBER):
        members_by_link.setdefault(row['MVMT_VAR_LINK_ID'], []).append(row['VRAS_NAME_PATH'])
    assert len(members_by_link) == 2
    for paths in members_by_link.values():
        assert sorted(paths) == ['0', '0.name', '0.ports', '0.ports.0', '0.ports.0.http']


def test_same_variable_same_structure_in_two_roles_is_one_row(run_backyard):
    """同一 Movement の 2 つの Role に同名・同じ構造の変数（一般変数同士、多段変数同士）があると、1 つに統合され Movement-変数紐付は 1 行

    経緯: Issue #3072
    """
    db = _db(
        {
            'role_a': {'vars': {'VAR_flat': 0}, 'array_vars': {'VAR_servers': SERVERS_YAML}},
            'role_b': {'vars': {'VAR_flat': 0}, 'array_vars': {'VAR_servers': SERVERS_YAML}},
        },
        [('mv-1', None, '0')],
        [('mv-1', 'role_a'), ('mv-1', 'role_b')],
    )

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_flat'): (ATTR_STD, '0'), ('mv-1', 'VAR_servers'): (ATTR_M_ARRAY, '0')}
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 5


def test_same_variable_different_structure_takes_first_role(run_backyard):
    """同一 Movement の 2 つの Role に同名・別構造の変数（一般変数と多段変数）があると、先に統合された Role の変数が採用され Movement-変数紐付は 1 行

    後の Role の変数には内部で「使用不可」の印が付くが刈取はその印を見ない。意図された仕様か未確認（現状挙動を固定）。
    経緯: Issue #3072（現状挙動を固定）
    """
    db = _db(
        {'role_flat': {'vars': {'VAR_x': 0}}, 'role_nest': {'array_vars': {'VAR_x': SERVERS_YAML.replace('VAR_servers', 'VAR_x')}}},
        [('mv-1', None, '0')],
        [('mv-1', 'role_flat'), ('mv-1', 'role_nest')],
    )

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_x'): (ATTR_STD, '0')}
    assert db.rows(TABLE_NESTVAR_MEMBER) == []


def test_header_option_variable_yields_to_role_variable(run_backyard):
    """Movement の追加オプション（ヘッダーセクション）に Role 変数と同名の変数があっても、Role 側の定義（多段変数）が優先される

    経緯: Issue #3072
    """
    header = "- hosts: all\n  vars:\n    servers: {{ VAR_servers }}\n"
    db = _db(
        {'role_nest': {'array_vars': {'VAR_servers': SERVERS_YAML}}},
        [('mv-1', header, '0')],
        [('mv-1', 'role_nest')],
    )

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_servers'): (ATTR_M_ARRAY, '0')}
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 5


def test_header_only_variable_is_registered_as_standard(run_backyard):
    """Movement の追加オプションにだけ現れる変数は一般変数として Movement-変数紐付に登録される

    経緯: Issue #3072
    """
    header = "- hosts: all\n  vars:\n    opt: {{ VAR_option }}\n"
    db = _db(
        {'role_a': {'vars': {'VAR_role': 0}}},
        [('mv-1', header, '0')],
        [('mv-1', 'role_a')],
    )

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_role'): (ATTR_STD, '0'), ('mv-1', 'VAR_option'): (ATTR_STD, '0')}


def test_role_linked_twice_to_movement_registers_once(run_backyard):
    """同じ Role が同一 Movement に 2 回紐付いていても、変数は名前で重複が排除され Movement-変数紐付は 1 行

    経緯: Issue #3072
    """
    db = _db(
        {'role_nest': {'vars': {'VAR_flat': 1}, 'array_vars': {'VAR_servers': SERVERS_YAML}}},
        [('mv-1', None, '0')],
        [('mv-1', 'role_nest'), ('mv-1', 'role_nest')],
    )

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_flat'): (ATTR_LIST, '0'), ('mv-1', 'VAR_servers'): (ATTR_M_ARRAY, '0')}
    assert len(db.rows(TABLE_NESTVAR_MEMBER)) == 5


def test_template_variable_is_registered_as_standard(run_backyard):
    """Role がテンプレート変数を使っていると、テンプレート管理に登録された変数が一般変数として Movement-変数紐付に取り込まれる

    経緯: Issue #3072
    """
    from tests.common import TABLE_TEMPLATE_FILE, create_template_row

    db = _db(
        {'role_a': {'vars': {'VAR_role': 0}, 'tpf_vars': ['TPF_conf']}},
        [('mv-1', None, '0')],
        [('mv-1', 'role_a')],
    )
    db.rows_by_table[TABLE_TEMPLATE_FILE] = [create_template_row('tpl-1', 'TPF_conf', vars_list={'VAR_from_template': 0})]

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_role'): (ATTR_STD, '0'), ('mv-1', 'VAR_from_template'): (ATTR_STD, '0')}


def test_link_to_discarded_movement_is_ignored(run_backyard):
    """Movement 自体が廃止されていると、その Movement-Role 紐付は無視され、その Movement の Movement-変数紐付の既存行は解析結果に無いので全部廃止される

    経緯: Issue #3072
    """
    db = _db(
        {'role_a': {'vars': {'VAR_x': 0}}},
        [('mv-1', None, '0'), ('mv-2', None, '0')],
        [('mv-1', 'role_a'), ('mv-2', 'role_a')],
    )
    run_backyard(db)
    assert _link_types(db) == {('mv-1', 'VAR_x'): (ATTR_STD, '0'), ('mv-2', 'VAR_x'): (ATTR_STD, '0')}
    db.find_row(TABLE_MOVEMENT, MOVEMENT_ID='mv-2')['DISUSE_FLAG'] = '1'

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_x'): (ATTR_STD, '0'), ('mv-2', 'VAR_x'): (ATTR_STD, '1')}


def test_movement_without_role_link_discards_its_variables(run_backyard):
    """Movement は有効だが Role 紐付が 0 件になると、その Movement の解析結果は空になり Movement-変数紐付の既存行は全部廃止される

    経緯: Issue #3072
    """
    db = _db(
        {'role_a': {'vars': {'VAR_x': 0}}},
        [('mv-1', None, '0'), ('mv-2', None, '0')],
        [('mv-1', 'role_a'), ('mv-2', 'role_a')],
    )
    run_backyard(db)
    remaining_links = []
    for row in db.rows(TABLE_MVMT_MATL_LINK):
        if row['MOVEMENT_ID'] != 'mv-2':
            remaining_links.append(row)
    db.rows_by_table[TABLE_MVMT_MATL_LINK] = remaining_links

    run_backyard(db)

    assert _link_types(db) == {('mv-1', 'VAR_x'): (ATTR_STD, '0'), ('mv-2', 'VAR_x'): (ATTR_STD, '1')}
