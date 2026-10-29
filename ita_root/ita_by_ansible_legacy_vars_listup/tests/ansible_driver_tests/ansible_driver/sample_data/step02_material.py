"""段階2: Playbook素材 / 対話種別・OS種別・対話ファイル素材 / テンプレート管理 / ファイル管理 を登録する。"""
import sys

from ita import post
from lib import b64, load_ids, pick, pk_rest, register, save_ids, show

# 横シートの代入値自動登録設定で使う一般変数。パラメータシートの項目と1対1で対応させる
# (step07 の PLAN_STD)。Playbook素材/対話ファイル素材に「書いてある」変数だけが
# Movement変数として抽出されるので、項目を増やしたらここも増やす。
VARS_H = [
    'pytest_std',        # 文字列(SingleTextColumn)
    'pytest_pw',         # パスワード列(PasswordColumn) → センシティブ
    'pytest_file',       # ファイル(FileUploadColumn)
    'pytest_empty',      # 空値 + NULL連携ON
    'pytest_id',         # プルダウン(IDColumn / *-(ブランク))
    'pytest_multi',      # 複数行(MultiTextColumn) → Key型
    'pytest_tpl',        # 具体値に {{ TPF_xxx }} を書いた文字列カラム
    'pytest_tpf',        # TPF選択(IDColumn / テンプレート埋込変数名) → '{{ TPF_x }}' 包み
    'pytest_cpf',        # CPF選択(IDColumn / ファイル埋込変数名)   → '{{ CPF_x }}' 包み
    'pytest_tpf_drop',   # 参照先テンプレートを廃止 → ID変換失敗 → レコードごと破棄
    'pytest_cpf_drop',   # 参照先ファイルを廃止     → ID変換失敗 → レコードごと破棄
    'pytest_host',       # ホスト選択(IDColumn / ホスト名) + 参照項目
    'pytest_host_user',  # 参照項目 host_name_ref_1 (IDColumn)
    'pytest_host_pw',    # 参照項目 host_name_ref_2 (PasswordIDColumn → センシティブ)
    'pytest_ref_std',    # パラメータシート参照 → JsonIDColumn
    'pytest_ref_pw',     # パラメータシート参照(参照先がパスワード) → JsonPasswordIDColumn
    'pytest_num',        # 整数(NumColumn) → 値が int で返る
    'pytest_float',      # 小数(FloatColumn)
    'pytest_link',       # リンク(HostInsideLinkTextColumn)
    'pytest_key',        # 『文字列』に **Key型**(具体値ではなく項目名を登録)で紐づける
    'pytest_noitem',     # 項目なしパラメータシート用
    'pytest_dup',        # 段階10(同一カラムに複数Movement)専用。他では使わない
]

# 縦(バンドル)シートの代入値自動登録設定で使う一般変数。**横シートと同じ変数は使えない**。
#   代入値自動登録設定は同一 Movement 内で (変数, メンバー変数, 代入順序) が一意でなければならず
#   (MSG-10430)、Legacy / Pioneer の変数は一般変数(= 代入順序を持てない)なので、
#   「同じ Movement に横と縦の両方を載せる」には**変数そのものを分けるしかない**。
#   LegacyRole は複数具体値変数の代入順序をずらして1変数で同居させている(step07 の PLAN_ROLE)。
# 同じ Movement に載せる理由: 登録経路(`get_data_from_parameter_sheet`)は
#   (オペレーション, Movement) を1組しか流さないので、横だけの Movement が選ばれると
#   縦シートを1件も通らない(step07 の `autoreg_L_v` / `autoreg_P_v`)。
# 末尾は PLAN_VERTICAL(step07)の変数名末尾と1対1で対応させる。
VARS_V = ['pytest_v_' + suffix for suffix in (
    'std', 'pw', 'file', 'empty', 'id', 'multi', 'tpl', 'tpf', 'cpf', 'tpf_drop', 'cpf_drop',
    'host', 'host_user', 'host_pw', 'ref_std', 'ref_pw', 'num', 'float', 'link',
    'vseq',          # 対応する INPUT_ORDER の行が無い代入順序(4)に割り当てる
)]

