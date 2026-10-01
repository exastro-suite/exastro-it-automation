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

"""テストデータ生成の共通ヘルパー（create_*）

解析結果（mov_vars_dict）と DB の行（T_ANSR_MVMT_VAR_LINK / T_ANSR_NESTVAR_MEMBER ほか）を組み立てる。
テストの意図が read しやすくなるよう、キー構成の知識はここに閉じ込める。

多段変数のメンバー構造は YAML 文字列を本物の解析器（CheckAnsibleRoleFiles.DefaultVarsFileAnalysis）に
渡して生成する（create_chain_array_from_yaml）。手書きの 11 項目辞書が要るときは create_chain_array_item。
"""
import copy
import json

import yaml

# テーブル名
TABLE_MVMT_VAR_LINK = "T_ANSR_MVMT_VAR_LINK"
TABLE_NESTVAR_MEMBER = "T_ANSR_NESTVAR_MEMBER"
TABLE_NESTVAR_MEMBER_MAX_COL = "T_ANSR_NESTVAR_MEMBER_MAX_COL"
TABLE_NESTVAR_MEMBER_COL_COMB = "T_ANSR_NESTVAR_MEMBER_COL_COMB"
TABLE_PROC_LOADED_LIST = "T_COMN_PROC_LOADED_LIST"
TABLE_MOVEMENT = "V_ANSR_MOVEMENT"
TABLE_MVMT_MATL_LINK = "T_ANSR_MVMT_MATL_LINK"
TABLE_ROLE_NAME = "T_ANSR_ROLE_NAME"
TABLE_MATL_COLL = "T_ANSR_MATL_COLL"
TABLE_TEMPLATE_FILE = "T_ANSC_TEMPLATE_FILE"
TABLE_DEVICE = "T_ANSC_DEVICE"

# AnscConst.GC_VARS_ATTR_* と同値（テスト側で意図が読めるように再掲）
ATTR_STD = '1'       # 一般変数
ATTR_LIST = '2'      # 複数具体値
ATTR_M_ARRAY = '3'   # 多段変数

TEST_USER_ID = "test_user_id"
OLD_USER_ID = "old_user_id"
BACKYARD_USER_ID = "20401"          # backyard_main.py:32 が固定で使う実行ユーザ
PROC_LOADED_ROW_ID = 204            # backyard_main.py:34

OLD_TIMESTAMP = '2026-01-01 00:00:00'

# T_ANSR_NESTVAR_MEMBER の INT 列（ita_api_admin/sql/ansible.sql:1595-1614）
MEMBER_INT_COLUMNS = (
    'PARENT_VARS_KEY_ID', 'VARS_KEY_ID', 'ARRAY_NEST_LEVEL',
    'ASSIGN_SEQ_NEED', 'COL_SEQ_NEED', 'MEMBER_DISP', 'MAX_COL_SEQ',
)


def create_variable(var_name, var_attr, var_struct=None):
    """Variable を生成する"""
    from backyard_libs.ansible_driver.classes.VariableClass import Variable

    return Variable(var_name, var_attr, var_struct)


def create_mov_vars_dict(specs):
    """解析結果（backyard_main.py の mov_vars_dict）を組み立てる

    Arguments:
        specs: {movement_id: [(var_name, var_attr[, var_struct]), ...]}
               var_struct の代わりに Variable をそのまま並べてもよい

    Returns:
        {movement_id: VariableManager}
    """
    from backyard_libs.ansible_driver.classes.VariableClass import Variable
    from backyard_libs.ansible_driver.classes.VariableManagerClass import VariableManager

    mov_vars_dict = {}
    for movement_id, var_specs in specs.items():
        varmng = VariableManager()
        for var_spec in var_specs:
            if isinstance(var_spec, Variable):
                varmng.add_variable(var_spec)
                continue
            var_name, var_attr = var_spec[0], var_spec[1]
            var_struct = var_spec[2] if len(var_spec) > 2 else None
            varmng.add_variable(create_variable(var_name, var_attr, var_struct))
        mov_vars_dict[movement_id] = varmng

    return mov_vars_dict


