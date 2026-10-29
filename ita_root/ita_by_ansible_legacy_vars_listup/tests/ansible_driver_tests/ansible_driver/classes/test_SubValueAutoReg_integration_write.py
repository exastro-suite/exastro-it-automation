#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License")
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
"""
SubValueAutoReg の結合テスト(**登録経路** = `get_data_from_parameter_sheet`)

対象ケース: INT-6〜INT-9、INT-12、INT-15〜INT-17

位置づけ:
  読み取り経路(vars-listup)は test_SubValueAutoReg_integration.py で担保している。
  こちらは ansible-execute が呼ぶ登録経路を実DBで通し、
  **getCMDBdata が返したレコードが代入値管理にそのまま登録されるか**を確認する。
  単体テストは代入値管理への INSERT を一切通していない(WS_DB がモック)。

実ワークスペースを汚さない方法:
  複製した**使い捨てワークスペース**を作ってそこに登録し、最後に DROP DATABASE する
  (subvalue_autoreg_integration_support.py の DisposableWorkspace)。
  ロールバック方式ではなく複製方式にした理由は
    - 「実際にコミットされた結果」を検証できる
    - 途中で例外が出ても実ワークスペースが汚れない
    - ストレージ(FileUploadColumn の実ファイル)も一緒に隔離できる
  ため。

実行方法:
  cd ita_root/ita_by_ansible_legacy_vars_listup
  INTEGRATION_ENABLE=1 poetry run pytest \
      tests/ansible_driver_tests/ansible_driver/classes/test_SubValueAutoReg_integration_write.py -v -s

  既定(`INTEGRATION_ENABLE` 未設定)では skip する。
  ワークスペースの複製に20秒前後かかるため `-s` で進捗を出すことを推奨。

検証対象の (オペレーション, Movement) の決め方:
  環境依存のUUIDをテストに埋め込まないため、**実データから選ぶ**。
  ドライバごとに getCMDBdata を全オペレーション分回し、
  登録対象レコード(STATUS が False でない)が最も多い組を使う。
"""

import os
import re
import uuid
from collections import Counter

import pytest
from flask import g

from .subvalue_autoreg_integration_support import (
    HORIZONTAL,
    VERTICAL,
    DisposableWorkspace,
    disused_ids,
    hostgroup_members,
    hostgroup_split_tables,
    list_workspaces,
    sheet_kinds,
    single_tpf_var,
    skip_or_fail,
    table_input_orders,
    target_from_env,
    vertical_value_orders,
)

pytestmark = pytest.mark.integration

# ドライバ別の登録先。menu_id は FileUploadColumn の格納先パスに現れる
DRIVER_TABLES = {
    'DF_LEGACY_DRIVER_ID': {
        'value_table': 'T_ANSL_VALUE',
        'host_table': 'T_ANSL_TGT_HOST',
        'menu_id': '20207',
        'has_combination': False,
    },
    'DF_PIONEER_DRIVER_ID': {
        'value_table': 'T_ANSP_VALUE',
        'host_table': 'T_ANSP_TGT_HOST',
        'menu_id': '20309',
        'has_combination': False,
    },
    'DF_LEGACY_ROLE_DRIVER_ID': {
        'value_table': 'T_ANSR_VALUE',
        'host_table': 'T_ANSR_TGT_HOST',
        'menu_id': '20409',
        'has_combination': True,
    },
}

# 検証するドライバ。設定が無いドライバは skip 理由付きで一覧に出る
# (Pioneer は代入値自動登録設定が置かれていない環境が多い)。
DRIVER_ATTRS = ['DF_LEGACY_DRIVER_ID', 'DF_PIONEER_DRIVER_ID', 'DF_LEGACY_ROLE_DRIVER_ID']


# ======================================================================
# 期待値の組み立て(実装の写しではなく、getCMDBdata の戻りからの変換だけを書く)
# ======================================================================
def _is_registered(record, operation_id=None, movement_id=None):
    """代入値管理に登録されるレコードか。

    実装(:180-196 / :212-226)の判定と同じ:
      - `TABLE_NAME` が無いレコードは対象外
      - `STATUS is False` は対象外
      - `STATUS == 'skip'`(項目なし)は**代入値管理には登録しない**が作業対象ホストには載る
      - 一般変数・複数具体値変数のみ オペレーション/Movement の一致を見る
        (多次元配列変数側は read_val_assign の Movement 絞り込みと
         SELECT文のオペレーション絞り込みに任せていて、ループ内では見ていない)
    """
    if 'TABLE_NAME' not in record or record['STATUS'] is False:
        return False
    if operation_id is not None and record['OPERATION_ID'] != operation_id:
        return False
    if movement_id is not None and record['MOVEMENT_ID'] != movement_id:
        return False
    return True


def _norm_text(value):
    """代入値管理のテキストカラムに入る値へ正規化する(None は '' 扱い)。"""
    if value is None:
        return ''
    return str(value)


def _norm_seq(value):
    """ASSIGN_SEQ(数値カラム)へ正規化する。"""
    if value is None or value == '':
        return None
    return int(value)


def _expected_key(record, has_combination):
    """getCMDBdata のレコードから、登録されるべき代入値管理レコードのキーを作る。

    ファイルの有無で VARS_ENTRY / VARS_ENTRY_FILE が入れ替わる(:680-685)。
    """
    if record['COL_FILEUPLOAD_PATH']:
        vars_entry, vars_entry_file = '', record['VARS_ENTRY']
    else:
        vars_entry, vars_entry_file = record['VARS_ENTRY'], ''
    key = [
        _norm_text(record['SYSTEM_ID']),
        _norm_text(record['MVMT_VAR_LINK_ID']),
        _norm_seq(record['ASSIGN_SEQ']),
        _norm_text(vars_entry),
        _norm_text(vars_entry_file),
        _norm_text(record['SENSITIVE_FLAG']),
    ]
    if has_combination:
        key.append(_norm_text(record.get('COL_SEQ_COMBINATION_ID')))
    return tuple(key)


def _actual_key(row, has_combination):
    """代入値管理の実レコードから、比較用のキーを作る。"""
    key = [
        _norm_text(row['SYSTEM_ID']),
        _norm_text(row['MVMT_VAR_LINK_ID']),
        _norm_seq(row['ASSIGN_SEQ']),
        _norm_text(row['VARS_ENTRY']),
        _norm_text(row['VARS_ENTRY_FILE']),
        _norm_text(row['SENSITIVE_FLAG']),
    ]
    if has_combination:
        key.append(_norm_text(row['COL_SEQ_COMBINATION_ID']))
    return tuple(key)


