# Terraform Cloud/EP driverの設定と利用方法

Terraform Cloud/EP driverは、ITAで登録したTerraform CloudまたはTerraform Enterpriseに対し、Organization/Workspaceの作成、作業実行（Plan/PolicyCheck/Apply）、作業ログ取得を行う機能です。TerraformおよびTerraform driver共通の概念（変数の取り扱いなど）は「Terraform driver 共通」を参照してください。

## メニュー構成

基本コンソール:

| No | メニューグループ | メニュー/画面 | 説明 |
|---|---|---|---|
| 1 | 基本コンソール | オペレーション一覧 | オペレーション一覧をメンテナンス（閲覧/登録/更新/廃止）できます。 |

Terraform Cloud/EP:

| No | メニュー・画面 | 説明 |
|---|---|---|
| 1 | インターフェース情報 | ITAと連携するTerraformの情報を管理します。 |
| 2 | Organization管理 | Terraformで利用するOrganizationの情報を管理します。 |
| 3 | Workspace管理 | Terraformで利用するWorkspaceの情報を管理します。 |
| 4 | Movement一覧 | Movementの一覧を管理します。 |
| 5 | Module素材集 | Moduleファイルを管理します。 |
| 6 | Policy管理 | Policyファイルを管理します。 |
| 7 | Policy set管理 | Policy SetはPolicyおよびWorkspaceと紐づけることで、作業実行時に対象のWorkspaceに対してPolicyを有効にします。 |
| 8 | Policy set-Policy紐付 | Policy setとPolicyの紐付けを管理します。 |
| 9 | Policy set-Workspace紐付 | Policy setとWorkspaceの紐付けを管理します。 |
| 10 | Movement-Module紐付 | MovementとModule素材の関連付けを管理します。 |
| 11 | 変数ネスト管理 | 変数タイプがlist/setかつ内部にlist/set/tuple/objectを含む場合、メンバー変数の最大繰返数を管理します。 |
| 12 | 代入値自動登録設定 | パラメータシートの項目・値をMovementの変数に紐付けます。 |
| 13 | 作業実行 | 実行するMovementとオペレーションを選択し実行を指示します。 |
| 14 | 作業管理 | 作業実行履歴を管理します。 |
| 15 | 作業状態確認 | 作業実行状態を表示します。 |
| 16 | 代入値管理 | 変数の代入値を管理します。 |
| 17 | 連携先Terraform管理 | 連携先Terraformに登録されているOrganization, Workspace, Policy, PolicySetの一覧表示・削除を行います。 |
| 18〜21 | Module-変数紐付／メンバー変数管理／Movement-変数紐付／Movement-メンバー変数紐付（非表示メニュー） | 内部機能でデータの登録・更新を行うメニュー。表示するには「管理コンソール→ロール・メニュー紐付管理」で復活処理が必要。 |

## 作業フロー

1. 基本コンソールのオペレーション一覧に投入オペレーション名を登録。
2. インターフェース情報（連携先TerraformのHostname/UserTokenなど）を設定。
3. Organizationを登録し、Terraformと連携。
4. Workspaceを登録し、Terraformと連携。
5. Movementを登録。
6. Module素材を登録。
7. 必要に応じてPolicy／Policy set／Policy set-Policy紐付／Policy set-Workspace紐付を登録。
8. MovementにModule素材を紐付ける。
9. 必要に応じて変数ネスト管理で最大繰返数を設定。
10. 必要に応じてパラメータシートを作成しデータを登録、代入値自動登録設定でMovementの変数と紐付ける。
11. 作業実行画面でMovementと投入オペレーションを選択し実行。
12. 作業状態確認でリアルタイムに状態・ログを監視。
13. 作業管理で履歴を確認。

## Policyの適用

Policy機能の利用には、連携先TerraformがTerraform Enterprise、またはTerraform Cloudで「Policy & Security」機能が有効なプランである必要があります。適用手順:

1. 登録したPolicyとPolicy setを「Policy set-Policy紐付」で紐付ける。
2. 登録したWorkspaceとPolicy setを「Policy set-Workspace紐付」で紐付ける。
3. 作業実行時、Movementに紐付いたWorkspaceに対しPolicy setとそれに紐付けられたPolicyが適用される。

