# Ansible driver共通機能（変数取り扱い・メニュー設定）

## Ansible driver概要

- **Ansible Core**: 多数の構築管理対象に対しデプロイ作業を容易にするPF構築自動化ツール。PlaybookというYAML形式のテキストにタスクを記述し実行する。
- **Ansible Automation Controller**: Ansibleにアクセスコントロール・ジョブスケジューリング・タスク可視化を拡張した管理プラットフォーム。“プロジェクト”“インベントリ”“認証情報”の組合せで“ジョブテンプレート”を作成し実行、複数のジョブテンプレートを組み合わせて“ワークフロージョブテンプレート”を作成できる。
- **Ansible Automation Platform (Cloud)**: Ansible Automation Controllerと同様だがRed Hat Ansible Automation Platform (Managed Service)版に対応。ITA固有の資材連携にSSHを必要としない。
- **Ansible Execution Agent**: ITAとは独立したAnsible実行専用サーバー。Ansible-builderで実行環境（コンテナ）を構築し、Ansible-runnerで実行環境を介しPlaybookを実行する。ワークスペース単位に用意し、同一ワークスペースに複数配置することで冗長化できる。
- **Ansible driver**: 作業対象機器に対しAnsible Core・Ansible Automation Controller・Ansible Execution Agentのいずれを経由するか選択し、Playbook処理を自動化するITA機能。3モードを用意:
  - **Legacyモード**: Ansible標準機能で各ホストへ設定投入。構築コードを単体YAMLファイルとして登録し、作業パターンをその組み合わせで構成。サーバ・ストレージ・ネットワーク機器の環境設定作業向け。
  - **Legacy Roleモード**: Legacyと同じくAnsible標準機能を使うが、構築コードをパッケージ（Role）として登録し、作業パターンをRoleの組み合わせで構成。製品部門提供のRoleパッケージでのインストール・環境構築向け。
  - **Pioneerモード**: Ansibleに独自モジュールを追加し、対話形式で設定投入。Telnet/SSHでログイン可能な機器に対応。作業対象と直接やり取りするため相応のITスキルが必要。

## 変数の取り扱い

Playbook中の変数はITAから具体値を設定できます。ITAで扱える変数は以下の7種類です。

| 変数種類 | 説明 |
|---|---|
| 通常変数 | 変数名に対し具体値を1つ定義できる変数。 |
| 複数具体値変数 | 変数名に対し具体値を複数定義できる変数。 |
| 多段変数 | 階層化された変数。Ansible-LegacyRoleでのみ扱える。 |
| グローバル変数 | 「Ansible共通→グローバル変数管理」から登録。複数のPlaybook/タスクで共通利用する情報を一元管理。テンプレート管理・Playbook素材集・対話ファイル素材集・ロールパッケージ管理内で使用可能（記述例: `{{ GBL_user }}`）。 |
| グローバル変数（センシティブ） | 「Ansible共通→グローバル変数（センシティブ）管理」から登録。使用方法はグローバル変数と同様だが暗号化保存され、実行時にansible-vaultを通して使用。認証情報やAPIキーなど機微情報向け。 |
| テンプレート埋込変数 | 「Ansible共通→テンプレート管理」から登録（例: `{{ TPF_SAMPLE }}`）。 |
| ファイル埋込変数 | 「Ansible共通→ファイル管理」から登録（例: `{{ CPF_SAMPLE }}`）。 |
| ITA独自変数 | ITA独自定義の変数（後述）。 |

### ITA独自変数一覧

