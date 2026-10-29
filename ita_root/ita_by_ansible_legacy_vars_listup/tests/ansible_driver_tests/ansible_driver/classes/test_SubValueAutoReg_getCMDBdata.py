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
SubValueAutoReg.getCMDBdata のテスト

本ファイルはテスト基盤(conftest.py / subvalue_autoreg_support.py)の
動作確認と、パターン表を埋めていくための雛形を兼ねる。

getCMDBdata の呼び出し規約:
    ina_vars_ass_list, ina_array_vars_ass_list = instance.getCMDBdata(
        in_tableNameToSqlList,          # {table: SELECT文}
        in_tableNameToMenuIdList,       # {table: menu_id}
        in_tabColNameToValAssRowList,   # {table: {'DATA_JSON': {idx: col_data}}}
        reg_operation_id,               # None:全件 / 値:オペ指定
        WS_DB,                          # mock_ws_db
        g_null_data_handling_def,       # IF情報のNULL連携デフォルト
    )
"""

import os
from unittest.mock import patch

import pytest

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

from .subvalue_autoreg_support import (
    make_col_data,
    make_cmdb_row,
    build_inputs,
    CountingParamSheet,
    assert_log_contains,
    assert_log_not_contains,
    disused_id_value,
    TPF_REF_TABLE,
    TPF_REF_COL,
    CPF_REF_TABLE,
    CPF_REF_COL,
    ID_REF_TABLE,
    ID_REF_PKEY,
    ID_REF_COL,
    PS_REF_TABLE,
    PS_REF_PKEY,
    PS_REF_COL,
)


class TestGetCMDBdataFoundation:
    """基盤(モック/戻り値/ログ捕捉)が機能することを確認する代表ケース。"""

    def test_normal_value_std_returns_one_record(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        正常系: Value型 / 一般変数 / 具体値あり
        期待値: 一般変数リストに1件、多次元リストは空、STATUS=True
        """
        table = 'T_PARAM_SHEET'
        col = make_col_data(COLUMN_NAME_REST='column_a', MENU_NAME_REST='menu_a')
        sqls, menu_ids, col_lists = build_inputs(table_name=table, menu_id='menu-001', col_data_list=[col])

        # 紐付メニュー(パラメータシート)のレコード
        mock_ws_db.cmdb_rows[table] = [make_cmdb_row(row_id='row-001')]

        instance = make_subvalue_autoreg(
            driver_id=AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
            param_sheets={'menu_a': {'row-001': {'column_a': 'value1'}}},
        )

        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, 'TRUE'
        )

        assert len(vars_ass_list) == 1
        assert array_vars_ass_list == []
        rec = vars_ass_list[0]
        assert rec['TABLE_NAME'] == table
        assert rec['OPERATION_ID'] == 'ope-001'
        assert rec['SYSTEM_ID'] == 'host-001'
        assert rec['VARS_ENTRY'] == 'value1'
        assert rec['STATUS'] is True

    def test_no_operation_id_skips_and_logs(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        異常系: 紐付メニューのオペレーションID未登録
        期待値: レコードは生成されず、MSG-10360 がログ出力される
        """
        table = 'T_PARAM_SHEET'
        sqls, menu_ids, col_lists = build_inputs(table_name=table)
        mock_ws_db.cmdb_rows[table] = [make_cmdb_row(row_id='row-001', operation_id='')]

        instance = make_subvalue_autoreg(param_sheets={'menu_a': {'row-001': {'column_a': 'v'}}})
        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, 'TRUE'
        )

        assert vars_ass_list == []
        assert array_vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10360")

    def test_host_not_linked_skips_and_logs(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        異常系: 機器一覧にホストが紐付いていない(件数0)
        期待値: レコードは生成されず、MSG-10359 がログ出力される
        """
        table = 'T_PARAM_SHEET'
        sqls, menu_ids, col_lists = build_inputs(table_name=table)
        mock_ws_db.cmdb_rows[table] = [make_cmdb_row(row_id='row-001', host_cnt=0)]

        instance = make_subvalue_autoreg(param_sheets={'menu_a': {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, 'TRUE')

        assert vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10359")

    def test_no_records_logs_msg_10368(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        レコード数0: 紐付メニューにレコードなし
        期待値: 戻り値は空、MSG-10368 がログ出力される
        """
        table = 'T_PARAM_SHEET'
        sqls, menu_ids, col_lists = build_inputs(table_name=table)
        mock_ws_db.cmdb_rows[table] = []  # 0件

        instance = make_subvalue_autoreg(param_sheets={})
        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, 'TRUE'
        )

        assert vars_ass_list == []
        assert array_vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10368")

    def test_col_group_id_none_status_skip(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        カラム具体値「無」(項目なし=COL_GROUP_ID None)
        期待値: STATUS='skip' のレコードが1件生成される
        """
        table = 'T_PARAM_SHEET'
        col = make_col_data(COL_GROUP_ID=None)
        sqls, menu_ids, col_lists = build_inputs(table_name=table, col_data_list=[col])
        mock_ws_db.cmdb_rows[table] = [make_cmdb_row(row_id='row-001')]

        instance = make_subvalue_autoreg(param_sheets={'menu_a': {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, 'TRUE')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['STATUS'] == 'skip'

    def test_tpf_variable_column_wraps_value(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        カラム具体値「TPF」: TPF変数カラムの具体値は "'{{ ... }}'" で囲まれる
        """
        table = 'T_PARAM_SHEET'
        col = make_col_data(REF_TABLE_NAME=TPF_REF_TABLE, REF_COL_NAME=TPF_REF_COL)
        sqls, menu_ids, col_lists = build_inputs(table_name=table, col_data_list=[col])
        mock_ws_db.cmdb_rows[table] = [make_cmdb_row(row_id='row-001')]

        instance = make_subvalue_autoreg(
            param_sheets={'menu_a': {'row-001': {'column_a': 'TPF_SAMPLE'}}},
        )
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, 'TRUE')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['VARS_ENTRY'] == "'{{ TPF_SAMPLE }}'"

    def test_reg_operation_id_passed_as_sql_param(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        オペ指定(reg_operation_id 指定)時は SELECT に OPERATION_ID 条件とパラメータが付与される
        """
        table = 'T_PARAM_SHEET'
        sqls, menu_ids, col_lists = build_inputs(table_name=table)
        mock_ws_db.cmdb_rows[table] = [make_cmdb_row(row_id='row-001', operation_id='ope-XYZ')]

        instance = make_subvalue_autoreg(param_sheets={'menu_a': {'row-001': {'column_a': 'v'}}})
        instance.getCMDBdata(sqls, menu_ids, col_lists, 'ope-XYZ', mock_ws_db, 'TRUE')

        # 紐付メニュー本体の SELECT(=対象テーブルを含むSQL)に reg_operation_id が渡っている
        cmdb_calls = [c for c in mock_ws_db.sql_log if "FROM `{}`".format(table) in c[0]]
        assert cmdb_calls, "紐付メニューへのSELECTが発行されていない"
        sql, params = cmdb_calls[-1]
        assert "OPERATION_ID = %s" in sql
        assert 'ope-XYZ' in params

    def test_no_debug_log_capture_baseline(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        ログ捕捉ヘルパの土台確認: 正常系では MSG-10360/10359/10368 は出ない
        """
        table = 'T_PARAM_SHEET'
        sqls, menu_ids, col_lists = build_inputs(table_name=table)
        mock_ws_db.cmdb_rows[table] = [make_cmdb_row(row_id='row-001')]

        instance = make_subvalue_autoreg(param_sheets={'menu_a': {'row-001': {'column_a': 'v'}}})
        instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, 'TRUE')

        assert_log_not_contains(mock_g, "MSG-10360")
        assert_log_not_contains(mock_g, "MSG-10359")
        assert_log_not_contains(mock_g, "MSG-10368")


class TestGetCMDBdataPatternTable:
    """パターン表に対応するケース。"""

    def test_bundle_no_hg_no_rec10_samehost_multiope_valid_value_present_value_noseq_nullfalse_driverL(
            self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """
        パターン:
          バンドル:無 / ホストグループ:無 /
          レコード:10(同一ホスト・複数オペ) / レコード有効性:有効 /
          カラム具体値:有 / 登録方式:Value / 代入順序:無 /
          NULL連携:FALSE / ドライバ:L / メンバ変数:無

        期待値:
          同一ホスト・別オペの10レコードがすべて代入値管理(一般変数)に登録される
          (STATUS=True が10件、多次元リストは空)
        """
        table = 'T_ANSL_PARAM_SHEET'
        menu_name_rest = 'menu_legacy'

        # ドライバ:L(Legacy) = 一般変数(STD) / COL_SEQ_COMBINATION_ID なし
        # 登録方式:Value / 代入順序:無(ASSIGN_SEQ=None) / NULL連携:FALSE
        # バンドル:無 = 横メニュー(レコード INPUT_ORDER 空 / COLUMN_ASSIGN_SEQ None)。
        # ホストグループ:無・メンバ変数:無 は
        # getCMDBdata より上流(read_val_assign/SQL)の条件のため、
        # ここでは「単一テーブル・単一カラム」の col_data として表現する。
        col = make_col_data(
            COL_TYPE=AnscConst.DF_COL_TYPE_VAL,          # 登録方式:Value
            VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_STD,     # ドライバL相当(一般変数)
            COL_SEQ_COMBINATION_ID=None,                 # メンバ変数:無
            ASSIGN_SEQ=None,                             # 代入順序:無
            COLUMN_ASSIGN_SEQ=None,                      # バンドル:無 = 横メニュー
            NULL_DATA_HANDLING_FLG='0',                  # NULL連携:FALSE
            COLUMN_CLASS='1',                            # 通常カラム(FileUpload/Passwordでない)
            REF_TABLE_NAME=None,                         # TPF/CPFでない
            COLUMN_NAME_REST='column_a',
            MENU_NAME_REST=menu_name_rest,
            MOVEMENT_ID='mov-001',
            MVMT_VAR_LINK_ID='vlink-001',
        )
        sqls, menu_ids, col_lists = build_inputs(
            table_name=table, menu_id='menu-L-001', col_data_list=[col]
        )

        # レコード数:10 / 同一ホスト('host-001') / 複数オペ(ope-001..ope-010) / 有効(件数1)
        host_id = 'host-001'
        rows = []
        param_rows = {}
        for i in range(1, 11):
            row_id = 'row-{:03d}'.format(i)
            rows.append(make_cmdb_row(
                row_id=row_id,
                operation_id='ope-{:03d}'.format(i),
                host_id=host_id,
                host_cnt=1,          # 機器一覧に紐付あり(有効)
                input_order='',      # バンドル:無 = 横メニュー
            ))
            # カラム具体値:有
            param_rows[row_id] = {'column_a': 'value-{:03d}'.format(i)}

        mock_ws_db.cmdb_rows[table] = rows

        instance = make_subvalue_autoreg(
            driver_id=AnscConst.DF_LEGACY_DRIVER_ID,   # ドライバ:L
            param_sheets={menu_name_rest: param_rows},
        )

        # NULL連携(IF情報):FALSE
        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, '0'
        )

        # 多次元(メンバ変数)は無し
        assert array_vars_ass_list == []

        # 10レコードすべてが一般変数として登録され、STATUS=True
        assert len(vars_ass_list) == 10
        assert all(rec['STATUS'] is True for rec in vars_ass_list)

        # すべて同一ホスト
        assert {rec['SYSTEM_ID'] for rec in vars_ass_list} == {host_id}

        # 複数オペ(10種類のオペレーションID)
        assert {rec['OPERATION_ID'] for rec in vars_ass_list} == \
            {'ope-{:03d}'.format(i) for i in range(1, 11)}

        # 具体値がオペ毎に正しく紐付いている / Value型 / 一般変数
        by_ope = {rec['OPERATION_ID']: rec for rec in vars_ass_list}
        for i in range(1, 11):
            rec = by_ope['ope-{:03d}'.format(i)]
            assert rec['VARS_ENTRY'] == 'value-{:03d}'.format(i)
            assert rec['REG_TYPE'] == 'Value'
            assert rec['VAR_TYPE'] == AnscConst.GC_VARS_ATTR_STD
            assert rec['MOVEMENT_ID'] == 'mov-001'
            assert rec['COL_SEQ_COMBINATION_ID'] is None

        # スキップ・エラー系ログは出ていない
        assert_log_not_contains(mock_g, "MSG-10359")
        assert_log_not_contains(mock_g, "MSG-10360")
        assert_log_not_contains(mock_g, "MSG-10361")
        assert_log_not_contains(mock_g, "MSG-10368")
        assert_log_not_contains(mock_g, "MSG-10375")  # NULLデータ連携無効による除外


# ======================================================================
# 以降、パターン表の各軸ごとのケース。
#
# 共通の土台:
#   - table       = 'T_PARAM_SHEET'（単一テーブル = バンドル/HG は上流条件のため既定形で表現）
#   - col_data    = make_col_data(...) で軸ごとに差し替え
#   - cmdb_rows   = make_cmdb_row(...) を並べる
#   - param_sheets= { menu_name_rest: { row_id: { 'column_a': 具体値 } } }
# ======================================================================
TABLE = 'T_PARAM_SHEET'
MENU_NAME_REST = 'menu_a'
MENU_ID = 'menu-001'

# ----------------------------------------------------------------------
# 戻りレコードのキー集合（= 戻り値の形の契約）
#
# キー集合を生成しているのは4箇所の dict リテラルで、いずれも内部に条件分岐を
# 持たない（`rec['X'] = ...` のような条件付きキー追加が無い）。
# そのため到達したリテラルだけでキー集合が決まり、値を左右する他の軸
# (COL_TYPE / VAL_VAR_TYPE / COLUMN_CLASS / NULL連携 / ASSIGN_SEQ /
#  COLUMN_ASSIGN_SEQ) には依存しない。
#
#   16キー : checkAndCreateVarsAssignData の STD/LIST 用 (SubValueAutoReg.py:1375-1390)
#            と M_ARRAY 用 (:1413-1428)  ※2箇所に重複実装
#    7キー : 項目なし(skip) 縦メニュー用 (:993-999) と 横メニュー用 (:1022-1028)
#            ※こちらも2箇所に重複実装
#
# 片方のリテラルにだけキーを追加/改名する変更を検知するのが目的。
# ----------------------------------------------------------------------
EXPECTED_RECORD_KEYS = {
    'TABLE_NAME', 'COL_NAME', 'COL_ROW_ID', 'COL_CLASS', 'COL_FILEUPLOAD_PATH',
    'REG_TYPE', 'OPERATION_ID', 'MOVEMENT_ID', 'SYSTEM_ID', 'MVMT_VAR_LINK_ID',
    'ASSIGN_SEQ', 'VARS_ENTRY', 'COL_SEQ_COMBINATION_ID', 'SENSITIVE_FLAG',
    'VAR_TYPE', 'STATUS',
}

EXPECTED_SKIP_RECORD_KEYS = {
    'TABLE_NAME', 'OPERATION_ID', 'MOVEMENT_ID', 'SYSTEM_ID',
    'VARS_ENTRY', 'MVMT_VAR_LINK_ID', 'STATUS',
}


def _single_col_inputs(col):
    """1カラム分の getCMDBdata 入力3辞書を組み立てる。"""
    return build_inputs(table_name=TABLE, menu_id=MENU_ID, col_data_list=[col])


def _make_col_and_row(col_overrides, bundle):
    """バンドル(縦/横メニュー)に応じた col_data とレコードを生成する。

    バンドルはパラメータシートの形態(縦/横)を決める軸で、
    getCMDBdata 内では COLUMN_ASSIGN_SEQ(設定側) と INPUT_ORDER(レコード側) の
    突合として現れる。ここでは「処理される有効な2形態」を作る:
      - bundle='no'  : 横メニュー = INPUT_ORDER 空 / COLUMN_ASSIGN_SEQ None
      - bundle='yes' : 縦メニュー = INPUT_ORDER='1' / COLUMN_ASSIGN_SEQ='1'(一致)

    値処理ロジック(項目なし/項目削除/TPF・CPFラップ)は縦分岐・横分岐で
    重複実装されているため、値処理系ケースは両バンドルで確認する。

    注: 代入順序(ASSIGN_SEQ)はこの軸とは独立の col_data 項目なので、ここでは触らない。
    """
    overrides = dict(col_overrides)
    if bundle == 'yes':
        overrides.setdefault('COLUMN_ASSIGN_SEQ', '1')
        input_order = '1'
    else:
        input_order = ''
    col = make_col_data(**overrides)
    row = make_cmdb_row(row_id='row-001', input_order=input_order)
    return col, row


# カラム具体値の種別ごとの (id, col_data差分, 具体値, 期待結果)
#   result: 'reg'(登録) / 'skip'(STATUS='skip') / 'none'(未登録)
_VALUE_CASES = [
    ('present',     {}, 'value1',                {'result': 'reg', 'entry': 'value1'}),
    ('tpf',         {'REF_TABLE_NAME': TPF_REF_TABLE, 'REF_COL_NAME': TPF_REF_COL}, 'TPF_X',
                    {'result': 'reg', 'entry': "'{{ TPF_X }}'"}),
    ('cpf',         {'REF_TABLE_NAME': CPF_REF_TABLE, 'REF_COL_NAME': CPF_REF_COL}, 'CPF_X',
                    {'result': 'reg', 'entry': "'{{ CPF_X }}'"}),
    # 廃止TPF/CPF の具体値は ID指定カラムが返す MSG-00001 の本文そのもの。
    # getCMDBdata は ja/en 両方の文言をハードコードで部分一致判定するため、
    # 入力も **メッセージ定義から生成**して 3-4=ja / 3-5=en で両系統を通す
    # (リテラル手書きにすると定義文言が変わっても気づけない)。
    ('disused_tpf', {'REF_TABLE_NAME': TPF_REF_TABLE, 'REF_COL_NAME': TPF_REF_COL},
                    disused_id_value('x'),
                    {'result': 'none'}),
    ('disused_cpf', {'REF_TABLE_NAME': CPF_REF_TABLE, 'REF_COL_NAME': CPF_REF_COL},
                    disused_id_value('x', 'EN'),
                    {'result': 'none'}),

    # --- TPF/CPF の「名前指定」: 文字列カラムに '{{ TPF_X }}' 形式を直接入力したもの ---
    #   REF_* が無いため VariableColumnAry 判定に入らず、ラップも変換失敗判定もされない。
    #   参照先の TPF/CPF が廃止されていても getCMDBdata から見た入力は同一(値が変わらない)
    #   ため区別できず、そのまま登録される(検知は実行時のテンプレート/ファイル取得側)。
    ('name_tpf',    {}, '{{ TPF_X }}',           {'result': 'reg', 'entry': '{{ TPF_X }}'}),
    ('name_cpf',    {}, '{{ CPF_XX }}',          {'result': 'reg', 'entry': '{{ CPF_XX }}'}),

    # --- CPF/TPF 以外の ID指定(プルダウン選択) ---
    ('ref_id',      {'COLUMN_CLASS': '7', 'REF_TABLE_NAME': ID_REF_TABLE,
                     'REF_PKEY_NAME': ID_REF_PKEY, 'REF_COL_NAME': ID_REF_COL}, 'host-A',
                    {'result': 'reg', 'entry': 'host-A', 'col_class': 'IDColumn'}),
    # 廃止(参照先レコードが廃止/未登録)の場合、値は MSG-00001 の本文になるが
    # 変換失敗判定は TPF/CPF 分岐の内側にしか無いため **そのまま登録される**
    ('ref_id_disused',
                    {'COLUMN_CLASS': '7', 'REF_TABLE_NAME': ID_REF_TABLE,
                     'REF_PKEY_NAME': ID_REF_PKEY, 'REF_COL_NAME': ID_REF_COL},
                    disused_id_value('host-A'),
                    {'result': 'reg', 'entry': disused_id_value('host-A'), 'col_class': 'IDColumn'}),

    # --- パラメータシート参照機能で参照されたカラム ---
    ('ps_ref',      {'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
                     'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL}, 'ref_value',
                    {'result': 'reg', 'entry': 'ref_value', 'col_class': 'JsonIDColumn'}),
    # 参照先がパスワード列の場合 COLUMN_CLASS='26'。read_val_assign が
    # COLUMN_CLASS 8/25/26/34 で VALUE_SENSITIVE_FLAG=ON にする(:1798-1799)ため合わせて指定する。
    ('ps_ref_pw',   {'COLUMN_CLASS': '26', 'REF_TABLE_NAME': PS_REF_TABLE,
                     'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL,
                     'VALUE_SENSITIVE_FLAG': AnscConst.DF_SENSITIVE_ON}, 'ref_secret',
                    {'result': 'reg', 'entry': 'ref_secret', 'sensitive': AnscConst.DF_SENSITIVE_ON,
                     'col_class': 'JsonPasswordIDColumn'}),
    # 参照先の行が廃止された場合、パスワード列だけは **具体値が None** になる
    # (SubValueAutoReg.py:2004-2008 が JsonPasswordIDColumn では convert_value_output を
    #  通さず get_values_by_key で ID を引き直し、id_class.py:130-153 の元表が
    #  json_password_id_class.py:42 の DISUSE_FLAG='0' で絞られているため .get が None)。
    # → 他の ID系(§3-12/§3-18)のように 'ID変換失敗' 文字列にはならず「具体値:無」と同じ
    #   段階④(NULL連携)へ落ちる。SENSITIVE_FLAG は ON のまま残る点が具体値:無 と違う。
    ('ps_ref_pw_disused',
                    {'COLUMN_CLASS': '26', 'REF_TABLE_NAME': PS_REF_TABLE,
                     'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL,
                     'VALUE_SENSITIVE_FLAG': AnscConst.DF_SENSITIVE_ON}, None,
                    {'result': 'reg', 'entry': None, 'sensitive': AnscConst.DF_SENSITIVE_ON,
                     'col_class': 'JsonPasswordIDColumn'}),
    ('ps_ref_disused',
                    {'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
                     'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL},
                    disused_id_value('row-ref-001'),
                    {'result': 'reg', 'entry': disused_id_value('row-ref-001'),
                     'col_class': 'JsonIDColumn'}),
    # 参照先が日時/日付列でも COLUMN_CLASS は '21'(ps_ref と同じ)。通常の日時('5')/日付('6')列は
    # AUTOREG_HIDE_ITEM=1 で代入値自動登録設定に載らないが、参照経由だと載る(※6-2 / #3068)。
    # #3068 は**修正せず現状の動作のまま**とする方針なので、xfail ではなく
    # 通常のケースとして「日時文字列がそのまま具体値になる」ことを固定する。
    ('ps_ref_datetime',
                    {'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
                     'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL},
                    '2026/08/31 12:34:56',
                    {'result': 'reg', 'entry': '2026/08/31 12:34:56',
                     'col_class': 'JsonIDColumn'}),

    ('item_none',   {'COL_GROUP_ID': None}, 'v',  {'result': 'skip'}),
]


class TestRecordValidity:
    """[1] レコード有効性: 有効 / 廃止オペ / 廃止ホスト / ホストID未登録"""

    def test_valid_record_registers(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """1-1 有効: 1件登録され、スキップ系ログは出ない"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001')]

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['STATUS'] is True
        for code in ("MSG-10359", "MSG-10360", "MSG-10361", "MSG-10368"):
            assert_log_not_contains(mock_g, code)

    def test_disused_operation_skips_and_logs(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """1-2 廃止オペ(OPERATION_ID空): 未登録 + MSG-10360"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001', operation_id='')]

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10360")

    def test_disused_host_skips_and_logs(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """1-3 廃止ホスト(機器一覧の紐付件数0): 未登録 + MSG-10359"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001', host_cnt=0)]

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10359")

    def test_missing_host_id_skips_and_logs(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """1-4 ホストID未登録(HOST_ID空・件数は非0): 未登録 + MSG-10361"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001', host_id='', host_cnt=1)]

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10361")


class TestRecordCount:
    """[2] レコード数: 0 / 1 / 10(同一ホスト・複数オペ)"""

    def test_zero_records_logs_msg_10368(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """2-1 レコード数0: 空 + MSG-10368"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = []

        instance = make_subvalue_autoreg(param_sheets={})
        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, '1'
        )

        assert vars_ass_list == []
        assert array_vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10368")

    def test_one_record(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """2-2 レコード数1: 1件登録"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001')]

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 1

    def test_ten_records_same_host_multi_ope(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """2-3 10(同一ホスト・複数オペ): 10件全STATUS=True / 同一ホスト / オペ10種"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(1, 11):
            rid = 'row-{:03d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-{:03d}'.format(i), host_id='host-001'))
            param_rows[rid] = {'column_a': 'value-{:03d}'.format(i)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, '1'
        )

        assert array_vars_ass_list == []
        assert len(vars_ass_list) == 10
        assert all(r['STATUS'] is True for r in vars_ass_list)
        assert {r['SYSTEM_ID'] for r in vars_ass_list} == {'host-001'}
        assert {r['OPERATION_ID'] for r in vars_ass_list} == \
            {'ope-{:03d}'.format(i) for i in range(1, 11)}

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_ten_records_same_host_same_ope_dedup(self, make_subvalue_autoreg, mock_ws_db,
                                                  mock_g, bundle):
        """2-4 10(同一ホスト・同一オペ): 重複排除で 1件目 STATUS=True / 2件目以降 STATUS=False

        同一(変数リンク+作業+ホスト+オペ+ASSIGN_SEQ)は重複チェックキーが一致するため、
        checkAndCreateVarsAssignData の chk_flg=False 経路を通り STATUS=False で記録される
        (レコード自体は生成され append される)。

        レコード数 × バンドル の掛け合わせ:
          この同一キー衝突が実運用で発生する主経路は縦メニュー(バンドル有)や
          ホストグループ展開経由なので、横メニューだけでなく縦メニューでも確認する。
        """
        overrides = {'COLUMN_ASSIGN_SEQ': '1'} if bundle == 'yes' else {}
        input_order = '1' if bundle == 'yes' else ''
        col = make_col_data(**overrides)
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(1, 11):
            rid = 'row-{:03d}'.format(i)
            # 同一ホスト・同一オペ(row_idのみ異なる) -> 重複チェックキーは全件一致
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001', host_id='host-001',
                                      input_order=input_order))
            param_rows[rid] = {'column_a': 'v'}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 10
        statuses = [r['STATUS'] for r in vars_ass_list]
        assert statuses.count(True) == 1     # 最初の1件のみ登録対象
        assert statuses.count(False) == 9    # 残りは重複として STATUS=False

    def test_ten_records_multi_host_same_ope(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """2-5 10(複数ホスト・同一オペ): 10件全STATUS=True / ホスト10種 / 同一オペ"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(1, 11):
            rid = 'row-{:03d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001',
                                      host_id='host-{:03d}'.format(i)))
            param_rows[rid] = {'column_a': 'v'}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 10
        assert all(r['STATUS'] is True for r in vars_ass_list)
        assert {r['OPERATION_ID'] for r in vars_ass_list} == {'ope-001'}
        assert {r['SYSTEM_ID'] for r in vars_ass_list} == \
            {'host-{:03d}'.format(i) for i in range(1, 11)}

    def test_ten_records_multi_host_multi_ope(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """2-6 10(複数ホスト・複数オペ): 10件全STATUS=True / ホスト10種 / オペ10種"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(1, 11):
            rid = 'row-{:03d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-{:03d}'.format(i),
                                      host_id='host-{:03d}'.format(i)))
            param_rows[rid] = {'column_a': 'v'}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 10
        assert all(r['STATUS'] is True for r in vars_ass_list)
        assert {r['OPERATION_ID'] for r in vars_ass_list} == \
            {'ope-{:03d}'.format(i) for i in range(1, 11)}
        assert {r['SYSTEM_ID'] for r in vars_ass_list} == \
            {'host-{:03d}'.format(i) for i in range(1, 11)}


class TestColumnValue:
    """[3] カラム具体値: 有 / TPF / CPF / 廃止TPF / 廃止CPF /
    TPF・CPFの名前指定 / ID指定(CPF・TPF以外) / パラメータシート参照 / 項目なし / 項目削除 /
    FileUpload

    ※「無」(具体値 None)は NULL連携の分岐に入るため §6(TestNullHandling)で扱う。

    値処理は縦分岐(バンドル有)・横分岐(バンドル無)で重複実装されているため、
    bundle='no'(横)/'yes'(縦) の両方で確認する。

    ラップ('{{ ... }}')と変換失敗スキップは
    [SubValueAutoReg.py:1010-1014](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1010-L1014)
    の `REF_TABLE_NAME in VariableColumnAry and REF_COL_NAME in VariableColumnAry[...]`
    を満たす場合のみ行われる。TPF/CPF 以外の参照カラム・名前指定は
    この条件の外側なので **素の値がそのまま登録される**(廃止でもスキップされない)。
    """

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    @pytest.mark.parametrize(
        "label,overrides,value,expect", _VALUE_CASES, ids=[c[0] for c in _VALUE_CASES]
    )
    def test_column_value(self, make_subvalue_autoreg, mock_ws_db, mock_g,
                          bundle, label, overrides, value, expect):
        """3-1〜3-5, 3-8〜3-13, 3-15〜3-18: カラム具体値の種別 × バンドル(縦/横)"""
        col, row = _make_col_and_row(overrides, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(
            driver_id=AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': value}}},
        )
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        if expect['result'] == 'reg':
            assert len(vars_ass_list) == 1
            # 登録対象(STATUS=True)であること。重複チェックに引っかかると STATUS=False の
            # 「登録されないレコード」になるため、件数と値だけでは登録の成立を保証できない。
            assert vars_ass_list[0]['STATUS'] is True
            assert vars_ass_list[0]['VARS_ENTRY'] == expect['entry']
            if 'sensitive' in expect:
                assert vars_ass_list[0]['SENSITIVE_FLAG'] == expect['sensitive']
            if 'col_class' in expect:
                # COLUMN_CLASS -> カラムクラス名(マスタ引き)が壊れていないことも固定する
                assert vars_ass_list[0]['COL_CLASS'] == expect['col_class']
        elif expect['result'] == 'skip':
            assert len(vars_ass_list) == 1
            assert vars_ass_list[0]['STATUS'] == 'skip'
        else:  # 'none' = 未登録
            assert vars_ass_list == []

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_deleted_column_is_not_registered(self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle):
        """3-19 項目削除(具体値に当該カラムのキーが無い): 未登録(縦/横)

        `if col_data['COLUMN_NAME_REST'] in parameter:` の else 側(continue)。
        「項目なし」(COL_GROUP_ID=None → STATUS='skip' で登録される §3-8)とは
        別分岐で、こちらは**レコードごと登録されない**。
        """
        col, row = _make_col_and_row({}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        # パラメータシート側からカラムが削除された状態(別カラムだけが存在する)
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'other_column': 'v'}}})

        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert array_vars_ass_list == []

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_record_not_in_param_sheet_is_not_registered(self, make_subvalue_autoreg, mock_ws_db,
                                                         mock_g, bundle):
        """3-20 レコードが具体値取得結果に無い: 未登録(例外にならない)(縦/横)

        具体値は主キー(UUID)で `tmp_result.get(row[DF_ITA_LOCAL_PKEY], {})` と引くため、
        該当キーが無くても既定値 `{}` になり、項目削除と同じ continue に落ちる。
        添字参照に退行すると KeyError で全体が落ちるためのガード。

        なお この状態は**静的な設定では作れない**(※7)。CMDB行の一覧(:474-475)と具体値(rest_filter
        :1964-1969)は同じメニューの TABLE_NAME / VIEW_NAME をどちらも DISUSE_FLAG='0' で読み、
        VIEW は行を落とさないため同一時点なら必ず一致する。①は読んだ時点でコミットされる
        (:880-886)ので、②を読むまでに行が廃止された/ホストグループ分割が sv_ テーブルを
        作り直した(split_function.py:601)ときの**時間差でだけ**発生する＝レースのガード。
        """
        col, row = _make_col_and_row({}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        # 具体値取得結果に row-001 が含まれない(rest_filter 側で除外された状態)
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-999': {'column_a': 'v'}}})

        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert array_vars_ass_list == []

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_fileupload_column_sets_path(self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle):
        """3-6 FileUploadColumn: ファイルが存在すれば COL_FILEUPLOAD_PATH が設定される(縦/横)

        パスは
        `STORAGEPATH + 組織ID + '/' + ワークスペースID + '/uploadfiles/'
         + アップロード用メニューID + '/' + カラムREST名 + '/' + 紐付テーブル主キー + '/' + ファイル名`
        ([SubValueAutoReg.py:1057-1066](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1057-L1066))。
        `os.path.exists` の対象は**ファイル名を除いたディレクトリ部分**で、
        戻り値のパスはそこにファイル名を連結したもの。
        後半だけを部分一致で見ると先頭の STORAGEPATH/組織/ワークスペースが欠けても通ってしまうため、
        **全体を完全一致で固定**する(組織・ワークスペースの取り違えは他ワークスペースのファイル参照になる)。
        """
        col, row = _make_col_and_row({'COLUMN_CLASS': '9'}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        # 紐付メニュー -> アップロード用メニューID の対応
        mock_ws_db.upload_menu_rows = [{
            'MENU_ID': MENU_ID, 'MENU_NAME_REST': 'menu_a_subst',
            'OUT_MENU_ID': 'out-menu-1', 'OUT_MENU_NAME_REST': MENU_NAME_REST,
        }]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'file.txt'}}})

        with patch('common_libs.ansible_driver.classes.SubValueAutoReg.os.path.exists',
                   return_value=True) as exists_mock:
            vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        expected_dir = '{}{}/{}/uploadfiles/out-menu-1/column_a/row-001'.format(
            os.environ['STORAGEPATH'], mock_g.ORGANIZATION_ID, mock_g.WORKSPACE_ID)

        assert len(vars_ass_list) == 1
        rec = vars_ass_list[0]
        assert rec['STATUS'] is True
        assert rec['VARS_ENTRY'] == 'file.txt'
        assert rec['COL_FILEUPLOAD_PATH'] == expected_dir + '/file.txt'
        # 存在確認はファイル名を含まないディレクトリ側に対して行われる
        assert exists_mock.call_args_list[0].args[0] == expected_dir

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_fileupload_missing_file_skips_and_logs(self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle):
        """3-7 FileUpload(ファイル無): os.path.exists False で未登録 + MSG-10166(縦/横)"""
        col, row = _make_col_and_row({'COLUMN_CLASS': '9'}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'file.txt'}}})

        with patch('common_libs.ansible_driver.classes.SubValueAutoReg.os.path.exists', return_value=False):
            vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10166")

    # strict=False は意図的(§10-6 / rest_filter R6-4 の xfail は strict=True)。
    # #3066 の対応方針(どこで直すか・パスの持ち方)が未定で、実装が入った時点で
    # 「xpass = 成功」として扱いたいため。方針が固まってパスの形まで確定したら
    # strict=True に上げるか、本マークを外して通常の期待値テストにする。
    @pytest.mark.xfail(strict=False, reason=(
        "既知の不具合(exastro-suite/exastro-it-automation#3066): "
        "「パラメータシート参照」で参照先に「ファイルアップロード」列を指定できるが、"
        "作成される項目のカラムクラスは '21'(JsonIDColumn) になる"
        "(ita_by_menu_create/backyard_main.py:1679-1699。参照先が '8' のときだけ '26')。"
        "そのためファイルパス生成ブロック(:1052 の COLUMN_CLASS 9/20 判定)を通らず、"
        "実ファイルではなく参照先 DATA_JSON の生値=ファイル名だけが具体値として"
        "代入値管理に登録される。本来は通常の FileUploadColumn(§3-6/§3-7)と同様に"
        "COL_FILEUPLOAD_PATH を伴い、ファイルが無ければ MSG-10166 で未登録とすべき。"
        "実装が直れば本ケースは xpass(成功)になる。"))
    @pytest.mark.parametrize("bundle", ["no", "yes"])
    @pytest.mark.parametrize("file_exists", [True, False])
    def test_param_sheet_reference_to_fileupload_should_be_handled_as_file(
            self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle, file_exists):
        """3-14 パラメータシート参照(参照先=ファイルアップロード列): §3-6/§3-7 と同じ扱いを期待

        期待(あるべき姿):
          - ファイル有: 登録され、COL_FILEUPLOAD_PATH に実ファイルのパスが入る
          - ファイル無: 未登録 + MSG-10166
        現状: COLUMN_CLASS='21' のためファイルとして扱われず、ファイル存在に関わらず
              COL_FILEUPLOAD_PATH='' でファイル名の文字列だけが登録される(→ xfail)。
        パスの持ち方(参照元メニュー基準か参照先メニュー基準か)は #3066 で未定なので、
        「空でなく、ファイル名で終わる」までを期待値とする。
        """
        col, row = _make_col_and_row(
            {'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
             'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        # 紐付メニュー -> アップロード用メニューID の対応(§3-6 と同じ前提)
        mock_ws_db.upload_menu_rows = [{
            'MENU_ID': MENU_ID, 'MENU_NAME_REST': 'menu_a_subst',
            'OUT_MENU_ID': 'out-menu-1', 'OUT_MENU_NAME_REST': MENU_NAME_REST,
        }]
        # rest_filter が返す具体値は参照先 DATA_JSON の生値なので、ファイル列ならファイル名
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'file.txt'}}})

        with patch('common_libs.ansible_driver.classes.SubValueAutoReg.os.path.exists',
                   return_value=file_exists):
            vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None,
                                                    mock_ws_db, '1')

        if file_exists:
            # 期待は §3-6 と同じ: ファイル名 + 実ファイルのパスが渡る
            assert len(vars_ass_list) == 1
            assert vars_ass_list[0]['VARS_ENTRY'] == 'file.txt'
            assert vars_ass_list[0]['COL_FILEUPLOAD_PATH'] != ''
            assert vars_ass_list[0]['COL_FILEUPLOAD_PATH'].endswith('/file.txt')
        else:
            # 期待は §3-7 と同じ: ファイルが無ければ未登録 + MSG-10166
            assert vars_ass_list == []
            assert_log_contains(mock_g, "MSG-10166")


