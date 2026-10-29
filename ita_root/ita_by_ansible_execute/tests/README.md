# ita_by_ansible_execute のテスト

pytest は VSCode の「テスト」タブから実行する前提です。  
このファイルでは、実行前の準備（`pytest.ini` の作成）と、実ホストに接続する結合テストの設定方法をまとめます。

以降のコマンドは、特に断りがない限り
`ita_root/ita_by_ansible_execute` をカレントにして実行します。

## 1. pytest.ini の作成

```sh
cp pytest.ini.sample pytest.ini
```

- `pytest.ini` は `.gitignore` の対象です。  
  設定を共有したいときは `pytest.ini.sample` を更新します。
- `pythonpath` は `/workspace/exastro-it-automation-dev/ita_root` です
  （`ita_by_ansible_legacy_vars_listup` の `.` とは異なります）。  
  テスト対象の `common_libs` は `ita_root/common_libs` から import されます。
- `env =` に書いた値は pytest-env によってテスト開始時に設定されます。
  `DB_HOST=unittest-ita-db` などは単体テスト用のダミー値で、このディレクトリのテストは DB に接続しません。

## 2. テストの構成

| ディレクトリ | 対象 | 種別 | 外部への接続 |
|---|---|---|---|
| `tests/ansible_driver_tests/ansibletowerlibs/` | `ExecuteDirector` / `AnsibleTowerRestApiCredentials` / `AnsibleTowerRestApiProjects` | 単体 | なし（モック） |
| `tests/ansible_driver_tests/ansible_driver/classes/` | `CreateAnsibleExecFiles` | 単体 | なし（モック） |
| `tests/ansible_driver_tests/ansible_driver/shells/` | `pioneer_module.py` / `ky_pionner_grep_side_Ansible.sh` | 下表 | C のみ実ホストへ SSH |

`shells/` のテストは、次の3層に分かれています。

| 層 | ファイル | 内容 |
|---|---|---|
| A | `test_ky_pionner_grep_side_shell.py` | 検索シェル（`ky_pionner_grep_side_Ansible.sh`）を `sh` で直接実行する |
| B | `test_pioneer_module_shell_cmd.py` | pexpect と subprocess を差し替えて、`pioneer_module.py` の `main()` を実行する |
| C | `test_pioneer_module_integration.py` | モックを使わず、実ホストへ SSH 接続して「モジュール → シェル → 判定」を通す（`integration` マーカー） |

## 3. 結合テスト（C: 実ホストへの SSH）

### 3.1 実行の切り替え

C は、実ホストへのSSH接続を行うテストです。  
接続情報の環境変数が3つとも設定されているときだけ実行されます。  
1つでも欠けていると、すべて skip されます（VSCode のテスト一覧には skip 理由付きで表示されます）。

| 変数 | 内容 |
|---|---|
| `ITA_TEST_SSH_HOST` | 接続先ホスト |
| `ITA_TEST_SSH_USER` | ログインユーザー |
| `ITA_TEST_SSH_PASS` | ログインパスワード |

VSCode のテストタブから実行する場合は、`pytest.ini` の `env =` にある次の行のコメントを外して、値を設定します。

```ini
env =
    ...
    D:ITA_TEST_SSH_HOST=<接続先>
    D:ITA_TEST_SSH_USER=<ユーザー>
    D:ITA_TEST_SSH_PASS=<パスワード>
```

- **接続情報は `pytest.ini` にだけ書き、`pytest.ini.sample` には書かないでください。**
- テスト中に作る対話ファイル・暗号化変数ファイルは、すべて pytest の `tmp_path` 配下に作られます。  
  ログインパスワードは暗号化変数（Vault）として渡されるので、対話ファイルには平文で残りません。


### 3.2 接続先ホストの条件

テストの対話ファイルは、次の前提で書かれています。

- テストを実行する環境に `ssh` コマンドがあること
- 接続先に**パスワード認証**でログインできること。パスワードの入力を求めるプロンプトは `[Pp]assword:` に一致する必要があります。
- ログイン後のシェルプロンプトが **`$ ` で終わる**こと。
  root ユーザーなど、プロンプトが `# ` で終わるユーザーでは一致せず、タイムアウトで失敗します。
- 接続先で `echo` と `tr` が使えること。

## 4. トラブルシュート

### A-23（`test_a23_runs_under_non_bash_sh`）が skip される

bash 以外の `sh`（dash / ash）が見つからない環境では skip されます。  
POSIX sh 互換性を確認したい場合は、dash などが入っている環境で実行してください。  
※作業実行サーバ（ansible-playbookの実行サーバ）の想定がRHEL系統であればbash のためskipで良いと思われます。  
　今後、Debian系統やAlpineを考慮する必要が出てきたならbash ではないため実施した方が良いと思われます。）

### C がすべて skip される

`ITA_TEST_SSH_HOST` / `ITA_TEST_SSH_USER` / `ITA_TEST_SSH_PASS` のどれかが未設定です → 3.1

### C がタイムアウトで失敗する

ログインのプロンプトやシェルプロンプトが想定と違う可能性があります → 3.2

### classes/ のテストがすべて error になる

依存パッケージ（`dictknife` など）が入っていない可能性があります → pyproject.toml の依存を入れることで対応可能です
