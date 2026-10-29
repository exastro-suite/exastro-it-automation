"""段階4: パラメータシート(横/縦/オペレーションのみ/項目なし)を定義・作成する。

作成自体はバックヤード(menu-create)が非同期に行うので、
メニューとして引けるようになるまでポーリングする。

パラメータシート参照は参照先が実体化してからでないと定義できないため2波に分ける。
"""
import sys
import time

from ita import get, post
from lib import find_active, load_ids, save_ids, show

ROLE = '_ws1-admin'                 # 対象WSの admin ロール名に合わせる
SHEET_HOST_OPE = 'パラメータシート（ホスト/オペレーションあり）'
SHEET_OPE = 'パラメータシート（オペレーションあり）'      # ホスト列を持たない

PULLDOWN_ASTERISK = '5011008'       # T_MENU_SELECT_1 の「*-(ブランク)」
PULLDOWN_HOST = '5011004'           # 機器一覧のホスト名(T_ANSC_DEVICE)
PULLDOWN_CPF = '5011005'            # ファイル管理のファイル埋込変数名
PULLDOWN_TPF = '5011006'            # テンプレート管理のテンプレート埋込変数名

# ホスト名プルダウンの「参照項目」。指定した順に <項目>_ref_1, <項目>_ref_2 が自動生成される
#   login_user     → ps_host_ref_1  項目名「ユーザ」        IDColumn(7)
#   login_password → ps_host_ref_2  項目名「パスワード」    PasswordIDColumn(25) = センシティブ
HOST_REFERENCE_ITEM = ['login_user', 'login_password']

# パラメータシート参照の参照先(第1波のシートの項目)。GET /create/define/ の
# parameter_sheet_reference_list の select_full_name と一致させる
REF_STD = '代入値自動登録用:pytestオペレーションパラメータシート:パラメータ/文字列'
REF_PW = '代入値自動登録用:pytestオペレーションパラメータシート:パラメータ/パスワード列'

WAVE1 = {
    'ps_ope': {
        'menu_name': 'pytestオペレーションパラメータシート',
        'menu_name_rest': 'pytest_ps_ope',
        'sheet_type': SHEET_OPE,
        'vertical': 'False',
        'columns': [
            ('文字列', 'po_std', 'SingleTextColumn', {}),
            ('パスワード列', 'po_pw', 'PasswordColumn', {}),
        ],
    },
    'ps_noitem': {
        'menu_name': 'pytest項目なしパラメータシート',
        'menu_name_rest': 'pytest_ps_noitem',
        'sheet_type': SHEET_HOST_OPE,
        'vertical': 'False',
        'columns': [],      # 0個。menu-create が「(項目なし)」項目を作る
    },
}