class TestRegistrationType:
    """[4] 登録方式: Value / Key / Key(具体値None)。縦/横(バンドル)両方で確認。"""

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_value_type(self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle):
        """4-1 Value: REG_TYPE='Value', VARS_ENTRY=具体値"""
        col, row = _make_col_and_row({'COL_TYPE': AnscConst.DF_COL_TYPE_VAL}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'value1'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list[0]['REG_TYPE'] == 'Value'
        assert vars_ass_list[0]['VARS_ENTRY'] == 'value1'

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_key_type_uses_column_name(self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle):
        """4-2 Key: REG_TYPE='Key', VARS_ENTRY=カラム名(COLUMN_NAME_JA)"""
        col, row = _make_col_and_row(
            {'COL_TYPE': AnscConst.DF_COL_TYPE_KEY, 'COLUMN_NAME_JA': 'カラムA', 'COLUMN_NAME_EN': 'ColumnA'},
            bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'x'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list[0]['REG_TYPE'] == 'Key'
        assert vars_ass_list[0]['VARS_ENTRY'] == 'カラムA'  # g.LANGUAGE='ja'

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_key_type_none_value_skips_and_logs(self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle):
        """4-3 Key(具体値None): 未登録 + MSG-10377"""
        col, row = _make_col_and_row({'COL_TYPE': AnscConst.DF_COL_TYPE_KEY}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': None}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert_log_contains(mock_g, "MSG-10377")


class TestRegistrationTypeAndFileUpload:
    """[4b] 登録方式 × カラム具体値(FileUpload) の掛け合わせ

    [SubValueAutoReg.py:1052](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1052)
    は1つの if に両軸が入っており、**直交していない**:

        if col_data['COL_TYPE'] == DF_COL_TYPE_VAL and (COLUMN_CLASS == "9" or == "20"):

    つまり Key登録の場合はファイルパス生成ブロック全体がスキップされ、
      - COL_FILEUPLOAD_PATH は '' のまま
      - os.path.exists によるファイル存在チェックが行われない
      - よってファイルが無くても MSG-10166 は出ず、そのまま登録される
    という Value 側 (§3-6 / §3-7) とは別の挙動になる。
    """

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    @pytest.mark.parametrize("column_class", ["9", "20"])
    @pytest.mark.parametrize("file_exists", [True, False])
    def test_key_type_fileupload_skips_path_and_existence_check(
            self, make_subvalue_autoreg, mock_ws_db, mock_g,
            bundle, column_class, file_exists):
        """4b-1 Key × FileUpload: ファイル有無に関わらず登録され、パスは空・MSG-10166なし"""
        col, row = _make_col_and_row(
            {'COL_TYPE': AnscConst.DF_COL_TYPE_KEY, 'COLUMN_CLASS': column_class}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        mock_ws_db.upload_menu_rows = [{
            'MENU_ID': MENU_ID, 'MENU_NAME_REST': 'menu_a_subst',
            'OUT_MENU_ID': 'out-menu-1', 'OUT_MENU_NAME_REST': MENU_NAME_REST,
        }]
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'file.txt'}}})

        with patch('common_libs.ansible_driver.classes.SubValueAutoReg.os.path.exists',
                   return_value=file_exists):
            vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None,
                                                    mock_ws_db, '1')

        # Value 側(§3-7)ならファイル無しで未登録になるが、Key 側は登録される
        assert len(vars_ass_list) == 1
        rec = vars_ass_list[0]
        assert rec['REG_TYPE'] == 'Key'
        assert rec['VARS_ENTRY'] == 'カラムA'          # Key はカラム名を登録
        assert rec['COL_FILEUPLOAD_PATH'] == ''        # パス生成ブロックを通らない
        assert_log_not_contains(mock_g, "MSG-10166")   # 存在チェックが行われない


