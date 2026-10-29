# Terraform CLI Driver Configuration and Usage

The Terraform CLI driver executes work (Plan/Apply) and retrieves execution logs against a Terraform installation on the same host as ITA. For concepts common to Terraform and the Terraform driver, see "Terraform Driver Common."

## Menu Structure

Basic Console:

| No | Menu Group | Menu/Screen | Description |
|---|---|---|---|
| 1 | Basic Console | Operation List | Maintain (view/register/update/decommission) the operation list. |

Terraform CLI:

| No | Menu/Screen | Description |
|---|---|---|
| 1 | Interface Information | Manages information for work execution. |
| 2 | Workspace Management | Manages Terraform Workspace information. |
| 3 | Movement List | Manages the list of Movements. |
| 4 | Module Materials | Manages Module files. |
| 5 | Movement-Module Linkage | Manages the association between a Movement and Module materials. |
| 6 | Variable Nesting Management | When a variable's type is list/set and contains a nested list/set/tuple/object, manages the maximum repeat count of the member variables. |
| 7 | Auto Value-Assignment Settings | Links parameter sheet fields/values to Movement variables. |
| 8 | Work Execution | Select the Movement and operation to execute and instruct execution. |
| 9 | Work Management | Manages work execution history. |
| 10 | Work Status Check | Displays the work execution status. |
| 11 | Assigned Value Management | Manages the assigned concrete values of variables. |
| 12-15 | Module-Variable Linkage / Member Variable Management / Movement-Variable Linkage / Movement-Member Variable Linkage (hidden menus) | Menus used internally to register/update data. To display them, restore access via "Management Console → Role-Menu Linkage Management." |

## Work Flow

1. Register the target operation name in the Basic Console's Operation List.
2. Register Interface Information.
3. Register a Workspace.
4. Register a Movement (must be linked to a Workspace).
5. Register Module materials.
6. Link Module materials to the Movement.
7. If needed, set the maximum repeat count for member variables in Variable Nesting Management.
8. Create a parameter sheet and register data.
9. Link the parameter sheet's values to the Movement's variables in Auto Value-Assignment Settings.
10. Select the Movement and target operation on the Work Execution screen and execute.
11. Monitor the status and logs in real time on Work Status Check.
12. Check the history in Work Management.

## Interface Information

Maintain (view/update) information for work execution. If this is unregistered, or if multiple records are registered, an unexpected error occurs during work execution.

| Field | Description | Constraints |
|---|---|---|
| NULL Linkage | Applied when "NULL Linkage" in Auto Value-Assignment Settings is blank. If "Enabled," the parameter sheet value is registered regardless of its content; if "Disabled," it is registered only when a value is present. | Required |
| Status Monitoring Interval (ms) | The refresh interval for logs on Work Status Check. Recommended around 3000 ms. | Min 1000 ms |
| Progress Display Line Count | Maximum number of lines shown for progress/error logs (applies while status is Not Executed/Preparing/Executing/Executing (Delayed); full logs are output for completed statuses). Recommended around 1000 lines. | - |
| Remarks | Free text | Max 4000 bytes |

## Workspace Management

Maintain (view/register/update/decommission/delete resources) the Workspace used as the directory in which Terraform commands are run. Work executed against the same Workspace has its state file managed per Workspace, preserving idempotency. The "Delete Resources" button navigates to Work Status Check and runs `terraform destroy` for the target Workspace.

| Field | Description | Constraints |
|---|---|---|
| Workspace Name | Alphanumeric characters and `_-` only | Max 90 bytes |
| Remarks | Free text | Max 4000 bytes |

## Movement List

Maintain (view/register/update/decommission) Movement names. Since a Movement must be linked to a Workspace, the Workspace must be registered first.

| Field | Description | Constraints |
|---|---|---|
| Movement Name | Arbitrary name | Max 256 bytes |
| Orchestrator | Auto-filled with "Terraform CLI" | - |
| Delay Timer | Displays a warning if the Movement is delayed beyond the specified period (1 minute or more). No warning if left blank. | Unit: minutes |
| Terraform Usage Info (Workspace) | Select a registered Workspace | Required |
| Remarks | Free text | Max 4000 bytes |

## Module Materials

Maintain (view/register/update/decommission) Modules created by the user.

| Field | Description | Constraints |
|---|---|---|
| Module Material Name | Arbitrary name | Max 255 bytes |
| Module Material | Upload the created Module material (.tf file) | Max 100MB |
| Remarks | Free text | Max 4000 bytes |

