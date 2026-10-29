# Parameter Collection Feature

Parameter Collection is a feature that lets you retrieve, or register data into, multiple parameter sheets created via the parameter sheet creation function, based on search conditions.

## Parameter modes

| Mode | Description |
|---|---|
| Host | Select one host linked to a parameter sheet, and retrieve data for multiple operations based on that host. |
| Operation | Select one operation linked to a parameter sheet, and retrieve data for multiple hosts based on that operation. |

- The selectable target parameters are limited to parameter sheets whose "Link" item is set to "Maintainable" or "View only" in Role/Menu Link Management. For parameter sheets that use a host group, select the parameter sheet for Auto-Registration of Substitution Values.
- The selectable target hosts are limited to hosts registered in the parameter sheet. When the parameter mode is Host, you can select only one target host (including "no host"); when it is Operation, you can select multiple hosts plus "no host" as retrieval targets.
- Parameter display runs automatically under the following conditions: ① a target host is selected while the parameter mode and target parameter are already selected; ② a target parameter is selected while the parameter mode and target host are already selected; ③ the operation is changed while the parameter mode is Operation and the target parameter/target host are already selected.
- The display order follows the selection order of the target parameters; when the parameter mode is Operation, the host display order follows the selection order of the target hosts (with "no host" last).

## Other features

- **Preset registration**: search conditions can be saved and recalled as a preset per workspace (can be updated, renamed, or deleted).
- **Parameter sheet maintenance**: you can edit after running a parameter display, but users whose "Link" is set to "View only" in Role/Menu Link Management cannot edit. For parameter sheets that use a host group, the Input parameter sheet is displayed.
- **Excel export**: each parameter sheet is exported as one sheet, and the sheet order follows the display order of the displayed results.
