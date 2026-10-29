# maintenance-all tool reference
パラメータシート（メニュー）のレコードの一括登録、更新、破棄、復元、および物理的削除を実行します。

## Minimal Working Example
```json
{
    "menu": "menu_name_rest",
    "records": [
        {
            "fileid": {
                "column_name_rest_file": "file_0123456789abcdef0123456789abcdef"
            },
            "parameter": {
                "discard": "0",
                "column_name_rest_a": "value-a",
                "column_name_rest_b": "value-b",
                "column_name_rest_c": "value-c",
                "column_name_rest_file": "filename"
            },
            "type": "Register"
        },
        {
            "parameter": {
                "discard": "0",
                "column_name_rest_a": "value-a",
                "column_name_rest_b": "value-b",
                "column_name_rest_c": "value-c",
                "last_update_date_time": "2026/12/31 23:59:59.000000"
            },
            "type": "Update"
        }
    ]
}
```

## How to use
- `list-menu-info`ツールを使用してメニュー項目の属性を事前に取得し、それらの属性に従って項目の値を指定します
- `list-menu-info` ツールの結果に `column_type` が `IDColumn` のメニュー項目が含まれている場合、`list-menu-info-pulldown` ツールで指定できる値を取得します
- 更新、破棄、復元、削除操作を実行する際には、楽観的ロックが使用されます。そのため、`menu-filter`ツールを使用してレコードを取得し、`records[].parameter`に渡してください（注：検証は`last_update_date_time`を使用して行われます）

- `FileUploadColumn`フィールドに書き込む場合は、以下の2つの方法のいずれかを使用してください:
    - 登録済み`file_id` を `.records[].fileid.column_name_rest` に、ファイル名を `records[].parameter.column_name_rest` に設定します
    - ファイルのBASE64エンコード値を`.records[].file.column_name_rest`に設定し、ファイル名を`records[].parameter.column_name_rest`に設定します
- `FileUploadColumn` フィールドに変更が加えられていない場合、`.records[].file.column_name_rest` および `.records[].fileid.column_name_rest` フィールドは不要です
- `column_type`が`IDColumn`である項目については、キー値（ID値）ではなく値（名前値）を設定します
- レコードを削除する際は、`Delete` ではなく`Discard`を使用してください
- `maintenance-all` バッチ操作はアトミックです。1 つの操作が失敗した場合、バッチ全体がロールバックされます

## FileUploadColumn: Which method to use (fileid vs file)
`FileUploadColumn`フィールドに書き込む方法は2つあります（上記参照）。
入力内容に基づいて、必ず適切な方法を選択してください。
安易に選択しないでください。

### 決定するルール
1. **ファイルIDが既に指定されている場合**（例：添付ファイルのIDが`file_xxxxxxxxxxxxxxxxxx`のような場合）：
   - **fileid メソッド** を使用してください。
   - Set the file ID to `records[].fileid.column_name_rest`.
   - Set the file name to `records[].parameter.column_name_rest`.
   - **必要なものはすべて揃っています。登録手続きにお進みください。**

2. **ファイルIDは利用できません。生のファイル/テキストコンテンツのみ利用可能です。**:
   - Use the **file (BASE64) method**.
   - BASE64-encode the content and set it to `records[].file.column_name_rest`.
   - Set the file name to `records[].parameter.column_name_rest`.

### 禁止事項（重要）
- ファイルIDが既に提供されている場合は、ユーザーにファイルのコンテンツ、生ファイル、またはそのBASE64値を尋ねないでください。ファイルIDのみで、fileidメソッドには十分です。
- 添付ファイルは必ずしもBASE64エンコードを必要としません。ファイルIDで参照される添付ファイルは、追加データなしで`fileid`メソッドを使用して登録できます。

### Quick reference
| What you have | Method | Where to put it |
|---------------|--------|-----------------|
| file ID (`file_...`) | fileid | `records[].fileid.column_name_rest` = ID, `parameter.column_name_rest` = name |
| raw file / text only | file | `records[].file.column_name_rest` = BASE64, `parameter.column_name_rest` = name |

## maintenance-all tool - IDColumn Value Format
### 重要: IDColumn には正確な表示値が必要です
`column_type: "IDColumn"` の列については、名前だけでなく、正確な表示値を指定する必要があります。
### 正しい値を取得する方法
1. メニュー名とともに`list-menu-info-pulldown`ツールを使用してください
2. 結果から列名を見つける
3. 返されたマッピングから値（キーではない）を使用してください
