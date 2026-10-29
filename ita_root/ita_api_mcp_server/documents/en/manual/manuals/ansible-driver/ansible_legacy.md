# Ansible-Legacy Configuration and Usage

Ansible-Legacy is a mode that applies settings to various hosts using Ansible's standard features. Build code is registered as individual YAML files (Playbooks), and work patterns are composed of combinations of them. Suited to configuration work for servers, storage, and network devices.

## Menu Configuration

In addition to the Basic Console (Operation List) and Ansible Common menus, Ansible-Legacy has its own menus: Movement List (manages Movements), Playbook Material Collection (manages Playbook files), Movement-Playbook Association (manages which Playbooks a Movement includes), Auto-Assignment Setting (manages the link between parameter sheet items and Movement variables), Execute Work, Work Management (history management), Work Status Check, Target Hosts (shows the target hosts for each work execution), Assigned Value Management (shows variable values for each work execution), and Movement-Variable Association (hidden menu, for internal processing).

## Work Flow

1. Register connection information in Ansible Common's Device List.
2. Register an operation name in the Basic Console's Operation List.
3. If needed, register AAP host information / Interface Information (execution engine selection and connection information).
4. If needed, register the Execution Environment Definition Template Management, the "Execution Environment Parameter Definition" parameter sheet, and Execution Environment Management.
5. Register a Movement, and register a Playbook.
6. If needed, register global variables, template files, file materials, and unmanaged variables.
7. Link the Playbook to the Movement (Movement-Playbook Association).
8. Create a parameter sheet and register data.
9. Link the parameter sheet items to the Movement's variables in the Auto-Assignment Setting.
10. Execute work → check Work Status (real-time monitoring, emergency stop, log review) → Work Management (history review).

## Movement List

Maintains Movement information (view/register/update/decommission).

| Item | Description | Constraints |
|---|---|---|
| Movement ID | Auto-numbered (36 digits) | - |
| Movement name | Any name | Required, up to 255 bytes |
| Delay timer | If execution is delayed beyond the specified period (1 minute or more), the Work Status Check status is shown as a warning ("Running (delayed)"). No warning if left unset | 0–2147483647 |
| Ansible connection info: host designation format | Select "Host name" when specifying a host that is not expressed by an IP address | Required |
| Ansible connection info: WinRM connection | Set True if the target is Windows Server (selecting this treats all target hosts as Windows Server) | - |
| Ansible connection info: header section | Edits the auto-generated parent Playbook, from the top through just before the tasks section. The default below is applied if left unset. Variables can be written here (e.g. `become_user: '{{△vvv△}}'`), with actual values registered via the Auto-Assignment Setting | Up to 4000 bytes |
| Ansible connection info: option parameters | Options specific to the Movement. If the execution engine is Core/Agent these are ansible-playbook options; if AAC these are job template parameters | Up to 4000 bytes |
| Ansible connection info: ansible.cfg | The ansible.cfg file used at execution time (the default is used if not uploaded) | Up to 100MB |
| Ansible Execution Agent connection info: execution environment | The execution environment name registered in Execution Environment Management. Required if the execution engine is Agent | - |
| Ansible Execution Agent connection info: ansible-builder parameters | Parameters used by ansible-builder when building the execution environment | Up to 4000 bytes |
| Ansible Automation Controller connection info: execution environment | An execution environment built on AAC (selected from AAC sync data). Uses AAC's default execution environment if not selected | - |
| Remarks | Free text | Up to 4000 bytes |

Default header section:
```yaml
- hosts: all
  remote_user: "{{ __loginuser__ }}"
  gather_facts: no
  become: yes
  # become: yes is not applied for a WinRM connection.
```
If `become: yes` is set, the login user on the target host must have sudo permission configured with NOPASSWD in `/etc/sudoers` (e.g. `Demo_user ALL=(ALL) NOPASSWD:ALL`).

## Playbook Material Collection

Maintains user-created Playbooks (view/register/update/decommission). Sample Playbooks (with material names starting with "~[Exastro standard]") are pre-registered, and can be linked to a Movement for use.

| Item | Description | Constraints |
|---|---|---|
| Playbook material name | Any name | Required, up to 255 bytes |
| Playbook material | A Playbook file (no UTF-8 BOM) | Required, up to 100MB |
| Target: Linux/Windows | Select "＊" for supported OSes (leaving this unselected does not affect execution) | - |
| Target: other | Enter uses other than Linux/Windows | Up to 4000 bytes |
| Python required | Select "＊" if Python is required on the target device (leaving this unselected does not affect execution) | - |
| Description / Description (en) / Remarks | Free text | Up to 4000 bytes each |

Because internal extraction of variables inside the Playbook is not real-time, it may take some time before a variable becomes usable in the Auto-Assignment Setting.

## Movement-Playbook Association

Maintains the Playbooks a Movement includes (view/register/update/decommission). Items: Movement (list selection, required), Playbook material (list selection, required), include order (1–2147483647, executed in ascending order, required), and remarks (up to 4000 bytes).

## Auto-Assignment Setting

Manages the link between parameter sheet item values and Movement variables (view/register/update/decommission). Registered information is reflected in "Assigned Value Management" and "Target Hosts" at execution time.

| Item | Description | Required |
|---|---|---|
| Parameter Sheet (From) Menu:Item | An item from a parameter sheet (with host/operation) | 〇 |
| Parameter Sheet (From) Assignment Order | Enter the parameter sheet's assignment order when using a bundle | Required only when using a bundle |
| Registration method | Value type (the item's value becomes the actual value) / Key type (the item's name becomes the actual value) | 〇 |
| Movement name | A registered Movement | 〇 |
| IaC Variable (To) Movement name:Variable name | A variable used in the material linked via Movement-Playbook Association | 〇 |
| IaC Variable (To) Assignment Order | Assignment order (1 or higher) when making this a multi-value variable. Required even if there is only one value | Required for multi-value variables |
| NULL linkage | True (register regardless of value) / False (register only if a value is entered). Uses the Interface Information value if not selected | - |
| Remarks | Free text | Up to 4000 bytes |

