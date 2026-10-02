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
SubValueAutoReg.getCMDBdata 用のテスト基盤（サポートモジュール）

パターン表を満たすテストを書くための共通部品を提供する。

  - MockWsDb          : WorkspaceDB(WS_DB) のモック。SQL/テーブル参照を内容で振り分ける。
  - _FakeLoadTable    : load_table.loadTable の戻り（menu_name_rest / カラム定義を保持）。
  - _FakeColumnClass  : common_libs/column/* のカラムクラスのスタブ（ID→値 変換）。
  - get_api_message_text
                      : 本物の messages/API_*.json からメッセージ本文を読む。
  - disused_id_value  : 廃止/未登録IDを ID指定カラムが出力する「値」(MSG-00001の本文)。
  - CountingParamSheet: 具体値辞書へのアクセス方法(辞書引き/全走査)を数えるプローブ。
  - make_col_data     : 代入値自動登録設定 1カラム分(col_data)のビルダー。
  - make_cmdb_row     : 紐付メニュー(パラメータシート)の 1レコード分のビルダー。
  - build_inputs      : getCMDBdata の3つの入力辞書を組み立てるビルダー。
  - get_logged_messages / assert_log_contains / assert_log_not_contains
                        : g.applogger に出力されたログ(メッセージコード)の捕捉・検証ヘルパ。

パターン表との対応（値の差し込みポイント）:
  - レコード数 / レコード有効性 : make_cmdb_row を並べて cmdb_rows に設定
  - カラム具体値 (有/無/TPF/CPF/FileUpload/廃止) : param_sheets の値 + make_col_data の REF_*
  - 登録方式 (Value/Key) : make_col_data(COL_TYPE=...)
  - 代入順序 (有/無)     : make_col_data(COLUMN_ASSIGN_SEQ=...) と make_cmdb_row(input_order=...)
  - NULL連携             : make_col_data(NULL_DATA_HANDLING_FLG=...) / g_null_data_handling_def 引数
  - ドライバ (L/P/R)     : make_subvalue_autoreg(driver_id=...)
  - メンバ変数 (R のみ)  : make_col_data(VAL_VAR_TYPE=GC_VARS_ATTR_M_ARRAY, COL_SEQ_COMBINATION_ID=...)
"""

import re

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

# 紐付メニューSELECT結果に含まれる ITA 独自カラム名
HOST_CNT_COL = AnscConst.DF_ITA_LOCAL_HOST_CNT   # '__ITA_LOCAL_COLUMN_2__' 機器一覧の紐付件数
PKEY_COL = AnscConst.DF_ITA_LOCAL_PKEY           # '__ITA_LOCAL_COLUMN_4__' 紐付テーブル主キー値(UUID)

# TPF/CPF 変数カラムとして扱われる REF_TABLE_NAME / REF_COL_NAME
#   （getCMDBdata 内の VariableColumnAry と一致させる）
TPF_REF_TABLE = 'T_ANSC_TEMPLATE_FILE'
TPF_REF_COL = 'ANS_TEMPLATE_VARS_NAME'
CPF_REF_TABLE = 'T_ANSC_CONTENTS_FILE'
CPF_REF_COL = 'CONTENTS_FILE_VARS_NAME'

# CPF/TPF 以外の ID指定(プルダウン選択)カラムの REF_*。
#   標準メニュー(機器一覧)を他メニュー連携で参照した場合の値。
#   ita_by_menu_create/backyard_main.py:1208-1212 と同じ組合せ(COLUMN_CLASS='7' IDColumn)。
ID_REF_TABLE = 'T_ANSC_DEVICE'
ID_REF_PKEY = 'SYSTEM_ID'
ID_REF_COL = 'HOST_NAME'

# パラメータシート参照機能(カラムクラス '11' ParameterSheetReference)で作られるカラムの REF_*。
#   ita_by_menu_create/backyard_main.py:1679-1699 で
#     COLUMN_CLASS = '21'(JsonIDColumn) / パスワード列参照なら '26'(JsonPasswordIDColumn)
#     REF_TABLE_NAME = 参照先パラメータシートのテーブル名
#     REF_PKEY_NAME  = 'OPERATION_ID' 固定
#     REF_COL_NAME   = 参照先カラムの COLUMN_NAME_REST
#   に変換される。
PS_REF_TABLE = 'T_CMDB_9999_REF_SHEET'
PS_REF_PKEY = 'OPERATION_ID'
PS_REF_COL = 'ref_column'

# パラメータシート(CMDB)のテーブル構成。
#   ita_by_menu_create/sql/parameter_sheet_cmdb.sql          (横メニュー)
#   ita_by_menu_create/sql/parameter_sheet_cmdb_vertical.sql (縦メニュー = INPUT_ORDER あり)
# の CREATE TABLE と一致させる。主キーは両方とも ROW_ID(UUID) 単独。
PARAM_SHEET_COLUMNS = ['ROW_ID', 'HOST_ID', 'OPERATION_ID', 'DATA_JSON', 'NOTE',
                       'DISUSE_FLAG', 'LAST_UPDATE_TIMESTAMP', 'LAST_UPDATE_USER']
PARAM_SHEET_COLUMNS_VERTICAL = ['ROW_ID', 'HOST_ID', 'OPERATION_ID', 'INPUT_ORDER', 'DATA_JSON',
                                'NOTE', 'DISUSE_FLAG', 'LAST_UPDATE_TIMESTAMP', 'LAST_UPDATE_USER']
PARAM_SHEET_PKEY = ['ROW_ID']

# table_columns_get の既定の戻り。テーブル構成を仕込まないテスト(getCMDBdata 系)向け。
DEFAULT_TABLE_COLUMNS = ([], list(PARAM_SHEET_PKEY))

# getFromColumnClassMaster / __init__ が引く カラムクラスマスタの既定値。
#   ID と名前は本物の T_COMN_COLUMN_CLASS
#   (ita_api_admin/sql/workspace_master.sql の INSERT) と一致させる。
#   getFromColumnClassMaster は `self.ColumnClassMaster_IDMap[column_class]` と
#   直接添字参照するため、テストで使う COLUMN_CLASS はここに存在しないと KeyError になる。
DEFAULT_COLUMN_CLASS_ROWS = [
    {'COLUMN_CLASS_ID': '1', 'COLUMN_CLASS_NAME': 'SingleTextColumn'},
    {'COLUMN_CLASS_ID': '2', 'COLUMN_CLASS_NAME': 'MultiTextColumn'},
    {'COLUMN_CLASS_ID': '3', 'COLUMN_CLASS_NAME': 'NumColumn'},
    {'COLUMN_CLASS_ID': '7', 'COLUMN_CLASS_NAME': 'IDColumn'},                 # プルダウン選択(ID指定)
    {'COLUMN_CLASS_ID': '8', 'COLUMN_CLASS_NAME': 'PasswordColumn'},
    {'COLUMN_CLASS_ID': '9', 'COLUMN_CLASS_NAME': 'FileUploadColumn'},
    {'COLUMN_CLASS_ID': '11', 'COLUMN_CLASS_NAME': 'ParameterSheetReference'},  # 作成機能側の指定値
    {'COLUMN_CLASS_ID': '20', 'COLUMN_CLASS_NAME': 'FileUploadEncryptColumn'},
    {'COLUMN_CLASS_ID': '21', 'COLUMN_CLASS_NAME': 'JsonIDColumn'},             # 作成メニュー参照/パラメータシート参照
    {'COLUMN_CLASS_ID': '25', 'COLUMN_CLASS_NAME': 'PasswordIDColumn'},
    {'COLUMN_CLASS_ID': '26', 'COLUMN_CLASS_NAME': 'JsonPasswordIDColumn'},     # パラメータシート参照(パスワード列)
]


def get_api_message_text(code, locale='JA'):
    """本物の messages/API_<locale>.json からメッセージ定義文字列を読む。

    mock_g の appmsg はメッセージコードしか返さないため、
    「メッセージ定義そのものに依存した実装」(getCMDBdata の 'ID変換失敗' 文字列マッチ)
    を検証したいテストではこちらを使う。
    """
    import json
    import os

    # このファイルから上に辿って ita_root/messages/API_<locale>.json を探す
    cur = os.path.dirname(os.path.abspath(__file__))
    while cur != os.path.dirname(cur):
        candidate = os.path.join(cur, 'messages', 'API_{}.json'.format(locale))
        if os.path.exists(candidate):
            with open(candidate, encoding='utf-8') as fp:
                return json.load(fp)[code]
        cur = os.path.dirname(cur)
    raise AssertionError('messages/API_{}.json not found'.format(locale))


def disused_id_value(id_value, locale='JA'):
    """廃止/未登録IDを ID指定カラムが出力する「値」を返す。

    本物の IDColumn.convert_value_output は変換できなかったIDについて
    MSG-00001('ID変換失敗({})' / 'Failed to exchange ID. ({})') の
    **メッセージ定義文字列を値として返す**
    ([id_class.py:247-270](../../../../../common_libs/column/id_class.py#L247-L270))。
    したがって「廃止された参照先」は getCMDBdata から見ると
    この文字列が具体値として渡ってくる状態になる。
    """
    return get_api_message_text('MSG-00001', locale).format(id_value)


class _FakeColumnClass:
    """common_libs/column/* のカラムクラスのスタブ。

    convert_colname_restkey が呼ぶ2メソッドのみ実装する。
      - convert_value_output(val) -> (retBool, msg, val)  : ID → 値 への変換
      - get_values_by_key([key])  -> {key: value}          : PasswordID 系で使用

    ID変換失敗時の戻り値は本物の IDColumn
    ([id_class.py:247-270](../../../../../common_libs/column/id_class.py#L247-L270))
    に合わせ、**MSG-00001 のメッセージ定義文字列を値として返す**。
    getCMDBdata 側はこの文字列を部分一致で判定しているため、
    スタブでコードだけ返すと契約テストの意味がなくなる。

    Args:
        class_name  : get_col_class_name が返すクラス名
        id_to_value : ID → 値 の変換表。ここに無いキーは「廃止ID」扱い
        convert_ok  : convert_value_output の retBool（False なら呼び出し側は値を差し替えない）
        locale      : ID変換失敗メッセージのロケール
    """

    def __init__(self, class_name='SingleTextColumn', id_to_value=None,
                 convert_ok=True, locale='JA'):
        self.class_name = class_name
        self.id_to_value = dict(id_to_value) if id_to_value else {}
        self.convert_ok = convert_ok
        self.locale = locale
        self.convert_calls = []
        self.get_values_calls = []

    def get_values_by_key(self, keys):
        self.get_values_calls.append(list(keys))
        return {k: self.id_to_value[k] for k in keys if k in self.id_to_value}

    def convert_value_output(self, val=''):
        self.convert_calls.append(val)
        if val is None:
            return self.convert_ok, '', val
        found = {k: self.id_to_value[k] for k in [val] if k in self.id_to_value}
        if len(found) == 1:
            return self.convert_ok, '', found[val]
        # 廃止/未登録ID: 本物同様 MSG-00001 の本文を「値」として返す
        return self.convert_ok, '', disused_id_value(val, self.locale)


class CountingParamSheet(dict):
    """具体値辞書(rest_filter の戻り)へのアクセス方法を数えるプローブ。

    改修後の getCMDBdata は具体値を「主キー(UUID)での辞書引き1回」だけで取得する
    ([:990](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L990) /
     [:1018](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1018))。
    改修前のように具体値を1件ずつ走査する実装に戻ると
    `__iter__` / `keys` / `values` / `items` のいずれかが呼ばれるため、
    **実行時間に依存せず決定的に**線形性の崩れを検知できる。

    Attributes:
        get_calls : get() の呼び出し回数（= 期待は レコード数 × 設定件数）
        scan_calls: 全走査系メソッドの呼び出し回数（= 期待は 0）
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_calls = 0
        self.scan_calls = 0

    def get(self, key, default=None):
        self.get_calls += 1
        return super().get(key, default)

    def __iter__(self):
        self.scan_calls += 1
        return super().__iter__()

    def keys(self):
        self.scan_calls += 1
        return super().keys()

    def values(self):
        self.scan_calls += 1
        return super().values()

    def items(self):
        self.scan_calls += 1
        return super().items()


class _FakeLoadTable:
    """load_table.loadTable のスタブ。

    getCMDBdata のテストでは menu_name_rest を保持するだけで足りるが、
    rest_filter / convert_colname_restkey のテストでは
    get_json_cols_base / get_columnclass / get_col_class_name も必要になるため、
    カラム定義を渡せるようにしてある。

    Args:
        columns   : {restkey: _FakeColumnClass} 。get_json_cols_base のキー集合にもなる
        view_name : ビュー名。None なら get_table_name が使われる
    """

    def __init__(self, ws_db, menu_name_rest, columns=None, view_name=None):
        self.ws_db = ws_db
        self.menu_name_rest = menu_name_rest
        self.columns = dict(columns) if columns else {}
        self.view_name = view_name

    def get_view_name(self):
        return self.view_name

    def get_table_name(self):
        return self.menu_name_rest

    def get_json_cols_base(self):
        # 本物は「JSON保存カラムを None で初期化した dict」を返す。
        # convert_colname_restkey は戻り値を copy せず書き換えるため、
        # **毎回新しい dict を返すこと**（この前提自体は R6-1/R6-2 で固定している）。
        return {restkey: None for restkey in self.columns}

    def get_columnclass(self, restkey):
        return self.columns[restkey]

    def get_col_class_name(self, restkey):
        return self.columns[restkey].class_name


class MockWsDb:
    """WorkspaceDB(WS_DB) のモック。

    発行された SQL / table_select を内容で判定して、設定済みデータを返す。
    getCMDBdata が呼ぶ以下を最小限サポートする:
      - db_transaction_start / db_transaction_end (no-op、呼び出し記録のみ)
      - sql_execute  (カラムクラスマスタ / 入力メニュー対応表 / SELECT 1 / 紐付メニュー本体)
      - table_select (T_ANSC_IF_INFO など)
      - table_columns_get
    """

    def __init__(self):
        # __init__ / getFromColumnClassMaster が引くカラムクラスマスタ
        self.column_class_rows = list(DEFAULT_COLUMN_CLASS_ROWS)
        # 紐付メニュー -> アップロード用メニューID対応(T_COMN_MENU の自己結合)結果
        self.upload_menu_rows = []
        # {table_name: [紐付メニューSELECT結果レコード, ...]}
        self.cmdb_rows = {}
        # getIFInfoDB 用(getCMDBdata単体では未使用だが公開メソッド経由で使う場合に備える)
        self.if_info_rows = []
        # rest_filter が table_select で引く紐付メニュー本体 {table_or_view_name: [row, ...]}
        self.param_sheet_rows = {}
        # createQuerySelectCMDB / read_val_assign が引くテーブル構成(SHOW COLUMNS 相当)
        # {table_name: (カラム名リスト, 主キー名リスト)}。set_param_sheet_table で仕込む。
        self.table_columns = {}

        # 呼び出し記録（アサート用）
        self.sql_log = []            # [(sql, params), ...]
        self.transaction_log = []    # ['start', ('end', True), ...]
        self.table_select_log = []   # [(table_name, where, params), ...]
        self.table_columns_get_log = []  # [table_name, ...]

    # ------------------------------------------------------------------
    # トランザクション（副作用なし、呼び出しの記録だけ行う）
    # ------------------------------------------------------------------
    def db_transaction_start(self):
        self.transaction_log.append('start')

    def db_transaction_end(self, commit=True):
        self.transaction_log.append(('end', commit))

    # ------------------------------------------------------------------
    # SQL 実行
    # ------------------------------------------------------------------
    def sql_execute(self, sql, params=None):
        self.sql_log.append((sql, params))

        # カラムクラスマスタ取得(getFromColumnClassMaster)
        if 'T_COMN_COLUMN_CLASS' in sql:
            return [dict(r) for r in self.column_class_rows]

        # 紐付メニュー -> 入力用メニューID の対応表
        if 'OUT_MENU_NAME_REST' in sql:
            return [dict(r) for r in self.upload_menu_rows]

        # コネクション維持用の keepalive
        if sql.strip() == 'SELECT 1':
            return [{'1': 1}]

        # 紐付メニュー本体の SELECT: "FROM `<table_name>` TBL_A" からテーブル名を判定
        matched = re.search(r"FROM\s+`([^`]+)`", sql)
        if matched:
            table_name = matched.group(1)
            return [dict(r) for r in self.cmdb_rows.get(table_name, [])]

        return []

    # ------------------------------------------------------------------
    # テーブル参照
    # ------------------------------------------------------------------
    def table_select(self, table_name, where='', params=None):
        self.table_select_log.append((table_name, where, params))
        if table_name == 'T_ANSC_IF_INFO':
            return [dict(r) for r in self.if_info_rows]
        # rest_filter からの紐付メニュー本体の参照
        if table_name in self.param_sheet_rows:
            return [dict(r) for r in self.param_sheet_rows[table_name]]
        return []

    def table_columns_get(self, table_name):
        """(カラム名リスト, 主キー名リスト) を返す。

        本物は `SHOW COLUMNS FROM <table>` の結果から組み立てる
        ([dbconnect_common.py:284-306](../../../../../common_libs/common/dbconnect/dbconnect_common.py#L284-L306))。
        createQuerySelectCMDB は縦メニュー判定に `[0]`(カラム名リスト) を使うため、
        テーブル構成を見るテストでは set_param_sheet_table で仕込むこと。
        """
        self.table_columns_get_log.append(table_name)
        return self.table_columns.get(table_name, DEFAULT_TABLE_COLUMNS)

    def set_param_sheet_table(self, table_name, vertical=False):
        """パラメータシートのテーブル構成(SHOW COLUMNS 相当)を仕込む。

        Args:
            table_name: パラメータシートのテーブル名
            vertical  : True で縦メニュー(INPUT_ORDER 列あり)の構成にする
        Returns:
            仕込んだカラム名リスト
        """
        columns = PARAM_SHEET_COLUMNS_VERTICAL if vertical else PARAM_SHEET_COLUMNS
        self.table_columns[table_name] = (list(columns), list(PARAM_SHEET_PKEY))
        return list(columns)


# ----------------------------------------------------------------------
# ビルダー
# ----------------------------------------------------------------------
def make_col_data(**overrides):
    """代入値自動登録設定の 1カラム分(col_data) を生成する。

    既定値は「Value型 / 一般変数(STD) / 縦メニューでない / 項目あり」の
    もっとも単純に具体値が登録されるケース。
    パターン表に合わせて overrides で差し替える。
    """
    base = {
        'COLUMN_ID': 'col-001',
        'COL_TYPE': AnscConst.DF_COL_TYPE_VAL,            # '1' Value / '2' Key
        'COLUMN_CLASS': '1',                              # DEFAULT_COLUMN_CLASS_ROWS に存在する必要あり
        'COLUMN_NAME_JA': 'カラムA',
        'COLUMN_NAME_EN': 'ColumnA',
        'COLUMN_NAME_REST': 'column_a',                   # param_sheets の値キーと一致させる
        'COL_GROUP_ID': 'grp-001',                        # None にすると「項目なし」(STATUS='skip')
        'REF_TABLE_NAME': None,                           # TPF/CPF 判定用
        'REF_PKEY_NAME': None,
        'REF_COL_NAME': None,
        'MOVEMENT_ID': 'mov-001',
        'MVMT_VAR_LINK_ID': 'vlink-001',
        'VAL_VAR_TYPE': AnscConst.GC_VARS_ATTR_STD,       # '1' 一般 / '2' 複数具体値 / '3' 多次元
        'COLUMN_ASSIGN_SEQ': None,                        # None:横メニュー / 値:縦メニュー(代入順序)
        'COL_SEQ_COMBINATION_ID': None,                   # メンバ変数(R/多次元)
        'VAL_COL_COMBINATION_MEMBER_ALIAS': None,
        'ASSIGN_SEQ': None,
        'VALUE_SENSITIVE_FLAG': AnscConst.DF_SENSITIVE_OFF,
        'KEY_VAR_TYPE': AnscConst.GC_VARS_ATTR_STD,
        'NULL_DATA_HANDLING_FLG': None,                   # None/'0'/'1' -> NULL連携
        'KEY_SENSITIVE_FLAG': AnscConst.DF_SENSITIVE_OFF,
        'MENU_NAME_REST': 'menu_a',                       # param_sheets のキーと一致させる
    }
    base.update(overrides)
    return base


def make_cmdb_row(row_id='row-001', operation_id='ope-001', host_id='host-001',
                  host_cnt=1, input_order='', **overrides):
    """紐付メニュー(パラメータシート)の SELECT 結果 1レコードを生成する。

    Args:
        row_id     : 紐付テーブル主キー値(UUID)。param_sheets のキーと一致させる。
        operation_id: オペレーションID。空/None にすると MSG-10360 でスキップ。
        host_id    : ホストID。空/None にすると MSG-10361 でスキップ。
        host_cnt   : 機器一覧の紐付件数。0 にすると MSG-10359 でスキップ。
        input_order: 縦メニュー用の代入順序。'' は横メニュー扱い。
    """
    row = {
        'OPERATION_ID': operation_id,
        'HOST_ID': host_id,
        HOST_CNT_COL: host_cnt,
        PKEY_COL: row_id,
        'INPUT_ORDER': input_order,
    }
    row.update(overrides)
    return row


def build_inputs(table_name='T_PARAM_SHEET', menu_id='menu-001', col_data_list=None):
    """getCMDBdata の入力3辞書を組み立てる。

    Returns:
        (in_tableNameToSqlList, in_tableNameToMenuIdList, in_tabColNameToValAssRowList)
    """
    if col_data_list is None:
        col_data_list = [make_col_data()]

    data_json = {idx: col_data for idx, col_data in enumerate(col_data_list)}
    in_tabColNameToValAssRowList = {table_name: {'DATA_JSON': data_json}}
    in_tableNameToMenuIdList = {table_name: menu_id}
    # MockWsDb.sql_execute が "FROM `table_name`" でテーブルを判別できる SQL にする
    in_tableNameToSqlList = {
        table_name: "SELECT TBL_A.* FROM `{}` TBL_A WHERE DISUSE_FLAG = '0'".format(table_name)
    }
    return in_tableNameToSqlList, in_tableNameToMenuIdList, in_tabColNameToValAssRowList


# ----------------------------------------------------------------------
# ログ捕捉ヘルパ
#   conftest の mock_g で appmsg.get_api_message はメッセージコードを含む
#   文字列を返すため、applogger の呼び出し引数からコードを拾える。
# ----------------------------------------------------------------------
def get_logged_messages(mock_g):
    """g.applogger に出力された文字列(第1引数)を全レベル分集めて返す。"""
    messages = []
    logger = mock_g.applogger
    for level in ('debug', 'info', 'warning', 'error', 'critical'):
        method = getattr(logger, level, None)
        if method is None:
            continue
        for call in method.call_args_list:
            args = call.args
            if args:
                messages.append(str(args[0]))
    return messages


def assert_log_contains(mock_g, code):
    """指定のメッセージコード(例 'MSG-10360')がログ出力されたことを検証する。"""
    messages = get_logged_messages(mock_g)
    assert any(code in m for m in messages), \
        "expected log '{}' not found. logged={}".format(code, messages)


def assert_log_not_contains(mock_g, code):
    """指定のメッセージコードがログ出力されていないことを検証する。"""
    messages = get_logged_messages(mock_g)
    assert not any(code in m for m in messages), \
        "unexpected log '{}' found. logged={}".format(code, messages)