# ======================================================================
# フィクスチャ
# ======================================================================
def _find_source_workspace():
    """複製元にするワークスペース (organization_id, workspace_id) を決める。"""
    from common_libs.common.dbconnect import DBConnectWs

    from_env = target_from_env()
    if from_env:
        return from_env

    try:
        candidates = list_workspaces()
    except Exception as e:
        skip_or_fail('DBに接続できない: {}'.format(e))

    checked = []
    for org_id, ws_id in candidates:
        g.ORGANIZATION_ID = org_id
        g.WORKSPACE_ID = ws_id
        ws_db = DBConnectWs(ws_id, org_id)
        try:
            settings = 0
            for table_name in ('T_ANSL_VALUE_AUTOREG', 'T_ANSP_VALUE_AUTOREG', 'T_ANSR_VALUE_AUTOREG'):
                # ドライバ未インストールのワークスペースではテーブル自体が無い
                if ws_db.sql_execute("SHOW TABLES LIKE %s", [table_name]):
                    settings += ws_db.table_count(table_name, "WHERE DISUSE_FLAG = '0'")
        finally:
            ws_db.db_disconnect()
        if settings > 0:
            return org_id, ws_id
        checked.append('{}/{}'.format(org_id, ws_id))

    skip_or_fail('代入値自動登録設定のあるワークスペースが見つからない(確認: {})'
                 .format(', '.join(checked) or 'なし'))


@pytest.fixture(scope='module')
def disposable(app_context):
    """複製した使い捨てワークスペースと、そこへの接続を返す。

    後始末(DROP DATABASE / DROP USER / 接続情報の削除 / ストレージ削除)は
    テストが失敗しても必ず実施する。
    """
    org_id, source_ws_id = _find_source_workspace()
    workspace = DisposableWorkspace(org_id, source_ws_id)
    workspace.create()
    print('\n[integration] 使い捨てワークスペースを作成: organization={} 複製元={} → {} (DB={}, '
          'テーブル{}件/ビュー{}件, DB複製{:.1f}秒, ストレージ複製{:.1f}秒)'
          .format(org_id, source_ws_id, workspace.workspace_id, workspace.db_name,
                  workspace.table_count, workspace.view_count,
                  workspace.elapsed['database'], workspace.elapsed['storage']))

    ws_db = workspace.connect()
    yield workspace, ws_db

    ws_db.db_disconnect()
    errors = workspace.drop()
    print('[integration] 使い捨てワークスペースを削除: {}'.format(workspace.workspace_id))
    assert not errors, '使い捨てワークスペースの後始末に失敗した:\n' + '\n'.join(errors)


def _read_records(ws_db, driver_id, operation_id, movement_id):
    """登録経路と同じ手順で getCMDBdata まで実行し、(一般変数, 多次元配列変数) を返す。"""
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

    instance = SubValueAutoReg(driver_id, ws_db)
    null_data_handling = instance.getIFInfoDB(ws_db)[1]['NULL_DATA_HANDLING_FLG']
    ret = instance.read_val_assign(driver_id, ws_db, movement_id)
    if ret[0] is not True or not ret[1]:
        return None, None
    sqls = instance.createQuerySelectCMDB(ret[1], ret[2], ret[3], ws_db)
    if not sqls:
        return None, None
    result = instance.getCMDBdata(sqls, ret[1], ret[2], operation_id, ws_db, null_data_handling)
    return result[0], result[1]


def _register(ws_db, driver_attr):
    """ドライバ1つ分の「対象の決定 → 期待値の算出 → 登録経路の実行」。"""
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

    driver_id = getattr(AnscConst, driver_attr)
    spec = DRIVER_TABLES[driver_attr]

    # 1. 全オペレーション分を読んで、登録対象が最も多い (オペレーション, Movement) を選ぶ
    std_all, array_all = _read_records(ws_db, driver_id, None, None)
    if std_all is None:
        skip_or_fail('ドライバ {} の代入値自動登録設定が無い'.format(driver_id))
    pair_counts = Counter((r['OPERATION_ID'], r['MOVEMENT_ID'])
                          for r in list(std_all) + list(array_all) if _is_registered(r))
    if not pair_counts:
        skip_or_fail('ドライバ {} に登録対象のレコードが無い'.format(driver_id))
    (operation_id, movement_id), _ = pair_counts.most_common(1)[0]

    # 2. 実装と同じ絞り込み(Movement指定で設定を読み、オペレーション指定でSQLを発行)で期待値を作る
    std, array = _read_records(ws_db, driver_id, operation_id, movement_id)
    expected_std = [r for r in std if _is_registered(r, operation_id, movement_id)]
    expected_array = [r for r in array if _is_registered(r)]
    expected_values = [r for r in expected_std + expected_array if r['STATUS'] != 'skip']
    expected_hosts = {(r['OPERATION_ID'], r['MOVEMENT_ID'], _norm_text(r['SYSTEM_ID']))
                      for r in expected_std + expected_array}

    # 3. 登録経路を実行(EXECUTION_NO はテスト実行ごとに一意にして、レコードを特定できるようにする)
    execution_no = 'pytest-{}'.format(uuid.uuid4().hex[:12])
    instance = SubValueAutoReg(driver_id, ws_db)
    assert instance.get_data_from_parameter_sheet(operation_id, movement_id, execution_no) is True

    print('\n[integration] {} 登録: operation={} movement={} 期待レコード={}件 対象ホスト={}件 (候補の組={}種)'.format(
        driver_id, operation_id, movement_id,
        len(expected_values), len(expected_hosts), len(pair_counts)))

    return {
        'driver_id': driver_id,
        'spec': spec,
        'operation_id': operation_id,
        'movement_id': movement_id,
        'execution_no': execution_no,
        'expected_values': expected_values,
        'expected_std': expected_std,
        'expected_array': expected_array,
        'expected_hosts': expected_hosts,
        'pair_counts': pair_counts,
        'ws_db': ws_db,
    }


@pytest.fixture(scope='module')
def registered(disposable):
    """ドライバ名を渡すと、登録済みの状態と期待値を返すファクトリ。

    同じドライバは1回だけ登録する(登録経路の実行は重いため)。
    """
    _, ws_db = disposable
    cache = {}

    def _get(driver_attr):
        if driver_attr not in cache:
            cache[driver_attr] = _register(ws_db, driver_attr)
        return cache[driver_attr]

    return _get


