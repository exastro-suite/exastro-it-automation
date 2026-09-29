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
SubValueAutoReg.getCMDBdata パターン表の軸定義（機械可読版）

getCMDBdata のパターン表に散在している以下3つを、
1箇所のデータとして起こしたもの。

  1. AXES        : 軸とその値（= パターン表の列）
  2. CONSTRAINTS : 現実装ではあり得ない組合せ（= 脚注 ※1〜※6-2）
  3. STAGES / relevant_axes()
                 : 判定順序と「その軸より後の段階でしか効かない軸は
                   ベースライン値で固定してよい」という独立性の主張
                   （= 各節の「他の軸: いずれの値でも同結果」）

用途:
  - 直積 / 実現可能な組合せ / **同値類**（=本当に必要なケース数）を数える
  - pairwise 生成器(PICT / allpairspy)への入力にする
  - 「網羅の水準」をレビューで議論できる形にする

    python3 -m tests.ansible_driver_tests.ansible_driver.classes.subvalue_autoreg_axes

注意: ここは「表の写し」であって実装の写しではない。
      実装を変えたらまずこのファイルを更新し、数値の変化を見る。
"""


# ======================================================================
# 判定順序（どの軸がどの段階で効くか）
#
# getCMDBdata は逐次フィルタなので、あるケースの期待値は
# 「最初に結果を確定させた段階」で決まる。後段の軸は結果に影響しない。
# これが「ベースライン値で固定してよい」根拠であり、
# 直積を取らなくてよい根拠でもある。
# ======================================================================
STAGES = {
    0: {'name': 'SELECT文組立（レコード取得前）',
        'impl': 'SubValueAutoReg.py:880-886',
        'axes': ['route']},
    1: {'name': 'レコード単位のスキップ（件数0 / オペ空 / 紐付件数0 / ホストID空）',
        'impl': 'SubValueAutoReg.py:892-929',
        'axes': ['record_count', 'record_validity']},
    2: {'name': '縦/横分岐 → 項目なしskip・項目削除continue・TPF/CPFラップと廃止continue',
        'impl': 'SubValueAutoReg.py:985-1047',
        'axes': ['bundle', 'column_value', 'locale']},
    3: {'name': 'FileUpload のパス生成・存在チェック（Value かつ COLUMN_CLASS 9/20 のみ）',
        'impl': 'SubValueAutoReg.py:1052-1066',
        'axes': ['column_value', 'reg_type']},
    4: {'name': 'Value: NULL連携判定(MSG-10375) / Key: 具体値None判定(MSG-10377)',
        'impl': 'SubValueAutoReg.py:1185-1247',
        'axes': ['column_value', 'reg_type', 'null_setting', 'null_if']},
    5: {'name': '変数タイプ振り分け + 重複チェック + レコード生成',
        'impl': 'SubValueAutoReg.py:1301-1430',
        'axes': ['var_type', 'assign_seq', 'record_count']},
}


def _v(vid, label, **kw):
    """軸の1値。

    feasible=False : 現実装では発生し得ない値（脚注に根拠あり）
    xfail=True     : 既知不具合。あるべき姿を期待値にして xfail 中
    perf=True      : 性能カナリア専用の値（機能ケースの直積には入れない）
    """
    value = {'id': vid, 'label': label, 'feasible': True, 'xfail': False, 'perf': False}
    value.update(kw)
    return value


# ======================================================================
# 1. 軸と値
#    baseline: 表に出てこない軸の固定値（make_col_data / make_cmdb_row /
#              make_subvalue_autoreg の既定値と一致させる）
# ======================================================================
AXES = [
    {
        'key': 'route', 'name': '経路', 'stage': 0, 'baseline': 'all',
        # 段階①より前で完結するため他の全軸と独立（§8）。
        # 直積に掛けず、独立に |values| ケースで足りる。
        'separable': True,
        'input': 'getCMDBdata 第4引数 reg_operation_id',
        'values': [
            _v('all', 'all（全件）: reg_operation_id=None'),
            _v('parameter_sheet', 'parameter_sheet（オペ指定）: reg_operation_id=値'),
        ],
    },
    {
        'key': 'bundle', 'name': 'バンドル（パラメータシート形態）', 'stage': 2, 'baseline': 'no',
        'input': 'make_cmdb_row(input_order=) / make_col_data(COLUMN_ASSIGN_SEQ=)',
        'note': '縦分岐・横分岐で値処理が重複実装されているため、値処理系は両方必要',
        'values': [
            _v('no', '無（横メニュー）: INPUT_ORDER="" / COLUMN_ASSIGN_SEQ=None'),
            _v('yes', '有（縦メニュー・一致）: INPUT_ORDER="1" / COLUMN_ASSIGN_SEQ="1"'),
        ],
    },
    {
        'key': 'hostgroup', 'name': 'ホストグループ', 'stage': 1, 'baseline': 'no',
        # getCMDBdata から見ると HOST_ID の多重度としてしか現れない（§軸表）。
        # = record_count の「複数ホスト」値に吸収される。独立の軸ではない。
        'subsumed_by': 'record_count',
        'input': 'make_cmdb_row(host_id=)',
        'values': [
            _v('no', '無（HOST_ID 1種）'),
            _v('yes', '有（HOST_ID 複数 → record_count の複数ホスト値と同一入力）'),
        ],
    },
    {
        'key': 'record_count', 'name': 'レコード数', 'stage': 1, 'baseline': '1',
        'input': 'mock_ws_db.cmdb_rows[table]',
        'values': [
            _v('0', '0件 → MSG-10368'),
            _v('1', '1件'),
            _v('10_1host_nope', '10件（同一ホスト・複数オペ）'),
            _v('10_1host_1ope', '10件（同一ホスト・同一オペ）→ 重複排除 True×1/False×9'),
            _v('10_nhost_1ope', '10件（複数ホスト・同一オペ）'),
            _v('10_nhost_nope', '10件（複数ホスト・複数オペ）'),
            _v('2000', '2000件（性能カナリア）', perf=True),
        ],
    },
    {
        'key': 'setting_count', 'name': '代入値自動登録設定の件数', 'stage': 5, 'baseline': '1',
        # 件数は「レコード×設定の全組合せが混線しないか」と線形性のための軸。
        # 機能分岐は増えないので直積には入れない（§12）。
        'perf_only': True,
        'input': 'build_inputs(col_data_list=[...])',
        'values': [
            _v('1', '1件'),
            _v('2', '2件', perf=True),
            _v('4', '4件', perf=True),
            _v('25', '25件', perf=True),
        ],
    },
    {
        'key': 'record_validity', 'name': 'レコード有効性', 'stage': 1, 'baseline': 'valid',
        'input': 'make_cmdb_row(operation_id= / host_id= / host_cnt=)',
        # 「ホストID未登録（HOST_ID=""）→ MSG-10361」は ※2-2 のとおり作成し得ない
        # （入力経路が REQUIRED_ITEM=1 で弾き、DB直接操作でも件数0が先に立って
        # MSG-10359 になる）ため、パターン表から削除＝**軸値にも持たない**。
        # MSG-10361 の分岐と判定順序は test_SubValueAutoReg_getCMDBdata.py の
        # 防御的テスト（§1-4）だけで固定する。
        'note': 'ホストID未登録は ※2-2 により軸値から除外（防御的テストは手書き側 §1-4 に残す）',
        'values': [
            _v('valid', '有効（OPERATION_ID有 / HOST_ID有 / 紐付件数=1）'),
            _v('disused_ope', '廃止オペ（OPERATION_ID=""）→ MSG-10360'),
            _v('disused_host', '廃止ホスト（紐付件数=0）→ MSG-10359'),
        ],
    },
    {
        'key': 'column_value', 'name': 'カラム具体値', 'stage': 2, 'baseline': 'present',
        'input': 'param_sheets の値 + make_col_data(COLUMN_CLASS / REF_* / COL_GROUP_ID / VALUE_SENSITIVE_FLAG)',
        # GBL系（GBL(id) / GBL_S(id) / 廃止GBL(id) / 廃止GBL_S(id)）は ※2-1 のとおり
        # 「プルダウン選択」の選択項目にグローバル変数名が出ない＝**設定自体が作れない**ので、
        # パターン表から削除＝軸値にも持たない（単体ケースも持たない）。
        # 「ID変換失敗メッセージがそのまま具体値として登録される」挙動は
        # ref_id_disused（§3-12）/ ps_ref_disused（§3-18）が
        # 同じ分岐を通るのでカバーは維持される（※5）。
        # 「廃止」が別の同値類になるのは、廃止によって **getCMDBdata への入力が変わる** 値だけ。
        #   ・TPF/CPF(id)・ID指定・パラメータシート参照 → 'ID変換失敗…' 文字列に変わる → 軸値にする
        #   ・パラメータシート参照(パスワード列)        → None に変わる（※4-2）    → 軸値にする
        #   ・TPF/CPF(名前指定)                        → 入力が変わらない（※4）    → 軸値にしない
        #   ・パラメータシート参照(日時/日付列・ファイルアップロード列)
        #        → COLUMN_CLASS='21' の 'ID変換失敗…' になり §3-18 と**完全に同一入力**
        #          （参照先の型は具体値からは見えない。これが #3066/#3068 の原因でもある）
        #        → 軸値にしない
        'note': 'GBL系4値（※2-1）・COLUMN_CLASS=20（作成不可・9 と同一分岐）・'
                'ID指定(TPFテーブル・対象外列)（※3 作成不可）は軸値から除外。'
                '名前指定の廃止（※4）と パラメータシート参照(日時/日付列・ファイルアップロード列)の廃止は'
                '有効時／§3-18 と入力が完全一致するので軸値にしない。'
                '変換失敗値の登録挙動は §3-12 / §3-18 が担う',
        'values': [
            _v('present', '3-1 有（通常文字列）'),
            _v('none', 'カラム具体値:無（value=None）→ 段階④のNULL連携へ（§6）'),
            _v('tpf', '3-2 TPF(id) → "\'{{ X }}\'" にラップ'),
            _v('cpf', '3-3 CPF(id) → "\'{{ X }}\'" にラップ'),
            _v('disused_tpf', '3-4 廃止TPF(id) → 未登録（continue・ログ無し）'),
            _v('disused_cpf', '3-5 廃止CPF(id) → 未登録（continue・ログ無し）'),
            _v('fileupload_exists', '3-6 FileUploadColumn（COLUMN_CLASS=9・ファイル有）'),
            _v('fileupload_missing', '3-7 FileUpload（ファイル無）→ 未登録 + MSG-10166'),
            # FileUploadEncryptColumn（COLUMN_CLASS=20）は MENU_CREATE_TARGET_FLAG=0
            # （workspace_master.sql:1477）で作成機能のカラムクラス候補に出ない＝設定を作れず、
            # かつ getCMDBdata の判定は SubValueAutoReg.py:1052 で 9 と同一分岐なので
            # 値としても持たない（GBL系と同じ扱い）。
            _v('item_none', '3-8 項目なし（COL_GROUP_ID=None）→ STATUS="skip"'),
            _v('name_tpf', '3-9 TPF（名前指定）→ 二重ラップされない'),
            _v('name_cpf', '3-10 CPF（名前指定・廃止）→ 廃止でも登録される（※4 原理的に区別不能）'),
            _v('ref_id', '3-11 ID指定（CPF/TPF以外・COLUMN_CLASS=7）→ ラップ無'),
            # ID指定(TPFテーブル・対象外列)は ※3 のとおり作成不可なので軸値に持たない
            # （単体ケースも持たない）。
            # 「プルダウン選択」の参照先候補は T_MENU_OTHER_LINK（メニュー 50111・
            # 追加/更新/廃止すべて不可の自動生成メニュー）に登録された組だけで、
            # T_ANSC_TEMPLATE_FILE 側は ANS_TEMPLATE_VARS_NAME しか無い＝
            # 「REF_TABLE_NAME は一致するが REF_COL_NAME が一致しない」設定を作れない。
            _v('ref_id_disused', '3-12 ID指定・廃止 → そのまま登録（※5）'),
            _v('ps_ref', '3-13 パラメータシート参照（COLUMN_CLASS=21）'),
            _v('ps_ref_fileupload', '3-14 パラメータシート参照（参照先=ファイルアップロード列）',
               xfail=True, reason='※6-1 既知不具合 #3066。あるべき姿を期待値にして xfail'),
            _v('ps_ref_pw', '3-16 パラメータシート参照（パスワード列・COLUMN_CLASS=26）'),
            # パスワード列だけは廃止で **具体値が None** になる（他のID系は 'ID変換失敗' 文字列）。
            # SubValueAutoReg.py:2004-2008 が JsonPasswordIDColumn を convert_value_output に
            # 通さず get_values_by_key で引き直し、その元表が DISUSE_FLAG='0' で絞られているため。
            # → 段階④のNULL連携へ落ちる。SENSITIVE ON のまま＝軸値 none とは別入力（※4-2）。
            _v('ps_ref_pw_disused',
               '3-17 パラメータシート参照（パスワード列）・廃止 → 具体値Noneで段階④へ（※4-2）'),
            _v('ps_ref_disused', '3-18 パラメータシート参照・廃止 → そのまま登録（※5）'),
            # ※6-2 / #3066 とは扱いが違う。#3068 は「修正せず現状の動作のまま」と決めたので
            # xfail ではなく**通常のケース**として現状挙動（COLUMN_CLASS='21' の通常値として
            # 登録される）を期待値に固定する。
            _v('ps_ref_datetime', '3-15 パラメータシート参照（参照先=日時/日付列）→ 通常値として登録（※6-2）'),
            _v('col_deleted', '3-19 項目削除（具体値に当該カラムのキーが無い）→ 未登録'),
            # ※7 静的な設定では作れない値。CMDB行の一覧(createQuerySelectCMDB → SubValueAutoReg.py:474-475)と
            # 具体値(rest_filter → :1964-1969)は**同じメニューの TABLE_NAME / VIEW_NAME**を
            # どちらも DISUSE_FLAG='0' で読み、VIEW は LEFT JOIN V_COMN_OPERATION だけで行を落とさない。
            # → 同一時点なら行集合は必ず一致する。ただし①は読んだ時点でコミットされる(:880-886)ので、
            #   ②を読むまでの間にその行が廃止されると起こる（②はメニュー単位でキャッシュされ :961-969、
            #   ホストグループ利用シートでは ita_by_hostgroup_split が sv_ テーブルの行を
            #   DISUSE_FLAG='1' にして作り直す split_function.py:601）。
            # 実行中に起こり得るレースのガードなので、※2-1/※3 のような「作れない値」とは違い軸値に残す。
            _v('row_missing', '3-20 レコードが具体値取得結果に無い → 未登録（※7 レース時のみ発生）'),
        ],
    },
    {
        'key': 'reg_type', 'name': '登録方式', 'stage': 3, 'baseline': 'Value',
        'input': 'make_col_data(COL_TYPE=)',
        'values': [
            _v('Value', 'Value（COL_TYPE="1"）'),
            _v('Key', 'Key（COL_TYPE="2"）: VARS_ENTRY=カラム名。段階③④が別経路'),
        ],
    },
    {
        'key': 'assign_seq', 'name': '代入順序（設定側 ASSIGN_SEQ）', 'stage': 5, 'baseline': 'none',
        'input': 'make_col_data(ASSIGN_SEQ=)',
        'note': '重複チェックキーの末尾要素。COLUMN_ASSIGN_SEQ（バンドル軸）とは別物',
        'values': [
            _v('none', '無（ASSIGN_SEQ=None）'),
            _v('value', '有（ASSIGN_SEQ="3"）'),
        ],
    },
    {
        'key': 'null_setting', 'name': 'NULL連携（設定）', 'stage': 4, 'baseline': 'None',
        'input': 'make_col_data(NULL_DATA_HANDLING_FLG=)',
        'values': [
            _v('TRUE', 'TRUE("1") → NULLでも登録'),
            _v('FALSE', 'FALSE("0") → 未登録 + MSG-10375'),
            _v('None', 'None → IF情報側に委譲'),
        ],
    },
    {
        'key': 'null_if', 'name': 'NULL連携（IF情報）', 'stage': 4, 'baseline': 'TRUE',
        'input': 'getCMDBdata 第6引数 g_null_data_handling_def',
        'note': 'getNullDataHandlingID は設定が "1"/"0" ならその場で確定するため、'
                'IF情報が効くのは設定=None のときだけ',
        'values': [
            _v('TRUE', 'TRUE("1")'),
            _v('FALSE', 'FALSE("0")'),
        ],
    },
    {
        'key': 'driver', 'name': 'ドライバ', 'stage': 5, 'baseline': 'R',
        'input': 'make_subvalue_autoreg(driver_id=)',
        'note': 'getCMDBdata は driver_id を参照しない。差は var_type の取り得る値としてのみ現れる。'
                'L/P のケースは上流仕様（L/P は STD 固定）のリグレッションガード',
        'values': [
            _v('L', 'Ansible Legacy'),
            _v('P', 'Ansible Pioneer'),
            _v('R', 'Ansible LegacyRole'),
        ],
    },
    {
        'key': 'var_type', 'name': '変数タイプ / メンバ変数', 'stage': 5, 'baseline': 'STD',
        'input': 'make_col_data(VAL_VAR_TYPE= / COL_SEQ_COMBINATION_ID=)',
        'note': 'パターン表の「メンバ変数 有/無」は var_type == M_ARRAY と同義',
        'values': [
            _v('STD', '一般変数("1") / メンバ変数:無'),
            _v('LIST', '複数具体値("2") / メンバ変数:無'),
            _v('M_ARRAY', '多次元("3") + COL_SEQ_COMBINATION_ID / メンバ変数:有 → array 側に入る'),
        ],
    },
    {
        'key': 'locale', 'name': 'ロケール', 'stage': 2, 'baseline': 'ja',
        'input': "conftest mock_g の g.LANGUAGE",
        'note': "廃止TPF/CPF の判定文字列（'ID変換失敗' / 'Failed to exchange ID'）と "
                "Key登録時のカラム名（COLUMN_NAME_JA / _EN）に効く",
        'values': [
            _v('ja', 'ja'),
            _v('en', 'en'),
        ],
    },
]

AXIS_BY_KEY = {a['key']: a for a in AXES}


# ======================================================================
# 2. 制約（現実装ではあり得ない組合せ）
#    脚注 ※1〜※6-2 のうち「値そのもの」ではなく「組合せ」の禁止をここに書く。
#    値単体の不可能性は _v(feasible=False) 側。
# ======================================================================
def _c_driver_var_type(combo):
    """L/P は valAssColumnValidate の else 節で一般変数に固定される（※ドライバ軸の意味）。

    複数具体値(LIST)・多次元(M_ARRAY) は R でしか発生しない。
    → driver × var_type の 9通りのうち有効なのは 5通り（= §7-1〜7-5）。
    """
    return not (combo['driver'] in ('L', 'P') and combo['var_type'] != 'STD')


def _c_hostgroup_record_count(combo):
    """ホストグループ有 = レコードのHOST_IDが複数、と同一入力。

    record_count が単一ホストの値のときに hostgroup='yes' は表現できない。
    """
    if combo['hostgroup'] != 'yes':
        return True
    return combo['record_count'] in ('10_nhost_1ope', '10_nhost_nope')


def _c_zero_record(combo):
    """0件のときはレコード属性を持てない。"""
    if combo['record_count'] != '0':
        return True
    return combo['record_validity'] == 'valid' and combo['hostgroup'] == 'no'


def _c_dedup_needs_same_key(combo):
    """10件（同一ホスト・同一オペ）の期待値 True×1/False×9 は重複チェックキーが
    全件一致することに依存する。M_ARRAY はキーにメンバ変数IDを含む別実装のため、
    この組合せは §2-4 の期待値では表現できない（→ 別ケース扱い）。
    """
    if combo['record_count'] != '10_1host_1ope':
        return True
    return combo['var_type'] != 'M_ARRAY'


CONSTRAINTS = [
    ('driver × var_type（L/P は STD 固定）', _c_driver_var_type),
    ('hostgroup × record_count（HGは複数ホストとして現れる）', _c_hostgroup_record_count),
    ('record_count=0 のときレコード属性を持てない', _c_zero_record),
    ('重複排除ケースは M_ARRAY と両立しない', _c_dedup_needs_same_key),
]


def is_feasible(combo):
    """現実装で発生し得る組合せか。"""
    for key, vid in combo.items():
        value = next(v for v in AXIS_BY_KEY[key]['values'] if v['id'] == vid)
        if not value['feasible']:
            return False
    return all(fn(combo) for _, fn in CONSTRAINTS)


# ======================================================================
# 3. 独立性（= どの軸が「いずれの値でも同結果」になるか）
#
#    パターン表の各節にある「他の軸」の注記を関数にしたもの。
#    ここが正しければ、直積ではなく **同値類の数** が必要ケース数になる。
#    ここが間違っていれば pairwise 実行で落ちて分かる（後述）。
# ======================================================================
_STAGE2_TERMINAL = {
    # 段階②で結果が確定する具体値（③以降に到達しない）
    'disused_tpf', 'disused_cpf',   # 廃止 → continue
    'item_none',                    # 項目なし → STATUS='skip' で append して continue
    'col_deleted', 'row_missing',   # 項目削除 / レコード不在 → continue
}
_FILEUPLOAD = {'fileupload_exists', 'fileupload_missing', 'ps_ref_fileupload'}


def relevant_axes(combo):
    """この組合せで期待値に影響する軸を返す。

    「最初に結果を確定させた段階」までの軸だけが効く。
    それ以降の軸はベースライン値に丸めても期待値が変わらない。
    """
    rel = {'route'}  # 段階0。SQLの形にのみ効く（§8）

    # --- 段階① ---
    rel |= {'record_count', 'record_validity'}
    if combo['record_count'] == '0':
        return rel
    if combo['record_validity'] != 'valid':
        return rel
    rel.add('hostgroup')

    # --- 段階② ---
    rel |= {'bundle', 'column_value'}
    if combo['column_value'] in ('disused_tpf', 'disused_cpf'):
        rel.add('locale')          # 判定文字列がロケール依存
    if combo['column_value'] in _STAGE2_TERMINAL:
        return rel

    # --- 段階③ ---
    if combo['column_value'] in _FILEUPLOAD:
        rel.add('reg_type')        # Value かつ 9/20 のときだけパス生成（§4b で反転）
        if combo['reg_type'] == 'Value' and combo['column_value'] == 'fileupload_missing':
            return rel             # MSG-10166 で未登録が確定

    # --- 段階④ ---
    rel.add('reg_type')
    if combo['column_value'] == 'none':
        if combo['reg_type'] == 'Key':
            return rel             # MSG-10377。NULL連携は見ない（§4-3）
        rel.add('null_setting')
        if combo['null_setting'] == 'None':
            rel.add('null_if')     # 設定=None のときだけ IF が効く
        if combo['null_setting'] == 'FALSE' or \
                (combo['null_setting'] == 'None' and combo['null_if'] == 'FALSE'):
            return rel             # MSG-10375 で未登録が確定

    # --- 段階⑤ ---
    rel |= {'var_type', 'assign_seq', 'driver'}
    if combo['locale'] and combo['reg_type'] == 'Key':
        rel.add('locale')          # Key の VARS_ENTRY は COLUMN_NAME_JA / _EN
    return rel


def canonicalize(combo):
    """無関係な軸をベースライン値に丸める（= 同値類の代表元）。"""
    rel = relevant_axes(combo)
    return tuple(sorted(
        (k, v if k in rel else AXIS_BY_KEY[k]['baseline'])
        for k, v in combo.items()
    ))


# ======================================================================
# 4. 集計
# ======================================================================
def functional_axes():
    """機能ケースの直積に使う軸（性能専用軸を除く）。"""
    return [a for a in AXES if not a.get('perf_only')]


def axis_values(axis, include_infeasible=True, include_perf=False):
    return [v['id'] for v in axis['values']
            if (include_infeasible or v['feasible'])
            and (include_perf or not v['perf'])]


def baseline_combo():
    return {a['key']: a['baseline'] for a in functional_axes()}


def stage_wise_cases():
    """段階ごとに「同居する軸だけ全組合せ、他はベースライン」でケースを生成する。

    パターン表が実際に主張している網羅水準はこれ。
      - 同一段階に同居する軸（= 1つの if を共有する軸）は組合せ全網羅
      - 異なる段階の軸は独立（relevant_axes() の根拠）

    Returns:
        同値類の集合（= 生成すべきケース集合）
    """
    import itertools

    axes = functional_axes()
    feasible = {a['key']: axis_values(a, include_infeasible=False) for a in axes}
    base = baseline_combo()
    cases = set()

    for stage in sorted(STAGES):
        stage_keys = [k for k in STAGES[stage]['axes'] if k in feasible]
        # 段階②以降は「そこへ到達する」ためにレコード有効性=有効が必要なので
        # ベースライン（有効・1件）を土台にする。
        for tup in itertools.product(*[feasible[k] for k in stage_keys]):
            combo = dict(base)
            combo.update(dict(zip(stage_keys, tup)))
            if not is_feasible(combo):
                continue
            cases.add(canonicalize(combo))
    return cases


def report():
    import itertools

    axes = functional_axes()
    keys = [a['key'] for a in axes]
    all_values = {a['key']: axis_values(a) for a in axes}
    feasible_values = {a['key']: axis_values(a, include_infeasible=False) for a in axes}

    print('=' * 72)
    print('軸定義')
    print('=' * 72)
    for a in AXES:
        flags = []
        if a.get('perf_only'):
            flags.append('性能専用')
        if a.get('separable'):
            flags.append('分離可能')
        if a.get('subsumed_by'):
            flags.append('{}に吸収'.format(a['subsumed_by']))
        n_all = len(axis_values(a))
        n_ok = len(axis_values(a, include_infeasible=False))
        print('  {:<16} {:<28} 値 {:>2}（実現可能 {:>2}） 段階{} {}'.format(
            a['key'], a['name'], n_all, n_ok, a['stage'],
            '[' + '/'.join(flags) + ']' if flags else ''))

    prod_all = 1
    prod_ok = 1
    for k in keys:
        prod_all *= len(all_values[k])
        prod_ok *= max(1, len(feasible_values[k]))
    print()
    print('  直積（表の値をそのまま掛ける）     : {:>10,}'.format(prod_all))
    print('  直積（あり得ない値を除く）         : {:>10,}'.format(prod_ok))

    # 制約適用 + 同値類
    combos = 0
    classes = set()
    for tup in itertools.product(*[feasible_values[k] for k in keys]):
        combo = dict(zip(keys, tup))
        if not is_feasible(combo):
            continue
        combos += 1
        classes.add(canonicalize(combo))
    print('  制約（軸間のあり得ない組合せ）適用 : {:>10,}'.format(combos))
    print('  → 同値類（期待値が区別できる数）   : {:>10,}   ★必要ケース数'.format(len(classes)))

    # 分離可能軸を外した数
    sep = [a['key'] for a in axes if a.get('separable')]
    if sep:
        reduced = set()
        for c in classes:
            d = dict(c)
            for k in sep:
                d[k] = AXIS_BY_KEY[k]['baseline']
            reduced.add(tuple(sorted(d.items())))
        extra = sum(len(feasible_values[k]) - 1 for k in sep)
        print('  → 分離可能軸({})を独立扱い       : {:>10,} + {} = {}'.format(
            ','.join(sep), len(reduced), extra, len(reduced) + extra))

    print()
    print('=' * 72)
    print('網羅水準ごとの必要ケース数')
    print('=' * 72)
    one_wise = max(len(feasible_values[k]) for k in keys)
    pair_lb = 0
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            pair_lb = max(pair_lb, len(feasible_values[k1]) * len(feasible_values[k2]))
    stage_cases = stage_wise_cases()
    print('  1-wise（各軸の各値を最低1回）下限   : {:>7}'.format(one_wise))
    print('  2-wise / pairwise 下限              : {:>7}'.format(pair_lb))
    print('  ★段階内のみ全組合せ（表の主張）     : {:>7}'.format(len(stage_cases)))
    print('  段階内も段階間も全組合せ            : {:>7,}'.format(len(classes)))
    print('  全直積                              : {:>7,}'.format(combos))
    print()
    print('  現状の pytest 実行ケース数          : {:>7}   (表66行 → parametrize展開)'.format(122))

    print()
    print('=' * 72)
    print('同一段階に同居する軸ペア（= 組合せ網羅の義務があるペア）')
    print('=' * 72)
    pairs = set()
    for stage, info in STAGES.items():
        sa = [k for k in info['axes'] if k in AXIS_BY_KEY]
        for i, k1 in enumerate(sa):
            for k2 in sa[i + 1:]:
                pairs.add((min(k1, k2), max(k1, k2), stage))
    for k1, k2, stage in sorted(pairs):
        print('  段階{}  {:<16} × {:<16} {}'.format(
            stage, k1, k2, STAGES[stage]['impl']))
    print()
    print('  上記以外のペアは「異なる段階にしか現れない」＝独立。')
    print('  独立性の主張は relevant_axes() に集約してあるので、')
    print('  pairwise を生成して全ペアを1度回し、新規の失敗が出ないことで反証を試みる。')


def dump_cases():
    """段階ベースのケース集合を「ベースラインからの差分」形式で出力する。

    既存テストが `make_col_data(...)` / `make_cmdb_row(...)` に
    差分だけを渡す書き方をしているので、そのまま突き合わせられる。
    """
    base = baseline_combo()
    rows = []
    for case in stage_wise_cases():
        d = dict(case)
        diff = {k: v for k, v in d.items() if v != base[k]}
        rows.append(diff)
    rows.sort(key=lambda d: (len(d), sorted(d.items())))

    by_stage = {}
    for diff in rows:
        stages = sorted({AXIS_BY_KEY[k]['stage'] for k in diff}) or [0]
        by_stage.setdefault(max(stages), []).append(diff)

    print('段階ベースのケース集合: {} 件（ベースラインからの差分表記）'.format(len(rows)))
    for stage in sorted(by_stage):
        print()
        print('--- 主段階{} : {} ({}件) ---'.format(
            stage, STAGES[stage]['name'], len(by_stage[stage])))
        for diff in by_stage[stage]:
            print('  ' + (', '.join('{}={}'.format(k, v) for k, v in sorted(diff.items()))
                          or '(ベースラインそのまま)'))


if __name__ == '__main__':
    import sys
    if '--dump' in sys.argv:
        dump_cases()
    else:
        report()
