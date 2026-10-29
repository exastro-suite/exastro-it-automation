# ITA REST APIによるレコード操作とパラメータ適用

## APIのアクセス（認証）について

各APIのエンドポイント・パラメータの詳細は利用者向けマニュアル（オペレータ向け／システム管理者向け）を参照してください。Bearer認証を使う場合は認証方式の変更が必要です。API実行時の言語は最終ログイン時の言語情報が参照されます。作成直後のユーザーでBasic認証を使う場合、初回ログイン後の設定が未完了だと認証エラー（`401-00002`）になります。

## 一覧取得（Menu Filter：レコードの取得）

`POST /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/filter/` にBasic/Bearer認証で条件を指定してレコードを取得します（GETでも全件取得可）。

条件指定の検索オプション:

| オプション | 説明 | 設定例 |
|---|---|---|
| NORMAL | あいまい検索（指定語句を含むレコード） | `{"キー":{"NORMAL":"条件"}}` |
| LIST | 完全一致検索 | `{"キー":{"LIST":["条件"]}}` |
| RANGE | 範囲検索（STARTのみ=以上、ENDのみ=以下） | `{"キー":{"RANGE":{"START":"..","END":".."}}}` |

レコードの`discard`値は論理削除状態を示します（`"0"`＝有効、`"1"`＝廃止。廃止レコードはバリデーション対象外）。ファイルデータはbase64エンコードされた文字列で出力されます。パスワード等の暗号化項目は、一覧取得APIの出力では常に`null`になります（登録値は出力されない）。

## 登録、編集（Menu MaintenanceAll レコードの一括操作）

`POST /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/maintenance/all/` で登録・編集を行います。Content-Typeにより指定方式が異なります。

- **application/json形式**: パラメータをJSONで送信し、ファイルデータはbase64文字列として`file`配下に指定します。
- **multipart/form-data形式**: パラメータをformデータとして送信し、ファイルのformデータキーは「JSONデータのインデックス + `.` + 対象キー」（例: `0.playbook_file=@echo.yml`）で指定します。

パラメータ構造（共通）: 配列内の各要素は`file`（アップロードファイルのbase64エンコード文字列、キー単位）、`parameter`（対象メニューのカラムキーと値）、`type`（`Register`/`Update`/`Discard`/`Restore`）で構成されます。API実行時も画面操作時と同じバリデーションが適用されます。

**レコード更新時の注意**: `last_update_date_time`にはFILTER取得時の最新値を指定する必要があり、一致しない場合は更新されません。

**ファイル操作（application/json）**: 登録・更新はparameter/file配下の対象キーに値を指定。ファイル名のみ変更する場合もfile配下への指定が必要（省略すると更新対象から除外）。削除はparameter配下の対象キーを`""`または`null`に設定（`"null"`は文字列としてファイル名扱いになるため注意）。

**ファイル操作（multipart/form-data）**: ファイル名はparameter配下に指定し、ファイル本体は「インデックス.キー」を`-F`で指定。ファイル名のみ変更する場合もファイルパス指定が必要。削除はparameter配下を`""`または`null`に設定。

ファイル・他項目を変更せず一部項目のみ更新する場合は、対象項目のキーのみをparameterに含め、file指定は行いません。プルダウン項目の選択可能値は「プルダウン項目情報取得API」で確認します。

## APIのパラメータ関連情報（Menu Info）

- `GET /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/`: メニューの構成情報（column_group_info、column_info、custom_menu、menu_info）を取得。column_infoの主なキー: `column_name`（画面表示名）、`column_name_rest`（APIパラメータ名）、`auto_input`（自動入力フラグ、0/1）、`input_item`（入力対象フラグ、0=非対象/1=対象/2=非表示）、`view_item`（出力対象フラグ、0/1）、`required_item`（必須フラグ、0/1）、`unique_item`（一意制約フラグ、0/1）。
- `GET /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/column/`: パラメータの項目情報（項目名(rest)と画面表示名の対応）を取得。
- `GET /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/pulldown/`: プルダウン項目で選択可能な値の一覧を取得（例: 機器一覧の`authentication_method`, `connection_type`, `hw_device_type`, `lang`, `protocol`等）。

