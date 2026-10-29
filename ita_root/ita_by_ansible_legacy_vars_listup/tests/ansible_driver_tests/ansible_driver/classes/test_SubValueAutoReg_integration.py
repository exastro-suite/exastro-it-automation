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
SubValueAutoReg の結合テスト(**読み取り専用**)

位置づけ:
  単体テスト(test_SubValueAutoReg_getCMDBdata / _createQuerySelectCMDB / _rest_filter)は
  WS_DB をモックしているため、生成した SELECT文が**実DBで実行できるか**は検証できていない
  (SQL の文法的な正しさ・実行可能性は結合テスト側で担保する)。
  本ファイルはその穴を、稼働中の devcontainer スタックの MariaDB に接続して埋める。

読み取り専用であること:
  - `read_val_assign` / `createQuerySelectCMDB` / `getCMDBdata` /
    `get_data_from_all_parameter_sheet` はいずれも SELECT のみで、代入値管理への
    登録(INSERT/UPDATE)は行わない経路(登録は `get_data_from_parameter_sheet` 側)。
  - 生成SQLが SELECT 以外を含まないことを INT-1 で明示的に検査する。
  - 代入値管理テーブルの件数が前後で変化しないことを INT-5 で検査する。

実行方法:
  cd ita_root/ita_by_ansible_legacy_vars_listup
  INTEGRATION_ENABLE=1 poetry run pytest \
      tests/ansible_driver_tests/ansible_driver/classes/test_SubValueAutoReg_integration.py -v

  既定(`INTEGRATION_ENABLE` 未設定)では skip する。
  収集自体はさせているので、VSCode のテスト一覧には「skip 理由付きで」出る。

接続情報:
  pytest.ini の env は単体テスト用のダミー(`DB_HOST=unittest-ita-db`)なので、
  結合テストは自前で環境変数を解決する(subvalue_autoreg_integration_support.py)。
  解決できない場合・DBに接続できない場合は skip する(CI で単体テストを止めない)。

対象ワークスペース:
  `ITA_ORGANIZATION_ID` / `ITA_WORKSPACE_ID` で明示できる
  (データ投入スクリプトと同じ環境変数名)。
  未指定なら「代入値自動登録設定が1件以上あるワークスペース」を自動で探す。
"""

import pytest
from flask import g

from .subvalue_autoreg_integration_support import (
    HORIZONTAL,
    VALUE_TABLES,
    VERTICAL,
    assign_seq,
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

# INT-5 / INT-14 で回すドライバ
DRIVER_ATTRS = ['DF_LEGACY_DRIVER_ID', 'DF_PIONEER_DRIVER_ID', 'DF_LEGACY_ROLE_DRIVER_ID']


@pytest.fixture(scope='module')
def target(app_context):
    """検証対象のワークスペースに接続した (org_id, ws_id, ws_db) を返す。

    `ITA_ORGANIZATION_ID` / `ITA_WORKSPACE_ID` が指定されていればそれを使い、
    無ければ代入値自動登録設定が1件以上あるワークスペースを探す。
    """
    from common_libs.common.dbconnect import DBConnectWs
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

    from_env = target_from_env()

    try:
        candidates = [from_env] if from_env else list_workspaces()
    except Exception as e:      # 接続不可(スタック未起動など)は skip
        skip_or_fail('DBに接続できない: {}'.format(e))

    checked = []
    for org_id, ws_id in candidates:
        g.ORGANIZATION_ID = org_id
        g.WORKSPACE_ID = ws_id
        ws_db = DBConnectWs(ws_id, org_id)
        instance = SubValueAutoReg(AnscConst.DF_LEGACY_ROLE_DRIVER_ID, ws_db)
        ret = instance.read_val_assign(instance.in_driver_name, ws_db)
        if ret[0] is True and len(ret[1]) > 0:
            # どの環境を叩いたかは失敗解析に必須なので出す(`-s` で表示)
            print('\n[integration] target organization={} workspace={} パラメータシート={}件'
                  .format(org_id, ws_id, len(ret[1])))
            yield org_id, ws_id, ws_db
            ws_db.db_disconnect()
            return
        checked.append('{}/{}'.format(org_id, ws_id))
        ws_db.db_disconnect()

    skip_or_fail('代入値自動登録設定のあるワークスペースが見つからない(確認: {})'
                 .format(', '.join(checked) or 'なし'))


@pytest.fixture(scope='module')
def generated(target):
    """本番と同じ経路で生成した SELECT文と、その材料を返す。

    read_val_assign(実DBの代入値自動登録設定) → createQuerySelectCMDB
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

    _, _, ws_db = target
    instance = SubValueAutoReg(AnscConst.DF_LEGACY_ROLE_DRIVER_ID, ws_db)
    ret = instance.read_val_assign(instance.in_driver_name, ws_db)
    assert ret[0] is True, '代入値自動登録設定の読み込みに失敗した'

    menu_ids, col_lists, pkeys = ret[1], ret[2], ret[3]
    sqls = instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, ws_db)
    assert sqls, 'SELECT文が1件も生成されなかった'
    return instance, sqls, menu_ids, pkeys


@pytest.fixture(scope='module')
def executed(generated, target):
    """生成SQLをテーブルごとに**1回だけ**実行した結果 (テーブル→行, 失敗一覧) を返す。

    INT-1(実行可能性) / INT-2(キー集合) / INT-4(絞り込みの独立オラクル)で共用する。
    例外はここでは投げず、テーブル名付きでまとめて INT-1 が報告する。
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

    _, _, ws_db = target
    _, sqls, _, _ = generated

    rows_by_table = {}
    failures = []
    for table_name, sql in sqls.items():
        try:
            rows_by_table[table_name] = ws_db.sql_execute(
                sql, [AnscConst.DF_ITA_LOCAL_HOST_CNT, AnscConst.DF_ITA_LOCAL_PKEY])
        except Exception as e:
            failures.append('{}: {}'.format(table_name, e))
    return rows_by_table, failures


@pytest.fixture(scope='module')
def records(target):
    """ドライバ名を渡すと getCMDBdata の戻り (一般変数, 多次元配列変数) を返すファクトリ。

    `get_data_from_all_parameter_sheet` と同じ引数(オペレーション/Movement 無指定)で
    read_val_assign → createQuerySelectCMDB → getCMDBdata を通す(:312-334 と同じ経路)。
    ドライバごとに1回だけ実行して使い回す。
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

    _, _, ws_db = target
    cache = {}

    def _get(driver_attr):
        if driver_attr not in cache:
            driver_id = getattr(AnscConst, driver_attr)
            instance = SubValueAutoReg(driver_id, ws_db)
            null_data_handling = instance.getIFInfoDB(ws_db)[1]['NULL_DATA_HANDLING_FLG']
            ret = instance.read_val_assign(driver_id, ws_db)
            sqls = instance.createQuerySelectCMDB(ret[1], ret[2], ret[3], ws_db) \
                if ret[0] is True and ret[1] else {}
            if not sqls:
                cache[driver_attr] = ([], [])
            else:
                result = instance.getCMDBdata(sqls, ret[1], ret[2], None, ws_db, null_data_handling)
                cache[driver_attr] = (list(result[0]), list(result[1]))
        return cache[driver_attr]

    return _get


