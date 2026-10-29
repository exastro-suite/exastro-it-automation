# Ansible-Pioneer Configuration and Writing Interaction Files

Ansible-Pioneer is a mode that adds proprietary modules to Ansible and applies settings interactively. It supports servers, storage, and network devices that can be logged into via Telnet/SSH.

## Menu Configuration

In addition to the Basic Console and Ansible Common menus, Ansible-Pioneer has its own menus: Movement List, Interaction Type (manages classifications that group interaction files with the same purpose), OS Type (manages the OS type of target devices), Interaction File Material Collection (manages interaction files per Interaction Type × OS Type combination), Movement-Interaction Type Association (manages which Interaction Types a Movement includes), Auto-Assignment Setting, Execute Work, Work Management, Work Status Check, Target Hosts, Assigned Value Management, and Movement-Variable Association (hidden menu, for internal processing).

## Work Flow

1. Register OS types, connection information in the device list, and an operation name in the operation list.
2. If needed, register AAP host information / Interface Information / execution-environment-related items.
3. Register a Movement, and register an Interaction Type.
4. Register an interaction file for each Interaction Type × OS Type combination (Interaction File Material Collection).
5. If needed, register global variables, templates, file materials, and unmanaged variables.
6. Link the Interaction Type to the Movement in Movement-Interaction Type Association.
7. Create a parameter sheet, register data, and link it to the Movement's variables in the Auto-Assignment Setting.
8. Execute work → check Work Status → review history in Work Management.

## OS Type

Maintains the OS type of target devices (view/register/update/decommission). Items: OS type name (required, up to 255 bytes), device type (SV/NW/ST, each selected True/False), and remarks.

## Movement List

| Item | Description | Constraints |
|---|---|---|
| Movement ID | Auto-numbered | - |
| Movement name | Any name | Required, up to 255 bytes |
| Delay timer | Shows a warning if delayed beyond the specified period (1 minute or more). No warning if left unset | 0–2147483647 |
| Ansible connection info: host designation format | Select "Host name" when specifying a host not expressed by an IP address | Required |
| Ansible connection info: ansible.cfg | The file used at execution time (default used if not uploaded) | Up to 100MB |
| Ansible connection info: parallelism | Equivalent to ansible-playbook's `--forks` value | 1–4294967296 |
| Ansible Execution Agent connection info: execution environment / ansible-builder parameters | Execution environment is required when using Agent | Execution environment up to 4000 bytes |
| Ansible Automation Controller connection info: execution environment | Selected from AAC sync data; defaults to the default execution environment if not selected | - |
| Remarks | Free text | Up to 4000 bytes |

## Interaction Type

A classification that groups interaction files with the same purpose, abstracting away differences between OS types. Items: Interaction Type name (required, up to 255 bytes) and remarks.

## Interaction File Material Collection

Registers an interaction file for each combination of Interaction Type and OS Type (if one Interaction Type should support multiple OSes, register it separately for each OS Type under the same Interaction Type).

| Item | Description | Constraints |
|---|---|---|
| Interaction Type name / OS Type | Select from registered Interaction Types/OS Types | Both required |
| Interaction file material | No UTF-8 BOM, YAML format | Required, up to 100MB |
| Target: Linux/Windows/other, Python required | Usage indicators (leaving unselected does not affect execution) | "Other" up to 4000 bytes |
| Description / Description (en) / Remarks | Free text | Up to 4000 bytes each |

Because internal variable extraction is not real-time, it may take time before variables become usable in the Auto-Assignment Setting.

## Movement-Interaction Type Association

Manages the Interaction Types corresponding to the interaction files a Movement includes (view/register/update/decommission). Items: Movement (required), Interaction Type (required; for each target, the interaction file linked to its OS Type and Interaction Type becomes the one that runs), include order (1–2147483647, executed in ascending order, required), and remarks (up to 4000 bytes).

## Auto-Assignment Setting