def create_link_row(link_id, movement_id, vars_name, var_attr, disuse_flag='0', note='initial note'):
    """T_ANSR_MVMT_VAR_LINK の 1 行を組み立てる

    NOTE は「更新対象外のカラムが巻き戻らない/書き換わらないこと」を検証するための番人。
    """
    return {
        'MVMT_VAR_LINK_ID': link_id,
        'MOVEMENT_ID': movement_id,
        'VARS_NAME': vars_name,
        'VARS_ATTRIBUTE_01': var_attr,
        'NOTE': note,
        'DISUSE_FLAG': disuse_flag,
        'LAST_UPDATE_USER': OLD_USER_ID,
        'LAST_UPDATE_TIMESTAMP': OLD_TIMESTAMP,
    }


def create_chain_array_item(vars_key_id, vars_name, parent_vars_key_id='0', array_nest_level='1',
                            assign_seq_need='0', col_seq_member='0', col_seq_need='0',
                            member_disp='1', max_col_seq='0', vars_name_path=None, vars_name_alias=None):
    """Variable.var_struct['CHAIN_ARRAY'] の 1 要素を組み立てる

    キー構成は CheckAnsibleRoleFiles.MakeMultiArrayToLastVarChainArray() の生成物に合わせている。
    MVMT_VAR_LINK_ID は NestVarsMemberTable が付与するのでここには含めない。
    """
    return {
        'PARENT_VARS_KEY_ID': parent_vars_key_id,
        'VARS_KEY_ID': vars_key_id,
        'VARS_NAME': vars_name,
        'ARRAY_NEST_LEVEL': array_nest_level,
        'ASSIGN_SEQ_NEED': assign_seq_need,
        'COL_SEQ_MEMBER': col_seq_member,
        'COL_SEQ_NEED': col_seq_need,
        'MEMBER_DISP': member_disp,
        'VRAS_NAME_PATH': vars_name_path if vars_name_path is not None else f"path/{vars_name}",
        'VRAS_NAME_ALIAS': vars_name_alias if vars_name_alias is not None else f"alias_{vars_name}",
        'MAX_COL_SEQ': max_col_seq,
    }


def create_nest_var_struct(member_names=('member1',)):
    """多段変数の var_struct を組み立てる（平坦なメンバーだけの簡易版）"""
    chain_array = []
    for idx, member_name in enumerate(member_names):
        chain_array.append(create_chain_array_item(vars_key_id=str(idx + 1), vars_name=member_name))
    return {'CHAIN_ARRAY': chain_array}


def create_member_row(member_id, link_id, chain_array_item, disuse_flag='0'):
    """T_ANSR_NESTVAR_MEMBER の 1 行を、対応する CHAIN_ARRAY 要素から組み立てる（値の型はそのまま）"""
    row = dict(chain_array_item)
    row.pop('COL_SEQ_MEMBER', None)
    row['ARRAY_MEMBER_ID'] = member_id
    row['MVMT_VAR_LINK_ID'] = link_id
    row['DISUSE_FLAG'] = disuse_flag
    row['LAST_UPDATE_USER'] = OLD_USER_ID
    row['LAST_UPDATE_TIMESTAMP'] = OLD_TIMESTAMP
    return row


def create_mov_vars_link_table(dummy_db, link_rows):
    """MovementVarsLinkTable を DB 状態込みで用意する（backyard_main.py:68-69 と同じ読み方）"""
    from backyard_libs.ansible_driver.classes.MovementVarsLinkTableClass import MovementVarsLinkTable

    dummy_db.rows_by_table[TABLE_MVMT_VAR_LINK] = copy.deepcopy(link_rows)
    table = MovementVarsLinkTable(dummy_db)
    table.store_dbdata_in_memory(contain_disused_data=True)
    return table


def create_nest_vars_member_table(dummy_db, member_rows):
    """NestVarsMemberTable を DB 状態込みで用意する（backyard_main.py:71-72 と同じ読み方）"""
    from backyard_libs.ansible_driver.classes.NestVarsMemberTableClass import NestVarsMemberTable

    dummy_db.rows_by_table[TABLE_NESTVAR_MEMBER] = copy.deepcopy(member_rows)
    table = NestVarsMemberTable(dummy_db)
    table.store_dbdata_in_memory(contain_disused_data=True)
    return table


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# YAML → 解析結果（本物の解析器を使う）
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def _collect_array_counts(node, path, counts):
    """YAML の構造を歩いて、配列階層の階層パス → 要素数 を集める

    解析器（CheckAnsibleRoleFiles.py:2417-2431）が具体値解析の途中で作る array_col_count_list と同じ形。
    """
    if isinstance(node, list):
        key = '0' if not path else f"{path}.0"
        if key not in counts:
            counts[key] = len(node)
        for item in node:
            _collect_array_counts(item, key, counts)
    elif isinstance(node, dict):
        for child_name, child in node.items():
            child_path = child_name if not path else f"{path}.{child_name}"
            _collect_array_counts(child, child_path, counts)


