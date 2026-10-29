# Menu Export/Import Feature

Menu Export/Import lets you select the ITA menus you want to migrate and overwrite-migrate data on a per-menu basis. When moving data to a different environment, you generally need to migrate all menus in order to preserve consistency.

## Modes

| Mode | Description |
|---|---|
| Environment migration | Exports all data of the specified menus; on import, all existing data is deleted and overwritten (replaced). |
| Time-specified | Exports only data from the specified time onward; if a unique item (ID, No., etc.) conflicts with data at the import destination, the exported data takes precedence on import. |

Discard scope: "Including discarded" (all records, including discarded data) / "Excluding discarded". History scope: "With history" / "Without history" (in both cases, the exported data takes precedence on conflict).

## Usage examples

**Pattern ① Duplicating an environment**: export all data from workspace A in Environment migration mode and import it into workspace B. Migrating data back to A afterward is not recommended, as it may cause inconsistency; bidirectional migration is likewise not recommended.

**Pattern ② Separating a data-entry workspace from an execution workspace**: after the initial migration in Environment migration mode, migrate the differences to workspace B using Time-specified mode each time workspace A is updated. If migrating data while work is being executed in workspace B, migrate only the differences using Time-specified mode to avoid affecting the data in use. Registering/updating data directly in workspace B (other than through work execution) is not recommended due to the risk of inconsistency, nor is bidirectional migration.

## About resource limits

Resources used during export/import processing are controlled by the resource plan. Backyard processing splits input/output for processing; raising the resource plan value `ita.organization.menu_export_import.buffer_size` shortens processing time but increases resource usage.

## Availability depending on environment differences (version/driver)

An exported KYM file is backward compatible only if all of the following are satisfied: ① it was exported from ITA version 2.5.0 or later, ② the import destination's ITA version is newer than the export source's, ③ every driver installed at the export source is also installed at the import destination.

| Case | Version difference | Driver difference | Import possible |
|---|---|---|---|
| A | None | None | Yes |
| B | None | Yes (destination has more drivers) | Yes |
| C | Yes (destination is newer) | None | Yes |
| D | Yes (destination is newer) | Yes (destination has more drivers) | Yes |
| E | None | Yes (destination has fewer drivers) | Conditional (possible if you use the driver install/uninstall feature to match the driver configuration, making it equivalent to case A/B) |
| F | Yes (destination is newer) | Yes (destination has fewer drivers) | Conditional (same as above, making it equivalent to case C/D) |
| G | Yes (source is newer) | None | No |
| H, I | Yes (source is newer) | Yes | No |

Import is not possible if the export source's version is newer than the import destination's (cases G/H/I).

## Menu structure

| Menu/Screen | Description |
|---|---|
| Menu Export | Exports menu data. |
| Menu Import | Imports menu data. |
| Menu Export/Import Management | Manages the status of executed exports/imports. |

## Menu Export

Menus excluded from export: export/import-related menus (Menu Export, Menu Import, Menu Export/Import Management, Excel Bulk Export, Excel Bulk Import, Excel Bulk Export/Import Management), Conductor-related work-execution/fulfillment-status menus (Conductor Edit/Work Execution, Conductor Work History, Conductor Work Status Check, Conductor Instance List, Conductor Node Instance List), parameter-sheet-creation-related menus (Parameter Sheet Definition/Creation, Parameter Sheet Creation History, Selection 1, Selection 2), Run Comparison, and each driver's (Ansible-Legacy/Pioneer/LegacyRole, Terraform-Cloud/EP, Terraform-CLI) target host, substitution value management, work execution, work status check, work management, work confirmation, and linked Terraform management menus.

Select the mode, discard scope, and history scope, select the menus, then run "Export"; pressing "Start Export" in the confirmation popup takes you to the Export/Import Management screen where you can check the status.

When menus were created via an initial environment migration or new parameter sheet creation, the following menus must be included in the export target (otherwise the import will finish as Completed (abnormal)): Menu Management, Menu-Table Link Management, Menu-Column Link Management, Role-Menu Link Management.

## Menu Import

Upload the exported file, check the menus to import, and run "Import"; pressing "Start Import" in the confirmation popup lets you check the status on the Export/Import Management screen. While the import status is "In progress", performing another operation right away (such as refreshing the screen or navigating to another menu) may cause a system error depending on the timing of the data swap, so wait a while before doing anything else.

## Menu Export/Import Management

Items: Execution No. (auto-numbered), Status (Not executed → In progress → Completed; Completed (abnormal) on error — if an import finishes as Completed (abnormal), it is automatically rolled back to the pre-import state), Process type (Export/Import), Mode (Environment migration/Time-specified), Discard scope (Including discarded/Excluding discarded), History scope (With history/Without history), Specified time (shown only when mode is Time-specified), File name (downloadable after completion), Executing user, Language (the logged-in user's language at import time; auto-registered and not editable), Execution log (shows a link to the log file when Completed (abnormal); e.g. `No matching file in the KYM file. (T_COMN_MENU_TABLE_LINK_DATA)`).