## インターフェース情報

ITAと連携するTerraformの情報をメンテナンス（閲覧/更新）します。連携対象のHostnameと、TerraformのUserが発行したUser Tokenが必要です。未登録または複数レコード登録された状態で作業実行すると想定外エラーになります。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| 連携先Terraform Protocol | http/https（通常https） | 必須 |
| 連携先Terraform Hostname | 連携先TerraformのHostname | 必須、最大256バイト |
| 連携先Terraform Port | 通常空欄 | 最小1、最大65535 |
| 連携先Terraform User Token | TerraformのUser Settingsより発行 | 最大1024バイト |
| Proxy Address / Port | ITAがプロキシ環境下にある場合、Terraformまでの疎通に必要な場合設定 | - |
| NULL連携 | 代入値自動登録設定でパラメータシートの具体値がNULLの場合の代入値管理への登録方法。代入値自動登録設定メニューの「NULL連携」が空白の場合に適用 | 必須 |
| 状態監視周期（単位ミリ秒） | 作業状態確認でのログのリフレッシュ間隔。推奨1000ミリ秒程度 | 最小1000ミリ秒、必須 |
| 進行状態表示桁数 | 進行ログ・エラーログの最大表示行数（未実行/準備中/実行中/実行中(遅延)時に適用。完了系ステータスでは全ログ出力）。推奨1000行程度 | 必須 |
| 備考 | 自由記述 | 最大4000バイト |

## Organization管理

TerraformのOrganizationをメンテナンス（閲覧/登録/更新/廃止）し、ITAに登録したOrganizationをTerraformへ連携（登録/更新/削除）できます。「状態チェック」ボタンで連携状態を確認、カラムグループ「Terraform連携」の「登録」「更新」「削除」ボタンで各操作を実行します。Organizationが連携（登録）されていない状態で作業実行すると想定外エラーになります。Hostname/UserTokenの誤りがあると「Terraformとの接続に失敗しました。インターフェース情報を確認して下さい。」と表示されます。削除すると元に戻せず、配下のWorkspaceも削除されます。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| Organization名 | 半角英数字と`_-`のみ | 必須、最大40バイト |
| Email address | OrganizationのEmail address | 必須、最大128バイト |
| 備考 | 自由記述 | 最大4000バイト |

## Workspace管理

TerraformのWorkspaceをメンテナンス（閲覧/登録/更新/廃止）し、ITAに登録したWorkspaceをTerraformへ連携（登録/更新/削除）、リソース削除（terraform destroy）を実行できます。「リソース削除」ボタンで作業状態確認に遷移し実行されます。Workspaceを削除するとリソース削除は実行不可、削除は元に戻せません。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| Organization名 | 登録したOrganization名を選択 | 必須、最大40バイト |
| Project名 | 空欄の場合「Default Project」に紐づく | 最大40バイト |
| Workspace名 | 半角英数字と`_-`のみ | 必須、最大90バイト |
| Terraform version | 空欄の場合、連携（登録）時に最新版が自動適用 | 必須、最大128バイト |
| 備考 | 自由記述 | 最大4000バイト |

## Movement一覧

Movement名をメンテナンス（閲覧/登録/更新/廃止）します。MovementはOrganization:Workspaceと紐付ける必要があるため、先にOrganization・Workspaceの登録が必要です。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| Movement名 | 任意の名称 | 必須、最大256バイト |
| オーケストレータ | 「Terraform Cloud/EP」が自動入力される | - |
| 遅延タイマー | 指定期間（1分〜）遅延時に警告表示。未入力なら警告なし | 単位:分 |
| Terraform利用情報（Organization:Workspace） | 登録した（Organizationに紐づく）Workspaceを選択 | 必須 |
| 備考 | 自由記述 | 最大4000バイト |

## Module素材集

ユーザーが作成したModuleをメンテナンス（閲覧/登録/更新/廃止）します。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| Module素材名 | 任意の名称 | 必須、最大255バイト |
| Module素材 | Module素材ファイルをアップロード | 必須、最大100MB |
| 備考 | 自由記述 | 最大4000バイト |

