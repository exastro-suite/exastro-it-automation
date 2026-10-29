"""段階1: 機器一覧・オペレーション・ホストグループを登録する。"""
from lib import find_active, load_ids, pick, register, save_ids, show

HOSTS = [
    ('pytest-host-A', '127.0.0.11'),
    ('pytest-host-B', '127.0.0.12'),
    ('pytest-host-C', '127.0.0.13'),
    ('pytest-host-Z', '127.0.0.19'),      # 段階9で廃止する
]
OPERATIONS = [
    ('pytest-ope-1', '2030/01/01 00:00:00'),
    ('pytest-ope-2', '2030/01/02 00:00:00'),
    ('pytest-ope-disused', '2030/01/03 00:00:00'),   # 段階9で廃止する
]

# ホストグループ(段階4 の `pytest_ps_hg` / 段階7 の具体値で使う)。
# 「ホストグループ利用=有」のパラメータシートは、入力用メニューのホスト列に
# `[HG]<ホストグループ名>` を選べる(プルダウンは `V_HGSP_UQ_HOST_LIST`)。
# その行は hostgroup-split バックヤードがメンバー機器ごとに分解して、
# **代入値自動登録用メニューの別テーブル**(`T_CMDB_<id>_SV`)へ書き込む。
# 代入値自動登録設定が読むのはこの `_SV` 側なので、
# 「入力した行」と「レコードになる行」が別テーブルになるのはこのパターンだけ。
HOSTGROUP = 'pytest-hg-1'
HOSTGROUP_MEMBERS = ['pytest-host-A', 'pytest-host-B']    # 1行が2ホストに展開される


def main():
    ids = load_ids()

    for name, ip in HOSTS:
        if pick('device_list', 'host_name', name):
            print('既存: %s' % name)
            continue
        ids['host_' + name] = register('device_list', [{'parameter': {
            'host_name': name,
            'ip_address': ip,
            'hw_device_type': 'SV',
            'connection_type': 'machine',
            'authentication_method': 'パスワード認証',
            'login_user': 'root',
            'login_password': 'dummy-password',
            'remarks': 'pytest integration',
            'discard': '0',
        }}])[0]
        print('登録: %s' % name)

    for name, scheduled in OPERATIONS:
        if pick('operation_list', 'operation_name', name):
            print('既存: %s' % name)
            continue
        ids['ope_' + name] = register('operation_list', [{'parameter': {
            'operation_name': name,
            'scheduled_date_for_execution': scheduled,
            'remarks': 'pytest integration',
            'discard': '0',
        }}])[0]
        print('登録: %s' % name)

    # 優先順位は必須ではない(NULL でも hostgroup-split は動く)
    if pick('hostgroup_management', 'hostgroup_name', HOSTGROUP):
        print('既存: %s' % HOSTGROUP)
    else:
        ids['hg_' + HOSTGROUP] = register('hostgroup_management', [{'parameter': {
            'hostgroup_name': HOSTGROUP,
            'remarks': 'pytest integration',
            'discard': '0',
        }}])[0]
        print('登録: %s' % HOSTGROUP)

    # ホストグループとメンバー機器の紐付。**オペレーションは指定しない** —
    # 空にすると全オペレーションが対象(`T_HGSP_HOST_LINK.OPERATION_ID` が NULL)になり、
    # オペレーションを増やしても紐付を足さずに済む
    linked = {(r['parameter'].get('hostgroup_name'), r['parameter'].get('hostname'))
              for r in find_active('host_link_list')}
    for host in HOSTGROUP_MEMBERS:
        if (HOSTGROUP, host) in linked:
            print('既存: %s → %s' % (HOSTGROUP, host))
            continue
        ids['hglink_%s' % host] = register('host_link_list', [{'parameter': {
            'hostgroup_name': HOSTGROUP,
            'hostname': host,
            'remarks': 'pytest integration',
            'discard': '0',
        }}])[0]
        print('登録: %s → %s' % (HOSTGROUP, host))

    save_ids(ids)
    show(ids)


if __name__ == '__main__':
    main()