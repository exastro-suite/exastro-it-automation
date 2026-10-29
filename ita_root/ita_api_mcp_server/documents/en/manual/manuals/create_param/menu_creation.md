# Configuring and Using the Parameter Sheet Creation Function

The parameter sheet creation function creates menus that can be operated within ITA. There are two types of menu you can create: "Parameter Sheet" and "Data Sheet". Created menus can be operated via Web, Excel, and the REST API just like any other menu. The number, format, size, and input constraints of items can be freely designed, and created menus can also be used as a pulldown reference source for other menus.

## Parameter sheets and data sheets

- **Parameter sheet**: a menu that can be targeted from the "Auto-Registration of Substitution Values" menu of each driver. Create it as either "Parameter Sheet (with Host/Operation)" or "Parameter Sheet (with Operation)", then link it to IaC variables in the Auto-Registration of Substitution Values setting to automatically substitute the parameter sheet's "Parameter" item values into IaC variables. Selectable patterns: "with Host/Operation" (created per host and operation), "with Operation" (created per operation), "Uses Host Group" (integrates with the host group feature), "Uses Bundle" (manages repeated settings of the same item with better visibility).
- **Data sheet**: a menu where you can freely create items; it cannot be used with any driver's Auto-Registration of Substitution Values. Intended for managing information as a CMDB (Configuration Management Database), or for use as pulldown choices in other menus (to use as pulldown choices, the target item must have both "Required" and "Unique constraint" checked).

Availability of Auto-Registration of Substitution Values by creation target:

| Creation target | Ansible driver | Terraform driver |
|---|---|---|
| Parameter Sheet (with Host/Operation) | Yes — selectable | No — not selectable |
| Parameter Sheet (with Operation) | Partial — not selectable directly (but its values can be used via a Parameter Sheet Reference item) | Yes — selectable |
| Data Sheet | Partial — not selectable (values can be used via a pulldown reference item) | Partial — not selectable (same as above) |

## Creation patterns and menu group structure

When you select Parameter Sheet, menus are created in three menu groups: **A. Input** (maintainable), **B. Auto-Registration of Substitution Values** (view-only), and **C. Reference** (view-only). When you select Data Sheet, only **A. Input** (maintainable) is created. Maintenance (register/update/discard/restore) is only possible in the Input menu group.

There are five creation patterns in total: ① Parameter Sheet + Uses Host Group + Uses Bundle, ② Parameter Sheet + Uses Host Group, ③ Parameter Sheet + Uses Bundle, ④ Parameter Sheet, ⑤ Data Sheet.

## Menus in the "Parameter Sheet Creation" menu group

| Menu | Description |
|---|---|
| Parameter Sheet Definition/Creation | Create and update parameter sheets/data sheets and their items. |
| Parameter Sheet Definition List | Maintain (view/update/discard/restore) creation targets. |
| Parameter Sheet Creation History | Check the processing status of parameter sheet creation. |
| Column Group Creation Info *(hidden)* | Maintain column groups. |
| Parameter Sheet Item Creation Info *(hidden)* | Maintain managed items. |
| Parameter Sheet Role Creation Info *(hidden)* | Maintain access permission roles. |
| Unique Constraint (Multiple Items) Creation Info *(hidden)* | Maintain multi-item unique constraints. |
| Parameter Sheet Definition - Table Link Management *(hidden)* | Displays links between created parameter sheets and DB tables (Backyard only, not for user operation). |
| Other Menu Integration *(hidden)* | Displays links between menu groups, menus, items, and DB tables (Backyard only). |
| Selection 1 / Selection 2 *(hidden)* | Manage items used for pulldown selection (single-choice `*`, two-choice `Yes-No`/`True-False`) (not for user operation). |
| Reference Item Info *(hidden)* | Displays item information available for use as a reference item (Backyard only). |

Hidden menus require a restore operation via "Management Console → Role/Menu Link Management". The "Parameter Sheet Definition/Creation" menu allows maintaining one record at a time; use Excel if you need to maintain multiple records in bulk.

## Item and group settings (settings per input type)

The recommended number of items per parameter sheet is 100, with an upper limit of 1000 (a larger number may affect display and behavior). The characters "/" and "\" cannot be used in item names or column group names.