内部処理でModuleファイル内の変数を抜出しますが、リアルタイムではないため、代入値自動登録設定で変数が扱えるまで時間がかかる場合があります。

## Policy管理

Sentinel languageで記述したPolicyファイルをメンテナンス（閲覧/登録/更新/廃止）します。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| Policy名 | 半角英数字と`_-`のみ | 必須、最大255バイト |
| Policy素材 | Policyファイルをアップロード | 必須、最大100MB |
| 備考 | 自由記述 | 最大4000バイト |

## Policy set管理

Policy setをメンテナンス（閲覧/登録/更新/廃止）します。Policy set-Policy紐付・Policy set-Workspace紐付でPolicyおよびWorkspaceと紐付けることで、作業実行時にWorkspaceへPolicyを適用します。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| Policy set名 | 半角英数字と`_-`のみ | 必須、最大255バイト |
| 備考 | 自由記述 | 最大4000バイト |

## Policy set-Policy紐付 / Policy set-Workspace紐付

それぞれ登録済みのPolicy setとPolicy、またはPolicy setとWorkspaceの紐付けをメンテナンス（閲覧/登録/更新/廃止）します。項目は「Policy set名」「Policy名（またはWorkspace名）」「備考」（いずれもリスト選択、必須）です。

## Movement-Module紐付

登録したMovementとModule素材の紐付けをメンテナンス（閲覧/登録/更新/廃止）します。Movement実行時に紐付けたModule素材が適用され、1つのMovementに複数のModule素材を紐付け可能です。

## 変数ネスト管理

Module素材集のtfファイルで定義された変数タイプがlist/setかつ、内部にlist/set/tuple/objectが定義されている場合、メンバー変数の最大繰返数を閲覧・更新します（内部機能がレコード管理するため登録・廃止・復活不可）。

| 項目 | 説明 | 制約事項 |
|---|---|---|
| 変数名 / メンバー変数名（繰返し有） | Module素材で使用している変数（入力不可）。メンバー変数名は各階層を「.」で連結して表示 | - |
| 最大繰返数 | 初期値はtfファイルのdefault値から取得（記載なしなら1）。最終更新者が「Terraform Cloud/EP変数更新機能」以外の場合、Module素材更新で値は変更されない。上限は管理コンソールの識別ID「MAXIMUM_ITERATION_TERRAFORM-CLOUD-EP」で1〜1024の範囲で変更可能。 | 必須、1〜1024（設定により変動） |
| 備考 | 自由記述 | 最大4000バイト |

初期登録・繰返数更新もリアルタイムではないため、代入値自動登録設定で変数が扱えるまで時間がかかる場合があります。

## 代入値自動登録設定

パラメータシート（オペレーションあり）とMovementの変数を紐付けます。登録情報は作業実行時に「代入値管理」に反映されます。

| 項目 | 説明 | 必須 |
|---|---|---|
| パラメータシート(From) メニュー:項目 | パラメータシート（オペレーションあり）の項目を選択 | 〇 |
| パラメータシート(From) 代入順序 | バンドル有効時、パラメータシートの代入順序を入力 | バンドル有効時のみ |
| 登録方式 | Value型（設定値を具体値とする）／Key型（項目名称を具体値とする） | 〇 |
| Movement名 | 登録したMovement | 〇 |
| IaC変数(To) Movement名:変数名 | 紐付けたい変数を選択 | 〇 |
| IaC変数(To) HCL設定 | True/False。Trueにすると変数タイプを考慮せず入力値を1:1で設定可能（メンバー変数・代入順序は入力不可）。map型はTrueでのみ登録可能。他レコードでオペレーション・Movement・変数名一致時はHCL設定値の統一が必要。 | 〇 |
| IaC変数(To) Movement名:変数名:メンバー変数 | メンバー変数を選択（object/tuple型で必須、HCL設定Falseの場合） | 条件付き必須 |
| IaC変数(To) 代入順序 | list/set型で複数具体値を設定する場合の代入順序（1〜） | 条件付き必須 |
| NULL連携 | 空白の場合はインターフェース情報の設定値が適用される | - |
| 備考 | 自由記述 | 最大4000バイト |

