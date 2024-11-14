### Exastro IT Automation
#   Ansible Execution Agent

### 概要
    Ansible実行エージェント：Ansibeの作業実行を、Pull型で行うためのエージェント機能
    ・ITA本体との通信は、http/httpsの、クローズド環境からアウトバウンドのみ（PULL型）​
    ・Ansible BuilderとAnsible Runnerを使った動的なAnsible作業実行環境の生成​（任意の環境・モジュールを利用可能）​
    ・冗長可能な仕組み（排他制御）

### ハードウェア要件(最小構成)
    CPU 2Cores
    メモリ	6GB
    ディスク容量	40GB

    ※ディスク容量は、エージェントサービスの件数や、作業実行結果の削除設定、ビルドするimageサイズに依存するため、
    　必要に応じて、サイジング、及びメンテナンス（Docker Image や Build Cache等について）を実行してください。

### OS要件
    RHEL9:
        Red Hat Enterprise Linux release 9.4 (Plow)：(動作確認済み)
    Almalinux8:
        AlmaLinux release 8.9 (Midnight Oncilla)：(動作確認済み)

    ※SELinuxがPermissiveに変更されていること。
        $ sudo vi /etc/selinux/config
            SELINUX=Permissive

        $ getenforce
            Permissive

    ※サブスクリプションの登録は、インストーラ実行前に実施しておいてください。

### RHEL(サポート付きライセンス利用の場合)
    有償版のAnsible-builder、Ansible-runnerを利用する場合、サブスクリプションの登録、リポジトリ有効化は、インストーラ実行前に実施しておいてください。

    ・Red Hat コンテナーレジストリーの認証
        podman login registry.redhat.io

    ・利用するリポジトリ
        rhel-9-for-x86_64-baseos-rpms
        rhel-9-for-x86_64-appstream-rpms
        ansible-automation-platform-2.5-for-rhel-9-x86_64-rpms

    ・有効化されているリポジトリの確認、リポジトリの有効化
        sudo subscription-manager repos --list-enabled
        sudo subscription-manager repos --enable=rhel-9-for-x86_64-baseos-rpms
        sudo subscription-manager repos --enable=rhel-9-for-x86_64-appstream-rpms
        sudo subscription-manager repos --enable=ansible-automation-platform-2.5-for-rhel-9-x86_64-rpms

### Ansible builderで使用する動作確認済みのベースイメージ
    ITAの画面で、入力用→実行環境バラメータ定義→Imageにて、指定します。
    registry.access.redhat.com/ubi9/ubi-init:latest
    registry.redhat.io/ansible-automation-platform-24/ee-supported-rhel8:latest 	(サポート付きライセンス利用の場合)

### ソフトウェア要件
    Python3.9以上がインストールされていること。
    以下、コマンドが実行できること
        ・sudo

        ・python3 -V
            Python 3.9.18
        ・pip3 -V
            pip 21.2.3 from /usr/lib/python3.9/site-packages/pip (python 3.9)

### 通信要件
    エージェントサーバから、外部NWへの通信が可能なこと
        ・接続先のITA
        ・各種インストール、及びモジュール、BaseImage取得先等（インターネットへの接続を含む）
        ・作業対象サーバ

### エージェントサービスの前提条件
    エージェントサーバ→ITAへのアウトバウンド通信が許可されていること
    以下、上記の各種要件を満たしていること
        ・ハードウェア要件
        ・OS要件
        ・ソフトウェア要件
       ・ 通信要件


### インストーラ実行の事前準備
    以下から、setup.shをDLし、インストールするサーバに配置してください。
        wget https://raw.githubusercontent.com/exastro-suite/exastro-it-automation/refs/heads/main/ita_root/ita_ag_ansible_execution/setup.sh
    インストーラを実行するユーザーが実行できる権限に変更してください。
        chmod 755 setup.sh

    インストーラを実行
    ./setup.sh <install / uninstall>

### エージェントインストーラでの対話事項
    エージェントのバージョン情報
    サービス名
    ソースコードのインストール先
    データの保存先
    使用するAnsible-builder　Ansible-runnerについて
    接続先のITAの接続情報（URL、ORGANIZATION_ID、WORKSPACE_ID、REFRESH_TOKEN）