| 項目名 | 変数名 | 説明 |
|---|---|---|
| ホスト名/DNSホスト名/IPアドレス/プロトコル/ログインユーザID/ログインパスワード | `__inventory_hostname__` `__dnshostname__` `__ipaddress__` `__loginprotocol__` `__loginuser__` `__loginpassword__` | 機器一覧の項目値。未設定で作業実行するとエラー。 |
| Movement ID | `__movement_id__` | 作業実行時に選択されたMovement一覧のMovement ID。 |
| オペレーション | `__operation__` `__operation_datetime__` `__operation_id__` `__operation_name__` | オペレーション一覧の値。`__operation__`は「YYYY/MM/DD HH:MM」_「オペレーションID」:「オペレーション名称」。 |
| 作業インスタンスID | `__execution_no__` | 作業実行時に生成される作業No。 |
| ConductorインスタンスID | `__conductor_id__` | Conductor実行時のインスタンスID。Conductor実行時のみ使用可（Movement単体実行ではエラー）。 |
| 作業ディレクトリパス | `__workflowdir__` | 作業実行時の作業ディレクトリ。ここに作成したファイルは作業管理の結果データからダウンロード可能。 |
| Conductor作業ディレクトリパス | `__conductor_workflowdir__` | Conductor実行時に各Movementで共有するディレクトリ（単体実行時は`__workflowdir__`と同じパス）。Parallel branchで並列実行されるMovement間では共有不可、並列関係にない後続Movementとの間でのみ共有可能。 |
| ステータスファイルパス | `__movement_status_filepath__` | Status file branchノードで参照するファイルパス。 |
| 収集機能の各ファイルパス | `__parameters_dir_for_epc__` `__parameters_file_dir_for_epc__` `__parameter_dir__` `__parameters_file_dir__` | 収集機能の作業ディレクトリ（in）/作業結果ディレクトリ（out）の`_parameters`（パラメータ格納）・`_parameters_file`（ファイル格納）のパス。 |
| オーガナイゼーション管理 | `__organization_id__` `__workspace_id__` `__external_url__` | オーガナイゼーションID・ワークスペースID・サービス公開エンドポイント。 |

### 変数抜出対象資材と書式

変数抜出対象の資材（メニュー・項目）は下表の通りです（〇: 対象、×: 対象外）。

| メニュー・項目 | Legacy | Pioneer | LegacyRole |
|---|---|---|---|
| Playbook素材集の Playbook素材 | 〇 | × | × |
| 対話ファイル素材集の 対話ファイル素材 | × | 〇 | × |
| ロールパッケージ管理の ロールパッケージファイル（ZIP形式） | × | × | 〇 |
| テンプレート管理の 変数定義 | 〇 | 〇 | 〇 |
| 機器一覧の インベントリファイル追加オプション、Movement一覧の ヘッダセクション | 〇 | × | 〇 |
| パラメータシートでテンプレート管理を選択している項目 | 〇 | 〇 | 〇 |

書式（△は半角スペース、vvv/xxxは255/251バイト以内の半角英数字とアンダースコア）:

- 通常変数・複数具体値変数: `{{△vvv△}}` または `{{△vvv△|△フィルタ△}}`（代入値自動登録設定の代入順序が入力されていれば複数具体値変数として扱う）
- グローバル変数: `{{△GBL_xxx△}}`
- テンプレート埋込変数: `{{△TPF_xxx△}}`
- ファイル埋込変数: `{{△CPF_xxx△}}`

ロールパッケージファイル（ZIP形式）では、通常変数・複数具体値変数・多段変数がdefaults/tasks/templates/handlers/meta配下で抜出対象（`vvv: value`等の形式、具体値省略可）。多段変数のメンバー変数名には`. [ ] ' \ :`の7文字を除くASCII文字(0x20〜0x7e)が使用可能です。機器一覧のインベントリファイル追加オプションとMovement一覧のヘッダセクションでは、Legacyは通常変数・複数具体値変数、LegacyRoleはこれに加え多段変数（ロールパッケージまたはテンプレート管理の変数定義で定義されていればその種類として扱い、未定義なら通常変数）が扱えます。グローバル変数・ファイル埋込変数・テンプレート埋込変数はここでは扱えません。

### 変数の具体値登録フロー（共通）

Ansible-Legacy／Ansible-Pioneer／Ansible-LegacyRoleいずれも同じ流れです。

1. 変数抜出対象の資材から変数を抜出し、各モードの「代入値自動登録設定」で変数が選択可能になる。
2. パラメータシートの項目に具体値を登録する。
3. 「代入値自動登録設定」でパラメータシートの項目と変数の紐付けを登録する。
4. 作業実行時、紐付けられた情報が「代入値管理」に反映され、ホスト変数ファイルに出力される。

LegacyRoleの場合、代入値自動登録設定で登録した具体値はホスト変数定義ファイル（host_vars）に出力され、ansibleが扱う変数具体値の優先順位は「ホスト変数定義ファイルの値」＞「defaults変数定義ファイルの値」となります。

## Ansible共通メニュー構成