class TestBundle:
    """[5] バンドル(パラメータシート形態): 無(横メニュー) / 有(縦メニュー)。

    有効な2形態がともに処理されることを確認する。値処理の縦/横カバレッジは
    TestColumnValue / TestRegistrationType / TestNullHandling で bundle を
    parametrize して担保している(ここは形態そのものの固定)。

    レコード側 `INPUT_ORDER` の役割は分岐の切替えと設定側との突合であり、
    **代入値管理レコードには格納されない**
    ([:1375-1390](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1375-L1390))。
    したがって「INPUT_ORDER が正しく反映されている」は次の2点で見る:
      - 縦: `INPUT_ORDER` と `COLUMN_ASSIGN_SEQ` が一致する設定**だけ**が採用される(5-2 / 5-3)
      - 横: `INPUT_ORDER` が空なので突合せず、レコードに痕跡も残らない(5-1)
    """

    def test_bundle_no_horizontal(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """5-1 バンドル無(横メニュー): 登録され、INPUT_ORDER はレコードに残らない

        `INPUT_ORDER` が空(`'' AS INPUT_ORDER`)なので横分岐に入り、
        設定側の `COLUMN_ASSIGN_SEQ`(=None)との突合は行われない。
        生成されるレコードは縦(5-2)と同一構成になる。
        """
        col, row = _make_col_and_row({}, 'no')
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 1
        rec = vars_ass_list[0]
        assert rec['STATUS'] is True
        assert rec['VARS_ENTRY'] == 'v'
        assert rec['COL_ROW_ID'] == 'row-001'
        assert rec['MVMT_VAR_LINK_ID'] == 'vlink-001'
        # 代入順序は設定側の ASSIGN_SEQ 由来。INPUT_ORDER は代入値管理には持ち込まれない
        assert rec['ASSIGN_SEQ'] is None
        assert 'INPUT_ORDER' not in rec

    def test_bundle_yes_vertical(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """5-2 バンドル有(縦メニュー): INPUT_ORDER に一致する設定だけが採用される

        縦メニューは「同じカラムに代入順序ごとのレコードが並ぶ」形態なので、
        レコード(`INPUT_ORDER`)と設定(`COLUMN_ASSIGN_SEQ`)の**組合せが正しいこと**を固定する。
        レコード2件 × 設定2件のうち、突合が成立する2組だけが登録され、
        値(具体値はレコード=主キー単位)と設定(変数)の対応が入れ替わらないこと。

        注: どのレコード由来かは `COL_ROW_ID` ではなく**具体値**で見る。
        `COL_ROW_ID` は「最後の有効レコードの主キー」が入る既知不具合があり
        (`TestColRowId` の xfail 参照)、レコードの識別子として使えない。
        """
        cols = [make_col_data(COLUMN_ID='col-1', COLUMN_ASSIGN_SEQ='1', MVMT_VAR_LINK_ID='vlink-1'),
                make_col_data(COLUMN_ID='col-2', COLUMN_ASSIGN_SEQ='2', MVMT_VAR_LINK_ID='vlink-2')]
        sqls, menu_ids, col_lists = build_inputs(table_name=TABLE, menu_id=MENU_ID,
                                                 col_data_list=cols)
        mock_ws_db.cmdb_rows[TABLE] = [
            make_cmdb_row(row_id='row-001', input_order='1'),
            make_cmdb_row(row_id='row-002', input_order='2'),
        ]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {
            'row-001': {'column_a': 'v1'},
            'row-002': {'column_a': 'v2'},
        }})

        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 2
        assert all(r['STATUS'] is True for r in vars_ass_list)
        assert {(r['MVMT_VAR_LINK_ID'], r['VARS_ENTRY']) for r in vars_ass_list} == \
            {('vlink-1', 'v1'), ('vlink-2', 'v2')}

    def test_bundle_yes_vertical_input_order_mismatch(self, make_subvalue_autoreg,
                                                      mock_ws_db, mock_g):
        """5-3 バンドル有(縦メニュー) × INPUT_ORDER 不一致: 未登録

        5-2 の裏側。突合を無視する実装(縦でも全設定を適用する等)に退行すると
        代入順序の異なる変数に他の順序の具体値が入るため、**不一致は未登録**を固定する。
        なお、この「代入順序に対応するレコードが無い」ことを通知する MSG-10902 は
        現状の実装では到達しない(未カバー表に記載)ため、ログは検証しない。
        """
        col = make_col_data(COLUMN_ASSIGN_SEQ='1')
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        # 設定は代入順序'1'だが、パラメータシートのレコードは代入順序'2'しか無い
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001', input_order='2')]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})

        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        assert array_vars_ass_list == []