Manages the link between parameter sheet item values and Movement variables (view/register/update/decommission). Registered information is reflected in "Assigned Value Management" and "Target Hosts" at execution time. The item structure is the same as Ansible-Legacy: Parameter Sheet (From) Menu:Item (required), assignment order (required when using a bundle), registration method (Value type/Key type, required), Movement name (required), IaC Variable (To) Movement name:Variable name (required), assignment order (required for multi-value variables, entered even for a single value), NULL linkage (True/False, uses the Interface Information value if not selected), and remarks.

A variable with no assignment order entered is treated as a normal variable; if entered, it is treated as a multi-value variable (values are packed in order even if not consecutive). Only variables registered in the Auto-Assignment Setting are output to the host variables file at execution time, and if a variable used in an interaction file is not registered, work execution fails immediately with an error (unlike Legacy, an unregistered variable causes an immediate error here).

The usage example for linking file-embedded and template-embedded variables to interaction file variables is the same as Ansible-Legacy (register `CPF_test` from File Management and `TPF_sample` from Template Management as parameter sheet item values, then link them to Role-internal variables in the Auto-Assignment Setting).

## Execute Work / Work Status Check / Work Management / Target Hosts / Assigned Value Management

Operation is the same as Ansible-Legacy. **Execute Work** execution types: Execute work (performs the build work), Dry run (equivalent to `--check`), Check parameters (reflects the Auto-Assignment Setting information for review only). A scheduled date/time can only be a future date.

**Work Status Check**: shows status, execution log, and error log. When run via AAC, logs are grouped by the device list's various values, further split by the job slice count option parameter, and shown in tabs (`exec.log` = all logs, `exec_<group number>_<sequence number>` = split logs). Target Hosts check / Assigned Value check / Emergency Stop / Cancel Schedule buttons, log search, input data/result data download, and collection status can all be checked here.

**Work Management, Target Hosts, and Assigned Value Management** have the same item structure as Ansible-Legacy.

## Writing Interaction Files

An interaction file consists of two sections: `conf` (specifies the timeout value, 1–3600 seconds, via the `timeout` parameter) and `exec_list` (describes the build process against the target using interaction modules). Since ITA's proprietary modules connect via ssh/telnet at execution time, password authentication handling (`expect: '*assword'` / `exec: 'password'`) is typically needed at the start of `exec_list` if required.

### List of Interaction Modules

| Module | Purpose |
|---|---|
| expect | Waits for a command prompt, then submits a command. |
| state | Submits a command, waits for the prompt, then analyzes the standard output content with an external shell script to judge the result. |
| command | Can submit commands consecutively, with conditional branching before and after submission. |
| localaction | Submits a command within the execution environment of Ansible Core/AAC/Agent. |

**expect module**: alternates `expect` (required, the command prompt, regex allowed; ends abnormally if not received within the timeout) and `exec` (required, the command to submit). Example: `- expect: '*assword'` / `exec: 'password'`.

**state module**: `state` (required, the command to submit), `prompt` (required, the command prompt, regex allowed), `shell` (optional, the name of a custom shell script used to judge the result; exit code 0 = success, otherwise failure; if omitted, the default shell greps the standard output for the `parameter` string, treating even a single match as success), `parameter` (optional, the search string(s); multiple can be specified; when using `shell`, these become arguments `$2` onward), `stdout_file` (optional, where the standard output is saved; an ITA-generated file name is used if omitted), `success_exit` (optional, "yes" ends immediately as success when the result is success; default "no"), `ignore_errors` (optional, "yes" continues to the next step even on failure; default "no"). The custom shell script is invoked with `$1` = stdout_file and `$2` onward = the contents of `parameter`.

