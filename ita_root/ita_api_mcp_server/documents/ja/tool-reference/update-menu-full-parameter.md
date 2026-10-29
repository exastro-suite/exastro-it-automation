# update-menu tool referrence
このセクションでは、`update-menu`ツールのすべてのパラメータについて説明します。
これらのパラメータをすべて確認する前に、基本パラメータの一覧が記載されている`tool-reference/update-menu.md`を必ず参照してください。

## Sheet Types
### 1. Parameter Sheet(Host/Operation) [sheet_type_id: "1"]
- **自動生成列**: ホスト（device_listから）、オペレーション（operation_listから）
- **ユースケース**: 特定のホストで操作を実行する必要がある場合

### 2. Data Sheet [sheet_type_id: "2"]
- **自動生成列**: なし
- **ユースケース**: ホスト/オペレーションなしの参照用のデータ

## update-menu parameter
`update-menu`を呼び出す際、`menu_definition`パラメータは以下の構造でなければなりません:

```json
{
    "type": "object",
    "$defs": {
        "baseColumn": {
            "type": "object",
            "properties": {
                "item_name": { "type": "string" },
                "item_name_rest": { "type": "string" },
                "required": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
                "uniqued": { "type": "string", "enum": ["0", "1"], "description": "1: true" },
                "description": { "type": "string" },
                "remarks": { "type": "string" },
                "column_group": { "type": "null" },
                "display_order": { "type": "integer", "description": "Sequential numbers starting from 0" },
                "column_group_id": { "type": "null" },
                "create_column_id": { "type": "null" }
            },
            "required": [
                "item_name",
                "item_name_rest",
                "required",
                "uniqued",
                "description",
                "remarks",
                "column_group",
                "display_order",
                "column_group_id",
                "create_column_id"
            ]
        },

        "singleTextColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "SingleTextColumn" },
                        "column_class_id": { "type": "string", "const": "1" },
                        "single_string_maximum_bytes": { "type": "string" },
                        "single_string_regular_expression": { "type": "string" },
                        "single_string_default_value": { "type": "string" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "single_string_maximum_bytes",
                        "single_string_regular_expression",
                        "single_string_default_value"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "multiTextColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "MultiTextColumn" },
                        "column_class_id": { "type": "string", "const": "2" },
                        "multi_string_maximum_bytes": { "type": "string" },
                        "multi_string_regular_expression": { "type": "string" },
                        "multi_string_default_value": { "type": "string" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "multi_string_maximum_bytes",
                        "multi_string_regular_expression",
                        "multi_string_default_value"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "numColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "NumColumn" },
                        "column_class_id": { "type": "string", "const": "3" },
                        "integer_minimum_value": { "type": "string" },
                        "integer_maximum_value": { "type": "string" },
                        "integer_default_value": { "type": "string" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "integer_minimum_value",
                        "integer_maximum_value",
                        "integer_default_value"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "floatColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "FloatColumn" },
                        "column_class_id": { "type": "string", "const": "4" },
                        "decimal_minimum_value": { "type": "string" },
                        "decimal_maximum_value": { "type": "string" },
                        "decimal_digit": { "type": "string" },
                        "decimal_default_value": { "type": "string" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "decimal_minimum_value",
                        "decimal_maximum_value",
                        "decimal_digit",
                        "decimal_default_value"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "dateTimeColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "DateTimeColumn" },
                        "column_class_id": { "type": "string", "const": "5" },
                        "datetime_default_value": { "type": "string", "description": "ex: yyyy/mm/dd hh:mi:ss" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "datetime_default_value"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "dateColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "DateColumn" },
                        "column_class_id": { "type": "string", "const": "6" },
                        "date_default_value": { "type": "string", "description": "ex: yyyy/mm/dd" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "date_default_value"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "idColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "IDColumn" },
                        "column_class_id": { "type": "string", "const": "7" },
                        "pulldown_selection_id": { "type": "string", "enum": ["5011008", "5011009", "5011010"], "description": "Pulldown Selection ID: 5011008=`Parameter sheet create:Selection 1:*-(blank)` 5011009=`Parameter sheet create:Selection 2:Yes-No` 5011010=`Parameter sheet create:Selection 2:True-False`" },
                        "pulldown_selection": { "type": "string", "enum":["Parameter sheet create:Selection 1:*-(blank)", "Parameter sheet create:Selection 2:Yes-No", "Parameter sheet create:Selection 2:True-False"], "description": "Pulldown Selection Name (must match pulldown_selection_id)" },
                        "pulldown_selection_default_value": { "type": "string" },
                        "reference_item": { "type": "string" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "pulldown_selection_id",
                        "pulldown_selection",
                        "pulldown_selection_default_value",
                        "reference_item"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "passwordColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "PasswordColumn" },
                        "column_class_id": { "type": "string", "const": "8" },
                        "password_maximum_bytes": { "type": "string" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "password_maximum_bytes"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "fileUploadColumn": {
            "allOf": [
                { "$ref": "#/$defs/baseColumn" },
                {
                    "type": "object",
                    "properties": {
                        "column_class": { "type": "string", "const": "FileUploadColumn" },
                        "column_class_id": { "type": "string", "const": "9" },
                        "file_upload_maximum_bytes": { "type": "string" }
                    },
                    "required": [
                        "column_class",
                        "column_class_id",
                        "file_upload_maximum_bytes"
                    ],
                    "additionalProperties": false
                }
            ]
        },

        "menuCommonDefinition": {
            "type": "object",
            "properties": {
                "menu_create_id": { "type": "string", "description": "Specify the UUID of the menu to update." },
                "menu_name": { "type": "string" },
                "menu_name_rest": { "type": "string" },
                "display_order": { "type": "string", "description": "Specify a numerical value" },
                "description": { "type": "string" },
                "remarks": { "type": "string" },
                "unique_constraint": { "type": "null" },
                "columns": {
                    "type": "array",
                    "description": "column key list",
                    "items": {
                        "type": "string",
                        "pattern": "^c[0-9]+$"
                    }
                }
            },
            "required": [
                "menu_create_id",
                "menu_name",
                "menu_name_rest",
                "display_order",
                "description",
                "remarks",
                "unique_constraint",
                "columns"
            ],
            "additionalProperties": false
        },
        "menuHostOperationDefinition": {
            "allOf": [
                { "$ref": "#/$defs/menuCommonDefinition" },
                {
                    "sheet_type_id": { "type": "string", "const": "1" },
                    "sheet_type": { "type": "string", "const": "Parameter Sheet(Host/Operation)" },
                    "hostgroup": { "type": "string", "enum": ["0", "1"] },
                    "vertical": { "type": "string", "enum": ["0", "1"] },
                    "menu_group_for_input": { "type": "string", "const": "Input" },
                    "menu_group_for_input_id": { "type": "string", "const": "502" },
                    "menu_group_for_subst": { "type": "string",  "const": "Substitution value"},
                    "menu_group_for_subst_id": { "type": "string", "const": "503" },
                    "menu_group_for_ref": { "type": "string", "const": "Reference" },
                    "menu_group_for_ref_id": { "type": "string", "const": "504" }
                }
            ],
            "required": [
                "sheet_type_id",
                "sheet_type",
                "hostgroup",
                "vertical",
                "menu_group_for_input",
                "menu_group_for_input_id",
                "menu_group_for_subst",
                "menu_group_for_subst_id",
                "menu_group_for_ref",
                "menu_group_for_ref_id"
            ],
            "additionalProperties": false
        },
        "menuDateSheetDefinition": {
            "allOf": [
                { "$ref": "#/$defs/menuCommonDefinition" },
                {
                    "sheet_type_id": { "type": "string", "const": "2" },
                    "sheet_type": { "type": "string", "const": "Data Sheet" },
                    "menu_group_for_input": { "type": "string", "const": "Input" },
                    "menu_group_for_input_id": { "type": "string", "const": "502" }
                }
            ],
            "required": [
                "sheet_type_id",
                "sheet_type",
                "menu_group_for_input",
                "menu_group_for_input_id"
            ],
            "additionalProperties": false
        },
        "menuOperationDefinition": {
            "allOf": [
                { "$ref": "#/$defs/menuCommonDefinition" },
                {
                    "sheet_type_id": { "type": "string", "const": "3" },
                    "sheet_type": { "type": "string", "const": "Parameter Sheet(Operation)" },
                    "vertical": { "type": "string", "enum": ["0", "1"] },
                    "menu_group_for_input": { "type": "string", "const": "Input" },
                    "menu_group_for_input_id": { "type": "string", "const": "502" },
                    "menu_group_for_subst": { "type": "string",  "const": "Substitution value"},
                    "menu_group_for_subst_id": { "type": "string", "const": "503" },
                    "menu_group_for_ref": { "type": "string", "const": "Reference" },
                    "menu_group_for_ref_id": { "type": "string", "const": "504" },
                }
            ],
            "required": [
                "sheet_type_id",
                "sheet_type",
                "vertical",
                "menu_group_for_input",
                "menu_group_for_input_id",
                "menu_group_for_subst",
                "menu_group_for_subst_id",
                "menu_group_for_ref",
                "menu_group_for_ref_id"
            ],
            "additionalProperties": false
        },
    },

    "properties": {
        "column": {
            "type": "object",
            "description": "patternProperties is `c` followed by a sequential number starting from 1.",
            "patternProperties": {
                "^c[0-9]+$": {
                    "oneOf": [
                        { "$ref": "#/$defs/singleTextColumn" },
                        { "$ref": "#/$defs/multiTextColumn" },
                        { "$ref": "#/$defs/numColumn" },
                        { "$ref": "#/$defs/floatColumn" },
                        { "$ref": "#/$defs/dateTimeColumn" },
                        { "$ref": "#/$defs/dateColumn" },
                        { "$ref": "#/$defs/idColumn" },
                        { "$ref": "#/$defs/passwordColumn" },
                        { "$ref": "#/$defs/fileUploadColumn" },
                        { "$ref": "#/$defs/hostInsideLinkTextColumn" }
                    ]
                }
            },
            "additionalProperties": false
        },
        "menu": {
            "oneOf": [
                { "$ref": "#/$defs/menuHostOperationDefinition" },
                { "$ref": "#/$defs/menuDateSheetDefinition" },
                { "$ref": "#/$defs/menuOperationDefinition" }
            ]
        }
    },
    "required": ["column", "menu"],
    "additionalProperties": false
  }
}
```
