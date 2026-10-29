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
SubValueAutoReg.createQuerySelectCMDB の単体テスト + getCMDBdata との連結テスト

位置づけ:
  test_SubValueAutoReg_getCMDBdata.py は build_inputs で SELECT文を**自前に組み立てて**
  getCMDBdata に渡すため、createQuerySelectCMDB は一度も呼ばれない。
  つまり「SQLを生成する側」と「SQL結果を読む側」の整合を誰も検証していない状態だった。
  本ファイルは
    (a) createQuerySelectCMDB 自体の分岐網羅（縦/横メニュー判定・INPUT_ORDER の出力）
    (b) 生成SQL → getCMDBdata の連結（getCMDBdata が参照するカラムが SELECT されているか）
  を担う。

対象メソッドの呼び出し規約:
    inout_tableNameToSqlList = instance.createQuerySelectCMDB(
        in_tableNameToMenuIdList,      # {table: menu_id}
        in_tabColNameToValAssRowList,  # {table: {'DATA_JSON': {idx: col_data}}}
        in_tableNameToPKeyNameList,    # {table: 主キー名}
        WS_DB,                         # mock_ws_db
    )
"""

import pytest

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

from .subvalue_autoreg_support import (
    HOST_CNT_COL,
    PKEY_COL,
    MockWsDb,
    assert_log_contains,
    assert_log_not_contains,
    make_cmdb_row,
    make_col_data,
)

TABLE = 'T_PARAM_SHEET'
MENU_ID = 'menu-001'
MENU_NAME_REST = 'menu_a'
PKEY_NAME = 'ROW_ID'


# ----------------------------------------------------------------------
# ヘルパ
# ----------------------------------------------------------------------
def build_query_inputs(tables):
    """createQuerySelectCMDB の入力3辞書を組み立てる。

    Args:
        tables: [(table_name, menu_id, [col_data, ...]), ...]

    Returns:
        (in_tableNameToMenuIdList, in_tabColNameToValAssRowList, in_tableNameToPKeyNameList)

    Note:
        `col_list` のキーは read_val_assign が入れる `COL_NAME`
        ([SubValueAutoReg.py:1803-1804](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1803-L1804))で、
        パラメータシートは全カラムの実体が DATA_JSON なので常に 'DATA_JSON' 単独になる。
    """
    menu_ids, col_lists, pkeys = {}, {}, {}
    for table_name, menu_id, col_data_list in tables:
        menu_ids[table_name] = menu_id
        col_lists[table_name] = {'DATA_JSON': {i: c for i, c in enumerate(col_data_list)}}
        pkeys[table_name] = PKEY_NAME
    return menu_ids, col_lists, pkeys


def vertical_col(**overrides):
    """縦メニュー用の代入値自動登録設定(COLUMN_ASSIGN_SEQ あり)。"""
    overrides.setdefault('COLUMN_ASSIGN_SEQ', '1')
    return make_col_data(**overrides)


@pytest.fixture
def query_instance(mock_g, mock_ws_db):
    """createQuerySelectCMDB を素のまま呼べる SubValueAutoReg インスタンス。"""
    return SubValueAutoReg(in_driver_name=AnscConst.DF_LEGACY_ROLE_DRIVER_ID, ws_db=mock_ws_db)


# ======================================================================
# [Q1] 縦メニュー判定（table_columns_get への置き換え）
# ======================================================================
class TestVerticalMenuDetection:
    """[Q1] 縦メニュー(INPUT_ORDER 列)の判定をテーブル構成から行う

    改修前は `table_select(table_name, "WHERE DISUSE_FLAG = '0'")` で**レコードを全件取得**し、
    その1件目に INPUT_ORDER キーがあるかで判定していた。
    そのため**レコード0件の縦メニューでは input_order_flg が False のまま**になり、
    横メニュー扱い → MSG-10939 を誤出力 → テーブルごとスキップ(SQL自体が生成されない)
    → getCMDBdata の「レコードなし」MSG-10368 すら出ない、という状態だった。
    改修後は `table_columns_get`(SHOW COLUMNS) で判定するためレコード件数に依存しない。
    """

    def test_vertical_zero_records_still_detected(self, query_instance, mock_ws_db, mock_g):
        """Q1-1 縦メニュー × レコード0件でも縦と判定される（今回の修正の回帰テスト）

        改修前はここで MSG-10939 が出てテーブルがスキップされていた。
        """
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, [vertical_col()])])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=True)
        # レコードは1件も無い（param_sheet_rows / cmdb_rows を仕込まない）

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert TABLE in sqls, "レコード0件の縦メニューがスキップされている"
        assert 'TBL_A.INPUT_ORDER' in sqls[TABLE]
        assert_log_not_contains(mock_g, "MSG-10939")
        assert_log_not_contains(mock_g, "MSG-10940")

    def test_vertical_with_records_detected(self, query_instance, mock_ws_db, mock_g):
        """Q1-2 縦メニュー × レコードあり: レコードの有無で結果が変わらない"""
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, [vertical_col()])])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=True)
        mock_ws_db.param_sheet_rows[TABLE] = [{'ROW_ID': 'row-001', 'INPUT_ORDER': 1}]

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert 'TBL_A.INPUT_ORDER' in sqls[TABLE]
        assert_log_not_contains(mock_g, "MSG-10939")

    def test_horizontal_emits_empty_input_order(self, query_instance, mock_ws_db, mock_g):
        """Q1-3 横メニュー: INPUT_ORDER 列が無いので `'' AS INPUT_ORDER` を出す

        getCMDBdata が row["INPUT_ORDER"] を無条件参照する
        ([:987](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L987))ため、
        横メニューでもキー自体は必ず結果セットに載せる必要がある。
        """
        menu_ids, col_lists, pkeys = build_query_inputs(
            [(TABLE, MENU_ID, [make_col_data(COLUMN_ASSIGN_SEQ=None)])])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=False)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert "'' AS INPUT_ORDER" in sqls[TABLE]
        assert 'TBL_A.INPUT_ORDER' not in sqls[TABLE]
        assert_log_not_contains(mock_g, "MSG-10939")
        assert_log_not_contains(mock_g, "MSG-10940")

    def test_uses_show_columns_not_full_select(self, query_instance, mock_ws_db, mock_g):
        """Q1-4 判定に table_columns_get を使い、テーブル全件SELECT(table_select)はしない

        改修前は縦メニュー判定のためにパラメータシートを**毎テーブル全件取得**していた。
        性能面の改修が戻っていないことを固定する。
        """
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, [vertical_col()])])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=True)

        query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert TABLE in mock_ws_db.table_columns_get_log
        assert [c for c in mock_ws_db.table_select_log if c[0] == TABLE] == [], \
            "縦メニュー判定でパラメータシートを全件SELECTしている"


# ======================================================================
# [Q2] INPUT_ORDER の出力回数
# ======================================================================
class TestInputOrderEmittedOnce:
    """[Q2] INPUT_ORDER は設定レコード数に関係なく1回だけ出力される

    改修前は代入値自動登録設定のレコードごとのループ内で `make_sql +=` していたため、
    設定がN件あると `INPUT_ORDER` がSELECT句にN回並んでいた
    (MySQL では重複列は許容されるが無駄。dict カーソルでは最後が残る)。
    """

    @pytest.mark.parametrize("col_count", [1, 2, 3])
    @pytest.mark.parametrize("vertical", [True, False])
    def test_input_order_appears_once(self, query_instance, mock_ws_db, mock_g,
                                      vertical, col_count):
        """Q2-1 設定レコード数 × 縦/横 で INPUT_ORDER の出現回数が常に1"""
        if vertical:
            cols = [vertical_col(COLUMN_ID='col-{}'.format(i), COLUMN_ASSIGN_SEQ=str(i + 1))
                    for i in range(col_count)]
        else:
            cols = [make_col_data(COLUMN_ID='col-{}'.format(i), COLUMN_ASSIGN_SEQ=None)
                    for i in range(col_count)]
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, cols)])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=vertical)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert sqls[TABLE].count('INPUT_ORDER') == 1


# ======================================================================
# [Q3] 生成SQLの形（getCMDBdata との契約）
# ======================================================================
class TestGeneratedSqlShape:
    """[Q3] getCMDBdata が参照するカラムがすべて SELECT されているか"""

    def _make_sql(self, query_instance, mock_ws_db, vertical=True):
        col = vertical_col() if vertical else make_col_data(COLUMN_ASSIGN_SEQ=None)
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, [col])])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=vertical)
        return query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)[TABLE]

    @pytest.mark.parametrize("vertical", [True, False])
    def test_selects_columns_getcmdbdata_reads(self, query_instance, mock_ws_db, mock_g, vertical):
        """Q3-1 OPERATION_ID / HOST_ID / 紐付件数 / 主キー / INPUT_ORDER が揃っている"""
        sql = self._make_sql(query_instance, mock_ws_db, vertical)

        assert 'AS  OPERATION_ID' in sql          # 廃止オペは NULL になるサブクエリ
        assert 'TBL_A.HOST_ID' in sql
        assert 'TBL_A.{} AS %s'.format(PKEY_NAME) in sql
        assert 'INPUT_ORDER' in sql
        assert "FROM `{}` TBL_A".format(TABLE) in sql
        assert "WHERE DISUSE_FLAG = '0'" in sql

    @pytest.mark.parametrize("vertical", [True, False])
    def test_placeholder_order_matches_getcmdbdata(self, query_instance, mock_ws_db,
                                                   mock_g, vertical):
        """Q3-2 %s は2個で、順序が getCMDBdata のバインド順(紐付件数 → 主キー)と一致する

        getCMDBdata は `[DF_ITA_LOCAL_HOST_CNT, DF_ITA_LOCAL_PKEY]`(+ オペ指定時はその後)の
        順でバインドする([:880-884](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L880-L884))ため、
        SELECT句側の別名の出現順が入れ替わると結果セットのキーが入れ替わる。
        """
        sql = self._make_sql(query_instance, mock_ws_db, vertical)

        assert sql.count('%s') == 2
        # 1つ目の %s は機器一覧の紐付件数の別名、2つ目は主キーの別名
        assert sql.index(') AS %s') < sql.index('TBL_A.{} AS %s'.format(PKEY_NAME))

    @pytest.mark.parametrize("vertical", [True, False])
    def test_data_json_not_selected(self, query_instance, mock_ws_db, mock_g, vertical):
        """Q3-3 具体値(DATA_JSON)は SELECT しない

        具体値は rest_filter 経由で取得する方式になったため、この SELECT では不要。
        col_sql は「SELECT対象の項目が1つ以上あるか」の判定にのみ使われる。
        """
        sql = self._make_sql(query_instance, mock_ws_db, vertical)

        assert 'DATA_JSON' not in sql

    def test_no_target_column_skips_table(self, query_instance, mock_ws_db, mock_g):
        """Q3-4 SELECT対象の項目が無い(col_list が空)テーブルは MSG-10356 でスキップ"""
        menu_ids = {TABLE: MENU_ID}
        col_lists = {TABLE: {}}          # col_sql が組み立てられない
        pkeys = {TABLE: PKEY_NAME}
        mock_ws_db.set_param_sheet_table(TABLE, vertical=False)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert TABLE not in sqls
        assert_log_contains(mock_g, "MSG-10356")


# ======================================================================
# [Q4] 代入値自動登録設定とパラメータシートの縦/横の不整合
# ======================================================================
class TestVerticalSettingMismatch:
    """[Q4] COLUMN_ASSIGN_SEQ(設定側) と INPUT_ORDER 列(テーブル側)の不整合"""

    def test_seq_set_but_table_is_horizontal(self, query_instance, mock_ws_db, mock_g):
        """Q4-1 設定は縦(COLUMN_ASSIGN_SEQ有) / テーブルは横: MSG-10939 + テーブルskip"""
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, [vertical_col()])])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=False)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert TABLE not in sqls
        assert_log_contains(mock_g, "MSG-10939")

    def test_seq_none_but_table_is_vertical(self, query_instance, mock_ws_db, mock_g):
        """Q4-2 設定は横(COLUMN_ASSIGN_SEQ None) / テーブルは縦: MSG-10940 + テーブルskip"""
        menu_ids, col_lists, pkeys = build_query_inputs(
            [(TABLE, MENU_ID, [make_col_data(COLUMN_ASSIGN_SEQ=None)])])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=True)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert TABLE not in sqls
        assert_log_contains(mock_g, "MSG-10940")

    def test_partial_mismatch_keeps_table(self, query_instance, mock_ws_db, mock_g):
        """Q4-3 縦テーブルに 縦設定+横設定 が混在: 横設定だけ除外しテーブルは残る

        data_cnt > 0 なので INPUT_ORDER は出力される。
        「1件でも有効な設定が残ればテーブルを処理する」という挙動の固定。
        """
        cols = [vertical_col(COLUMN_ID='col-vertical'),
                make_col_data(COLUMN_ID='col-horizontal', COLUMN_ASSIGN_SEQ=None)]
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, cols)])
        mock_ws_db.set_param_sheet_table(TABLE, vertical=True)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert TABLE in sqls
        assert sqls[TABLE].count('TBL_A.INPUT_ORDER') == 1
        assert_log_contains(mock_g, "MSG-10940")      # 横設定側は除外
        assert_log_not_contains(mock_g, "MSG-10939")


# ======================================================================
# [Q5] 複数テーブル
# ======================================================================
class TestMultipleTables:
    """[Q5] 複数の紐付メニュー(テーブル)を1回で処理する"""

    def test_two_tables_generate_independent_sql(self, query_instance, mock_ws_db, mock_g):
        """Q5-1 縦メニューと横メニューが混在しても互いに影響しない

        input_order_flg / data_cnt はテーブル単位で初期化されるため、
        1テーブル目の縦判定が2テーブル目に漏れないことを固定する。
        """
        table_v, table_h = 'T_PARAM_SHEET_V', 'T_PARAM_SHEET_H'
        menu_ids, col_lists, pkeys = build_query_inputs([
            (table_v, 'menu-v', [vertical_col()]),
            (table_h, 'menu-h', [make_col_data(COLUMN_ASSIGN_SEQ=None)]),
        ])
        mock_ws_db.set_param_sheet_table(table_v, vertical=True)
        mock_ws_db.set_param_sheet_table(table_h, vertical=False)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert set(sqls.keys()) == {table_v, table_h}
        assert 'TBL_A.INPUT_ORDER' in sqls[table_v]
        assert "'' AS INPUT_ORDER" in sqls[table_h]
        assert "FROM `{}` TBL_A".format(table_v) in sqls[table_v]
        assert "FROM `{}` TBL_A".format(table_h) in sqls[table_h]

    def test_skipped_table_does_not_affect_next(self, query_instance, mock_ws_db, mock_g):
        """Q5-2 不整合でスキップされたテーブルの後続テーブルは正常に生成される"""
        table_bad, table_ok = 'T_PARAM_SHEET_NG', 'T_PARAM_SHEET_OK'
        menu_ids, col_lists, pkeys = build_query_inputs([
            (table_bad, 'menu-ng', [vertical_col()]),                        # 設定は縦
            (table_ok, 'menu-ok', [make_col_data(COLUMN_ASSIGN_SEQ=None)]),  # 設定は横
        ])
        mock_ws_db.set_param_sheet_table(table_bad, vertical=False)          # テーブルは横 → 不整合
        mock_ws_db.set_param_sheet_table(table_ok, vertical=False)

        sqls = query_instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, mock_ws_db)

        assert set(sqls.keys()) == {table_ok}
        assert_log_contains(mock_g, "MSG-10939")


# ======================================================================
# [Q6] createQuerySelectCMDB → getCMDBdata の連結
# ======================================================================
class _ProjectingWsDb(MockWsDb):
    """生成SQLのSELECT句に載っているカラムだけを返す MockWsDb。

    素の MockWsDb は SQL を無視して cmdb_rows をそのまま返すため、
    「getCMDBdata が参照するカラムを createQuerySelectCMDB が SELECT していない」
    という不整合(= 本番では KeyError)を検知できない。
    本モックは生成SQLを解釈して結果セットを射影し、本物のカーソルの挙動に寄せる。
    """

    #: 射影対象。結果セットのキー名 = SELECT句に現れる文字列
    PROJECTED_KEYS = ('OPERATION_ID', 'HOST_ID', 'INPUT_ORDER', 'DATA_JSON',
                      HOST_CNT_COL, PKEY_COL)

    def selected_keys(self, sql, params):
        """SELECT句(= 最初の "FROM `" より前)に現れるキーを返す。

        別名が `AS %s` になっている箇所はバインド値で解決してから判定する。
        サブクエリの FROM はバッククォートを使わないため "FROM `" で切って良い。
        """
        resolved = sql
        for param in (params or []):
            resolved = resolved.replace('%s', str(param), 1)
        select_part = resolved.split('FROM `')[0]
        return {key for key in self.PROJECTED_KEYS if key in select_part}

    def sql_execute(self, sql, params=None):
        rows = super().sql_execute(sql, params)
        if 'FROM `' not in sql:
            return rows
        keys = self.selected_keys(sql, params)
        return [{k: v for k, v in row.items() if k in keys} for row in rows]


@pytest.fixture
def projecting_ws_db():
    """生成SQLに従って結果セットを射影する WS_DB モック。"""
    return _ProjectingWsDb()


class TestQueryToGetCMDBdata:
    """[Q6] 生成SQLをそのまま getCMDBdata に流す

    ここが「SQL生成側」と「SQL結果を読む側」の唯一の接点テスト。
    getCMDBdata 側のテストは SELECT文を自前に組み立てているため、
    createQuerySelectCMDB が列を落としても検知できない。
    """

    def _run(self, instance, ws_db, vertical, rows, if_null='1'):
        col = vertical_col() if vertical else make_col_data(COLUMN_ASSIGN_SEQ=None)
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, [col])])
        ws_db.set_param_sheet_table(TABLE, vertical=vertical)
        ws_db.cmdb_rows[TABLE] = rows

        sqls = instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, ws_db)
        return sqls, instance.getCMDBdata(sqls, menu_ids, col_lists, None, ws_db, if_null)

    @pytest.mark.parametrize("vertical", [True, False])
    def test_end_to_end_registers_record(self, make_subvalue_autoreg, projecting_ws_db,
                                         mock_g, vertical):
        """Q6-1 生成SQL → getCMDBdata で具体値が登録される(縦/横)

        生成SQLに INPUT_ORDER が無ければ getCMDBdata の row["INPUT_ORDER"] で
        KeyError になるため、このテストは列落ちを直接検知する。
        """
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'value1'}}})
        rows = [make_cmdb_row(row_id='row-001', input_order='1' if vertical else '')]

        _, (vars_ass_list, array_vars_ass_list) = self._run(
            instance, projecting_ws_db, vertical, rows)

        assert array_vars_ass_list == []
        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['VARS_ENTRY'] == 'value1'
        assert vars_ass_list[0]['STATUS'] is True

    @pytest.mark.parametrize("vertical", [True, False])
    def test_result_row_has_all_keys_getcmdbdata_reads(self, make_subvalue_autoreg,
                                                       projecting_ws_db, mock_g, vertical):
        """Q6-2 射影後の結果セットに getCMDBdata が読むキーが揃っている"""
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        rows = [make_cmdb_row(row_id='row-001', input_order='1' if vertical else '')]
        sqls, _ = self._run(instance, projecting_ws_db, vertical, rows)

        keys = projecting_ws_db.selected_keys(
            sqls[TABLE], [HOST_CNT_COL, PKEY_COL])
        assert {'OPERATION_ID', 'HOST_ID', 'INPUT_ORDER', HOST_CNT_COL, PKEY_COL} <= keys

    def test_vertical_zero_records_logs_msg_10368(self, make_subvalue_autoreg,
                                                  projecting_ws_db, mock_g):
        """Q6-3 縦メニュー × レコード0件: MSG-10368(レコードなし)が出る

        改修前は createQuerySelectCMDB が MSG-10939 を出してテーブルをスキップしていたため、
        「レコードが無い」という本来出るべきログ(MSG-10368)に到達しなかった。
        今回の「縦メニューの0レコード時のログ」修正のエンドツーエンド回帰テスト。
        """
        instance = make_subvalue_autoreg(param_sheets={})

        sqls, (vars_ass_list, array_vars_ass_list) = self._run(
            instance, projecting_ws_db, True, [])

        assert TABLE in sqls
        assert vars_ass_list == []
        assert array_vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10368")
        assert_log_not_contains(mock_g, "MSG-10939")

    def test_operation_filter_binds_after_alias_params(self, make_subvalue_autoreg,
                                                       projecting_ws_db, mock_g):
        """Q6-4 オペ指定(parameter_sheet経路)でもバインド順が崩れない

        getCMDBdata は生成SQLの末尾に `AND OPERATION_ID = %s` を足して
        reg_operation_id を**最後**にバインドする。別名用の %s との順序関係を固定する。
        """
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        col = make_col_data(COLUMN_ASSIGN_SEQ=None)
        menu_ids, col_lists, pkeys = build_query_inputs([(TABLE, MENU_ID, [col])])
        projecting_ws_db.set_param_sheet_table(TABLE, vertical=False)
        projecting_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001',
                                                           operation_id='ope-XYZ')]

        sqls = instance.createQuerySelectCMDB(menu_ids, col_lists, pkeys, projecting_ws_db)
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, 'ope-XYZ',
                                                projecting_ws_db, '1')

        cmdb_calls = [c for c in projecting_ws_db.sql_log
                      if "FROM `{}`".format(TABLE) in c[0]]
        sql, params = cmdb_calls[-1]
        assert params == [HOST_CNT_COL, PKEY_COL, 'ope-XYZ']
        assert sql.rstrip().endswith('AND OPERATION_ID = %s')
        assert len(vars_ass_list) == 1