| Input type | Item created | Main settings |
|---|---|---|
| String (single-line) | Single-line text box | Max byte count (up to 65536; half-width = character count, full-width = character count × 3 + 2), regular expression (e.g. half-width digits `^[0-9]*$`), default value |
| String (multi-line) | Multi-line text box | Same as above |
| Integer | Text box with integer validation | Min/max value (-2147483648 to 2147483647; defaults to the lower/upper bound if left blank), default value |
| Decimal | Text box with decimal validation | Min/max value (-99999999999999 to 99999999999999, integer + decimal digits combined ≤ 14), number of digits (1–14, default 14), default value |
| Date-time | Calendar picker | Default value (`YYYY-MM-DD hh:mm:ss`) |
| Date | Calendar picker | Default value (`YYYY-MM-DD`) |
| Pulldown selection | Pulldown | Selectable items (in the form "menu group: menu: item", targets described below), reference item (displays other items side by side based on the selected value, described below), default value |
| Password | Masked text box (displayed as `*`) | Max byte count (up to 8192) |
| File upload | Item with a file-select/upload button | Max file byte count (upper limit is the plan's `ita.organization.common.upload_file_size_limit`) |
| Link | Item where the URL is displayed as a link | Max byte count (up to 8192), default value |
| Parameter sheet reference | References the value of an item in a "Parameter Sheet (with Operation)" menu when the operation matches | Selectable items (only items with input type string/integer/decimal/date-time/date/password/file upload/link) |

Settings common to all input types: Required (checkbox), Unique constraint item (checkbox), Description, Remarks.

**Items eligible for linking with Auto-Registration of Substitution Values**: for the Ansible driver, "String (single-line/multi-line)", "Integer", "Decimal", "Password", "Link", and "File upload" are eligible ("Date-time", "Date", and pulldown selections of date-time/date are not eligible). For the Terraform driver, "String (single-line/multi-line)", "Integer", "Decimal", "Password", and "Link" are eligible ("Date-time", "Date", "File upload", and pulldown selections of date-time/date are not eligible).

## Settings in the "Parameter Sheet Creation Info" tab

### Basic information section

| Setting item | Description |
|---|---|
| Parameter sheet name | The name to create ("Main Menu" cannot be used). |
| Creation target | Choose from "Parameter Sheet (with Host/Operation)", "Parameter Sheet (with Operation)", or "Data Sheet". When Data Sheet is selected, only "Input" is shown; when a Parameter Sheet is selected, the "Host Group" and "Bundle" checkboxes and the "Input"/"Auto-Registration of Substitution Values"/"Reference" fields are shown. |
| Display order | Display order within the menu group (ascending). |
| Host Group | Shown when the creation target is with Host/Operation. Check to support host groups; leave unchecked to create a per-host parameter sheet. |
| Bundle | Shown when the creation target is a parameter sheet. Check to create a bundle-enabled parameter sheet. |
| Last updated date/time / Last updated by | Auto-filled (shows the latest information, excluding update records made by Backyard). |

### Target menu group section

Select the menu groups to use for creation. The defaults are "Input", "Auto-Registration of Substitution Values" (hidden for Data Sheet), and "Reference" (same); confirming creates menus in those groups. To use groups other than the defaults, you must create the menu group in the Management Console beforehand. "Input" is required.

### Unique constraint (multiple items) section

Set a constraint that disallows duplicate records based on a combination of multiple items when data is registered. Use "Add pattern" to configure multiple combinations. A validation error occurs if a pattern contains only one item, or if the same combination pattern is duplicated.

### Access permission role section

If you select one or more roles, only the selected roles can access the Parameter Sheet Definition (each menu under the creation function) and the created menu (access to the menu side still follows the "Role/Menu Link Management" settings). If no role is selected, all roles can access the definition menu, while the created menu is only accessible to the System Manager role and roles the creating user belongs to.

### Preview and creation

The "Preview" tab lets you check the items you are entering in table form. Press the "Create" button to run creation, and check the result in the "Parameter Sheet Creation History" menu. On creation, data is automatically registered in the "Parameter Sheet Definition List", "Column Group Management", "Parameter Sheet Item Creation Info", "Unique Constraint (Multiple Items) Creation Info", and "Parameter Sheet Role Creation Info" menus.

## Operations after creation (edit, initialize, copy as new)

After creating a new parameter sheet, you are taken to a view screen where editing/creation is not possible. Before Backyard processing completes, a "Create (New)" button is shown; after it completes, a "Create (Edit)" button is shown instead (completion status can be checked in Parameter Sheet Creation History).

- **Edit**: you can add/remove items while keeping the Input menu group's data. For existing items you can freely change "Item name", "Regular expression", "Description", and "Remarks", but "Max byte count", "Min value", "Max value", "Number of digits", and "Max file byte count" can only be changed to a larger value than the original. If existing data becomes inconsistent after changing the regular expression, it is kept as-is. Deleting an existing item deletes its data; a newly added item is added with empty records (this may register empty values even under Required/Unique constraint checks, potentially causing inconsistency). Changing the target menu group discards the old menu and newly registers the new one (data is preserved). "Parameter sheet name", "Creation target", "Uses Host Group", and "Uses Bundle" cannot be changed. Existing item names cannot be swapped with each other, and renaming an item may cause an error.
- **Initialize**: recreates the currently displayed parameter sheet, but all data in the Input menu group is deleted. Other than "Parameter sheet name", there are no restrictions on what can be changed.
- **Copy as new**: takes you to a creation screen that uses the currently displayed parameter sheet as a template. The parameter sheet name must differ from the existing one.

## Parameter Sheet Definition List

Displays a list of created parameter sheets and lets you maintain them (view/update/discard/restore). Main items: Parameter sheet name (ja/en/rest) (cannot be changed once created), Sheet type (creation target, pulldown), Display order, Bundle/Host Group (can be set to True for an applicable creation target), Input/Auto-Registration of Substitution Values/Reference menu group (pulldown selection), Parameter sheet creation status (Created/Not created; the name cannot be changed once created), Description (ja/en), Remarks. **Discarding a record in the Parameter Sheet Definition List does not change the already-created menu itself** (the one shown in Management Console → Menu List); discarding an already-created parameter sheet requires a separate procedure (described below).

## Parameter Sheet Creation History

Backyard watches for data with the status "Not executed" and performs config file creation, table creation (SQL execution), and screen program deployment/registration. Once the status becomes "Completed", the menu is added to the menu group (takes roughly tens of seconds). Items: Parameter sheet name, Status (Not executed/In progress/Completed/Completed (abnormal)), Creation type (New/Initialize/Edit), Remarks.

## Structure of created parameter sheets

### Data Sheet (Input only)

Maintainable; since it is not tied to a host/operation, those items are not shown. Items: Parameter (the items you created), Remarks. "Auto-Registration of Substitution Values" and "Reference" are not created.

### Parameter Sheet (with Host/Operation)

- **Input**: Host name (selected from the device list), Operation (operation name selection; reference date/time, scheduled date, and last execution date/time are auto-filled), Parameter (created items), Remarks. Maintainable per host and operation.
- **Auto-Registration of Substitution Values**: view-only. Lists the registered content from Input.
- **Reference**: view-only. Lists the settings effective as of the point in time specified by the "Operation: reference date/time" display filter (if unspecified, shows only the most recent reference date/time per host name).

### Parameter Sheet (with Operation)

The host name item is removed from Input, and maintenance is done per operation (otherwise the same as with Host/Operation; the Reference menu, when unspecified, likewise shows only the most recent reference date/time data).

### Parameter Sheet (Uses Bundle)

In Input, you can set multiple parameter values for the same combination of a registered "Host name" and "Operation" (or just "Operation" when using with-Operation) by additionally entering a "Substitution order" field (allowing multiple values for the same combination; without a bundle, registering a duplicate for the same combination is an error, and adding more items has a fixed limit and worsens visibility — so using a bundle is recommended for repeated settings. Bundles cannot be used with Data Sheets). Items: Host name (hidden when with-Operation), Operation, Substitution order, Parameter, Remarks. Auto-Registration of Substitution Values and Reference behave the same as in other patterns.

### Parameter Sheet (Uses Host Group)

In Input, the host name item lets you select either a host name (prefixed `[H]`) or a host group name (prefixed `[HG]`) from a list. In Auto-Registration of Substitution Values, you can check the data split per host by the host group feature. Reference similarly shows the per-host data.

## Settings of the hidden menus

### Column Group Management

Manages column groups that group parameter sheet item headings. Items: Parent column group name (pulldown), Column group name (ja/en) ("/" and "\" prohibited), Full column group name (ja/en) (parent group name and group name joined with "/"), Remarks. Checks on update/discard: a group cannot be set as its own parent; a group set as another's parent cannot be discarded; circular parent-child relationships (e.g. A→B→C, then setting C as A's parent) cannot be configured.

### Parameter Sheet Item Creation Info

Manages each item of a parameter sheet/data sheet. Items: Parameter sheet name (pulldown), Item name (ja/en) ("/" and "\" prohibited), Item name (rest) (half-width alphanumeric and `_-` only), Description (ja/en), Column group, Column class (`SingleTextColumn` = single-line string, `MultiTextColumn` = multi-line, `NumColumn` = integer, `FloatColumn` = decimal, `DateTimeColumn`/`DateColumn` = calendar, `IDColumn` = pulldown (can display side-by-side via a reference item), `PasswordColumn` = masked, `FileUploadColumn` = file upload, `HostInsideLinkTextColumn` = link display, `ParameterSheetReference` = parameter sheet reference), Display order (ascending), Required (select True), Unique constraint (select True), Remarks.

### Unique Constraint (Multiple Items) Creation Info

Specify the parameter sheet name (pulldown) and the combinations of item names (rest) subject to the unique constraint, in list form (e.g. `[["item_1", "item_2"], ["item_3", "item_4"]]`).

### Parameter Sheet Role Creation Info

Set the parameter sheet name (pulldown) and the role (pulldown) to link it to.

## Appendix: Parameter Sheet Definition - Table Link Management / Other Menu Integration (Backyard only)

Internal menus that display link information between created parameter sheets and DB tables/other menus (not for user operation; if the link is changed directly after parameter sheet creation, these menus do not automatically follow the change). Items of "Parameter Sheet Definition - Table Link Management": Parameter sheet name (and rest), Table name, Primary key, Table name (history), Remarks. Items of "Other Menu Integration": Menu group name, Menu name (and rest), Item name (ja/en), Menu group name:Menu name:Item name (ja/en), ID-linked table/PK/item name (and REST)/sort condition/multilingual support flag, Column class, Parameter-sheet-creation-target flag, Remarks.

## Appendix: Selection 1 / Selection 2 / Reference Item Info (Backyard only)

"Selection 1" manages the single-choice pulldown item (`*`), and "Selection 2" manages the two-choice pulldown items (`Yes-No`, `True-False`). "Reference Item Info" displays reference item information used with "Pulldown Selection" (the Other Menu Integration ID, menu group name, menu name, display order, column class, item name (ja/en/rest), column group, ID-linked table/PK/item name (and REST)/sort condition/multilingual support flag, Sensitive setting, Parameter-sheet-creation-target flag, Description (ja/en), Remarks).

## Appendix: Targets available for "Selectable Items" in "Pulldown Selection"

| Menu group | Menu | Item |
|---|---|---|
| Management Console | Menu Management | Menu group name + Menu name |
| Basic Console | Operation List / Movement List | Operation name / Movement name |
| Ansible Common | Device List / File Management / Template Management | Host name / File-embedded variable name / Template-embedded variable name |
| Conductor | Conductor List | Conductor name |
| Parameter Sheet Creation | Selection 1 / Selection 2 | `*` / `True-False`, `Yes-No` |

In addition to the above, items in menus created by the parameter sheet creation function are also selectable, provided the column class is one of "String (single-line/multi-line)", "Integer", "Decimal", "Date-time", "Date", or "Link", and the item is both "Required" and "Unique constraint".

## Appendix: "Reference Item" of "Pulldown Selection"

A feature that displays other items within the same menu side by side, based on the value chosen in a pulldown selection. It is configured by checking the target items via the "Select reference items" button and confirming. Representative reference item targets: Management Console: Menu Management: Menu name → Menu name (rest); Ansible Common: Device List: Host name → DNS host name/IP address/user/password. In addition, if the selected item is a menu created by the parameter sheet creation function, other items in that parameter sheet with a column class of "String (single-line/multi-line)", "Integer", "Decimal", "Date-time", "Date", "Password", "File upload", or "Link" are also eligible. Once a reference item is configured, only the pulldown item is shown on the "Register" screen of the Input menu group, but the "List/Update", Auto-Registration of Substitution Values, and Reference lists display the values from the same row as the selected value, side by side. Reference items shown in Auto-Registration of Substitution Values can be used the same way as regular values in the Auto-Registration of Substitution Values setting.

## Appendix: Discarding (logical deletion) / restoring a created parameter sheet

To discard a parameter sheet, search for it by menu name (ja/en/rest) in Menu Management in the Management Console to identify the target (the target is a menu belonging to the target menu group specified at parameter sheet creation time), then discard or restore it. Discarded parameter sheets can no longer be used, so care is needed. If a discarded parameter sheet is used in a pulldown item, a reference item, or a driver's Auto-Registration of Substitution Values, it results in "ID conversion failed (X)". Likewise, items in other menus that reference the discarded parameter sheet's menu name/item name show the same behavior.
