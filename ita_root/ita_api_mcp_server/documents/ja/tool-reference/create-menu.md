# `create-menu` tool reference
`create-menu`ツールの基本的なパラメータについて説明します
より詳細なパラメータが必要な場合は、`tool-reference/create-menu-full-parameter.md`を参照すること

## Important
- 一部の項目は自動的に追加されるため、`create-menu` を実行した後は、`list-menu-info` を使用して項目のリストを再取得すること
- 自動的に追加される項目の中には`IDColumn`の項目もあるため、`list-menu-info-pulldown` に指定できる値を取得すること

## `create-menu`の前に必要なワークフロー
1. search_docs を使用して menu_definition_and_creation.md を取得し、バンドル/一意制約に関するセクションを参照すること
2. 使用されているプレイブック内の変数の型を確認し、リスト型がある場合は vertical:1 を設定することを検討すること
3. create-menu を呼び出す前に、上記の判断結果をユーザーに提示し、同意を得ること

## `create-menu`の必須ワークフロー
**`maintenance-all`でデータを登録する前に、必ず以下の手順に従ってください。**

1. `list-menu-info` を呼び出して、メニュー構造とフィールド定義を取得します
    - `column_name_rest` の値（`column_name` ではない）を特定します
    - 必須フィールドについては `required_item: "1"` を確認します
    - IDColumn 型のフィールドを特定します

2. IDColumn項目に選択可能な値の正確な形式を取得するには、`list-menu-info-pulldown` を呼び出してください
    - ID や表示名のみを使用したり、推測したりしないでください
    - IDColumn項目には表示値を指定します

3. ステップ1～2が完了した後、データ登録のために「maintenance-all」を呼び出します

**重要な理由:** ステップ 1,2 をスキップすると検証エラーが発生し、再試行が必要になります

## Minimal Working Example
```json
{
    "menu_definition": {
        "menu": {
            "menu_name": "Simple Parameter Sheet",
            "menu_name_rest": "simple_param_sheet",
            "description": "A simple parameter sheet",
            "sheet_type_id": "1",
            "hostgroup": "0",
            "vertical": "0",
        },
        "column": {
            "c1": {
                "item_name": "A text field",
                "item_name_rest": "a_text_field",
                "required": "1",
                "column_class": "SingleTextColumn",
                "single_string_maximum_bytes": "256",
            },
            "c2": {
                "item_name": "B file field",
                "item_name_rest": "b_file_field",
                "required": "1",
                "column_class": "FileUploadColumn",
                "file_upload_maximum_bytes": "1024000"
            }
        }
    }
}
```

## Explanation of parameters
### menu_definition.menu.sheet_type_id
- 1: Parameter Sheet(Host/Operation)
        - Ansible Lagacyで使用するパラメータシート
- 2: Data Sheet
        - データの蓄積や収集機能で使用するシート
- 3: Parameter Sheet(Operation)

### menu_definition.menu.vertical
0: バンドル形式を使用しない、1: バンドル形式を使用する

### menu_definition.menu.hostgroup
0: ホストグループを使用しない、1: ホストグループを使用する

### menu_definition.column
`c` ＋連番の形式のキーを使用して定義します

### column_class
- `SingleTextColumn`: String field
- `MultiTextColumn`: Multi-line string field
- `NumColumn`: Integer field
- `FloatColumn`: Floating-point number field
- `DateTimeColumn`: Date and time field
- `DateColumn`: Date field
- `IDColumn`: field such as Check ON/OFF, Yes/No, True/False, etc.
- `PasswordColumn`: Sensitive field such as passwords
- `FileUploadColumn`: Field for storing file

### item_name_rest の予約語
次の値はitem_name_restに使用できません、項目作成時は別の名前を使用すること
- uuid
- host_name
- operation_name_select
- operation_name_disp
- base_datetime
- operation_date
- last_execute_timestamp
- input_order
- no_item
- remarks
- discard
- last_update_date_time
- last_updated_user

### column_class=SingleTextColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "SingleTextColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
        "single_string_maximum_bytes": { "type": "string" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```

### column_class=MultiTextColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "MultiTextColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
        "multi_string_maximum_bytes": { "type": "string" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```

### column_class=NumColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "NumColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
        "integer_minimum_value": { "type": "string" },
        "integer_maximum_value": { "type": "string" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```

### column_class=FloatColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "FloatColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
        "decimal_minimum_value": { "type": "string" },
        "decimal_maximum_value": { "type": "string" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```

### column_class=DateTimeColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "DateTimeColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```

### column_class=DateColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "DateColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```

### column_class=IDColumn definition
```json
{
    "type": "object",
    "properties": {
        "column_class": { "type": "string", "const": "IDColumn" },
        "column_class_id": { "type": "string", "const": "7" },
        "pulldown_selection": { "type": "string", "enum":["Parameter sheet create:Selection 1:*-(blank)", "Parameter sheet create:Selection 2:Yes-No", "Parameter sheet create:Selection 2:True-False"] },
    },
    "required": ["item_name", "item_name_rest", "column_class", "pulldown_selection"]
```

### column_class=PasswordColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "PasswordColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
        "password_maximum_bytes": { "type": "string" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```

### column_class=FileUploadColumn definition
```json
{
    "type": "object",
    "properties": {
        "item_name": { "type": "string" },
        "item_name_rest": { "type": "string" },
        "column_class": { "type": "string", "const": "FileUploadColumn" },
        "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
        "file_upload_maximum_bytes": { "type": "string" }
    },
    "required": ["item_name", "item_name_rest", "column_class"]
}
```
