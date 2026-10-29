# Admin Console Configuration and Custom Menu Development

In addition to the initial menus, the Admin Console lets you create custom menus so that individual departments can manage their own information in ITA's database (registering, changing, or deleting a custom menu requires contacting product support).

## Menu Structure

Admin Console: Main Menu, System Settings, Menu Group Management, Menu Management, Role-Menu Association Management, Operation Deletion Management, File Deletion Management.

## System Settings

Updates various information that should be configured when introducing and operating the ITA system. Items: Identification ID (used to identify the system setting, **must not be changed** — changing it invalidates ITA's guaranteed behavior), item name, setting value, remarks.

## Menu Group Management

Registers/updates/decommissions the parent menu group that a (child) menu belongs to.

| Item | Description |
|---|---|
| Menu Group ID | The menu group's ID |
| Parent Menu Group | The parent menu group |
| Menu Group Name (ja/en) | Display name. **Must be unique — duplicate registration is not allowed** |
| Panel Image | The menu group's panel image. Only **PNG files** can be used |
| Parameter Sheet Creation Usage Flag | Flag indicating whether this group can be used as a "target menu group" for the parameter sheet creation function |
| Display Order | Display order on the main menu (ascending; ties are broken by ascending menu group ID) |
| Remarks | Free text (optional) |

Since these are data-update operations, you must be logged in as a system administrator.

## Menu Management

Registers/updates/decommissions content functions (menus).

| Item | Description |
|---|---|
| Menu ID | The menu's ID |
| Menu Group | The parent menu group |
| Menu Name (ja/en/rest) | Display name and REST name. **The menu name must be unique** |
| Display Order Within Menu Group | Display order within the submenu |
| Auto Filter Check | Whether the auto filter checkbox is checked when the menu is displayed |
| Initial Filter | Whether the filter is shown already clicked when the menu is displayed |
| Custom Menu Material | A ZIP file for displaying a custom menu (described below) |
| Max Rows for Web Display | Maximum number of rows shown in the "list" |
| Rows Requiring Confirmation Before Web Display | Maximum number of rows before a confirmation dialog is shown prior to outputting the "list" |
| Max Rows for Excel Export | Maximum number of rows for Excel export (0 to 1048576) |
| Sort Key | Sort order of the list (JSON format, e.g. `{"ASC":"display_order"}`; the item name maps to ASC/DESC, the value is the key column name) |

If the number of records in a menu's item list (or the total history count) exceeds the max rows for Excel export, the Excel download in the "Download All / Bulk File Registration" tab is aborted (JSON format is still possible). The "Download All Change History" at the bottom of the screen is for confirmation purposes only and does not support upload.

### About Custom Menu Material

This material is only used when a menu is registered directly via "Menu Management" (it does not apply to existing menus or menus created via the parameter sheet creation function). Compress the HTML/JavaScript/CSS you want to display into a ZIP file and register it; the main display HTML file must be named `main.html` (file names used within `main.html` can be anything). All files inside the ZIP must be placed directly at the top level (no subfolders). If no material is registered for a new menu, nothing is displayed even if the menu is opened. To make it display, after registering the material you must grant "Maintainable" or "View only" permission for the target menu via "Role-Menu Association Management".

## Role-Menu Association Management

Registers/updates/decommissions the association between each menu and role. A menu screen not associated with any role is not shown in the menu group. Items: UUID, role, menu, association ("Maintainable" or "View only"), remarks (optional).

## Operation Deletion Management / File Deletion Management

For details, see "Automatic Operation Deletion" and "Automatic File Deletion" in Maintenance.

## Custom Menu Development (JavaScript Libraries / API)

Main JavaScript libraries used by ITA: jQuery 3.5.1 (MIT), select2 4.0.13 (MIT, requires jQuery), Ace v1.5.0 (BSD, editor supporting json/python/terraform/text/yaml), ExcelJS 4.3.0 (MIT), diff2html v2.11.3 (MIT). These can be loaded from paths provided by ITA (e.g. `/_/ita/lib/jquery/jquery.js`).

When reproducing ITA's standard screens in a custom menu, you can use the JS/CSS provided by ITA (jQuery and language files must be loaded separately).

- **common.js** (required foundation): `fn.fetch(URL, TOKEN, METHOD, BODY)` sends a request to the ITA API (URL omits the `/api/{organization_id}/workspaces/{workspace_id}/ita` prefix; TOKEN is normally null; METHOD defaults to GET). `fn.xhr(URL, FORMDATA)` is dedicated to data registration and shows a progress indicator (URL is in the form `/menu/{menu_name_rest}/maintenance/all/`; FORMDATA is a FormData object).
- **common.css**: ITA's basic screen style (required when using ITA's JS).
- **ui.js**: `new CommonUi()` generates basic UI such as tab screens (`ui.info.menu_info` holds the menu name/description, `ui.contentTab(tabs)` generates the tab HTML, use `type: 'blank'` for an empty tab, `ui.contentTabEvent('#tab1')` sets up tab events).
- **table.js**: `new DataTable(ID, MODE, INFO, PARAMS)` generates a table display/edit view for the specified parameter sheet (MODE is `view` for basic display or `history` for history display; INFO is the result retrieved from `/menu/{menuNameRest}/info/`; PARAMS is `fn.getCommonParams()` with `menuNameRest` added).
- **dialog.js**: `new Dialog(CONFIG, FUNCTIONS)` creates a dialog, shown via `dialog.open(CONTENTS)` (CONFIG configures position/header/width/footer buttons; FUNCTIONS defines the behavior on button click. A button's `action` only affects its display color: positive/restore/duplicate/warning/danger/history/normal/negative).
