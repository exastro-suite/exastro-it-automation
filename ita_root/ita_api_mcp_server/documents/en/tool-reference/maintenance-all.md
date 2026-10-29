# maintenance-all tool reference
Performs bulk registration, update, discard, restore, and physical deletion of records in a parameter sheet (menu).

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
- Use the `list-menu-info` tool in advance to retrieve the attributes of menu items, and specify item values according to those attributes.
- If the result of the `list-menu-info` tool includes a menu item with `column_type` of `IDColumn`, use the `list-menu-info-pulldown` tool to get the values that can be specified.
- Optimistic locking is used when performing update, discard, restore, or delete operations. Therefore, use the `menu-filter` tool to retrieve the record and pass it to `records[].parameter` (note: validation is performed using `last_update_date_time`).

- When writing to a `FileUploadColumn` field, use one of the following two methods:
    - Set a registered `file_id` in `.records[].fileid.column_name_rest`, and set the file name in `records[].parameter.column_name_rest`.
    - Set the BASE64-encoded value of the file in `.records[].file.column_name_rest`, and set the file name in `records[].parameter.column_name_rest`.
- If no changes have been made to a `FileUploadColumn` field, the `.records[].file.column_name_rest` and `.records[].fileid.column_name_rest` fields are not required.
- For items where `column_type` is `IDColumn`, set the value (the name value), not the key value (the ID value).
- When deleting a record, use `Discard` instead of `Delete`.
- `maintenance-all` batch operations are atomic. If one operation fails, the entire batch is rolled back.

## FileUploadColumn: Which method to use (fileid vs file)
There are two ways to write to a `FileUploadColumn` field (see above).
Always choose the appropriate method based on the input content.
Do not choose it carelessly.

### Rules for deciding
1. **If a file ID has already been specified** (e.g., when the attachment's ID looks like `file_xxxxxxxxxxxxxxxxxx`):
   - Use the **fileid method**.
   - Set the file ID to `records[].fileid.column_name_rest`.
   - Set the file name to `records[].parameter.column_name_rest`.
   - **Everything you need is available. Proceed with the registration process.**

2. **No file ID is available. Only raw file/text content is available.**:
   - Use the **file (BASE64) method**.
   - BASE64-encode the content and set it to `records[].file.column_name_rest`.
   - Set the file name to `records[].parameter.column_name_rest`.

### Prohibited actions (important)
- If a file ID has already been provided, do not ask the user for the file content, raw file, or its BASE64 value. The file ID alone is sufficient for the fileid method.
- An attachment does not always require BASE64 encoding. An attachment referenced by a file ID can be registered using the `fileid` method without any additional data.

### Quick reference
| What you have | Method | Where to put it |
|---------------|--------|-----------------|
| file ID (`file_...`) | fileid | `records[].fileid.column_name_rest` = ID, `parameter.column_name_rest` = name |
| raw file / text only | file | `records[].file.column_name_rest` = BASE64, `parameter.column_name_rest` = name |

## maintenance-all tool - IDColumn Value Format
### Important: IDColumn requires the exact display value
For columns where `column_type: "IDColumn"`, you must specify the exact display value, not just the name.
### How to get the correct value
1. Use the `list-menu-info-pulldown` tool with the menu name.
2. Find the column name in the result.
3. Use the value (not the key) from the returned mapping.
