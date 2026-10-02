#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License")
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
SubValueAutoReg 結合テストの共通基盤

利用側:
  - test_SubValueAutoReg_integration.py       (読み取り専用: INT-1〜INT-5、INT-13、INT-14、INT-17)
  - test_SubValueAutoReg_integration_write.py (登録経路: INT-6〜INT-9、INT-12、INT-15〜INT-17)

提供するもの
  - 実行ゲート/接続情報の解決(`gate_reason` / `resolve_env`)
  - 検証対象ワークスペースの明示(`target_from_env`)
  - データ不足の skip を fail に変える厳密モード(`skip_or_fail` / `INTEGRATION_STRICT`)
  - 独立オラクル用のヘルパ(`disused_ids` / `single_tpf_var`)
  - 縦(バンドル)/横シートの判定(`sheet_kinds`)
  - ワークスペース一覧(`list_workspaces`)
  - 使い捨てワークスペース(`DisposableWorkspace`)

フィクスチャ(`integration_env` / `app_context`)は conftest.py 側にある。

**接続情報はリポジトリに一切埋め込まない**。実行時に環境変数/環境変数ファイルから解決し、
解決できなければ理由付きで skip する。
"""

import json
import os
import re
import shutil
import time
import uuid

import pytest
from flask import g

# ======================================================================
# 実行ゲートと接続情報
# ======================================================================

# 結合テスト**専用**の環境変数は `INTEGRATION_` 接頭辞で揃えてある
# (製品コードが読む `DB_*` / `ENCRYPT_KEY` / `ITA_*` と区別できるようにするため)。

# 結合テストを実行するかどうかのスイッチ。既定(未設定)では skip する。
#   - pytest.ini で `-m "not integration"` を指定すると VSCode のテスト一覧から
#     ケースごと消えてしまい「存在しない」と誤読されるため、
#     収集はさせて **フィクスチャ側で skip** する方式にしている。
ENABLE_ENV = 'INTEGRATION_ENABLE'

# データが足りないことによる skip を fail に変えるスイッチ。
#   結合テストは「データが無ければ skip」で組んであるため、
#   生成SQLが全パラメータシートで0件になるような回帰が入っても
#   skip の山ができるだけで**1件も落ちない**(緑と誤読される)。
#   データを揃えた環境(tests/README.md の段階1〜11)では
#   skip は0件になるので、そこでは `INTEGRATION_STRICT=1` を付けて
#   実行ゲート以外の skip をすべて fail として扱う。
STRICT_ENV = 'INTEGRATION_STRICT'

# 検証対象ワークスペースを明示する環境変数。
#   **データ投入スクリプト(sample_data/ita.py)と同じ名前に揃えてある**。
#   投入とテストで別名にすると、投入したワークスペースとは違うワークスペースを
#   検証しても気付けない(自動探索が別のWSを拾う)。
ORGANIZATION_ID_ENV = 'ITA_ORGANIZATION_ID'
WORKSPACE_ID_ENV = 'ITA_WORKSPACE_ID'

# 接続情報を読む .env を明示する環境変数。
ENV_FILE_ENV = 'INTEGRATION_ENV_FILE'

# ストレージ(`STORAGEPATH`)のルートを明示する環境変数。
STORAGEPATH_ENV = 'INTEGRATION_STORAGEPATH'

# 接続情報を補うための環境変数ファイル(devcontainer の docker-compose 用 .env)
DEFAULT_ENV_FILES = (
    '/workspace/exastro-devcontainer/docker-compose/.env',
    '/workspace/.devcontainer/.env',
)

# DBConnectCommon / ky_decrypt が参照する環境変数
REQUIRED_ENV_KEYS = ('DB_HOST', 'DB_PORT', 'DB_DATABASE', 'DB_USER', 'DB_PASSWORD', 'ENCRYPT_KEY')

# pytest.ini の env が指すダミー値。これらは実環境の値に差し替える必要がある
DUMMY_ENV_VALUES = {'DB_HOST': ('unittest-ita-db',)}

# FileUploadColumn のパス確認・ファイル配置に使うストレージ。
# コンテナ内の `/storage/` と同じツリーが devcontainer からはこのパスで見える。
DEFAULT_STORAGEPATH = '/workspace/exastro-devcontainer/.volumes/storage/'

# 代入値管理テーブル(ドライバ別)
VALUE_TABLES = ('T_ANSL_VALUE', 'T_ANSP_VALUE', 'T_ANSR_VALUE')

# 使い捨てワークスペースの命名。**この接頭辞は掃除の目印なので変更しないこと**
DISPOSABLE_WS_PREFIX = 'itpytest'
DISPOSABLE_DB_PREFIX = 'ITA_WS_PYTEST_'
DISPOSABLE_USER_PREFIX = 'ITA_PYTEST_'


def _truthy(value):
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def _parse_env_file(path):
    """`KEY=VALUE` 形式のファイルを dict にする(コメント/空行は無視)。"""
    values = {}
    with open(path, encoding='utf-8') as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            values[key.strip()] = value.strip()
    return values


def resolve_env():
    """結合テストで使う環境変数を解決して返す(解決できないキーは含めない)。"""
    candidates = []
    if os.environ.get(ENV_FILE_ENV):
        candidates.append(os.environ[ENV_FILE_ENV])
    candidates.extend(DEFAULT_ENV_FILES)

    from_file = {}
    for path in candidates:
        if path and os.path.exists(path):
            from_file = _parse_env_file(path)
            break

    resolved = {}
    for key in REQUIRED_ENV_KEYS:
        current = os.environ.get(key)
        if current and current not in DUMMY_ENV_VALUES.get(key, ()):
            resolved[key] = current
        elif from_file.get(key):
            resolved[key] = from_file[key]
    return resolved


def target_from_env():
    """環境変数で明示された検証対象 (organization_id, workspace_id)。

    片方でも欠けていたら None を返す(呼び出し側は自動探索にフォールバックする)。
    """
    organization_id = os.environ.get(ORGANIZATION_ID_ENV)
    workspace_id = os.environ.get(WORKSPACE_ID_ENV)
    if organization_id and workspace_id:
        return organization_id, workspace_id
    return None


def storage_root():
    """ストレージ(`STORAGEPATH`)のルート。"""
    return os.environ.get(STORAGEPATH_ENV, DEFAULT_STORAGEPATH)


def gate_reason():
    """結合テストを実行しない理由。実行してよい場合は None を返す。

    既定では実行しない。`INTEGRATION_ENABLE=1` を付けたときだけ動く。
        INTEGRATION_ENABLE=1 poetry run pytest ...
    """
    if not _truthy(os.environ.get(ENABLE_ENV, '')):
        return ('結合テストは既定で実行しない(実DBに接続するため)。'
                '実行するには {}=1 を設定する'.format(ENABLE_ENV))

    missing = [k for k in REQUIRED_ENV_KEYS if k not in resolve_env()]
    if missing:
        return ('結合テスト用の接続情報が解決できない(未解決: {})。'
                '{} で .env のパスを指定するか、環境変数を設定してください'
                .format(','.join(missing), ENV_FILE_ENV))
    return None


# 具体値に書かれた TPF 変数。実装の抽出処理(WrappedStringReplaceAdmin.SimpleFillterVerSearch)は
# `{{[\s]TPF_[a-zA-Z0-9_]*[\s]}}` を探すので、前後の空白は**1文字ずつ**でなければ一致しない。
TPF_VAR_PATTERN = re.compile(r'\{\{\s(TPF_[a-zA-Z0-9_]*)\s\}\}')


def single_tpf_var(vars_entry):
    """具体値に TPF 変数が「ちょうど1個」書かれているかを、実装とは別に判定する。

    実装(SubValueAutoReg.py:692-696)は `SimpleFillterVerSearch` で抽出した変数が
    **ちょうど1個**のときだけ `VARS_ENTRY_USE_TPFVARS='1'` にし、Movement変数へも登録する
    (2個以上書くと 0 のまま。仕様というより現状の挙動)。
    テストから同じ関数を呼ぶと実装の写しになるため、ここで独立に判定する。

    Returns:
        (判定できたか(bool), ちょうど1個だったときの変数名 or None)

    コメント(`#`)やフィルタ付き変数(`|`)、Jinja2 のブロック(`{%`)を含む具体値は
    実装側の行解釈に依存するため「判定できない」を返す(検査対象から外す)。
    """
    if not isinstance(vars_entry, str):
        return True, None
    if '#' in vars_entry or '|' in vars_entry or '{%' in vars_entry:
        return False, None

    found = []
    for line in vars_entry.split('\n'):
        # 実装は1行ごとに重複を除いた変数を積む
        found.extend(sorted(set(TPF_VAR_PATTERN.findall(line))))
    if len(found) == 1:
        return True, found[0]
    return True, None


def is_strict():
    """厳密モード(データ不足の skip を fail にする)か。"""
    return _truthy(os.environ.get(STRICT_ENV, ''))


def skip_or_fail(reason):
    """データが足りないことによる skip。厳密モードでは fail にする。

    実行ゲート(`INTEGRATION_ENABLE` 未設定 / 接続情報が解決できない)以外の skip は
    すべてこの関数を通す。データを揃えた環境で `INTEGRATION_STRICT=1` を付ければ
    「データが無いので検証していない」状態を検知できる。
    """
    if is_strict():
        pytest.fail('{}({}=1 のため fail として扱う)'.format(reason, STRICT_ENV))
    pytest.skip(reason)


def disused_ids(ws_db):
    """廃止済みの (オペレーションID集合, ホストID集合) を返す。

    生成SQLの**独立オラクル**。createQuerySelectCMDB は
      - オペレーション: `T_COMN_OPERATION` を `DISUSE_FLAG='0'` で引く相関サブクエリ(NULL になる)
      - ホスト        : `T_ANSC_DEVICE` を `DISUSE_FLAG='0'` で数える相関サブクエリ(0 になる)
    で廃止データを除外し、getCMDBdata がその結果でレコードを捨てる
    (SubValueAutoReg.py:398-412 / :903-920)。
    期待値を getCMDBdata の戻りから作る方式ではこの除外を検証できないため、
    「廃止済みのIDが結果に現れない」ことを別の経路で取ったIDで確認する。
    """
    operations = {row['OPERATION_ID'] for row
                  in ws_db.table_select('T_COMN_OPERATION', "WHERE DISUSE_FLAG = '1'", [])}
    hosts = {row['SYSTEM_ID'] for row
             in ws_db.table_select('T_ANSC_DEVICE', "WHERE DISUSE_FLAG = '1'", [])}
    return operations, hosts


VERTICAL = '縦'
HORIZONTAL = '横'


def sheet_kinds(ws_db, table_names):
    """パラメータシートの実テーブル名 → `'縦'` / `'横'`。

    縦(バンドル)シートの判定は実装と同じ `INPUT_ORDER` 列の有無(SHOW COLUMNS。INT-3)。
    縦と横は実装の分岐が**別のコピー**になっている箇所が多い
    (TPF/CPF の変換、ID変換失敗の破棄、`'{{ }}'` の括り。SubValueAutoReg.py:985-1047)ため、
    「どちらの経路を通ったか」をテストから見えるようにするために使う。
    """
    kinds = {}
    for table_name in set(table_names):
        columns = ws_db.table_columns_get(table_name)[0]
        kinds[table_name] = VERTICAL if 'INPUT_ORDER' in columns else HORIZONTAL
    return kinds


def table_input_orders(ws_db, table_name):
    """縦(バンドル)シートの実テーブル: {行のROW_ID: 代入順序(`INPUT_ORDER`)}。

    縦の分岐は「設定のカラム代入順序 == 行の `INPUT_ORDER`」の行だけをレコードにする
    (SubValueAutoReg.py:987-988)。その突き合わせをテストから見るために、
    テーブルに**何種類の代入順序があるか**をレコードとは別経路で取る。
    廃止行はレコードにならないが、種類数の下限を見るだけなので廃止で絞らない。
    """
    return {row['ROW_ID']: assign_seq(row['INPUT_ORDER'])
            for row in ws_db.table_select(table_name, "WHERE 1 = 1", [])}


def vertical_value_orders(ws_db, table_name):
    """縦(バンドル)シートの実テーブル: {(ホストID, オペレーションID, 具体値): {代入順序, …}}。

    「レコードがどの行から採られたか」を**具体値から逆に引く**ための独立オラクル。

    行のIDで引けない理由: getCMDBdata のレコードは `COL_ROW_ID`(パラメータシートの項番)を
    持つが、実装はこれをレコードを作るループの**外側**(最初の収集ループ)で代入したままにしている
    (`col_row_id = row[AnscConst.DF_ITA_LOCAL_PKEY]`: SubValueAutoReg.py:933。
    レコードを作るのは :945 からの別ループで、行のIDは :990 / :1018 の
    `row[AnscConst.DF_ITA_LOCAL_PKEY]` にしか無い)。結果として1テーブル分のレコードは
    **全部同じ `COL_ROW_ID`(最後に収集した行のID)**になり、行の特定には使えない。
    (この `COL_ROW_ID` はファイル項目のエラーメッセージ MSG-10166 にも出るため、
    そちらの項番表示も同じ理由でずれる。代入値管理には保存されない。)

    したがって代入順序ごとに値を変えた行を投入し、レコードの具体値がどの代入順序の行の値と
    一致するかで判定する。同じ値が複数の代入順序に現れる場合は集合が広がるだけなので、
    「意図と違う行から採られた」以外で失敗することはない。
    値の変換(ID変換・TPF展開など)が入るカラムは一致する行が無くなるので判定対象外になる。
    """
    orders = {}
    for row in ws_db.table_select(table_name, "WHERE DISUSE_FLAG = '0'", []):
        order = assign_seq(row['INPUT_ORDER'])
        data = json.loads(row['DATA_JSON']) if row.get('DATA_JSON') else {}
        for value in data.values():
            # ファイル項目などの非文字列は具体値と直接比べられないので入れない
            if isinstance(value, str):
                orders.setdefault((row['HOST_ID'], row['OPERATION_ID'], value),
                                  set()).add(order)
    return orders


def assign_seq(value):
    """代入順序(`INPUT_ORDER` / `COLUMN_ASSIGN_SEQ`)を比較できる形に正規化する。

    実装は両方をDBから取った値のまま `==` で比べる(:987-988)。テスト側では
    別のSQLで取った値と比べるため、int と str の食い違いで誤検知しないよう文字列にする
    (未設定は `None` / `''` のどちらもありうるので `None` に寄せる)。
    """
    if value is None or value == '':
        return None
    return str(value)


def hostgroup_split_tables(ws_db):
    """hostgroup-split の展開先テーブル名 → 入力元テーブル名。

    「ホストグループ利用=有」のパラメータシートは、入力用メニューのテーブルと
    代入値自動登録用メニューのテーブル(`T_CMDB_<id>_SV`)が**別**で、
    `[HG]<ホストグループ名>` の行を hostgroup-split バックヤードが
    メンバー機器ごとに複製して後者へ書き込む(`common_libs/hostgroup`)。
    代入値自動登録設定が読むのは後者なので、このパターンだけ
    「利用者が入力した行」と「レコードになる行」が一致しない。
    対応関係は `T_HGSP_SPLIT_TARGET`(入力用メニューID, 登録対象メニューID)にある。
    """
    sql = """
        SELECT
            OUT_LINK.TABLE_NAME AS OUTPUT_TABLE_NAME,
            IN_LINK.TABLE_NAME AS INPUT_TABLE_NAME
        FROM T_HGSP_SPLIT_TARGET TGT
        INNER JOIN T_COMN_MENU_TABLE_LINK IN_LINK ON (TGT.INPUT_MENU_ID = IN_LINK.MENU_ID)
        INNER JOIN T_COMN_MENU_TABLE_LINK OUT_LINK ON (TGT.OUTPUT_MENU_ID = OUT_LINK.MENU_ID)
        WHERE TGT.DISUSE_FLAG = '0'
          AND IN_LINK.DISUSE_FLAG = '0'
          AND OUT_LINK.DISUSE_FLAG = '0'
    """
    return {row['OUTPUT_TABLE_NAME']: row['INPUT_TABLE_NAME']
            for row in ws_db.sql_execute(sql, [])
            if row['OUTPUT_TABLE_NAME'] and row['INPUT_TABLE_NAME']}


def hostgroup_members(ws_db):
    """{ホストグループのROW_ID: {'NAME': 名前, 'HOSTS': {メンバー機器のSYSTEM_ID, …}}}。

    展開結果の**独立オラクル**。`T_HGSP_HOST_LINK.HOSTNAME` には機器の SYSTEM_ID が入り、
    `OPERATION_ID` が NULL なら全オペレーションが対象。
    メンバーにホストグループを指定する入れ子も作れるが、その場合は展開が機器まで
    再帰するのでここでは機器一覧にあるものだけを返す(部分集合として使う)。
    """
    devices = {row['SYSTEM_ID'] for row
               in ws_db.table_select('T_ANSC_DEVICE', "WHERE DISUSE_FLAG = '0'", [])}
    groups = {row['ROW_ID']: {'NAME': row['HOSTGROUP_NAME'], 'HOSTS': set()}
              for row in ws_db.table_select('T_HGSP_HOSTGROUP_LIST',
                                            "WHERE DISUSE_FLAG = '0'", [])}
    for row in ws_db.table_select('T_HGSP_HOST_LINK', "WHERE DISUSE_FLAG = '0'", []):
        group = groups.get(row['HOSTGROUP_NAME'])
        if group is not None and row['HOSTNAME'] in devices:
            group['HOSTS'].add(row['HOSTNAME'])
    return groups


def list_workspaces():
    """(organization_id, workspace_id) の一覧を返す。

    使い捨てワークスペース(`itpytest*`)は対象外にする。
    異常終了で残骸が残っていた場合に、それを検証対象に選んでしまわないため。
    """
    from common_libs.common.dbconnect import DBConnectCommon, DBConnectOrg

    common_db = DBConnectCommon()
    try:
        orgs = common_db.table_select('T_COMN_ORGANIZATION_DB_INFO', "WHERE DISUSE_FLAG = '0'")
    finally:
        common_db.db_disconnect()

    pairs = []
    for org in orgs:
        org_id = org['ORGANIZATION_ID']
        org_db = DBConnectOrg(org_id)
        try:
            workspaces = org_db.table_select('T_COMN_WORKSPACE_DB_INFO', "WHERE DISUSE_FLAG = '0'")
        finally:
            org_db.db_disconnect()
        pairs.extend((org_id, ws['WORKSPACE_ID']) for ws in workspaces
                     if not str(ws['WORKSPACE_ID']).startswith(DISPOSABLE_WS_PREFIX))
    return pairs


# ======================================================================
# 使い捨てワークスペース
# ======================================================================
class DisposableWorkspace():
    """既存ワークスペースを複製した、使い捨てのワークスペース。

    登録経路(`get_data_from_parameter_sheet`)は代入値管理へ INSERT するため、
    実ワークスペースに対しては流せない。ロールバックで戻す方式は
    「本当に登録されたか」を確認しづらく、途中で例外が出た場合に汚染が残るため、
    **複製した専用ワークスペースを作って、最後に DROP DATABASE する**方式にしている。

    作るもの(すべて `ITA_WS_PYTEST_` / `ITA_PYTEST_` / `itpytest` 接頭辞)
      1. WS用DB(複製元の BASE TABLE を `CREATE TABLE LIKE` + `INSERT SELECT`、VIEW は再作成)
      2. WS用DBユーザ(複製したDBにのみ権限を持つ)
      3. 組織DBの `T_COMN_WORKSPACE_DB_INFO` レコード(複製元の行をコピーして書き換え)
      4. ストレージ(`STORAGEPATH/組織/ワークスペース/`)のコピー
         FileUploadColumn の具体値は実ファイルの存在確認が入るため

    後始末は `drop()`(DROP DATABASE / DROP USER / レコード削除 / ストレージ削除)。

    注意: 同一DBに対する並行実行は考慮していない(setup 時に残骸を掃除するため)。
    """

    def __init__(self, organization_id, source_workspace_id):
        self.organization_id = organization_id
        self.source_workspace_id = source_workspace_id

        tag = uuid.uuid4().hex[:12]
        self.workspace_id = DISPOSABLE_WS_PREFIX + tag
        self.db_name = DISPOSABLE_DB_PREFIX + tag.upper()
        self.db_user = DISPOSABLE_USER_PREFIX + tag.upper()
        self._db_password = uuid.uuid4().hex          # 16進のみ。SQLへの埋め込みでエスケープ不要
        self.storage_path = os.path.join(storage_root(), organization_id, self.workspace_id)

        self.source_db_name = None
        self.elapsed = {}
        self._root = None
        self._org_db_name = None
        self._created_db = False
        self._created_user = False
        self._created_info = False
        self._created_storage = False

    # ------------------------------------------------------------------
    def create(self):
        """複製を作って、接続できる状態にする。"""
        from common_libs.common.dbconnect import DBConnectOrg, DBConnectOrgRoot
        from common_libs.common.util import ky_encrypt

        org_db = DBConnectOrg(self.organization_id)
        try:
            self._org_db_name = org_db._db
            source_rows = org_db.table_select(
                'T_COMN_WORKSPACE_DB_INFO', "WHERE WORKSPACE_ID = %s AND DISUSE_FLAG = '0'",
                [self.source_workspace_id])
        finally:
            org_db.db_disconnect()
        assert source_rows, '複製元ワークスペースの接続情報が無い: {}'.format(self.source_workspace_id)
        source_row = source_rows[0]
        self.source_db_name = source_row['DB_DATABASE']

        self._root = DBConnectOrgRoot(self.organization_id)
        self.prune_orphans()

        # 1. WS用DBの複製
        started = time.time()
        self._clone_database()
        self._created_db = True
        self.elapsed['database'] = time.time() - started

        # 2. WS用DBユーザ
        self._root.user_create(self.db_user, self._db_password, self.db_name)
        self._created_user = True

        # 3. 組織DBへワークスペースの接続情報を登録
        row = dict(source_row)
        row['PRIMARY_KEY'] = str(uuid.uuid4())
        row['WORKSPACE_ID'] = self.workspace_id
        row['DB_DATABASE'] = self.db_name
        row['DB_USER'] = self.db_user
        row['DB_PASSWORD'] = ky_encrypt(self._db_password)
        row['NOTE'] = 'created by pytest integration test (disposable)'
        columns = list(row.keys())
        self._execute(
            "INSERT INTO `{}`.`T_COMN_WORKSPACE_DB_INFO` ({}) VALUES ({})".format(
                self._org_db_name,
                ','.join('`{}`'.format(c) for c in columns),
                ','.join(['%s'] * len(columns))),
            [row[c] for c in columns])
        self._created_info = True

        # 4. ストレージの複製(FileUploadColumn の具体値のため)
        started = time.time()
        source_storage = os.path.join(storage_root(), self.organization_id, self.source_workspace_id)
        if os.path.isdir(source_storage):
            shutil.copytree(source_storage, self.storage_path, symlinks=True)
            self._created_storage = True
        self.elapsed['storage'] = time.time() - started

        return self

    def connect(self):
        """複製したワークスペースに接続した DBConnectWs を返す。"""
        from common_libs.common.dbconnect import DBConnectWs

        g.ORGANIZATION_ID = self.organization_id
        g.WORKSPACE_ID = self.workspace_id
        return DBConnectWs(self.workspace_id, self.organization_id)

    # ------------------------------------------------------------------
    def drop(self):
        """作ったものをすべて消す。失敗しても残りの後始末は続ける。"""
        errors = []
        if self._created_db:
            try:
                self._root.database_drop(self.db_name)
            except Exception as e:                                  # pragma: no cover
                errors.append('DROP DATABASE {}: {}'.format(self.db_name, e))
        if self._created_user:
            try:
                self._root.user_drop(self.db_user)
            except Exception as e:                                  # pragma: no cover
                errors.append('DROP USER {}: {}'.format(self.db_user, e))
        if self._created_info:
            try:
                self._execute("DELETE FROM `{}`.`T_COMN_WORKSPACE_DB_INFO` WHERE WORKSPACE_ID = %s".format(
                    self._org_db_name), [self.workspace_id])
            except Exception as e:                                  # pragma: no cover
                errors.append('DELETE T_COMN_WORKSPACE_DB_INFO {}: {}'.format(self.workspace_id, e))
        if self._created_storage and os.path.isdir(self.storage_path):
            try:
                shutil.rmtree(self.storage_path)
            except Exception as e:                                  # pragma: no cover
                errors.append('rmtree {}: {}'.format(self.storage_path, e))
        if self._root is not None:
            self._root.db_disconnect()
        return errors

    def prune_orphans(self):
        """異常終了で残った使い捨てワークスペースを掃除する。

        自分自身より前の実行の残骸(DB/ユーザ/接続情報/ストレージ)を消す。
        残しておくと DB とストレージを食い潰し、
        ワークスペース自動検出が壊れたワークスペースを選ぶ原因になる。
        """
        pruned = []
        for row in self._root.sql_execute(
                "SELECT SCHEMA_NAME FROM information_schema.schemata WHERE SCHEMA_NAME LIKE %s",
                [DISPOSABLE_DB_PREFIX + '%']):
            name = row['SCHEMA_NAME']
            if name.upper() != self.db_name.upper():
                self._root.database_drop(name)
                pruned.append(name)
        for row in self._root.sql_execute(
                "SELECT User FROM mysql.user WHERE User LIKE %s", [DISPOSABLE_USER_PREFIX + '%']):
            name = row['User']
            if name.upper() != self.db_user.upper():
                self._root.user_drop(name)
                pruned.append(name)
        rows = self._root.sql_execute(
            "SELECT WORKSPACE_ID FROM `{}`.`T_COMN_WORKSPACE_DB_INFO` WHERE WORKSPACE_ID LIKE %s".format(
                self._org_db_name), [DISPOSABLE_WS_PREFIX + '%'])
        for row in rows:
            if row['WORKSPACE_ID'] != self.workspace_id:
                self._execute("DELETE FROM `{}`.`T_COMN_WORKSPACE_DB_INFO` WHERE WORKSPACE_ID = %s".format(
                    self._org_db_name), [row['WORKSPACE_ID']])
                pruned.append(row['WORKSPACE_ID'])
                orphan_storage = os.path.join(storage_root(), self.organization_id, row['WORKSPACE_ID'])
                if os.path.isdir(orphan_storage):
                    shutil.rmtree(orphan_storage)
        if pruned:
            print('\n[integration] 前回実行の残骸を掃除した: {}'.format(', '.join(pruned)))
        return pruned

    # ------------------------------------------------------------------
    def _execute(self, sql, bind_list=None):
        """更新系SQLを1件実行してコミットする。

        `db_commit()` は `db_transaction_start()` 済みでないと**何もしない**ため、
        必ず対で呼ぶ(でないと切断時に巻き戻る)。
        """
        self._root.db_transaction_start()
        result = self._root.sql_execute(sql, bind_list if bind_list is not None else [])
        self._root.db_commit()
        return result

    def _clone_database(self):
        """複製元DBのテーブル(定義+データ)とビューを複製する。"""
        source = self.source_db_name
        clone = self.db_name
        self._root.database_create(clone)

        tables = [r['TABLE_NAME'] for r in self._root.sql_execute(
            "SELECT TABLE_NAME FROM information_schema.tables "
            "WHERE table_schema = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME", [source])]
        views = [r['TABLE_NAME'] for r in self._root.sql_execute(
            "SELECT TABLE_NAME FROM information_schema.tables "
            "WHERE table_schema = %s AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME", [source])]
        assert tables, '複製元DBにテーブルが無い: {}'.format(source)

        for table_name in tables:
            self._root.sql_execute("CREATE TABLE `{}`.`{}` LIKE `{}`.`{}`".format(
                clone, table_name, source, table_name))
            self._execute("INSERT INTO `{}`.`{}` SELECT * FROM `{}`.`{}`".format(
                clone, table_name, source, table_name))

        # ビューは定義文を書き換えて作り直す。
        #   - DEFINER: 複製元のDBユーザは複製先に権限が無いので外す
        #   - SQL SECURITY: DEFINER のままだと実行時に権限エラーになるので INVOKER にする
        #   - DB名: `SHOW CREATE VIEW` は**小文字**で返すので大文字小文字を無視して置換する
        #   - 依存関係: ビューがビューを参照するため、進捗が出る限りリトライする
        definer_pattern = re.compile(r"DEFINER=`[^`]*`@`[^`]*`\s*")
        source_db_pattern = re.compile('`' + re.escape(source) + '`', re.IGNORECASE)
        pending = list(views)
        last_error = None
        while pending:
            remain = []
            progressed = False
            for view_name in pending:
                ddl = self._root.sql_execute("SHOW CREATE VIEW `{}`.`{}`".format(
                    source, view_name))[0]['Create View']
                ddl = definer_pattern.sub('', ddl).replace('SQL SECURITY DEFINER', 'SQL SECURITY INVOKER')
                ddl = source_db_pattern.sub('`{}`'.format(clone), ddl)
                try:
                    self._root.sql_execute(ddl)
                    progressed = True
                except Exception as e:
                    last_error = '{}: {}'.format(view_name, e)
                    remain.append(view_name)
            pending = remain
            if pending and not progressed:
                raise AssertionError('ビューを複製できない({}件): {}'.format(len(pending), last_error))

        self.table_count = len(tables)
        self.view_count = len(views)
