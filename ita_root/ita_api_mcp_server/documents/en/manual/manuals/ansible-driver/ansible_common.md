# Ansible Driver Common Features (Variable Handling and Menu Configuration)

## Ansible Driver Overview

- **Ansible Core**: A platform build automation tool that makes it easy to perform deployment work against a large number of managed targets. Tasks are written in a Playbook, a YAML-format text file, and executed.
- **Ansible Automation Controller**: A management platform that extends Ansible with access control, job scheduling, and task visualization. A combination of "Project", "Inventory", and "Credential" is used to create a "Job Template", which is executed; multiple job templates can be combined into a "Workflow Job Template".
- **Ansible Automation Platform (Cloud)**: Equivalent to Ansible Automation Controller but supports the Red Hat Ansible Automation Platform (Managed Service) edition. SSH is not required for ITA's material transfer.
- **Ansible Execution Agent**: A dedicated Ansible execution server independent of ITA. It builds an execution environment (container) using ansible-builder, and runs Playbooks through that execution environment using ansible-runner. It is set up per workspace, and multiple agents can be placed in the same workspace for redundancy.
- **Ansible driver**: An ITA feature that automates Playbook processing by choosing whether to go through Ansible Core, Ansible Automation Controller, or Ansible Execution Agent for the target devices. Three modes are provided:
  - **Legacy mode**: Applies settings to each host using Ansible's standard features. Build code is registered as individual YAML files, and work patterns are composed of combinations of those files. Suited to configuration work for servers, storage, and network devices.
  - **Legacy Role mode**: Uses Ansible's standard features like Legacy mode, but build code is registered as packages (Roles), and work patterns are composed of combinations of Roles. Suited to installation and environment setup using Role packages provided by product divisions.
  - **Pioneer mode**: Adds proprietary modules to Ansible and applies settings interactively. Supports devices that can be logged into via Telnet/SSH. Since it communicates directly with the target, a corresponding level of IT skill is required.

## Variable Handling

Values for variables used in Playbooks can be set from ITA. ITA supports the following 7 kinds of variables.

| Variable Type | Description |
|---|---|
| Normal variable | A variable for which a single value can be defined against the variable name. |
| Multi-value variable | A variable for which multiple values can be defined against the variable name. |
| Nested variable | A hierarchical variable. Supported only in Ansible-LegacyRole. |
| Global variable | Registered from "Ansible Common → Global Variable Management". Centrally manages information shared across multiple Playbooks/tasks. Can be used within Template Management, the Playbook material collection, the interaction file material collection, and Role Package Management (example notation: `{{ GBL_user }}`). |
| Global variable (sensitive) | Registered from "Ansible Common → Global Variable (Sensitive) Management". Used the same way as a global variable, but stored encrypted and used via ansible-vault at execution time. Intended for sensitive information such as credentials and API keys. |
| Template-embedded variable | Registered from "Ansible Common → Template Management" (example: `{{ TPF_SAMPLE }}`). |
| File-embedded variable | Registered from "Ansible Common → File Management" (example: `{{ CPF_SAMPLE }}`). |
| ITA proprietary variable | A variable proprietary to ITA (described below). |

### List of ITA Proprietary Variables

| Item Name | Variable Name | Description |
|---|---|---|
| Host name / DNS host name / IP address / protocol / login user ID / login password | `__inventory_hostname__` `__dnshostname__` `__ipaddress__` `__loginprotocol__` `__loginuser__` `__loginpassword__` | Values from the device list. An error occurs if execution is run without these being set. |
| Movement ID | `__movement_id__` | The Movement ID of the Movement selected from the Movement list at execution time. |
| Operation | `__operation__` `__operation_datetime__` `__operation_id__` `__operation_name__` | Values from the operation list. `__operation__` is formatted as "YYYY/MM/DD HH:MM"_"Operation ID":"Operation name". |
| Work instance ID | `__execution_no__` | The work number generated at execution time. |
| Conductor instance ID | `__conductor_id__` | The instance ID at Conductor execution time. Usable only during Conductor execution (an error occurs for standalone Movement execution). |
| Work directory path | `__workflowdir__` | The working directory at execution time. Files created here can be downloaded from the work management result data. |
| Conductor work directory path | `__conductor_workflowdir__` | A directory shared between Movements during Conductor execution (same path as `__workflowdir__` for standalone execution). Cannot be shared between Movements running in parallel via a parallel branch; can only be shared with subsequent Movements that are not in a parallel relationship. |
| Status file path | `__movement_status_filepath__` | The file path referenced by a Status file branch node. |
| Collection feature file paths | `__parameters_dir_for_epc__` `__parameters_file_dir_for_epc__` `__parameter_dir__` `__parameters_file_dir__` | Paths for `_parameters` (parameter storage) / `_parameters_file` (file storage) under the collection feature's working directory (in) / result directory (out). |
| Organization management | `__organization_id__` `__workspace_id__` `__external_url__` | Organization ID, workspace ID, and the service's public endpoint. |