# ホストグループ利用シート(段階4 の `pytest_ps_hg`)の代入値自動登録設定で使う一般変数。
# このシートも**横シートと同じ Movement**(L1 / P1)に載せる(登録経路は
# (オペレーション, Movement) を1組しか流さないため)。よって横・縦と同じ理屈で
# 変数そのものを分けるしかない。項目構成は横シートと同じなので、
# 末尾は PLAN_STD(step07)の変数名末尾と1対1で対応させ、設定は PLAN_STD を使い回す。
VARS_G = ['pytest_g_' + suffix for suffix in (
    'std', 'pw', 'file', 'empty', 'id', 'multi', 'tpl', 'tpf', 'cpf', 'tpf_drop', 'cpf_drop',
    'host', 'host_user', 'host_pw', 'ref_std', 'ref_pw', 'num', 'float', 'link',
    'key',           # Key型
)]

# ホストグループ利用 **かつ** バンドル(縦)のシート(段階4 の `pytest_ps_hg_v`)用。
# 展開先テーブル(`T_CMDB_<id>_SV`)に INPUT_ORDER が載るのはこの組み合わせだけで、
#   - hostgroup-split 側: `insert_data['INPUT_ORDER'] = ...`(split_function.py:899 / :1299-1302)
#   - vars-listup 側: 「設定のカラム代入順序 == 行の INPUT_ORDER」(SubValueAutoReg.py:998-999)
# の2つが噛み合うのもここだけなので、専用のシートと変数を用意する。
# 横HG(VARS_G) / 縦(VARS_V) と同じ Movement(L1)に載せるので変数は分ける(MSG-10430)。
# 項目構成は他の3シートと同じ17項目(+派生2項目)に揃えてあるので、
# 末尾は VARS_G / PLAN_STD と同じ並びで1対1に対応させる(step07 の PLAN_HG_VERTICAL)。
VARS_G_V = ['pytest_gv_' + suffix for suffix in (
    'std', 'pw', 'file', 'empty', 'id', 'multi', 'tpl', 'tpf', 'cpf', 'tpf_drop', 'cpf_drop',
    'host', 'host_user', 'host_pw', 'ref_std', 'ref_pw', 'num', 'float', 'link',
    'key',           # Key型
)]

# 素材に書き出す変数。ここに書いてある変数だけが Movement変数として抽出される
VARS = VARS_H + VARS_V + VARS_G + VARS_G_V

PLAYBOOK_NAME = 'pytest_std_vars.yml'
PLAYBOOK_BODY = '---\n' + ''.join(
    '- name: pytest var %s\n  debug:\n    msg: "%s={{ %s }}"\n' % (v, v, v) for v in VARS
) + """- name: pytest template embedded
  template:
    src: "{{ TPF_pytest_tpl }}"
    dest: /tmp/pytest_tpf.txt
"""

DIALOG_TYPE = 'pytest-dialog-type'
OS_TYPE = 'pytest-os-type'
DIALOG_NAME = 'pytest_dialog.yml'
DIALOG_BODY = '---\n' + ''.join(
    '- exec: "echo %s={{ %s }}"\n  expect:\n    - "prompt> "\n' % (v, v) for v in VARS)

# テンプレート管理。TPF_pytest_drop は段階8で廃止して「ID変換失敗 → 破棄」の分岐を作る
TEMPLATE_VAR = 'TPF_pytest_tpl'
TEMPLATE_NAME = 'pytest_template.txt'
TEMPLATE_BODY = """pytest template body
tpl_inner={{ pytest_tpl_inner }}
tpl_inner2={{ pytest_tpl_inner2 }}
"""
# テンプレート管理の「変数定義」。**ファイル本文ではなくここが解析される**
TEMPLATE_VARS_DEF = 'pytest_tpl_inner: \npytest_tpl_inner2: '

TEMPLATE_DROP_VAR = 'TPF_pytest_drop'
TEMPLATE_DROP_NAME = 'pytest_template_drop.txt'
TEMPLATE_DROP_BODY = 'pytest template to be discarded\n'

# ファイル管理(CPF)。CPF_pytest_drop は段階8で廃止する
FILE_VAR = 'CPF_pytest_conf'
FILE_NAME = 'pytest_conf.txt'
FILE_BODY = 'pytest contents file\n'

FILE_DROP_VAR = 'CPF_pytest_drop'
FILE_DROP_NAME = 'pytest_conf_drop.txt'
FILE_DROP_BODY = 'pytest contents file to be discarded\n'