@pytest.fixture(scope='module')
def val_assign(target):
    """(ドライバ名, Movement) を渡すと read_val_assign の戻りをそのまま返すファクトリ。

    戻りは (ok, テーブル名→メニューID, カラム情報, テーブル名→主キー名,
    テーブル名→メニューRest名, パラメータシートごとの件数)。
    `movement_id` を渡すと**登録経路と同じ** Movement 絞り込み付きの読み込みになる
    (`get_data_from_parameter_sheet` は Movement を渡し、
     `get_data_from_all_parameter_sheet` は渡さない。両者の差はこの引数だけ:1677-1684)。
    同じ (ドライバ, Movement) は1回だけ実行して使い回す。
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

    _, _, ws_db = target
    cache = {}

    def _get(driver_attr, movement_id=None):
        if (driver_attr, movement_id) not in cache:
            driver_id = getattr(AnscConst, driver_attr)
            instance = SubValueAutoReg(driver_id, ws_db)
            cache[(driver_attr, movement_id)] = instance.read_val_assign(driver_id, ws_db, movement_id)
        return cache[(driver_attr, movement_id)]

    return _get


@pytest.fixture(scope='module')
def all_sheet_data(target):
    """ドライバ名を渡すと `get_data_from_all_parameter_sheet` の戻りを返すファクトリ。

    戻りは (ok, template_list, host_list, 代入値管理の件数(実行前), 同(実行後))。
    件数は呼び出しを挟んで測るので、読み取り専用であることの確認(INT-5)に使える。
    ドライバごとに1回だけ実行して INT-5 / INT-13 で使い回す。
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

    _, _, ws_db = target
    cache = {}

    def _value_table_counts():
        counts = {}
        for table_name in VALUE_TABLES:
            if ws_db.sql_execute("SHOW TABLES LIKE %s", [table_name]):
                counts[table_name] = ws_db.table_count(table_name)
        return counts

    def _get(driver_attr):
        if driver_attr not in cache:
            instance = SubValueAutoReg(getattr(AnscConst, driver_attr), ws_db)
            before = _value_table_counts()
            ok, template_list, host_list = instance.get_data_from_all_parameter_sheet()
            cache[driver_attr] = (ok, template_list, host_list, before, _value_table_counts())
        return cache[driver_attr]

    return _get


def _live_records(records, driver_attr):
    """getCMDBdata の戻りのうち、TPF変数抽出・登録の対象になるレコード。

    `extract_tpl_vars`(:1936-1939)と同じ判定にする(空レコードと `STATUS is False` を除く)。
    """
    std, array = records(driver_attr)
    return [r for r in list(std) + list(array) if len(r) != 0 and r['STATUS'] is not False]


def _settings_by_column(col_lists):
    """read_val_assign のカラム情報を {(テーブル名, カラム名): [設定, …]} に平す。

    元の形は `col_lists[テーブル名][カラム名][連番] = {設定}`(:1812)で、
    連番は全テーブル通しの採番なので設定そのものの識別には使わない。
    """
    flat = {}
    for table_name, columns in col_lists.items():
        for col_name, settings in columns.items():
            flat[(table_name, col_name)] = list(settings.values())
    return flat


def _assert_select_only(sql, table_name):
    """生成SQLが SELECT のみであること(このテストが書き込まないこと)を保証する。"""
    assert sql.lstrip().upper().startswith('SELECT'), \
        '{}: 生成SQLが SELECT で始まっていない'.format(table_name)
    upper = sql.upper()
    for keyword in ('INSERT ', 'UPDATE ', 'DELETE ', 'DROP ', 'ALTER ', 'TRUNCATE ', 'CREATE '):
        assert keyword not in upper, '{}: 生成SQLに {} が含まれる'.format(table_name, keyword.strip())


# ======================================================================
# [INT-1] 生成SQLが実DBで実行できる
# ======================================================================
def test_generated_sql_is_executable(generated, executed):
    """INT-1 createQuerySelectCMDB の生成SQLが実DBで実行できる

    単体テスト(§Q1〜§Q5)は生成SQLを**文字列として**しか見ていない。
    ここでは実テーブルに対して発行し、
      - 構文エラーが無いこと
      - 存在しないカラムを参照していないこと
      - `%s` のバインド数が getCMDBdata のバインド順と一致すること
    を確認する(全テーブル分を実行し、失敗はまとめて報告する)。

    「実行できる」だけでは中身を見ていないため、結果セットの中身は
    INT-2(キー集合) / INT-4(絞り込み) / INT-14(廃止データの除外)で検査する。
    """
    _, sqls, _, _ = generated
    _, failures = executed

    for table_name, sql in sqls.items():
        _assert_select_only(sql, table_name)
        assert sql.count('%s') == 2, '{}: バインド数が2でない'.format(table_name)

    assert not failures, '実DBで実行できない生成SQLがある:\n' + '\n'.join(failures)