**command module**: `command` (required, the command to submit), `prompt` (required, the command prompt, regex allowed), `timeout` (optional, uses `conf.timeout` if omitted), `register` (optional, a variable name to save the standard output; usable only in when/exec_when/failed_when, holds only one value), `with_items` (optional, specifies multi-value variable names to submit the command repeatedly; referenced as `{{ item.X }}`, X = 0–99; if variables have different numbers of values, the loop runs for the maximum count with missing entries treated as null; variables used in `prompt`/`timeout` need one more value than `command`), `when` (optional, a condition checked before submission; the command is submitted if it matches, skipped otherwise), `exec_when` (optional, a continue condition per loop iteration when using `with_items`), `failed_when` (optional, a condition checked against the stdout content after submission; matching means success, not matching means failure).

Condition expression format: variable-defined check (`VAR_xx is define` / `is undefine`), variable value check (`VAR_xx or register-variable comparison-operator string/VAR_xx`, where the comparison operator is `==` `!=` `>` `>=` `<` `<=`), `match(regex)` / `no match(regex)`, and for `failed_when` also `stdout comparison-operator string`. OR conditions are written on the same line with `OR`; AND conditions are written on separate lines.

**localaction module**: `localaction` (required, the command to submit; `conf.timeout` does not apply — it does not proceed until the command completes), `ignore_errors` (optional, default "no"). Used for file operations, etc. on the execution engine side (Ansible Core/AAC/Agent) (e.g. creating a directory under `{{ __workflowdir__ }}`).

### Regular Expressions and Escaping

The `expect` of the expect module, the `prompt` of the state module and command module, and `match()` in when/exec_when/failed_when are evaluated as regular expressions. If they contain `\` `*` `.` `+` `?` `|` `{}` `()` `[]` `^` `$`, these must be escaped with `\`.

### Notes

- Do not use a trailing wildcard `.*` in `prompt`, as this causes the standard output to be empty.
- Interactive commands (such as `ssh-keygen`) cannot be handled with the `command`/`state` modules; use the `expect` module instead.
- Multi-value variables can only be used with the `command` module's `with_items` (using them in other parameters causes an error).
- Always submit `exit` as the last line of the interaction file (omitting this can disconnect the session immediately after the final process completes, which may cause a time-consuming process to end abnormally).
- Enclose the entire parameter value of each module in quotes per YAML syntax (when it contains a variable, or is a constant ending in `:`, etc.).
- The login user's LANG supports UTF-8/euc/shift_jis (set via LANG in the device list). With euc/shift_jis, some full-width characters (such as circled numbers) may fail to decode to UTF-8 and display as `??`, or cause the `expect` wait to time out.
- Commands are terminated with "LF". If the target's line ending is "CRLF", append `\r` to the end of the submitted command.
- An Operating System Command escape sequence may be appended immediately before the target's command prompt, but ITA strips the escape sequence immediately preceding `prompt`.

## Appendix: Input and Result Data for Ansible Execution

Input data can be downloaded as a ZIP file from Work Status Check (device list passwords and variables with Sensitive set to True are encrypted with ansible-vault). Main mappings: interaction file → `/child_playbooks`, template/file materials → `/template_files`/`/copy_files`, values (files) from Assigned Value Management → `/upload_files`, various variables and device information → `/host_vars`, ssh key files → `/ssh_key_files`, option parameters/parallelism → `/AnsibleExecOption.txt` (Core/AAC) or `/env/cmdline` (Agent), device list connection information → `/hosts` (Core/AAC) or `/inventory/hosts` (Agent), device list connection options → `/host_vars`, interaction file and include order → `/playbook.yml`, execution-environment-related files (Agent only) → `builder_executable_files/`, `runner_executable_files/`.

Main result data files: `result.txt` (Core only), `xxx.pid` (ansible-playbook process ID, Core/Agent), `pioneer.xxx` (Pioneer module process log, all engines), `xxx_private.log` (Pioneer module log, all engines), `error.log`/`exec.log.org`/`exec.log` (all engines), `exec_<work number>_<group number>` (split log, AAC only), `forced.txt` (emergency stop record, Core/Agent), `user_files` (output destination for `__workflowdir__`, all engines), `child_exec.log`/`child_error.log` (ansible-builder execution log, Agent only).
