"""段階10: 同一カラムに複数 Movement の代入値自動登録設定を紐づける。"""
from lib import find_active, load_ids, save_ids
from step07_rows_and_autoreg import AUTOREG_L, autoreg_rows

# pytest横パラメータシートの「文字列」を L2 にも紐づける(L1 は pytest_std で既存)。
# 同一 Movement 内では (変数, メンバー変数, 代入順序) が一意でなければならないので
# L2 側は L1 と別の変数(pytest_dup)を使う。
PLAN_SECOND_MOVEMENT = [
    ('文字列', 'dup', 'Value型', 'False', {}),
]


def main():
    ids = load_ids()
    ids['autoreg_L_multi'] = autoreg_rows(AUTOREG_L, 'pytest横', 'pytest-mvmt-L2',
                                          'pytest_', PLAN_SECOND_MOVEMENT)
    save_ids(ids)

    # 同一カラムに何件の設定が乗ったかを確認。
    # 縦シートの『文字列』は代入順序 1 と 4 で2件あるが Movement は同じ(L1)なので、
    # Movement を**重複除去**して数える(同じ Movement 2件は複数Movementではない)
    counts = {}
    for row in find_active(AUTOREG_L):
        p = row['parameter']
        counts.setdefault(p.get('menu_group_menu_item'), set()).add(p.get('movement'))
    for key, movements in sorted(counts.items()):
        mark = ' <== 複数Movement' if len(movements) > 1 else ''
        print('%-60s %s%s' % (key, sorted(movements), mark))


if __name__ == '__main__':
    main()