# ======================================================================
# [INT-2] 結果セットのキーが getCMDBdata の参照と一致する
# ======================================================================
def test_result_set_keys_match_getcmdbdata(executed):
    """INT-2 実DBの結果セットに getCMDBdata が参照するキーが揃っている

    §Q6 は `_ProjectingWsDb`(SELECT句を解釈する擬似カーソル)で列落ちを検知しているが、
    本物のカーソルで同じ結果になることは未検証だった。
    レコードが1件以上あるテーブルすべてでキー集合を確認する。

    期待値の5つは getCMDBdata が結果セットから実際に読むキーの**全部**
    (具体値は `rest_filter` 経由で別に取るため、SELECT句の他の列は参照されない。
    SubValueAutoReg.py:892-945)。キーは結果セット全体で共通なので先頭行で判定する。
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

    rows_by_table, _ = executed

    expected_keys = {'OPERATION_ID', 'HOST_ID', 'INPUT_ORDER',
                     AnscConst.DF_ITA_LOCAL_HOST_CNT, AnscConst.DF_ITA_LOCAL_PKEY}

    checked = 0
    for table_name, rows in rows_by_table.items():
        if not rows:
            continue
        checked += 1
        missing = expected_keys - set(rows[0].keys())
        assert not missing, '{}: 結果セットに {} が無い'.format(table_name, sorted(missing))

    if checked == 0:
        skip_or_fail('レコードのあるパラメータシートが無いためキー集合を確認できない')


# ======================================================================
# [INT-3] 縦/横メニューの判定が実テーブル構成で機能する
# ======================================================================
def test_vertical_detection_matches_real_table(generated, target):
    """INT-3 INPUT_ORDER 列の有無(実 SHOW COLUMNS)と生成SQLが一致する

    縦メニュー判定は `table_columns_get`(=SHOW COLUMNS)の結果で行う(§Q1)。
    実テーブルに `INPUT_ORDER` 列がある場合だけ `TBL_A.INPUT_ORDER` を、
    無い場合は `'' AS INPUT_ORDER` を出すことを実構成で確認する。
    """
    _, _, ws_db = target
    _, sqls, _, _ = generated

    kinds = {'vertical': [], 'horizontal': []}
    for table_name, sql in sqls.items():
        columns = ws_db.table_columns_get(table_name)[0]
        if 'INPUT_ORDER' in columns:
            kinds['vertical'].append(table_name)
            assert 'TBL_A.INPUT_ORDER' in sql, '{}: 縦メニューなのに INPUT_ORDER を選んでいない'.format(table_name)
        else:
            kinds['horizontal'].append(table_name)
            assert "'' AS INPUT_ORDER" in sql, \
                "{}: 横メニューなのに '' AS INPUT_ORDER が無い".format(table_name)
        assert sql.count('INPUT_ORDER') == 1, '{}: INPUT_ORDER が複数回出力されている'.format(table_name)

    assert kinds['vertical'] or kinds['horizontal']
    if not kinds['vertical']:
        skip_or_fail('縦メニュー(INPUT_ORDER 列あり)のパラメータシートが無い')


# ======================================================================
# [INT-4] オペレーション指定(ansible-execute 経路)のSQLも実行できる
# ======================================================================
def test_operation_id_filter_sql_is_executable(generated, target, executed):
    """INT-4 `AND OPERATION_ID = %s` を付けたSQL(オペ指定)が実DBで実行でき、正しく絞れる

    getCMDBdata は オペ指定時に生成SQLの末尾へ条件を足し、バインドを3個にする
    ([:880-884](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L880-L884))。
    §Q6-4/§8-2 は文字列とバインド値の検証までで、実行はしていない。

    絞り込みの検証には**オペ無指定の結果を Python 側で絞ったもの**を独立オラクルに使う。
      - 「他のオペの行が混じる(絞り込みが効いていない)」
      - 「1行も返らない(絞り込みが強すぎる / 別名側で絞ってしまい NULL 比較になる)」
    の両方を検知できる。オペレーションは**実データに現れるもの**から選ぶ
    (`LIMIT 1` で選ぶと該当行が0件になり、行ループが空回りして何も検証しないため)。

    なお WHERE句の `OPERATION_ID` は SELECT句の別名ではなく `TBL_A` の実カラムを指すので、
    廃止でないオペレーションなら「別名が一致する行」=「実カラムが一致する行」になる。
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

    _, _, ws_db = target
    _, sqls, _, _ = generated
    rows_by_table, _ = executed
    pkey = AnscConst.DF_ITA_LOCAL_PKEY

    # 別名 OPERATION_ID は廃止オペだと NULL になるため、非空の値は有効オペレーション
    candidates = sorted({row['OPERATION_ID'] for rows in rows_by_table.values()
                         for row in rows if row['OPERATION_ID']})
    if not candidates:
        skip_or_fail('生成SQLの結果に有効なオペレーションが1件も現れないため、'
                     'オペ指定の絞り込みを検証できない')
    operation_id = candidates[0]

    matched = 0
    for table_name, sql in sqls.items():
        if table_name not in rows_by_table:      # 実行できなかったテーブルは INT-1 が報告する
            continue
        sql_with_ope = sql + " AND OPERATION_ID = %s \n "
        rows = ws_db.sql_execute(sql_with_ope, [AnscConst.DF_ITA_LOCAL_HOST_CNT,
                                                AnscConst.DF_ITA_LOCAL_PKEY,
                                                operation_id])
        expected = {row[pkey] for row in rows_by_table[table_name]
                    if row['OPERATION_ID'] == operation_id}
        actual = {row[pkey] for row in rows}
        assert actual == expected, (
            '{}: オペ指定の絞り込み結果がオペ無指定の結果と一致しない(不足 {} / 余分 {})'
            .format(table_name, sorted(expected - actual)[:3], sorted(actual - expected)[:3]))
        matched += len(actual)

        # 絞り込みが効いていること(サブクエリ側の別名 OPERATION_ID ではなく TBL_A 側で絞る)
        for row in rows:
            assert row['OPERATION_ID'] == operation_id, \
                '{}: オペ指定で絞り込めていない'.format(table_name)

    assert matched > 0, \
        'オペレーション {} に該当する行が1件も返らず、絞り込みを検証できていない'.format(operation_id)