def create_chain_array_from_yaml(yaml_text):
    """多段変数 1 つ分の YAML から、解析結果のメンバー一覧（CHAIN_ARRAY）を本物の解析器で作る

    YAML の最上位キーが変数名。戻り値の各要素は解析器の生成物そのまま（定義順・階層などは int）。

    Returns:
        (var_name, chain_array, body)  body は YAML の変数本体（DIFF_ARRAY 相当）
    """
    from common_libs.ansible_driver.classes.CheckAnsibleRoleFiles import DefaultVarsFileAnalysis

    struct = yaml.safe_load(yaml_text)
    assert len(struct) == 1, "YAML には多段変数を 1 つだけ書く"
    var_name = list(struct.keys())[0]
    body = struct[var_name]

    counts = {}
    _collect_array_counts(body, '', counts)

    analyzer = DefaultVarsFileAnalysis(None)
    ret, first_chain, error_code, line, _, _, _ = analyzer.MakeMultiArrayToFirstVarChainArray(
        False, "", "", body, {}, "", "", 0, 0, 0, 0, 0
    )
    assert ret, f"解析失敗: {error_code} line={line}"
    ret, chain_array, error_code, line = analyzer.MakeMultiArrayToLastVarChainArray(first_chain, counts, [], "", "")
    assert ret, f"解析失敗: {error_code} line={line}"

    return var_name, chain_array, body


def create_nest_variable_from_yaml(yaml_text, var_name=None):
    """YAML から多段変数（Variable, タイプ 3）を作る。var_name を渡すと YAML の変数名を上書きする"""
    yaml_var_name, chain_array, body = create_chain_array_from_yaml(yaml_text)
    if var_name is None:
        var_name = yaml_var_name
    return create_variable(var_name, ATTR_M_ARRAY, {'CHAIN_ARRAY': chain_array, 'DIFF_ARRAY': body})


def create_member_rows_from_chain_array(link_id, chain_array, id_prefix='member', disuse_flag='0'):
    """解析結果のメンバー一覧から、DB から読んだ形の T_ANSR_NESTVAR_MEMBER 行を作る

    列型に揃える（INT 列は int、VARCHAR/TEXT 列は str）。行 ID は f"{id_prefix}-{定義順}"。
    """
    rows = []
    for item in chain_array:
        row = create_member_row(f"{id_prefix}-{item['VARS_KEY_ID']}", link_id, item, disuse_flag)
        rows.append(as_db_member_row(row))
    return rows


def as_db_member_row(row):
    """T_ANSR_NESTVAR_MEMBER の 1 行を DB の列型に揃える（INT 列は int、それ以外の値は str）"""
    result = {}
    for column, value in row.items():
        if value is None:
            result[column] = None
        elif column in MEMBER_INT_COLUMNS:
            result[column] = int(value)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            result[column] = str(value)
        else:
            result[column] = value
    return result


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# 変数ネスト管理・多段変数配列組合せ管理と解析工程の入力行
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def create_max_col_row(max_col_id, link_id, member_id, max_col_seq=1, disuse_flag='0'):
    """T_ANSR_NESTVAR_MEMBER_MAX_COL（変数ネスト管理）の 1 行"""
    return {
        'MAX_COL_SEQ_ID': max_col_id,
        'MVMT_VAR_LINK_ID': link_id,
        'ARRAY_MEMBER_ID': member_id,
        'MAX_COL_SEQ': max_col_seq,
        'DISUSE_FLAG': disuse_flag,
        'LAST_UPDATE_USER': OLD_USER_ID,
        'LAST_UPDATE_TIMESTAMP': OLD_TIMESTAMP,
    }


def create_col_comb_row(comb_id, link_id, member_id, alias, col_seq_value, disuse_flag='0'):
    """T_ANSR_NESTVAR_MEMBER_COL_COMB（多段変数配列組合せ管理）の 1 行"""
    return {
        'COL_SEQ_COMBINATION_ID': comb_id,
        'MVMT_VAR_LINK_ID': link_id,
        'ARRAY_MEMBER_ID': member_id,
        'COL_COMBINATION_MEMBER_ALIAS': alias,
        'COL_SEQ_VALUE': col_seq_value,
        'DISUSE_FLAG': disuse_flag,
        'LAST_UPDATE_USER': OLD_USER_ID,
        'LAST_UPDATE_TIMESTAMP': OLD_TIMESTAMP,
    }