def ensure(ids, key, menu, match_col, match_value, parameter, file=None, id_col=None,
           update=False):
    """無ければ Register する。`update=True` なら既存行を Update で上書きする。

    VARS を増やすと Playbook素材 / 対話ファイル素材の**中身**が変わる。Register だけだと
    既存WSには新しい変数が入らず Movement変数にも出てこないので、この2つは毎回上書きする
    (素材の更新 → vars-listup が再抽出)。
    """
    row = pick(menu, match_col, match_value)
    if row:
        p = row['parameter']
        ids[key] = p[id_col] if id_col else p.get('item_no')
        if not update:
            print('既存を使う  %-16s %s = %s' % (menu, key, ids[key]))
            return ids[key]
        pk = pk_rest(menu)
        body = [{'parameter': dict(parameter, **{
                     pk: p[pk], 'last_update_date_time': p['last_update_date_time']}),
                 'file': file or {}, 'type': 'Update'}]
        res = post('/menu/%s/maintenance/all/' % menu, body)
        if res.get('result') != '000-00000':
            show(res)
            sys.exit(1)
        print('上書きした  %-16s %s = %s' % (menu, key, ids[key]))
        return ids[key]
    ids[key] = register(menu, [{'parameter': parameter, 'file': file or {}}])[0]
    print('登録した    %-16s %s = %s' % (menu, key, ids[key]))
    return ids[key]


def main():
    ids = load_ids()

    ensure(ids, 'playbook_L', 'playbook_files', 'playbook_name', PLAYBOOK_NAME, {
        'playbook_name': PLAYBOOK_NAME,
        'playbook_file': PLAYBOOK_NAME,
        'target_linux': '*',
        'python_necessary': '*',
        'description': 'pytest(結合テスト)用。一般変数のみを含む',
        'discard': '0',
    }, {'playbook_file': b64(PLAYBOOK_BODY)}, update=True)

    ensure(ids, 'dialog_type', 'dialog_type_list', 'dialog_type_name', DIALOG_TYPE, {
        'dialog_type_name': DIALOG_TYPE, 'discard': '0', 'remarks': 'pytest(結合テスト)用',
    })
    ensure(ids, 'os_type', 'os_type_master', 'os_type_name', OS_TYPE, {
        'os_type_name': OS_TYPE, 'sv': 'True', 'discard': '0', 'remarks': 'pytest(結合テスト)用',
    })
    ensure(ids, 'dialog_P', 'dialog_files', 'dialog_file', DIALOG_NAME, {
        'dialog_type': DIALOG_TYPE,
        'os_type': OS_TYPE,
        'dialog_file': DIALOG_NAME,
        'target_linux': '*',
        'python_necessary': '*',
        'description': 'pytest(結合テスト)用',
        'discard': '0',
    }, {'dialog_file': b64(DIALOG_BODY)}, update=True)

    ensure(ids, 'template', 'template_list', 'template_embedded_variable_name', TEMPLATE_VAR, {
        'template_embedded_variable_name': TEMPLATE_VAR,
        'template_files': TEMPLATE_NAME,
        'variable_definition': TEMPLATE_VARS_DEF,
        'discard': '0',
    }, {'template_files': b64(TEMPLATE_BODY)}, id_col='template_id')

    ensure(ids, 'template_drop', 'template_list', 'template_embedded_variable_name',
           TEMPLATE_DROP_VAR, {
               'template_embedded_variable_name': TEMPLATE_DROP_VAR,
               'template_files': TEMPLATE_DROP_NAME,
               'variable_definition': '',
               'discard': '0',
           }, {'template_files': b64(TEMPLATE_DROP_BODY)}, id_col='template_id')

    ensure(ids, 'cfile', 'file_list', 'file_embedded_variable_name', FILE_VAR, {
        'file_embedded_variable_name': FILE_VAR,
        'files': FILE_NAME,
        'remarks': 'pytest(結合テスト)用。CPF選択プルダウンの選択肢',
        'discard': '0',
    }, {'files': b64(FILE_BODY)}, id_col='file_id')

    ensure(ids, 'cfile_drop', 'file_list', 'file_embedded_variable_name', FILE_DROP_VAR, {
        'file_embedded_variable_name': FILE_DROP_VAR,
        'files': FILE_DROP_NAME,
        'remarks': 'pytest(結合テスト)用。段階8で廃止して ID変換失敗 を作る',
        'discard': '0',
    }, {'files': b64(FILE_DROP_BODY)}, id_col='file_id')

    save_ids(ids)
    show(ids)


if __name__ == '__main__':
    main()