Ansible共通のメニュー一覧: 機器一覧（作業対象機器情報の管理）、インターフェース情報（実行エンジンの選択と接続情報管理）、Ansible Automation Controllerホスト一覧（RestAPI実行・資材転送用情報の管理）、グローバル変数管理／グローバル変数（センシティブ）管理（共通利用変数の管理）、ファイル管理／テンプレート管理（共通利用の素材ファイル・テンプレートと埋込変数の管理）、実行環境定義テンプレート管理／実行環境管理（Ansible Execution Agent内の実行環境定義ファイルのテンプレートとパラメータシートの紐付管理）、エージェント管理（接続Agentの名称・バージョン閲覧）、管理対象外変数リスト（代入値自動登録設定に表示したくない変数の管理）、共通変数利用リスト（非表示メニュー。各変数がどの素材で使用されているか閲覧）、Ansible Automation Platform (Cloud)連携用資材（非表示メニュー。実行エンジンAAP Cloud利用時の内部処理用）。非表示メニューは「管理コンソール→ロール・メニュー紐付管理」で復活処理が必要です。

## 機器一覧

作業対象機器情報をメンテナンス（閲覧/登録/更新/廃止）します。インストール時にローカル実行用機器「localhost」が登録されます（pioneerでは使用不可）。

主な項目: 管理システム項番（自動採番）、HW機器種別（NW/ST/SV）、ホスト名（必須、Ansibleインベントリホストとして使用、最大255バイト）、DNSホスト名、IPアドレス（IPv4形式）、ログインユーザ/パスワード、ssh鍵認証情報（秘密鍵ファイル・パスフレーズ、登録後ダウンロード不可）。

**Ansible利用情報（Legacy/Role利用情報）の認証方式**: パスワード認証（パスワード必須）、鍵認証（パスフレーズなし/あり、秘密鍵ファイル必須）、パスワード認証（winrm）、証明書認証(winrm)（公開鍵・秘密鍵ファイル必須）。WinRM接続情報にポート番号（未入力時5985）、winrm公開鍵/秘密鍵ファイルを設定。

**Pioneer利用情報**: プロトコル（ssh: パスワード認証(winrm)以外を選択／telnet: 認証方式を使わずユーザ・パスワードで接続）、OS種別（Ansible-Pioneer→OS種別から登録）、LANG（未選択時utf-8）。

**接続オプション**: ssh/telnet接続時のオプション（最大4000バイト）。**インベントリファイル追加オプション**: ITA作成のインベントリファイルに追加するyaml形式パラメータ（Ansible-Pioneerでは適用外）。値は変数（`{{△vvv△}}`）で記述可能、具体値は代入値自動登録設定から登録。**Ansible Automation Controller利用情報**: インスタンスグループ名（クラスタ構成時、未選択ならデフォルトのインスタンスグループ）、接続タイプ（通常は「machine」。`ansible_connection: local`が必要なNetwork OS等では「Network」を選択し、インベントリファイル追加オプションにPlatform Optionsの設定が必要）。

## インターフェース情報

実行エンジン（Ansible Core／Ansible Automation Controller／Ansible Execution Agent／Ansible Automation Platform(Cloud)）を選択し、接続情報をメンテナンス（閲覧/更新）します。

主な項目: 実行エンジン（必須）。Ansible Automation Controllerインターフェース（実行エンジンがAACの場合必須）: 代表ホスト（AAP 2.4はAAPノード一覧からAAC選択、2.5/Cloudはノード一覧からPlatform Gateway選択）、プロトコル（http/https）、ポート（通常https:443）、組織名（AAC同期データから選択）、認証トークン（最大255バイト）、REST APIタイムアウト値（60〜3600秒、未入力時60秒）。Proxy Address/Port（プロキシ環境下で疎通に必要な場合）。実行時データ削除（True/False。実行エンジンがAACかAgentの場合必須。Trueで作業終了後に一時データリソースを削除）。Ansible-vaultパスワード（最大64バイト、未入力時デフォルト値）。オプションパラメータ（Movement共通のオプション、最大4000バイト。実行エンジンがCore/Agentならansible-playbookコマンドのオプション、AACならジョブテンプレートのパラメータ）。NULL連携（True/False。パラメータシート具体値がNULLの場合に代入値管理へNULL登録するか。各Movementの代入値自動登録設定で未選択の場合に適用、未選択時False）。状態監視周期（1000〜2147483647ミリ秒、推奨1000ミリ秒）。進行状態表示行数（0〜2147483647、推奨1000行。未実行/準備中/準備完了/実行待ち/実行中/実行中(遅延)は指定行数、完了系ステータスは全ログ出力）。実行エンジンがAAP(Cloud)の場合、ホスト以外の入力は不要です。