def _rows_of(context):
    """このテスト実行(EXECUTION_NO)で登録された代入値管理レコード。"""
    return context['ws_db'].table_select(
        context['spec']['value_table'], "WHERE EXECUTION_NO = %s", [context['execution_no']])


# ======================================================================
# [INT-6] getCMDBdata のレコードがそのまま代入値管理に登録される
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_registered_values_match_getcmdbdata(registered, driver_attr):
    """INT-6 代入値管理のレコードが getCMDBdata の戻りと1:1で一致する

    単体テストは getCMDBdata の**戻り**までしか見ていない(登録は WS_DB のモック)。
    ここでは実DBに登録された結果を読み直し、
      具体値 / Sensitive / ASSIGN_SEQ / ホスト / 変数(MVMT_VAR_LINK_ID) / 多次元配列の組合せID
    が一致することを多重集合として確認する。
    """
    context = registered(driver_attr)
    has_combination = context['spec']['has_combination']

    rows = _rows_of(context)
    expected = Counter(_expected_key(r, has_combination) for r in context['expected_values'])
    actual = Counter(_actual_key(row, has_combination) for row in rows)

    assert expected, '登録対象のレコードが0件では検証にならない'
    missing = expected - actual
    unexpected = actual - expected
    assert not missing and not unexpected, (
        '{}: 登録内容が getCMDBdata の戻りと一致しない\n未登録: {}\n余分: {}'
        .format(context['spec']['value_table'], list(missing)[:3], list(unexpected)[:3]))


@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_registered_rows_common_columns(registered, driver_attr):
    """INT-6 登録レコードの共通カラム(EXECUTION_NO / DISUSE_FLAG / 更新者 / TPF変数フラグ)"""
    context = registered(driver_attr)
    rows = _rows_of(context)
    assert rows

    for row in rows:
        assert row['EXECUTION_NO'] == context['execution_no']
        assert row['OPERATION_ID'] == context['operation_id']
        assert row['MOVEMENT_ID'] == context['movement_id']
        assert row['DISUSE_FLAG'] == '0'
        assert row['LAST_UPDATE_USER'] == g.USER_ID
        assert row['LAST_UPDATE_TIMESTAMP'] is not None
        assert row['VARS_ENTRY_USE_TPFVARS'] in ('0', '1')


@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_registered_rows_tpf_flag(registered, driver_attr):
    """INT-6 VARS_ENTRY_USE_TPFVARS が「具体値にTPF変数がちょうど1個」と一致する

    実装は `SimpleFillterVerSearch("TPF_", …)` の抽出結果が**ちょうど1件**のときだけ
    `'1'` にする(:692-696 / :752-756)。
    `'1' なら VARS_ENTRY に 'TPF_' を含む` だけの検査では
      - フラグが常に `'0'`(vars-listup の変数刈り取りが丸ごと動かなくなる)
      - TPF変数が2個以上ある行まで `'1'` にする
    をどちらも見逃す。ここでは実装とは別に書き下した `single_tpf_var()` を
    オラクルにして、`'0'`/`'1'` の**両方向**を検査する。

    判定が実装と食い違いうる書き方(`#` のコメント行 / `| filter` / `{% %}`)は
    「判定不能」として除外する(実データを対象にするため、
    仕様の再実装で誤検知を出すより除外して件数を報告する方を選ぶ)。
    フラグの元になるのは**入れ替え前**の `VARS_ENTRY` なので、
    ファイル項目は登録後の `VARS_ENTRY_FILE` 側を見る必要がある。
    """
    context = registered(driver_attr)
    has_combination = context['spec']['has_combination']
    rows = _rows_of(context)
    assert rows

    # 比較キー → 期待フラグ。同じキーで期待値が食い違う場合は判定に使わない
    expected_flag = {}
    conflicted = set()
    undecidable = 0
    for record in context['expected_values']:
        decidable, var_name = single_tpf_var(record['VARS_ENTRY'])
        if not decidable:
            undecidable += 1
            continue
        key = _expected_key(record, has_combination)
        flag = '1' if var_name else '0'
        if expected_flag.setdefault(key, flag) != flag:
            conflicted.add(key)

    checked = 0
    for row in rows:
        key = _actual_key(row, has_combination)
        if key not in expected_flag or key in conflicted:
            continue
        checked += 1
        assert row['VARS_ENTRY_USE_TPFVARS'] == expected_flag[key], (
            'VARS_ENTRY_USE_TPFVARS が具体値と合わない(具体値={!r} 期待={} 実際={})'
            .format(_norm_text(row['VARS_ENTRY']) or _norm_text(row['VARS_ENTRY_FILE']),
                    expected_flag[key], row['VARS_ENTRY_USE_TPFVARS']))

    if not checked:
        skip_or_fail('TPF変数の有無を判定できる具体値が無い(判定不能 {}件)'.format(undecidable))

    # TPF変数を1個だけ含む具体値があるなら、'1' が立った行が実際に存在すること
    if '1' in expected_flag.values():
        assert any(row['VARS_ENTRY_USE_TPFVARS'] == '1' for row in rows), \
            '具体値にTPF変数があるのに VARS_ENTRY_USE_TPFVARS が1件も立っていない'


# ======================================================================
# [INT-7] 作業対象ホスト
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_registered_target_hosts(registered, driver_attr):
    """INT-7 作業対象ホストが (オペレーション, Movement, ホスト) の重複なしで登録される

    代入値管理に登録した組み合わせだけが載る(:276-283)。
    項目なし(`STATUS == 'skip'`)のレコードは代入値管理には載らないが
    作業対象ホストには載るため、期待値は skip も含めて作る。
    """
    context = registered(driver_attr)
    rows = context['ws_db'].table_select(
        context['spec']['host_table'], "WHERE EXECUTION_NO = %s", [context['execution_no']])

    actual = {(row['OPERATION_ID'], row['MOVEMENT_ID'], _norm_text(row['SYSTEM_ID'])) for row in rows}
    assert actual == context['expected_hosts']
    assert len(rows) == len(actual), '作業対象ホストに同じ組み合わせが重複して登録されている'
    for row in rows:
        assert row['DISUSE_FLAG'] == '0'
        assert row['LAST_UPDATE_USER'] == g.USER_ID