WAVE2 = {
    'ps_h': {
        'menu_name': 'pytest横パラメータシート',
        'menu_name_rest': 'pytest_ps_h',
        'sheet_type': SHEET_HOST_OPE,
        'vertical': 'False',
        'columns': [
            ('文字列', 'ps_std', 'SingleTextColumn', {}),
            ('パスワード列', 'ps_pw', 'PasswordColumn', {}),
            ('ファイル', 'ps_file', 'FileUploadColumn', {}),
            ('プルダウン', 'ps_id', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_ASTERISK}),
            ('複数行', 'ps_multi', 'MultiTextColumn', {}),
            ('空値', 'ps_empty', 'SingleTextColumn', {}),
            ('テンプレート埋込', 'ps_tpl', 'SingleTextColumn', {}),
            # TPF/CPF プルダウン → 値が '{{ TPF_x }}' / '{{ CPF_x }}' に包まれる分岐
            ('TPF選択', 'ps_tpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択', 'ps_cpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_CPF}),
            # 参照先を段階8で廃止 → ID変換失敗 → レコードごと破棄される分岐
            ('TPF選択廃止用', 'ps_tpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択廃止用', 'ps_cpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_CPF}),
            # 参照項目付きプルダウン → ps_host_ref_1 / ps_host_ref_2 が派生する
            ('ホスト選択', 'ps_host', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_HOST,
              'reference_item': HOST_REFERENCE_ITEM}),
            # パラメータシート参照 → JsonIDColumn(21) / JsonPasswordIDColumn(26)
            ('シート参照文字列', 'ps_ref_std', 'ParameterSheetReference',
             {'reference_name': REF_STD}),
            ('シート参照パスワード', 'ps_ref_pw', 'ParameterSheetReference',
             {'reference_name': REF_PW}),
            ('整数', 'ps_num', 'NumColumn', {}),
            ('小数', 'ps_float', 'FloatColumn', {}),
            ('リンク', 'ps_link', 'HostInsideLinkTextColumn', {}),
        ],
    },
    'ps_v': {
        'menu_name': 'pytest縦パラメータシート',
        'menu_name_rest': 'pytest_ps_v',
        'sheet_type': SHEET_HOST_OPE,
        'vertical': 'True',           # バンドル(縦) = INPUT_ORDER 列ができる
        # 横シート(ps_h)と**同じカラムクラス構成**にする。getCMDBdata の分岐は
        # 縦専用(:998-1029)と横専用(:1030-1060)に分かれており、実テーブルの形も
        # (INPUT_ORDER 付き / バンドル行) 違うので、クラス別の値の作り方は
        # 縦でも実データで通しておく。
        'columns': [
            ('文字列', 'pv_std', 'SingleTextColumn', {}),
            ('パスワード列', 'pv_pw', 'PasswordColumn', {}),
            ('ファイル', 'pv_file', 'FileUploadColumn', {}),
            ('プルダウン', 'pv_id', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_ASTERISK}),
            ('複数行', 'pv_multi', 'MultiTextColumn', {}),
            ('空値', 'pv_empty', 'SingleTextColumn', {}),
            ('テンプレート埋込', 'pv_tpl', 'SingleTextColumn', {}),
            # → "'{{ TPF_x }}'" / "'{{ CPF_x }}'" 括り(縦側のコピー :1023-1025)
            ('TPF選択', 'pv_tpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択', 'pv_cpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_CPF}),
            # 参照先を段階8で廃止 → ID変換失敗 → レコード破棄(縦側のコピー :1026-1027)
            ('TPF選択廃止用', 'pv_tpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択廃止用', 'pv_cpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_CPF}),
            # 参照項目付きプルダウン → pv_host_ref_1 / pv_host_ref_2 が派生する
            ('ホスト選択', 'pv_host', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_HOST,
              'reference_item': HOST_REFERENCE_ITEM}),
            ('シート参照文字列', 'pv_ref_std', 'ParameterSheetReference',
             {'reference_name': REF_STD}),
            ('シート参照パスワード', 'pv_ref_pw', 'ParameterSheetReference',
             {'reference_name': REF_PW}),
            ('整数', 'pv_num', 'NumColumn', {}),
            ('小数', 'pv_float', 'FloatColumn', {}),
            ('リンク', 'pv_link', 'HostInsideLinkTextColumn', {}),
        ],
    },
    'ps_hg': {
        'menu_name': 'pytestホストグループパラメータシート',
        'menu_name_rest': 'pytest_ps_hg',
        'sheet_type': SHEET_HOST_OPE,
        'vertical': 'False',
        # ホストグループ利用=有。入力用メニューのホスト列に `[HG]<ホストグループ名>` を選べる
        'hostgroup': 'True',
        # 横シート(ps_h)と**同じカラムクラス構成**にする。代入値自動登録設定が読むのは
        # 入力したテーブルではなく hostgroup-split が展開した `T_CMDB_<id>_SV` 側で、
        # 展開はカラムクラスごとに処理が分かれている
        # (FileUploadColumn は実ファイルのコピーまで行う: split_function.py の
        #  `copy_upload_file` / `chk_file_file_columns`)。
        # よって「展開後のテーブルでも各クラスの値が壊れずに運ばれる」ことを
        # INT-16 で見られるように、クラスを削らず横シートと揃える。
        'columns': [
            ('文字列', 'pg_std', 'SingleTextColumn', {}),
            ('パスワード列', 'pg_pw', 'PasswordColumn', {}),
            ('ファイル', 'pg_file', 'FileUploadColumn', {}),
            ('プルダウン', 'pg_id', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_ASTERISK}),
            ('複数行', 'pg_multi', 'MultiTextColumn', {}),
            ('空値', 'pg_empty', 'SingleTextColumn', {}),
            ('テンプレート埋込', 'pg_tpl', 'SingleTextColumn', {}),
            ('TPF選択', 'pg_tpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択', 'pg_cpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_CPF}),
            ('TPF選択廃止用', 'pg_tpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択廃止用', 'pg_cpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_CPF}),
            # ホスト列(ホストグループを選ぶ列)とは別の、機器一覧プルダウン + 参照項目
            ('ホスト選択', 'pg_host', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_HOST,
              'reference_item': HOST_REFERENCE_ITEM}),
            ('シート参照文字列', 'pg_ref_std', 'ParameterSheetReference',
             {'reference_name': REF_STD}),
            ('シート参照パスワード', 'pg_ref_pw', 'ParameterSheetReference',
             {'reference_name': REF_PW}),
            ('整数', 'pg_num', 'NumColumn', {}),
            ('小数', 'pg_float', 'FloatColumn', {}),
            ('リンク', 'pg_link', 'HostInsideLinkTextColumn', {}),
        ],
    },
    # ホストグループ利用=有 **かつ** バンドル(縦)=有。
    # この2つが同時に立つと
    #   - hostgroup-split が INPUT_ORDER も含めて展開する
    #     (`insert_data['INPUT_ORDER'] = ...`: split_function.py:899 / :1299-1302。
    #      横では :1302 で INPUT_ORDER を落とす)
    #   - 展開先テーブル(`T_CMDB_<id>_SV`)を読む代入値自動登録設定が
    #     「カラム代入順序 == 行の INPUT_ORDER」で行を選ぶ(SubValueAutoReg.py:998-999)
    # という**別々のコピー**同士が初めて噛み合う。さらに hostgroup-split は
    # 入力用/代入値自動登録用の VERTICAL が食い違うと get_target_menu で例外を投げ、
    # **そのWSの全ホストグループシートの展開が止まる**(split_function.py:114-122)。
    # カラムクラスは他の3シート(ps_h / ps_v / ps_hg)と**同じ17項目**に揃える。
    # 展開(クラスごとに処理が分かれる。FileUploadColumn は実ファイルのコピーまで行う)と
    # 縦の行選択(代入順序)が同時に効く経路でも、クラス別の値の作り方が壊れないことを
    # INT-16 で見られるようにするため。
    'ps_hg_v': {
        # 項目名は `代入値自動登録用:<メニュー名>:パラメータ/<項目名>` で引くので、
        # 他シートの検索プレフィクス(`pytest横` / `pytest縦` / `pytestホストグループ` /
        # `pytest項目なし`)を**部分文字列として含まない**名前にする(step07 の autoreg_rows 内 find_item)
        'menu_name': 'pytestHG縦パラメータシート',
        'menu_name_rest': 'pytest_ps_hg_v',
        'sheet_type': SHEET_HOST_OPE,
        'vertical': 'True',
        'hostgroup': 'True',
        'columns': [
            ('文字列', 'pgv_std', 'SingleTextColumn', {}),
            ('パスワード列', 'pgv_pw', 'PasswordColumn', {}),   # 展開後もセンシティブ
            # 展開時に実ファイルもコピーされる(split_function.py の copy_upload_file)。
            # 縦の展開コピーでもコピーされることは段階9 で実データを載せて確認する
            ('ファイル', 'pgv_file', 'FileUploadColumn', {}),
            ('プルダウン', 'pgv_id', 'IDColumn',                 # 展開後の行でも ID変換が効く
             {'pulldown_selection_id': PULLDOWN_ASTERISK}),
            ('複数行', 'pgv_multi', 'MultiTextColumn', {}),
            ('空値', 'pgv_empty', 'SingleTextColumn', {}),      # NULL連携ON で使う
            ('テンプレート埋込', 'pgv_tpl', 'SingleTextColumn', {}),
            ('TPF選択', 'pgv_tpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択', 'pgv_cpf', 'IDColumn', {'pulldown_selection_id': PULLDOWN_CPF}),
            ('TPF選択廃止用', 'pgv_tpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_TPF}),
            ('CPF選択廃止用', 'pgv_cpf_drop', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_CPF}),
            # ホスト列(ホストグループを選ぶ列)とは別の、機器一覧プルダウン + 参照項目
            ('ホスト選択', 'pgv_host', 'IDColumn',
             {'pulldown_selection_id': PULLDOWN_HOST,
              'reference_item': HOST_REFERENCE_ITEM}),
            ('シート参照文字列', 'pgv_ref_std', 'ParameterSheetReference',
             {'reference_name': REF_STD}),
            ('シート参照パスワード', 'pgv_ref_pw', 'ParameterSheetReference',
             {'reference_name': REF_PW}),
            ('整数', 'pgv_num', 'NumColumn', {}),
            ('小数', 'pgv_float', 'FloatColumn', {}),
            ('リンク', 'pgv_link', 'HostInsideLinkTextColumn', {}),
        ],
    },
}