The Parameter Sheet (From) Assignment Order is required only when using a parameter sheet (bundle). A variable with no assignment order entered is treated as a normal variable; if entered, it is treated as a multi-value variable (values are packed in order even if the assignment order numbers are not consecutive). Only variables registered in the Auto-Assignment Setting are output to the host variables file at execution time (an unregistered variable, even if used in the Playbook, is not output, which can cause an "undefined variable" error at Ansible execution time).

**Example of a multi-value variable**: registering value1–value4 in parameter sheet items 1–4, and setting an assignment order of item1=30, item2=10, item3=20 for `VAR_substitutionA`, and item1=2, item2=4, item3=1, item4=3 for `VAR_substitutionB` in the Auto-Assignment Setting, results in the host variables file containing `VAR_substitutionA: [value2, value3, value1]` and `VAR_substitutionB: [value3, value1, value4, value2]`, output in ascending order.

**Example of using file-embedded and template-embedded variables**: register `CPF_test` (file material `test_file.txt`) in File Management and `TPF_sample` (template material `sample.tpl`) in Template Management, set these embedded variable names as parameter sheet item values, and link them in the Auto-Assignment Setting to Playbook variables (e.g. `VAR_filetest`, `VAR_temptest`). At execution time, the actual values shown in Assigned Value Management will be reflected as `'{{ CPF_test }}'` and `'{{ TPF_sample }}'`.

## Execute Work

Select the Movement and operation, specify the execution type, and run. Results can be checked in Work Status Check.

- **Execute work**: performs the build work on the target.
- **Dry run**: does not make actual changes; equivalent to ansible-playbook's `--check`.
- **Check parameters**: does not perform build work; reflects the Auto-Assignment Setting information into "Assigned Value Management" and "Target Hosts" for review only.
- **Scheduled date/time**: only a future date/time can be specified, allowing execution to be scheduled.

## Work Status Check

Monitors the execution status of a job. "Execution type" is normal/dry run/check parameters. An error message is shown in the error log for an unexpected error. "Calling Conductor" is set only when run via a Conductor.

When run via AAC, the Playbook is executed in units grouped by the device list's user/password/ssh private key file/passphrase/connection type/instance group values, and logs are split accordingly. Specifying a job slice count via an option parameter in Interface Information or the Movement List further splits each group. Execution logs are shown in tabs: `exec.log` (all logs) and `exec_<group number>_<sequence number>` (split logs; sequence number 0 means unsplit).

Other features: Target Hosts / Assigned Values check buttons, Emergency Stop / Cancel Schedule buttons, log search (string search, showing only matching lines; the refresh interval/max line count follow the Interface Information setting), input data / result data download, and collection status (statuses: Collected / Collected (with notice) / Not applicable / Collection error).

## Work Management / Target Hosts / Assigned Value Management

**Work Management**: lists and filters work history. Items: work number, execution type, status, emergency stop flag, execution engine, calling Conductor, executing user, registration date/time, Movement (ID/name/delay timer/various Ansible connection info/Ansible Execution Agent connection info/AAC connection info), operation (number/name), input data/result data, work status (scheduled/start/end date-time), collection status, and Conductor instance number.

**Target Hosts**: shows the target hosts for each work execution (item number, work number, operation, Movement name, host name, remarks).

**Assigned Value Management**: shows variable values for each work execution. Items: item number, work number, operation, Movement name, host name, Movement name:variable name, value (encrypted and used via ansible-vault if the Sensitive setting is True; otherwise shown as the actual value / file name), assignment order, and remarks.

## Writing Playbooks (Ansible-Legacy)

An uploaded Playbook is executed via an include from the master Playbook that ITA generates. The master Playbook consists of a header section and a tasks section; the uploaded Playbook does not need a header section (it can be changed via the Movement List's header section; the default is as shown above). The tasks section should be written following Ansible's official Playbook format, and is included according to the include order set in Movement-Playbook Association.

## Appendix: Mapping Between Ansible Input Data and ITA Menus

Input data is generated from information across ITA's various menus (device list passwords and variable values with Sensitive set to True are encrypted with ansible-vault). The input data can be downloaded as a ZIP file from Work Status Check, and can also be extracted to run Ansible directly. Main mappings: Playbook material → `/child_playbooks`, template material → `/template_files`, file material → `/copy_files`, values (files) from Assigned Value Management → `/upload_files`, global variables / Assigned Value Management / template- and file-embedded variables / device list information → `/host_vars`, ssh authentication key files → `/ssh_key_files`, WinRM key files → `/winrm_key_files`, server certificates → `/winrm_ca_files`, option parameters → `/AnsibleExecOption.txt` (Core/AAC) or `/env/cmdline` (Agent), device list connection information → `/hosts` (Core/AAC) or `/inventory/hosts` (Agent), Playbook name and include order → `/playbook.yml`, and execution-environment-related files (Agent only) → `builder_executable_files/`, `runner_executable_files/`.

## Appendix: Result Data from Ansible Execution

Execution results are saved as a ZIP file, downloadable from Work Status Check. Main files: `result.txt` (Ansible execution result, Core only), `error.log` (error output, all engines), `exec.log.org`/`exec.log` (raw/processed standard output, all engines), `exec_<work number>_<group number>` (split log, AAC only), `forced.txt` (emergency stop record, Core/Agent), `user_files` (output destination for `__workflowdir__`, all engines), `child_exec.log`/`child_error.log` (ansible-builder execution log, Agent only).
