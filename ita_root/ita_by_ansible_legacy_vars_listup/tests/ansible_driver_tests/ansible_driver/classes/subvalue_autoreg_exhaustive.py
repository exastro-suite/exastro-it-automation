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
SubValueAutoReg.getCMDBdata の全組合せ（431,424件）実行基盤

subvalue_autoreg_axes.py の軸定義から**実現可能な組合せを全列挙**し、
1件ずつ getCMDBdata を実行して結果を突き合わせる。

なぜ全件やるのか
----------------
既存の test_SubValueAutoReg_getCMDBdata.py は「判定順序に従ってベースライン値を
決め、1軸だけ動かす」構成なので、判定順序が変わると
「パターン表を満たしている」と言えなくなる（= レビュー指摘）。

全件実行はベースライン値・同値類への丸め・段階分解を**一切使わない**ので、
判定順序に依存しない。1件あたり約 170us（実測）なので
431,424 件でも 1コア 約73秒 / 6コア 約13秒 で回る。

期待値の扱い
------------
全件分の期待値は人手では書けないため、**現実装の出力をゴールデンとして固定**する。
  - 保証すること   : 判定順序を変えたら、影響を受けた項番が全部わかる
  - 保証しないこと : 現実装が仕様として正しいか（変化しか見ない）
「仕様として正しいか」は パターン表 70行の手書き期待値
（test_SubValueAutoReg_getCMDBdata.py）側の役割。役割が違う2枚構成にしてある。

pytest 項目にしない理由
-----------------------
431,424 を parametrize すると 1項目あたり約14ms の pytest オーバーヘッド
（実測: 122項目 2.3秒）で約1.7時間かかり、収集時のメモリと
VSCode のテスト一覧も破壊する。実処理は 0.2ms なので、
**pytest 項目は1本にして、その中でループする**。

