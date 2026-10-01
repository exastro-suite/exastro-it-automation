"""段階7: パラメータシートへの具体値投入と、代入値自動登録設定の登録。"""
import json
import sys
import time

from ita import get
from lib import b64, find_active, load_ids, register, rest_of, save_ids, show

SHEET_H = 'pytest_ps_h'
SHEET_V = 'pytest_ps_v'
SHEET_O = 'pytest_ps_ope'         # パラメータシート参照の参照先(ホスト列が無い)
SHEET_N = 'pytest_ps_noitem'      # 項目なし
SHEET_G = 'pytest_ps_hg'          # ホストグループ利用=有(入力用メニュー)
# ホストグループ利用シートの代入値自動登録用メニュー。実体は入力用とは**別テーブル**
# (`T_CMDB_<id>_SV`)で、hostgroup-split バックヤードが `[HG]…` の行を
# メンバー機器ごとに展開して書き込む。代入値自動登録設定が読むのはこちら側
SUBST_G = 'pytest_ps_hg_subst'
SHEET_GV = 'pytest_ps_hg_v'       # ホストグループ利用=有 **かつ** バンドル(縦)=有
SUBST_GV = 'pytest_ps_hg_v_subst'  # 同シートの代入値自動登録用メニュー(INPUT_ORDER 付き)
AUTOREG_L = 'subst_value_auto_reg_setting_ansible_legacy'
AUTOREG_P = 'subst_value_auto_reg_setting_ansible_pioneer'
AUTOREG_R = 'subst_value_auto_reg_setting_ansible_role'

HOST_A, HOST_B, HOST_C, HOST_Z = 'pytest-host-A', 'pytest-host-B', 'pytest-host-C', 'pytest-host-Z'
OPE_1, OPE_2, OPE_D = 'pytest-ope-1', 'pytest-ope-2', 'pytest-ope-disused'

# ホストグループ利用シートのホスト列(`V_HGSP_UQ_HOST_LIST`)の選択肢。
# `[HG]<ホストグループ名>` / `[H]<ホスト名>` の形式で、前者だけが展開される
HG_VALUE = '[HG]pytest-hg-1'      # → pytest-host-A / pytest-host-B の2行に展開される
HG_HOST_VALUE = '[H]' + HOST_C    # ホスト直指定。展開されずそのまま `_SV` に載る
HG_EXPECT_SV_ROWS = 3             # 上記2行 → A / B / C の3行になる
# 縦HGシートは (ホスト, オペレーション, 代入順序) で行が増える。
# `[HG]` × 代入順序1/2 → A/B × 2 の4行 + `[H]` × 代入順序1 の1行 = 5行
HG_V_EXPECT_SV_ROWS = 5

TPF_VALUE = '{{ TPF_pytest_tpl }}'    # 文字列カラムに直接書く TPF変数
TEMPLATE_VAR = 'TPF_pytest_tpl'       # TPFプルダウンの選択肢(段階2で登録)
TEMPLATE_DROP_VAR = 'TPF_pytest_drop'
FILE_VAR = 'CPF_pytest_conf'          # CPFプルダウンの選択肢(段階2で登録)
FILE_DROP_VAR = 'CPF_pytest_drop'


# ----------------------------------------------------------------------
def wait_menu(menu, timeout=1800, interval=20):
    """メニュー(パラメータシート)が実体化するまで待つ。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        res = get('/menu/%s/info/' % menu)
        if isinstance(res.get('data'), dict):
            return res['data']
        print('  %s 待機中 (%s)' % (menu, res.get('result')))
        time.sleep(interval)
    return None


def wait_pulldown(menu, column, prefix, timeout=1800, interval=20):
    """指定カラムのプルダウンに prefix を含む選択肢が出るまで待つ。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        values = get('/menu/%s/info/pulldown/' % menu)['data'].get(column) or {}
        hit = {k: v for k, v in values.items() if prefix in str(v)}
        if hit:
            return hit
        print('  %s の %s 待機中' % (menu, column))
        time.sleep(interval)
    return {}


def operation_values(menu, ope_col):
    """オペレーション列が受け付ける値(『日時_オペレーション名』)へのマップを作る。

    プルダウンの表示値そのままでないと 499-00201 になるので、
    オペレーション名から実際の選択肢を引けるようにしておく。
    """
    pull = get('/menu/%s/info/pulldown/' % menu)['data'].get(ope_col) or {}
    table = {}
    for value in pull.values():
        table[value] = value                       # 表示値そのまま
        if '_' in value:
            table[value.split('_', 1)[1]] = value  # オペレーション名から引く
    return table


def insert_rows(menu, info, rows):
    """既に同じホスト/オペ(/代入順序)の行があればスキップして投入する。"""
    host_col = rest_of(info, 'HOST_ID')            # 例: host_name。オペのみのシートは None
    ope_col = rest_of(info, 'OPERATION_ID')        # 例: operation_name_select
    order_col = rest_of(info, 'INPUT_ORDER')       # 縦シートのみ存在
    ope_map = operation_values(menu, ope_col)
    # 廃止済みの機器/オペレーションはプルダウンから消える。段階8 の後に
    # この段階を再実行しても落ちないように、選べない行はスキップする
    host_values = set((get('/menu/%s/info/pulldown/' % menu)['data'].get(host_col) or {}).values()) \
        if host_col else set()
    print('  %s: ホスト列=%s オペ列=%s 代入順序列=%s' % (menu, host_col, ope_col, order_col))

    existing = set()
    for row in find_active(menu):
        p = row['parameter']
        existing.add((p.get(host_col) if host_col else None, p.get(ope_col),
                      str(p.get(order_col)) if order_col else None))

    todo = []
    for host, ope, values, files in rows:
        # 段階8(廃止)を実施済みで再実行した場合。廃止した機器/オペレーションは
        # プルダウンから消えるので新規には登録できない(既存行はそのまま残る)
        if ope not in ope_map:
            print('  スキップ(オペレーション %s がプルダウンに無い。廃止済み?)' % ope)
            continue
        if host_col and host not in host_values:
            print('  スキップ(機器 %s がプルダウンに無い。廃止済み?)' % host)
            continue
        parameter = {ope_col: ope_map[ope]}
        if host_col:                               # sheet_type 3 はホスト列を持たない
            parameter[host_col] = host
        parameter.update(values)
        key = (host if host_col else None, ope_map[ope],
               str(values.get(order_col)) if order_col else None)
        if key in existing:
            print('  既存: %s' % (key,))
            continue
        todo.append({'parameter': parameter, 'file': files})

    if not todo:
        return []
    ids = register(menu, todo)
    print('  %d件 登録: %s' % (len(ids), ids))
    return ids


