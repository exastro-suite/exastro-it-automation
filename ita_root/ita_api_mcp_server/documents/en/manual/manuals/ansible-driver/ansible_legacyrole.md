# Ansible-LegacyRole Configuration and Usage

Ansible-LegacyRole applies settings using Ansible's standard features, the same as Legacy mode, but build code is registered as packages (Roles), and work patterns are composed of combinations of Roles. Used for installation and environment setup with Role packages provided by product divisions.

## Menu Configuration

In addition to the Basic Console and Ansible Common menus, Ansible-LegacyRole has its own menus: Movement List, Role Package Management (manages Role packages), Movement-Role Association (manages which Role packages a Movement includes), Variable Nesting Management (manages the maximum repeat count when a nested variable consists of a repeating array), Auto-Assignment Setting, Execute Work, Work Management, Work Status Check, Target Hosts, Assigned Value Management, and Role Name Management / Movement-Variable Association / Nested Variable Member Management / Nested Variable Array Combination Management (all hidden menus, for internal processing).

## Work Flow

1. Register connection information in the device list and an operation name in the operation list.
2. If needed, register AAP host information / Interface Information / execution-environment-related items (template / parameter sheet / Execution Environment Management).
3. Register a Movement, and register a Role package.
4. If needed, register global variables, templates, file materials, and unmanaged variables.
5. Link the Role package to the Movement in Movement-Role Association.
6. If needed, register the maximum repeat count for nested variables in Variable Nesting Management.
7. Create a parameter sheet, register data, and link it to the Movement's variables in the Auto-Assignment Setting.
8. Execute work → check Work Status → review history in Work Management.

## Movement List

The items are the same as Ansible-Legacy: Movement ID (auto-numbered), Movement name (required, up to 255 bytes), delay timer (0–2147483647, in minutes), Ansible connection info (host designation format required; WinRM connection; header section up to 4000 bytes, default when unset is `hosts: all` / `remote_user: "{{ __loginuser__ }}"` / `gather_facts: no` / `become: yes` (become omitted for WinRM); option parameters up to 4000 bytes; ansible.cfg up to 100MB), Ansible Execution Agent connection info (execution environment: required when using Agent; ansible-builder parameters up to 4000 bytes), Ansible Automation Controller connection info (execution environment: selected from AAC sync data, defaults to the default execution environment if not selected), and remarks (up to 4000 bytes). If `become: yes` is set, sudo permission with NOPASSWD must be configured on the target host.

## Role Package Management

Maintains user-created Role package files (zip, compressed from the directory level containing the `roles` directory) (view/register/update/decommission).

| Item | Description | Constraints |
|---|---|---|
| Role package name | Any name | Required, up to 255 bytes |
| Role package file | ZIP format (contained Playbook files must have no UTF-8 BOM) | Required, up to 100MB |
| Target: Linux/Windows/other | Supported OS (leaving unselected does not affect execution) | "Other" up to 4000 bytes |
| Python required | Select "＊" if required (leaving unselected does not affect execution) | - |
| Description / Description (en) / Remarks | Free text | Up to 4000 bytes each |

Because internal variable extraction is not real-time, it may take time before variables are reflected. **Variable names are managed uniquely per Movement**: variable names extracted from the materials subject to extraction are managed uniquely per Movement. If different Roles within the same Role package use the same variable name with a different variable structure (normal vs. nested), registration fails (only a difference in the order member variables are listed is fine; mixing normal and nested variables, or differing nested structures, causes an error). The same name is fine across different Role packages.

## Movement-Role Association

Manages the Role packages a Movement includes (view/register/update/decommission). Items: Movement (list selection, required), Role package name:Role name (multiple Role packages cannot be registered for the same Movement, required), include order (1–2147483647, executed in ascending order, required), and remarks (up to 4000 bytes).

## Variable Nesting Management

Views and updates the maximum repeat count for array members of nested variables within a Role package that define a repeating array. Items: maximum repeat count (1–1024; the upper bound can be changed via the identifier "MAXIMUM_ITERATION_ANSIBLE-LEGACYROLE" in the Management Console, required) and remarks (up to 4000 bytes). Initial registration/updates happen through internal processing based on the repeating arrays of nested variables in the Role package, and are not real-time, so it may take time before a variable becomes usable in the Auto-Assignment Setting.