項番
----
AXIS_ORDER の順に mixed-radix で全直積を走査し、is_feasible() を通ったものに
1 から連番を振る。軸の順序・各軸の値の順序が変わらなければ項番は不変。
逆に軸や値を増減させたら項番は振り直しになる（そのときはゴールデンも作り直す）。
"""

import hashlib
import itertools
import os
import sys
from unittest.mock import patch

from flask import Flask, g

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

from . import subvalue_autoreg_axes as axes_mod
from .subvalue_autoreg_support import (
    MockWsDb,
    _FakeLoadTable,
    build_inputs,
    disused_id_value,
    make_cmdb_row,
    make_col_data,
    CPF_REF_COL,
    CPF_REF_TABLE,
    ID_REF_COL,
    ID_REF_PKEY,
    ID_REF_TABLE,
    PS_REF_COL,
    PS_REF_PKEY,
    PS_REF_TABLE,
    TPF_REF_COL,
    TPF_REF_TABLE,
)

TABLE = 'T_PARAM_SHEET'
MENU_NAME_REST = 'menu_a'
MENU_ID = 'menu-001'
UPLOAD_MENU_ID = 'out-menu-1'

# FileUpload 列のパス生成に使う STORAGEPATH。ゴールデンを実行環境から切り離すため、
# ExhaustiveRunner の中で環境変数をこの値に強制する（変更するとゴールデンが変わる）。
STORAGE_ROOT = '/exhaustive-storage/'

# 項番を決める軸の順序（**変更すると項番が振り直しになる**）
AXIS_ORDER = [
    'route',
    'bundle',
    'hostgroup',
    'record_count',
    'record_validity',
    'column_value',
    'reg_type',
    'assign_seq',
    'null_setting',
    'null_if',
    'driver',
    'var_type',
    'locale',
]


# ======================================================================
# カラム具体値（21値）を「col_data の差分 + パラメータシートの値」に落とす表
#
#   overrides   : make_col_data への差分
#   value       : パラメータシートに入る具体値
#   param_mode  : 'normal'       該当カラムのキーで値を入れる
#                 'other_column' 別カラムだけ入れる（= 項目削除）
#                 'row_missing'  どのレコードのキーも入れない（= レコード不在）
#   file_exists : os.path.exists の戻り（None は「この値では効かない」）
#
# 出典は test_SubValueAutoReg_getCMDBdata.py の _VALUE_CASES と
# FileUpload / NULL連携 / 項目削除 / レコード不在 の各テスト。
# ======================================================================
def _cv(overrides=None, value='value1', param_mode='normal', file_exists=None):
    return {'overrides': dict(overrides or {}), 'value': value,
            'param_mode': param_mode, 'file_exists': file_exists}


COLUMN_VALUE_SPEC = {
    'present':      _cv(),
    'none':         _cv(value=None),
    'tpf':          _cv({'REF_TABLE_NAME': TPF_REF_TABLE, 'REF_COL_NAME': TPF_REF_COL}, 'TPF_X'),
    'cpf':          _cv({'REF_TABLE_NAME': CPF_REF_TABLE, 'REF_COL_NAME': CPF_REF_COL}, 'CPF_X'),
    # 廃止TPF/CPF の具体値は IDColumn が返す MSG-00001 の本文そのもの。
    # 実装は ja/en 両方の文言をハードコードで部分一致判定するので両系統を通す。
    'disused_tpf':  _cv({'REF_TABLE_NAME': TPF_REF_TABLE, 'REF_COL_NAME': TPF_REF_COL},
                        disused_id_value('x')),
    'disused_cpf':  _cv({'REF_TABLE_NAME': CPF_REF_TABLE, 'REF_COL_NAME': CPF_REF_COL},
                        disused_id_value('x', 'EN')),
    'fileupload_exists':  _cv({'COLUMN_CLASS': '9'}, 'file.txt', file_exists=True),
    'fileupload_missing': _cv({'COLUMN_CLASS': '9'}, 'file.txt', file_exists=False),
    'item_none':    _cv({'COL_GROUP_ID': None}, 'v'),
    'name_tpf':     _cv(value='{{ TPF_X }}'),
    'name_cpf':     _cv(value='{{ CPF_XX }}'),
    'ref_id':       _cv({'COLUMN_CLASS': '7', 'REF_TABLE_NAME': ID_REF_TABLE,
                         'REF_PKEY_NAME': ID_REF_PKEY, 'REF_COL_NAME': ID_REF_COL}, 'host-A'),
    'ref_id_disused': _cv({'COLUMN_CLASS': '7', 'REF_TABLE_NAME': ID_REF_TABLE,
                           'REF_PKEY_NAME': ID_REF_PKEY, 'REF_COL_NAME': ID_REF_COL},
                          disused_id_value('host-A')),
    'ps_ref':       _cv({'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
                         'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL}, 'ref_value'),
    # #3066: 参照先がファイルアップロード列でも COLUMN_CLASS は '21' になる。
    # 全件実行は「あるべき姿」ではなく**現実装**を固定するので xfail 扱いはしない。
    'ps_ref_fileupload': _cv({'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
                              'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL},
                             'file.txt', file_exists=True),
    'ps_ref_pw':    _cv({'COLUMN_CLASS': '26', 'REF_TABLE_NAME': PS_REF_TABLE,
                         'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL,
                         'VALUE_SENSITIVE_FLAG': AnscConst.DF_SENSITIVE_ON}, 'ref_secret'),
    # パスワード列は廃止で ID を引き直せず具体値が None になる（他のID系は 'ID変換失敗' 文字列）。
    # SENSITIVE ON のまま段階④のNULL連携へ落ちる＝ 'none' とは別入力（※4-2）。
    'ps_ref_pw_disused': _cv({'COLUMN_CLASS': '26', 'REF_TABLE_NAME': PS_REF_TABLE,
                              'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL,
                              'VALUE_SENSITIVE_FLAG': AnscConst.DF_SENSITIVE_ON}, None),
    'ps_ref_disused': _cv({'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
                           'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL},
                          disused_id_value('row-ref-001')),
    # #3068: 参照先が日時/日付でも COLUMN_CLASS は '21'（ps_ref と同じ）。
    # 修正しない方針なので、日時文字列がそのまま具体値になる現状挙動を固定する。
    'ps_ref_datetime': _cv({'COLUMN_CLASS': '21', 'REF_TABLE_NAME': PS_REF_TABLE,
                            'REF_PKEY_NAME': PS_REF_PKEY, 'REF_COL_NAME': PS_REF_COL},
                           '2026/08/31 12:34:56'),
    'col_deleted':  _cv(param_mode='other_column'),
    'row_missing':  _cv(param_mode='row_missing'),
}

# レコード数 -> (件数, ホストIDの振り方, オペIDの振り方)
RECORD_COUNT_SPEC = {
    '0':              (0,  'same', 'same'),
    '1':              (1,  'same', 'same'),
    '10_1host_nope':  (10, 'same', 'each'),
    '10_1host_1ope':  (10, 'same', 'same'),
    '10_nhost_1ope':  (10, 'each', 'same'),
    '10_nhost_nope':  (10, 'each', 'each'),
}

VAR_TYPE_SPEC = {
    'STD':     {'VAL_VAR_TYPE': AnscConst.GC_VARS_ATTR_STD},
    'LIST':    {'VAL_VAR_TYPE': AnscConst.GC_VARS_ATTR_LIST},
    'M_ARRAY': {'VAL_VAR_TYPE': AnscConst.GC_VARS_ATTR_M_ARRAY,
                'COL_SEQ_COMBINATION_ID': 'memb-001'},
}

DRIVER_SPEC = {
    'L': AnscConst.DF_LEGACY_DRIVER_ID,
    'P': AnscConst.DF_PIONEER_DRIVER_ID,
    'R': AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
}

NULL_SETTING_SPEC = {'TRUE': '1', 'FALSE': '0', 'None': None}
NULL_IF_SPEC = {'TRUE': '1', 'FALSE': '0'}


# ======================================================================
# 組合せの列挙と項番
# ======================================================================
def _feasible_values():
    by_key = axes_mod.AXIS_BY_KEY
    return {k: axes_mod.axis_values(by_key[k], include_infeasible=False)
            for k in AXIS_ORDER}


def iter_combos():
    """実現可能な組合せを (項番, combo) で列挙する。項番は 1 始まり。"""
    values = _feasible_values()
    # 値単体の feasible 判定は _feasible_values() で済んでいるので、
    # ここでは軸間制約だけを見る（is_feasible() を全直積に掛けると遅い）。
    checks = [fn for _, fn in axes_mod.CONSTRAINTS]
    no = 0
    for tup in itertools.product(*[values[k] for k in AXIS_ORDER]):
        combo = dict(zip(AXIS_ORDER, tup))
        if not all(fn(combo) for fn in checks):
            continue
        no += 1
        yield no, combo


def total_cases():
    return sum(1 for _ in iter_combos())


def combo_label(combo):
    """項番と1対1に対応する短いラベル（ゴールデンの可読性用）。"""
    return '/'.join(combo[k] for k in AXIS_ORDER)


# ======================================================================
# combo -> getCMDBdata の入力
# ======================================================================
def _row_value(value, index):
    """レコードごとに異なる具体値にする（取り違え検知用）。

    行番号を**末尾に足すだけ**なので、廃止マーカー('ID変換失敗' 等)や
    '{{ ... }}' 形式の判定結果は変わらず、分岐は同じまま値だけが行ごとに変わる。
    """
    if index == 1 or not isinstance(value, str) or value == '':
        return value
    return '{}#{:03d}'.format(value, index)


def build_case(combo):
    """組合せから getCMDBdata の入力一式を作る。

    Returns:
        dict: keys = col_data, rows, param_sheets, reg_operation_id,
              null_if, driver_id, language, file_exists
    """
    cv = COLUMN_VALUE_SPEC[combo['column_value']]

    overrides = dict(cv['overrides'])
    overrides.update(VAR_TYPE_SPEC[combo['var_type']])
    overrides['COL_TYPE'] = (AnscConst.DF_COL_TYPE_VAL if combo['reg_type'] == 'Value'
                             else AnscConst.DF_COL_TYPE_KEY)
    overrides['ASSIGN_SEQ'] = None if combo['assign_seq'] == 'none' else '3'
    overrides['NULL_DATA_HANDLING_FLG'] = NULL_SETTING_SPEC[combo['null_setting']]
    # バンドル（パラメータシート形態）: 縦は COLUMN_ASSIGN_SEQ と INPUT_ORDER を一致させる
    if combo['bundle'] == 'yes':
        overrides['COLUMN_ASSIGN_SEQ'] = '1'
        input_order = '1'
    else:
        overrides['COLUMN_ASSIGN_SEQ'] = None
        input_order = ''

    col_data = make_col_data(**overrides)

    # --- レコード ---
    count, host_mode, ope_mode = RECORD_COUNT_SPEC[combo['record_count']]
    validity = combo['record_validity']
    rows = []
    for i in range(1, count + 1):
        host_id = 'host-001' if host_mode == 'same' else 'host-{:03d}'.format(i)
        ope_id = 'ope-001' if ope_mode == 'same' else 'ope-{:03d}'.format(i)
        host_cnt = 1
        if validity == 'disused_ope':
            ope_id = ''
        elif validity == 'disused_host':
            host_cnt = 0
        rows.append(make_cmdb_row(row_id='row-{:03d}'.format(i), operation_id=ope_id,
                                  host_id=host_id, host_cnt=host_cnt,
                                  input_order=input_order))

    # --- パラメータシートの具体値 ---
    # 2件目以降は値に行番号を付ける。全行同じ値にすると「レコードと具体値の取り違え」
    # (今回の改修の本体。§10-1〜10-3)が起きても出力が変わらず検知できない。
    # 1件目は素の値のままにして、単一レコードのケースをパターン表の期待値と一致させる。
    col_rest = col_data['COLUMN_NAME_REST']
    param_rows = {}
    if cv['param_mode'] == 'row_missing':
        param_rows['row-999'] = {col_rest: cv['value']}
    else:
        key = 'other_column' if cv['param_mode'] == 'other_column' else col_rest
        for i in range(1, count + 1):
            param_rows['row-{:03d}'.format(i)] = {key: _row_value(cv['value'], i)}

    return {
        'col_data': col_data,
        'rows': rows,
        'param_sheets': {MENU_NAME_REST: param_rows},
        'reg_operation_id': None if combo['route'] == 'all' else 'ope-001',
        'null_if': NULL_IF_SPEC[combo['null_if']],
        'driver_id': DRIVER_SPEC[combo['driver']],
        'language': combo['locale'],
        # os.path.exists は「その値で効かない」ときも呼ばれ得るので既定 True
        'file_exists': True if cv['file_exists'] is None else cv['file_exists'],
    }


# ======================================================================
# 実行環境（1回だけ組み立てて 431,424 回使い回す）
# ======================================================================
class _CollectingLogger:
    """g.applogger の軽量スタブ。MagicMock は reset_mock() が重いので使わない。"""

    def __init__(self):
        self.messages = []

    def _record(self, *args, **kwargs):
        if args:
            self.messages.append(str(args[0]))

    debug = info = warning = error = critical = exception = _record

    def clear(self):
        del self.messages[:]


class _AppMsg:
    """g.appmsg のスタブ。メッセージコードを本文に含めて返す（conftest の mock_g と同じ）。"""

    @staticmethod
    def get_api_message(code, args=None):
        return '{}:{}'.format(code, args) if args else '{}'.format(code)

    @staticmethod
    def get_log_message(code, args=None):
        return '{}:{}'.format(code, args) if args else '{}'.format(code)


class ExhaustiveRunner:
    """全組合せ実行用のコンテキストマネージャ。

        with ExhaustiveRunner() as runner:
            for no, combo in iter_combos():
                result = runner.run(combo)
    """

    def __init__(self):
        self._patchers = []
        self._app_ctx = None
        self.logger = _CollectingLogger()
        self._file_exists = True
        self._saved_storagepath = None

    def __enter__(self):
        # FileUpload 列の COL_FILEUPLOAD_PATH は STORAGEPATH から組み立てられるので、
        # 環境変数のままだとゴールデンが実行環境（pytest.ini の env / シェル）に依存する。
        # os.path.exists はパッチ済みで実ファイルは見ないため、固定値を強制する。
        self._saved_storagepath = os.environ.get('STORAGEPATH')
        os.environ['STORAGEPATH'] = STORAGE_ROOT

        app = Flask(__name__)
        self._app_ctx = app.app_context()
        self._app_ctx.push()
        g.USER_ID = 'test_user_id'
        g.SERVICE_NAME = 'test_service'
        g.WORKSPACE_ID = 'test_workspace_id'
        g.ORGANIZATION_ID = 'test_org_id'
        g.LANGUAGE = 'ja'
        g.applogger = self.logger
        g.appmsg = _AppMsg()

        self._patchers.append(patch(
            'common_libs.ansible_driver.classes.SubValueAutoReg.load_table.loadTable',
            side_effect=lambda ws_db, menu_name_rest: _FakeLoadTable(ws_db, menu_name_rest)))
        self._patchers.append(patch(
            'common_libs.ansible_driver.classes.SubValueAutoReg.os.path.exists',
            side_effect=lambda _path: self._file_exists))
        for p in self._patchers:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in self._patchers:
            p.stop()
        self._patchers = []
        self._app_ctx.pop()
        self._app_ctx = None
        if self._saved_storagepath is None:
            os.environ.pop('STORAGEPATH', None)
        else:
            os.environ['STORAGEPATH'] = self._saved_storagepath
        return False

    def run(self, combo):
        """1組合せを実行して結果を返す。

        Returns:
            dict: vars(一般変数レコード), array(多次元レコード),
                  logs(出力されたメッセージコード), sql(発行されたSELECTの形)
        """
        from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

        case = build_case(combo)
        self._file_exists = case['file_exists']
        g.LANGUAGE = case['language']
        self.logger.clear()

        ws_db = MockWsDb()
        ws_db.cmdb_rows[TABLE] = case['rows']
        # 紐付メニュー -> アップロード用メニューID の対応（FileUpload のパス生成に必要）
        ws_db.upload_menu_rows = [{
            'MENU_ID': MENU_ID, 'MENU_NAME_REST': MENU_NAME_REST + '_subst',
            'OUT_MENU_ID': UPLOAD_MENU_ID, 'OUT_MENU_NAME_REST': MENU_NAME_REST,
        }]

        sqls, menu_ids, col_lists = build_inputs(
            table_name=TABLE, menu_id=MENU_ID, col_data_list=[case['col_data']])

        instance = SubValueAutoReg(in_driver_name=case['driver_id'], ws_db=ws_db)
        sheets = case['param_sheets']
        instance.rest_filter = (
            lambda WS_DB, obj_load_table:
            sheets.get(getattr(obj_load_table, 'menu_name_rest', None), {}))

        vars_list, array_list = instance.getCMDBdata(
            sqls, menu_ids, col_lists, case['reg_operation_id'], ws_db, case['null_if'])

        return {
            'vars': vars_list,
            'array': array_list,
            'logs': _message_codes(self.logger.messages),
            'sql': _sql_shape(ws_db),
        }


def _message_codes(messages):
    """ログ本文から MSG-xxxxx を拾って昇順のリストにする。"""
    codes = set()
    for m in messages:
        idx = m.find('MSG-')
        while idx >= 0:
            code = m[idx:idx + 9]
            if code[4:].isdigit():
                codes.add(code)
            idx = m.find('MSG-', idx + 1)
    return sorted(codes)


def _sql_shape(ws_db):
    """紐付メニューSELECTの「形」。経路(route)軸はここにしか現れない。"""
    for sql, params in reversed(ws_db.sql_log):
        if 'FROM `{}`'.format(TABLE) in sql:
            return ('OPERATION_ID = %s' in sql, len(params or []),
                    (params or [None])[-1])
    return None


# ======================================================================
# 出力の正規化とダイジェスト
# ======================================================================
def normalize(result):
    """突き合わせ対象の文字列表現。dict のキー順に依存しないよう並べ替える。"""
    def rec(r):
        return '{' + ','.join('{}={!r}'.format(k, r[k]) for k in sorted(r)) + '}'

    return '|'.join([
        'V:' + ';'.join(rec(r) for r in result['vars']),
        'A:' + ';'.join(rec(r) for r in result['array']),
        'L:' + ','.join(result['logs']),
        'S:' + repr(result['sql']),
    ])


def digest(result):
    return hashlib.sha1(normalize(result).encode('utf-8')).hexdigest()


def summary(result):
    """人が読める1行要約（ゴールデンの distinct 側と、テスト失敗時の差分表示に使う）。

    ハッシュだけだと「何が変わったか」が読めないので、
    件数・STATUS・ログのほかに先頭レコードの主要フィールドまで入れる。
    """
    records = result['vars'] + result['array']
    if records:
        head = records[0]
        first = ' first={{REG_TYPE={!r} VARS_ENTRY={!r} COL_CLASS={!r} ' \
                'COL_FILEUPLOAD_PATH={!r} SENSITIVE_FLAG={!r}}}'.format(
                    head.get('REG_TYPE'), head.get('VARS_ENTRY'), head.get('COL_CLASS'),
                    head.get('COL_FILEUPLOAD_PATH'), head.get('SENSITIVE_FLAG'))
    else:
        first = ''
    return 'vars={} array={} status={} logs={}{}'.format(
        len(result['vars']), len(result['array']),
        ','.join(sorted({repr(r.get('STATUS')) for r in records})) or '-',
        ','.join(result['logs']) or '-', first)


# ======================================================================
# ゴールデン（項番 -> 出力）の入出力
#
#   全件を「項番 \t ハッシュ」で持つと約24MBになるため、
#     [1] 相異なる出力の一覧（id / sha1 / 1行要約）
#     [2] 項番 -> id の連長圧縮（軸順が mixed-radix なので隣接項番は同じidになりやすい）
#   の2部構成にする。中身は完全に固定されるが、ファイルは数十KB〜数百KBに収まる。
# ======================================================================
GOLDEN_HEADER = '# SubValueAutoReg.getCMDBdata exhaustive golden'


def encode_golden(assignments, distinct):
    """
    Args:
        assignments: 項番順(1..N)の出力id リスト
        distinct   : {id: (sha1, summary)}
    Returns:
        str: ゴールデンファイルの内容
    """
    lines = [GOLDEN_HEADER,
             '# axis_order: ' + ','.join(AXIS_ORDER),
             '# cases: {}'.format(len(assignments)),
             '# distinct_outputs: {}'.format(len(distinct)),
             '[distinct]']
    for oid in sorted(distinct):
        sha, summ = distinct[oid]
        lines.append('{}\t{}\t{}'.format(oid, sha, summ))
    lines.append('[assign_rle]')
    # 連長圧縮: "開始項番:件数:id"
    start = 0
    for i in range(1, len(assignments) + 1):
        if i == len(assignments) or assignments[i] != assignments[start]:
            lines.append('{}:{}:{}'.format(start + 1, i - start, assignments[start]))
            start = i
    return '\n'.join(lines) + '\n'


def decode_golden(text):
    """Returns: (assignments, distinct)"""
    distinct = {}
    assignments = []
    section = None
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        if line.startswith('['):
            section = line
            continue
        if section == '[distinct]':
            oid, sha, summ = line.split('\t', 2)
            distinct[int(oid)] = (sha, summ)
        elif section == '[assign_rle]':
            start, length, oid = (int(x) for x in line.split(':'))
            if len(assignments) != start - 1:
                raise ValueError('assign_rle が不連続: {}'.format(line))
            assignments.extend([oid] * length)
    return assignments, distinct


def golden_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'subvalue_autoreg_getCMDBdata_exhaustive_golden.txt')


def run_all(progress=None, observer=None):
    """全組合せを実行して (assignments, distinct, first_of) を返す。

    Args:
        progress: 呼ばれると進捗を受け取る callable(done, total)
        observer: 各件で呼ばれる callable(no, combo, result)。
                  トレーサビリティ集計をゴールデン生成と同じ1パスで行うために使う。
    Returns:
        assignments: 項番順の出力id
        distinct   : {id: (sha1, summary)}
        first_of   : {id: 項番}  その出力が最初に現れた項番
    """
    assignments = []
    by_sha = {}
    distinct = {}
    first_of = {}
    with ExhaustiveRunner() as runner:
        for no, combo in iter_combos():
            result = runner.run(combo)
            sha = digest(result)
            oid = by_sha.get(sha)
            if oid is None:
                oid = len(by_sha) + 1
                by_sha[sha] = oid
                distinct[oid] = (sha, summary(result))
                first_of[oid] = no
            assignments.append(oid)
            if observer is not None:
                observer(no, combo, result)
            if progress is not None and no % 20000 == 0:
                progress(no, None)
    return assignments, distinct, first_of


# ======================================================================
# パターン表のケースID <-> 項番 の対応
#
#   パターン表の各行を「組合せ(と出力)に対する
#   述語」として書き下す。これで
#     - 表の1行が 431,424 件のどれに当たるか（= 項番の集合）
#     - どの行にも当たらない項番が何件あるか（= 表の穴の量）
#   を機械的に出せる。
#
#   pred(combo, result) -> bool     None は「全件モデルでは表現できない行」
# ======================================================================
def _cv_is(*ids):
    ids = set(ids)
    return lambda c, r: c['column_value'] in ids


def _axis_is(key, *ids):
    ids = set(ids)
    return lambda c, r: c[key] in ids


_FILEUPLOAD_VALUES = ('fileupload_exists', 'fileupload_missing', 'ps_ref_fileupload')

# (ケースID, 概要, 述語, 全件モデルで表現できない場合の理由)
CASE_MAP = [
    # --- §1 レコード有効性 ---
    ('1-1', '有効', lambda c, r: c['record_validity'] == 'valid' and c['record_count'] == '1', None),
    ('1-2', '廃止オペ', _axis_is('record_validity', 'disused_ope'), None),
    ('1-3', '廃止ホスト', _axis_is('record_validity', 'disused_host'), None),
    ('1-4', 'ホストID未登録', None,
     'HOST_ID が dict_hostinfo に無い状態は現実装の上流では起こらない(※2-2)ため'
     'パターン表・軸値の双方から削除した。'
     'MSG-10361 の分岐と判定順序は既存 pytest の防御的テストにのみ置く'),

    # --- §2 レコード数 ---
    ('2-1', '0件', _axis_is('record_count', '0'), None),
    ('2-2', '1件', _axis_is('record_count', '1'), None),
    ('2-3', '10件(同一ホスト・複数オペ)', _axis_is('record_count', '10_1host_nope'), None),
    ('2-4', '10件(同一ホスト・同一オペ)', _axis_is('record_count', '10_1host_1ope'), None),
    ('2-5', '10件(複数ホスト・同一オペ)', _axis_is('record_count', '10_nhost_1ope'), None),
    ('2-6', '10件(複数ホスト・複数オペ)', _axis_is('record_count', '10_nhost_nope'), None),

    # --- §3 カラム具体値 ---
    ('3-1', '有(通常文字列)', _cv_is('present'), None),
    ('3-2', 'TPF(id)', _cv_is('tpf'), None),
    ('3-3', 'CPF(id)', _cv_is('cpf'), None),
    ('3-4', '廃止TPF(id)', _cv_is('disused_tpf'), None),
    ('3-5', '廃止CPF(id)', _cv_is('disused_cpf'), None),
    ('3-6', 'FileUploadColumn(ファイル有)', _cv_is('fileupload_exists'), None),
    ('3-7', 'FileUpload(ファイル無)', _cv_is('fileupload_missing'), None),
    ('3-8', '項目なし', _cv_is('item_none'), None),
    ('3-9', 'TPF(名前指定)', _cv_is('name_tpf'), None),
    ('3-10', 'CPF(名前指定)・廃止', _cv_is('name_cpf'), None),
    ('3-11', 'ID指定(CPF/TPF以外)', _cv_is('ref_id'), None),
    ('3-12', 'ID指定(CPF/TPF以外)・廃止', _cv_is('ref_id_disused'), None),
    ('3-13', 'パラメータシート参照', _cv_is('ps_ref'), None),
    ('3-14', 'パラメータシート参照(参照先=ファイルアップロード列)', _cv_is('ps_ref_fileupload'),
     'ファイル有(os.path.exists=True)側のみ。ファイル無側は軸の値になっていない'),
    ('3-15', 'パラメータシート参照(参照先=日時/日付列)', _cv_is('ps_ref_datetime'), None),
    ('3-16', 'パラメータシート参照(パスワード列)', _cv_is('ps_ref_pw'), None),
    ('3-17', 'パラメータシート参照(パスワード列)・廃止', _cv_is('ps_ref_pw_disused'), None),
    ('3-18', 'パラメータシート参照・廃止', _cv_is('ps_ref_disused'), None),
    ('3-19', '項目削除', _cv_is('col_deleted'), None),
    ('3-20', 'レコードが具体値取得結果に無い', _cv_is('row_missing'), None),

    # --- §4 登録方式 ---
    ('4-1', 'Value', _axis_is('reg_type', 'Value'), None),
    ('4-2', 'Key', _axis_is('reg_type', 'Key'), None),
    ('4-3', 'Key(具体値None)',
     lambda c, r: c['reg_type'] == 'Key' and c['column_value'] == 'none', None),
    ('4b-1', 'Key × FileUpload',
     lambda c, r: c['reg_type'] == 'Key' and c['column_value'] in _FILEUPLOAD_VALUES, None),

    # --- §5 バンドル ---
    ('5-1', '無(横メニュー)', _axis_is('bundle', 'no'), None),
    ('5-2', '有(縦メニュー・一致)', _axis_is('bundle', 'yes'),
     '表は「レコード2件 × 設定2件」で対応関係まで見る行。全件モデルは設定1件固定なので、'
     '「縦で突合が成立する形態」までしか当たらない'),
    ('5-3', '有(縦メニュー・不一致)', None,
     'バンドル軸に「不一致」の値が無い(INPUT_ORDER と COLUMN_ASSIGN_SEQ は常に一致させている)'),

    # --- §5b 代入順序 ---
    ('5b-1', '代入順序 無', _axis_is('assign_seq', 'none'), None),
    ('5b-2', '代入順序 有', _axis_is('assign_seq', 'value'), None),

    # --- §6 NULL連携 ---
    ('6-1', '設定TRUE / IF TRUE',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'TRUE'
                   and c['null_if'] == 'TRUE'), None),
    ('6-2', '設定TRUE / IF FALSE',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'TRUE'
                   and c['null_if'] == 'FALSE'), None),
    ('6-3', '設定FALSE / IF TRUE',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'FALSE'
                   and c['null_if'] == 'TRUE'), None),
    ('6-4', '設定FALSE / IF FALSE',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'FALSE'
                   and c['null_if'] == 'FALSE'), None),
    ('6-5', '設定None / IF TRUE',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'None'
                   and c['null_if'] == 'TRUE'), None),
    ('6-6', '設定None / IF FALSE',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'None'
                   and c['null_if'] == 'FALSE'), None),
    ('6-7', 'NULL連携TRUE × メンバ変数(多次元)',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'TRUE'
                   and c['var_type'] == 'M_ARRAY'), None),
    ('6-8', 'NULL連携FALSE × メンバ変数(多次元)',
     lambda c, r: (c['column_value'] == 'none' and c['null_setting'] == 'FALSE'
                   and c['var_type'] == 'M_ARRAY'), None),

    # --- §7 ドライバ / メンバ変数 ---
    ('7-1', 'L / STD', lambda c, r: c['driver'] == 'L' and c['var_type'] == 'STD', None),
    ('7-2', 'P / STD', lambda c, r: c['driver'] == 'P' and c['var_type'] == 'STD', None),
    ('7-3', 'R / STD', lambda c, r: c['driver'] == 'R' and c['var_type'] == 'STD', None),
    ('7-4', 'R / LIST', lambda c, r: c['driver'] == 'R' and c['var_type'] == 'LIST', None),
    ('7-5', 'R / M_ARRAY', lambda c, r: c['driver'] == 'R' and c['var_type'] == 'M_ARRAY', None),

    # --- §8 経路 ---
    ('8-1', 'all', _axis_is('route', 'all'), None),
    ('8-2', 'parameter_sheet', _axis_is('route', 'parameter_sheet'), None),

    # --- §9 戻りレコードの形 ---
    ('9-1', '一般変数レコード(16キー)',
     lambda c, r: any(x.get('STATUS') != 'skip' for x in r['vars']), None),
    ('9-2', '多次元レコード(16キー)', lambda c, r: bool(r['array']), None),
    ('9-3', 'skip レコード(7キー)',
     lambda c, r: any(x.get('STATUS') == 'skip' for x in r['vars']), None),

    # --- §10 具体値の取り違え検知 ---
    ('10-1', '同一ホスト・同一オペ×10 で行ごとの値を保持',
     lambda c, r: (c['record_count'] == '10_1host_1ope'
                   and len({x.get('VARS_ENTRY') for x in r['vars']}) > 1), None),
    ('10-2', '複数ホスト・同一オペ×10 で行ごとの値を保持',
     lambda c, r: (c['record_count'] == '10_nhost_1ope'
                   and len({x.get('VARS_ENTRY') for x in r['vars']}) > 1), None),
    ('10-3', '同一ホスト・複数オペ×10 で行ごとの値を保持',
     lambda c, r: (c['record_count'] == '10_1host_nope'
                   and len({x.get('VARS_ENTRY') for x in r['vars']}) > 1), None),
    ('10-4', '縦メニュー: INPUT_ORDER 1/2/3 × 設定 1/2/3 の総当たり', None,
     '設定を複数件持つ必要がある(全件モデルは設定1件固定)'),
    ('10-5', '2レコードのうち片方だけ具体値取得結果に不在', None,
     'レコードごとに有効性/具体値の有無を変える必要がある(全件モデルは全レコード一律)'),
    ('10-6', '3レコードの COL_ROW_ID(既知の不具合・xfail)', None,
     '全件実行は現実装をゴールデンに固定するので「あるべき姿」の期待値を持てない'),

    # --- §11 複数テーブル ---
    ('11-1', '別メニューの2テーブル', None, '複数テーブルは軸になっていない(全件モデルは1テーブル固定)'),
    ('11-2', '1テーブル目が0件 / 2テーブル目に1件', None, '同上'),
    ('11-3', '2テーブルが同一の紐付メニューを参照', None, '同上'),

    # --- §12 性能 ---
    ('12-1', '2000レコード × 設定1件', None, '性能軸(2000件)は機能ケースの直積に入れていない'),
    ('12-2', '2000レコード × 設定25件', None, '同上(設定件数も性能専用軸)'),
    ('12-3', '50レコード × 設定4件 の辞書引き線形性', None, '同上'),
]


class CoverageTracer:
    """run_all() の observer として渡し、ケースIDごとの該当項番を数える。

        tracer = CoverageTracer()
        assignments, distinct, first_of = run_all(observer=tracer)
        tracer.hits          # {ケースID: (件数, 最小項番, 最大項番)}
        tracer.uncased       # どのケースIDにも当たらなかった件数
    """

    #: uncased の実例として保持する項番の上限
    SAMPLE_LIMIT = 20

    def __init__(self):
        self._preds = [(cid, pred) for cid, _n, pred, _w in CASE_MAP if pred is not None]
        self._hits = {cid: [0, None, None] for cid, _ in self._preds}
        self.uncased = 0
        self.uncased_samples = []
        self.total = 0

    def __call__(self, no, combo, result):
        self.total = no
        matched = False
        for cid, pred in self._preds:
            if pred(combo, result):
                matched = True
                h = self._hits[cid]
                h[0] += 1
                if h[1] is None:
                    h[1] = no
                h[2] = no
        if not matched:
            self.uncased += 1
            if len(self.uncased_samples) < self.SAMPLE_LIMIT:
                self.uncased_samples.append(no)

    @property
    def hits(self):
        return {k: tuple(v) for k, v in self._hits.items()}


def trace_coverage(progress=None):
    """全件を1パス実行し、ゴールデン素材とトレーサビリティ集計を同時に得る。

    Returns:
        (assignments, distinct, first_of, tracer)
    """
    tracer = CoverageTracer()
    assignments, distinct, first_of = run_all(progress=progress, observer=tracer)
    return assignments, distinct, first_of, tracer


def oneway_combos():
    """既存 pytest の戦略に対応する組合せ集合（ベースライン固定＋1軸だけ動かす）。

    レビュー指摘「判定順序が変わると網羅の主張が崩れる」を数値化するために使う。
    この集合が到達できる出力の種類数と、全件が到達する 1,224 通りを比べる。
    """
    values = _feasible_values()
    checks = [fn for _, fn in axes_mod.CONSTRAINTS]
    base = axes_mod.baseline_combo()
    combos = set()
    for key in AXIS_ORDER:
        for value in values[key]:
            candidate = dict(base)
            candidate[key] = value
            if all(fn(candidate) for fn in checks):
                combos.add(tuple(candidate[k] for k in AXIS_ORDER))
    return combos


def oneway_reach(assignments):
    """1軸戦略が到達する出力id集合と、その項番を返す。

    Returns:
        (項番のソート済みリスト, 到達した出力id集合)
    """
    wanted = oneway_combos()
    numbers = []
    reached = set()
    for no, combo in iter_combos():
        if tuple(combo[k] for k in AXIS_ORDER) in wanted:
            numbers.append(no)
            reached.add(assignments[no - 1])
    return numbers, reached


def combos_at(numbers):
    """指定した項番の組合せを1パスで引く。Returns: {項番: combo}"""
    want = set(numbers)
    found = {}
    if not want:
        return found
    for no, combo in iter_combos():
        if no in want:
            found[no] = combo
            if len(found) == len(want):
                break
    return found


# ======================================================================
# 成果物の出力
# ======================================================================
def index_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'subvalue_autoreg_getCMDBdata_exhaustive_index.tsv')


def traceability_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'SubValueAutoReg_getCMDBdata_exhaustive_traceability.md')


def lookup(no):
    """項番から「どういうケースか」を引く。

    Returns:
        dict: axes(軸値), case_ids(該当するパターン表の行), label
        None: 項番が範囲外
    """
    for n, combo in iter_combos():
        if n != no:
            continue
        with ExhaustiveRunner() as runner:
            result = runner.run(combo)
        return {
            'no': no,
            'axes': dict(combo),
            'label': combo_label(combo),
            'case_ids': [cid for cid, _n, pred, _w in CASE_MAP
                         if pred is not None and pred(combo, result)],
            'summary': summary(result),
        }
    return None


def write_index(assignments, path=None):
    """項番 -> 軸値 -> 出力id の全件一覧(TSV)。

    431,424行 = 約39MB になるので**既定では作らない**（リポジトリに置かない）。
    項番は AXIS_ORDER と各軸の値定義だけで決まるので、必要になったら
    `--index` で作り直せる。1件だけ引きたいときは lookup() / `--lookup N`。
    """
    path = path or index_path()
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('# 項番\t' + '\t'.join(AXIS_ORDER) + '\t出力id\n')
        for no, combo in iter_combos():
            fh.write('{}\t{}\t{}\n'.format(
                no, '\t'.join(combo[k] for k in AXIS_ORDER), assignments[no - 1]))
    return path


def _axis_table_rows():
    """項番の定義（mixed-radix）を説明するための軸一覧。"""
    values = _feasible_values()
    rows = []
    for key in AXIS_ORDER:
        axis = axes_mod.AXIS_BY_KEY[key]
        rows.append((key, axis['name'], len(values[key]), values[key]))
    return rows


def render_traceability_markdown(assignments, distinct, first_of, tracer):
    """ケースID <-> 項番 の対応表を markdown で組み立てる。"""
    total = len(assignments)
    hits = tracer.hits
    reps = {}
    for cid, (cnt, lo, _hi) in hits.items():
        if cnt:
            reps[cid] = lo
    combos = combos_at(reps.values())
    sample_combos = combos_at(tracer.uncased_samples)

    out = []
    a = out.append
    a('# SubValueAutoReg.getCMDBdata 全件実行 トレーサビリティ')
    a('')
    a('自動生成物。`python3 -m tests...subvalue_autoreg_exhaustive --all` で再生成する。')
    a('')
    a('- 実現可能な組合せ: **{:,} 件**'.format(total))
    a('- 相異なる出力: **{:,} 通り**'.format(len(distinct)))
    a('- パターン表のどの行にも当たらない項番: **{:,} 件**'.format(tracer.uncased))
    a('')

    a('## 1. 項番の定義')
    a('')
    a('軸を下表の順に並べた mixed-radix（右端が最も速く回る）で全直積を列挙し、')
    a('軸間制約を満たすものだけに 1 から連番を振る。')
    a('**軸の順序・軸値の並びを変えると項番は総入れ替えになる**ので、')
    a('`AXIS_ORDER` と各軸の値定義は不変とみなして扱う。')
    a('')
    a('| # | 軸キー | 軸名 | 値数 | 値 |')
    a('|---|---|---|---:|---|')
    for i, (key, label, n, vals) in enumerate(_axis_table_rows(), 1):
        a('| {} | `{}` | {} | {} | {} |'.format(
            i, key, label, n, ', '.join('`{}`'.format(v) for v in vals)))
    a('')

    a('## 2. パターン表のケースID -> 項番')
    a('')
    a('| ケースID | 概要 | 該当件数 | 代表項番 | 代表項番の軸値 |')
    a('|---|---|---:|---:|---|')
    for cid, name, pred, why in CASE_MAP:
        if pred is None:
            a('| {} | {} | — | — | 全件モデルでは表現不可（§3参照） |'.format(cid, name))
            continue
        cnt, lo, _hi = hits[cid]
        if not cnt:
            a('| {} | {} | **0** | — | **述語に一致する組合せが無い（要確認）** |'.format(cid, name))
            continue
        a('| {} | {} | {:,} | {} | {} |'.format(
            cid, name, cnt, lo, combo_label(combos[lo])))
    a('')

    not_repr = [(cid, name, why) for cid, name, pred, why in CASE_MAP if pred is None]
    partial = [(cid, name, why) for cid, name, pred, why in CASE_MAP
               if pred is not None and why]
    a('## 3. 全件モデルで表現できない/部分的にしか当たらない行')
    a('')
    a('| ケースID | 概要 | 状態 | 理由 |')
    a('|---|---|---|---|')
    for cid, name, why in not_repr:
        a('| {} | {} | 表現不可 | {} |'.format(cid, name, why))
    for cid, name, why in partial:
        a('| {} | {} | 部分的 | {} |'.format(cid, name, why))
    a('')
    a('※ここに挙げた行は `test_SubValueAutoReg_getCMDBdata.py`（手書き期待値・122項目）'
      '側でカバーする。全件実行と既存 pytest は互いの穴を埋める2枚構成。')
    a('')

    a('## 4. どのケースIDにも当たらない項番')
    a('')
    if not tracer.uncased:
        a('**0件**。実現可能な {:,} 件すべてがパターン表のいずれかの行に該当する。'.format(total))
        a('')
        a('ただしこれは表が強いという意味ではない。パターン表の各行は基本的に')
        a('「ある1軸がある値である」という主張なので、行の和集合は当然に全件を覆う。')
        a('表が言えていないのは**軸の組合せ**であり、その差は §7 で数える。')
    else:
        a('{:,} 件（全体の {:.1f}%）。パターン表が明示していない組合せ領域の量。'.format(
            tracer.uncased, 100.0 * tracer.uncased / total))
        a('')
        a('| 項番 | 軸値 |')
        a('|---:|---|')
        for no in tracer.uncased_samples:
            a('| {} | {} |'.format(no, combo_label(sample_combos[no])))
    a('')

    a('## 5. 相異なる出力の一覧（先頭50件）')
    a('')
    a('全 {:,} 通りは `{}` の `[distinct]` 節を参照。'.format(
        len(distinct), os.path.basename(golden_path())))
    a('')
    a('| 出力id | 初出項番 | 要約 |')
    a('|---:|---:|---|')
    for oid in sorted(distinct)[:50]:
        a('| {} | {} | {} |'.format(oid, first_of[oid], distinct[oid][1]))
    a('')
    a('## 6. 項番から中身を引く')
    a('')
    a('項番は AXIS_ORDER と各軸の値定義だけで決まるので、{:,}行の一覧を'.format(total))
    a('リポジトリに置く必要は無い（TSVにすると約39MB、markdownの表なら数十MBで閲覧不能）。')
    a('1件だけ引きたいときは:')
    a('')
    a('```')
    a('python3 -m tests.ansible_driver_tests.ansible_driver.classes'
      '.subvalue_autoreg_exhaustive --lookup 8161')
    a('```')
    a('')
    a('全件のTSVが必要なときは `--all --index` を付ける（`{}` に出る）。'.format(
        os.path.basename(index_path())))
    a('')

    numbers, reached = oneway_reach(assignments)
    a('## 7. 1軸戦略との差（なぜ全件やるのか）')
    a('')
    a('既存 pytest と同じ戦略、つまり「ベースライン値で固定して1軸だけ動かす」で')
    a('到達できる組合せは **{:,} 件**（全 {:,} 件の {:.3f}%）。'.format(
        len(numbers), total, 100.0 * len(numbers) / total))
    a('その {:,} 件が到達する出力は **{:,} 通り**で、'.format(len(numbers), len(reached)))
    a('全件が到達する {:,} 通りのうち **{:.1f}%** にとどまる。'.format(
        len(distinct), 100.0 * len(reached) / len(distinct)))
    a('')
    a('残る **{:,} 通り**の出力は、2軸以上を同時に動かさないと現れない。'.format(
        len(distinct) - len(reached)))
    a('しかも1軸戦略の「ベースライン値」は現実装の判定順序を読んで決めた値なので、')
    a('判定順序が変わればこの {:.1f}% という数字自体が変わる。'.format(
        100.0 * len(reached) / len(distinct)))
    a('全件実行はベースライン値を一切使わないので、この依存が無い。')
    return '\n'.join(out) + '\n'


def regenerate(progress=None, write_index_file=False):
    """ゴールデン・トレーサビリティ・全件一覧をまとめて作り直す。"""
    assignments, distinct, first_of, tracer = trace_coverage(progress=progress)

    with open(golden_path(), 'w', encoding='utf-8') as fh:
        fh.write(encode_golden(assignments, distinct))
    with open(traceability_path(), 'w', encoding='utf-8') as fh:
        fh.write(render_traceability_markdown(assignments, distinct, first_of, tracer))
    if write_index_file:
        write_index(assignments)
    return assignments, distinct, first_of, tracer


# ======================================================================
# 保守用エントリポイント
#
#   相対 import があるのでスクリプト直起動ではなく -m で呼ぶ。
#   ita_by_ansible_legacy_vars_listup をカレントにして:
#     python3 -m tests...subvalue_autoreg_exhaustive --count       件数だけ数える
#     python3 -m tests...subvalue_autoreg_exhaustive --all         ゴールデン+表を作り直す
#     python3 -m tests...subvalue_autoreg_exhaustive --all --index 全件一覧TSVも作る(約39MB)
#     python3 -m tests...subvalue_autoreg_exhaustive --lookup 8161 項番1件の中身を見る
#   ("tests..." は tests.ansible_driver_tests.ansible_driver.classes の略)
# ======================================================================
def _cli(argv):
    import time

    def progress(done, _total):
        sys.stderr.write('\r  {:,} / {:,}'.format(done, TOTAL_CASES))
        sys.stderr.flush()

    if '--count' in argv:
        print('cases: {:,}'.format(total_cases()))
        return 0

    if '--lookup' in argv:
        no = int(argv[argv.index('--lookup') + 1])
        found = lookup(no)
        if found is None:
            sys.stderr.write('項番 {} は範囲外（1..{:,}）\n'.format(no, total_cases()))
            return 1
        print('項番    : {}'.format(found['no']))
        print('ラベル  : {}'.format(found['label']))
        for key in AXIS_ORDER:
            print('  {:<16}: {}'.format(key, found['axes'][key]))
        print('ケースID: {}'.format(', '.join(found['case_ids']) or '-'))
        print('出力    : {}'.format(found['summary']))
        return 0

    if '--all' in argv:
        started = time.time()
        sys.stderr.write('全件実行中...\n')
        _asg, distinct, _first, tracer = regenerate(
            progress=progress, write_index_file='--index' in argv)
        sys.stderr.write('\n')
        elapsed = time.time() - started
        print('cases           : {:,}'.format(tracer.total))
        print('distinct outputs: {:,}'.format(len(distinct)))
        print('uncased         : {:,}'.format(tracer.uncased))
        print('elapsed         : {:.1f}s ({:.0f} us/case)'.format(
            elapsed, elapsed / max(tracer.total, 1) * 1e6))
        print('golden          : ' + golden_path())
        print('traceability    : ' + traceability_path())
        return 0

    sys.stderr.write(__doc__ or '')
    sys.stderr.write('\nusage: --count | --all [--index] | --lookup <項番>\n')
    return 1


TOTAL_CASES = 431424  # --all の進捗表示用（実測値。--count で検算できる）

if __name__ == '__main__':
    sys.exit(_cli(sys.argv[1:]))