def reference_ids(names):
    """GET /create/define/ の parameter_sheet_reference_list から選択項目IDを引く。"""
    common = get('/create/define/').get('data') or {}
    table = {r.get('select_full_name'): r.get('column_definition_id')
             for r in common.get('parameter_sheet_reference_list') or []}
    missing = [n for n in names if n not in table]
    if missing:
        print('パラメータシート参照の参照先が見つからない(第1波の実体化が未完了):')
        for name in missing:
            print('  欲しい: %s' % name)
        for name in sorted(table):
            print('  候補  : %s' % name)
        sys.exit(1)
    return {name: table[name] for name in names}


def build_body(sheet, refs):
    columns = {}
    for i, (name, rest, klass, extra) in enumerate(sheet['columns'], 1):
        col = {
            'item_name': name,
            'item_name_rest': rest,
            'column_class': klass,
            'display_order': i,
            'required': 'False',
            'uniqued': 'False',
            'description': 'pytest(結合テスト)用',
        }
        if klass == 'SingleTextColumn':
            col['single_string_maximum_bytes'] = 255
        elif klass == 'MultiTextColumn':
            col['multi_string_maximum_bytes'] = 4000
        elif klass == 'PasswordColumn':
            col['password_maximum_bytes'] = 255
        elif klass == 'FileUploadColumn':
            col['file_upload_maximum_bytes'] = 1048576
        elif klass == 'NumColumn':
            col['integer_minimum_value'] = -1000
            col['integer_maximum_value'] = 1000
        elif klass == 'FloatColumn':
            col['decimal_minimum_value'] = -1000
            col['decimal_maximum_value'] = 1000
            col['decimal_digit'] = 4
        elif klass == 'HostInsideLinkTextColumn':
            col['link_maximum_bytes'] = 255
        elif klass == 'ParameterSheetReference':
            col['parameter_sheet_reference_id'] = refs[extra['reference_name']]
        col.update({k: v for k, v in extra.items() if k != 'reference_name'})
        columns[str(i)] = col

    return {
        'type': 'create_new',
        'menu': {
            'menu_name': sheet['menu_name'],
            'menu_name_rest': sheet['menu_name_rest'],
            'sheet_type': sheet['sheet_type'],
            'display_order': 1000,
            'description': 'pytest(結合テスト)用',
            'remarks': 'pytest(結合テスト)用',
            'vertical': sheet['vertical'],
            # ホストグループ利用。有にすると menu-create が
            #   - `T_CMDB_<id>_SV` / `V_CMDB_<id>_SV`(展開後のテーブル)を追加で作り、
            #     代入値自動登録用・参照用メニューをそちらに向ける
            #   - 入力用メニューのホスト列を `V_HGSP_UQ_HOST_LIST`(`[H]…` / `[HG]…`)に向ける
            #   - `T_HGSP_SPLIT_TARGET` に (入力用メニュー, 代入値自動登録用メニュー) を登録する
            # ようになる。以降は hostgroup-split バックヤードが展開を担当する
            'hostgroup': sheet.get('hostgroup', 'False'),
            'menu_group_for_input': '入力用',
            'menu_group_for_subst': '代入値自動登録用',
            'menu_group_for_ref': '参照用',
            'role_list': [ROLE],
        },
        # 項目0個でも 'column' キー自体は必須(省略すると None.values() で500になる)
        'column': columns,
    }


