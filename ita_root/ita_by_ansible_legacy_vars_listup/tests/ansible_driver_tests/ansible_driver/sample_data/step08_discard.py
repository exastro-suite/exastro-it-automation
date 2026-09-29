"""段階8: 廃止パターンを作る(機器 pytest-host-Z / オペレーション pytest-ope-disused を廃止)。

`python3 step08_discard.py restore` で**廃止を戻す**(Restore)。
シートを作り直して具体値を入れ直すときは、廃止した TPF/CPF がプルダウンから消えていて
`利用できない値です。(入力値:TPF_pytest_drop)` で登録できないので、
restore → 段階7 → 段階9 → もう一度この段階 の順で回す。
"""
import sys

from ita import post
from lib import find, pk_rest, show

TARGETS = [
    ('device_list', 'host_name', 'pytest-host-Z'),
    ('operation_list', 'operation_name', 'pytest-ope-disused'),
    # プルダウンの参照先を廃止して「ID変換失敗 → レコード破棄」を作る
    ('template_list', 'template_embedded_variable_name', 'TPF_pytest_drop'),
    ('file_list', 'file_embedded_variable_name', 'CPF_pytest_drop'),
]


def main():
    restore = len(sys.argv) > 1 and sys.argv[1] == 'restore'
    type_name = 'Restore' if restore else 'Discard'
    done_flag = '0' if restore else '1'
    for menu, name_col, name in TARGETS:
        pk = pk_rest(menu)
        target = None
        for row in find(menu):                     # 廃止済みも見たいので find_active は使わない
            if row['parameter'].get(name_col) == name:
                target = row['parameter']
        if not target:
            print('見つからない: %s の %s' % (menu, name))
            continue
        if target.get('discard') == done_flag:
            print('既に%s済み: %s' % ('復活' if restore else '廃止', name))
            continue
        body = [{'parameter': {pk: target[pk],
                               'last_update_date_time': target['last_update_date_time']},
                 'type': type_name}]
        res = post('/menu/%s/maintenance/all/' % menu, body)
        print('%s %s -> %s' % (type_name, name, res.get('result')))
        if res.get('result') != '000-00000':
            show(res)


if __name__ == '__main__':
    main()