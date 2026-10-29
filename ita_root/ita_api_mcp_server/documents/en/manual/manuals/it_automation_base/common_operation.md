# Specification of Common ITA Menu Operations

Every menu screen provided by ITA is basically built from the same components (menu name, menu, submenu, workspace information, login information).

## Main Functions of the List Tab

### Register / Edit

The content of registration/editing differs per menu. Button behavior: "Add" = add a new registration record (for registering multiple records at once); "Duplicate" = duplicate the checked record(s) (**password fields are not duplicated**); "Delete" = delete the checked record(s); "Decommission" = set the decommission flag of the checked record(s) to True (takes effect once the edit is applied). Dropdown input can be narrowed down via partial-match search (case and full-width/half-width are normalized).

**File upload fields**: Use "+" to select and upload a file; text files can be created/edited/downloaded in the built-in editor (edits are only applied to the file once you click "Update", but are not yet saved to the record — they are finalized via edit confirmation → apply edits). Deletions are likewise not finalized until edits are applied. Forbidden upload extensions are configured in the Admin Console's system settings under the identification ID "FORBIDDEN_UPLOAD" (increasing the allowed extensions may introduce a security hole, so use caution). Extensions that support preview: images (gif, jpe, jpg, jpeg, png, svg, webp, bmp, ico, avif), text (txt, yaml, yml, json, hc, hcl, tf, sentinel, py, j2, css, html, htm, js), or files with no extension.

### Display Filter

- **Decommission column**: You must select one of "Excluding decommissioned" (default), "All records", or "Decommissioned only".
- **Search conditions**: Specifying multiple items applies an AND condition; combining "fuzzy search" and "dropdown search" on the same item applies an OR condition. For file upload fields, the search target is the file name. Integer, decimal, date, and date-time fields can be searched using "greater than or equal", "less than or equal", or "range".
- **Auto filter**: When checked, the list automatically refreshes each time a condition is selected. The default checked state is configured via "Auto Filter Check" in the Admin Console's "Menu Management".
- **Download**: You can choose Excel format, JSON format (file upload fields are downloaded as base64), or JSON format without files (file data excluded). Excel/JSON files downloaded from the display filter can also be used with the "download all" and "bulk file registration" functions.

### Table Settings

Table settings are stored server-side, so the same settings apply even when accessing from a different device or browser. "Common settings" apply to the shared parts of the submenu across all menus, while "individual settings" apply only to the menu on which they were configured (items in individual settings set to "use common setting" use the common setting's value). Configurable items: item display direction (vertical/horizontal), filter display position (inside/outside; fixed to outside when item display direction is horizontal), item menu display (hidden/shown; when hidden it can still be accessed from each record's operation menu icon), and item show/hide plus left/right pinning (individual settings only).

## Change History Tab

For each menu, you can view the change history keyed by primary key (newest change date/time first; the parts that changed from the previous entry are shown in bold orange).

**Note on dropdown selections (reference items)**: If you change the source of a dropdown selection (e.g., a value in a data sheet), the referencing side's displayed value (e.g., in a parameter sheet) also changes automatically. However, the "change history" records **the referenced value at the time the referencing record itself was edited** (registered/updated/decommissioned/restored); if the referenced value is changed afterward on its own, the referencing side's history entry is not updated. In other words, the value in the history is "a snapshot of the referenced value at the moment the edit was made" and may not match the current value of the reference source.

## Download All / Bulk File Registration

You can bulk-download and bulk-register the registered information of each menu in Excel or JSON format.

- **Excel**: Use "Download All (Excel)" for update/decommission/restore, and "Download for New Registration (Excel)" for new registrations. Files downloaded from "Download All Change History (Excel)" cannot be used for bulk registration. If "Execution Process Type" in the file is unselected or invalid, registration will not be executed.
- **JSON**: Use "Download All (JSON)" for update/decommission/restore as well as new registration.

Edit the downloaded file and upload it via the corresponding "Bulk File Registration" feature (follow each menu's manual for editing details).