# ======================================================================
# [INT-5] vars-listup の本番エントリポイントが実DBで完走する(読み取りのみ)
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_get_data_from_all_parameter_sheet(all_sheet_data, records, driver_attr):
    """INT-5 get_data_from_all_parameter_sheet がドライバ L/P/R で完走し、DBを変更しない

    read_val_assign → createQuerySelectCMDB → getCMDBdata → TPF変数抽出 の
    全経路を実データで通す(vars-listup が実際に呼ぶ入口)。
    併せて代入値管理テーブルの件数が前後で変化しないことを確認し、
    このテストが読み取り専用であることを保証する。

    形(キーが空でない等)だけでは「戻りが空でも通る」ため、
    戻りが getCMDBdata のレコードと対応していることまで確認する。
    """
    ok, template_list, host_list, before, after = all_sheet_data(driver_attr)

    assert ok is True
    assert isinstance(template_list, dict)
    assert isinstance(host_list, dict)

    # { MovementID: { TPF変数名: 0 } } の形になっている。
    # 具体値に埋まっていた TPF 変数名がそのままキーになるので、空文字や None は不正。
    for movement_id, tpl_vars in template_list.items():
        assert movement_id, 'template_list に空の MOVEMENT_ID がある'
        assert isinstance(tpl_vars, dict), \
            'MOVEMENT_ID={} の template_list の中身が dict でない'.format(movement_id)
        for tpl_var_name in tpl_vars:
            assert isinstance(tpl_var_name, str) and tpl_var_name, \
                'MOVEMENT_ID={} に空のTPF変数名がある'.format(movement_id)

    # { MovementID: { OPERATION_ID: { SYSTEM_ID: 0 } } } の形になっている
    for movement_id, operations in host_list.items():
        assert movement_id, 'host_list に空の MOVEMENT_ID がある'
        assert isinstance(operations, dict), 'MOVEMENT_ID={} の中身が dict でない'.format(movement_id)
        for operation_id, hosts in operations.items():
            assert operation_id, 'MOVEMENT_ID={} に空の OPERATION_ID がある'.format(movement_id)
            assert isinstance(hosts, dict)
            assert hosts, \
                'MOVEMENT_ID={} OPERATION_ID={} の作業対象ホストが空'.format(movement_id, operation_id)
            for system_id in hosts:
                assert system_id, \
                    'MOVEMENT_ID={} OPERATION_ID={} に空の SYSTEM_ID がある'.format(
                        movement_id, operation_id)

    assert after == before, '代入値管理テーブルの件数が変化した(読み取り専用ではない)'

    # --- 戻りが getCMDBdata のレコードと対応しているか(空の戻りで通らないようにする)
    live_records = _live_records(records, driver_attr)
    if not live_records:
        skip_or_fail('ドライバ {} は getCMDBdata が1件もレコードを返さないため、'
                     '戻り値の対応を検証できない'.format(driver_attr))

    # host_list は「レコードの (Movement, オペレーション, ホスト)」と一致する(:1951-1957)
    expected_hosts = {}
    for record in live_records:
        expected_hosts.setdefault(record['MOVEMENT_ID'], {}) \
                      .setdefault(record['OPERATION_ID'], set()) \
                      .add(record['SYSTEM_ID'])
    actual_hosts = {movement_id: {operation_id: set(hosts) for operation_id, hosts in operations.items()}
                    for movement_id, operations in host_list.items()}
    assert actual_hosts == expected_hosts, \
        'host_list が getCMDBdata のレコードと対応していない'

    # template_list は「具体値に TPF変数がちょうど1個あるレコード」の変数名と一致する。
    # 実装の抽出処理を呼ばず、独立に判定する(判定できない具体値がある場合は包含関係まで)
    expected_template = {}
    undecidable = 0
    for record in live_records:
        decidable, tpf_var_name = single_tpf_var(record['VARS_ENTRY'])
        if not decidable:
            undecidable += 1
        elif tpf_var_name:
            expected_template.setdefault(record['MOVEMENT_ID'], set()).add(tpf_var_name)

    actual_template = {movement_id: set(tpl_vars) for movement_id, tpl_vars in template_list.items()}
    if undecidable == 0:
        assert actual_template == expected_template, \
            'template_list が具体値のTPF変数と一致しない(判定不能な具体値なし)'
    else:
        for movement_id, tpf_var_names in expected_template.items():
            assert tpf_var_names <= actual_template.get(movement_id, set()), \
                'MOVEMENT_ID={} のTPF変数 {} が template_list に無い'.format(
                    movement_id, sorted(tpf_var_names - actual_template.get(movement_id, set())))


# ======================================================================
# [INT-14] getCMDBdata のレコードに廃止データが混じらない
#          (INT-6〜INT-9 / INT-12 / INT-15 は登録経路 test_SubValueAutoReg_integration_write.py が使用)
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_getcmdbdata_records_exclude_disused(records, target, driver_attr):
    """INT-14 getCMDBdata がレコードを返し、そこに廃止データが混じらない(独立オラクル)

    読み取り経路の他のケースは
      - INT-1 … SQL が実行できること(返った行は見ない)
      - INT-2 … 結果セットのキー集合(0件なら skip)
      - INT-5 … 入口の戻り(getCMDBdata の**レコードそのもの**は見ていない)
    しか見ておらず、レコードの中身に対する期待値がどこにも無かった。
    登録経路(INT-6)も期待値を getCMDBdata の戻りから作るので、
    「getCMDBdata の結果が正しいか」は**別経路で取った値**と比べないと分からない。

    ここでは廃止データを独立オラクルにする。生成SQLは
      - 廃止オペレーション … 相関サブクエリが NULL を返す(:398-404)
      - 廃止ホスト        … 相関サブクエリが 0 を返す(:406-412)
    で除外し、getCMDBdata が MSG-10360 / MSG-10359 でレコードを捨てる(:903-920)。
    この `DISUSE_FLAG = '0'` が外れると、廃止済みの機器/オペレーションに紐づく具体値が
    そのまま代入値管理へ流れる(=作業実行の対象になる)が、
    期待値を getCMDBdata から作る方式では検知できない。
    """
    _, _, ws_db = target

    live_records = _live_records(records, driver_attr)
    if not live_records:
        skip_or_fail('ドライバ {} は getCMDBdata が1件もレコードを返さないため、'
                     '廃止データの除外を検証できない'.format(driver_attr))

    for record in live_records:
        assert record['OPERATION_ID'], 'OPERATION_ID が空のレコードが残っている'
        assert record['SYSTEM_ID'], 'SYSTEM_ID が空のレコードが残っている'

    disused_operations, disused_hosts = disused_ids(ws_db)
    if not disused_operations and not disused_hosts:
        skip_or_fail('廃止済みのオペレーション/機器が無いため、廃止データの除外を検証できない'
                     '(投入手順の段階8 を実施すると検証対象になる)')

    bad_operations = sorted({r['OPERATION_ID'] for r in live_records
                             if r['OPERATION_ID'] in disused_operations})
    bad_hosts = sorted({r['SYSTEM_ID'] for r in live_records
                        if r['SYSTEM_ID'] in disused_hosts})
    assert not bad_operations, \
        '廃止済みオペレーション {} のレコードが返っている'.format(bad_operations[:3])
    assert not bad_hosts, \
        '廃止済み機器 {} のレコードが返っている'.format(bad_hosts[:3])