def already_defined(menu_name_rest):
    for row in find_active('menu_definition_list'):
        if row['parameter'].get('menu_name_rest') == menu_name_rest:
            return row['parameter']
    return None


def wait_created(menu_name_rest, timeout=600, interval=15):
    """パラメータシートが実際に作られる(=メニューとして引ける)まで待つ。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if isinstance(get('/menu/%s/info/' % menu_name_rest).get('data'), dict):
            return True
        print('   待機中... %s' % menu_name_rest)
        time.sleep(interval)
    return False


def define(ids, sheets, refs):
    for key, sheet in sheets.items():
        rest = sheet['menu_name_rest']
        exist = already_defined(rest)
        if exist:
            ids[key] = exist.get('uuid') or exist.get('menu_create_id')
            print('既存の定義を使う %s = %s' % (rest, ids[key]))
        else:
            res = post('/create/define/execute/', build_body(sheet, refs))
            if not isinstance(res.get('data'), dict):
                print('定義に失敗 %s:' % rest)
                show(res)
                sys.exit(1)
            ids[key + '_history'] = res['data'].get('history_id')
            print('定義した %s history=%s' % (rest, ids[key + '_history']))
        save_ids(ids)

    for sheet in sheets.values():
        rest = sheet['menu_name_rest']
        ok = wait_created(rest)
        print('%s の作成: %s' % (rest, '完了' if ok else 'タイムアウト(バックヤード未稼働の可能性)'))
        if not ok:
            sys.exit(1)


def main():
    ids = load_ids()
    print('=== 第1波(参照先シート / 項目なしシート) ===')
    define(ids, WAVE1, {})
    print('=== 第2波(参照元シート) ===')
    define(ids, WAVE2, reference_ids([REF_STD, REF_PW]))
    show(ids)


if __name__ == '__main__':
    main()