## Ansible Automation Platform ノード一覧

AAPへのRestAPI実行・構築資材の連携に必要な情報をメンテナンス（閲覧/登録/更新/廃止）します。クラスタ構成の場合は全ノードを登録（hop nodeは不要）。AAP 2.5ではPlatform GatewayとExecution Node(Hybrid Node含む)を登録（Controller Node・Hop Nodeは不要）。

主な項目: ホスト（Controller/Execution/Hybrid NodeまたはPlatform Gatewayのホスト名/IP、最大255バイト、必須）、認証方式（Execution/Hybrid Nodeへのscp接続用。パスワード認証／鍵認証(パスフレーズなし/あり)。Platform Gatewayはこの設定を使用しない）、ユーザ/パスワード（awxユーザ推奨）、ssh鍵認証情報、ポート（デフォルト22）、Execution node（True/False。AAP2.4はクラスタ構成でexecution nodeの場合True、AAP2.5/CloudはPlatform Gateway=False、Execution/Hybrid Node=True）。

## グローバル変数管理 / グローバル変数（センシティブ）管理

Playbookや対話ファイルで共通利用するグローバル変数をメンテナンス（閲覧/登録/更新/廃止）します。項目: グローバル変数名（`GBL_****`形式、半角英数字とアンダースコア、1〜255バイト、必須）、具体値（最大4000バイト。複数行可だがPioneer対話ファイルで使用時に複数行を設定すると作業実行時エラー）、変数名説明、備考。センシティブ管理では具体値が暗号化保存され、実行時にansible-vaultを通して使用されます（更新時に現在値は参照不可）。**グローバル変数名は通常管理とセンシティブ管理の間で一意である必要があり、両方に同名を登録できません。**

## ファイル管理 / テンプレート管理

**ファイル管理**: 共通利用のファイル素材とファイル埋込変数をメンテナンス（閲覧/登録/更新/廃止）します。項目: ファイル埋込変数名（`CPF_****`形式、1〜255バイト、必須）、ファイル素材（アップロード、最大100MB、必須）、備考。Playbookでは`- copy: src='{{ CPF_hosts }}' dest=/etc/hosts`のように記述（destにファイル名を含めない場合、登録ファイル名の前にITA管理番号が付与される）。

**テンプレート管理**: 共通利用のテンプレートファイル素材とテンプレート埋込変数を管理します。項目: テンプレート埋込変数名（`TPF_****`形式、1〜255バイト、必須）、テンプレート素材（テキスト形式、最大100MB、必須）、変数定義（テンプレート内で使用する変数を定義。通常変数・複数具体値変数・多段変数（LegacyRoleのみ使用可）・グローバル変数・ITA独自変数（定義不要）の5種類。同名変数をdefault変数定義ファイル等にも定義している場合は変数構造を一致させる必要があり、不一致だと登録エラー）、備考。内部処理での変数抽出はリアルタイムでないため、代入値自動登録設定で変数が扱えるまで時間がかかる場合があります。Playbookでは`- template: src='{{ TPF_hosts }}' dest=/etc/hosts`のように記述します。

大容量ファイルの登録時に「認証に失敗しました。」エラーが出る場合、ネットワーク状況等でアクセストークンが期限切れになったことが原因のため、アクセストークンの有効期間設定を確認・変更してください。

## 実行環境定義テンプレート管理 / 実行環境管理

**実行環境定義テンプレート管理**: Ansible Execution Agent内でansible-builderが実行環境（コンテナ）をbuildする際の定義ファイル(execution-environment.yml)のテンプレートをメンテナンスします（インストール時にpythonモジュール/ansible galaxyコレクション追加用テンプレートが登録済み）。項目: テンプレート名（最大255バイト、必須）、テンプレートファイル（Jinja2 template形式、最大100MB、必須）、備考。

