# Configuring and Using the Host Group Feature

A host group is a group that logically bundles target hosts by function/role. The upper level is called the parent host group and the lower level the child host group; the lowest-level host group is linked to the target hosts. Each host group counts as one level of hierarchy, and up to 15 levels can be defined from the top to the bottom.

## Benefit of host groups: parameter inheritance

Parameters set on a parent host group (only when a concrete value is set) are inherited by child host groups. Localizing where settings are made simplifies adding and changing values. When a new child host group is added, it automatically inherits the parent's settings just like existing children.

A child host group can be linked to multiple parent host groups. Rules when parameters conflict:

- **Conflict across different levels**: the value of the lowest-level host group takes precedence (e.g. if the same parameter exists on both a higher-level `dcx` and a lower-level `zabbix1`, the value from `zabbix1` is inherited).
- **Conflict at the same level**: the value of the parent host group with the higher priority (larger number) takes precedence.

## Main function

Manages host group settings and splits host-group-level records of a parameter sheet into per-host records. The following operations trigger a split process across **all parameter sheets**: register/update/discard/restore in Host Group List, Host Group Parent-Child Link, or Host Link Management. The following operations trigger a split process for **only the relevant parameter sheet**: register/update/discard/restore of a Parameter Sheet (Uses Host Group), or create/edit/initialize with "Uses Host Group" selected in Parameter Sheet Definition/Creation.

## Menu structure

| Menu/Screen | Description |
|---|---|
| Host Group List | Register host groups. |
| Host Group Parent-Child Link | Link parent-child relationships between host groups. |
| Host Link Management | Link a host group, an operation, and a target host. |
| Host Group Split Targets | Manage the parameter sheet information and processing status for splitting from host-group level to host level. |

## Flow from configuration to work execution

1. **Create the parameter sheet**: use the parameter sheet creation function to create the host-group parameter sheet menu.
2. **Register host groups** (Host Group List): items are Host group name (required, max 255 bytes) and Priority (0 to 2147483647; if left blank and multiple groups exist at the same level, their priority order becomes random).
3. **Define parent-child relationships between host groups** (Host Group Parent-Child Link): select the parent host group and child host group (both required, list selection). A combination that creates a circular parent-child relationship (e.g. HG1→HG2→HG3→HG1) causes an error on register/update.
4. **Link a host group, an operation, and a target host** (Host Link Management): Host group name (required), Operation (can be registered blank; if blank, the link is valid for all operations, otherwise it is valid only for the specified operation), Host name (required). This link enables selecting a target host from within a host group.
5. **Register into the parameter sheet** (the created host-group parameter sheet, Input menu): Host name (select a target host or a host group; prefix `[H]` = host, `[HG]` = host group; required), Operation name (required), Reference date/time / Scheduled date / Last execution date/time (auto-displayed based on the selected operation), the parameter sheet's target items (enter concrete values; these are reflected as variable values in "Reflecting substitution values" below). The combination of "Host name" and "Operation" is registered as unique (the same host can be registered again as long as it is paired with a different operation).
6. **Resolving to hosts** (internal processing, no user action needed): the "Host Group Resolution function" aggregates the registered information per operation and inherits it down to the target-host level according to the host group links. The result can be checked in the Auto-Registration of Substitution Values menu group's menu (view-only; register/update/discard/restore not possible). If a value is registered on both the host group and the target host, **the target host's value takes precedence**; the value from the parent host group is inherited only when the target host's value is blank.
7. **Link the per-operation, per-target-host item values** (Auto-Registration of Substitution Values setting): link the target menu/item to the Movement's variable (register/update/discard/restore possible). The registered information is reflected internally into "Substitution Value Management" and "Target Host".
8. **Reflect the target hosts linked to the operation** (internal processing): the target hosts associated with the operation are automatically reflected and can be checked in the "Target Host" menu.
9. **Reflect substitution values** (internal processing): for each operation, the concrete values entered in step 5 are automatically reflected as the values to substitute into the target Movement's Playbook/template variables, and can be checked in the "Substitution Value Management" menu.

## Example

Suppose host groups `HG_1` (children: `hg_1a`, `hg_1b`) and `HG_2` (children: `hg_2a`, `hg_2b`) are defined, linked as `hg_1a`→`host_1a`, `hg_1b`→`host_1b`, `hg_2a`→`host_2a`, `hg_2b`→`host_2b`, and the following is registered in the parameter sheet.

| Target host/host group | Operation | Item 1 | Item 2 |
|---|---|---|---|
| HG_1 | 2023/01/01 00:00_OP1 | 111 | AAA |
| HG_2 | 2023/01/01 00:00_OP1 | — | BBB |
| host_1a | 2023/01/01 00:00_OP1 | 222 | — |

After resolution, `host_1a` gets its own registered value `222` for item 1 (the target host's value takes precedence), and inherits `AAA` from parent `HG_1` for item 2 since its own value is blank. `host_1b` inherits both `111` and `AAA` from parent `HG_1` for items 1 and 2. For `host_2a` and `host_2b`, item 1 is blank because the parent `HG_2`'s value is blank, and item 2 inherits `BBB` from `HG_2`.
