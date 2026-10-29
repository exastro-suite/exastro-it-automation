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
SubValueAutoReg.rest_filter / convert_colname_restkey の単体テスト

位置づけ:
  test_SubValueAutoReg_getCMDBdata.py では rest_filter をスタブ化しているため、
  rest_filter の戻り値の形が変わっても getCMDBdata のテストは緑のままになる。
  本ファイルは
    (a) rest_filter / convert_colname_restkey 自体の分岐網羅
    (b) getCMDBdata が前提としている「戻り値の契約」の固定
  を担う。(b) が壊れたら getCMDBdata 側のスタブも直す必要がある、という対応関係。
"""

import json

import pytest

from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg
from common_libs.loadtable.load_table import loadTable

from .subvalue_autoreg_support import (
    HOST_CNT_COL,
    PKEY_COL,
    _FakeColumnClass,
    _FakeLoadTable,
    get_api_message_text,
    make_cmdb_row,
    make_col_data,
)

TABLE = 'T_PARAM_SHEET'
VIEW = 'V_PARAM_SHEET'


# ----------------------------------------------------------------------
# ヘルパ
# ----------------------------------------------------------------------
def make_sheet_row(row_id='row-001', operation_id='ope-001', host_id='host-001',
                   data_json=None, input_order=None, **overrides):
    """rest_filter が table_select で受け取る紐付メニュー1レコードを作る。

    rest_filter は 'ROW_ID' / 'HOST_ID' / 'OPERATION_ID' / 'DATA_JSON' を参照し、
    'INPUT_ORDER' はキーが存在するときだけ拾う(=縦メニュー判定)。
    """
    row = {
        'ROW_ID': row_id,
        'HOST_ID': host_id,
        'OPERATION_ID': operation_id,
        'DATA_JSON': data_json if data_json is None or isinstance(data_json, str)
        else json.dumps(data_json, ensure_ascii=False),
    }
    if input_order is not None:
        row['INPUT_ORDER'] = input_order
    row.update(overrides)
    return row


@pytest.fixture
def rest_filter_instance(mock_g, mock_ws_db):
    """rest_filter を素のまま呼べる SubValueAutoReg インスタンス。

    getCMDBdata 用の make_subvalue_autoreg とは違い rest_filter はスタブ化しない。
    """
    return SubValueAutoReg(in_driver_name='R', ws_db=mock_ws_db)


def call_rest_filter(instance, ws_db, rows, columns=None, view_name=None,
                     table_name=TABLE):
    """紐付メニューのレコードを仕込んで rest_filter を1回呼ぶ。"""
    lookup_name = view_name if view_name else table_name
    ws_db.param_sheet_rows[lookup_name] = rows
    load_table = _FakeLoadTable(ws_db, table_name, columns=columns, view_name=view_name)
    return instance.rest_filter(ws_db, load_table)


# ======================================================================
# [R1] 参照先テーブル名の決定
# ======================================================================
class TestRestFilterTargetTable:
    """[R1] ビュー名有無で table_select の対象が切り替わる"""

    def test_view_name_present_uses_view(self, rest_filter_instance, mock_ws_db):
        """R1-1 ビュー有: view_name を参照する"""
        cols = {'column_a': _FakeColumnClass(id_to_value={'v': 'value1'})}
        result = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(data_json={'column_a': 'v'})],
            columns=cols, view_name=VIEW,
        )

        selected = [name for name, _, _ in mock_ws_db.table_select_log]
        assert VIEW in selected
        assert TABLE not in selected
        assert result['row-001']['column_a'] == 'value1'

    def test_view_name_absent_uses_table(self, rest_filter_instance, mock_ws_db):
        """R1-2 ビュー無: table_name を参照する"""
        cols = {'column_a': _FakeColumnClass(id_to_value={'v': 'value1'})}
        call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(data_json={'column_a': 'v'})],
            columns=cols,
        )

        selected = [name for name, _, _ in mock_ws_db.table_select_log]
        assert TABLE in selected

    def test_disuse_flag_filter_in_where(self, rest_filter_instance, mock_ws_db):
        """R1-3 廃止レコードは WHERE DISUSE_FLAG='0' で除外される"""
        call_rest_filter(rest_filter_instance, mock_ws_db, [], columns={})

        wheres = [where for name, where, _ in mock_ws_db.table_select_log if name == TABLE]
        assert wheres, 'table_select が呼ばれていない'
        assert "DISUSE_FLAG = '0'" in wheres[0]


# ======================================================================
# [R2] 戻り値の形 (= getCMDBdata との契約)
# ======================================================================
class TestRestFilterReturnShape:
    """[R2] 戻り値は {ROW_ID: parameter} の dict

    getCMDBdata:990 / :1018 は
        tmp_result.get(row[PKEY_COL], {})
    で引くため、dict でなければ（例: 昔の実装のような list に戻ると）動かない。
    """

    def test_returns_dict_keyed_by_row_id(self, rest_filter_instance, mock_ws_db):
        """R2-1 ROW_ID をキーにした dict を返す(list ではない)"""
        cols = {'column_a': _FakeColumnClass(id_to_value={'v': 'value1'})}
        result = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [
                make_sheet_row(row_id='row-001', data_json={'column_a': 'v'}),
                make_sheet_row(row_id='row-002', data_json={'column_a': 'v'}),
            ],
            columns=cols,
        )

        assert isinstance(result, dict)
        assert set(result.keys()) == {'row-001', 'row-002'}

    def test_fixed_keys_present(self, rest_filter_instance, mock_ws_db):
        """R2-2 uuid / HOST_ID / OPERATION_ID が必ず含まれる"""
        result = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(row_id='row-001', operation_id='ope-A', host_id='host-A',
                            data_json={})],
            columns={},
        )

        parameter = result['row-001']
        assert parameter['uuid'] == 'row-001'
        assert parameter['HOST_ID'] == 'host-A'
        assert parameter['OPERATION_ID'] == 'ope-A'

    def test_zero_records_returns_empty_dict(self, rest_filter_instance, mock_ws_db):
        """R2-3 レコード0件: 空 dict（None ではない）"""
        result = call_rest_filter(rest_filter_instance, mock_ws_db, [], columns={})
        assert result == {}

    @pytest.mark.parametrize("input_order,expect_key", [
        ('1', True),     # R2-4 縦メニュー: INPUT_ORDER キー有 -> input_order を持つ
        (None, False),   # R2-5 横メニュー: INPUT_ORDER キー無 -> input_order を持たない
    ])
    def test_input_order_only_for_vertical_menu(self, rest_filter_instance, mock_ws_db,
                                                input_order, expect_key):
        """R2-4/R2-5 INPUT_ORDER はキーが存在するときだけ input_order として載る"""
        result = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(data_json={}, input_order=input_order)],
            columns={},
        )

        parameter = result['row-001']
        assert ('input_order' in parameter) is expect_key
        if expect_key:
            assert parameter['input_order'] == input_order

    def test_duplicate_row_id_last_wins(self, rest_filter_instance, mock_ws_db):
        """R2-6 ROW_ID が重複した場合は後勝ち(dict 代入のため件数は1)

        主キーなので実運用では起きないが、dict 化により list 実装時と挙動が
        変わる点を仕様として固定しておく。
        """
        cols = {'column_a': _FakeColumnClass(id_to_value={'v1': 'first', 'v2': 'second'})}
        result = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [
                make_sheet_row(row_id='dup', data_json={'column_a': 'v1'}),
                make_sheet_row(row_id='dup', data_json={'column_a': 'v2'}),
            ],
            columns=cols,
        )

        assert len(result) == 1
        assert result['dup']['column_a'] == 'second'


# ======================================================================
# [R3] convert_colname_restkey: DATA_JSON の展開
# ======================================================================
class TestConvertColnameRestkey:
    """[R3] DATA_JSON -> restkey 付き dict への変換"""

    def test_data_json_none_returns_base_only(self, rest_filter_instance, mock_ws_db):
        """R3-1 DATA_JSON=None: 全カラム None で初期化された base がそのまま返る"""
        cols = {'column_a': _FakeColumnClass(), 'column_b': _FakeColumnClass()}
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns=cols)

        result = rest_filter_instance.convert_colname_restkey(load_table, None)

        assert result == {'column_a': None, 'column_b': None}
        # 変換は一度も呼ばれない
        assert cols['column_a'].convert_calls == []

    def test_data_json_empty_returns_base_only(self, rest_filter_instance, mock_ws_db):
        """R3-2 DATA_JSON='{}': base のみ(変換なし)"""
        cols = {'column_a': _FakeColumnClass()}
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns=cols)

        result = rest_filter_instance.convert_colname_restkey(load_table, '{}')

        assert result == {'column_a': None}
        assert cols['column_a'].convert_calls == []

    def test_unknown_key_is_ignored(self, rest_filter_instance, mock_ws_db):
        """R3-3 json_cols_base に無いキーは無視される(項目削除相当)

        getCMDBdata:1004 の `col_data['COLUMN_NAME_REST'] in parameter` が
        False になる = 「項目が削除された」経路の入力側にあたる。
        """
        cols = {'column_a': _FakeColumnClass(id_to_value={'v': 'value1'})}
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns=cols)

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'v', 'column_zzz': 'ignored'}))

        assert 'column_zzz' not in result
        assert result == {'column_a': 'value1'}

    def test_column_not_in_data_json_stays_none(self, rest_filter_instance, mock_ws_db):
        """R3-4 DATA_JSON に含まれないカラムは None のまま(具体値「無」)"""
        cols = {'column_a': _FakeColumnClass(id_to_value={'v': 'value1'}),
                'column_b': _FakeColumnClass()}
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns=cols)

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'v'}))

        assert result == {'column_a': 'value1', 'column_b': None}

    @pytest.mark.parametrize("class_name", ['PasswordColumn', 'MultiPasswordColumn'])
    def test_password_column_passes_value_through(self, rest_filter_instance, mock_ws_db,
                                                  class_name):
        """R3-5 PasswordColumn/MultiPasswordColumn: 変換せず素通し"""
        col = _FakeColumnClass(class_name=class_name, id_to_value={'enc': 'DECODED'})
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns={'column_a': col})

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'enc'}))

        assert result['column_a'] == 'enc'          # 変換されない
        assert col.convert_calls == []
        assert col.get_values_calls == []

    @pytest.mark.parametrize("class_name", ['PasswordIDColumn', 'JsonPasswordIDColumn'])
    def test_password_id_column_uses_get_values_by_key(self, rest_filter_instance,
                                                       mock_ws_db, class_name):
        """R3-6 PasswordIDColumn/JsonPasswordIDColumn: get_values_by_key の結果を使う"""
        col = _FakeColumnClass(class_name=class_name, id_to_value={'pid': 'BASE64VAL'})
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns={'column_a': col})

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'pid'}))

        assert result['column_a'] == 'BASE64VAL'
        assert col.get_values_calls == [['pid']]
        assert col.convert_calls == []

    def test_password_id_column_unknown_key_becomes_none(self, rest_filter_instance,
                                                         mock_ws_db):
        """R3-7 PasswordIDColumn で ID が引けない: dict.get の結果 None になる

        convert_value_output 経路と違い ID変換失敗メッセージにはならない。
        """
        col = _FakeColumnClass(class_name='PasswordIDColumn', id_to_value={})
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns={'column_a': col})

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'missing'}))

        assert result['column_a'] is None

    def test_password_id_column_none_value_skips_lookup(self, rest_filter_instance,
                                                        mock_ws_db):
        """R3-8 PasswordIDColumn で値が None: 引き当てを行わず None のまま"""
        col = _FakeColumnClass(class_name='PasswordIDColumn')
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns={'column_a': col})

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': None}))

        assert result['column_a'] is None
        assert col.get_values_calls == []

    def test_other_column_uses_convert_value_output(self, rest_filter_instance, mock_ws_db):
        """R3-9 その他のカラム: convert_value_output の戻り値で置換(GBL(id) 成功系)"""
        col = _FakeColumnClass(class_name='IDColumn', id_to_value={'gbl-1': 'resolved_gbl'})
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns={'column_a': col})

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'gbl-1'}))

        assert result['column_a'] == 'resolved_gbl'
        assert col.convert_calls == ['gbl-1']

    def test_convert_value_output_false_keeps_original(self, rest_filter_instance, mock_ws_db):
        """R3-10 convert_value_output の retBool=False: 値を差し替えない

        本番の実装は `if tmp_exec[0] is True:` なので、False の場合は
        変換前の値(=ID)がそのまま残る。
        """
        col = _FakeColumnClass(class_name='IDColumn', id_to_value={'gbl-1': 'resolved_gbl'},
                               convert_ok=False)
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns={'column_a': col})

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'gbl-1'}))

        assert result['column_a'] == 'gbl-1'

    def test_mixed_column_classes_in_one_record(self, rest_filter_instance, mock_ws_db):
        """R3-11 1レコードにカラムクラスが混在しても分岐が他カラムに干渉しない

        R3-5〜R3-10 は 1カラムだけの DATA_JSON で各分岐を確認している。
        本番の DATA_JSON は複数カラムを含み、実装は
        ループ内で `jsonval` を再代入しながら回す
        ([SubValueAutoReg.py:1997-2014](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1997-L2014))
        ため、混在時に前のカラムの値/呼び出しが漏れないことを1ケースで押さえる。
        """
        cols = {
            'plain_pw': _FakeColumnClass(class_name='PasswordColumn',
                                         id_to_value={'enc': 'DECODED'}),
            'pw_id': _FakeColumnClass(class_name='PasswordIDColumn',
                                      id_to_value={'pid': 'BASE64VAL'}),
            'id_ok': _FakeColumnClass(class_name='IDColumn',
                                      id_to_value={'gbl-1': 'resolved_gbl'}),
            'id_disused': _FakeColumnClass(class_name='IDColumn', id_to_value={}),
            'not_in_json': _FakeColumnClass(class_name='IDColumn',
                                            id_to_value={'x': 'never_used'}),
        }
        load_table = _FakeLoadTable(mock_ws_db, TABLE, columns=cols)

        result = rest_filter_instance.convert_colname_restkey(load_table, json.dumps({
            'plain_pw': 'enc',            # R3-5 素通し
            'pw_id': 'pid',               # R3-6 get_values_by_key
            'id_ok': 'gbl-1',             # R3-9 convert_value_output 成功
            'id_disused': 'disused-id',   # R4-2 ID変換失敗メッセージ
            'column_zzz': 'ignored',      # R3-3 base外キー
        }))

        assert result['plain_pw'] == 'enc'
        assert result['pw_id'] == 'BASE64VAL'
        assert result['id_ok'] == 'resolved_gbl'
        assert 'ID変換失敗' in result['id_disused']
        assert result['not_in_json'] is None       # R3-4 未出現は None のまま
        assert 'column_zzz' not in result

        # 呼び出しが他カラムのクラスに漏れていない
        assert cols['plain_pw'].convert_calls == []
        assert cols['plain_pw'].get_values_calls == []
        assert cols['pw_id'].get_values_calls == [['pid']]
        assert cols['pw_id'].convert_calls == []
        assert cols['id_ok'].convert_calls == ['gbl-1']
        assert cols['id_disused'].convert_calls == ['disused-id']
        assert cols['not_in_json'].convert_calls == []


# ======================================================================
# [R4] getCMDBdata との契約: 廃止ID の表現
# ======================================================================
class TestDisusedIdContract:
    """[R4] 廃止ID が getCMDBdata の判定文字列と一致することの確認

    getCMDBdata:1011 / :1042 は
        if 'ID変換失敗' not in col_val and 'Failed to exchange ID' not in col_val:
    というハードコードされた部分一致で TPF/CPF の廃止を判定している。
    この文字列の出どころは messages/API_{JA,EN}.json の MSG-00001 なので、
    **メッセージ定義を変えると getCMDBdata の判定が黙って壊れる**。
    ここでは両者が実際に噛み合っていることを固定する。
    """

    # getCMDBdata が廃止判定に使っているマーカー(実装と一致させる)
    MARKERS = ('ID変換失敗', 'Failed to exchange ID')

    @pytest.mark.parametrize("locale", ['JA', 'EN'])
    def test_msg_00001_contains_getcmdbdata_marker(self, locale):
        """R4-1 MSG-00001 の定義文が getCMDBdata のマーカーを含む

        失敗した場合は messages/API_*.json の変更に対して
        SubValueAutoReg.py:1011 / :1042 の判定を追随させる必要がある。
        """
        text = get_api_message_text('MSG-00001', locale)
        assert any(marker in text for marker in self.MARKERS), \
            "MSG-00001({})='{}' が getCMDBdata の廃止判定文字列 {} を含まない".format(
                locale, text, self.MARKERS)

    @pytest.mark.parametrize("locale", ['JA', 'EN'])
    def test_disused_id_value_is_detectable_by_getcmdbdata(self, rest_filter_instance,
                                                           mock_ws_db, locale):
        """R4-2 廃止ID(引けないID)の変換結果が getCMDBdata で廃止と判定できる形になる"""
        col = _FakeColumnClass(class_name='IDColumn', id_to_value={}, locale=locale)
        result = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(data_json={'column_a': 'disused-id'})],
            columns={'column_a': col},
        )

        col_val = result['row-001']['column_a']
        assert any(marker in col_val for marker in self.MARKERS), \
            "廃止IDの値 '{}' が getCMDBdata の廃止判定に引っかからない".format(col_val)
        # 元のIDが埋め込まれていること(MSG-00001 の {} 部分)
        assert 'disused-id' in col_val

    def test_valid_id_is_not_detected_as_disused(self, rest_filter_instance, mock_ws_db):
        """R4-3 正常な変換結果は廃止と誤判定されない(偽陽性がない)"""
        col = _FakeColumnClass(class_name='IDColumn', id_to_value={'tpf-1': 'TPF_X'})
        result = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(data_json={'column_a': 'tpf-1'})],
            columns={'column_a': col},
        )

        col_val = result['row-001']['column_a']
        assert not any(marker in col_val for marker in self.MARKERS)


# ======================================================================
# [R5] getCMDBdata のスタブが本物と同じ形か
# ======================================================================
class TestStubMatchesRealRestFilter:
    """[R5] getCMDBdata テストのスタブ(conftest)が本物の戻り値の形と一致するか

    ここが失敗したら、getCMDBdata 側のテストが「本物ではありえない入力」で
    緑になっている（=スタブのドリフト）ことを意味する。
    """

    def test_stub_shape_equals_real_shape(self, rest_filter_instance, mock_ws_db):
        """R5-1 本物の戻り値のキー構造が、スタブ(param_sheets)の構造と一致する

        スタブは
            {menu_name_rest: {row_id: {COLUMN_NAME_REST: 具体値}}}
        の内側 `{row_id: {...}}` をそのまま rest_filter の戻り値として渡している。
        本物も「row_id -> 具体値 dict」であり、かつ固定キーが追加で載る。
        """
        col_data = make_col_data()          # COLUMN_NAME_REST='column_a'
        col = _FakeColumnClass(class_name='IDColumn', id_to_value={'v': 'value1'})
        real = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(row_id='row-001', data_json={'column_a': 'v'})],
            columns={'column_a': col},
        )

        # getCMDBdata が行う引き方が本物に対しても成立する
        cmdb_row = make_cmdb_row(row_id='row-001')
        parameter = real.get(cmdb_row[PKEY_COL], {})
        assert parameter, 'PKEY_COL(紐付テーブル主キー) で引けない'
        assert col_data['COLUMN_NAME_REST'] in parameter
        assert parameter[col_data['COLUMN_NAME_REST']] == 'value1'

        # スタブが省略している固定キー。getCMDBdata は現状これらを参照しないが、
        # 参照するようになったらスタブ側も足す必要がある。
        assert {'uuid', 'HOST_ID', 'OPERATION_ID'} <= set(parameter.keys())

    def test_cmdb_row_pkey_matches_rest_filter_key(self, rest_filter_instance, mock_ws_db):
        """R5-2 紐付メニューSELECT の主キー(PKEY_COL) と rest_filter のキー(ROW_ID) が同一値

        getCMDBdata は SELECT 結果の `__ITA_LOCAL_COLUMN_4__` で
        rest_filter の戻りを引く。両者が同じ ROW_ID を指していることが前提。
        """
        col = _FakeColumnClass(class_name='IDColumn', id_to_value={'v': 'value1'})
        real = call_rest_filter(
            rest_filter_instance, mock_ws_db,
            [make_sheet_row(row_id='uuid-xyz', data_json={'column_a': 'v'})],
            columns={'column_a': col},
        )

        cmdb_row = make_cmdb_row(row_id='uuid-xyz', host_cnt=1)
        assert cmdb_row[PKEY_COL] in real
        assert cmdb_row[HOST_CNT_COL] == 1   # 件数カラムは SELECT 側のみに存在
        assert 'uuid-xyz' == real['uuid-xyz']['uuid']


# ======================================================================
# [R6] json_cols_base の独立性 (レコード間で値が漏れないこと)
# ======================================================================
class _ObjColsOnlyStub:
    """本物の loadTable.get_json_cols_base が参照する2メソッドだけを持つスタブ。

    get_json_cols_base ([load_table.py:774-780](../../../../../common_libs/loadtable/load_table.py#L774-L780))
    は self.get_objcols() と self.get_save_type() しか使わないため、
    DB 接続なしで実物のメソッドを呼べる。
    """

    def get_objcols(self):
        return {'column_a': {}, 'column_b': {}}

    def get_save_type(self, rest_key):
        return 'JSON'


class _RecordingLoadTable(_FakeLoadTable):
    """get_json_cols_base が返した dict を記録する _FakeLoadTable。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_calls = []

    def get_json_cols_base(self):
        base = super().get_json_cols_base()
        self.base_calls.append(base)
        return base


class _SharedBaseLoadTable(_FakeLoadTable):
    """get_json_cols_base が毎回「同じ」dict を返す _FakeLoadTable。

    実物は毎回組み立て直すので現状こうはならないが、
    キャッシュ化された場合を模す (R6-4)。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._base = {restkey: None for restkey in self.columns}

    def get_json_cols_base(self):
        return self._base


class TestJsonColsBaseIsolation:
    """[R6] convert_colname_restkey は base を copy せず書き換える

    実装 ([SubValueAutoReg.py:1991](../../../../../common_libs/ansible_driver/classes/SubValueAutoReg.py#L1991))
        data_json_parameter = obj_load_table.get_json_cols_base()
    は copy を取らないため、「レコードごとに新しい base が返る」ことは
    **loadTable 側の実装に依存した暗黙の前提**になっている。
    ここが崩れると 1件目の具体値が2件目以降に漏れ、R3-4(未出現カラムは None)が
    2件目から成立しなくなる。R4/R5 と同種の「別ユニットへの依存」の固定。
    """

    def test_real_get_json_cols_base_returns_fresh_dict(self):
        """R6-1 実物の get_json_cols_base は呼ぶたびに別 dict を返す

        ここが落ちる(=キャッシュを返すようになった)場合、
        convert_colname_restkey 側で copy を取る必要がある。R6-4 も参照。
        """
        stub = _ObjColsOnlyStub()

        first = loadTable.get_json_cols_base(stub)
        second = loadTable.get_json_cols_base(stub)

        assert first == {'column_a': None, 'column_b': None}
        assert first == second
        assert first is not second

        # 戻り値を書き換えても次の呼び出しに影響しない
        first['column_a'] = 'MUTATED'
        assert loadTable.get_json_cols_base(stub)['column_a'] is None

    def test_convert_colname_restkey_returns_base_itself(self, rest_filter_instance,
                                                         mock_ws_db):
        """R6-2 戻り値は get_json_cols_base の戻り値そのもの(copy していない)

        R6-1 への依存を明示的に固定する。ここが落ちた(copy するようになった)
        場合は R6-4 の既知の脆さも解消しているので、ケース表を更新すること。
        """
        col = _FakeColumnClass(class_name='IDColumn', id_to_value={'v': 'value1'})
        load_table = _RecordingLoadTable(mock_ws_db, TABLE, columns={'column_a': col})

        result = rest_filter_instance.convert_colname_restkey(
            load_table, json.dumps({'column_a': 'v'}))

        assert len(load_table.base_calls) == 1
        assert result is load_table.base_calls[0]

    def test_records_do_not_share_values(self, rest_filter_instance, mock_ws_db):
        """R6-3 複数レコードで前レコードの具体値が漏れない

        R2-1 は2レコードとも同じカラム/同じ値なので、この漏れを検知できない。
        ここでは row-001 が column_a のみ、row-002 が column_b のみを持たせる。
        """
        cols = {
            'column_a': _FakeColumnClass(class_name='IDColumn',
                                         id_to_value={'a': 'value_a'}),
            'column_b': _FakeColumnClass(class_name='IDColumn',
                                         id_to_value={'b': 'value_b'}),
        }
        load_table = _RecordingLoadTable(mock_ws_db, TABLE, columns=cols)
        mock_ws_db.param_sheet_rows[TABLE] = [
            make_sheet_row(row_id='row-001', data_json={'column_a': 'a'}),
            make_sheet_row(row_id='row-002', data_json={'column_b': 'b'}),
        ]

        result = rest_filter_instance.rest_filter(mock_ws_db, load_table)

        assert result['row-001']['column_a'] == 'value_a'
        assert result['row-001']['column_b'] is None
        assert result['row-002']['column_a'] is None    # 1件目の値が漏れていない
        assert result['row-002']['column_b'] == 'value_b'

        # レコードごとに別の base を受け取っている
        assert len(load_table.base_calls) == 2
        assert load_table.base_calls[0] is not load_table.base_calls[1]

    @pytest.mark.xfail(strict=True, reason=(
        "既知の脆さ: convert_colname_restkey は base を copy しないため、"
        "get_json_cols_base がキャッシュを返すようになると値が漏れる。"
        "R6-1 が守られている限り実害はない。"
        "このテストが xpass したら実装が copy を取るようになった(=脆さが解消した)ので、"
        "本マークとケース表 R6-4 を削除すること。"))
    def test_shared_base_leaks_values_across_records(self, rest_filter_instance,
                                                     mock_ws_db):
        """R6-4 base が共有されると値が漏れる(実装の前提を可視化する)"""
        cols = {
            'column_a': _FakeColumnClass(class_name='IDColumn',
                                         id_to_value={'a': 'value_a'}),
            'column_b': _FakeColumnClass(class_name='IDColumn',
                                         id_to_value={'b': 'value_b'}),
        }
        load_table = _SharedBaseLoadTable(mock_ws_db, TABLE, columns=cols)
        mock_ws_db.param_sheet_rows[TABLE] = [
            make_sheet_row(row_id='row-001', data_json={'column_a': 'a'}),
            make_sheet_row(row_id='row-002', data_json={'column_b': 'b'}),
        ]

        result = rest_filter_instance.rest_filter(mock_ws_db, load_table)

        assert result['row-002']['column_a'] is None