**実行環境管理**: 登録したテンプレートファイルと「実行環境パラメータ定義」パラメータシートの紐付を管理します（インストール時に基本のパラメータシートと紐付も登録済み）。項目: 実行環境名（最大255バイト、必須）、実行環境構築方法（「ITA」= ansible-builderでbuild、実行環境定義名とテンプレート名が必須／「Manual」= buildせず、ITA外でbuildしたコンテナイメージを事前にAgentへロードしておく必要あり）、タグ名（イメージ名。ITA選択時は`{{organization_id}}_{{workspace_id}}_タグ名`、Manual選択時はタグ名がそのままイメージ名、最大255バイト、必須）、実行環境定義名（パラメータシート「実行環境パラメータ定義」から選択）、テンプレート名（実行環境定義テンプレート管理から選択）、備考。

## エージェント管理

接続済みAnsible Execution Agentのエージェント名・バージョンを閲覧します。ステータス: 「正常（最新）」（バージョン一致）、「正常（更新可能）」（バージョン不一致だが互換性あり、更新推奨）、「連携不可（要更新）」（バージョン不一致で互換性なし、更新必須）。

## 管理対象外変数リスト

変数抜出対象資材から抜出した変数のうち、各モードの代入値自動登録設定の「Movement名:変数名」に表示したくない変数をメンテナンス（参照/更新/廃止/復活）します（インストール時にansibleマジック変数が登録済み）。項目: 変数名（正規表現指定可、例: `ansible_*`、`ansible_[0-9a-zA-Z]*`、最大255バイト、必須）、備考。

## Ansible Automation Platform (Cloud)連携用資材

AAP(Cloud)方式での作業実行時に使用する内部処理用メニューで、リソースの自動登録・管理を行います（内部処理により自動更新されるため手動編集は非推奨。デフォルト非表示、使用時はロール・メニュー紐付管理で有効化）。

APIエンドポイント: `GET /api/{organization_id}/workspaces/{workspace_id}/aap/{execution_no}/populated_data`（ITA独自資材の取得）、`POST /api/{organization_id}/workspaces/{workspace_id}/aap/{execution_no}/result_data`（結果ファイルの送信）。アクセスには実行エージェントと同等の権限が必要です。

**動作フロー**: ①ITAがAAP Platform GatewayにREST API経由でリソース作成・作業実行を指示 → ②AAP Execution Node上のPlaybook（EE上のlocalhost）がITA APIにGETし投入データ（zip）を取得・展開 → ③Execution NodeでPlaybookを実行 → ④実行完了後、Execution Node（EE上のlocalhost）がITA APIにPOSTし結果データ（zip）を送信 → ⑤ITAで結果確認。従来のSSH/SCP方式と異なりAAPからITAへのpull型通信となり、APIでサービスアカウントを使用します。

## 付録: 実行環境定義テンプレートとパラメータシート「実行環境パラメータ定義」

テンプレートファイルはJinja2形式で、ansible-builderのexecution-environment.yml仕様に準じます。パラメータシート「実行環境パラメータ定義」の項目: execution_environment_name（レコード名、必須、最大255バイト）、python_requirements_file（pip追加インストール対象。空ファイル不可、必須）、galaxy_requirements_file（ansible-galaxyコレクション。空ファイル不可）、bindep_file（dnf追加インストール対象。空ファイル不可、必須）、ansible_runner（"ansible_runner"を入力、必須）、image（ベースイメージ、必須）、package_manager_path（パッケージ管理コマンドパス、必須）。

新規作成・更新時の注意: パラメータシート名(rest)は「execution_environment_parameter_definition_sheet」で始める、作成対象はデータシート、項目にRest API用項目名`execution_environment_name`（文字列単一行、最大255バイト）を含める、テンプレートファイル内の変数と同名の項目を用意する（項目名=変数名、設定値=変数値としてテンプレートに埋め込む）。Pythonをpython3.11に変更しローカル実行する場合は、機器一覧のlocalhostの「インベントリファイル追加オプション」の`ansible_python_interpreter`も`/usr/bin/python3.11`に合わせて更新が必要です。

## 付録: BackYardコンテンツ（AACデータ同期）

実行エンジンがAACの場合、以下をAACから取得します: 組織名（インターフェース情報の組織名リスト用。認証トークンのユーザが利用可能な組織）、インスタンスグループ（機器一覧のインスタンスグループリスト用。選択組織が利用可能なもの）、実行環境（Movement一覧の実行環境リスト用。選択組織が利用可能なもの）。