# ======================================================================
# [INT-17] ドライバごとに横シートと縦シートの両方を読んでいる
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_records_cover_horizontal_and_vertical(records, target, driver_attr):
    """INT-17 getCMDBdata のレコードに横シート由来と縦シート由来の両方が含まれる(投入データの歯止め)

    INT-3 は「縦判定と生成SQLが一致するか」を LegacyRole の設定で1回だけ見ている。
    ドライバごとに縦シートを通しているかは見ていないため、
    あるドライバの代入値自動登録設定に縦シートが1件も無くても気付けない。
    縦の処理は実装上**横とは別のコピー**(TPF/CPF の変換 :1010-1014、
    ID変換失敗の破棄 :1013-1014、カラム代入順序と `INPUT_ORDER` の突き合わせ :987-988)なので、
    ドライバ L/P/R それぞれで両方を通しておく必要がある。

    これは実装ではなく**投入データ**の問題なので、
    検知したら tests/README.md の段階7 に戻る。
    """
    _, _, ws_db = target

    live_records = _live_records(records, driver_attr)
    if not live_records:
        skip_or_fail('ドライバ {} は getCMDBdata が1件もレコードを返さないため、'
                     'シート種別の網羅を確認できない'.format(driver_attr))

    table_names = [r['TABLE_NAME'] for r in live_records if r.get('TABLE_NAME')]
    kinds = sheet_kinds(ws_db, table_names)
    observed = {}
    for table_name in table_names:
        observed.setdefault(kinds[table_name], set()).add(table_name)

    print('\n[integration] {} シート種別ごとのレコード数: {}'.format(
        driver_attr,
        ', '.join('{}={}件({}テーブル)'.format(
            kind, sum(1 for t in table_names if kinds[t] == kind), len(tables))
            for kind, tables in sorted(observed.items()))))

    missing = [kind for kind in (HORIZONTAL, VERTICAL) if kind not in observed]
    if missing:
        skip_or_fail('ドライバ {} の代入値自動登録設定に {}シートのものが無い(投入手順の段階7 で足す)'
                     .format(driver_attr, ' / '.join(missing)))


# ======================================================================
# [INT-18] 同一パラメータシートに複数 Movement の設定がある状態で Movement 絞り込みが効く
# ======================================================================
def test_movement_filter_selects_only_that_movement(val_assign, records):
    """INT-18 同じ実テーブルに複数 Movement の設定があるとき、Movement 指定がその Movement だけを返す

    読み取り経路(`get_data_from_all_parameter_sheet`)は Movement を**指定せず**、
    登録経路(`get_data_from_parameter_sheet`)は**指定して**同じ `read_val_assign` を呼ぶ。
    両者の差は `AND TBL_A.MOVEMENT_ID = %s` の1行だけ(:1677-1684)なので、
      - 絞り込みが外れる → 登録経路が指定外の Movement の設定まで読み、
        別 Movement 向けの具体値を代入値管理に登録する
      - 絞り込みが強すぎる → 登録経路が1件も読まない
    のどちらも起きうる。ところが**そのテーブルに Movement が1つしか紐づいていない**データでは
    「テーブル単位で見れば結果が同じ」になり、INT-6〜INT-9 では検知できない。

    パラメータシートの実テーブルは具体値を1つの `DATA_JSON` カラムに持つので、
    `read_val_assign` のカラム情報(`col_lists[テーブル名][カラム名]`)は
    実質**シート単位**にまとまる。したがってここで探す「複数 Movement のカラム」は
    「複数 Movement の設定が載っているパラメータシート」と同じ意味になる。

    ここでは1枚のシートに複数 Movement が紐づいた状態(投入手順の段階10)を前提に
      (1) Movement 指定の結果に他 Movement の設定が1件も無い
      (2) Movement ごとの結果の**和**が、絞り込みなしの結果と一致する(取りこぼしが無い)
      (3) `getCMDBdata` のレコードにも両方の Movement が現れる
          (= 同じ具体値が Movement ごとに別レコードとして登録対象になる)
    を確認する。
    """
    # 段階10 は Legacy に作るが、どのドライバに作っても検知できるように全ドライバを走査する
    found = None
    for driver_attr in DRIVER_ATTRS:
        ret = val_assign(driver_attr)
        if ret[0] is not True:
            continue
        for (table_name, col_name), settings in sorted(_settings_by_column(ret[2]).items()):
            movements = {s['MOVEMENT_ID'] for s in settings}
            if len(movements) >= 2:
                found = (driver_attr, table_name, col_name, settings, movements)
                break
        if found:
            break

    if not found:
        skip_or_fail('複数 Movement の代入値自動登録設定が載ったパラメータシートが無いため、'
                     'Movement 絞り込みを検証できない(投入手順の段階10 を実施すると検証対象になる)')
    driver_attr, table_name, col_name, settings, movements = found
    print('\n[integration] {} 複数 Movement のカラム: {}.{} Movement={}件 設定={}件'.format(
        driver_attr, table_name, col_name, len(movements), len(settings)))

    expected_ids = {s['COLUMN_ID'] for s in settings}
    union = set()
    for movement_id in sorted(movements):
        ret = val_assign(driver_attr, movement_id)
        assert ret[0] is True, 'Movement {} 指定の読み込みに失敗した'.format(movement_id)
        per_column = _settings_by_column(ret[2])

        # (1) 指定した Movement 以外の設定が混ざらない
        movements_in_result = {s['MOVEMENT_ID'] for entries in per_column.values() for s in entries}
        others = sorted(movements_in_result - {movement_id})
        assert not others, \
            'Movement {} を指定したのに別 Movement {} の設定が返っている'.format(movement_id, others[:3])

        # 対象カラムについては「絞り込みなしの結果をその Movement で絞ったもの」と一致する
        got = {s['COLUMN_ID'] for s in per_column.get((table_name, col_name), [])}
        want = {s['COLUMN_ID'] for s in settings if s['MOVEMENT_ID'] == movement_id}
        assert got == want, (
            '{}.{} の Movement {} の設定が一致しない(不足 {} / 余分 {})'
            .format(table_name, col_name, movement_id, sorted(want - got), sorted(got - want)))
        union |= got

    # (2) 取りこぼしが無い(絞り込みが強すぎないこと)
    assert union == expected_ids, \
        '{}.{} の設定が Movement 別の和と一致しない(取りこぼし {})'.format(
            table_name, col_name, sorted(expected_ids - union))

    # (3) レコード側でも Movement ごとに別レコードになる
    live_records = [r for r in _live_records(records, driver_attr)
                    if r.get('TABLE_NAME') == table_name and r.get('COL_NAME') == col_name]
    if not live_records:
        skip_or_fail('{}.{} に具体値が無いため、Movement ごとのレコード生成を検証できない'
                     .format(table_name, col_name))
    got_movements = {r['MOVEMENT_ID'] for r in live_records}
    assert got_movements <= movements, \
        'レコードに設定の無い Movement {} が現れている'.format(sorted(got_movements - movements)[:3])
    assert len(got_movements) >= 2, (
        '{}.{} は複数 Movement に紐づいているのに、レコードは Movement {} の分しか無い'
        '(具体値が空だと Key型 は MSG-10377 / Value型 は MSG-10375 で捨てられる。'
        '投入手順の段階7・段階10 を確認する)'.format(table_name, col_name, sorted(got_movements)))
    # 同じ (COL_TYPE, 具体値) が Movement ごとに複製されるので、変数の紐づけだけが違う
    assert len({r['MVMT_VAR_LINK_ID'] for r in live_records}) >= 2, \
        '{}.{} のレコードが同じ変数しか参照していない'.format(table_name, col_name)