# ======================================================================
# [INT-8] 指定した (オペレーション, Movement) 以外は登録されない
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_other_operations_are_not_registered(registered, driver_attr):
    """INT-8 指定外のオペレーション/Movement のレコードは登録されない

    getCMDBdata はオペレーション指定でSQLを絞り(:880-884)、
    さらに登録ループでも オペレーション/Movement の一致を見ている(:186-187)。
    実データに他の組み合わせの候補があることを確認した上で、
    それらが1件も登録されていないことを見る(条件が効いていない場合に検知できる)。
    """
    context = registered(driver_attr)
    if len(context['pair_counts']) < 2:
        skip_or_fail('登録候補の (オペレーション, Movement) が1種類しかないため、絞り込みを検証できない')

    target_pair = (context['operation_id'], context['movement_id'])
    others = [row for row in _rows_of(context)
              if (row['OPERATION_ID'], row['MOVEMENT_ID']) != target_pair]
    assert not others, '指定外の (オペレーション, Movement) が {} 件登録された'.format(len(others))


# ======================================================================
# [INT-9] 多次元配列変数(LegacyRole 固有)
# ======================================================================
def test_role_multidimensional_array_combination(registered):
    """INT-9 多次元配列変数は COL_SEQ_COMBINATION_ID 付きで登録される

    LegacyRole だけが持つカラム(:152-169)。
    多次元配列変数のレコードには組合せIDが入り、一般変数・複数具体値変数には入らない。
    """
    context = registered('DF_LEGACY_ROLE_DRIVER_ID')
    array_records = [r for r in context['expected_array'] if r['STATUS'] != 'skip']
    if not array_records:
        skip_or_fail('多次元配列変数の登録対象レコードが無い')

    rows = _rows_of(context)

    # 組合せIDは「getCMDBdata の戻りに値があるときだけ」コピーされる(:667-669 / :727-729)。
    # 多次元配列変数のレコードだけが持つとは限らないため、
    # 「配列側の件数 = 組合せID付きの件数」ではなく、
    # getCMDBdata の戻りから同じ条件で作った期待値と多重集合で比べる。
    def _combination_ids(records, getter):
        return Counter(value for value in (_norm_text(getter(r)) for r in records) if value)

    expected = _combination_ids(context['expected_values'], lambda r: r.get('COL_SEQ_COMBINATION_ID'))
    actual = _combination_ids(rows, lambda row: row['COL_SEQ_COMBINATION_ID'])
    assert expected, '組合せID付きの登録対象レコードが無い(多次元配列変数が登録されていない)'
    assert actual == expected, (
        'COL_SEQ_COMBINATION_ID の登録内容が getCMDBdata の戻りと一致しない\n未登録: {}\n余分: {}'
        .format(list(expected - actual)[:3], list(actual - expected)[:3]))

    # 多次元配列変数のレコードが持つ組合せIDは、必ず登録済みレコード側にも現れる
    array_ids = {_norm_text(r.get('COL_SEQ_COMBINATION_ID')) for r in array_records}
    array_ids.discard('')
    assert array_ids <= set(actual), \
        '多次元配列変数の組合せID {} が登録されていない'.format(sorted(array_ids - set(actual))[:3])


# ======================================================================
# [INT-12] FileUploadColumn の実ファイル
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_file_upload_column_is_stored(registered, driver_attr):
    """INT-12 FileUploadColumn の具体値はファイル名で登録され、実ファイルが配置される

    `exec_maintenance`(:2018-2052)は
      STORAGEPATH/組織/ワークスペース/uploadfiles/<メニューID>/file/<ASSIGN_ID>/
    に old 配下の実体(`retry_copy2`)とそこへのシンボリックリンク(`retry_symlink`)を作る。
    パスの組み立ては単体テスト §3-6 で、ここでは**実際にファイルが置かれること**を見る。

    「リンクが存在する」「実体が存在する」だけでは
      - リンクの向き先が old 配下の実体でない(リンク切れ / 別ファイルを指す)
      - コピー元と中身が違う(空ファイル・別の具体値のファイル)
    を見逃すので、リンクの解決先と**中身**まで比べる。
    対象データが無い環境では skip する。
    """
    context = registered(driver_attr)
    rows = [row for row in _rows_of(context) if _norm_text(row['VARS_ENTRY_FILE'])]
    if not rows:
        skip_or_fail('FileUploadColumn を代入値自動登録設定に使っているパラメータシートが無い')

    # コピー元(getCMDBdata が返した COL_FILEUPLOAD_PATH)の中身。ファイル名で引ける形にする
    source_bytes = {}
    for record in context['expected_values']:
        org_path = record['COL_FILEUPLOAD_PATH']
        if not org_path or not os.path.isfile(org_path):
            continue
        with open(org_path, 'rb') as fp:
            source_bytes.setdefault(_norm_text(record['VARS_ENTRY']), set()).add(fp.read())

    compared = 0
    for row in rows:
        assert _norm_text(row['VARS_ENTRY']) == '', 'ファイル項目は VARS_ENTRY を空にする'
        base = os.path.join(os.environ['STORAGEPATH'], g.ORGANIZATION_ID, g.WORKSPACE_ID,
                            'uploadfiles', context['spec']['menu_id'], 'file', row['ASSIGN_ID'])
        link_path = os.path.join(base, row['VARS_ENTRY_FILE'])
        real_path = os.path.join(base, 'old', row['ASSIGN_ID'], row['VARS_ENTRY_FILE'])
        assert os.path.islink(link_path), 'シンボリックリンクが無い: {}'.format(link_path)
        assert os.path.isfile(real_path), '実ファイルが無い: {}'.format(real_path)
        assert os.path.realpath(link_path) == os.path.realpath(real_path), \
            'シンボリックリンクが old 配下の実体を指していない: {} → {}'.format(
                link_path, os.path.realpath(link_path))

        with open(real_path, 'rb') as fp:
            stored = fp.read()
        candidates = source_bytes.get(_norm_text(row['VARS_ENTRY_FILE']))
        if candidates is None:
            # コピー元を特定できない場合(複製元のストレージに実体が無い等)は
            # 少なくとも空ファイルではないことを見る
            assert stored, '配置されたファイルが空: {}'.format(real_path)
            continue
        compared += 1
        assert stored in candidates, \
            '配置されたファイルの中身がコピー元と違う: {}'.format(real_path)

    if not compared:
        skip_or_fail('コピー元のファイル({})を読めないため、中身の一致を検証できない'
                     .format(sorted({_norm_text(r['VARS_ENTRY_FILE']) for r in rows})[:3]))


