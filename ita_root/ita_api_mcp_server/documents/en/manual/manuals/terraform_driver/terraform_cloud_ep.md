# Terraform Cloud/EP Driver Configuration and Usage

The Terraform Cloud/EP driver creates Organizations/Workspaces, executes work (Plan/PolicyCheck/Apply), and retrieves work logs against a Terraform Cloud or Terraform Enterprise instance registered in ITA. For concepts common to Terraform and the Terraform driver (such as variable handling), see "Terraform Driver Common."

## Menu Structure

Basic Console:

| No | Menu Group | Menu/Screen | Description |
|---|---|---|---|
| 1 | Basic Console | Operation List | Maintain (view/register/update/decommission) the operation list. |

Terraform Cloud/EP:

| No | Menu/Screen | Description |
|---|---|---|
| 1 | Interface Information | Manages the Terraform information that ITA integrates with. |
| 2 | Organization Management | Manages Organization information used by Terraform. |
| 3 | Workspace Management | Manages Workspace information used by Terraform. |
| 4 | Movement List | Manages the list of Movements. |
| 5 | Module Materials | Manages Module files. |
| 6 | Policy Management | Manages Policy files. |
| 7 | Policy Set Management | A Policy Set is linked to Policies and Workspaces, enabling the Policy to be enforced on the target Workspace during work execution. |
| 8 | Policy Set-Policy Linkage | Manages the linkage between Policy Sets and Policies. |
| 9 | Policy Set-Workspace Linkage | Manages the linkage between Policy Sets and Workspaces. |
| 10 | Movement-Module Linkage | Manages the association between a Movement and Module materials. |
| 11 | Variable Nesting Management | When a variable's type is list/set and contains a nested list/set/tuple/object, manages the maximum repeat count of the member variables. |
| 12 | Auto Value-Assignment Settings | Links parameter sheet fields/values to Movement variables. |
| 13 | Work Execution | Select the Movement and operation to execute and instruct execution. |
| 14 | Work Management | Manages work execution history. |
| 15 | Work Status Check | Displays the work execution status. |
| 16 | Assigned Value Management | Manages the assigned concrete values of variables. |
| 17 | Linked Terraform Management | Displays and deletes the list of Organizations, Workspaces, Policies, and Policy Sets registered on the linked Terraform. |
| 18-21 | Module-Variable Linkage / Member Variable Management / Movement-Variable Linkage / Movement-Member Variable Linkage (hidden menus) | Menus used internally to register/update data. To display them, restore access via "Management Console → Role-Menu Linkage Management." |

## Work Flow

1. Register the target operation name in the Basic Console's Operation List.
2. Configure Interface Information (Hostname, User Token, etc. of the linked Terraform).
3. Register an Organization and link it with Terraform.
4. Register a Workspace and link it with Terraform.
5. Register a Movement.
6. Register Module materials.
7. If needed, register Policy / Policy Set / Policy Set-Policy Linkage / Policy Set-Workspace Linkage.
8. Link Module materials to the Movement.
9. If needed, set the maximum repeat count in Variable Nesting Management.
10. If needed, create a parameter sheet, register data, and link it to the Movement's variables in Auto Value-Assignment Settings.
11. Select the Movement and target operation on the Work Execution screen and execute.
12. Monitor the status and logs in real time on Work Status Check.
13. Check the history in Work Management.

## Applying Policies

To use the Policy feature, the linked Terraform must be Terraform Enterprise, or Terraform Cloud on a plan with the "Policy & Security" feature enabled. Application procedure:

1. Link a registered Policy and Policy Set via "Policy Set-Policy Linkage."
2. Link a registered Workspace and Policy Set via "Policy Set-Workspace Linkage."
3. During work execution, the Policy Set—and the Policies linked to it—linked to the Movement's Workspace is applied.

## Interface Information

Maintain (view/update) the Terraform information that ITA integrates with. The target Hostname and a User Token issued by a Terraform user are required. If this is unregistered, or if multiple records are registered, an unexpected error occurs during work execution.

| Field | Description | Constraints |
|---|---|---|
| Linked Terraform Protocol | http/https (normally https) | Required |
| Linked Terraform Hostname | Hostname of the linked Terraform | Required, max 256 bytes |
| Linked Terraform Port | Normally left blank | Min 1, max 65535 |
| Linked Terraform User Token | Issued from Terraform's User Settings | Max 1024 bytes |
| Proxy Address / Port | Set if needed for connectivity to Terraform when ITA is behind a proxy | - |
| NULL Linkage | How to register into Assigned Value Management when the parameter sheet's concrete value is NULL in Auto Value-Assignment Settings. Applied when "NULL Linkage" in the Auto Value-Assignment Settings menu is blank. | Required |
| Status Monitoring Interval (ms) | The refresh interval for logs on Work Status Check. Recommended around 1000 ms. | Min 1000 ms, required |
| Progress Display Digit Count | Maximum number of lines shown for progress/error logs (applies while status is Not Executed/Preparing/Executing/Executing (Delayed); full logs are output for completed statuses). Recommended around 1000 lines. | Required |
| Remarks | Free text | Max 4000 bytes |

