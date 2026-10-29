# Procedure for decommissioning (deleting) a parameter sheet/data sheet (important)
## Decommissioning overview
When decommissioning (logically deleting) a parameter sheet:
1. The record in `menu_definition_list` cannot be decommissioned, so leave it as is
   (the definition entry in `menu_definition_list` is merely "configuration information for creation," so leaving it in place has no impact)
2. Records in `role_menu_link_list` (role-menu link) are subject to decommissioning
3. Records in `subst_value_auto_reg_setting_<driver>` (substitution value auto-registration setting) are subject to decommissioning
4. Records in `menu_list` (menu management) are subject to decommissioning

### Menu entities subject to decommissioning (watch for oversights)
- `subst_value_auto_reg_setting_<driver>` (substitution value auto-registration setting)
  Records subject to decommissioning:
    - Records in `subst_value_auto_reg_setting_<driver>` whose `menu_name_rest` matches the `menu_name_rest` of the parameter sheet to be decommissioned + `_subst`.

- `role_menu_link_list` (role-menu link management)
  Depending on what was created, a single parameter sheet corresponds to multiple menu entities, and multiple rows are registered in `role_menu_link_list` for each operable role, so all of these records must be decommissioned.
  Note, however, that some records may not exist depending on the parameter sheet type.
  Records subject to decommissioning:
    - Records in `role_menu_link_list` whose `menu_name` ends with `:` + `menu_name_en` of the parameter sheet to be decommissioned.

- `menu_list` (menu management)
  Depending on what was created, a single parameter sheet is split across multiple menu entities registered in `menu_list`, so all of these records must be decommissioned.
  Note, however, that some records may not exist depending on the parameter sheet type.
  Records subject to decommissioning:
    - Records in `menu_list` whose `menu_name_rest` matches the `menu_name_rest` of the parameter sheet to be decommissioned.
    - Records in `menu_list` whose `menu_name_rest` matches the `menu_name_rest` of the parameter sheet to be decommissioned + `_subst`.
    - Records in `menu_list` whose `menu_name_rest` matches the `menu_name_rest` of the parameter sheet to be decommissioned + `_ref`.

### Decommissioning procedure (tool operations)
- `role_menu_link_list` (role-menu link management)
  1. Search using `menu-filter` (menu: "role_menu_link_list") with `{discard: {NORMAL: "0"}, menu_name: {NORMAL: `:` + `menu_name_en`}}`.
  2. From the search results, narrow down to records whose menu_name ends with `:` + `menu_name_en`.
  3. Use `maintenance-all` (menu: "role_menu_link_list") to set type="Discard" for the narrowed-down records (last_update_date_time is required for optimistic locking).

- `subst_value_auto_reg_setting_<driver>` (substitution value auto-registration setting)
  1. Use `menu-filter` (menu: "subst_value_auto_reg_setting_<driver>") to fetch the records (get the latest last_update_date_time).
  2. Narrow down to records whose `menu_name_rest` matches the `menu_name_rest` of the parameter sheet to be decommissioned + `_subst`.
  3. Use `maintenance-all` (menu: "subst_value_auto_reg_setting_<driver>") to set type="Discard" for the narrowed-down records (last_update_date_time is required for optimistic locking).

- `menu_list` (menu management)
  1. Use `menu-filter` (menu: "menu_list") to fetch the target 3 menu entities (get the latest last_update_date_time).
  2. Use `maintenance-all` (menu: "menu_list") to set type="Discard" for the 3 records (last_update_date_time is required for optimistic locking).
  3. Also decommission any input data, Movement associations, substitution value auto-registration settings, etc. linked to that parameter sheet, in child-to-parent order.