# ======================================================================
# [INT-15] 廃止済みのオペレーション/機器は登録されない
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_disused_data_is_not_registered(registered, disposable, driver_attr):
    """INT-15 廃止済みオペレーション/機器のレコードは代入値管理に登録されない(独立オラクル)

    INT-6〜INT-9 の期待値はすべて `getCMDBdata` の戻りから作っているので、
    getCMDBdata 側の除外条件が壊れると期待値も一緒に壊れて**一致したまま通る**。
    廃止データの除外は
      - 生成SQL の相関サブクエリ(`DISUSE_FLAG = '0'`。:398-412)
      - getCMDBdata のレコード破棄(MSG-10360 / MSG-10359。:903-920)
    で行われるが、これが外れると廃止済み機器に対する作業実行が起きる。
    ここでは `T_COMN_OPERATION` / `T_ANSC_DEVICE` を直接読んで独立に検査する。
    """
    _, ws_db = disposable
    context = registered(driver_attr)

    rows = _rows_of(context)
    hosts = ws_db.table_select(
        context['spec']['host_table'], "WHERE EXECUTION_NO = %s", [context['execution_no']])
    assert rows, '登録レコードが0件では検証にならない'

    disused_operations, disused_hosts = disused_ids(ws_db)
    if not disused_operations and not disused_hosts:
        skip_or_fail('廃止済みのオペレーション/機器が無いため、廃止データの除外を検証できない'
                     '(投入手順の段階8 を実施すると検証対象になる)')

    bad = sorted({row['OPERATION_ID'] for row in rows + hosts
                  if row['OPERATION_ID'] in disused_operations})
    assert not bad, '廃止済みオペレーション {} が登録された'.format(bad[:3])
    bad = sorted({_norm_text(row['SYSTEM_ID']) for row in rows + hosts
                  if _norm_text(row['SYSTEM_ID']) in disused_hosts})
    assert not bad, '廃止済み機器 {} が登録された'.format(bad[:3])


# ======================================================================
# [INT-16] カラムクラスごとの不変条件
# ======================================================================
# 代入値管理のレコードには「どのカラムクラスの具体値だったか」が残らないため、
# getCMDBdata の戻りの `COL_CLASS`(getFromColumnClassMaster() が
# T_COMN_COLUMN_CLASS から引いたクラス名)と `REG_TYPE`(Value/Key)を
# 比較キー経由で登録レコードに対応づけて検査する。

# 具体値が sensitive として扱われるカラムクラス(マスタの COLUMN_CLASS_ID 8/25/26/34)。
# 実装は COLUMN_CLASS の数値で判定している(:1798)ので、ここはクラス名で持って
# 「実装の写し」にならないようにする。
SENSITIVE_COLUMN_CLASSES = (
    'PasswordColumn',           # 8
    'PasswordIDColumn',         # 25
    'JsonPasswordIDColumn',     # 26
    'MultiPasswordColumn',      # 34
)

# 具体値がファイル名で、実体がストレージに置かれるカラムクラス(同 9/20)。
FILE_COLUMN_CLASSES = (
    'FileUploadColumn',         # 9
    'FileUploadEncryptColumn',  # 20
)

# 具体値に改行を含めないカラムクラス(複数行を許すのは MultiText / Json 系)。
SINGLE_LINE_COLUMN_CLASSES = (
    'SingleTextColumn',
    'NumColumn',
    'FloatColumn',
    'DateTimeColumn',
    'DateColumn',
    'HostInsideLinkTextColumn',
    'IDColumn',
)

# `'{{ 変数名 }}'` に括られた具体値。
#   テンプレート/ファイルの**埋込変数名**を選ぶプルダウン
#   (REF_TABLE_NAME が T_ANSC_TEMPLATE_FILE / T_ANSC_CONTENTS_FILE、
#    REF_COL_NAME が ANS_TEMPLATE_VARS_NAME / CONTENTS_FILE_VARS_NAME)のときだけ
#   実装が括る(:818-822 / :1010-1014 / :1039-1045)。
#   埋込変数名は `TPF_` / `CPF_` 接頭辞で作られる。
WRAPPED_VALUE_PATTERN = re.compile(r"^'\{\{ (.*) \}\}'$", re.DOTALL)
EMBEDDED_VAR_NAME_PATTERN = re.compile(r'^(TPF|CPF)_[A-Za-z0-9_]*$')


