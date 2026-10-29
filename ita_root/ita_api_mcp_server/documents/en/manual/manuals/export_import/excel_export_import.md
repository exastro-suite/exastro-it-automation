# Excel Bulk Export/Import Feature

Excel Bulk Export/Import bundles the downloadable Excel files from each menu into a zip file for bulk export/import. Menus eligible for export are those whose "Link" is "View only" or "Maintainable" in Role/Menu Link Management and that have an editable Excel file. Menus eligible for import are limited to those that are "Maintainable" and have an editable Excel file.

## Menu structure

| Menu/Screen | Description |
|---|---|
| Excel Bulk Export | Bundles the downloadable files of each menu into a zip and exports it. |
| Excel Bulk Import | Imports a zip bundling downloadable files. |
| Excel Bulk Export/Import Management | Manages the status of executed exports/imports. |

## Excel Bulk Export

Select the discard-status scope to export (all records / excluding discarded / discarded only) and the menus, then run "Export". An execution number is shown, and you check the status in the management menu.

Export file structure: inside `ITA_FILES_YYYYMMDDhhmmss.zip` there is a `MENU_LIST.txt` (a list of the exported menu REST names and file names) and a folder per menu group (folder name "menu group ID_menu group name"; if it exceeds 200 characters, only the first 200 are output), with the editable Excel files (xlsx) placed under each folder.

## Excel Bulk Import

You can adjust the list of files to import by editing `MENU_LIST.txt` inside the exported zip (lines starting with `#` are comments; the format is `menu REST name:file name`). Files required for import: `MENU_LIST.txt` and the full set of target files (placed under the menu group folders).

Uploading the zip displays the menu list; check the menus you want to import and run "Import" (unchecking excludes it from import). The target menu's checkbox becomes disabled and an error occurs in any of the following cases:

1. The same menu REST name is specified twice or more in `MENU_LIST.txt`.
2. The same file name is specified for different menus twice or more in `MENU_LIST.txt`.
3. `MENU_LIST.txt` contains a line that does not follow the required format.
4. `MENU_LIST.txt` lists a menu REST name that does not exist.
5. `MENU_LIST.txt` specifies a file that does not exist inside the zip.
6. Two or more files with the same name exist in different folders.
7. `MENU_LIST.txt` is not included.
8. A menu group folder name does not follow the "menu group ID_menu group name" format.
9. The logged-in user does not have "Maintainable" permission for the target menu.

## Excel Bulk Export/Import Management

Manages the execution status of exports/imports. Items: Execution No. (auto-numbered), Status (Not executed → In progress → Completed; Completed (abnormal) on error), Process type (Export/Import), Discard scope (all records / excluding discarded / discarded only), Executing user, File name (downloadable after completion), Language (exported in the logged-in user's language), Result (a text file describing the import result).

The result file reports, per imported file, the counts of "Registered/Updated/Discarded/Restored/Error" and the error details (e.g. `movement_name: ['This is a required item.:(line 12)']`). If the file is not a valid editable Excel file for that menu, it outputs "This is not the editable Excel file for this menu."