class TestAssignSeq:
    """[5b] 代入順序 = 代入値自動登録設定の ASSIGN_SEQ: 無(None) / 有(値)。

    ASSIGN_SEQ は代入値管理レコードにそのまま格納され、
    重複チェックキー(vars_link_id__patten__host__ope__assign_seq)の一部になる。
    """

    def test_assign_seq_none(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """代入順序:無 → ASSIGN_SEQ=None がレコードに反映"""
        col = make_col_data(ASSIGN_SEQ=None)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001')]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['ASSIGN_SEQ'] is None

    def test_assign_seq_value(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """代入順序:有 → ASSIGN_SEQ の値がレコードに反映"""
        col = make_col_data(ASSIGN_SEQ='3')
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001')]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['ASSIGN_SEQ'] == '3'


class TestNullHandling:
    """[6] NULL連携(カラム具体値:無=None時): 設定(col_data) と IF情報(g_null) の組合せ。縦/横両方。"""

    # (設定NULL連携, IF情報NULL連携, 登録されるか)
    @pytest.mark.parametrize("bundle", ["no", "yes"])
    @pytest.mark.parametrize("setting_null, if_null, expect_registered", [
        ('1', '1', True),    # 6-1 設定TRUE  -> 登録(None)
        ('1', '0', True),    # 6-2 設定TRUE  -> 登録(None)
        ('0', '1', False),   # 6-3 設定FALSE -> 除外(MSG-10375)
        ('0', '0', False),   # 6-4 設定FALSE -> 除外(MSG-10375)
        (None, '1', True),   # 6-5 設定None,IF TRUE  -> 登録(None)
        (None, '0', False),  # 6-6 設定None,IF FALSE -> 除外(MSG-10375)
    ])
    def test_null_value_handling(self, make_subvalue_autoreg, mock_ws_db, mock_g,
                                 bundle, setting_null, if_null, expect_registered):
        col, row = _make_col_and_row({'NULL_DATA_HANDLING_FLG': setting_null}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        # カラム具体値:無 = 値 None
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': None}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, if_null)

        if expect_registered:
            assert len(vars_ass_list) == 1
            assert vars_ass_list[0]['VARS_ENTRY'] is None
            assert_log_not_contains(mock_g, "MSG-10375")
        else:
            assert vars_ass_list == []
            assert_log_contains(mock_g, "MSG-10375")

    @pytest.mark.parametrize("setting_null, expect_registered", [
        ('1', True),    # 6-7 設定TRUE  -> 多次元リストに登録(VARS_ENTRY=None)
        ('0', False),   # 6-8 設定FALSE -> 除外(MSG-10375)
    ])
    def test_null_value_handling_with_member_var(self, make_subvalue_autoreg, mock_ws_db,
                                                 mock_g, setting_null, expect_registered):
        """6-7/6-8 NULL連携 × メンバ変数(多次元)

        NULL連携の判定
        ([SubValueAutoReg.py:1189-1190](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1189-L1190))
        は VAL_VAR_TYPE より手前にあり多次元とも共有される。
        よって除外時は一般変数リストではなく**多次元リストにも入らない**ことを確認する。
        """
        col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_M_ARRAY,
                            COL_SEQ_COMBINATION_ID='memb-001',
                            NULL_DATA_HANDLING_FLG=setting_null)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001')]
        instance = make_subvalue_autoreg(
            driver_id=AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': None}}},
        )
        vars_ass_list, array_vars_ass_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert vars_ass_list == []
        if expect_registered:
            assert len(array_vars_ass_list) == 1
            assert array_vars_ass_list[0]['VARS_ENTRY'] is None
            assert array_vars_ass_list[0]['COL_SEQ_COMBINATION_ID'] == 'memb-001'
            assert_log_not_contains(mock_g, "MSG-10375")
        else:
            assert array_vars_ass_list == []
            assert_log_contains(mock_g, "MSG-10375")


class TestDriverAndMemberVars:
    """[7] ドライバ/メンバ変数: L / P / R一般 / R複数具体値 / Rメンバ変数(多次元)"""

    def _run(self, make_subvalue_autoreg, mock_ws_db, driver_id, col):
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001')]
        instance = make_subvalue_autoreg(
            driver_id=driver_id,
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}},
        )
        return instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

    def test_driver_legacy_std(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """7-1 L / 一般変数(STD): 一般変数リストに1件"""
        col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_STD)
        vars_ass_list, array_vars_ass_list = self._run(
            make_subvalue_autoreg, mock_ws_db, AnscConst.DF_LEGACY_DRIVER_ID, col)
        assert len(vars_ass_list) == 1
        assert array_vars_ass_list == []

    def test_driver_pioneer_std(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """7-2 P / 一般変数(STD): 一般変数リストに1件"""
        col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_STD)
        vars_ass_list, array_vars_ass_list = self._run(
            make_subvalue_autoreg, mock_ws_db, AnscConst.DF_PIONEER_DRIVER_ID, col)
        assert len(vars_ass_list) == 1
        assert array_vars_ass_list == []

    def test_driver_role_std(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """7-3 R / メンバ変数無(一般変数STD): 一般変数リストに1件"""
        col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_STD)
        vars_ass_list, array_vars_ass_list = self._run(
            make_subvalue_autoreg, mock_ws_db, AnscConst.DF_LEGACY_ROLE_DRIVER_ID, col)
        assert len(vars_ass_list) == 1
        assert array_vars_ass_list == []

    def test_driver_role_list(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """7-4 R / 複数具体値(LIST): 一般変数リストに1件(STDと同じ分岐)"""
        col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_LIST)
        vars_ass_list, array_vars_ass_list = self._run(
            make_subvalue_autoreg, mock_ws_db, AnscConst.DF_LEGACY_ROLE_DRIVER_ID, col)
        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['VAR_TYPE'] == AnscConst.GC_VARS_ATTR_LIST
        assert array_vars_ass_list == []

    def test_driver_role_member_var_multi_array(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """7-5 R / メンバ変数有(多次元M_ARRAY): 多次元リストに1件、一般変数リストは空"""
        col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_M_ARRAY,
                            COL_SEQ_COMBINATION_ID='memb-001')
        vars_ass_list, array_vars_ass_list = self._run(
            make_subvalue_autoreg, mock_ws_db, AnscConst.DF_LEGACY_ROLE_DRIVER_ID, col)
        assert vars_ass_list == []
        assert len(array_vars_ass_list) == 1
        rec = array_vars_ass_list[0]
        assert rec['VAR_TYPE'] == AnscConst.GC_VARS_ATTR_M_ARRAY
        assert rec['COL_SEQ_COMBINATION_ID'] == 'memb-001'
        assert rec['STATUS'] is True