Variables within the Module file are extracted internally, but since this extraction is not real-time, it may take some time before the variables become available in Auto Value-Assignment Settings.

## Movement-Module Linkage

Maintain (view/register/update/decommission) the linkage between a registered Movement and Module materials. The linked Module materials are applied when the Movement is executed, and multiple Module materials can be linked to a single Movement.

## Variable Nesting Management

When a variable type defined in a .tf file in Module Materials is list/set and contains a nested list/set/tuple/object, view and update the maximum repeat count of the member variables (this menu cannot register, decommission, or restore records, since they are managed internally).

| Field | Description | Constraints |
|---|---|---|
| Variable Name | The variable used in the Module material (not editable) | - |
| Member Variable Name (repeating) | Displays the variable at each level joined by "." (not editable) | - |
| Maximum Repeat Count | The maximum repeat count of the array. The initial value is taken from the `default` value in the .tf file (1 if not specified). If the last updater was something other than the "Terraform CLI variable update function," the value is not changed by a Module material update. The upper limit can be changed within the range 1-1024 via the Management Console identification ID "MAXIMUM_ITERATION_TERRAFORM-CLI." | 1-1024 (varies by configuration) |
| Remarks | Free text | Max 4000 bytes |

Since initial registration and repeat-count updates are also not real-time, it may take some time before the variables become available in Auto Value-Assignment Settings.

## Auto Value-Assignment Settings

Links a parameter sheet (with operation) created by the parameter sheet creation feature to a Movement's variables. The registered information is reflected in Assigned Value Management at work execution time.

| Field | Description | Required |
|---|---|---|
| Parameter Sheet (From) Menu:Field | Select a field of the parameter sheet (with operation) | Yes |
| Parameter Sheet (From) Assignment Order | When bundling is enabled, enter the parameter sheet's assignment order | Only when bundling is enabled |
| Registration Method | Value type (uses the field's set value as the concrete value) / Key type (uses the field's name as the concrete value) | Yes |
| Movement Name | A registered Movement | Yes |
| IaC Variable (To) Movement Name:Variable Name | Select the variable to link | Yes |
| IaC Variable (To) HCL Setting | True/False. If True, the input value can be set 1:1 regardless of variable type (in this case, member variables and assignment order cannot be entered). map type can only be registered with this set to True. If the operation, Movement, and variable name match another record, the HCL Setting value must be consistent. | Yes |
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

Monitors the work execution status. "Execution Type" is one of Plan Confirmation / Delete Resources / Normal. For an unexpected error, if it is caused by a configuration issue such as incomplete Interface Information registration, it is shown in the error log; otherwise, check the application log. "Calling Conductor" is set only when executed via a Conductor (for Delete Resources, the calling Conductor, Movement, operation, and input data are not set).

- Execution log types: init.log (Terraform Init), plan.log (Terraform Plan), apply.log (Terraform Apply)
- Logs can be filtered. The display interval and maximum line count follow the Interface Information settings.
- "Input Data" allows downloading the Module material and `terraform.tfvars` (excluding values with Secure Setting True) as a zip file.
- "Result Data" allows downloading init.log/plan.log/apply.log/error.log/result.txt/`.terraform.lock.hcl`/the encrypted `terraform.tfstate` and its backup as a zip file.
- The "Emergency Stop" button stops execution; before a scheduled execution runs, the "Cancel Reservation" button can cancel it.

## Work Management

Displays a filterable list of work execution history. Fields: Work No. (36-digit auto-numbered), Execution Type (Normal/Plan Confirmation/Parameter Sheet Confirmation), Status (Not Executed/Not Executed (Scheduled)/Preparing/Executing/Executing (Delayed)/Completed/Completed (Abnormal)/Unexpected Error/Emergency Stopped/Reservation Cancelled), Executing User, Registration Date/Time, Movement (ID/Name/Delay Timer/Workspace ID and Name), Operation (No./Name), Input Data and Result Data (zip download), Work Status (Scheduled Date/Time/Start Date/Time/End Date/Time), and Remarks.

## Assigned Value Management

View the concrete values of variables used by the Module materials of the Movement linked to an operation. Fields: Work No., Operation, Movement Name, Movement Name:Variable Name, HCL Setting (automatically True for variables with a nested structure where a member variable and assignment order have been entered), Movement Name:Variable Name:Member Variable, Assignment Order, Concrete Value (Sensitive Setting True/False—if True, the value is excluded from Input Data—and the value itself), and Remarks.