### Materials Subject to Variable Extraction and Their Format

The materials (menus/items) subject to variable extraction are as follows (〇: applicable, ×: not applicable).

| Menu / Item | Legacy | Pioneer | LegacyRole |
|---|---|---|---|
| Playbook material in the Playbook material collection | 〇 | × | × |
| Interaction file material in the interaction file material collection | × | 〇 | × |
| Role package file (ZIP format) in Role Package Management | × | × | 〇 |
| Variable definitions in Template Management | 〇 | 〇 | 〇 |
| Device list's inventory file additional options, Movement list's header section | 〇 | × | 〇 |
| Parameter sheet items that select Template Management | 〇 | 〇 | 〇 |

Notation format (△ denotes a half-width space; vvv/xxx are half-width alphanumerics and underscores within 255/251 bytes):

- Normal variable / multi-value variable: `{{△vvv△}}` or `{{△vvv△|△filter△}}` (treated as a multi-value variable if an assignment order is entered in the auto-assignment setting)
- Global variable: `{{△GBL_xxx△}}`
- Template-embedded variable: `{{△TPF_xxx△}}`
- File-embedded variable: `{{△CPF_xxx△}}`

For Role package files (ZIP format), normal variables, multi-value variables, and nested variables under defaults/tasks/templates/handlers/meta are subject to extraction (in the form `vvv: value`, etc.; the value can be omitted). Member variable names of nested variables can use any ASCII character (0x20–0x7e) except the 7 characters `. [ ] ' \ :`. In the device list's inventory file additional options and the Movement list's header section, Legacy supports normal and multi-value variables, while LegacyRole additionally supports nested variables (treated according to the type defined in the Role package or the Template Management variable definitions, or as a normal variable if undefined). Global variables, file-embedded variables, and template-embedded variables cannot be used here.

### Variable Value Registration Flow (Common)

The flow is the same for Ansible-Legacy, Ansible-Pioneer, and Ansible-LegacyRole.

1. Variables are extracted from the materials subject to extraction, becoming selectable in each mode's "Auto-Assignment Setting".
2. Values are registered in the parameter sheet items.
3. The link between the parameter sheet item and the variable is registered in "Auto-Assignment Setting".
4. At execution time, the linked information is reflected in "Assigned Value Management" and output to the host variables file.

For LegacyRole, the values registered via the auto-assignment setting are output to the host variable definition file (host_vars), and the priority Ansible uses for variable values is "value in the host variable definition file" > "value in the defaults variable definition file".

## Ansible Common Menu Configuration

List of Ansible Common menus: Device List (manages information on target devices), Interface Information (selects the execution engine and manages connection information), Ansible Automation Controller Host List (manages information for REST API execution and material transfer), Global Variable Management / Global Variable (Sensitive) Management (manages commonly used variables), File Management / Template Management (manages commonly used material files/templates and their embedded variables), Execution Environment Definition Template Management / Execution Environment Management (manages the link between execution environment definition file templates within the Ansible Execution Agent and parameter sheets), Agent Management (view names/versions of connected agents), Unmanaged Variable List (manages variables to be excluded from display in the auto-assignment setting), Common Variable Usage List (hidden menu; view which materials use each variable), and Ansible Automation Platform (Cloud) Integration Materials (hidden menu; for internal processing when using the AAP Cloud execution engine). Hidden menus need to be re-enabled via "Management Console → Role/Menu Association Management".

## Device List

Maintains information about target devices (view/register/update/decommission). A local execution device named "localhost" is registered at installation time (not usable with Pioneer).

Main items: Management system number (auto-numbered), hardware device type (NW/ST/SV), host name (required, used as the Ansible inventory host, up to 255 bytes), DNS host name, IP address (IPv4 format), login user/password, SSH key authentication information (private key file and passphrase; cannot be downloaded after registration).