def operation_rows():
    """参照先シート(オペレーションあり)の行。

    **OPE_2 の行は意図的に作らない。** パラメータシート参照の値は「その行のオペレーションID」
    なので、参照先に行が無いオペレーションでは JsonIDColumn が `ID変換失敗(...)`、
    JsonPasswordIDColumn が NULL になる。廃止処理を増やさずに両方の分岐を作れる。
    """
    return [(None, OPE_1, {'po_std': '参照元の値', 'po_pw': 'ref-pw-1'}, {})]


def noitem_rows():
    """項目なしシートの行。項目が無いのでホストとオペレーションだけを入れる。

    自動生成される `no_item` は UNIQUE/REQUIRED が立っているが `INPUT_ITEM=2`
    (入力欄非表示)なので、必須チェックも一意チェックも走らない。送ってはいけない。
    """
    return [
        (HOST_A, OPE_1, {}, {}),
        (HOST_B, OPE_1, {}, {}),
        (HOST_A, OPE_2, {}, {}),
    ]


def horizontal_rows():
    """横メニュー用の行。検証したいパターンを1つのシートに詰める。

    `ps_ref_std` / `ps_ref_pw`(パラメータシート参照)は送らない。登録時に
    `operation_name_select` の `set_reference_operation` がその行のオペレーションIDを
    流し込むので、クライアントから送っても `exclusion_parameter` に捨てられる。
    """
    common = {
        'ps_id': '*',
        'ps_tpl': TPF_VALUE,               # 文字列カラムに直接 TPF変数を書く
        'ps_tpf': TEMPLATE_VAR,            # → "'{{ TPF_pytest_tpl }}'" に包まれる
        'ps_cpf': FILE_VAR,                # → "'{{ CPF_pytest_conf }}'" に包まれる
        'ps_tpf_drop': TEMPLATE_DROP_VAR,  # 段階8で廃止 → ID変換失敗 → レコード破棄
        'ps_cpf_drop': FILE_DROP_VAR,      # 同上
        'ps_host': HOST_A,                 # → ps_host_ref_1/2 に機器のユーザ/パスワード
        'ps_num': '42',                    # → 値が int で返る
        'ps_float': '3.14',
        'ps_link': 'http://127.0.0.1/pytest',
    }
    return [
        # 通常値(全カラム埋め) + ファイルアップロード
        (HOST_A, OPE_1, dict(common, ps_std='値A', ps_pw='pw-A',
                             ps_multi='line1\nline2', ps_empty='not-empty'),
         {'ps_file': b64('pytest file A\n')}),
        # 別ホスト・同一オペ(ホスト複数)
        (HOST_B, OPE_1, dict(common, ps_std='値B', ps_pw='pw-B', ps_multi='B1\nB2'), {}),
        # 同一ホスト・別オペ(オペ複数)。OPE_2 は参照先シートに行が無いので
        # ps_ref_std → 'ID変換失敗(...)' / ps_ref_pw → NULL になる
        (HOST_A, OPE_2, dict(common, ps_std='値A2', ps_pw='pw-A2'), {}),
        # 空値のみの行。整数/小数/プルダウン/参照項目が全部 NULL になる分岐
        (HOST_B, OPE_2, {'ps_std': '', 'ps_pw': '', 'ps_empty': ''}, {}),
        # 廃止オペレーションに紐づく行
        (HOST_C, OPE_D, dict(common, ps_std='値C-廃止オペ'), {}),
        # 廃止機器に紐づく行
        (HOST_Z, OPE_1, dict(common, ps_std='値Z-廃止機器'), {}),
    ]


