"""ITA Organization API の薄いクライアント(結合テスト用データ投入)。"""
import base64
import json
import os
import sys
import urllib.request

BASE = '{}/api/{}/workspaces/{}/ita'.format(
    os.environ['ITA_BASE_URL'].rstrip('/'),
    os.environ['ITA_ORGANIZATION_ID'],
    os.environ['ITA_WORKSPACE_ID'])
AUTH = base64.b64encode(
    '{}:{}'.format(os.environ['ITA_USER'], os.environ['ITA_PASSWORD']).encode()).decode()


def call(path, method='GET', body=None, timeout=180):
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Authorization', 'Basic ' + AUTH)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', 'replace')
        try:
            return json.loads(raw)      # ITA はエラーもJSONで返す。中身を見たいのでそのまま返す
        except Exception:
            return {'status': e.code, 'raw': raw[:2000]}


def get(path):
    return call(path)


def post(path, body):
    return call(path, 'POST', body)


def show(obj, limit=4000):
    print(json.dumps(obj, ensure_ascii=False, indent=2)[:limit])


if __name__ == '__main__':
    show(get(sys.argv[1]))          # 例: python3 ita.py /menu/device_list/info/