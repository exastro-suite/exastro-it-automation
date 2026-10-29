"""段階3: Movement(Legacy/Pioneer)と素材紐付を登録する。"""
from lib import find_active, load_ids, pick, register, save_ids, show

MOVEMENTS_L = ['pytest-mvmt-L1', 'pytest-mvmt-L2']
MOVEMENTS_P = ['pytest-mvmt-P1']
PLAYBOOK_NAME = 'pytest_std_vars.yml'
DIALOG_TYPE = 'pytest-dialog-type'


def ensure_movement(ids, menu, name, key):
    row = pick(menu, 'movement_name', name)
    if row:
        ids[key] = row['parameter']['movement_id']
        print('既存を使う  %-30s %s = %s' % (menu, name, ids[key]))
        return ids[key]
    ids[key] = register(menu, [{'parameter': {
        'movement_name': name,
        'host_specific_format': 'IP',
        'remarks': 'pytest(結合テスト)用',
        'discard': '0',
    }}])[0]
    print('登録した    %-30s %s = %s' % (menu, name, ids[key]))
    return ids[key]


def ensure_link(ids, menu, key, parameter, match):
    for row in find_active(menu):
        if all(row['parameter'].get(k) == v for k, v in match.items()):
            ids[key] = row['parameter']['associated_item_no']
            print('既存を使う  %-30s %s = %s' % (menu, key, ids[key]))
            return ids[key]
    ids[key] = register(menu, [{'parameter': parameter}])[0]
    print('登録した    %-30s %s = %s' % (menu, key, ids[key]))
    return ids[key]


def main():
    ids = load_ids()

    for i, name in enumerate(MOVEMENTS_L, 1):
        ensure_movement(ids, 'movement_list_ansible_legacy', name, 'mvmt_L%d' % i)
    for i, name in enumerate(MOVEMENTS_P, 1):
        ensure_movement(ids, 'movement_list_ansible_pioneer', name, 'mvmt_P%d' % i)

    for i, name in enumerate(MOVEMENTS_L, 1):
        ensure_link(ids, 'movement_playbook_link', 'link_L%d' % i, {
            'movement': name, 'playbook_file': PLAYBOOK_NAME, 'include_order': '1',
            'remarks': 'pytest(結合テスト)用', 'discard': '0',
        }, {'movement': name, 'playbook_file': PLAYBOOK_NAME})

    for i, name in enumerate(MOVEMENTS_P, 1):
        ensure_link(ids, 'movement_dialogue_type_link', 'link_P%d' % i, {
            'movement': name, 'dialog_type': DIALOG_TYPE, 'include_order': '1',
            'remarks': 'pytest(結合テスト)用', 'discard': '0',
        }, {'movement': name, 'dialog_type': DIALOG_TYPE})

    save_ids(ids)
    show(ids)


if __name__ == '__main__':
    main()