class TestRoute:
    """[8] 経路: all(reg_operation_id=None) / parameter_sheet(reg_operation_id=値)"""

    def test_all_route_no_operation_filter(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """8-1 all: SELECT に OPERATION_ID 条件が付かない"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001')]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        cmdb_calls = [c for c in mock_ws_db.sql_log if "FROM `{}`".format(TABLE) in c[0]]
        assert cmdb_calls
        sql, params = cmdb_calls[-1]
        assert "OPERATION_ID = %s" not in sql
        # all 経路では reg_operation_id を積まない -> params は [HOST_CNT, PKEY] の2要素
        assert len(params) == 2

    def test_parameter_sheet_route_operation_filter(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """8-2 parameter_sheet: SELECT に OPERATION_ID = %s とパラメータが付く"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [make_cmdb_row(row_id='row-001', operation_id='ope-XYZ')]
        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        instance.getCMDBdata(sqls, menu_ids, col_lists, 'ope-XYZ', mock_ws_db, '1')

        cmdb_calls = [c for c in mock_ws_db.sql_log if "FROM `{}`".format(TABLE) in c[0]]
        assert cmdb_calls
        sql, params = cmdb_calls[-1]
        assert "OPERATION_ID = %s" in sql
        # parameter_sheet 経路では reg_operation_id を末尾に積む -> [HOST_CNT, PKEY, reg_operation_id]
        assert len(params) == 3
        assert params[-1] == 'ope-XYZ'


class TestReturnRecordShape:
    """[9] 戻りレコードのキー集合(= 戻り値の形)の固定

    キー集合を生成しているのは条件分岐を含まない4箇所の dict リテラルだけなので、
    キー集合は「到達したリテラル」でのみ決まり、値を左右する他の軸には依存しない。
    したがって 正常(16キー) / skip(7キー) の2形態を押さえれば全体を固定できる。

    目的は主に**二重実装の乖離検知**:
      - 16キー: STD/LIST 用 (:1375-1390) と M_ARRAY 用 (:1413-1428)
      -  7キー: skip 縦メニュー用 (:993-999) と 横メニュー用 (:1022-1028)
    片方にだけキーを追加/改名する変更を検知する。

    限界(このクラスでは守れないこと):
      - 条件付きでキーを増やす変更(`if ...: rec['X'] = ..`)は、その条件を満たす
        入力を通していなければ検知できない。値やログの変化も対象外。
        それらは §1〜§8 のケースで担保する。
    """

    def _run(self, make_subvalue_autoreg, mock_ws_db, col, bundle='no'):
        _, row = _make_col_and_row({}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(
            driver_id=AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}},
        )
        return instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

    def test_vars_record_key_set_is_fixed(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """9-1 一般変数レコードのキー集合が16キーで固定されている"""
        col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_STD)
        vars_ass_list, _ = self._run(make_subvalue_autoreg, mock_ws_db, col)

        assert len(vars_ass_list) == 1
        assert set(vars_ass_list[0].keys()) == EXPECTED_RECORD_KEYS

    def test_array_record_key_set_matches_vars_record(self, make_subvalue_autoreg,
                                                      mock_ws_db, mock_g):
        """9-2 多次元レコードのキー集合が一般変数レコードと一致する(二重実装の乖離検知)"""
        std_col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_STD)
        vars_ass_list, _ = self._run(make_subvalue_autoreg, mock_ws_db, std_col)

        mock_ws_db.cmdb_rows.clear()
        ma_col = make_col_data(VAL_VAR_TYPE=AnscConst.GC_VARS_ATTR_M_ARRAY,
                               COL_SEQ_COMBINATION_ID='memb-001')
        _, array_vars_ass_list = self._run(make_subvalue_autoreg, mock_ws_db, ma_col)

        assert len(array_vars_ass_list) == 1
        assert set(array_vars_ass_list[0].keys()) == EXPECTED_RECORD_KEYS
        # 1375-1390 と 1413-1428 の dict リテラルが乖離していないこと
        assert set(array_vars_ass_list[0].keys()) == set(vars_ass_list[0].keys())

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_skip_record_key_set_is_fixed(self, make_subvalue_autoreg, mock_ws_db,
                                          mock_g, bundle):
        """9-3 項目なし(skip)レコードのキー集合が7キーで固定(縦/横で一致・16キーの部分集合)"""
        col, row = _make_col_and_row({'COL_GROUP_ID': None}, bundle)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [row]
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'v'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None,
                                               mock_ws_db, '1')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['STATUS'] == 'skip'
        assert set(vars_ass_list[0].keys()) == EXPECTED_SKIP_RECORD_KEYS
        # skip レコードは正常レコードのキーの部分集合(独自キーを持たない)
        assert EXPECTED_SKIP_RECORD_KEYS <= EXPECTED_RECORD_KEYS