### エージェントサービスのインストール
    ./setup.sh install

    ①以下で、エージェントのインストールモードを聞かれるので、指定してください。
        1: 必要なモジュールのインストール、サービスのソースコードのインストール、サービスの登録・起動を行います。
        2: 追加でサービスの登録・起動を行います。
        3: envファイルを指定して、サービスの登録・起動を行います。
        ※ 2.3については、1が実行されている前提になります。

    Please select which process to execute.
        1: Create ENV, Install, Register service
        2: Create ENV, Register service
        3: Register service
        q: Quit installer
    select value: (1, 2, 3, q)  :

    以下、「default: xxxxxx」がある項目については、Enterを押下すると、defaultの値が適用されます。

    以下①で、1, 2を指定した場合です。

        ②以下、Enterを押下すると、必要な設定値を対話形式での入力が開始されます。
        'No value + Enter' is input while default value exists, the default value will be used.
        ->  Enter

        ③インストールするエージェントのバージョンを指定できます。デフォルトでは、最新のソースコードが使用されます。
        Input the version of the Agent. Tag specification: X.Y.Z, Branch specification: X.Y [default: No Input+Enter(Latest release version)]:
        Input Value [default: main ]:

        ④インストールするエージェントサービスの名称を設定すす場合は、nを押して以降の対話で、指定してください。
        The Agent service name is in the following format: ita-ag-ansible-execution-20241112115209622. Select n to specify individual names. (y/n):
        Input Value [default: y ]:

        ⑤↑で「n」を入力した場合のみこちら表示されます。
        Input the Agent service name . The string ita-ag-ansible-execution- is added to the start of the name.:
        Input Value :

        ⑥ソースコードのインストール先を指定する場合は入力してください。
        Specify full path for the install location.:
        Input Value [default: /home/cloud-user/exastro ]:

        ⑦データの保存先を指定する場合は入力してください。
        Specify full path for the data storage location.:
        Input Value [default: /home/cloud-user/exastro ]:

        ⑧使用するAnsible-builder　Ansible-runnerを指定してください。
        　償版を利用する場合は、リポジトリ有効化したうえで、2を指定してください。
        Select which Ansible-builder and/or Ansible-runner to use(1, 2) [1=Ansible 2=Red Hat Ansible Automation Platform] :
        Input Value [default: 1 ]:

        ⑨接続先のITAのURLを指定してください。　e.g. http://exastro.example.com:30080
        Input the ITA connection URL.:
        Input Value :

        ⑩接続先のITAのORGANIZATIONを指定してください。
        Input ORGANIZATION_ID.:
        Input Value :

        ⑪接続先のITAのWORKSPACEを指定してください。
        Input WORKSPACE_ID.:
        Input Value :

        ⑫接続先のITAのリフレッシュトークンを指定してください。（トークンの取得方法は以下、参照。）
            https://ita-docs.exastro.org/ja/2.4/manuals/platform_management/general.html#id8
        後で設定する場合は、Enter押して次に進んでください。
　　　　.envのEXASTRO_REFRESH_TOKENを書き換えてください。

        Input a REFRESH_TOKEN for a user that can log in to ITA. If the token cannot be input here, change the EXASTRO_REFRESH_TOKEN in the generated .env file.:
        Input Value [default:  ]:

        ⑬サービスの起動を行う場合は、を選択してください。起動しない場合は、後ほど手動で起動してください。
        Do you want to start the Agent service? (y/n)y

        ⑭インストールしたサービスの情報が表示されます。
        Install Ansible Execution Agent Infomation:
            Agent Service id:   <サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
            Agent Service Name: ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
            Storage Path:       /home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/storage
            Env Path:           /home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/.env


    以下①で、3を指定した場合です。
        ③使用する.envのパスを指定してください。envの情報をもとに、サービスの登録・起動を行います。
        Input the full path for the .env file.:
        Input Value :

        ⑬サービスの起動を行う場合は、を選択してください。起動しない場合は、後ほど手動で起動してください。
        Do you want to start the Agent service? (y/n)y

        ⑭インストールしたサービスの情報が表示されます。
        Install Ansible Execution Agent Infomation:
            Agent Service id:   <サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
            Agent Service Name: ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
            Storage Path:       /home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/storage
            Env Path:           /home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/.env


### エージェントサービスの各種操作

AlmaLinux
    systemctl daemon-reload
    systemctl status  ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
    systemctl start ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
    systemctl stop  ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
    systemctl restart  ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>

RHEL9
    systemctl --user daemon-reload
    systemctl --user status  ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
    systemctl --user start ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
    systemctl --user stop  ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
    systemctl --user restart  ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>