# ======================================================================
# [INT-19] ドライバごとに Value型 と Key型 の両方の設定を読んでいる
# ======================================================================
@pytest.mark.parametrize('driver_attr', DRIVER_ATTRS)
def test_records_cover_value_and_key_registration(val_assign, records, driver_attr):
    """INT-19 読み取り経路が Value型 と Key型 の両方を通り、Key型は**項目名**を登録する(投入データの歯止め)

    登録方式(`COL_TYPE`)は代入値自動登録設定の軸のひとつで、
    Key型 は具体値ではなく**カラムの項目名**を変数の値として登録する
    (`makeVarsAssignData` :1218-1247。sensitive は常に OFF、
     具体値が空ならそのペアだけ MSG-10377 で捨てる)。
    Value型 とは別のコピーなので、あるドライバの設定が Value型 だけだと
    Key型 の分岐が壊れていても全部緑のままになる。

    これは実装ではなく**投入データ**の問題なので、
    検知したら tests/README.md の段階7 に戻る。
    """
    from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

    ret = val_assign(driver_attr)
    if ret[0] is not True or not ret[1]:
        skip_or_fail('ドライバ {} の代入値自動登録設定が無い'.format(driver_attr))

    per_column = _settings_by_column(ret[2])
    col_types = {s['COL_TYPE'] for entries in per_column.values() for s in entries}
    print('\n[integration] {} 登録方式ごとの設定件数: {}'.format(
        driver_attr,
        ', '.join('{}={}件'.format(name, sum(1 for entries in per_column.values()
                                            for s in entries if s['COL_TYPE'] == col_type))
                  for name, col_type in (('Value型', AnscConst.DF_COL_TYPE_VAL),
                                         ('Key型', AnscConst.DF_COL_TYPE_KEY)))))

    missing = [name for name, col_type in (('Value型', AnscConst.DF_COL_TYPE_VAL),
                                           ('Key型', AnscConst.DF_COL_TYPE_KEY))
               if col_type not in col_types]
    if missing:
        skip_or_fail('ドライバ {} の代入値自動登録設定に {} のものが無い(投入手順の段階7 で足す)'
                     .format(driver_attr, ' / '.join(missing)))

    live_records = _live_records(records, driver_attr)
    if not live_records:
        skip_or_fail('ドライバ {} は getCMDBdata が1件もレコードを返さないため、'
                     '登録方式の網羅を確認できない'.format(driver_attr))

    # 項目なしメニューのレコード(`STATUS='skip'`)は登録方式を持たない(:992-1001)
    reg_types = {r['REG_TYPE'] for r in live_records if 'REG_TYPE' in r}
    assert {'Value', 'Key'} <= reg_types, (
        'ドライバ {} のレコードに {} 由来のものが無い(設定はあるのにレコードにならない。'
        '具体値が空のカラムだけに Key型 を付けていると MSG-10377 で全部捨てられる)'
        .format(driver_attr, sorted({'Value', 'Key'} - reg_types)))

    # Key型 のレコードは具体値ではなく項目名(COLUMN_NAME_JA / _EN)が入る。
    # 表示言語で ja/en のどちらを使うかは実装依存なので、どちらかであることまでを見る
    item_names = {}
    for (table_name, col_name), entries in per_column.items():
        for setting in entries:
            if setting['COL_TYPE'] == AnscConst.DF_COL_TYPE_KEY:
                item_names.setdefault((table_name, col_name), set()).update(
                    (setting['COLUMN_NAME_JA'], setting['COLUMN_NAME_EN']))

    checked = 0
    for record in live_records:
        if record.get('REG_TYPE') != 'Key':
            continue
        names = item_names.get((record.get('TABLE_NAME'), record.get('COL_NAME')))
        if not names:
            continue
        checked += 1
        assert record['VARS_ENTRY'] in names, (
            'Key型 のレコードに項目名ではない値が入っている({}.{}: {!r} 期待={})'
            .format(record['TABLE_NAME'], record['COL_NAME'],
                    record['VARS_ENTRY'], sorted(names)))
    assert checked, 'Key型 のレコードを設定と対応づけられなかった'


