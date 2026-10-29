# Substitution value auto-registration setting (subst_value_auto_reg_setting_ansible_legacy)
## About the type of variable in the substitution value auto-registration setting
- Specifying substitution_order makes the variable a list type (e.g., ["value"]); leaving it blank makes it a scalar (single value).
- Match the type to how the variable is received on the Playbook side:
    - A variable looped over with with_items etc. → specify substitution_order
    - A variable that passes a single value, such as dest in copy → leave substitution_order blank
- An error such as `'_AnsibleTaggedList' object has no attribute ...` is a sign that a list type is being passed where a scalar is expected. Suspect substitution_order.

## About specifying column_substitution_order
- Do not specify this if the parameter sheet selected in `menu_group_menu_item` is not in bundle format.
- Specify the assignment order `input_order` of the record registered in the parameter sheet selected in `menu_group_menu_item`.

## About the number of settings when linking a bundle item to a single list variable
- **Important**: When multiple rows (values) are entered for a single bundle item and passed as multiple elements
  of a single list variable, the substitution value auto-registration setting requires "as many records as the number of rows."
  1 record = the linkage for 1 row of the bundle; multiple rows are not linked together by a single record.
- Specifically, for the same `menu_group_menu_item` (From item) x the same `variable_name` (To variable),
  create as many records as the number of rows you want to link, specifying the following pair in each record:
    - `column_substitution_order`: the assignment order (input_order) of the bundle row to pick up
    - `substitution_order`: the order of the element within the list variable
- Example: If row 1 = httpd (input_order=1) and row 2 = unzip (input_order=2) are entered for the bundle item "Install package",
  and these are passed to `ITA_DFLT_Install_Target_packages` (a list variable looped over with with_items),
  2 substitution value auto-registration setting records are required:
    | From item | To variable | column_substitution_order | substitution_order |
    |---|---|---|---|
    | Install package | ITA_DFLT_Install_Target_packages | 1 | 1 |
    | Install package | ITA_DFLT_Install_Target_packages | 2 | 2 |
- Check point: When linking a bundle item to a list variable, always verify that
  "the number of rows planned for input" == "the number of substitution value auto-registration setting records for that variable."

## [Pre-registration check] Consistency between the number of bundle rows and the number of substitution value settings (required when linking a list variable)

When linking multiple rows of a bundle (vertical:1) to a list-type variable, before registering rows
to the parameter sheet, verify the count consistency using the following procedure.

Procedure:
1. Fetch the target substitution value auto-registration settings using `menu-filter` (menu: `subst_value_auto_reg_setting_ansible_legacy`).
2. Count the number of existing records tied to "the same From item (`menu_group_menu_item`) x the same To variable (`variable_name`)."
3. Cross-check whether "the number of rows to be entered this time (the number of `input_order` values in the bundle)"
   == "the number of substitution value setting records counted above."
4. If there is a shortfall, **add the missing substitution value setting records first**, then
   register the parameter sheet rows. For each added record, specify the following pair:
   - `column_substitution_order`: the assignment order (`input_order`) of the bundle row to pick up
   - `substitution_order`: the order of the element within the list variable
5. Clearly present the cross-check result (planned number of rows / number of existing settings / surplus or shortfall) to the user before proceeding to registration and execution.

Timing:
- This verification must always be performed **before** "registering rows to the parameter sheet" and
  "Movement execution (execute-driver / dryrun-driver)."

Supplementary notes:
- 1 record = the linkage for 1 row of the bundle; multiple rows are not linked together by a single record.
- If the substitution value settings are insufficient, the latter part of the `input_order` values can be
  **silently dropped without an error**, so do not skip the count cross-check.

---

## Symptom lookup: only some bundle rows are processed / the latter part is missing

- Symptom: Even though N rows were registered in the parameter sheet, fewer than N `item` entries
          (the target of the with_items loop) appear in the execution log. The latter part of the
          `input_order` values is entirely missing. In most cases this happens silently without an
          error, making it easy to miss.
- Cause: The substitution value auto-registration setting records for the list variable (a list-type
          variable with `substitution_order` specified) do not match the number of rows
          (e.g., 4 rows registered but only 2 settings exist → the latter 2 do not make it into the variable list).
- Check: Count the number of records for the target From item (`menu_group_menu_item`) x To variable
          (`variable_name`) using `menu-filter`, and cross-check against the number of registered rows
          (the count of `input_order` values).
- Remedy: Add the missing `(column_substitution_order, substitution_order)` records, then re-run.

Related keywords: missing / latter part / row count / record count / match / input_order / record count / with_items / list variable