### エージェントサービスのアンインストール
    以下、アンインストールでは、サービスの削除、データの削除は実施可能ですが、アプリケーションのソースコードは、削除されません。
    削除する場合は、手動での対応が必要となります。

    ./setup.sh uninstall

    ①以下で、エージェントのアンインストールモードを聞かれるので、指定してください。
        1: サービスの削除、データの削除を行います。
        2: サービスの削除、を行います。データは削除されません。
        3: データの削除
        ※ 3については、2が実行されている前提になります。

    Please select which process to execute.
        1: Delete service, Delete Data
        2: Delete service
        3: Delete Data
        q: Quit uninstaller
    select value: (1, 2, 3, q)  :

    以下①で、1, 2を指定した場合です。

        ②アンインストールするエージェントのサービス名（ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>）を指定してください。
        Input a SERVICE_NAME.(e.g. ita-ag-ansible-execution-xxxxxxxxxxxxx):

        ③②で指定した、サービス名のデータの保存先を指定してください。
        Input a STORAGE_PATH.(e.g. /home/cloud-user/exastro/<SERVICE_ID>):


    以下①で、2を指定した場合です。
        ②アンインストールするエージェントのサービス名（ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>）を指定してください。
        Input a SERVICE_NAME.(e.g. ita-ag-ansible-execution-xxxxxxxxxxxxx):

    以下①で、3を指定した場合です。
        サービス削除済みのサービス名のデータの保存先（<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>）を指定してください。
        Input a STORAGE_PATH.(e.g. /home/cloud-user/exastro/<SERVICE_ID>):


### エージェントサービスの構成
    以下、デフォルトの設定値で、インストールした場合

    サービスのアプリケーションソースコード
        /home/cloud-user/exastro/ita_ag_ansible_execution/
    各種データの保存領域
        /home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/storage
    サービスの設定ファイル(.env)
        /home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/.env
    ログ出力先
        /home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/log

    ※作業実行（Ansible実行）の作業領域については、各コンポーネント（Ansible-builder, Ansible-runner及び関連コンポーネント）の仕様や、ドキュメントを参照してください。

### エージェントサービスの設定値
    作成された.envファイル
        LOG_LEVEL=INFO
        #LOGGING_MAX_SIZE=10485760
        #LOGGING_MAX_FILE=30
        LANGUAGE=en
        TZ=Asia/Tokyo
        PYTHON_CMD=/home/cloud-user/.local/bin/poetry run python3
        PYTHONPATH=/home/cloud-user/exastro/ita_ag_ansible_execution/
        APP_PATH=/home/cloud-user/exastro
        STORAGEPATH=/home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/storage
        LOGPATH=/home/cloud-user/exastro/<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>/log
        EXASTRO_ORGANIZATION_ID=<接続先のITAのオーガナイゼーション>
        EXASTRO_WORKSPACE_ID=<接続先のITAのワークスペース>
        EXASTRO_URL=<払い出したリフレッシュトークン:http://exastro.example.com:30080>
        EXASTRO_REFRESH_TOKEN=<払い出したリフレッシュトークン:xxxxxxx>
        EXECUTION_ENVIRONMENT_NAMES=
        AGENT_NAME=ita-ag-ansible-execution-<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
        USER_ID=<サービスの一意な識別子:yyyyMMddHHmmssfff or 対話で指定した文字列>
        ITERATION=10
        EXECUTE_INTERVAL=5

    以下の設定値については、インストーラで固定値で設定されますので、必要に応じて、コメントアウト外す、値を変更してください。
        LOG_LEVEL=INFO                  :ログ出力のレベル <INFO/DEBUG>
        #LOGGING_MAX_SIZE=10485760      :ログローテートするファイルサイズ
        #LOGGING_MAX_FILE=30            :ログローテートされたバックアップ数
        EXECUTION_ENVIRONMENT_NAMES=    :実行環境名を指定　※1
        ITERATION=10                    :サービスの実行スクリプト中に、実行するpythonの回数
        EXECUTE_INTERVAL=5              :処理実行のインターバルの時間

        ※1 Ansible共通→実行環境管理→実行環境名のものを,区切りで指定してください。
            デフォルト状態（指定無し）では、全てを作業実行対象として動作します。
            指定されている場合、該当する実行環境名で実行された作業のみを作業対象とみなします。
