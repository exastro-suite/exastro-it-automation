"""段階9: FileUploadColumn に実ファイルを載せる。"""
import time

from ita import get, post
from lib import b64, find_active, rest_of, show
from step07_rows_and_autoreg import (AUTOREG_R, HG_VALUE, SHEET_G, SHEET_GV, SUBST_G, SUBST_GV,
                                     autoreg_rows)

FILE_NAME = 'pytest_upload.txt'
FILE_BODY = 'pytest file A\n'

TARGET_HOST = 'pytest-host-A'
TARGET_OPE = '2030/01/01 00:00_pytest-ope-1'      # プルダウンの表示値

# (メニュー, FileUploadColumn の REST名, その行の INPUT_ORDER, ホスト列の値)
# 縦シートは『ファイル』のカラム代入順序を 3 にしてあるので、
# INPUT_ORDER=3 の行に載せないと代入値管理に出てこない(step07 の PLAN_VERTICAL)。
# ホストグループ利用シートは `[HG]…` の行に載せる。展開(hostgroup-split)は
# FileUploadColumn だけ実ファイルのコピーを伴う(`split_function.py` の
# `copy_upload_file` / `chk_file_file_columns`)ので、展開後のテーブルでも
# ファイル名が取れることをここで作っておく
TARGETS = [
    ('pytest_ps_h', 'ps_file', None, TARGET_HOST),
    ('pytest_ps_v', 'pv_file', '3', TARGET_HOST),
    (SHEET_G, 'pg_file', None, HG_VALUE),
    # ホストグループ利用 × 縦。展開のファイルコピーが**縦のコピー**でも動くことを作る。
    # 『ファイル』のカラム代入順序は 1(step07 の PLAN_HG_VERTICAL)なので INPUT_ORDER=1 の行に載せる
    (SHEET_GV, 'pgv_file', '1', HG_VALUE),
]

# INT-12 はドライバごとに parametrize されているので LegacyRole 側にも
# FileUploadColumn の設定が要る。代入順序は step07 の割り当て表どおり 4
PLAN_ROLE_FILE = [('ファイル', 'list', 'Value型', 'False', {'substitution_order': '4'})]


def upload(menu, column, input_order, host_value):
    info = get('/menu/%s/info/' % menu)['data']
    order_col = rest_of(info, 'INPUT_ORDER')
    host_col = rest_of(info, 'HOST_ID') or 'host_name'
    ope_col = rest_of(info, 'OPERATION_ID') or 'operation_name_select'
    target = None
    for row in find_active(menu):
        p = row['parameter']
        if p.get(host_col) != host_value or p.get(ope_col) != TARGET_OPE:
            continue
        if order_col and str(p.get(order_col)) != str(input_order):
            continue
        target = p
    if not target:
        print('%s: 対象行が見つからない' % menu)
        return
    if target.get(column):
        print('%s: 既にファイルあり: %s' % (menu, target[column]))
        return

    body = [{
        'parameter': {
            'uuid': target['uuid'],
            column: FILE_NAME,                    # ← ファイル名も必須
            'last_update_date_time': target['last_update_date_time'],
        },
        'file': {column: b64(FILE_BODY)},
        'type': 'Update',
    }]
    res = post('/menu/%s/maintenance/all/' % menu, body)
    print('%s: 更新 -> %s' % (menu, res.get('result')))
    if res.get('result') != '000-00000':
        show(res)
        return
    for row in find_active(menu):
        p = row['parameter']
        if p['uuid'] == target['uuid']:
            print('  %s = %r' % (column, p.get(column)))


def wait_split_file(column, menu=SUBST_G, timeout=1800, interval=20):
    """展開後のテーブル(`<入力用>_subst`)にファイル名が載るまで待つ。

    入力用メニューを更新すると `T_HGSP_SPLIT_TARGET.DIVIDED_FLG` が 0 に戻り、
    hostgroup-split が再度展開する。ファイルのコピーもそのときに行われるので、
    更新直後の展開結果を見るとファイル名が入っていないことがある。
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            rows = find_active(menu)
        except RuntimeError as e:
            print('  %s を引けない (%s)' % (menu, e))
            rows = []
        hit = [r['parameter'] for r in rows if r['parameter'].get(column)]
        if hit:
            print('  %s: %d件にファイルあり' % (menu, len(hit)))
            return hit
        print('  %s の再展開待ち (%d件中0件にファイル)' % (menu, len(rows)))
        time.sleep(interval)
    print('  !! %s にファイルが載らなかった(hostgroup-split 未稼働?)' % menu)
    return []


def main():
    for menu, column, input_order, host_value in TARGETS:
        upload(menu, column, input_order, host_value)
    print('== ホストグループの再展開(ファイルのコピー)を待つ')
    wait_split_file('pg_file')
    wait_split_file('pgv_file', SUBST_GV)
    # INT-12 はドライバごとに parametrize されているので、Legacy だけでは
    # Pioneer / LegacyRole が skip したままになる。Pioneer 分は段階7 の
    # PLAN_STD にある ('ファイル', 'file', …) で入っているので、
    # ここでは LegacyRole 分を足す
    print('== 代入値自動登録設定(LegacyRole/ファイル)')
    autoreg_rows(AUTOREG_R, 'pytest横', 'pytest-mvmt-R1', 'pytest_r_', PLAN_ROLE_FILE)


if __name__ == '__main__':
    main()