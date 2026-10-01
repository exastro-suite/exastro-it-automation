"""段階5: 作成済みパラメータシートの「正規表現」を明示的に埋め直す(ITA 2.9.0 の不具合回避)。"""
import sys
import time

from ita import get, post
from lib import find, show

SHEETS = ('pytest_ps_ope', 'pytest_ps_noitem', 'pytest_ps_h', 'pytest_ps_v',
          'pytest_ps_hg', 'pytest_ps_hg_v')
ANY_REGEX = '.*'
HISTORY = 'menu_creation_history'

REGEX_KEY = {
    'SingleTextColumn': 'single_string_regular_expression',
    'MultiTextColumn': 'multi_string_regular_expression',
}
CLASS_BY_ID = {}


def load_class_map(define):
    for c in define['column_class_list']:
        CLASS_BY_ID[c['column_class_id']] = c['column_class_name']


def build_edit_body(define):
    """GET /create/define/{rest}/ の結果から `type: edit` のボディを組み立てる。"""
    menu = dict(define['menu_info']['menu'])
    columns = define['menu_info'].get('column') or {}

    menu_body = {
        'menu_create_id': menu['menu_create_id'],
        'menu_name': menu['menu_name'],
        'menu_name_rest': menu['menu_name_rest'],
        'sheet_type': menu['sheet_type'],
        'display_order': menu['display_order'],
        'description': menu.get('description'),
        'remarks': menu.get('remarks'),
        'vertical': 'True' if menu.get('vertical') == '1' else 'False',
        'hostgroup': 'True' if menu.get('hostgroup') == '1' else 'False',
        'menu_group_for_input': menu.get('menu_group_for_input'),
        'menu_group_for_subst': menu.get('menu_group_for_subst'),
        'menu_group_for_ref': menu.get('menu_group_for_ref'),
        'role_list': menu.get('role_list') or [],
        'last_update_date_time': menu['last_update_date_time'],   # 楽観ロック
    }
    if menu.get('unique_constraint'):
        menu_body['unique_constraint'] = menu['unique_constraint']

    column_body = {}
    changed = []
    # 項目0個のシート(`pytest_ps_noitem`)は `menu` に `columns` キー自体が無い。
    # `changed` が空のまま返るので main() 側でスキップされる。
    for i, key in enumerate(menu.get('columns') or [], 1):   # c1..cN を "1".."N" に詰め替える
        col = dict(columns[key])
        klass = CLASS_BY_ID[col['column_class_id']]
        col['column_class'] = klass                   # ID ではなく名前で渡す
        col['required'] = 'True' if col.get('required') == '1' else 'False'
        col['uniqued'] = 'True' if col.get('uniqued') == '1' else 'False'
        for drop in ('column_class_id', 'group_id', 'group_name', 'pulldown_selection'):
            col.pop(drop, None)

        regex_key = REGEX_KEY.get(klass)
        if regex_key and not col.get(regex_key):
            col[regex_key] = ANY_REGEX
            changed.append(col['item_name_rest'])
        column_body[str(i)] = col

    return {'type': 'edit', 'menu': menu_body, 'column': column_body, 'group': {}}, changed


def latest_history(menu_name):
    rows = [r['parameter'] for r in find(HISTORY)
            if r['parameter'].get('menu_name') == menu_name]
    rows.sort(key=lambda p: p.get('last_update_date_time') or '')
    return rows[-1] if rows else None


def wait_done(menu_name, timeout=900, interval=15):
    """『パラメータシート作成履歴』の最新が完了/失敗になるまで待つ。

    `/menu/{rest}/info/` は既存メニューなら即返るので待機判定に使えない。
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = (latest_history(menu_name) or {}).get('status')
        if status and status not in ('未実行', '実行中'):
            print('   %s: 履歴の状態=%s' % (menu_name, status))
            return status == '完了'
        print('   %s 反映待ち... (状態=%s)' % (menu_name, status))
        time.sleep(interval)
    return False


def main():
    edited = []
    for rest in SHEETS:
        define = get('/create/define/%s/' % rest)['data']
        if not CLASS_BY_ID:
            load_class_map(define)
        menu_name = define['menu_info']['menu']['menu_name']
        body, changed = build_edit_body(define)
        if not changed:
            print('%s: 正規表現は既に設定済み。スキップ' % rest)
            continue
        print('%s: 正規表現を設定するカラム = %s' % (rest, changed))
        res = post('/create/define/execute/', body)
        if not isinstance(res.get('data'), dict):
            print('編集に失敗 %s:' % rest)
            show(res)
            sys.exit(1)
        print('  編集を登録 history=%s' % res['data'].get('history_id'))
        edited.append((rest, menu_name))

    for rest, menu_name in edited:
        print('%s: %s' % (rest, '反映OK' if wait_done(menu_name) else 'タイムアウト'))
        for col in get('/create/define/%s/' % rest)['data']['menu_info']['column'].values():
            for k in REGEX_KEY.values():
                if k in col:
                    print('   %-10s %s = %r' % (col['item_name_rest'], k, col[k]))


if __name__ == '__main__':
    main()