## Auto-Assignment Setting

Manages the link between parameter sheet item values and Movement variables (view/register/update/decommission). Registered information is reflected in "Assigned Value Management" and "Target Hosts" at execution time.

| Item | Description | Required |
|---|---|---|
| Parameter Sheet (From) Menu:Item | An item from a parameter sheet (with host/operation) | 〇 |
| Parameter Sheet (From) Assignment Order | Only when using a bundle | Required when using a bundle |
| Registration method | Value type / Key type | 〇 |
| Movement name | A registered Movement | 〇 |
| IaC Variable (To) Movement name:Variable name | A variable used in the material linked via Movement-Role Association | 〇 |
| IaC Variable (To) Movement name:Variable name:Member variable | The member variable when a nested variable is selected (only variables requiring an actual value are shown; hierarchy is delimited by ".", and a repeating array position 0 or higher is shown with "[]") | Required when a nested variable is selected |
| IaC Variable (To) Assignment Order | Assignment order for a multi-value variable (1 or higher; required even for a single value) | Required for multi-value variables |
| NULL linkage | True/False. Uses the Interface Information value if not selected | - |
| Remarks | Free text | Up to 4000 bytes |

**Example of selecting a member variable**: if `defaults/main.yml` defines `name`, `object`, `directory`, `password`, `user.root.dev`, `user.root.prod`, etc. nested under `VAR_aaaa`, Variable Nesting Management registers `0`, `0.directory`, `0.password`, `0.user.root`, `0.user.root.dev`, `0.user.root.prod` (max repeat count 1), and the Auto-Assignment Setting makes `[0].name`, `[0].object`, `[0].directory[0].create_dir`, `[0].user.root[0].prod[0].prod_user`, etc. selectable. Updating the max repeat count for `0.user.root.prod` from 1 to 3 in Variable Nesting Management adds `[0].user.root[0].prod[1].prod_user` and `[0].user.root[0].prod[2].prod_user` as additional selectable options.

**Example of multi-value variable assignment order** (same as Ansible-Legacy): linking parameter sheet item values value1–4 to `VAR_substitutionA` with order 30/10/20 and to `VAR_substitutionB` with order 2/4/1/3 results in the host variables file containing `VAR_substitutionA: [value2, value3, value1]` and `VAR_substitutionB: [value3, value1, value4, value2]` (values are packed in order even if the assignment order numbers are not consecutive).

**Example of nested variable output**: linking values (value1, value2) only to `[0].name` and `[0].user.root[0].dev[0].dev_user` of `VAR_output` results in the host variables file containing `VAR_output: [{name: value1, user: {root: [{dev: [{dev_user: value2}]}]}}]` — only the member variables with a linked value are output.

**Example of using file/template-embedded variables**: register `CPF_test` in File Management and `TPF_sample` in Template Management as parameter sheet item values, link them in the Auto-Assignment Setting to Role variables (e.g. `VAR_filetest`, `VAR_temptest`), and confirm in Work Status Check's Assigned Value check that the values `'{{ CPF_test }}'` and `'{{ TPF_sample }}'` are reflected.

## Execute Work / Work Status Check / Work Management / Target Hosts / Assigned Value Management

Operation is the same as Ansible-Legacy. **Execute Work** execution types: Execute work (performs the build work), Dry run (equivalent to `--check`), Check parameters (reflects the Auto-Assignment Setting information into Assigned Value Management/Target Hosts for review only). A scheduled date/time can only be a future date/time.

**Work Status Check**: shows status, execution log, and error log. When run via AAC, logs are grouped by the device list's user/password/ssh private key file/passphrase/connection type/instance group, and further split by job slice count, shown in tabs (`exec.log` = all logs, `exec_<group number>_<sequence number>` = split logs). Target Hosts check / Assigned Value check / Emergency Stop / Cancel Schedule buttons, log search, input data/result data download, and collection status (Collected / Collected (with notice) / Not applicable / Collection error) can all be checked here.

**Work Management**: lists and filters work number, execution type, status, emergency stop flag, execution engine, calling Conductor, executing user, registration date/time, Movement details, operation, input data/result data, work status, collection status, and Conductor instance number.

**Target Hosts**: shows item number, work number, operation, Movement name, host name, and remarks.