def _column_class_violations(col_class, reg_type, vars_entry, vars_entry_file, sensitive_flag):
    """カラムクラスから決まる不変条件に反しているものを列挙する(理由の文字列)。

    ここに書くのは**カラムクラスの仕様から決まる形**だけで、
    getCMDBdata の戻り値そのものは使わない(値の一致は INT-6 の担当)。
    INT-6 の期待値は getCMDBdata の戻りから作っているので、
    getCMDBdata と登録処理が一緒に壊れると一致したまま通ってしまう。
    その穴を「クラスごとに必ず成り立つ形」で塞ぐのがこのケース。

    `REG_TYPE == 'Key'` は具体値ではなく**項目名**を登録する経路(:1218-1247)で、
    sensitive でもファイルでもないため、値の形の検査からは外す。
    """
    violations = []
    is_key = (reg_type == 'Key')

    # 1. sensitive フラグはカラムクラスだけで決まる。
    #    キー型は KEY_SENSITIVE_FLAG が常に OFF(:1796-1799)なので '0'。
    expected_flag = '1' if (not is_key and col_class in SENSITIVE_COLUMN_CLASSES) else '0'
    if sensitive_flag != expected_flag:
        violations.append('SENSITIVE_FLAG が {} (このカラムクラスでは {})'.format(sensitive_flag, expected_flag))

    # 2. sensitive な具体値は**暗号文のまま**代入値管理に入る
    #    (復号は ansible-execute 側で行う)。平文が入っていたら情報漏洩の回帰。
    if sensitive_flag == '1' and vars_entry:
        from common_libs.common.util import ky_decrypt

        decrypted = ky_decrypt(vars_entry)
        if not decrypted:
            violations.append('sensitive な具体値を ENCRYPT_KEY で復号できない(暗号文になっていない): {!r}'
                              .format(vars_entry[:16]))
        elif decrypted == vars_entry:
            violations.append('sensitive な具体値が平文のまま登録されている')

    # 3. ファイル項目とそれ以外の入れ替わり(:680-685 / :740-745)
    if col_class in FILE_COLUMN_CLASSES and not is_key:
        if vars_entry:
            violations.append('ファイル項目なのに VARS_ENTRY に値が入っている: {!r}'.format(vars_entry[:32]))
    elif vars_entry_file:
        violations.append('ファイル項目でないのに VARS_ENTRY_FILE に値が入っている: {!r}'.format(vars_entry_file))

    # 4. 数値カラムは数値として読める(パラメータシート側のバリデーションが効いていること)
    if not is_key and vars_entry:
        if col_class == 'NumColumn':
            try:
                int(vars_entry)
            except ValueError:
                violations.append('整数カラムの具体値が整数でない: {!r}'.format(vars_entry[:32]))
        elif col_class == 'FloatColumn':
            try:
                float(vars_entry)
            except ValueError:
                violations.append('小数カラムの具体値が数値でない: {!r}'.format(vars_entry[:32]))

        # 5. 単一行のカラムに改行が入っていたら、別カラムの値が混ざった疑い
        if col_class in SINGLE_LINE_COLUMN_CLASSES and ('\n' in vars_entry or '\r' in vars_entry):
            violations.append('単一行のカラムクラスなのに改行を含む: {!r}'.format(vars_entry[:32]))

    # 6. `'{{ … }}'` の括りは埋込変数名のときだけ。
    #    ID変換に失敗した値(`ID変換失敗(…)`)は括らずレコードごと捨てる実装なので、
    #    括りの中身が変数名でなければ回帰。
    wrapped = WRAPPED_VALUE_PATTERN.match(vars_entry)
    if wrapped:
        if not EMBEDDED_VAR_NAME_PATTERN.match(wrapped.group(1)):
            violations.append("'{{ … }}' に括られているのが埋込変数名(TPF_/CPF_)ではない: {!r}"
                              .format(wrapped.group(1)[:32]))
    elif col_class == 'IDColumn' and EMBEDDED_VAR_NAME_PATTERN.match(vars_entry):
        violations.append("埋込変数名なのに '{{ … }}' に括られていない: {!r}".format(vars_entry))

    # 7. キー型は項目名が入るので空にならない(:1220-1225 で空はレコードを作らない)
    if is_key and not vars_entry:
        violations.append('キー型の登録なのに VARS_ENTRY が空')

    return violations


@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_registered_values_satisfy_column_class_invariants(registered, driver_attr):
    """INT-16 登録された具体値がカラムクラスごとの不変条件を満たす(独立オラクル)

    INT-6 は「getCMDBdata の戻り == 代入値管理」を見るので、
    **値の作り方そのもの**が壊れると期待値も一緒に壊れて一致したまま通る
    (例: sensitive カラムの平文化、`'{{ }}'` の括り忘れ、
     ファイル名が VARS_ENTRY 側に入る、数値カラムに別カラムの値が入る)。
    ここではカラムクラスの仕様から決まる形だけを書き下し、
    **実DBに登録された値**に対して検査する(`_column_class_violations`)。

    カラムクラスの網羅そのものは投入データ側の責務(tests/README.md の
    段階4・段階7でスクリプトが17項目・11クラスを作る)なので、
    ここでは「観測できたクラスの下限」は縛らず、内訳を出力するだけにしている。
    """
    context = registered(driver_attr)
    has_combination = context['spec']['has_combination']
    rows = _rows_of(context)
    assert rows, '登録レコードが0件では検証にならない'

    # 比較キー → (カラムクラス, 登録種別)。同じキーに別クラスが来たら判定に使わない
    attrs = {}
    conflicted = set()
    for record in context['expected_values']:
        key = _expected_key(record, has_combination)
        attr = (record['COL_CLASS'], record['REG_TYPE'])
        if attrs.setdefault(key, attr) != attr:
            conflicted.add(key)

    observed = Counter()
    undecidable = 0
    violations = []
    for row in rows:
        key = _actual_key(row, has_combination)
        attr = attrs.get(key)
        if attr is None or key in conflicted:
            undecidable += 1
            continue
        col_class, reg_type = attr
        observed[(col_class, reg_type)] += 1
        violations.extend(
            '{}({}) ASSIGN_ID={}: {}'.format(col_class, reg_type, row['ASSIGN_ID'], reason)
            for reason in _column_class_violations(
                col_class, reg_type,
                _norm_text(row['VARS_ENTRY']), _norm_text(row['VARS_ENTRY_FILE']),
                _norm_text(row['SENSITIVE_FLAG'])))

    print('\n[integration] {} カラムクラス別の登録件数(クラス特定不能 {}件): {}'.format(
        context['driver_id'], undecidable,
        ', '.join('{}/{}={}'.format(col_class, reg_type, count)
                  for (col_class, reg_type), count in sorted(observed.items()))))

    if not observed:
        skip_or_fail('カラムクラスを特定できる登録レコードが無い')
    assert not violations, ('カラムクラスの不変条件に反する登録レコードが {}件ある:\n{}'
                            .format(len(violations), '\n'.join(violations[:10])))