def create_movement_row(movement_id, header_def=None, disuse_flag='0'):
    """V_ANSR_MOVEMENT の 1 行。header_def は Movement の追加オプション（ヘッダーセクション）文字列"""
    return {
        'MOVEMENT_ID': movement_id,
        'MOVEMENT_NAME': f"movement {movement_id}",
        'ANS_PLAYBOOK_HED_DEF': header_def,
        'DISUSE_FLAG': disuse_flag,
    }


def create_matl_link_row(matl_link_id, movement_id, role_pkg_id, role_id, include_seq=1, disuse_flag='0'):
    """T_ANSR_MVMT_MATL_LINK（Movement-Role 紐付）の 1 行"""
    return {
        'MVMT_MATL_LINK_ID': matl_link_id,
        'MOVEMENT_ID': movement_id,
        'ROLE_PACKAGE_ID': role_pkg_id,
        'ROLE_ID': role_id,
        'INCLUDE_SEQ': include_seq,
        'DISUSE_FLAG': disuse_flag,
    }


def create_role_name_row(role_id, role_pkg_id, role_name, disuse_flag='0'):
    """T_ANSR_ROLE_NAME（Role 名管理）の 1 行"""
    return {
        'ROLE_ID': role_id,
        'ROLE_PACKAGE_ID': role_pkg_id,
        'ROLE_NAME': role_name,
        'DISUSE_FLAG': disuse_flag,
        'LAST_UPDATE_USER': OLD_USER_ID,
        'LAST_UPDATE_TIMESTAMP': OLD_TIMESTAMP,
    }


def create_role_pkg_row(role_pkg_id, role_defs, disuse_flag='0'):
    """T_ANSR_MATL_COLL（Role パッケージ管理）の 1 行。解析結果 JSON を role_defs から組む

    Arguments:
        role_defs: {role_name: {'vars': {var_name: 0(一般)/1(複数具体値)},
                                'array_vars': {var_name: yaml_text または var_struct},
                                'tpf_vars': [template_var_name, ...]}}
    """
    role_name_list = []
    vars_list = {}
    array_vars_list = {}
    tpf_vars_list = {}
    for role_name, role_def in role_defs.items():
        role_name_list.append(role_name)
        vars_list[role_name] = dict(role_def.get('vars', {}))

        array_vars_list[role_name] = {}
        for var_name, definition in role_def.get('array_vars', {}).items():
            if isinstance(definition, str):
                _, chain_array, body = create_chain_array_from_yaml(definition)
                definition = {'CHAIN_ARRAY': chain_array, 'DIFF_ARRAY': body}
            array_vars_list[role_name][var_name] = definition

        tpf_vars_list[role_name] = {}
        if role_def.get('tpf_vars'):
            file_vars = {}
            for tpf_var_name in role_def['tpf_vars']:
                file_vars[tpf_var_name] = 0
            tpf_vars_list[role_name] = {'tasks/main.yml': {'1': file_vars}}

    var_struct = {
        'Role_name_list': role_name_list,
        'Vars_list': vars_list,
        'Array_vars_list': array_vars_list,
        'TPF_vars_list': tpf_vars_list,
    }
    return {
        'ROLE_PACKAGE_ID': role_pkg_id,
        'ROLE_PACKAGE_NAME': f"package {role_pkg_id}",
        'VAR_STRUCT_ANAL_JSON_STRING': json.dumps(var_struct),
        'DISUSE_FLAG': disuse_flag,
    }


def create_template_row(template_id, tpl_var_name, vars_list=None, array_vars=None, disuse_flag='0'):
    """T_ANSC_TEMPLATE_FILE（テンプレート管理）の 1 行"""
    array_vars_list = {}
    for var_name, definition in (array_vars or {}).items():
        if isinstance(definition, str):
            _, chain_array, body = create_chain_array_from_yaml(definition)
            definition = {'CHAIN_ARRAY': chain_array, 'DIFF_ARRAY': body}
        array_vars_list[var_name] = definition
    var_struct = {'Vars_list': dict(vars_list or {}), 'Array_vars_list': array_vars_list}
    return {
        'ANS_TEMPLATE_ID': template_id,
        'ANS_TEMPLATE_VARS_NAME': tpl_var_name,
        'VAR_STRUCT_ANAL_JSON_STRING': json.dumps(var_struct),
        'DISUSE_FLAG': disuse_flag,
    }


