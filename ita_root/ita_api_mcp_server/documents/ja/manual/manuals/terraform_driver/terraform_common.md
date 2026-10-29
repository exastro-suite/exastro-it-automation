# Terraform driver 共通機能（変数の取り扱い・構築コード）

## 概要

Terraformは HashiCorp社が提供するインフラストラクチャオーケストレーションツールで、HCL（HashiCorp Configuration Language）でコード化したインフラ構成の実行計画を生成し構築を実行します。Terraform CloudおよびTerraform EnterpriseではPolicy as Codeによるアクセスポリシー管理も可能です。

Terraform driverはITAの機能として、Terraformへの実行および実行ログ取得を行います。作業実行（Plan/Apply）に使うModuleファイルと、PolicyCheckに使うPolicyファイルをITA上で部品化・再利用可能に管理できます。また、Module中の変数を画面から設定できます。

Terraform driverには2種類あります。

- **Terraform Cloud/EP driver**: ITAで登録したTerraform Cloud/EnterpriseへOrganization/Workspaceの作成、作業実行（Plan/PolicyCheck/Apply）、作業ログ取得を行う。
- **Terraform CLI driver**: ITAと同一環境内にインストールしたTerraformへ、作業実行（Plan/Apply）と作業ログ取得を行う。

## 変数の取り扱い

Terraform driverでは、Module中の変数の具体値をITAの設定画面から設定できます。ModuleファイルのVariableブロックに定義した対象が変数として扱われます。

- **通常変数**: 変数名に対して具体値を定義する変数。HCLのVariableブロック（`variable "xxx" { type = ○○  default = △△ }`）のルールに従って記述し、typeとdefaultの設定は必須ではありません。

ITAにアップロードされたModule素材から変数を抜出し、具体値をパラメータシートと連携させて登録します。Terraform Cloud/EP driverでは連携先TerraformのWorkspace管理Variablesに「変数名」がKey、「具体値」がValueとして登録されます。Terraform CLI driverでは作業実行時に生成される`terraform.tfvars`ファイルに同様に記載されます。

### 変数タイプ

| type | 詳細 | メンバー変数対象 | 代入順序対象 | typeの記述例 | defaultの記述例 |
|---|---|---|---|---|---|
| string | 文字列型 | × | × | string | あいう |
| number | 数字型 | × | × | number | 123 |
| bool | Boolean型（true/false） | × | × | bool | true |
| list | 配列型 | × | 〇 | list(string) | ["あ","い","う"] |
| set | 配列型（ユニーク値。ITA上ではユニーク判定は行われない） | × | 〇 | set(number) | [1,2,3] |
| tuple | 配列型（n番目の型が固定。ITA上ではプルダウン選択） | 〇 | × | tuple([string, number]) | ["あいう", 2023] |
| map | key-value型。map型を含むtypeは代入値自動登録設定でHCL設定をONにする必要あり | × | × | map(string) | {"test_key"="test_value"} |
| object | key-value型。key名をメンバー変数として扱う（日本語不可） | 〇 | × | object({test_key=string}) | {"test_key"="test_value"} |
| any | ITA上ではstring型と同様の扱い | × | × | any | あいう |
| 記載なし | ITA上ではstring型と同様の扱い | × | × | - | あいう |

**メンバー変数対象**（key-value型の場合のkey名）: object型は`<KEY>=<TYPE>`のKEY、tuple型は先頭から`[0],[1],[2]...`と採番。変数ネスト管理の登録対象は最大繰返数をもとに`[0],[1],[2]...`と採番。

例（object型 `VAR_hoge { type = object({NAME=string, IP=string}) }`）: メンバー変数`NAME`に`my_machine`、`IP`に`192.168.100.1`を登録すると、Terraformには `{ NAME="my_machine" IP="192.168.100.1" }` が送信される。tuple型（`type = tuple([string,number])`）は `[0]`に`def`、`[1]`に`2024`を登録すると `["def", 2024]` が送信される。ネスト管理対象（`type = list(set(string))`）は`[0]`の1,2番目、`[1]`の1,2番目に値を登録すると `[["あああ","いいい"],["ううう","えええ"]]` のように送信される。

**代入順序対象**（複数具体値を設定する際の先頭からの代入順序）: 変数または階層構造の最下層の変数タイプがlist/setの場合に設定可能。例えば`list(string)`型に代入順序1,2で値`あいう`,`かきく`を登録すると`["あいう","かきく"]`が送信される。`object({key=set(number)})`型でkeyに順序1,2の値`1,2`を登録すると`{key=[1,2]}`が送信される。

## 構築コード記述方法

- **Module**: HCL（HashiCorp Configuration Language）で記述します。詳細はTerraformの製品マニュアルを参照してください。
- **Policy**: Sentinel languageで記述します（Terraform Cloud/EP driverのみ有効な機能）。詳細はTerraformの製品マニュアルを参照してください。