メンバー変数を設定する場合、同じ変数内の他のメンバー変数の具体値もすべて設定する必要があります（未設定分にデフォルト値は使用されません）。

## 作業実行

Movementとオペレーションをそれぞれ選択し「作業実行」ボタンで作業状態確認に遷移し実行されます。

- **予約日時**: 未来日時を指定すると実行・Plan確認を予約可能。
- **実行**: Terraform Plan完了後にTerraform Applyが自動実行される。
- **Plan確認**: Terraform Planのみ実行し、Applyは実行しない。
- **パラメータ確認**: 投入パラメータの値のみ確認（Plan/Applyは実行しない）。

Outputブロックを含むModule素材をConductorから実行した場合、出力内容が `[Conductor作業ディレクトリパス]/[ConductorインスタンスID]/terraform_output_[作業No.].json` に保存され、同一Conductorの別Movementで参照できます。

## 作業状態確認

作業の実行状態を監視します。「実行種別」はPlan確認/リソース削除/通常のいずれか。想定外エラーの場合、インターフェース情報やOrganization/Workspaceの連携（登録）不備等が原因であればエラーログに表示、それ以外はアプリケーションログを確認します。「呼出元Conductor」はConductor経由実行時のみ設定。「Terraform利用情報」の「RUN-ID」はTerraform側の実行管理IDです（リソース削除時は呼出元Conductor・Movement・オペレーション・投入データが設定されない）。

- 実行ログ種別: plan.log（Terraform Plan）、policyCheck.log（Policy Check）、apply.log（Terraform Apply）
- ログはフィルタリング可能。表示間隔・最大行数はインターフェース情報の設定に従う。
- 「投入データ」はModule素材・Policy素材と`variables.json`（変数名/具体値/HCL設定/Sensitive設定。Sensitive設定ONの場合具体値はnull）をzip形式でダウンロード可能。
- 「結果データ」はplan.log/policyCheck.log/apply.log/error.logと暗号化された`sv-XXXXXX.tfstate`（ファイル名は実行毎に異なる）をzip形式でダウンロード可能。
- 「緊急停止」ボタンで停止、予約実行前なら「予約取消」ボタンで取消可能。

## 作業管理

作業実行履歴を一覧表示し、フィルタ検索できます。項目: 作業No.（36桁自動採番）、実行種別（通常/Plan確認/パラメータシート確認）、ステータス（未実行/未実行(予約)/準備中/実行中/実行中(遅延)/完了/完了(異常)/想定外エラー/緊急停止/予約取り消し）、実行ユーザ、登録日時、Movement（ID/名称/遅延タイマー/Terraform利用情報のWorkspace ID・Organization:Workspace名・RUN-ID）、オペレーション（No./名称）、投入データ・結果データ（zipダウンロード）、作業状況（予約日時/開始日時/終了日時）、備考。

## 代入値管理

オペレーションに紐付くMovementで利用されるModule素材の変数の具体値を閲覧します。項目: 作業No.、オペレーション、Movement名、Movement名:変数名、HCL設定（Trueの場合、連携先TerraformのVariablesのHCL設定が有効）、Movement名:変数名:メンバー変数、代入順序、具体値（Sensitive設定True/False、Trueの場合連携先TerraformのVariablesのSensitive設定が有効、値）、備考。

## 連携先Terraform管理

インターフェース情報の設定をもとにTerraformへ接続し、Terraformに登録されているOrganization/Workspace/Policy/Policy setの一覧を表示します。表示された一覧からITAに登録されている対象をTerraformから削除でき、Workspaceごとのリソース削除、Policy setに紐付いたWorkspace・Policyの紐付け解除も可能です。ここでの操作はITA側の登録対象に影響しません。

各一覧の「ITAの登録状態」列は、対応するITAメニュー（Organization管理／Workspace管理／Policy管理／Policy set管理・紐付メニュー）に登録済みかどうかを「登録済み」「未登録」で表示します。「削除」操作は元に戻せず、Workspaceの「リソース削除」も元に戻せません。