def vertical_rows(info):
    """縦(バンドル)メニュー用の行。INPUT_ORDER を変えて複数行。

    縦シートでは「設定のカラム代入順序 == 行の INPUT_ORDER」の行だけが登録対象になる
    (`SubValueAutoReg.py:998-999`)。INPUT_ORDER 1〜3 を作り、PLAN_VERTICAL 側で
    代入順序を 1/2/3 に散らすことで「代入順序ごとに別の行を拾う」ことまで通す。

    **INPUT_ORDER=4 の行は意図的に作らない** — PLAN_VERTICAL の代入順序4 が
    どの行にも一致せず、MSG-10902(`:1114-1128`)の経路を通るようにするため。
    """
    order_col = rest_of(info, 'INPUT_ORDER') or 'input_order'
    # 横シートと同じカラム構成なので、値も横(horizontal_rows)と同じ形で入れる。
    # pv_ref_std / pv_ref_pw は送らない(登録時にその行のオペレーションIDが入る)
    common = {
        'pv_id': '*',
        'pv_tpl': TPF_VALUE,               # 文字列カラムに直接 TPF変数を書く
        'pv_tpf': TEMPLATE_VAR,            # → "'{{ TPF_pytest_tpl }}'" に包まれる
        'pv_cpf': FILE_VAR,                # → "'{{ CPF_pytest_conf }}'" に包まれる
        'pv_tpf_drop': TEMPLATE_DROP_VAR,  # 段階8で廃止 → ID変換失敗 → レコード破棄
        'pv_cpf_drop': FILE_DROP_VAR,      # 同上
        'pv_host': HOST_A,                 # → pv_host_ref_1/2 に機器のユーザ/パスワード
        'pv_num': '42',
        'pv_float': '3.14',
        'pv_link': 'http://127.0.0.1/pytest',
    }
    rows = [(HOST_A, OPE_1,
             dict(common, **{order_col: str(i),
                             'pv_std': '縦値%d' % i,
                             'pv_pw': 'pw-v%d' % i,
                             'pv_multi': 'v%d-line1\nv%d-line2' % (i, i),
                             'pv_empty': 'not-empty'}),
             {})
            for i in range(1, 4)]
    # 空値のみの行(縦側で NULL連携 / 空値の分岐を通す)
    rows.append((HOST_B, OPE_1, {order_col: '1', 'pv_std': '', 'pv_pw': '',
                                 'pv_empty': ''}, {}))
    # OPE_2 は参照先シート(pytest_ps_ope)に行が無いので
    # pv_ref_std → 'ID変換失敗(...)' / pv_ref_pw → NULL(MSG-10375)になる
    rows.append((HOST_A, OPE_2, dict(common, **{order_col: '1', 'pv_std': '縦値A2',
                                                'pv_pw': 'pw-vA2'}), {}))
    return rows


def hostgroup_rows():
    """ホストグループ利用シート用の行。ホスト列に `[HG]…` / `[H]…` を入れる。

    このシートだけは「投入した行」と「代入値自動登録設定が読む行」が別テーブルになる。
    `[HG]…` の行は hostgroup-split バックヤードがメンバー機器ごとに複製して
    代入値自動登録用メニューのテーブル(`T_CMDB_<id>_SV`)へ書き込み、
    ホストグループ名のままの行は廃止扱いになる(`split_function.py`)。
    展開はカラムクラスごとに処理が分かれている(FileUploadColumn は実ファイルのコピーまで)
    ので、値は横シート(horizontal_rows)と同じ形で全カラムに入れる。

    `[H]…`(ホスト直指定)の行も入れる。展開されない行と展開された行が
    同じテーブルに並ぶので、どちらも壊れずにレコードになることを見られる。
    """
    common = {
        'pg_id': '*',
        'pg_tpl': TPF_VALUE,
        'pg_tpf': TEMPLATE_VAR,
        'pg_cpf': FILE_VAR,
        'pg_tpf_drop': TEMPLATE_DROP_VAR,  # 段階8で廃止 → ID変換失敗 → レコード破棄
        'pg_cpf_drop': FILE_DROP_VAR,      # 同上
        'pg_host': HOST_A,                 # → pg_host_ref_1/2 に機器のユーザ/パスワード
        'pg_num': '42',
        'pg_float': '3.14',
        'pg_link': 'http://127.0.0.1/pytest',
    }
    return [
        (HG_VALUE, OPE_1, dict(common, pg_std='HG値', pg_pw='pw-hg',
                               pg_multi='hg-line1\nhg-line2', pg_empty='not-empty'), {}),
        (HG_HOST_VALUE, OPE_1, dict(common, pg_std='HG値(ホスト直指定)', pg_pw='pw-hg-c',
                                    pg_multi='c-line1\nc-line2', pg_empty='not-empty'), {}),
    ]


def hostgroup_vertical_rows(info):
    """ホストグループ利用 **かつ** バンドル(縦)のシート用の行。

    `[HG]…` の行を **代入順序(INPUT_ORDER)ごとに** 作る。ここだけが
      - hostgroup-split の縦コピー(`insert_data['INPUT_ORDER'] = ...`:
        split_function.py:899 / :1299-1302。横では :1302 で INPUT_ORDER を落とす)
      - 代入値自動登録設定の縦分岐(「代入順序 == 行の INPUT_ORDER」:
        SubValueAutoReg.py:998-999)
    の両方を同時に通る経路で、片方が INPUT_ORDER を落とす/振り直すと
    「レコードが0件」または「別の代入順序の値」になる。

    設定側(PLAN_HG_VERTICAL)は代入順序1と2を混ぜてあるので、
    行の値も1と2で変えておき「どちらの行から採ったか」が値で分かるようにする。
    `[H]…`(ホスト直指定 = 展開されない行)も1行だけ入れて、展開行と非展開行が
    同じ `_SV` テーブルに INPUT_ORDER 付きで並ぶ状態を作る。

    項目は他の3シートと同じ構成なので、値も横HG(hostgroup_rows)と同じ形で全カラムに
    入れる(展開はカラムクラスごとに処理が分かれるため)。
    `pgv_ref_std` / `pgv_ref_pw`(パラメータシート参照)は送らない
    — 登録時にその行のオペレーションIDが流し込まれる。
    """
    order_col = rest_of(info, 'INPUT_ORDER') or 'input_order'
    common = {
        'pgv_id': '*',
        'pgv_tpl': TPF_VALUE,
        'pgv_tpf': TEMPLATE_VAR,
        'pgv_cpf': FILE_VAR,
        'pgv_tpf_drop': TEMPLATE_DROP_VAR,  # 段階8で廃止 → ID変換失敗 → レコード破棄
        'pgv_cpf_drop': FILE_DROP_VAR,      # 同上
        'pgv_host': HOST_A,                 # → pgv_host_ref_1/2 に機器のユーザ/パスワード
        'pgv_num': '42',
        'pgv_float': '3.14',
        'pgv_link': 'http://127.0.0.1/pytest',
    }
    return [
        # 代入順序1: 空値 + NULL連携ON の分岐を通すため pgv_empty は空のまま
        (HG_VALUE, OPE_1, dict(common, **{order_col: '1', 'pgv_std': 'HG縦値1',
                                          'pgv_pw': 'pw-hgv1', 'pgv_empty': '',
                                          'pgv_multi': 'hgv1-line1\nhgv1-line2'}), {}),
        # 代入順序2: 同じホストグループ・同じオペレーションで INPUT_ORDER だけ違う行。
        # 値を1と違えておくと「どちらの行から採ったか」が具体値で分かる(INT-20)
        (HG_VALUE, OPE_1, dict(common, **{order_col: '2', 'pgv_std': 'HG縦値2',
                                          'pgv_pw': 'pw-hgv2', 'pgv_empty': 'not-empty',
                                          'pgv_multi': 'hgv2-line1\nhgv2-line2'}), {}),
        # ホスト直指定(展開されない)。代入順序1のみ
        (HG_HOST_VALUE, OPE_1, dict(common, **{order_col: '1', 'pgv_std': 'HG縦値C',
                                               'pgv_pw': 'pw-hgv-c', 'pgv_empty': '',
                                               'pgv_multi': 'c-line1\nc-line2'}), {}),
    ]


