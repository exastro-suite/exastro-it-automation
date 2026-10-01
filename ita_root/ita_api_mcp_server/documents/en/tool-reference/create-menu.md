# `create-menu` tool reference
Describes the basic parameters of the `create-menu` tool
If more detailed parameters are needed, refer to `tool-reference/create-menu-full-parameter.md`

## Important
- Some items are added automatically, so after running `create-menu`, use `list-menu-info` to retrieve the item list again
- Some of the automatically added items are `IDColumn` items, so retrieve the values that can be specified for `list-menu-info-pulldown`

## Workflow required before `create-menu`
1. Use search_docs to retrieve menu_definition_and_creation.md and refer to the section on bundles/unique constraints
2. Check the types of variables used in the playbook being used, and if there is a list type, consider setting vertical:1
3. Before calling create-menu, present the above judgment results to the user and obtain agreement

## Required workflow for `create-menu`
**Before registering data with `maintenance-all`, be sure to follow the steps below.**

1. Call `list-menu-info` to retrieve the menu structure and field definitions
    - Identify the value of `column_name_rest` (not `column_name`)
    - Check `required_item: "1"` for required fields
    - Identify fields of type IDColumn

2. Call `list-menu-info-pulldown` to obtain the exact format of the values that can be selected for IDColumn items
    - Do not use or guess based on the ID or display name alone
    - Specify the display value for IDColumn items

3. After steps 1-2 are complete, call `maintenance-all` to register the data

**Important reason:** Skipping steps 1 and 2 will cause a validation error and require a retry

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
        - Parameter sheet used with Ansible Legacy
- 2: Data Sheet
        - Sheet used for data accumulation and collection features
- 3: Parameter Sheet(Operation)

### menu_definition.menu.vertical
0: Do not use bundle format, 1: Use bundle format

### menu_definition.menu.hostgroup
0: Do not use host group, 1: Use host group

### menu_definition.column
Define using keys in the format `c` + sequential number

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

### Reserved words for item_name_rest
The following values cannot be used for `item_name_rest`; use a different name when creating an item
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
