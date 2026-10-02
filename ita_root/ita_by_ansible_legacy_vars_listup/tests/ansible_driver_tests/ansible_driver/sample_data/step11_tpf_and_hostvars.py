"""段階11: vars-listup 固有の「実行時相当」変数刈り取り経路にデータを通す。"""
from ita import post
from lib import b64, find_active, pick, show

TEMPLATE_VAR = 'TPF_pytest_tpl'
TEMPLATE_NAME = 'pytest_template.txt'
TEMPLATE_BODY = """pytest template body
tpl_inner={{ pytest_tpl_inner }}
tpl_inner2={{ pytest_tpl_inner2 }}
"""
# ここ(変数定義)が解析対象。ファイル本文ではない
TEMPLATE_VARS_DEF = 'pytest_tpl_inner: \npytest_tpl_inner2: '

TARGET_HOST = 'pytest-host-A'
# AnscConst.DF_HOST_VAR_HED は2系で "" なので、接頭辞なしの {{ 変数名 }} が刈り取られる
HOST_EXTRA_ARGS = 'pytest_dev_var: "{{ pytest_dev_var }}"\n'


def update_template():
    row = pick('template_list', 'template_embedded_variable_name', TEMPLATE_VAR)
    if not row:
        print('テンプレート管理に %s が無い' % TEMPLATE_VAR)
        return
    p = row['parameter']
    print('現在の変数定義: %r' % p.get('variable_definition'))
    body = [{
        'parameter': {
            'template_id': p['template_id'],
            'template_embedded_variable_name': TEMPLATE_VAR,
            'template_files': TEMPLATE_NAME,
            'variable_definition': TEMPLATE_VARS_DEF,
            'last_update_date_time': p['last_update_date_time'],
        },
        'file': {'template_files': b64(TEMPLATE_BODY)},
        'type': 'Update',
    }]
    res = post('/menu/template_list/maintenance/all/', body)
    print('テンプレート管理の更新 -> %s' % res.get('result'))
    if res.get('result') != '000-00000':
        show(res)


def update_device():
    row = pick('device_list', 'host_name', TARGET_HOST)
    if not row:
        print('機器一覧に %s が無い' % TARGET_HOST)
        return
    p = row['parameter']
    body = [{
        'parameter': {
            'managed_system_item_number': p['managed_system_item_number'],
            'inventory_file_additional_option': HOST_EXTRA_ARGS,
            'last_update_date_time': p['last_update_date_time'],
        },
        'file': {},
        'type': 'Update',
    }]
    res = post('/menu/device_list/maintenance/all/', body)
    print('機器一覧の更新 -> %s' % res.get('result'))
    if res.get('result') != '000-00000':
        show(res)


def main():
    update_template()
    update_device()
    for row in find_active('template_list'):
        p = row['parameter']
        print('template %-16s vars=%r' % (p.get('template_embedded_variable_name'),
                                          p.get('variable_definition')))
    for row in find_active('device_list'):
        p = row['parameter']
        if p.get('inventory_file_additional_option'):
            print('device   %-16s extra=%r' % (p.get('host_name'),
                                               p.get('inventory_file_additional_option')))


if __name__ == '__main__':
    main()