# ======================================================================
# [INT-19] 登録経路が Value型 と Key型 の両方を通る
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_registered_rows_cover_value_and_key_registration(registered, driver_attr):
    """INT-19 登録レコードに Value型 由来と Key型 由来の両方が含まれる(投入データの歯止め)

    Key型 は具体値ではなく**カラムの項目名**を変数の値として登録する経路で、
    Value型 とは別のコピー(:1218-1247)。sensitive は常に OFF、
    具体値が空ならそのペアだけ MSG-10377 で捨てる、という Value型 とは違う分岐を持つ。
    したがってあるドライバの設定が Value型 だけだと、
    INT-6 / INT-16 が Key型 を1件も通らず、Key型 側が壊れても全部緑のままになる。

    INT-16 と同じ方法(比較キー → `REG_TYPE`)で登録レコードに登録方式を対応づける。
    値の形そのもの(項目名が入る / sensitive にならない / ファイル項目にならない)は
    INT-16 の `_column_class_violations` が `REG_TYPE == 'Key'` として検査するので、
    ここでは**両方を通していること**だけを見る。
    """
    context = registered(driver_attr)
    has_combination = context['spec']['has_combination']
    rows = _rows_of(context)
    assert rows, '登録レコードが0件では検証にならない'

    # 比較キー → 登録方式。同じキーに別の登録方式が来たら判定に使わない
    reg_types = {}
    conflicted = set()
    for record in context['expected_values']:
        key = _expected_key(record, has_combination)
        if reg_types.setdefault(key, record['REG_TYPE']) != record['REG_TYPE']:
            conflicted.add(key)

    observed = Counter()
    undecidable = 0
    for row in rows:
        key = _actual_key(row, has_combination)
        if key not in reg_types or key in conflicted:
            undecidable += 1
            continue
        observed[reg_types[key]] += 1

    print('\n[integration] {} 登録方式ごとの登録件数(特定不能 {}件): {}'.format(
        context['driver_id'], undecidable,
        ', '.join('{}={}'.format(reg_type, count) for reg_type, count in sorted(observed.items()))))

    missing = [reg_type for reg_type in ('Value', 'Key') if not observed[reg_type]]
    if missing:
        skip_or_fail(
            '登録経路が {} 型のレコードを1件も通っていない(内訳: {})。'
            '登録経路は (オペレーション, Movement) を1組しか流さないので、'
            '登録対象が最も多い Movement に両方の登録方式の設定を載せる'
            '(投入手順の段階7 で足す)'
            .format(' / '.join(missing),
                    ', '.join('{}={}'.format(k, v) for k, v in sorted(observed.items())) or 'なし'))


# ======================================================================
# [INT-17] 登録経路が横シートと縦シートの両方を通る
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_registered_rows_cover_horizontal_and_vertical(registered, disposable, driver_attr):
    """INT-17 登録レコードに横シート由来と縦シート由来の両方が含まれる(投入データの歯止め)

    縦(バンドル)シートの処理は実装上**横とは別のコピー**になっている
    (TPF/CPF の変換 :1010-1014 / :1039-1045、ID変換失敗の破棄 :1013-1014、
     カラム代入順序と `INPUT_ORDER` の突き合わせ :987-988)。
    したがって INT-6〜INT-9 / INT-12 / INT-16 が縦を1件も通っていないと、
    縦側のコピーだけが壊れても全部緑のままになる。

    登録経路は (オペレーション, Movement) を**1組しか**流さないため、
    「横だけの Movement が選ばれる」と縦を通らない
    (代入値自動登録設定を横と縦で別 Movement に分けていると起きる)。
    これは実装ではなく**投入データ**の問題なので、
    ここで検知して tests/README.md の段階7 に戻れるようにする。

    判定は実テーブルの `INPUT_ORDER` 列の有無(INT-3 と同じ `sheet_kinds`)で行う。
    """
    _, ws_db = disposable
    context = registered(driver_attr)
    has_combination = context['spec']['has_combination']
    rows = _rows_of(context)
    assert rows, '登録レコードが0件では検証にならない'

    # 比較キー → 由来テーブル。同じキーに別テーブルが来たら判定に使わない
    tables = {}
    conflicted = set()
    for record in context['expected_values']:
        key = _expected_key(record, has_combination)
        if tables.setdefault(key, record['TABLE_NAME']) != record['TABLE_NAME']:
            conflicted.add(key)

    kinds = sheet_kinds(ws_db, tables.values())
    observed = Counter()
    undecidable = 0
    for row in rows:
        key = _actual_key(row, has_combination)
        if key not in tables or key in conflicted:
            undecidable += 1
            continue
        observed[kinds[tables[key]]] += 1

    print('\n[integration] {} シート種別ごとの登録件数(特定不能 {}件): {}'.format(
        context['driver_id'], undecidable,
        ', '.join('{}={}'.format(kind, count) for kind, count in sorted(observed.items()))))

    missing = [kind for kind in (HORIZONTAL, VERTICAL) if not observed[kind]]
    if missing:
        skip_or_fail(
            '登録経路が {}シート由来のレコードを1件も通っていない(内訳: {})。'
            '代入値自動登録設定を横と縦で別の Movement に分けていると、'
            '登録対象が最も多い1組だけが流れるため片方しか通らない'
            '(投入手順の段階7 で同じ Movement に載せる)'
            .format(' / '.join(missing),
                    ', '.join('{}={}'.format(k, v) for k, v in sorted(observed.items())) or 'なし'))