# ======================================================================
# [INT-20] ホストグループ利用シートは展開後のテーブルからレコードになる
# ======================================================================
def test_hostgroup_rows_are_split_into_member_hosts(records, val_assign, target):
    """INT-20 `[HG]…` の1行がメンバー機器ごとのレコードになり、ホストグループのIDは残らない

    「ホストグループ利用=有」のパラメータシートは、代入値自動登録設定が読むテーブルが
    入力用メニューのテーブルではなく hostgroup-split の展開先(`T_CMDB_<id>_SV`)になる。
    つまりこのパターンだけ「利用者が入力した行」と「レコードになる行」が一致せず、
      - 展開が動いていない  → メンバー機器の分のレコードが1件も出ない
      - 展開元の行が残る    → 機器一覧に無い**ホストグループのID**をホストとして
                              代入値管理に登録してしまう(実行時にホストが解決できない)
      - 展開時の値のコピー漏れ → メンバーごとに値が食い違う
    のどれも、生成SQLやレコード件数だけ見ていると気付けない。

    ホストグループの構成は `T_HGSP_HOSTGROUP_LIST` / `T_HGSP_HOST_LINK` から
    独立に取り(`hostgroup_members`)、getCMDBdata の戻りと突き合わせる。

    **展開先テーブルは1枚だけ見ては足りない。** ホストグループ利用は
    バンドル(縦)と併用でき、そのときだけ
      - hostgroup-split が `INPUT_ORDER` も含めて展開する
        (`insert_data['INPUT_ORDER'] = …`: split_function.py:899 / :1299-1302。
         横は :1302 で `INPUT_ORDER` を落とす)
      - 展開先を読む側が「設定のカラム代入順序 == 行の `INPUT_ORDER`」で行を選ぶ(:987-988)
    という**別々のコピー**同士が噛み合う。よって
      (a) レコードが出た展開先テーブルは**全部**検証する
      (b) 縦・横の両方の展開先を通していることを最後に確認する(投入データの歯止め)
      (c) 縦の展開先では「設定のカラム代入順序の行の具体値がレコードになっている」ことを
          レコードとは別経路(`vertical_value_orders`)で突き合わせる
    ここまで見ないと、展開時に `INPUT_ORDER` が落ちる/振り直される不具合が
    「レコード0件」や「別の代入順序の値」として静かに通ってしまう。

    (c) を行のID(`COL_ROW_ID`)ではなく具体値で突き合わせるのは、レコードの
    `COL_ROW_ID` が行を特定できないため(実装が最後に収集した行のIDを入れたままにする。
    `vertical_value_orders` の説明と SubValueAutoReg.py:933 参照)。
    """
    _, _, ws_db = target
    split_tables = hostgroup_split_tables(ws_db)
    if not split_tables:
        skip_or_fail('ホストグループ利用=有 のパラメータシートが無いため、展開を検証できない'
                     '(投入手順の段階4 の `pytest_ps_hg` / `pytest_ps_hg_v` を作ると'
                     '検証対象になる)')

    groups = hostgroup_members(ws_db)
    multi = {row_id: group for row_id, group in groups.items() if len(group['HOSTS']) >= 2}
    if not multi:
        skip_or_fail('メンバーが2台以上のホストグループが無いため、1行が複数行に展開される'
                     'ことを検証できない(投入手順の段階1 を確認する)')

    kinds = sheet_kinds(ws_db, split_tables)

    # ホストグループ利用シートの設定はどのドライバに作ってもよいので全ドライバを走査し、
    # レコードが出た展開先テーブルは(先頭1枚ではなく)全部検証する
    found = {}
    for driver_attr in DRIVER_ATTRS:
        live_records = _live_records(records, driver_attr)
        for table_name in sorted(split_tables):
            rows = [r for r in live_records if r.get('TABLE_NAME') == table_name]
            if rows and table_name not in found:
                found[table_name] = (driver_attr, rows)
    if not found:
        skip_or_fail('ホストグループ利用シート({})のレコードが1件も無いため、展開を検証できない'
                     '(展開({} バックヤード)が終わっていない / 代入値自動登録設定が無い。'
                     '投入手順の段階7 を確認する)'
                     .format(', '.join(sorted(split_tables)), 'hostgroup-split'))

    print('\n[integration] ホストグループ利用シートの展開先: {}'.format(', '.join(
        '{}({}/入力元 {}) レコード={}件'.format(
            table_name, kinds[table_name], split_tables[table_name], len(rows))
        for table_name, (_, rows) in sorted(found.items()))))

    verified = []
    for table_name, (driver_attr, rows) in sorted(found.items()):
        system_ids = {r['SYSTEM_ID'] for r in rows}

        # (1) 展開元(ホストグループのROW_ID)がホストとしてレコードに残らない
        leaked = sorted(system_ids & set(groups))
        assert not leaked, (
            '{}: レコードのホストにホストグループのID {} が残っている'
            '(展開前の行が廃止されずにレコードになっている)'
            .format(table_name, [(row_id, groups[row_id]['NAME']) for row_id in leaked[:3]]))

        # (2) 縦の展開先では、レコードの具体値が「設定のカラム代入順序と同じ
        #     `INPUT_ORDER` の行」の値になっている(展開で `INPUT_ORDER` が壊れていないこと)
        if kinds[table_name] == VERTICAL:
            value_orders = vertical_value_orders(ws_db, table_name)
            table_orders = {order for order in table_input_orders(ws_db, table_name).values()
                            if order is not None}
            per_column = _settings_by_column(val_assign(driver_attr)[2])
            checked = 0
            used = set()
            for record in rows:
                settings = [s for s in per_column.get((table_name, record.get('COL_NAME')), [])
                            if s['MVMT_VAR_LINK_ID'] == record.get('MVMT_VAR_LINK_ID')]
                if not settings:
                    continue        # 設定と対応づけられないレコードは対象外
                wanted = {assign_seq(s['COLUMN_ASSIGN_SEQ']) for s in settings}
                # 具体値が一致する行の代入順序(値の変換が入るカラムは一致無し=対象外)
                actual = value_orders.get((record['SYSTEM_ID'], record['OPERATION_ID'],
                                           record['VARS_ENTRY']))
                if not actual:
                    continue
                checked += 1
                assert actual & wanted, (
                    '{}: 縦の展開先で代入順序と違う行の値がレコードになっている'
                    '(カラム {} ホスト {} 具体値 {!r} は INPUT_ORDER={} の行の値。'
                    '設定のカラム代入順序={})'
                    .format(table_name, record.get('COL_NAME'), record['SYSTEM_ID'],
                            record['VARS_ENTRY'], sorted(actual),
                            sorted(str(v) for v in wanted)))
                used |= actual & wanted
            assert checked, (
                '{}: 縦の展開先のレコードを展開先テーブルの行の値と対応づけられなかった'
                '(投入手順の段階7 の `hostgroup_vertical_rows` に'
                '変換の入らない項目(文字列)があることを確認する)'.format(table_name))
            print('[integration] {} 縦の展開先: {}件のレコードで '
                  '代入順序どおりの行の値になっていることを確認(使われた代入順序={})'
                  .format(table_name, checked, sorted(used)))
            # 代入順序が1つに潰れていないこと。テーブルに複数の `INPUT_ORDER` があるのに
            # 1種類しかレコードになっていなければ、展開/突き合わせのどちらかが壊れている
            if len(table_orders) < 2:
                skip_or_fail('{}: 展開先に `INPUT_ORDER` が1種類しか無いため、代入順序ごとに'
                             '別の行が採られることを検証できない(投入手順の段階7 の'
                             '`hostgroup_vertical_rows` で複数の代入順序の行を作る)'
                             .format(table_name))
            assert len(used) >= 2, (
                '{}: 縦の展開先でレコードになった代入順序が {} しか無い(展開先の行は {})。'
                '展開時に `INPUT_ORDER` が落ちる/振り直されると、代入順序に一致する行が'
                '見つからず値が消える(:987-988)'
                .format(table_name, sorted(used), sorted(table_orders)))

        # (3) 少なくとも1つのホストグループが、メンバー全員のレコードに展開されている
        expanded = [group for group in multi.values() if group['HOSTS'] <= system_ids]
        if not expanded:
            print('[integration] {}: メンバー全員のレコードが揃ったホストグループが無いため'
                  '値の複製は未検証(ホストグループ={} レコードのホスト={})'
                  .format(table_name,
                          {g['NAME']: sorted(g['HOSTS']) for g in multi.values()},
                          sorted(system_ids)))
            continue
        group = expanded[0]
        print('[integration] {} 展開を確認したホストグループ: {} → {}'
              .format(table_name, group['NAME'], sorted(group['HOSTS'])))

        # (4) 展開された行は「ホストが違うだけ」で、具体値は同じものが複製される。
        #     ホストごとに (オペレーション, Movement, カラム, 変数, 代入順序) → 具体値 を作って比べる。
        #     縦は同じカラムが代入順序ごとに別の行から来るが、代入順序ごとに変数
        #     (`MVMT_VAR_LINK_ID`)が別なのでキーは重複しない(レコードは行を特定できる情報を
        #     持たないため、行そのものは (2) で具体値から突き合わせている)
        def _fingerprint(system_id, rows=rows):
            prints = {}
            for record in rows:
                if record['SYSTEM_ID'] != system_id:
                    continue
                # 項目なしメニューのレコード(`STATUS='skip'`)はカラムの情報を持たないので
                # `.get` で引く(ホストグループ利用シートには項目なしの行は無いが、念のため)
                key = (record['OPERATION_ID'], record['MOVEMENT_ID'], record.get('COL_NAME'),
                       record['MVMT_VAR_LINK_ID'], record.get('ASSIGN_SEQ'),
                       record.get('COL_SEQ_COMBINATION_ID'), record.get('REG_TYPE'))
                prints.setdefault(key, set()).add(record['VARS_ENTRY'])
            return prints

        members = sorted(group['HOSTS'])
        base = _fingerprint(members[0])
        assert base, '{}: ホスト {} のレコードが空(展開されていない)'.format(
            table_name, members[0])
        for system_id in members[1:]:
            other = _fingerprint(system_id)
            missing = sorted(set(base) - set(other))
            extra = sorted(set(other) - set(base))
            assert not missing and not extra, (
                '{}: 展開後のホスト {} と {} で登録対象のカラム/行が違う(不足 {} / 余分 {})'
                .format(table_name, members[0], system_id, missing[:3], extra[:3]))
            differ = [key for key in base if base[key] != other[key]]
            assert not differ, (
                '{}: 展開後のホスト {} と {} で具体値が違う({}: {!r} != {!r})'
                .format(table_name, members[0], system_id, differ[0],
                        sorted(base[differ[0]]), sorted(other[differ[0]])))
        verified.append(table_name)

    if not verified:
        skip_or_fail('メンバー全員のレコードが揃ったホストグループが無いため、値の複製を'
                     '検証できない(展開待ち / `[HG]…` の行が無い。投入手順の段階7 を確認する)')

    # (5) 縦・横の両方の展開先を通していることの歯止め。
    #     ホストグループ利用 × 縦 は上記のとおり実装のコピーが噛み合う唯一の組み合わせなので、
    #     片方しか無い状態を通過扱いにしない(これは実装ではなく投入データの問題)
    observed = {kinds[table_name] for table_name in verified}
    missing_kinds = [kind for kind in (HORIZONTAL, VERTICAL) if kind not in observed]
    if missing_kinds:
        skip_or_fail('ホストグループ利用シートに {} のものが無い(展開先={})。'
                     '投入手順の段階4 の `pytest_ps_hg`(横) / `pytest_ps_hg_v`(縦)と'
                     '段階7 を確認する'
                     .format(' / '.join(missing_kinds),
                             {t: kinds[t] for t in sorted(split_tables)}))


