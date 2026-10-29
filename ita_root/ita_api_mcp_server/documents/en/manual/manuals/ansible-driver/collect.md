# Collection Feature Configuration and Usage

The collection feature is a mechanism that automatically registers values into a parameter sheet based on the result of a work execution (a source file output in a specified format) run via ITA's Ansible driver. The IaC (Playbook, Role) that generates the source file must be prepared by each user (reference: Ansible Playbook Collection).

## Operating Requirements

The following must be configured in ITA.

- A parameter sheet (with host/operation) has been created.
- Collection Item Value Management has the link configured between the work execution result (source file) and the parameter sheet item.
- The target device (host name) for collection is already registered in the device list.

After work execution, registration to the parameter sheet is performed if:

- The work execution completed successfully.
- The directory/file structure of the work execution result matches the specified structure.

## Collection Target Directory/File Structure

Source files for collection are output in YAML format (example: `VAR_RH_sshd_config: [{key: PermitRootLogin, value: yes}, ...]`).

The output directory can be referenced within the IaC using the following ITA proprietary variables.

| ITA Proprietary Variable | Maps To |
|---|---|
| `__parameter_dir__` | `_parameters` under the work result directory |
| `__parameters_file_dir__` | `_parameters_file` under the work result directory |
| `__parameters_dir_for_epc__` | `_parameters` under the working directory |
| `__parameters_file_dir_for_epc__` | `_parameters_file` under the working directory |

Directory structure: `_parameters/<host name>/<collection target file>`, `_parameters_file/<host name>/<upload target file>` (`_parameters_file` is a fixed name used for file uploads). The parent directory depends on the Ansible driver's execution mode: `/storage/<Organization>/<Workspace>/driver/ansible/<mode identifier>/<work number>/in (or out)/` (mode identifiers: legacy / pioneer / legacy_role). If these ITA proprietary variables are not used, the Playbook must be written with awareness of this structure to determine the output destination.

When collecting for a file-upload parameter sheet, a file corresponding to the variable value (file name/path) in the source file must be placed under `_parameters_file`. Specification methods:

| Method | Example | Notes |
|---|---|---|
| File name specification | `VAR_FILE_NAME: 'file name'` | If multiple files match, the target file is chosen at random |
| File path specification (suffix match) | `VAR_FILE_NAME: '/<level X>/<file name>'` | If multiple files match, the target file is chosen at random |

To delete a file, set the target variable's value to an empty string (`""`).

## Types of Variables Handled

Three types of variables can be used within a source file.

- **Normal variable**: `VAR_users: root` (defines a single value)
- **Multi-value variable**: `VAR_users: [root, mysql]` (defines multiple values)
- **Nested variable**: `VAR_users: [{user-name: alice, authorized: password}]` (a hierarchical variable; `user-name` etc. are member variables)

Variable names can use any ASCII character (0x20–0x7e) except the 7 characters `" . [ ] ' \ :` (characters that cannot appear at the start must be enclosed in quotes).

## Menu Configuration

- **Ansible Common → Collection Item Value Management**: configures the link between work execution output results (source files) and parameter sheet items, managing the target parameters registered by the collection feature.
- **Ansible-Legacy / Ansible-LegacyRole / Ansible-Pioneer → Work Management**: manages work execution history and shows the registration status and execution log for the collection feature.

## Work Flow

1. Create a parameter sheet (with host/operation).
2. Register the link between the source file and parameter sheet items in Collection Item Value Management.
3. Prepare and execute the work (select the operation, Movement, and workflow, and run).
4. The collection feature (BackYard) registers the parameter sheet for completed work numbers.
5. Check the collection status and logs on each mode's Work Management screen.

## Collection Item Value Management

Configures the link between collection items and parameter sheet items.

**Collection Item (From)**: parse format (parses a YAML-format file, required), PREFIX (file name, without extension, required), variable name (the target variable name for collection, required; a member variable is also required for array/hash structures), and member variable (entered for multi-value/nested variables).