# ======================================================================
# [INT-20] 登録経路がホストグループの展開後テーブルを通り、メンバー機器で登録される
# ======================================================================
def test_registered_rows_cover_hostgroup_split(registered, disposable):
    """INT-20 `[HG]…` の1行が、メンバー機器ごとのレコードとして代入値管理に登録される

    「ホストグループ利用=有」のパラメータシートでは、代入値自動登録設定が読むテーブルが
    hostgroup-split の展開先(`T_CMDB_<id>_SV`)になる。読み取り経路側は同名の INT-20 で
    見ているが、**登録経路は (オペレーション, Movement) を1組しか流さない**ので、
    ホストグループ利用シートの設定を別 Movement に置くと登録経路が1件も通らない。
    その状態だと「展開された行がそのまま代入値管理に載る」ことを誰も見ていないことになる。

    ホストグループの構成は `T_HGSP_HOSTGROUP_LIST` / `T_HGSP_HOST_LINK` から独立に取る。
    ドライバは走査する(ホストグループ利用シートの設定はどのドライバに載せてもよい)。

    **展開先テーブルは1枚だけでは足りない。** ホストグループ利用はバンドル(縦)と併用でき、
    その組み合わせだけ「展開先テーブルに `INPUT_ORDER` が載る」
    (split_function.py:899 / :1299-1302。横は :1302 で落とす)状態で
    「代入順序 == 行の `INPUT_ORDER`」の突き合わせ(:987-988)が走る。
    したがってここでは
      (a) 登録経路が通った展開先テーブルを**全部**検証し
      (b) 縦・横の両方の展開先を通していることを最後に確認し(投入データの歯止め)
      (c) 縦の展開先では、入力側に複数の `INPUT_ORDER` があるのに登録が
          1つの `INPUT_ORDER` に潰れていないこと(展開で振り直されていないこと)を見る
    ところまでやる。片方だけを見ていると、縦の展開先由来の登録が0件でも緑になる。

    (c) の「どの `INPUT_ORDER` の行が登録されたか」は、登録された具体値が展開先の
    どの行の値と一致するかで引く(`vertical_value_orders`)。レコードは行を特定できる
    情報を持たない(`COL_ROW_ID` は全レコード同じ。SubValueAutoReg.py:933)。
    """
    _, ws_db = disposable
    split_tables = hostgroup_split_tables(ws_db)
    if not split_tables:
        skip_or_fail('ホストグループ利用=有 のパラメータシートが無いため、展開の登録を検証できない'
                     '(投入手順の段階4 の `pytest_ps_hg` / `pytest_ps_hg_v` を作ると'
                     '検証対象になる)')

    groups = hostgroup_members(ws_db)
    multi = {row_id: group for row_id, group in groups.items() if len(group['HOSTS']) >= 2}
    if not multi:
        skip_or_fail('メンバーが2台以上のホストグループが無いため、1行が複数ホストに'
                     '展開されて登録されることを検証できない(投入手順の段階1 を確認する)')

    kinds = sheet_kinds(ws_db, split_tables)

    # 展開先テーブルごとに「登録経路を通ったか」を集める(先頭1枚で打ち切らない)
    found = {}
    for driver_attr in DRIVER_ATTRS:
        context = registered(driver_attr)
        has_combination = context['spec']['has_combination']
        # 比較キー → 由来テーブル(INT-17 と同じ対応づけ)
        tables = {}
        conflicted = set()
        for record in context['expected_values']:
            key = _expected_key(record, has_combination)
            if tables.setdefault(key, record['TABLE_NAME']) != record['TABLE_NAME']:
                conflicted.add(key)
        rows = _rows_of(context)
        for table_name in sorted(split_tables):
            if table_name in found:
                continue
            hg_keys = {key for key, source in tables.items()
                       if source == table_name and key not in conflicted}
            if not hg_keys:
                continue
            matched = [row for row in rows if _actual_key(row, has_combination) in hg_keys]
            hg_hosts = {_norm_text(row['SYSTEM_ID']) for row in matched}
            if hg_hosts:
                found[table_name] = (context, rows, matched, hg_hosts, has_combination)

    if not found:
        skip_or_fail('登録経路がホストグループ利用シート({})由来のレコードを1件も通っていない。'
                     '登録経路は (オペレーション, Movement) を1組しか流さないので、'
                     '登録対象が最も多い Movement に設定を載せる(投入手順の段階7)。'
                     '展開(hostgroup-split バックヤード)が終わっていない可能性もある'
                     .format(', '.join(sorted(split_tables))))

    print('\n[integration] ホストグループ由来の登録: {}'.format(', '.join(
        '{}({}/{}) {}件 ホスト={}'.format(table_name, kinds[table_name],
                                        context['driver_id'], len(matched), sorted(hg_hosts))
        for table_name, (context, _, matched, hg_hosts, _) in sorted(found.items()))))

    for table_name, (context, rows, matched, hg_hosts, has_combination) in sorted(found.items()):
        # (1) メンバー全員の分が登録されている(1行が複数ホストに展開されている)
        expanded = [group for group in multi.values() if group['HOSTS'] <= hg_hosts]
        assert expanded, (
            '{}: ホストグループのメンバー全員分が登録されていない'
            '(ホストグループ={} 登録されたホスト={})'
            .format(table_name, {g['NAME']: sorted(g['HOSTS']) for g in multi.values()},
                    sorted(hg_hosts)))
        print('[integration] {} 展開を確認したホストグループ: {} → {}'
              .format(table_name, expanded[0]['NAME'], sorted(expanded[0]['HOSTS'])))

        # (2) ホストグループのID自体はホストとして登録されない(展開前の行が残っていない)
        leaked = sorted({_norm_text(row['SYSTEM_ID']) for row in rows} & set(groups))
        assert not leaked, (
            '代入値管理にホストグループのID {} がホストとして登録されている'
            .format([(row_id, groups[row_id]['NAME']) for row_id in leaked[:3]]))

        # (3) 縦の展開先は `INPUT_ORDER` が1つに潰れていない。
        #     入力側(利用者が入力したテーブル)の `INPUT_ORDER` の種類数を独立に取り、
        #     2種類以上あるのに登録が1種類しか使っていなければ展開/突き合わせの不具合
        if kinds[table_name] != VERTICAL:
            continue
        source_orders = {order for order
                         in table_input_orders(ws_db, split_tables[table_name]).values()
                         if order is not None}
        # 登録された具体値が、展開先のどの `INPUT_ORDER` の行の値かを値から逆に引く。
        # レコード側に行を特定できる情報が無い(`COL_ROW_ID` は実装が最後に収集した行のIDを
        # 入れたままで全レコード同じ。SubValueAutoReg.py:933)ため、行のIDでは辿れない
        value_orders = vertical_value_orders(ws_db, table_name)
        used = set()
        for row in matched:
            orders = value_orders.get((_norm_text(row['SYSTEM_ID']), row['OPERATION_ID'],
                                       _norm_text(row['VARS_ENTRY'])))
            if orders:
                used |= orders
        print('[integration] {} 縦の展開先: 入力側の INPUT_ORDER={} 登録に使われた={}'
              .format(table_name, sorted(source_orders), sorted(used)))
        if len(source_orders) < 2:
            skip_or_fail('{}: 入力側に `INPUT_ORDER` が1種類しか無いため、代入順序ごとに'
                         '別の行が登録されることを検証できない(投入手順の段階7 の'
                         '`hostgroup_vertical_rows` で複数の代入順序の行を作る)'
                         .format(table_name))
        assert len(used) >= 2, (
            '{}: 縦のホストグループ利用シートで、登録に使われた行の `INPUT_ORDER` が {} しか無い'
            '(入力側は {})。展開時に `INPUT_ORDER` が落ちる/振り直されると、'
            '代入順序に一致する行が見つからず値が消える(:987-988)'
            .format(table_name, sorted(used), sorted(source_orders)))

    # (4) 縦・横の両方の展開先を通していることの歯止め(実装ではなく投入データの問題)
    observed = {kinds[table_name] for table_name in found}
    missing_kinds = [kind for kind in (HORIZONTAL, VERTICAL) if kind not in observed]
    if missing_kinds:
        skip_or_fail('登録経路が {} のホストグループ利用シート由来のレコードを1件も通っていない'
                     '(展開先={})。投入手順の段階4 の `pytest_ps_hg`(横) / '
                     '`pytest_ps_hg_v`(縦)と段階7(同じ Movement に載せる)を確認する'
                     .format(' / '.join(missing_kinds),
                             {t: kinds[t] for t in sorted(split_tables)}))
