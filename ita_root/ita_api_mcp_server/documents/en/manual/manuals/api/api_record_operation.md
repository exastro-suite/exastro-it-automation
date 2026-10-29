# Record Operations and Parameter Application via the ITA REST API

## About API access (authentication)

For endpoint and parameter details of each API, refer to the user manuals (for operators / for system managers). To use Bearer authentication, the authentication method must be changed first. The language used when executing an API is taken from the language setting at the last login. If a newly created user uses Basic authentication before completing the initial post-login setup, an authentication error (`401-00002`) occurs.

## Listing records (Menu Filter: retrieving records)

Send `POST /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/filter/` with Basic/Bearer authentication and search conditions to retrieve records (GET can also be used to retrieve all records).

Search options for specifying conditions:

| Option | Description | Example |
|---|---|---|
| NORMAL | Fuzzy match (records containing the specified term) | `{"key":{"NORMAL":"condition"}}` |
| LIST | Exact match | `{"key":{"LIST":["condition"]}}` |
| RANGE | Range search (START only = greater than or equal, END only = less than or equal) | `{"key":{"RANGE":{"START":"..","END":".."}}}` |

The `discard` value on a record indicates its logical-deletion state (`"0"` = active, `"1"` = discarded; discarded records are excluded from validation). File data is output as a base64-encoded string. Encrypted items such as passwords are always output as `null` from the listing API (the stored value is never returned).

## Registering and editing (Menu MaintenanceAll: batch record operations)

Use `POST /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/maintenance/all/` to register or edit records. The way parameters are specified depends on the Content-Type.

- **application/json format**: Send parameters as JSON; file data is specified as a base64 string under `file`.
- **multipart/form-data format**: Send parameters as form data; the form-data key for a file is "JSON array index + `.` + target key" (e.g. `0.playbook_file=@echo.yml`).

Common parameter structure: each element of the array consists of `file` (base64-encoded string of the uploaded file, keyed by column), `parameter` (column keys and values of the target menu), and `type` (`Register`/`Update`/`Discard`/`Restore`). The same validation rules that apply to screen operations also apply when using the API.

**Note when updating a record**: `last_update_date_time` must be set to the latest value obtained from a FILTER retrieval; if it does not match, the update is not applied.

**File operations (application/json)**: for register/update, specify the value under the target key in parameter/file. Even when only renaming a file, the file must still be specified under `file` (omitting it excludes that file from the update). To delete a file, set the target key under `parameter` to `""` or `null` (note that `"null"` as a string is treated as a literal file name, not a deletion).

**File operations (multipart/form-data)**: specify the file name under `parameter`, and pass the file body with `-F` using "index.key". Even when only renaming a file, the file path must still be specified. To delete, set the key under `parameter` to `""` or `null`.

To update only some items without changing files or other items, include only the target item's key in `parameter` and omit `file` entirely. Selectable values for pulldown items can be checked via the "Pulldown Item Information" API.

## API parameter reference information (Menu Info)

- `GET /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/`: retrieves menu configuration information (column_group_info, column_info, custom_menu, menu_info). Main keys under column_info: `column_name` (display name), `column_name_rest` (API parameter name), `auto_input` (auto-input flag, 0/1), `input_item` (input-target flag, 0 = not applicable/1 = applicable/2 = hidden), `view_item` (output-target flag, 0/1), `required_item` (required flag, 0/1), `unique_item` (unique-constraint flag, 0/1).
- `GET /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/column/`: retrieves parameter item information (mapping between the item name (rest) and the display name).
- `GET /api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/pulldown/`: retrieves the list of selectable values for pulldown items (e.g. `authentication_method`, `connection_type`, `hw_device_type`, `lang`, `protocol`, etc. in the device list).

## Parameter Application API (Apply)

An API that generates an operation, applies parameters, and executes the Conductor work (completion must be checked via the Conductor work history — this API does not check for completion).

- URL: `POST /api/{organization_id}/workspaces/{workspace_id}/ita/apply/`
- headers: `content-type: application/json`, `Authorization: Basic or Bearer authentication`

### Request body

| Key | Item | Required | Type | Description |
|---|---|---|---|---|
| conductor_class_name | Conductor name | Yes | String | Name of a Conductor already registered in the Conductor list. An error occurs if it is not registered. |
| operation_name | Operation name | - | String | Specify an existing operation name, or a new operation is registered under this name if it does not exist. If omitted, a name is auto-generated in the form `yyyymmddhhmissffffffN`. |
| schedule_date | Scheduled date/time | - | String | Format `yyyy/mm/dd hh:mi:ss`. If omitted, executed immediately. |
| parameter_info | Parameter information | - | Array | Parameter information for register/update/discard/restore. If there are multiple menus and order matters, adjust via the array order. Can be omitted if only Conductor execution is needed. |
| parameter_info[].(menu_name_rest) | Menu name (REST) | - | Array | Specify the "Menu Name (Rest)" shown in Menu Management in the Management Console. |
| ...[].type | Record operation type | - | String | `Register`/`Update`/`Discard`/`Restore` |
| ...[].file | Uploaded file | - | Dict | Combination of column key and base64-encoded string |
| ...[].parameter | Parameter | - | Dict | Combination of the target menu's column keys and values. For a new or auto-numbered operation, the key corresponding to the operation name is not needed. To explicitly target an individual operation of a sub-Conductor, specify that operation's name. |

The structure from `(menu_name_rest)` down to `parameter` is identical to the "Menu MaintenanceAll" API.

### Request body examples

Execute using only parameters already registered on an existing operation:
```json
{"conductor_class_name": "sample_conductor", "operation_name": "sample_operation"}
```

For a scheduled execution, add `schedule_date`. When applying parameters to an existing operation, specify `operation_name_select` (the existing operation's "Scheduled Date (YYYY/MM/DD hh:mm)" + "Operation Name") inside `parameter`. For a new or auto-numbered operation, `operation_name_select` is not needed.

When applying parameters across multiple menus/records, or when explicitly targeting individual operations of a sub-Conductor (Conductor call function), list multiple menus/records inside the `parameter_info` array (each record can specify `operation_name_select` to target an individual sub-Conductor operation).

### Response body

On success: `{"data": {"conductor_instance_id": "assigned ID"}, "message": "SUCCESS", "result": "000-00000", "ts": "processing timestamp"}`

On failure: `{"message": "error message", "result": "error code", "ts": "processing timestamp"}` (example validation error: `{"message": {"1": {"column_1": ["Character length error (threshold: value<=8byte, value: 30byte), menu: sample_menu_001"]}}, "result": "499-00201", "ts": "timestamp"}`. The key in the message is the record number within the menu (0-origin).

### Notes

- **Applying parameters to Host Group Management**: because Conductor executes before host resolution completes, records must first be registered via "Menu MaintenanceAll" or "Menu Maintenance".
- **Applying parameters to variable-extraction target menus**: because Conductor executes before variable extraction completes, records must similarly be pre-registered (see the Terraform driver common / Ansible driver common documentation for variable-extraction target menus).
- **Rollback on error**: since this API performs DB updates within a transaction, if the update fails due to an incomplete request body or other issue, all updates within the transaction are rolled back.