## Organization Management

Maintain (view/register/update/decommission) Terraform Organizations, and link (register/update/delete) Organizations registered in ITA to Terraform. The "Status Check" button checks the linkage status, and the "Register," "Update," and "Delete" buttons in the "Terraform Linkage" column group perform each operation. Executing work while an Organization is not linked (registered) results in an unexpected error. An incorrect Hostname/User Token displays "Failed to connect to Terraform. Please check the Interface Information." Deletion cannot be undone, and any Workspaces under it are also deleted.

| Field | Description | Constraints |
|---|---|---|
| Organization Name | Alphanumeric characters and `_-` only | Required, max 40 bytes |
| Email Address | The Organization's email address | Required, max 128 bytes |
| Remarks | Free text | Max 4000 bytes |

## Workspace Management

Maintain (view/register/update/decommission) Terraform Workspaces, link (register/update/delete) Workspaces registered in ITA to Terraform, and execute resource deletion (terraform destroy). The "Delete Resources" button navigates to Work Status Check where it is executed. If a Workspace is deleted, resource deletion can no longer be executed, and the deletion cannot be undone.

| Field | Description | Constraints |
|---|---|---|
| Organization Name | Select a registered Organization name | Required, max 40 bytes |
| Project Name | If blank, linked to "Default Project" | Max 40 bytes |
| Workspace Name | Alphanumeric characters and `_-` only | Required, max 90 bytes |
| Terraform Version | If blank, the latest version is automatically applied at link (registration) time | Required, max 128 bytes |
| Remarks | Free text | Max 4000 bytes |

## Movement List

Maintain (view/register/update/decommission) Movement names. Since a Movement must be linked to an Organization:Workspace, the Organization and Workspace must be registered first.

| Field | Description | Constraints |
|---|---|---|
| Movement Name | Arbitrary name | Required, max 256 bytes |
| Orchestrator | Auto-filled with "Terraform Cloud/EP" | - |
| Delay Timer | Displays a warning if delayed beyond the specified period (1 minute or more). No warning if left blank. | Unit: minutes |
| Terraform Usage Info (Organization:Workspace) | Select a registered Workspace (linked to an Organization) | Required |
| Remarks | Free text | Max 4000 bytes |

## Module Materials

Maintain (view/register/update/decommission) Modules created by the user.

| Field | Description | Constraints |
|---|---|---|
| Module Material Name | Arbitrary name | Required, max 255 bytes |
| Module Material | Upload the Module material file | Required, max 100MB |
| Remarks | Free text | Max 4000 bytes |

Variables within the Module file are extracted internally, but since this is not real-time, it may take some time before the variables become available in Auto Value-Assignment Settings.

## Policy Management

Maintain (view/register/update/decommission) Policy files written in Sentinel language.

| Field | Description | Constraints |
|---|---|---|
| Policy Name | Alphanumeric characters and `_-` only | Required, max 255 bytes |
| Policy Material | Upload the Policy file | Required, max 100MB |
| Remarks | Free text | Max 4000 bytes |

## Policy Set Management

Maintain (view/register/update/decommission) Policy Sets. By linking a Policy Set to Policies and Workspaces via Policy Set-Policy Linkage and Policy Set-Workspace Linkage, the Policy is applied to the Workspace during work execution.

| Field | Description | Constraints |
|---|---|---|
| Policy Set Name | Alphanumeric characters and `_-` only | Required, max 255 bytes |
| Remarks | Free text | Max 4000 bytes |

## Policy Set-Policy Linkage / Policy Set-Workspace Linkage

Maintain (view/register/update/decommission) the linkage between a registered Policy Set and a Policy, or between a Policy Set and a Workspace. The fields are "Policy Set Name," "Policy Name (or Workspace Name)," and "Remarks" (all selected from a list; required).

## Movement-Module Linkage

Maintain (view/register/update/decommission) the linkage between a registered Movement and Module materials. The linked Module materials are applied when the Movement is executed, and multiple Module materials can be linked to a single Movement.

## Variable Nesting Management

When a variable type defined in a .tf file in Module Materials is list/set and contains a nested list/set/tuple/object, view and update the maximum repeat count of the member variables (registration, decommissioning, and restoration are not available since these records are managed internally).

| Field | Description | Constraints |
|---|---|---|
| Variable Name / Member Variable Name (repeating) | The variable used in the Module material (not editable). Member variable names are shown with each level joined by "." | - |
| Maximum Repeat Count | The initial value is taken from the `default` value in the .tf file (1 if not specified). If the last updater was something other than the "Terraform Cloud/EP variable update function," the value is not changed by a Module material update. The upper limit can be changed within the range 1-1024 via the Management Console identification ID "MAXIMUM_ITERATION_TERRAFORM-CLOUD-EP." | Required, 1-1024 (varies by configuration) |
| Remarks | Free text | Max 4000 bytes |

Since initial registration and repeat-count updates are also not real-time, it may take some time before the variables become available in Auto Value-Assignment Settings.

## Auto Value-Assignment Settings

Links a parameter sheet (with operation) to a Movement's variables. The registered information is reflected in Assigned Value Management at work execution time.