**Parameter Sheet (To)**: menu group:menu:item (select the item shown delimited by ":"). If multiple "PREFIX-variable name" pairs are set for the same parameter sheet item, they are processed in ascending order of file name.

**Configuration examples**:
- Normal variable (`VAR_sample_config_1: yes` in `SAMPLE.yml`): PREFIX=`SAMPLE`, variable name=`VAR_sample_config_1`
- Multi-value variable (`VAR_sample2_conf: [SAMPLE1, SAMPLE2, SAMPLE3]`): member variable=`[0]`, `[1]`, `[2]`
- Nested variable (`VAR_RH_sshd_config: [{key:.., value:..}, ...]`): member variable=`[0].key`, `[0].value`, `[1].key`, `[1].value`
- Deep nesting (`sec_name` etc. under `VAR_RH_snmpd_info.com2sec[]`): member variable=`com2sec[0].sec_name`, etc.

## Checking Collection Status

Statuses shown on each mode's Work Management screen: "Not applicable" (no target file), "Collected" (completed), "Collected (with notice)" (an issue occurred during registration/update), "Collection error" (an issue with the Movement's operation or host). If the work status is not "Complete", the collection status remains blank and is not updated. Execution logs can be downloaded from "Collection Log" (examples: on registration failure, `{'item_1': [{...'msg': 'Regular expression error...'}]}`; `Operation is abolished, so registration and update processing is skipped`; when no target file exists, `There is no file in the collection target directory.`, etc.).

## Overview of BackYard's Registration Processing

1. Retrieve the list of work items whose collection target status is "Complete".
2. Retrieve the operation information, target hosts, and target source files for the target work number.
3. Check whether the target host is registered in the device list (registered = target for collection, unregistered = not applicable).
4. Retrieve the target parameter sheet's menu ID from the target source file and Collection Item Value Management (multiple files are processed in ascending order of file name).
5. Generate registration/update parameters, and determine registration vs. update based on whether unique data exists for the operation/host combination.
6. Register/update data in the parameter sheet.
7. Update the collection status for the work number.

Registration timing depends on BackYard's execution process cycle.

## Handling of Collected File Values (Data Type Conversion)

When a value in the YAML file is registered into a parameter sheet item (assumed to be a single-line string), it is converted as follows.

| YAML Notation | Registered String Value |
|---|---|
| `TEST` (unquoted), `'TEST1'`, `"TEST2"` | The string as-is (`TEST`, `TEST1`, `TEST2`) |
| `null`, `NULL`, empty value | `null` (data type is also null) |
| `"null"`, `"NULL"` | The string `"null"`, `"NULL"` |
| `true`, `false`, `YES`, `NO` (unquoted) | The string `"true"`, `"false"` |
| `"true"`, `"false"`, `"YES"`, `"NO"` (quoted) | Each string as-is |
| `''`, `""` (empty string) | Empty string `""` |
| `100` (number) | The string `"100"` |

## Handling Multiple Files with the Same Name

If files with the same name exist under different paths for the same host, specifying only the file name (e.g. `VAR_upload_file_1: config`) causes a random target to be selected. Path specification (suffix match, e.g. `'/APP002/config'`) also results in a random selection if multiple matches exist, but specifying a deeper path can narrow it down to a unique match (e.g. `'/APP003/APP002/config'` matches only that exact path).

## Appendix: Reference Materials

- Exastro Playbook Collection (example Playbooks for OS configuration collection)
- Ansible config retrieval sample (`makeYml_Ansible.yml`): an example that outputs facts variables such as `ansible_architecture` to `{{ __parameter_dir__ }}/{{ inventory_hostname }}/Ansible_conf.yml` using blockinfile, and collects files such as `/etc/vconsole.conf` to `{{ __parameters_file_dir__ }}/{{ inventory_hostname }}/` using the `fetch` module. Using facts variables requires `gather_facts: yes` in the header section (the default is `no`).