class TestValueIntegrity:
    """[10] 具体値がレコードごとに正しく取得されるか(具体値の取り違え検知)

    今回の改修の本体。改修前は具体値を
    「HOST_ID と OPERATION_ID が一致する**最初の**レコード」から引いていたため、
    同一ホスト・同一オペのレコードが複数あると全レコードが1件目の具体値になり、
    複数ホストのケースでも組み合わせ次第で他レコードの値を拾っていた。
    改修後はパラメータシートの主キー(ROW_ID/UUID)で引くため取り違えが起こらない。

    既存の §2(レコード数) のケースは全レコードに同じ具体値 'v' を入れているため、
    値の取り違えが起きても検知できない。本クラスは**レコードごとに異なる値**を与える。
    """

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_same_host_same_ope_keeps_own_value(self, make_subvalue_autoreg, mock_ws_db,
                                                mock_g, bundle):
        """10-1 同一ホスト・同一オペ: 各レコードが自分の行の具体値を持つ

        改修前は10件すべてが 'value-001'(1件目の値)になっていた。
        代入値管理への登録対象は重複排除で1件だけだが、
        戻りレコードの VARS_ENTRY は10件すべて生成されるため値の取り違えを直接見られる。
        """
        overrides = {'COLUMN_ASSIGN_SEQ': '1'} if bundle == 'yes' else {}
        input_order = '1' if bundle == 'yes' else ''
        col = make_col_data(**overrides)
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(1, 11):
            rid = 'row-{:03d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001', host_id='host-001',
                                      input_order=input_order))
            param_rows[rid] = {'column_a': 'value-{:03d}'.format(i)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 10
        # レコードの並び順は data_list の順序を保つ
        assert [r['VARS_ENTRY'] for r in vars_ass_list] == \
            ['value-{:03d}'.format(i) for i in range(1, 11)]

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_multi_host_same_ope_keeps_own_value(self, make_subvalue_autoreg, mock_ws_db,
                                                 mock_g, bundle):
        """10-2 複数ホスト・同一オペ: ホストと具体値の対応が入れ替わらない"""
        overrides = {'COLUMN_ASSIGN_SEQ': '1'} if bundle == 'yes' else {}
        input_order = '1' if bundle == 'yes' else ''
        col = make_col_data(**overrides)
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(1, 11):
            rid = 'row-{:03d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001',
                                      host_id='host-{:03d}'.format(i),
                                      input_order=input_order))
            param_rows[rid] = {'column_a': 'value-{:03d}'.format(i)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 10
        assert {(r['SYSTEM_ID'], r['VARS_ENTRY']) for r in vars_ass_list} == \
            {('host-{:03d}'.format(i), 'value-{:03d}'.format(i)) for i in range(1, 11)}

    def test_same_host_multi_ope_keeps_own_value(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """10-3 同一ホスト・複数オペ: オペと具体値の対応が入れ替わらない"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(1, 11):
            rid = 'row-{:03d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-{:03d}'.format(i),
                                      host_id='host-001'))
            param_rows[rid] = {'column_a': 'value-{:03d}'.format(i)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert {(r['OPERATION_ID'], r['VARS_ENTRY']) for r in vars_ass_list} == \
            {('ope-{:03d}'.format(i), 'value-{:03d}'.format(i)) for i in range(1, 11)}

    def test_vertical_menu_pairs_input_order_with_assign_seq(self, make_subvalue_autoreg,
                                                             mock_ws_db, mock_g):
        """10-4 縦メニュー: INPUT_ORDER と COLUMN_ASSIGN_SEQ の対応が正しい組だけ登録される

        同一ホスト・同一オペの縦メニュー(代入順序 1/2/3)と、
        代入順序 1/2/3 の設定3件の総当たり(9通り)のうち、
        一致する3組だけが登録され、かつそれぞれ**自分の行の**具体値を持つこと。

        パラメータシート側には全カラムの値を入れておくため、
        行と設定の対応がずれた場合は「別の値が登録される」形で失敗する
        (件数だけを見るアサートでは検知できない)。
        """
        cols = [make_col_data(COLUMN_ID='col-{}'.format(i),
                              COLUMN_NAME_REST='column_{}'.format(i),
                              COLUMN_ASSIGN_SEQ=str(i),
                              MVMT_VAR_LINK_ID='vlink-{}'.format(i))
                for i in (1, 2, 3)]
        sqls, menu_ids, col_lists = build_inputs(table_name=TABLE, menu_id=MENU_ID,
                                                col_data_list=cols)

        rows, param_rows = [], {}
        for i in (1, 2, 3):
            rid = 'row-{}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001', host_id='host-001',
                                      input_order=str(i)))
            param_rows[rid] = {'column_{}'.format(j): 'v-{}-{}'.format(i, j) for j in (1, 2, 3)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 3
        assert all(r['STATUS'] is True for r in vars_ass_list)
        # 行i × 設定i の組だけが成立する
        assert {r['VARS_ENTRY'] for r in vars_ass_list} == {'v-1-1', 'v-2-2', 'v-3-3'}
        assert {(r['MVMT_VAR_LINK_ID'], r['VARS_ENTRY']) for r in vars_ass_list} == \
            {('vlink-{}'.format(i), 'v-{}-{}'.format(i, i)) for i in (1, 2, 3)}

    @pytest.mark.parametrize("bundle", ["no", "yes"])
    def test_row_missing_from_param_sheet_is_skipped(self, make_subvalue_autoreg, mock_ws_db,
                                                     mock_g, bundle):
        """10-5 具体値取得結果に無いROW_ID: 例外にならず、そのレコードだけ未登録

        rest_filter の結果は DISUSE_FLAG='0' で絞られている一方、
        SELECT 側の結果と取得タイミングがずれると ROW_ID が見つからないことがある。
        `tmp_result.get(ROW_ID, {})` の既定値経路(KeyError にしない)を固定する。
        同一時点のスナップショットでは両者は必ず一致するので、これは**時間差でだけ**起こる
        (実行中の廃止 / ホストグループ分割による sv_ テーブル再構築)。→ ※7 / §3-20
        """
        overrides = {'COLUMN_ASSIGN_SEQ': '1'} if bundle == 'yes' else {}
        input_order = '1' if bundle == 'yes' else ''
        col = make_col_data(**overrides)
        sqls, menu_ids, col_lists = _single_col_inputs(col)
        mock_ws_db.cmdb_rows[TABLE] = [
            make_cmdb_row(row_id='row-001', host_id='host-001', input_order=input_order),
            make_cmdb_row(row_id='row-002', host_id='host-002', input_order=input_order),
        ]

        # row-002 は具体値取得結果に存在しない
        instance = make_subvalue_autoreg(
            param_sheets={MENU_NAME_REST: {'row-001': {'column_a': 'value1'}}})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['SYSTEM_ID'] == 'host-001'
        assert vars_ass_list[0]['VARS_ENTRY'] == 'value1'

    @pytest.mark.xfail(strict=True, reason=(
        "既知の不具合(今回の改修範囲外): COL_ROW_ID が全レコードで『最後の有効行のROW_ID』になる。"
        "col_row_id は data_list の詰め直しループ(SubValueAutoReg.py:933)で束縛されたまま、"
        "レコード展開ループ(:947-)で再取得されないため。"
        "makeVarsAssignData には UUID が別引数(:1084)でも渡っており、"
        "現状 COL_ROW_ID の参照箇所は無い(コメントアウト済みコードのみ)ので実害は出ていない。"
        "修正する場合は :1074 の col_row_id を row[DF_ITA_LOCAL_PKEY] に置き換える。"))
    def test_col_row_id_matches_own_row(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """10-6 COL_ROW_ID が自分の行のROW_IDになっている(現状は失敗する = 既知の不具合)"""
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in (1, 2, 3):
            rid = 'row-{}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, host_id='host-{}'.format(i)))
            param_rows[rid] = {'column_a': 'v-{}'.format(i)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 3
        assert [r['COL_ROW_ID'] for r in vars_ass_list] == ['row-1', 'row-2', 'row-3']


class TestMultipleTables:
    """[11] 複数の紐付メニュー(テーブル)を1回で処理する

    getCMDBdata は in_tableNameToSqlList をテーブル単位でループし、
    tmp_ary_data / registered_host_ary をテーブル単位に初期化する一方、
    host_ary と dict_objmenu(load_table結果のキャッシュ) はテーブル間で共有する。
    テーブル間の値の混線と、キャッシュが効いていることを確認する。
    """

    def _merge(self, *built):
        """build_inputs の戻り(3辞書)を複数テーブル分マージする。"""
        sqls, menu_ids, col_lists = {}, {}, {}
        for s, m, c in built:
            sqls.update(s)
            menu_ids.update(m)
            col_lists.update(c)
        return sqls, menu_ids, col_lists

    def test_two_tables_do_not_mix_values(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """11-1 別メニューの2テーブル: 具体値/TABLE_NAME が混線しない"""
        table_a, table_b = 'T_PARAM_SHEET_A', 'T_PARAM_SHEET_B'
        col_a = make_col_data(COLUMN_NAME_REST='column_a', MENU_NAME_REST='menu_a',
                              MVMT_VAR_LINK_ID='vlink-a')
        col_b = make_col_data(COLUMN_NAME_REST='column_b', MENU_NAME_REST='menu_b',
                              MVMT_VAR_LINK_ID='vlink-b')
        sqls, menu_ids, col_lists = self._merge(
            build_inputs(table_name=table_a, menu_id='menu-a', col_data_list=[col_a]),
            build_inputs(table_name=table_b, menu_id='menu-b', col_data_list=[col_b]),
        )
        mock_ws_db.cmdb_rows[table_a] = [make_cmdb_row(row_id='row-a1', host_id='host-a')]
        mock_ws_db.cmdb_rows[table_b] = [make_cmdb_row(row_id='row-b1', host_id='host-b')]

        instance = make_subvalue_autoreg(param_sheets={
            'menu_a': {'row-a1': {'column_a': 'value-a'}},
            'menu_b': {'row-b1': {'column_b': 'value-b'}},
        })
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 2
        assert {(r['TABLE_NAME'], r['SYSTEM_ID'], r['VARS_ENTRY']) for r in vars_ass_list} == \
            {(table_a, 'host-a', 'value-a'), (table_b, 'host-b', 'value-b')}

    def test_zero_record_table_does_not_block_next_table(self, make_subvalue_autoreg,
                                                         mock_ws_db, mock_g):
        """11-2 先のテーブルが0件でも後続テーブルは処理される(MSG-10368 は出る)"""
        table_empty, table_ok = 'T_PARAM_SHEET_EMPTY', 'T_PARAM_SHEET_OK'
        col_a = make_col_data(MENU_NAME_REST='menu_a')
        col_b = make_col_data(MENU_NAME_REST='menu_b', COLUMN_NAME_REST='column_b')
        sqls, menu_ids, col_lists = self._merge(
            build_inputs(table_name=table_empty, menu_id='menu-a', col_data_list=[col_a]),
            build_inputs(table_name=table_ok, menu_id='menu-b', col_data_list=[col_b]),
        )
        mock_ws_db.cmdb_rows[table_empty] = []
        mock_ws_db.cmdb_rows[table_ok] = [make_cmdb_row(row_id='row-b1')]

        instance = make_subvalue_autoreg(param_sheets={
            'menu_b': {'row-b1': {'column_b': 'value-b'}},
        })
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == 1
        assert vars_ass_list[0]['TABLE_NAME'] == table_ok
        assert_log_contains(mock_g, "MSG-10368")

    def test_load_table_result_is_cached_per_menu(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """11-3 同一メニューの具体値取得は1回だけ(dict_objmenu キャッシュ)

        キャッシュはテーブルループの外で保持されるため、
        別テーブル・別レコードでも同じ menu_name_rest なら再取得しない。
        キャッシュヒット時は分岐が変わる(SELECT 1 の keepalive 経路)ので、
        「キャッシュを使っても値が変わらない」ことも合わせて確認する。
        """
        table_a, table_b = 'T_PARAM_SHEET_A', 'T_PARAM_SHEET_B'
        # 2テーブルとも同じ紐付メニュー(menu_a)を参照する設定
        col_a = make_col_data(MENU_NAME_REST=MENU_NAME_REST, MVMT_VAR_LINK_ID='vlink-a')
        col_b = make_col_data(MENU_NAME_REST=MENU_NAME_REST, MVMT_VAR_LINK_ID='vlink-b')
        sqls, menu_ids, col_lists = self._merge(
            build_inputs(table_name=table_a, menu_id='menu-a', col_data_list=[col_a]),
            build_inputs(table_name=table_b, menu_id='menu-b', col_data_list=[col_b]),
        )
        mock_ws_db.cmdb_rows[table_a] = [
            make_cmdb_row(row_id='row-001', host_id='host-a'),
            make_cmdb_row(row_id='row-002', host_id='host-b'),
        ]
        mock_ws_db.cmdb_rows[table_b] = [make_cmdb_row(row_id='row-003', host_id='host-c')]

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: {
            'row-001': {'column_a': 'value-1'},
            'row-002': {'column_a': 'value-2'},
            'row-003': {'column_a': 'value-3'},
        }})
        original_rest_filter = instance.rest_filter
        calls = []

        def counting_rest_filter(WS_DB, obj_load_table):
            calls.append(obj_load_table.menu_name_rest)
            return original_rest_filter(WS_DB, obj_load_table)

        instance.rest_filter = counting_rest_filter

        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert calls == [MENU_NAME_REST], "同一メニューの具体値取得がキャッシュされていない"
        assert {(r['SYSTEM_ID'], r['VARS_ENTRY']) for r in vars_ass_list} == \
            {('host-a', 'value-1'), ('host-b', 'value-2'), ('host-c', 'value-3')}


class TestPerformance:
    """[12] 性能カナリア(具体値取得がレコード数・設定件数に対して線形であること)

    改修前の具体値取得は
    「代入値自動登録設定(col_data)のループの中で、具体値リストを線形探索」
    だったため、コストは
        パラメータシートのレコード数 × 代入値自動登録設定の件数 × 具体値の件数
        (= O(レコード数^2 × 設定件数))
    だった。改修後は主キー(UUID)の辞書引きなので O(レコード数 × 設定件数)。

    **線形性のカナリアは 12-3**。具体値辞書へのアクセス方法そのものを数えるため、
    マシン速度に依存せず決定的に「走査していないこと」を固定できる。

    12-1/12-2 は**大量データでの正しさ**(レコード×設定の全組合せが、他の組合せの
    値と混ざらずに登録される)を担保する。
    以前は実行時間の上限(`elapsed < 10`)も見ていたが、改修前の線形探索でも
    この規模では 10秒に届かず回帰を検知できない(実測: 12-1 0.2秒 / 12-2 約5秒)ため、
    性能判定は 12-3 に一本化して時間の assert は撤去した。
    """

    def test_two_thousand_records(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """12-1 2000レコード: 全件が自分の具体値を持つ"""
        record_count = 2000
        col = make_col_data()
        sqls, menu_ids, col_lists = _single_col_inputs(col)

        rows, param_rows = [], {}
        for i in range(record_count):
            rid = 'row-{:05d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001',
                                      host_id='host-{:05d}'.format(i)))
            param_rows[rid] = {'column_a': 'value-{:05d}'.format(i)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})

        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == record_count
        assert all(r['STATUS'] is True for r in vars_ass_list)
        assert [r['VARS_ENTRY'] for r in vars_ass_list] == \
            ['value-{:05d}'.format(i) for i in range(record_count)]

    def test_many_val_assign_settings(self, make_subvalue_autoreg, mock_ws_db, mock_g):
        """12-2 2000レコード × 代入値自動登録設定25件: 全組合せが自分の具体値を持つ

        改修前は具体値の線形探索が設定件数分繰り返されたため、
        コストが「レコード数 × 設定件数 × 具体値件数」だった。
        設定件数の軸でも値が混ざらないことを確認する(線形性の判定は 12-3)。
        """
        record_count = 2000
        setting_count = 25

        cols = [make_col_data(COLUMN_ID='col-{:03d}'.format(c),
                              COLUMN_NAME_REST='column_{:03d}'.format(c),
                              MVMT_VAR_LINK_ID='vlink-{:03d}'.format(c))
                for c in range(setting_count)]
        sqls, menu_ids, col_lists = build_inputs(table_name=TABLE, menu_id=MENU_ID, col_data_list=cols)

        rows, param_rows = [], {}
        for i in range(record_count):
            rid = 'row-{:05d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001',
                                      host_id='host-{:05d}'.format(i)))
            param_rows[rid] = {'column_{:03d}'.format(c): 'value-{:05d}-{:03d}'.format(i, c)
                               for c in range(setting_count)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})

        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == record_count * setting_count
        assert all(r['STATUS'] is True for r in vars_ass_list)
        # レコード × 設定 の全組合せが、他の組合せの値と混ざらずに登録されている
        assert {(r['SYSTEM_ID'], r['MVMT_VAR_LINK_ID'], r['VARS_ENTRY']) for r in vars_ass_list} == \
            {('host-{:05d}'.format(i), 'vlink-{:03d}'.format(c), 'value-{:05d}-{:03d}'.format(i, c))
             for i in range(record_count) for c in range(setting_count)}

    @pytest.mark.parametrize('bundle', ['no', 'yes'])
    def test_lookup_is_dict_access_only(self, make_subvalue_autoreg, mock_ws_db, mock_g, bundle):
        """12-3 具体値の取得は主キーの辞書引きのみ(全走査していない) ※縦/横両方

        実行時間ではなくアクセス方法を数える決定的なカナリア。
        辞書引きの回数は「レコード数 × 設定件数」と一致し、
        全走査(__iter__/keys/values/items)は0回であること。
        """
        record_count = 50
        setting_count = 4
        input_order = '1' if bundle == 'yes' else ''
        assign_seq = '1' if bundle == 'yes' else None

        cols = [make_col_data(COLUMN_ID='col-{:03d}'.format(c),
                              COLUMN_NAME_REST='column_{:03d}'.format(c),
                              MVMT_VAR_LINK_ID='vlink-{:03d}'.format(c),
                              COLUMN_ASSIGN_SEQ=assign_seq)
                for c in range(setting_count)]
        sqls, menu_ids, col_lists = build_inputs(table_name=TABLE, menu_id=MENU_ID, col_data_list=cols)

        rows = []
        param_rows = CountingParamSheet()
        for i in range(record_count):
            rid = 'row-{:05d}'.format(i)
            rows.append(make_cmdb_row(row_id=rid, operation_id='ope-001',
                                      host_id='host-{:05d}'.format(i),
                                      input_order=input_order))
            param_rows[rid] = {'column_{:03d}'.format(c): 'value-{:05d}-{:03d}'.format(i, c)
                               for c in range(setting_count)}
        mock_ws_db.cmdb_rows[TABLE] = rows

        instance = make_subvalue_autoreg(param_sheets={MENU_NAME_REST: param_rows})
        vars_ass_list, _ = instance.getCMDBdata(sqls, menu_ids, col_lists, None, mock_ws_db, '1')

        assert len(vars_ass_list) == record_count * setting_count
        assert param_rows.get_calls == record_count * setting_count, \
            "具体値の辞書引き回数が レコード数×設定件数 と一致しない"
        assert param_rows.scan_calls == 0, \
            "具体値辞書が全走査されている(改修前の線形探索に戻っている可能性)"