# ======================================================================
# [INT-13] template_list / host_list が vars-listup の変数刈り取りに効く
# ======================================================================
def test_extract_variable_for_execute(target, all_sheet_data):
    """INT-13 get_data_from_all_parameter_sheet の戻りが Movement変数へマージされる

    INT-5 は `get_data_from_all_parameter_sheet` が完走することしか見ていないので、
    戻り値が空でも通ってしまう。実際の利用者は vars-listup 固有の
    `util.extract_variable_for_execute()` (backyard_main.py:83) で、
      (1) template_list(具体値にTPF変数が入っている) × tpl_vars_dict(テンプレート管理の変数定義)
      (2) host_list(具体値の作業対象ホスト) × device_vars_dict(機器一覧のインベントリファイル追加オプション)
    の2経路を Movement変数へマージする。
    ここでは実DBから取れた template_list / host_list のキーに合わせて
    tpl_vars_dict / device_vars_dict を組み立て、マージが実際に起きることを検査する。
    (WSのテンプレート管理・機器一覧の内容に依存せず、両方の経路を必ず通せる)

    skip の判定は**経路ごと**に行う。`template_list and host_list` のどちらか片方でも
    空なら、その経路のマージは1度も実行されないため、
    「片方だけデータがある」状態を通過扱いにしないこと(TPF変数の刈り取りが
    丸ごと壊れても host_list 側だけで pass してしまう)。
    """
    from backyard_libs.ansible_driver.functions import util

    _, _, ws_db = target

    _, template_list, host_list, _, _ = all_sheet_data('DF_LEGACY_DRIVER_ID')
    if not template_list:
        skip_or_fail('具体値に TPF 変数を含む行が無いため、template_list 経路の'
                     '変数刈り取りを検査できない(投入手順の段階6 を実施すると検証対象になる)')
    if not host_list:
        skip_or_fail('具体値が登録されていないため、host_list 経路の変数刈り取りを検査できない')

    # 実データのキーに対応する「変数を持っている」入力を作る
    tpl_vars_dict = {}
    for tpl_vars in template_list.values():
        for tpl_var_name in tpl_vars:
            tpl_vars_dict[tpl_var_name] = {'IT_PYTEST_TPL_VAR'}
    device_vars_dict = {}
    for operations in host_list.values():
        for hosts in operations.values():
            for system_id in hosts:
                device_vars_dict[system_id] = {'IT_PYTEST_DEVICE_VAR'}

    # マージ先は空から始める(Movement変数が既にあるかどうかに影響されないようにする)
    mov_vars_dict = {movement_id: set()
                     for movement_id in set(template_list) | set(host_list)}

    result = util.extract_variable_for_execute(mov_vars_dict, tpl_vars_dict, device_vars_dict, ws_db)

    assert result is mov_vars_dict, '引数の辞書をそのまま返す前提が崩れている'
    for movement_id in template_list:
        assert 'IT_PYTEST_TPL_VAR' in result[movement_id], \
            'MOVEMENT_ID={} にテンプレート由来の変数がマージされていない'.format(movement_id)
    for movement_id in host_list:
        assert 'IT_PYTEST_DEVICE_VAR' in result[movement_id], \
            'MOVEMENT_ID={} に機器一覧由来の変数がマージされていない'.format(movement_id)
