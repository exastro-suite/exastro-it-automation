"""投入処理の共通ヘルパ。作成したIDは ids.json に追記して冪等に扱う。"""
import base64
import json
import os

from ita import get, post

IDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ids.json')


def load_ids():
    if os.path.exists(IDS_PATH):
        with open(IDS_PATH, encoding='utf-8') as fp:
            return json.load(fp)
    return {}


def save_ids(ids):
    with open(IDS_PATH, 'w', encoding='utf-8') as fp:
        json.dump(ids, fp, ensure_ascii=False, indent=2, sort_keys=True)


def b64(text):
    if isinstance(text, str):
        text = text.encode('utf-8')
    return base64.b64encode(text).decode()


def register(menu, rows):
    """rows = [{'parameter': {...}, 'file': {...}}] を Register で投入し IdList を返す。"""
    body = [{'parameter': r['parameter'], 'file': r.get('file', {}), 'type': 'Register'}
            for r in rows]
    res = post('/menu/%s/maintenance/all/' % menu, body)
    if not isinstance(res.get('data'), dict) or 'IdList' not in res['data']:
        raise RuntimeError('%s の登録に失敗: %s' % (menu, json.dumps(res, ensure_ascii=False)[:3000]))
    return res['data']['IdList']


def find(menu, filter_body=None):
    res = post('/menu/%s/filter/' % menu, filter_body or {})
    if res.get('status_code') not in (None, '000-00000'):
        raise RuntimeError('%s の検索に失敗: %s' % (menu, json.dumps(res, ensure_ascii=False)[:1200]))
    return res['data']


def find_active(menu, filter_body=None):
    """廃止(`discard == '1'`)を除いた行だけ返す。

    filter API は**廃止済みの行も返す**ので、「既存かどうか」の冪等判定にはこちらを使う。
    廃止した行を既存と数えると、作り直したときに再投入されなくなる。
    """
    return [r for r in find(menu, filter_body) if r['parameter'].get('discard') != '1']


def pick(menu, key, value):
    """指定カラムが value の行を1件返す(無ければ None)。"""
    for row in find(menu):
        if row['parameter'].get(key) == value:
            return row
    return None


def pk_rest(menu):
    """メニューのPKの REST 名を引く(Update / Discard に必要)。"""
    return get('/menu/%s/info/' % menu)['data']['menu_info']['pk_column_name_rest']


def rest_of(info, col_name):
    """物理カラム名から REST 名を引く(ホスト列/オペレーション列の特定用)。"""
    for c in info['column_info'].values():
        if c.get('col_name') == col_name:
            return c['column_name_rest']
    return None


def show(obj, limit=3000):
    print(json.dumps(obj, ensure_ascii=False, indent=2)[:limit])