# Reference for parameter sheet definitions (menu_definition_and_creation.md)

- **Important** Always confirm the parameter sheet definition with the user before creating the parameter sheet.
- **Important** The parameter sheet type (sheet_type_id), host group (hostgroup), and bundle (vertical) cannot be changed after the parameter sheet is created.
- **Important** The "required" setting for each item cannot be changed after the parameter sheet is created. The required setting must be finalized at creation time.

- **Important (compliance check)** When proposing a parameter sheet definition, as evidence that this reference has been read,
  the proposal must always explicitly state the following "pre-creation check results" (this must not be omitted).
  `create-menu` must not be called without presenting these results.
    1. A list of the variables and types for all Playbooks planned for use (or all modules linked to the Movement)
       (state clearly whether each variable is a "list type" or a "single value")
    2. The finalized values for sheet_type_id / hostgroup / vertical, and the rationale for them
       (in particular, for vertical, cite the result of the "Bundle (vertical) determination procedure" below)
    3. Confirmation that the above cannot be changed after creation

- Notes on item definitions
    - Check the variables and variable types of the Playbook to be used, and define items to match them.

- Notes on the parameter sheet type (sheet_type_id)
    - For parameter sheets related to work execution, basically use "with host/operation" (sheet_type_id: "1").
    - For parameter sheets used as the output destination of data accumulation or collection functions, use a data sheet (sheet_type_id: "2").

- Notes on bundles
    - Enabling a bundle allows the same set of items to be registered repeatedly in vertical rows (repeated rows / vertical layout) for the same combination of "host name" x "operation" (or operation alone).
    - If the variable type of the Playbook to be used is a list format, propose the use of a bundle to the user and confirm.
    - Disabling a bundle adds a unique constraint on the same "host name" x "operation" (or operation alone).
    - Enabling a bundle adds a unique constraint on the assignment order `input_order` in addition to the same "host name" x "operation" (or operation alone).
    - Bundles cannot be used with data sheets (sheet_type_id: "2").
    - The assignment order `input_order` can be linked to a Playbook etc. by specifying it in `column_substitution_order` of the substitution value auto-registration setting.

- **Important (design when list-type and single-value variables are mixed)**
    - With a bundle (vertical:1), an item set is registered across multiple rows (input_order) for the same "host name x operation".
      In this case, when rows are added to pass multiple elements to a list-type variable, the question of whether a value must be entered also arises for single-value items in the same row.
    - When list-type variables (items that should span multiple rows) and single-value variables (items for which one row is sufficient) are mixed, create the single-value items with required:"0" (optional).
      This allows the single-value items to be left blank from the second row onward, preventing a single-value variable from unintentionally becoming a multi-element list.
    - Since required cannot be changed after creation, this decision must always be made at definition time.
    - Guideline for judgment:
        | Variable the item links to | Number of rows | Recommended required |
        |---|---|---|
        | List type (passing multiple elements) | Multiple rows | Depends on usage (each row's item can be "1") |
        | Single value (one element is sufficient) | Only 1 row of input | "0" (optional) so rows 2+ can be left blank |

- **Bundle (vertical) determination procedure (always perform this before running create-menu, and record the result in the "pre-creation check results" above)**
    1. Enumerate the type (list type / single value) of all variables planned for use.
    2. If either "for a single combination of 'host name' x 'operation', a value needs to be passed as a list of multiple values to a certain item"
       or "the user has stated that they want to split records (rows) by value/element"
       → **a bundle (vertical:1) is required**. This cannot be achieved with a non-bundle (vertical:0).
    3. If all variables are single-valued and one combination = one record is sufficient, choose vertical:0.

- **Failure when trying to make a list with a non-bundle (vertical:0) (a common anti-pattern)**
    - vertical:0 places a unique constraint on "host name x operation",
      so **only one record can be registered for the same combination**.
      Therefore, "splitting records by value/element to pass a list" is structurally impossible.
    - If records are passed separately to maintenance-all in this state, the following error occurs:
      `The combination is incorrect. (Combination: {'operation_name_select': ..., 'host_name': ...})`
    - If you encounter this error, or realize that "vertical:0 is set even though you want to pass multiple values to a list-type variable",
      review the design and switch to a bundle (vertical:1).
    - Note that the default solution when multiple values need to be passed to a list-type variable is vertical:1.
      If avoiding this by aggregating into a single item (e.g., comma-separated), you must always verify in the body (YAML)
      that the target module/Playbook interprets that aggregated format as multiple values.

- **Vertical determination quick reference table**
    | Variable type / user requirement                                  | How records are held           | vertical   |
    |---------------------------------------------------------------------|---------------------------------|------------|
    | All single values                                                    | 1 combination = 1 record        | 0          |
    | Want to pass a list type as multiple elements for 1 combination      | Enter items across multiple rows vertically | 1 (required)  |
    | Want to split records by value/element                              | Vertical layout (bundle)        | 1 (required)  |
    ※ A configuration where "multiple values are aggregated into a single cell and passed as a single item" can only be considered if the corresponding argument of the target Ansible module (or Playbook) is implemented to interpret that aggregated format as multiple values.
      Whether aggregation is possible must always be judged by checking the actual Playbook/module specification, and must not be uniformly decided as "comma-separation is an acceptable compromise."
      When it cannot be determined, or when you need to reliably pass multiple elements, choose vertical:1.

- **Supplementary notes on the relationship between list-type variables and bundles**
    - When multiple rows are entered for a single bundle item and passed as multiple elements of a single list variable, the substitution value auto-registration setting requires "as many records as the number of rows"
      (for details, see the reference for subst_value_auto_reg_setting_ansible_legacy).