## パラメータ適用API（Apply）

オペレーションの生成からパラメータ適用までを行い、Conductor作業実行を行うAPIです（完了確認はConductor作業履歴から行う必要があります。本APIは完了確認を行いません）。

- URL: `POST /api/{organization_id}/workspaces/{workspace_id}/ita/apply/`
- headers: `content-type: application/json`、`Authorization: Basic認証またはBearer認証`

### Request body

| キー | 項目 | 必須 | 型 | 説明 |
|---|---|---|---|---|
| conductor_class_name | Conductor名 | 〇 | 文字列 | Conductor一覧に登録済みのConductor名称。未登録の場合エラー。 |
| operation_name | オペレーション名 | - | 文字列 | 既存オペレーション名を指定するか、未登録の名前を指定すると新規オペレーションとして登録される。省略時は`yyyymmddhhmissffffffN`形式で自動採番される。 |
| schedule_date | 予約日時 | - | 文字列 | `yyyy/mm/dd hh:mi:ss`形式。省略時は即時実行。 |
| parameter_info | パラメータ情報 | - | 配列 | 登録/更新/廃止/復活を行うパラメータ情報。複数メニューがあり順序が重要な場合は配列順で調整。Conductor実行のみなら省略可。 |
| parameter_info[].(menu_name_rest) | メニュー名(REST) | - | 配列 | 管理コンソールのメニュー管理で確認できる「メニュー名(Rest)」を指定。 |
| ...[].type | レコード操作種別 | - | 文字列 | `Register`/`Update`/`Discard`/`Restore` |
| ...[].file | アップロードファイル | - | 辞書 | カラムキーとbase64エンコード文字列の組み合わせ |
| ...[].parameter | パラメータ | - | 辞書 | 対象メニューのカラムキーと値の組み合わせ。新規/自動採番オペレーションの場合オペレーション名相当のキーは不要。サブConductorの個別オペレーションを明示する場合は該当オペレーション名を指定。 |

`(menu_name_rest)`からparameterまでの構造は「Menu MaintenanceAll」APIと同一仕様です。

### Request bodyの具体例

既存オペレーションで登録済みパラメータのみで実行:
```json
{"conductor_class_name": "sample_conductor", "operation_name": "sample_operation"}
```

予約実行の場合は`schedule_date`を追加。既存オペレーションでパラメータ適用する場合は`operation_name_select`（既存オペレーションの「実施予定日(YYYY/MM/DD hh:mm)」_「オペレーション名」）をparameter内に指定。新規オペレーション・自動採番の場合は`operation_name_select`の指定は不要です。

複数メニュー・複数レコードへのパラメータ適用や、サブConductor（Conductor call function）の個別オペレーションを明示指定する場合は、`parameter_info`配列内に複数のメニュー・レコードを列挙します（各レコードに`operation_name_select`を指定してサブConductor個別のオペレーションを明示できる）。

### Response body

正常時: `{"data": {"conductor_instance_id": "採番されたID"}, "message": "SUCCESS", "result": "000-00000", "ts": "処理日時"}`

異常時: `{"message": "エラーメッセージ", "result": "エラーコード", "ts": "処理日時"}`（バリデーションエラーの例: `{"message": {"1": {"column_1": ["文字長エラー (閾値 : 値<=8byte, 値 : 30byte), menu : sample_menu_001"]}}, "result": "499-00201", "ts": "実施日時"}`。メッセージのキーはメニュー内のレコード番号（0オリジン）。

### 留意事項

- **ホストグループへのパラメータ適用**: ホストグループ管理へのパラメータ適用はホスト解析が未処理の状態でConductorが実行されるため、事前に「Menu MaintenanceAll」または「Menu Maintenance」で登録しておく必要があります。
- **変数抜出対象メニューへのパラメータ適用**: 変数の刈取りが未処理の状態でConductorが実行されるため、同様に事前登録が必要です（変数抜出対象メニューはTerraform driver共通・Ansible driver共通のドキュメントを参照）。
- **エラー時のロールバック**: 本APIはトランザクション処理でDB更新を行うため、Request body不備等で更新に失敗した場合、トランザクション内の更新はロールバックされます。