**Ansible connection information (Legacy/Role connection information) authentication methods**: Password authentication (password required), key authentication (with or without passphrase, private key file required), password authentication (WinRM), certificate authentication (WinRM) (public/private key files required). WinRM connection information also includes a port number (default 5985 if not entered) and WinRM public/private key files.

**Pioneer connection information**: Protocol (ssh: any method other than password authentication (WinRM) / telnet: connects with user/password without using an authentication method), OS type (registered from Ansible-Pioneer → OS Type), LANG (defaults to utf-8 if not selected).

**Connection options**: Options used for ssh/telnet connections (up to 4000 bytes). **Inventory file additional options**: YAML-format parameters to add to the inventory file created by ITA (not applicable for Ansible-Pioneer). Values can be written as variables (`{{△vvv△}}`), with actual values registered via the auto-assignment setting. **Ansible Automation Controller connection information**: Instance group name (in a cluster configuration; the default instance group is used if not selected), connection type (normally "machine"; for Network OS devices that require `ansible_connection: local`, select "Network", which also requires Platform Options settings in the inventory file additional options).

## Interface Information

Selects the execution engine (Ansible Core / Ansible Automation Controller / Ansible Execution Agent / Ansible Automation Platform (Cloud)) and maintains connection information (view/update).

Main items: Execution engine (required). Ansible Automation Controller interface (required when the execution engine is AAC): representative host (for AAP 2.4, select AAC from the AAP node list; for 2.5/Cloud, select Platform Gateway from the node list), protocol (http/https), port (usually https:443), organization name (selected from AAC sync data), authentication token (up to 255 bytes), REST API timeout value (60–3600 seconds, defaults to 60 seconds if not entered). Proxy address/port (if required for connectivity in a proxy environment). Delete runtime data (True/False; required when the execution engine is AAC or Agent; when True, temporary data resources are deleted after the work completes). Ansible-vault password (up to 64 bytes, uses the default value if not entered). Option parameters (options common to Movements, up to 4000 bytes; if the execution engine is Core/Agent these are ansible-playbook command options, and if AAC these are job template parameters). NULL linkage (True/False; whether to register NULL in Assigned Value Management when the parameter sheet value is NULL; applied when not selected in each Movement's auto-assignment setting; defaults to False if not selected). Status monitoring interval (1000–2147483647 milliseconds, recommended 1000ms). Progress display line count (0–2147483647, recommended 1000 lines; for not-yet-executed/preparing/ready/waiting/running/running (delayed) statuses only the specified number of lines is shown, while completed statuses output the full log). If the execution engine is AAP (Cloud), no input other than the host is required.

## Ansible Automation Platform Node List

Maintains information needed for REST API execution to AAP and for build-material transfer (view/register/update/decommission). In a cluster configuration, register all nodes (a hop node is not required). For AAP 2.5, register the Platform Gateway and Execution Nodes (including Hybrid Nodes); Controller Nodes and Hop Nodes are not required.

Main items: Host (host name/IP of the Controller/Execution/Hybrid Node or Platform Gateway, up to 255 bytes, required), authentication method (for scp connections to Execution/Hybrid Nodes: password authentication or key authentication (with/without passphrase); not used for the Platform Gateway), user/password (the awx user is recommended), SSH key authentication information, port (default 22), Execution node (True/False; for AAP 2.4 in a cluster configuration set True if it is an execution node; for AAP 2.5/Cloud set False for the Platform Gateway and True for Execution/Hybrid Nodes).

## Global Variable Management / Global Variable (Sensitive) Management

Maintains global variables shared across Playbooks and interaction files (view/register/update/decommission). Items: global variable name (format `GBL_****`, half-width alphanumerics and underscores, 1–255 bytes, required), value (up to 4000 bytes; multi-line is allowed, but using a multi-line value in a Pioneer interaction file causes an execution error), variable description, and remarks. In Sensitive management, values are stored encrypted and used via ansible-vault at execution time (the current value cannot be viewed when updating). **A global variable name must be unique across both regular and sensitive management — the same name cannot be registered in both.**

## File Management / Template Management

**File Management**: Maintains commonly used file materials and file-embedded variables (view/register/update/decommission). Items: file-embedded variable name (format `CPF_****`, 1–255 bytes, required), file material (upload, up to 100MB, required), and remarks. In a Playbook, write it as `- copy: src='{{ CPF_hosts }}' dest=/etc/hosts` (if the destination does not include a file name, the registered file name is prefixed with the ITA management number).

**Template Management**: Manages commonly used template file materials and template-embedded variables. Items: template-embedded variable name (format `TPF_****`, 1–255 bytes, required), template material (text format, up to 100MB, required), variable definitions (defines variables used within the template; 5 types: normal variable, multi-value variable, nested variable (LegacyRole only), global variable, and ITA proprietary variable (no definition needed); if the same variable name is also defined in a defaults variable definition file, the variable structures must match, otherwise registration fails), and remarks. Because internal variable extraction is not real-time, it may take some time before a variable becomes usable in the auto-assignment setting. In a Playbook, write it as `- template: src='{{ TPF_hosts }}' dest=/etc/hosts`.

If an "Authentication failed." error occurs when registering a large file, it is usually because the access token expired due to network conditions; check and adjust the access token validity period setting.

## Execution Environment Definition Template Management / Execution Environment Management

**Execution Environment Definition Template Management**: Maintains templates for the definition file (execution-environment.yml) used by ansible-builder when building the execution environment (container) inside the Ansible Execution Agent (templates for adding Python modules/Ansible Galaxy collections are pre-registered at installation). Items: template name (up to 255 bytes, required), template file (Jinja2 template format, up to 100MB, required), and remarks.

**Execution Environment Management**: Manages the link between registered template files and the "Execution Environment Parameter Definition" parameter sheet (a basic parameter sheet and its link are pre-registered at installation). Items: execution environment name (up to 255 bytes, required), execution environment build method ("ITA" = built with ansible-builder, requiring an execution environment definition name and template name / "Manual" = not built by ITA; a container image built outside ITA must be pre-loaded onto the Agent), tag name (the image name; for "ITA" it becomes `{{organization_id}}_{{workspace_id}}_tag name`, and for "Manual" the tag name itself is the image name, up to 255 bytes, required), execution environment definition name (selected from the "Execution Environment Parameter Definition" parameter sheet), template name (selected from Execution Environment Definition Template Management), and remarks.

## Agent Management

Views the name and version of connected Ansible Execution Agents. Status values: "Normal (latest)" (versions match), "Normal (update available)" (versions differ but are compatible; update recommended), "Cannot connect (update required)" (versions differ and are incompatible; update required).

## Unmanaged Variable List

Maintains (view/update/decommission/restore) variables extracted from the materials subject to variable extraction that should be excluded from the "Movement name: variable name" display in each mode's auto-assignment setting (Ansible magic variables are pre-registered at installation). Items: variable name (regular expressions allowed, e.g. `ansible_*`, `ansible_[0-9a-zA-Z]*`, up to 255 bytes, required) and remarks.

## Ansible Automation Platform (Cloud) Integration Materials

An internal-processing menu used when executing work via the AAP (Cloud) method, handling automatic registration and management of resources (updated automatically by internal processing, so manual editing is not recommended; hidden by default — enable it via Role/Menu Association Management if needed).

API endpoints: `GET /api/{organization_id}/workspaces/{workspace_id}/aap/{execution_no}/populated_data` (retrieves ITA-proprietary materials), `POST /api/{organization_id}/workspaces/{workspace_id}/aap/{execution_no}/result_data` (sends result files). Access requires the same permissions as the execution agent.

**Operation flow**: ① ITA instructs the AAP Platform Gateway via REST API to create resources and run the job → ② the Playbook on the AAP Execution Node (localhost on the EE) sends a GET to the ITA API to fetch and extract the input data (zip) → ③ the Playbook runs on the Execution Node → ④ after execution completes, the Execution Node (localhost on the EE) sends a POST to the ITA API with the result data (zip) → ⑤ results are checked in ITA. Unlike the traditional SSH/SCP method, this is pull-type communication from AAP to ITA, using a service account for the API.

## Appendix: Execution Environment Definition Templates and the "Execution Environment Parameter Definition" Parameter Sheet

The template file is in Jinja2 format and follows the execution-environment.yml specification used by ansible-builder. Items in the "Execution Environment Parameter Definition" parameter sheet: execution_environment_name (record name, required, up to 255 bytes), python_requirements_file (additional pip install targets; cannot be empty, required), galaxy_requirements_file (Ansible Galaxy collections; cannot be empty), bindep_file (additional dnf install targets; cannot be empty, required), ansible_runner (enter "ansible_runner", required), image (base image, required), and package_manager_path (package manager command path, required).

Notes for creating/updating: the parameter sheet name (rest) must start with "execution_environment_parameter_definition_sheet"; the creation target must be a data sheet; the item list must include the Rest API item name `execution_environment_name` (single-line string, up to 255 bytes); and items with the same name as variables in the template file must be prepared (item name = variable name, set value = variable value embedded in the template). If changing Python to python3.11 for local execution, the `ansible_python_interpreter` in the localhost entry's "inventory file additional options" in the device list must also be updated to `/usr/bin/python3.11`.

## Appendix: BackYard Content (AAC Data Sync)

When the execution engine is AAC, the following is retrieved from AAC: organization names (for the organization name list in Interface Information; organizations available to the authentication token's user), instance groups (for the instance group list in the device list; those available to the selected organization), and execution environments (for the execution environment list in the Movement list; those available to the selected organization).

## Appendix: Inventory File Created by ITA

```yaml
all:
  children:
    hostgroups:
      hosts:
        Inventory_host:
          Inventory_host_parameters:
          Inventory_host_option_parameters:
```

`Inventory_host` is the host name from the device list, and `Inventory_host_option_parameters` is the inventory file additional options. `Inventory_host_parameters` is set depending on the authentication method (unset items are not set): `ansible_host` (all authentication methods, DNS host/IP address), `ansible_user` (all except certificate authentication (WinRM)), `ansible_password` (password authentication / password authentication (WinRM)), `ansible_ssh_private_key_file` (all key authentication variants), `ansible_ssh_extra_args` (password authentication and all key authentication variants), `ansible_connection: winrm` (WinRM variants), `ansible_port` / `ansible_winrm_cert_pem` / `ansible_winrm_cert_key_pem` (WinRM variants).

## Appendix: List of Option Parameters

For the option parameters in Interface Information and the Movement list, if a single-value parameter is defined in both, the Movement list setting takes precedence. When the execution engine is Core/Execution Agent, these are ansible-playbook command options (see `ansible-playbook -h` for help). For AAC, the main supported options are: `-v/--verbose` (verbosity level; the sum of the v's is applied, treated as 5 if 6 or higher), `-f/--forks` (number of forks; if specified multiple times, the last value takes effect), `-l/--limit` (target host name; the last value takes effect), `-e/--extra-vars` (extra variables, json/yaml format; the last value takes effect), `-t/--tags` (job tags, can be specified multiple times), `-b/--become` (enables privilege escalation), `-D/--diff` (shows change diffs), `--skip-tags` (tags to skip, can be specified multiple times), `--start-at-task` (not shown in the AAC Web UI), `-ufc/--use_fact_cache` (enables fact caching), `-as/--allow_simultaneous` (enables simultaneous job execution), `-jsc/--job_slice_count` (job slice count). See the AAC official manual's job template documentation for details.

## Appendix: Data Resources Deleted by "Delete Runtime Data"

Resources deleted when "Delete runtime data" is set to true. **On the AAC side**: the ITA working directory (`/var/lib/exastro/ita_<category>_executions_<work number>`), the SCM management directory (deleted along with removal of the project resource), and the inventory, credential, project, job template, workflow job template, and job resources (named with the pattern `ita_<category>_executions_*_<work number>`). `<category>` is legacy / legacy_role / pioneer. **On the ITA side**: the Git repository (`/tmp/git_repositories/<category>_<work number>`, always deleted regardless of the setting). **On the Ansible Execution Agent side**: the ITA working directory (`<storage>/<org>/<ws>/driver/ag_ansible_execution/<category>/<work number>`, `<storage>/<org>/<ws>/ag_ansible_execution/status`).

## Appendix: Notes on Using ITA Proprietary Variables with Ansible Automation Controller

Notes for running a Movement that includes a Playbook that outputs files using `__workflowdir__`, `__conductor_workflowdir__`, `__movement_status_filepath__`, `__parameters_dir_for_epc__`, `__parameters_file_dir_for_epc__`, `__parameter_dir__`, or `__parameters_file_dir__`, when running on a clustered AAC.

The output directory is configured under `/var/lib/exastro`, within AAC's ITA working directory. Before a Movement runs, files under the Conductor/Movement are transferred to that directory on each execution node, and after execution, files created there are transferred (in overwrite mode) to the result data (or the Conductor shared area). If a file with the same name is created, the updated file may not be reflected correctly.

**Notes**: ① Include Ansible's `inventory_hostname` (or similar) in the file name so that the same file name is not used for output across different target hosts. ② When running from a Conductor, avoid outputting to the same file name from multiple Movements.
