# ita_by_ansible_legacy_vars_listup のテスト

pytest は VSCode の「テスト」タブから実行する前提です。  
このファイルでは、実行前の準備（`pytest.ini` の作成、ゴールデンファイルの生成、結合テスト用データの投入）と、マーカー・環境変数の使い方をまとめます。

以降のコマンドは、特に断りがない限り
`ita_root/ita_by_ansible_legacy_vars_listup` をカレントにして実行します。

## 1. pytest.ini の作成

```sh
cp pytest.ini.sample pytest.ini
```

- `pytest.ini` は `.gitignore` の対象です。
  設定を共有したいときは `pytest.ini.sample` を更新します。
- `env =` に書いた値は pytest-env によってテスト開始時に設定されます。
  `DB_HOST=unittest-ita-db` などは単体テスト用のダミー値です。  
  結合テストでは、これを実環境の値で上書きします（→ [4.4](#45-接続情報の解決)）。
- デバッガを使うときは、末尾の `addopts=--no-cov` のコメントを外します  
  （外している間は、カバレッジが更新されません）。

## 2. マーカーと実行の切り替え

| マーカー | 対象 | 既定 | 切り替え方 |
|---|---|---|---|
| なし | 単体テスト | 実行する | - |
| `exhaustive` | `getCMDBdata` の実現可能な全組合せ（431,424件）をゴールデンと突き合わせる | **実行する**（約140秒） | 外す: `-m "not exhaustive"` |
| `integration` | 稼働中のスタック（MariaDB）に実際に接続する結合テスト | **skip** | `INTEGRATION_ENABLE=1` |

`integration` は、テストを deselect せずにフィクスチャ側で skip します。   
そのため、VSCode のテスト一覧には skip 理由付きで表示されます。  


### VSCode から環境変数を渡す

VSCode のテストタブは `pytest.ini` を読みます。  
結合テストを流したい間だけ、`pytest.ini` の `env =` に次の行を追加してください。

```ini
env =
    ...
    INTEGRATION_ENABLE=1
    ; データを揃えた環境では skip を fail に変える（→ 5章）
    ; INTEGRATION_STRICT=1
```

`pytest.ini` はコミットされないので、追加したままでも他の人には影響しません。  
ただし、既定の挙動（結合テストは skip）に戻したいときは、行を消すかコメントにしてください。

### 結合テストで使う環境変数

| 変数 | 用途 | 既定値 |
|---|---|---|
| `INTEGRATION_ENABLE` | `1` のときだけ結合テストを実行する | 未設定（skip） |
| `INTEGRATION_STRICT` | `1` のとき、データ不足による skip を fail にする | 未設定 |
| `INTEGRATION_ENV_FILE` | DB 接続情報を読み込む `.env` のパス | 下記の既定パスを順に探す |
| `INTEGRATION_STORAGEPATH` | ストレージのルート（FileUploadColumn の確認に使う） | `/workspace/exastro-devcontainer/.volumes/storage/` |
| `ITA_ORGANIZATION_ID` / `ITA_WORKSPACE_ID` | 検証対象のワークスペース | 代入値自動登録設定が1件以上あるワークスペースを自動で探す |

`ITA_ORGANIZATION_ID` / `ITA_WORKSPACE_ID` は、データ投入スクリプト（4章）と同じ変数名です。

## 3. ゴールデンファイルの生成（exhaustive）

`exhaustive` のテスト（パターン全網羅）は、現在の実装で作ったゴールデンファイル
`tests/ansible_driver_tests/ansible_driver/classes/subvalue_autoreg_getCMDBdata_exhaustive_golden.txt`
と結果を比較します。  
このファイルが無いと、`test_all_feasible_combinations_match_golden` が fail になります。

```sh
python3 -m tests.ansible_driver_tests.ansible_driver.classes.subvalue_autoreg_exhaustive --all
# --index を付けると、組合せの一覧(tsv)も出力される かなり大容量のため注意
```

`getCMDBdata` の挙動を意図的に変えたときは、ゴールデンを作り直して差分を確認してから再実施してください。  
また、作り直したゴールデンはコミットしてください。

## 4. 結合テスト（integration）の準備

### 4.1 前提

- devcontainer のスタックが起動していること。  
  下記のバックヤードコンテナが起動していて、entrypoint.shを実行していること

  | バックヤード | 使われる段階 |
  |---|---|
  | ita-by-menu-create | 段階4（パラメータシートの作成） |
  | ita-by-ansible-legacy-vars-listup / ita-by-ansible-pioneer-vars-listup / ita-by-ansible-legacy-role-vars-listup | 段階7（Movement 変数の抽出を待つ） |
  | ita-by-hostgroup-split | 段階7（ホストグループの展開を待つ） |
  
  `docker exec -d`によって実行する場合は下記
    - `docker exec -d exastro-ita-by-ansible-legacy-vars-listup-1 bash -c 'bash /exastro/backyard/entrypoint.sh >> /tmp/backyard.log 2>&1'`
    - `docker exec -d exastro-ita-by-ansible-legacy-role-vars-listup-1 bash -c 'bash /exastro/backyard/entrypoint.sh >> /tmp/backyard.log 2>&1'`
    - `docker exec -d exastro-ita-by-ansible-pioneer-vars-listup-1 bash -c 'bash /exastro/backyard/entrypoint.sh >> /tmp/backyard.log 2>&1'`
    - `docker exec -d exastro-ita-by-menu-create-1 bash -c 'bash /exastro/backyard/entrypoint.sh >> /tmp/backyard.log 2>&1'`
- データを投入するための、使い捨てにできるオーガナイゼーション/ワークスペースがあること

### 4.2 データ投入スクリプト（sample_data）

`tests/ansible_driver_tests/ansible_driver/sample_data/` にあるスクリプトで、ITA REST API を使ってデータを投入します。

必要な環境変数:

| 変数 | 内容 |
|---|---|
| `ITA_BASE_URL` | ITA の URL（例: `http://10.XXX.XXX.XXX:8000`・**localhostは使用しない**） |
| `ITA_ORGANIZATION_ID` | 投入先のオーガナイゼーション ID |
| `ITA_WORKSPACE_ID` | 投入先のワークスペース ID（**ws1を使用する**） |
| `ITA_USER` / `ITA_PASSWORD` | Basic 認証に使うユーザー/パスワード |

認証情報はシェルの環境変数で渡し、ファイルには書かないでください。

スクリプトは、**sample_data ディレクトリに移動してから**実行します。

```sh
cd tests/ansible_driver_tests/ansible_driver/sample_data
export ITA_BASE_URL=... ITA_ORGANIZATION_ID=... ITA_WORKSPACE_ID=...
export ITA_USER=... ITA_PASSWORD=...
```

疎通確認を行ってからデータ投入を行います。
```bash
python3 ita.py /version/
```

下記のような情報が取得できることを確認します。
```json
{
  "data": {
    "installed_driver": [
      "パラメータシート作成",
      "ホストグループ",
      "Ansible"
    ],
    "version": "2.9.0"
  },
  "message": "SUCCESS",
  "result": "000-00000",
  "ts": "2050-12-31T00:00:00.000Z"
}
```

その後投入作業に進みます。
```sh
python3 step01_hosts_ops.py
python3 step02_material.py
# ... step11 まで番号順に実行する
```

作成したデータの ID は `sample_data/ids.json` に記録されます。  
`ids.json` は投入先の環境に依存する（UUID を含む）ので、コミットしないでください。  
ワークスペースを初期化して再実行するときは、`ids.json` を削除してから段階1からやり直します。

### 4.3 各段階の内容と注意点

| 段階 | スクリプト | 内容 | 注意点 |
|---|---|---|---|
| 1 | `step01_hosts_ops.py` | 機器一覧・オペレーション・ホストグループ | |
| 2 | `step02_material.py` | Playbook 素材 / 対話種別・OS 種別・対話ファイル素材 / テンプレート管理 / ファイル管理 | |
| 3 | `step03_movement.py` | Movement（Legacy: L1・L2、Pioneer: P1）と素材の紐付 | |
| 4 | `step04_sheets.py` | パラメータシート6種（横 / 縦 / オペレーションのみ / 項目なし / ホストグループ横・縦） | menu-create による作成を待つ。パラメータシート参照は参照先ができてから定義するため、2回に分けて作成する |
| 5 | `step05_fix_regex.py` | 作成したパラメータシートの「正規表現」を埋め直す | ITA 2.9.0 の不具合を回避するための段階 |
| 6 | `step06_role.py` | LegacyRole 用のロールパッケージ / Movement / 紐付 | 「ロールパッケージ解析待ち」と表示されたら、少し待ってから再実行する |
| 7 | `step07_rows_and_autoreg.py` | パラメータシートへの具体値の投入と、代入値自動登録設定の登録 | 終了コード 2: パラメータシートが無い（menu-create が動いていない）。終了コード 3: Movement 変数が無い（vars-listup が動いていない） |
| 8 | `step08_discard.py` | 廃止パターンを作る（機器 `pytest-host-Z` / オペレーション `pytest-ope-disused` を廃止） | `python3 step08_discard.py restore` で廃止を戻せる（→ 4.4） |
| 9 | `step09_upload_file.py` | FileUploadColumn に実ファイルを載せる | |
| 10 | `step10_multi_movement.py` | 同じカラムに、複数の Movement の代入値自動登録設定を紐づける | |
| 11 | `step11_tpf_and_hostvars.py` | vars-listup 固有の「実行時相当」の変数を刈り取る経路にデータを通す（TPF など） | |

### 4.4 接続情報の解決

結合テストは、DB の接続情報を `pytest.ini` の `env` からは取りません。  
`subvalue_autoreg_integration_support.py` が、次の順に `.env` を探して読み込みます。

1. `INTEGRATION_ENV_FILE` で指定したパス
2. `/workspace/exastro-devcontainer/docker-compose/.env`
3. `/workspace/.devcontainer/.env`

使うキーは `DB_HOST` / `DB_PORT` / `DB_DATABASE` / `DB_USER` / `DB_PASSWORD` / `ENCRYPT_KEY` です。  
1つでも解決できない場合、結合テストはその旨を理由にして skip されます。

登録経路のテスト（`test_SubValueAutoReg_integration_write.py`）は、対象のワークスペースを複製して使い捨てのワークスペースを作成し、
テスト後に削除します（DROP DATABASE / DROP USER / レコード削除 / ストレージ削除）。  
作成されるものの名前の接頭辞は `itpytest` / `ITA_WS_PYTEST_` / `ITA_PYTEST_` です。  
テストが途中で中断されると、これらが残ることがあります。

## 5. INTEGRATION_STRICT

結合テストの中には、投入データに該当するパターンが無いと skip するものがあります。  
段階1〜11 をすべて投入した環境では、このような skip は0件になるはずです。  
`INTEGRATION_STRICT=1` を付けると、この skip が fail になるので、データ不足に気付けます。

なお、実行ゲートによる skip（`INTEGRATION_ENABLE` が未設定、接続情報が解決できない）は、
`INTEGRATION_STRICT` を付けても skip のままです。

## 6. トラブルシュート

### 「段階7 に戻る」と書かれたテストが落ちる

`test_SubValueAutoReg_integration.py` / `test_SubValueAutoReg_integration_write.py` の一部のテストは、
実装ではなく**投入データ**の状態を検査しています（例: ドライバごとに縦シートを通る設定があるか）。  
これらが落ちた場合は、段階7（`step07_rows_and_autoreg.py`）の実行ログに登録エラーがないか確認し段階7を再実行する、又は代入値自動登録設定を見直して下さい。

### 結合テストがすべて skip される

VSCode のテスト結果に表示される skip 理由を確認してください。

- `INTEGRATION_ENABLE=1` が設定されていない → 2章
- 接続情報が解決できない → 4.4
- 接続できない（スタックが起動していない） → devcontainer のスタックを起動する

### exhaustive が fail する

ゴールデンファイルが無い、または実装の変更で結果が変わった可能性があります → 3章
