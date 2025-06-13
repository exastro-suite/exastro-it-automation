# Red Hatライセンス自動投入手順

## 概要
本作業手順を実行することで、Ansible実行エージェントのインストールに必要なライセンスを自動投入することが可能です。

## 前提条件

### 設定ファイル（.env）
下記の項目が揃っている設定ファイルが必須となります。

※REPO_LISTは利用するリポジトリに応じて書き換えが可能です。

| 環境変数名                   | 備考           |
|------------------------------|----------------|
| ITA_PROTCOL                  | 変更不可       |
| ITA_HOST                     | 変更不可       |
| ITA_PORT                     | 変更不可       |
| ITA_EXASTRO_ORG_ID           | 変更不可       |
| ITA_EXASTRO_WS_ID            | 変更不可       |
| ITA_REFRESH_TOKEN            | 変更不可       |
| PASSPHRASE                   | 変更不可       |
| KANRI_ID                     | 変更不可       |
| AAP_REGISTER_FLG             | 変更不可       |
| AAH_LOGIN_FLG                | 変更不可       |
| AAH_CONTAINER_IMAGE_REGISTRY | 変更不可       |
| REPO_LIST                    | **※変更可能**, カンマ区切り |


### OS
動作保証がされているOS・バージョンは下記となります。
| OS                       | 動作確認済みバージョン |
| ------------------------ | ---------------------- |
| Red Hat Enterprise Linux | 9.4                    |

### スクリプトの実行ユーザー
スクリプトを実行するユーザーは下記の条件を満たしている必要があります。
- 一般ユーザー
- sudoコマンドが利用可能

### 注意事項
- すでにAnsible実行エージェントが稼働している環境で、スクリプトを利用することはできません。

## 作業手順

### 1. 資材の配置
- シェルスクリプト取得
    
    下記コマンドでシェルスクリプトを取得します。
    ```
    wget https://raw.githubusercontent.com/exastro-suite/exastro-it-automation/refs/heads/2.6/tools/RegisterLicense/client-licence_registration.sh
    ```

- 設定ファイル配置

    事前に用意した設定ファイルをシェルスクリプトと同じディレクトリに配置します。
    
    ※ファイル名は必ず「.env」である必要があります。

### 2. ライセンス投入

- シェルスクリプト実行
    ```
    sh client-license_registration.sh
    ```
- 正常終了確認
    
    下記例のログが表示されると正常終了となります。
    ```
    Thu Jun 12 17:55:31 JST 2025 [INFO]: Process completed successfully.
    ```
    ※上記のログが表示されない場合は、処理が異常終了しています。
    原因を確認するため、出力されたログ内容を確認してください。

## その他
### 実行ログ
実行ログファイルは、シェルスクリプトと同じディレクトリに作成されます。
- ファイル名：exastro-ansible-license-registration.log