## 付録: ITAが作成するインベントリファイル

```yaml
all:
  children:
    hostgroups:
      hosts:
        Inventory_host:
          Inventory_host_parameters:
          Inventory_host_option_parameters:
```

`Inventory_host`は機器一覧のホスト名、`Inventory_host_option_parameters`はインベントリファイル追加オプション。`Inventory_host_parameters`は認証方式に応じて以下を設定（未入力項目は設定しない）: `ansible_host`（全認証方式、DNSホスト/IPアドレス）、`ansible_user`（証明書認証(winrm)以外）、`ansible_password`（パスワード認証／パスワード認証(winrm)）、`ansible_ssh_private_key_file`（鍵認証各種）、`ansible_ssh_extra_args`（パスワード認証・鍵認証各種）、`ansible_connection: winrm`（winrm系）、`ansible_port`／`ansible_winrm_cert_pem`／`ansible_winrm_cert_key_pem`（winrm系）。

## 付録: オプションパラメータ一覧

インターフェース情報とMovement一覧のオプションパラメータについて、単一値パラメータを両方で定義した場合はMovement一覧側が優先されます。実行エンジンがCore/Execution Agentの場合はansible-playbookコマンドのオプション（`ansible-playbook -h`でヘルプ参照）。AACの場合、指定可能な主なオプション: `-v/--verbose`（詳細度、vの合計値を適用、6以上は5扱い）、`-f/--forks`（フォーク数、複数指定時は最後の値が有効）、`-l/--limit`（対象ホスト名、最後の値が有効）、`-e/--extra-vars`（追加変数、json/yaml形式、最後の値が有効）、`-t/--tags`（ジョブタグ、複数指定可）、`-b/--become`（権限昇格有効化）、`-D/--diff`（変更差分表示）、`--skip-tags`（スキップタグ、複数指定可）、`--start-at-task`（AAC WebUIには表示なし）、`-ufc/--use_fact_cache`（ファクトキャッシュ有効化）、`-as/--allow_simultaneous`（同時実行ジョブ有効化）、`-jsc/--job_slice_count`（ジョブスライス数）。詳細はAAC公式マニュアルのジョブテンプレートを参照。

## 付録: 実行時データ削除で削除されるデータリソース

「実行時データ削除」をtrueにした場合の削除対象。**AAC側**: ITA作業用ディレクトリ（`/var/lib/exastro/ita_<区分>_executions_作業番号`）、SCM管理ディレクトリ（プロジェクトリソース削除に伴い削除）、インベントリ・認証情報・プロジェクト・ジョブテンプレート・ワークフロージョブテンプレート・ジョブの各リソース（`ita_<区分>_executions_*_作業番号`系の名前）。<区分>はlegacy/legacy_role/pioneer。**ITA側**: Gitリポジトリ（`/tmp/git_repositories/<区分>_作業番号`、設定値に関係なく常に削除）。**Ansible Execution Agent側**: ITA作業用ディレクトリ（`<storage>/<org>/<ws>/driver/ag_ansible_execution/<区分>/作業番号`、`<storage>/<org>/<ws>/ag_ansible_execution/status`）。

## 付録: Ansible Automation ControllerでITA独自変数を利用する場合の留意事項

`__workflowdir__`、`__conductor_workflowdir__`、`__movement_status_filepath__`、`__parameters_dir_for_epc__`、`__parameters_file_dir_for_epc__`、`__parameter_dir__`、`__parameters_file_dir__`を利用してファイル出力するPlaybookを含むMovementを、クラスタ構成のAACで実行する場合の注意事項です。

出力先ディレクトリはAACのITA作業用ディレクトリ配下`/var/lib/exastro`に設定されます。Movement実行前にConductor/Movement配下のファイルが各実行ノードの当該ディレクトリに転送され、実行後に作成されたファイルが結果データ（またはConductor共有領域）へ上書きモードで転送されます。同一ファイル名で作成した場合、更新ファイルが正しく反映されない場合があります。

**留意事項**: ①ファイル名にはansibleの`inventory_hostname`を含めるなどし、作業対象ホスト毎に同一ファイル名で出力しないようにする。②Conductorから実行する場合、複数のMovementで同一ファイル名に出力しないようにする。