def create_proc_loaded_row(loaded_flg='0'):
    """T_COMN_PROC_LOADED_LIST の当バックヤードの行（実行要否フラグ）"""
    return {'ROW_ID': PROC_LOADED_ROW_ID, 'LOADED_FLG': loaded_flg}


# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
# 通し（backyard_main を本物のまま動かす）
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

def create_backyard_db(rows_by_table=None):
    """刈取メイン処理を通すための DummyDB を作る（全テーブルの行は深いコピー。実行要否フラグの行は自動で入れる）"""
    from tests.dummy_db import DummyDB

    rows_by_table = copy.deepcopy(rows_by_table) if rows_by_table else {}
    rows_by_table.setdefault(TABLE_PROC_LOADED_LIST, [create_proc_loaded_row()])
    return DummyDB(rows_by_table)


def run_backyard_main(monkeypatch, dummy_db, mov_vars_dict=None, reset_loaded_flag=True):
    """刈取メイン処理（backyard_main.backyard_main）を本物のまま 1 回実行する

    差し替えるのは 3 点だけ:
      - DB 接続 → dummy_db
      - パラメータシート参照工程（util.extract_variable_for_execute）→ 素通し（DB のパラメータシートを要するため）
      - 解析工程（util.extract_variable_for_movement）→ mov_vars_dict を渡した場合だけ、それを返す関数

    reset_loaded_flag=True のとき、実行前に実行要否フラグを「未実行」に戻す
    （本番では関連メニューの更新で戻る。2 回目以降の刈取を回すのに必要）。
    例外はそのまま呼び出し元へ伝える（Movement-変数紐付で書き込みが失敗したとき、多段変数メンバー管理以降に進まずコミットもされないことの確認に使う）。
    """
    import backyard_main
    from backyard_libs.ansible_driver.functions import util

    if reset_loaded_flag:
        for row in dummy_db.rows(TABLE_PROC_LOADED_LIST):
            if row.get('ROW_ID') == PROC_LOADED_ROW_ID:
                row['LOADED_FLG'] = '0'

    def _connect(workspace_id):
        return dummy_db

    def _pass_through_execute(mov_vars, tpl_varmng_dict, device_varmng_dict, ws_db):
        return mov_vars

    monkeypatch.setattr(backyard_main, 'DBConnectWs', _connect)
    monkeypatch.setattr(util, 'extract_variable_for_execute', _pass_through_execute)

    if mov_vars_dict is not None:
        def _prepared_extraction(mov_records, mov_matl_lnk_records, registerd_role_records, role_varmgr_dict, ws_db):
            return mov_vars_dict

        monkeypatch.setattr(util, 'extract_variable_for_movement', _prepared_extraction)

    backyard_main.backyard_main('test_org', 'test_workspace')


def snapshot_rows(dummy_db, table_name):
    """テーブルの全行を退避する（深いコピー）"""
    return copy.deepcopy(dummy_db.rows(table_name))


def assert_rows_unchanged(before_rows, after_rows, ignore_columns=('LAST_UPDATE_TIMESTAMP',)):
    """件数と、ignore_columns 以外の全カラムが一致することを確認する（順序は主キー無関係に集合として比較）"""
    assert len(before_rows) == len(after_rows), f"件数が変わった: {len(before_rows)} -> {len(after_rows)}"

    def _strip(rows):
        stripped = []
        for row in rows:
            item = {}
            for column, value in row.items():
                if column in ignore_columns:
                    continue
                item[column] = value
            stripped.append(item)
        return stripped

    before_stripped = _strip(before_rows)
    for after_row in _strip(after_rows):
        assert after_row in before_stripped, f"刈取前に無い行がある: {after_row}"


def create_active_link_records(link_rows):
    """Movement-変数紐付の確定結果（再読込＝有効行のみ）を、多段変数メンバー管理が受け取る形 {MVMT_VAR_LINK_ID: row} にする"""
    records = {}
    for row in link_rows:
        if row['DISUSE_FLAG'] != '0':
            continue
        records[row['MVMT_VAR_LINK_ID']] = copy.deepcopy(row)
    return records
