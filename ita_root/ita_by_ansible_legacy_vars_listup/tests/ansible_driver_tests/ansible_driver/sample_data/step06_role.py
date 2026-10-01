"""段階6: LegacyRole 用のロールパッケージ/Movement/紐付を登録する。"""
import io
import zipfile

from ita import get
from lib import b64, find_active, load_ids, pick, register, save_ids, show

ROLE_PKG = 'pytest_role_pkg'
ROLE_NAME = 'pytest_role'
MOVEMENT_R = 'pytest-mvmt-R1'

TASKS_MAIN = """---
- name: pytest role std
  debug:
    msg: "std={{ pytest_r_std }}"

- name: pytest role list
  debug:
    msg: "{{ item }}"
  with_items: "{{ pytest_r_list }}"

- name: pytest role array
  debug:
    msg: "{{ item.pytest_r_member1 }} / {{ item.pytest_r_member2 }}"
  with_items: "{{ pytest_r_array }}"
"""

# defaults の構造が変数の型を決める。
#   pytest_r_std   -> 一般変数
#   pytest_r_list  -> 複数具体値(LIST)      … 代入順序が必要
#   pytest_r_array -> 多次元配列(M_ARRAY)   … メンバー変数が必要
DEFAULTS_MAIN = """---
pytest_r_std: ""
pytest_r_list:
  - ""
pytest_r_array:
  - pytest_r_member1: ""
    pytest_r_member2: ""
"""


def build_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('roles/%s/tasks/main.yml' % ROLE_NAME, TASKS_MAIN)
        zf.writestr('roles/%s/defaults/main.yml' % ROLE_NAME, DEFAULTS_MAIN)
    return buf.getvalue()


def main():
    ids = load_ids()

    row = pick('role_package_list', 'role_package_name', ROLE_PKG)
    if row:
        ids['role_pkg'] = row['parameter']['item_no']
        print('既存のロールパッケージを使う:', ids['role_pkg'])
    else:
        ids['role_pkg'] = register('role_package_list', [{
            'parameter': {
                'role_package_name': ROLE_PKG,
                'zip_format_role_package_file': '%s.zip' % ROLE_PKG,
                'target_linux': '*',
                'python_necessary': '*',
                'description': 'pytest(結合テスト)用。一般変数/複数具体値/多次元配列を含む',
                'discard': '0',
            },
            'file': {'zip_format_role_package_file': b64(build_zip())},
        }])[0]
        print('ロールパッケージを登録:', ids['role_pkg'])
    save_ids(ids)

    row = pick('movement_list_ansible_role', 'movement_name', MOVEMENT_R)
    if row:
        ids['mvmt_R1'] = row['parameter']['movement_id']
    else:
        ids['mvmt_R1'] = register('movement_list_ansible_role', [{'parameter': {
            'movement_name': MOVEMENT_R,
            'host_specific_format': 'IP',
            'remarks': 'pytest(結合テスト)用',
            'discard': '0',
        }}])[0]
    print('Movement:', ids['mvmt_R1'])
    save_ids(ids)

    # ロール紐付はロールパッケージの解析結果(V_ANSR_ROLE)が要るので、選択肢に出るまで待つ
    roles = get('/menu/movement_role_link/info/pulldown/')['data'].get('role_package_name_role_name', {})
    target = None
    for name in roles.values():
        if name.startswith(ROLE_PKG):
            target = name
    if not target:
        print('!! ロールが選択肢に出ていない(ロールパッケージ解析待ち)。少し待って再実行する')
        return

    if any(r['parameter'].get('movement') == MOVEMENT_R for r in find_active('movement_role_link')):
        print('既存の Movement-ロール紐付を使う')
    else:
        ids['link_R1'] = register('movement_role_link', [{'parameter': {
            'movement': MOVEMENT_R,
            'role_package_name_role_name': target,
            'include_order': '1',
            'remarks': 'pytest(結合テスト)用',
            'discard': '0',
        }}])[0]
        print('Movement-ロール紐付を登録:', ids['link_R1'])
    save_ids(ids)
    show(ids)


if __name__ == '__main__':
    main()