| Field | Description | Required |
|---|---|---|
| Parameter Sheet (From) Menu:Field | Select a field of the parameter sheet (with operation) | Yes |
| Parameter Sheet (From) Assignment Order | When bundling is enabled, enter the parameter sheet's assignment order | Only when bundling is enabled |
| Registration Method | Value type (uses the set value as the concrete value) / Key type (uses the field name as the concrete value) | Yes |
| Movement Name | A registered Movement | Yes |
| IaC Variable (To) Movement Name:Variable Name | Select the variable to link | Yes |
| IaC Variable (To) HCL Setting | True/False. If True, the input value can be set 1:1 regardless of variable type (member variables and assignment order cannot be entered). map type can only be registered with this set to True. If the operation, Movement, and variable name match another record, the HCL Setting value must be consistent. | Yes |
| IaC Variable (To) Movement Name:Variable Name:Member Variable | Select the member variable (required for object/tuple types when HCL Setting is False) | Conditionally required |
| IaC Variable (To) Assignment Order | The assignment order (1 or higher) when setting multiple concrete values for a list/set type | Conditionally required |
| NULL Linkage | If left blank, the Interface Information setting is applied | - |
| Remarks | Free text | Max 4000 bytes |

When setting a member variable, the concrete values of all other member variables within the same variable must also be set (default values are not used for unset ones).

## Work Execution

Select the Movement and operation, then use the "Execute" button to navigate to Work Status Check where execution occurs.

- **Scheduled Date/Time**: Specifying a future date/time allows scheduling execution or plan confirmation.
- **Execute**: Terraform Apply runs automatically after Terraform Plan completes.
- **Plan Confirmation**: Runs only Terraform Plan; Apply is not executed.
- **Parameter Confirmation**: Only checks the input parameter values (neither Plan nor Apply is executed).

If a Module material containing an Output block is executed from a Conductor, the output is saved to `[Conductor work directory path]/[Conductor instance ID]/terraform_output_[work no.].json` and can be referenced by other Movements in the same Conductor.

## Work Status Check

Monitors the work execution status. "Execution Type" is one of Plan Confirmation / Delete Resources / Normal. For an unexpected error, if it is caused by an issue such as incomplete Interface Information or Organization/Workspace linkage (registration), it is shown in the error log; otherwise, check the application log. "Calling Conductor" is set only when executed via a Conductor. The "RUN-ID" under "Terraform Usage Info" is the execution management ID on the Terraform side (for Delete Resources, the calling Conductor, Movement, operation, and input data are not set).

- Execution log types: plan.log (Terraform Plan), policyCheck.log (Policy Check), apply.log (Terraform Apply)
- Logs can be filtered. The display interval and maximum line count follow the Interface Information settings.
- "Input Data" allows downloading the Module material, Policy material, and `variables.json` (variable name/concrete value/HCL setting/Sensitive setting—if Sensitive is ON, the concrete value is null) as a zip file.
- "Result Data" allows downloading plan.log/policyCheck.log/apply.log/error.log and the encrypted `sv-XXXXXX.tfstate` (filename differs per execution) as a zip file.
- The "Emergency Stop" button stops execution; before a scheduled execution runs, the "Cancel Reservation" button can cancel it.

## Work Management

Displays a filterable list of work execution history. Fields: Work No. (36-digit auto-numbered), Execution Type (Normal/Plan Confirmation/Parameter Sheet Confirmation), Status (Not Executed/Not Executed (Scheduled)/Preparing/Executing/Executing (Delayed)/Completed/Completed (Abnormal)/Unexpected Error/Emergency Stopped/Reservation Cancelled), Executing User, Registration Date/Time, Movement (ID/Name/Delay Timer/Workspace ID and Organization:Workspace Name and RUN-ID from Terraform Usage Info), Operation (No./Name), Input Data and Result Data (zip download), Work Status (Scheduled Date/Time/Start Date/Time/End Date/Time), and Remarks.

## Assigned Value Management

View the concrete values of variables used by the Module materials of the Movement linked to an operation. Fields: Work No., Operation, Movement Name, Movement Name:Variable Name, HCL Setting (True if the HCL Setting is enabled for the corresponding Variable on the linked Terraform), Movement Name:Variable Name:Member Variable, Assignment Order, Concrete Value (Sensitive Setting True/False—True if the Sensitive Setting is enabled for the corresponding Variable on the linked Terraform—and the value itself), and Remarks.

## Linked Terraform Management

Connects to Terraform based on the Interface Information settings and displays the list of Organizations/Workspaces/Policies/Policy Sets registered on Terraform. From this list, targets registered in ITA can be deleted from Terraform, and resource deletion per Workspace, as well as unlinking Workspaces/Policies from a Policy Set, are also possible. Operations here do not affect the corresponding registrations on the ITA side.

The "ITA Registration Status" column in each list shows "Registered" or "Unregistered," indicating whether the item is registered in the corresponding ITA menu (Organization Management / Workspace Management / Policy Management / Policy Set Management and its linkage menus). The "Delete" operation cannot be undone, and "Delete Resources" for a Workspace also cannot be undone.