**Assigned Value Management**: shows item number, work number, operation, Movement name, host name, Movement name:variable name, Movement name:variable name:member variable, value (encrypted and used via ansible-vault if Sensitive is True; otherwise shown as the actual value/file name), assignment order, and remarks.

## Writing Role Packages

For the basic format, refer to the best practices in the official Ansible manual. Directories to include in the zip, and how ITA treats them:

| Directory/File | Required | ITA Handling |
|---|---|---|
| site.yml (master Playbook) | Optional | Created by ITA; overwritten if present |
| hosts | Optional | Created by ITA; overwritten if present |
| group_vars | Optional | Not handled by ITA; deleted if present |
| host_vars | Optional | Created by ITA; overwritten if present |
| ITA readme | Optional | Defined per Role. Must be created with no UTF-8 BOM |
| roles | Required | Upload fails if missing |
| roles/[role name] | Required | Any directory containing a `tasks` directory is treated as a Role. Can be nested at any depth |
| roles/[role name]/tasks | Required | main.yml is required (no UTF-8 BOM); other files may also be placed here |
| roles/[role name]/handlers, templates, files, vars, defaults, meta | Optional | Each file must be created with no UTF-8 BOM (ITA does not check the contents or presence) |

**When the Role name is a directory hierarchy**: the level containing the `tasks` directory is recognized as the Role. If a parent directory has a `tasks` directory, any `tasks` directory in a child directory below it is not treated as a separate Role (only the topmost `tasks` is valid).

The **master Playbook** consists of a header section (changeable via the Movement List's header section; default as described above) and a roles section (executes each Role in the include order set in Movement-Role Association).

## Writing the ITA readme

If you do not want to define variables directly in the Playbook, or if a variable is not defined in the defaults variable definition file, you can specify actual values through Assigned Value Management by writing variable definitions in the ITA readme file. Naming convention: `ita_readme_[role name].yml` (if the role name contains `/`, replace it with `%`, e.g. `mysql/install` → `ita_readme_mysql%install.yml`). Format: YAML, no UTF-8 BOM.

Variable adoption rule: if only defaults defines it, the defaults structure is used; if only the ITA readme defines it, the ITA readme structure is used; if both define it, the ITA readme takes precedence. The ITA readme is detached from the Role package at execution time, and the variables/values written there are not passed to Ansible (it is a mechanism for telling ITA the variable name and type, not for defining actual values).

**Usage examples**: ① You can supply parameters for a Role obtained externally (e.g. from Galaxy) without editing it, by placing an ITA readme outside the `roles` directory. ② The ITA readme is a mechanism for telling ITA the variable name and type, not for defining actual values. ③ Variables and default values in `defaults/main.yml` remain in effect unless overridden by host_vars. ④ The host_vars file is auto-generated per execution from the ITA parameter sheet. ⑤ If you do not want to modify `defaults/main.yml`, the ITA readme can be used as a workaround to define additional variables (in case of duplication, the ITA readme takes precedence). ⑥⑦ Whether a value is present for a variable defined in the ITA readme can be used for conditional branching based on `length` or `defined` evaluations.

## Appendix: Input and Result Data for Ansible Execution

Input data can be downloaded as a ZIP file from Work Status Check (device list passwords and variables with Sensitive set to True are encrypted with ansible-vault). Main mappings: Role package → `/roles`, template/file materials → `/template_files`/`/copy_files`, values (files) from Assigned Value Management → `/upload_files`, various variables and device information → `/host_vars`, ssh/WinRM key files → `/ssh_key_files`/`/winrm_key_files`, server certificates → `/winrm_ca_files`, option parameters → `/AnsibleExecOption.txt` (Core/AAC) or `/env/cmdline` (Agent), device list connection information → `/hosts` (Core/AAC) or `/inventory/hosts` (Agent), Role name and include order → `/site.yml`, execution-environment-related files (Agent only) → `builder_executable_files/`, `runner_executable_files/`.

Main result data files: `result.txt` (Core only), `error.log`/`exec.log.org`/`exec.log` (all engines), `exec_<work number>_<group number>` (split log, AAC only), `forced.txt` (emergency stop record, Core/Agent), `user_files` (output destination for `__workflowdir__`, all engines), `child_exec.log`/`child_error.log` (ansible-builder execution log, Agent only).