def wait_split(menu, expect, timeout=1800, interval=20):
    """hostgroup-split バックヤードの展開が終わるまで待つ。

    展開先は代入値自動登録用メニュー(`<入力用>_subst`)。入力用メニューを更新すると
    `T_HGSP_SPLIT_TARGET.DIVIDED_FLG` が 0 に戻り、バックヤードが再展開する。

    バックヤードは対象メニューを**まとめて**処理し、入力用と代入値自動登録用で
    VERTICAL が食い違うメニューが1つでもあると get_target_menu が例外を投げて
    **全メニューの展開が止まる**(split_function.py:114-122)。よって横HGだけ・
    縦HGだけが止まることは無く、どちらかが0件なら両方を疑う。
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            rows = find_active(menu)
        except RuntimeError as e:
            print('  %s を引けない (%s)' % (menu, e))
            rows = []
        if len(rows) >= expect:
            return rows
        print('  %s の展開待ち (%d/%d件)' % (menu, len(rows), expect))
        time.sleep(interval)
    return []


# ----------------------------------------------------------------------
# (シート項目名, 変数名の末尾, 登録方式, NULL連携, 追加パラメータ)
# 項目名は `代入値自動登録用:<メニュー名>:パラメータ/<項目名>` の末尾と完全一致で引く。
PLAN_STD = [
    ('文字列', 'std', 'Value型', 'False', {}),               # 一般的な組み合わせ
    ('パスワード列', 'pw', 'Value型', 'False', {}),           # センシティブ(PasswordColumn)
    ('ファイル', 'file', 'Value型', 'False', {}),             # FileUploadColumn
    ('空値', 'empty', 'Value型', 'True', {}),                # 空値 + NULL連携ON
    ('プルダウン', 'id', 'Value型', 'False', {}),             # IDColumn(*-(ブランク))
    ('複数行', 'multi', 'Key型', 'False', {}),               # Key型(Pioneer は項目に出ない)
    # Key型 を Pioneer でも通すための行。Pioneer の項目プルダウン(V_ANSP_COLUMN_LIST)は
    # MultiTextColumn を除外するので、上の『複数行』だけでは Pioneer が Key型 を1件も通らない
    # (Key型 は具体値ではなく**項目名**を登録する別経路: SubValueAutoReg.py:1216-1245)。
    # 重複キー (変数, メンバー変数, 代入順序) にカラムは含まれないので、
    # Value型 と同じ『文字列』に別変数(pytest_key)で載せてよい
    ('文字列', 'key', 'Key型', 'False', {}),
    ('テンプレート埋込', 'tpl', 'Value型', 'False', {}),        # 具体値に {{ TPF_x }}
    ('TPF選択', 'tpf', 'Value型', 'False', {}),              # → '{{ TPF_x }}' に包まれる
    ('CPF選択', 'cpf', 'Value型', 'False', {}),              # → '{{ CPF_x }}' に包まれる
    ('TPF選択廃止用', 'tpf_drop', 'Value型', 'False', {}),     # ID変換失敗 → 破棄
    ('CPF選択廃止用', 'cpf_drop', 'Value型', 'False', {}),     # ID変換失敗 → 破棄
    ('ホスト選択', 'host', 'Value型', 'False', {}),           # IDColumn(機器一覧)
    ('ユーザ', 'host_user', 'Value型', 'False', {}),          # 派生 ps_host_ref_1 (7)
    ('パスワード', 'host_pw', 'Value型', 'False', {}),         # 派生 ps_host_ref_2 (25)
    ('シート参照文字列', 'ref_std', 'Value型', 'False', {}),     # JsonIDColumn (21)
    ('シート参照パスワード', 'ref_pw', 'Value型', 'False', {}),   # JsonPasswordIDColumn (26)
    ('整数', 'num', 'Value型', 'False', {}),                 # NumColumn(値が int)
    ('小数', 'float', 'Value型', 'False', {}),               # FloatColumn
    ('リンク', 'link', 'Value型', 'False', {}),               # HostInsideLinkTextColumn
]

# 縦(バンドル)シート用。項目は PLAN_STD と同じ19個(カラムクラスを縦でも網羅する)。
# 変数は `pytest_v_` 系(段階2 の VARS_V)を使う。横シート(PLAN_STD)と同じ Movement に
# 載せるため、変数が重複すると MSG-10430 になるので変数だけ別にしてある。
# 縦シートは `column_substitution_order`(カラム代入順序)が必須で、
# 「設定の代入順序 == 行の INPUT_ORDER」の行だけが登録対象になる
# (SubValueAutoReg.py:998-999)。1/2/3 を散らして「代入順序ごとに別の行を拾う」ことまで通す。
# extra に書かない行は autoreg_rows の既定値 '1'。
PLAN_VERTICAL = [
    ('文字列', 'std', 'Value型', 'False', {}),                                        # 順序1
    ('パスワード列', 'pw', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('ファイル', 'file', 'Value型', 'False', {'column_substitution_order': '3'}),
    ('空値', 'empty', 'Value型', 'True', {'column_substitution_order': '1'}),
    ('プルダウン', 'id', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('複数行', 'multi', 'Key型', 'False', {'column_substitution_order': '3'}),
    ('テンプレート埋込', 'tpl', 'Value型', 'False', {'column_substitution_order': '1'}),
    # 縦側の TPF/CPF 変換(:1023-1025)。横側(:1052-1056)とは別のコピー
    ('TPF選択', 'tpf', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('CPF選択', 'cpf', 'Value型', 'False', {'column_substitution_order': '3'}),
    # 縦側の ID変換失敗 → レコード破棄(:1026-1027)。参照先は段階8で廃止する
    ('TPF選択廃止用', 'tpf_drop', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('CPF選択廃止用', 'cpf_drop', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('ホスト選択', 'host', 'Value型', 'False', {'column_substitution_order': '3'}),
    ('ユーザ', 'host_user', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('パスワード', 'host_pw', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('シート参照文字列', 'ref_std', 'Value型', 'False', {'column_substitution_order': '3'}),
    ('シート参照パスワード', 'ref_pw', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('整数', 'num', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('小数', 'float', 'Value型', 'False', {'column_substitution_order': '3'}),
    ('リンク', 'link', 'Value型', 'False', {'column_substitution_order': '1'}),
    # 代入順序4 に一致する INPUT_ORDER=4 の行は作らない → MSG-10902(:1114-1128)。
    # 重複キーにカラムは含まれないので項目は使い回してよい。変数だけ専用のものを使う
    ('文字列', 'vseq', 'Value型', 'False', {'column_substitution_order': '4'}),
]

# ホストグループ利用 × 縦シート(`pytest_ps_hg_v`)用。項目は他の3シートと同じ19個
# (17項目 + 派生2項目)に揃え、**代入順序1と2を交互に振る**。
# 展開先テーブルの INPUT_ORDER が壊れると
#   - 落ちる → 代入順序2の項目が MSG-10902(該当行なし)になり値が消える
#   - 振り直される → 代入順序1の項目に『HG縦値2』が入る
# のどちらかになり、値まで見れば区別できる(hostgroup_vertical_rows)。
# 「展開 × 縦」でもクラスごとの値の作り方(センシティブ / TPF・CPF の括り /
# ID変換失敗による破棄 / 派生項目 / シート参照 / 数値)が壊れないことまで見るため、
# 代入順序は**同じクラスが1と2の両方に散る**ようにはせず、
# 項目ごとに固定(下表)にして「どの行から採ったか」が値で分かる状態を保つ。
# 変数は `pytest_gv_` 系(段階2 の VARS_G_V)。Movement は横HG・縦と同じ L1
PLAN_HG_VERTICAL = [
    ('文字列', 'std', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('パスワード列', 'pw', 'Value型', 'False', {'column_substitution_order': '2'}),
    # 段階9 で実ファイルを載せるのは代入順序1の `[HG]` 行(展開時のファイルコピー)
    ('ファイル', 'file', 'Value型', 'False', {'column_substitution_order': '1'}),
    # 空値 + NULL連携ON。代入順序1の行の pgv_empty は空
    ('空値', 'empty', 'Value型', 'True', {'column_substitution_order': '1'}),
    ('プルダウン', 'id', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('複数行', 'multi', 'Key型', 'False', {'column_substitution_order': '2'}),
    # Key型 は具体値ではなく項目名を登録する別経路。重複キー (変数, メンバー変数, 代入順序)
    # にカラムは含まれないので『文字列』に別変数で載せてよい
    ('文字列', 'key', 'Key型', 'False', {'column_substitution_order': '1'}),
    ('テンプレート埋込', 'tpl', 'Value型', 'False', {'column_substitution_order': '2'}),
    # 縦側の TPF/CPF 変換(:1023-1025)を展開後のテーブルでも通す
    ('TPF選択', 'tpf', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('CPF選択', 'cpf', 'Value型', 'False', {'column_substitution_order': '2'}),
    # 縦側の ID変換失敗 → レコード破棄(:1026-1027)。参照先は段階8で廃止する
    ('TPF選択廃止用', 'tpf_drop', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('CPF選択廃止用', 'cpf_drop', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('ホスト選択', 'host', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('ユーザ', 'host_user', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('パスワード', 'host_pw', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('シート参照文字列', 'ref_std', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('シート参照パスワード', 'ref_pw', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('整数', 'num', 'Value型', 'False', {'column_substitution_order': '2'}),
    ('小数', 'float', 'Value型', 'False', {'column_substitution_order': '1'}),
    ('リンク', 'link', 'Value型', 'False', {'column_substitution_order': '2'}),
]

# 項目なしシート。カラムグループが無いので項目名は『:(項目なし)』で終わる。
# 変数名は `None` = 選択しない(`AUTOREG_ONLY_ITEM='1'` の項目では
# 変数名/メンバー変数/代入順序を入れると MSG-10897 / MSG-10896 で弾かれる)。
PLAN_NOITEM = [
    ('(項目なし)', None, 'Value型', 'False', {}),
]

# LegacyRole 専用。複数具体値(LIST)は代入順序、多次元配列(M_ARRAY)はメンバー変数が要る。
# 同一 Movement 内で (変数, メンバー変数, 代入順序) が一意でないと MSG-10430 になるため、
# 一般変数 pytest_r_std は1項目だけ・多次元配列はメンバー2個だけ・
# 残りは複数具体値 pytest_r_list に代入順序をずらして割り当てる。
# ファイルは段階9で入れるのでここには無い。
PLAN_ROLE = [
    ('文字列', 'std', 'Value型', 'False', {}),                # 一般変数(代入順序なし)
    # メンバー変数の行は代入順序を入れてはいけない(MSG-10429)
    ('空値', 'array', 'Value型', 'True', {'member_variable_name': 'pytest_r_member1'}),
    ('テンプレート埋込', 'array', 'Value型', 'False', {'member_variable_name': 'pytest_r_member2'}),
    ('パスワード列', 'list', 'Value型', 'False', {'substitution_order': '5'}),
    ('プルダウン', 'list', 'Value型', 'False', {'substitution_order': '6'}),
    ('複数行', 'list', 'Value型', 'False', {'substitution_order': '7'}),
    ('TPF選択', 'list', 'Value型', 'False', {'substitution_order': '8'}),
    ('CPF選択', 'list', 'Value型', 'False', {'substitution_order': '9'}),
    ('TPF選択廃止用', 'list', 'Value型', 'False', {'substitution_order': '10'}),
    ('CPF選択廃止用', 'list', 'Value型', 'False', {'substitution_order': '11'}),
    ('ホスト選択', 'list', 'Value型', 'False', {'substitution_order': '12'}),
    ('ユーザ', 'list', 'Value型', 'False', {'substitution_order': '13'}),
    ('パスワード', 'list', 'Value型', 'False', {'substitution_order': '14'}),
    ('シート参照文字列', 'list', 'Value型', 'False', {'substitution_order': '15'}),
    ('シート参照パスワード', 'list', 'Value型', 'False', {'substitution_order': '16'}),
    ('整数', 'list', 'Value型', 'False', {'substitution_order': '17'}),
    ('小数', 'list', 'Value型', 'False', {'substitution_order': '18'}),
    ('リンク', 'list', 'Value型', 'False', {'substitution_order': '19'}),
    # LegacyRole でも Key型(項目名を登録する経路)を通す。変数の種類による制約
    # (複数具体値 → 代入順序が必要)は登録方式と独立なので(valid_20407.py:355-432)、
    # 複数具体値 pytest_r_list に未使用の代入順序20 を割り当てて載せる。
    # 重複キーは (変数, メンバー変数, 代入順序) なので上の『文字列』行とは衝突しない
    ('文字列', 'list', 'Key型', 'False', {'substitution_order': '20'}),
]

# LegacyRole は変数が3種類(一般変数 `pytest_r_std` / 複数具体値 `pytest_r_list` /
# 多次元配列 `pytest_r_array`)しか無いので、Legacy のように**シートごとに変数を分けられない**
# (Legacy は `pytest_` / `pytest_v_` / `pytest_g_` / `pytest_gv_` の4系統)。
# そのかわり**複数具体値 `pytest_r_list` の代入順序をシートごとの帯に割り当てる**ことで
# (変数, メンバー変数, 代入順序) の一意制約(MSG-10430)を満たす。
#
#   帯      用途
#   ------  ----------------------------------------------------------------
#   (なし)  横シートの『文字列』(一般変数) / 『空値』『テンプレート埋込』(多次元配列のメンバー)
#   4       横シートの『ファイル』(段階9 の PLAN_ROLE_FILE)
#   5〜20   横シート           (PLAN_ROLE)
#   21〜40  縦シート           (PLAN_VERTICAL と同じ20項目)
#   41〜60  HG横シート         (PLAN_STD と同じ20項目)
#   61〜80  HG×縦シート        (PLAN_HG_VERTICAL と同じ20項目)
def role_plan(plan, first_order):
    """Legacy 用のプランを LegacyRole 用に変換する。

    項目・登録方式・NULL連携・カラム代入順序はそのまま使い、変数は複数具体値
    `pytest_r_list` に固定して代入順序を `first_order` から連番で振る。
    多次元配列のメンバー変数は横シート(PLAN_ROLE)だけで使うので落とす。
    """
    out = []
    for i, (item, _suffix, method, null_link, extra) in enumerate(plan):
        extra = dict(extra)
        extra.pop('member_variable_name', None)
        extra['substitution_order'] = str(first_order + i)
        out.append((item, 'list', method, null_link, extra))
    return out


# LegacyRole の縦 / HG横 / HG×縦。**使用可能なカラムはすべて設定に載せる**
# (Legacy と同じ項目構成)。
# ケース表の軸「設定件数 1/2/4/25」は `perf_only`(件数は機能分岐を増やさない性能軸)で、
# 単体の全組合せ・性能カナリアが持つ軸なので、結合テストのデータ側で
# 「4設定のテーブル」をわざわざ残す必要はない。
PLAN_ROLE_VERTICAL = role_plan(PLAN_VERTICAL, 21)
PLAN_ROLE_HG = role_plan(PLAN_STD, 41)
PLAN_ROLE_HG_VERTICAL = role_plan(PLAN_HG_VERTICAL, 61)

# LegacyRole × 項目なしシート。LegacyRole でも代入順序は入れられない(MSG-10896)
PLAN_ROLE_NOITEM = [
    ('(項目なし)', None, 'Value型', 'False', {}),
]


def autoreg_rows(menu, sheet_item_prefix, movement, var_prefix, plan=PLAN_STD, vertical=False):
    """代入値自動登録設定を作る。項目/変数はプルダウンの実値から選ぶ。

    vertical=True(バンドル)のシートは column_substitution_order が必須、
    横シートでは逆に入力してはいけない(valid_20407.py:487-497)。
    既定は '1' で、plan の extra に書けば行ごとに変えられる(あとの extra ループが上書きする)。
    """
    pull = get('/menu/%s/info/pulldown/' % menu)['data']
    items = sorted((pull.get('menu_group_menu_item') or {}).values())
    variables = sorted((pull.get('variable_name') or {}).values())
    members = sorted((pull.get('member_variable_name') or {}).values())

    def find_item(item_name):
        """『代入値自動登録用:<メニュー名>:パラメータ/<項目名>』を項目名の完全一致で探す。

        部分一致にすると「文字列」が「シート参照文字列」に、
        「パスワード」が「パスワード列」に当たってしまう。
        カラムグループを持たない「(項目なし)」は `:<項目名>` で終わる。
        """
        tails = (':パラメータ/' + item_name, ':' + item_name)
        for name in items:
            if sheet_item_prefix in name and name.endswith(tails):
                return name
        return None

    def find_var(var_name):
        """『Movement名:変数名』は対象 Movement のものでなければ弾かれる。"""
        want = '%s:%s' % (movement, var_prefix + var_name)
        return want if want in variables else None

    def find_member(var_name, member):
        """メンバー変数は『Movement名:変数名:[0].メンバー名』形式。"""
        head = '%s:%s:' % (movement, var_prefix + var_name)
        for name in members:
            if name.startswith(head) and name.endswith('.' + member):
                return name
        return None

    rows = []
    for suffix, var_name, method, null_link, extra in plan:
        item = find_item(suffix)
        # var_name が None の行は「項目なしメニューの項目」= 変数を選ばない
        var = find_var(var_name) if var_name is not None else None
        missing = []
        if not item:
            missing.append('項目 %s' % suffix)
        if var_name is not None and not var:
            missing.append('変数 %s' % (var_prefix + var_name))
        if missing:
            print('  スキップ(%s が無い)' % ' / '.join(missing))
            continue
        parameter = {
            'menu_group_menu_item': item,
            'registration_method': method,
            'movement': movement,
            'null_link': null_link,
            'remarks': 'pytest(結合テスト)用',
            'discard': '0',
        }
        # 項目なしメニューの項目は変数名/メンバー変数/代入順序を入れてはいけない
        # (MSG-10897 / MSG-10896)。縦の column_substitution_order も同様
        if var is not None:
            parameter['variable_name'] = var
            if vertical:
                parameter['column_substitution_order'] = '1'   # extra があれば下で上書き
        for key, value in extra.items():
            if key == 'member_variable_name':
                member = find_member(var_name, value)
                if not member:
                    print('  スキップ(メンバー変数 %s が無い): %s' % (value, suffix))
                    parameter = None
                    break
                parameter[key] = member
            else:
                parameter[key] = value
        if parameter:
            rows.append({'parameter': parameter})

    if not rows:
        return []
    existing = {(r['parameter'].get('menu_group_menu_item'), r['parameter'].get('variable_name'))
                for r in find_active(menu)}
    rows = [r for r in rows
            if (r['parameter']['menu_group_menu_item'],
                r['parameter'].get('variable_name')) not in existing]
    if not rows:
        print('  すべて既存')
        return []
    ids = register(menu, rows)
    print('  %d件 登録: %s' % (len(ids), ids))
    return ids


# ----------------------------------------------------------------------
def main():
    ids = load_ids()

    print('== パラメータシートの実体化を待つ')
    info_o = wait_menu(SHEET_O)
    info_n = wait_menu(SHEET_N)
    info_h = wait_menu(SHEET_H)
    info_v = wait_menu(SHEET_V)
    info_g = wait_menu(SHEET_G)
    info_gv = wait_menu(SHEET_GV)
    if not (info_o and info_n and info_h and info_v and info_g and info_gv):
        print('!! パラメータシートが作成されていない(menu-create バックヤード未稼働)。中断')
        sys.exit(2)

    print('== 具体値の投入')
    # ps_ref_* に入るのはオペレーションIDで、参照先の値は読み取り時に引かれる。
    # よって投入順は問わないが、分かりやすさのため参照先から入れる
    ids['rows_o'] = insert_rows(SHEET_O, info_o, operation_rows())
    ids['rows_n'] = insert_rows(SHEET_N, info_n, noitem_rows())
    ids['rows_h'] = insert_rows(SHEET_H, info_h, horizontal_rows())
    ids['rows_v'] = insert_rows(SHEET_V, info_v, vertical_rows(info_v))
    ids['rows_g'] = insert_rows(SHEET_G, info_g, hostgroup_rows())
    ids['rows_gv'] = insert_rows(SHEET_GV, info_gv, hostgroup_vertical_rows(info_gv))
    save_ids(ids)

    print('== ホストグループの展開(hostgroup-split バックヤード)を待つ')
    for menu, expect in ((SUBST_G, HG_EXPECT_SV_ROWS), (SUBST_GV, HG_V_EXPECT_SV_ROWS)):
        sv_rows = wait_split(menu, expect)
        if sv_rows:
            print('  %s に %d件(展開後)' % (menu, len(sv_rows)))
        else:
            # 展開されていなくても代入値自動登録設定そのものは登録できる(項目は
            # メニュー定義から出るため)。テスト側が skip して気付けるので中断はしない
            print('  !! %s が展開されていない(hostgroup-split バックヤード未稼働?)。'
                  'ホストグループ関連のテストは skip する' % menu)

    print('== Movement変数(vars-listup バックヤード)を待つ')
    if not wait_pulldown(AUTOREG_L, 'variable_name', 'pytest_'):
        print('!! Movement変数が登録されていない(vars-listup バックヤード未稼働)。'
              '代入値自動登録設定は投入できない')
        sys.exit(3)

    # 1つのドライバで失敗しても残りは投入したいので、まとめて try で囲む
    todo = [
        ('autoreg_L', '代入値自動登録設定(Legacy/横)',
         (AUTOREG_L, 'pytest横', 'pytest-mvmt-L1', 'pytest_', PLAN_STD)),
        ('autoreg_L_n', '代入値自動登録設定(Legacy/項目なし)',
         (AUTOREG_L, 'pytest項目なし', 'pytest-mvmt-L1', 'pytest_', PLAN_NOITEM)),
        # 縦は**横と同じ Movement**(L1)に載せる。登録経路は (オペレーション, Movement) を
        # 1組しか流さないので、横だけの Movement が選ばれると縦シートを1件も通らない。
        # 変数は `pytest_v_` 系にして MSG-10430(同一Movementでの重複)を避ける(段階2 の VARS_V)
        ('autoreg_L_v', '代入値自動登録設定(Legacy/縦)',
         (AUTOREG_L, 'pytest縦', 'pytest-mvmt-L1', 'pytest_v_', PLAN_VERTICAL, True)),
        # ホストグループ利用シート。項目は横シートと同じなので PLAN_STD を使い回し、
        # 変数だけ `pytest_g_` 系にして MSG-10430 を避ける(段階2 の VARS_G)。
        # Movement も横と同じ L1 — 登録経路は (オペレーション, Movement) を1組しか
        # 流さないので、別 Movement にすると登録経路がこのシートを通らない
        ('autoreg_L_g', '代入値自動登録設定(Legacy/ホストグループ)',
         (AUTOREG_L, 'pytestホストグループ', 'pytest-mvmt-L1', 'pytest_g_', PLAN_STD)),
        # ホストグループ利用 × 縦。項目検索プレフィクスは `pytestHG縦`
        # (`pytestホストグループ` を部分文字列として含まない名前にしてある)。
        # 変数は `pytest_gv_` 系、Movement は横HG・縦と同じ L1、vertical=True
        ('autoreg_L_gv', '代入値自動登録設定(Legacy/ホストグループ×縦)',
         (AUTOREG_L, 'pytestHG縦', 'pytest-mvmt-L1', 'pytest_gv_', PLAN_HG_VERTICAL, True)),
        ('autoreg_P', '代入値自動登録設定(Pioneer/横)',
         (AUTOREG_P, 'pytest横', 'pytest-mvmt-P1', 'pytest_', PLAN_STD)),
        ('autoreg_P_n', '代入値自動登録設定(Pioneer/項目なし)',
         (AUTOREG_P, 'pytest項目なし', 'pytest-mvmt-P1', 'pytest_', PLAN_NOITEM)),
        # Pioneer も Movement は1つ(P1)なので、これで読み取り経路と登録経路の両方が縦を通る。
        # `複数行` は V_ANSP_COLUMN_LIST が MultiTextColumn を除外するため
        # 項目プルダウンに出ず、autoreg_rows がスキップする(Legacy より1件少ない)
        ('autoreg_P_v', '代入値自動登録設定(Pioneer/縦)',
         (AUTOREG_P, 'pytest縦', 'pytest-mvmt-P1', 'pytest_v_', PLAN_VERTICAL, True)),
        # ホストグループ利用シートも**3ドライバとも**設定を作る。展開先(`_SV`)を読むこと自体は
        # ドライバ共通の実装だが、「実装が共通だから1ドライバで足りる」は実装の話でしかないので、
        # 3ドライバ × (HG横 / HG×縦) を実データで通す。変数は Legacy と同じ
        # `pytest_g_` / `pytest_gv_` 系(Movement が別なので変数名は重複してよい)
        ('autoreg_P_g', '代入値自動登録設定(Pioneer/ホストグループ)',
         (AUTOREG_P, 'pytestホストグループ', 'pytest-mvmt-P1', 'pytest_g_', PLAN_STD)),
        ('autoreg_P_gv', '代入値自動登録設定(Pioneer/ホストグループ×縦)',
         (AUTOREG_P, 'pytestHG縦', 'pytest-mvmt-P1', 'pytest_gv_', PLAN_HG_VERTICAL, True)),
        ('autoreg_R', '代入値自動登録設定(LegacyRole/横)',
         (AUTOREG_R, 'pytest横', 'pytest-mvmt-R1', 'pytest_r_', PLAN_ROLE)),
        # generated フィクスチャは DF_LEGACY_ROLE_DRIVER_ID で read_val_assign するため、
        # LegacyRole に縦シートが無いと INT-3 が skip する
        ('autoreg_R_v', '代入値自動登録設定(LegacyRole/縦)',
         (AUTOREG_R, 'pytest縦', 'pytest-mvmt-R1', 'pytest_r_', PLAN_ROLE_VERTICAL, True)),
        ('autoreg_R_g', '代入値自動登録設定(LegacyRole/ホストグループ)',
         (AUTOREG_R, 'pytestホストグループ', 'pytest-mvmt-R1', 'pytest_r_', PLAN_ROLE_HG)),
        ('autoreg_R_gv', '代入値自動登録設定(LegacyRole/ホストグループ×縦)',
         (AUTOREG_R, 'pytestHG縦', 'pytest-mvmt-R1', 'pytest_r_', PLAN_ROLE_HG_VERTICAL, True)),
        ('autoreg_R_n', '代入値自動登録設定(LegacyRole/項目なし)',
         (AUTOREG_R, 'pytest項目なし', 'pytest-mvmt-R1', 'pytest_r_', PLAN_ROLE_NOITEM)),
    ]
    for key, title, params in todo:
        print('== %s' % title)
        try:
            ids[key] = autoreg_rows(*params)
        except RuntimeError as e:
            print('  !! %s' % e)
        save_ids(ids)

    show(ids)
    counts = (SHEET_O, SHEET_N, SHEET_H, SHEET_V, SHEET_G, SUBST_G, SHEET_GV, SUBST_GV,
              AUTOREG_L, AUTOREG_P, AUTOREG_R)
    print(json.dumps({m: len(find_active(m)) for m in counts}, ensure_ascii=False))


if __name__ == '__main__':
    main()