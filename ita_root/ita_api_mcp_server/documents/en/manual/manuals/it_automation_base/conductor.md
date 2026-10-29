# Conductor Configuration and Usage

Conductor is a function for defining and executing work flows that combine Movements.

## Menu Structure

| Menu | Description |
|---|---|
| Conductor Interface Information | Maintain (view/update, always a single record) interface information. |
| Conductor Notification Destination Definition | Maintain (view/register/update) definitions of notifications sent during work execution. |
| Conductor List | Maintain (view/decommission) registered Conductors. "Details" navigates to Conductor Edit/Work Execution. |
| Conductor Edit/Work Execution | Edit a Conductor and execute work. |
| Conductor Work History | View execution history. "Details" navigates to Conductor Work Confirmation. |
| Conductor Work Confirmation | Check the execution results of work. |
| Conductor Scheduled Work Execution | Maintain (view/register/update) Conductor work that runs periodically according to a schedule. |

## Standard Work Flow

1. Register and confirm device information (Ansible Common).
2. Register and confirm an operation (Basic Console).
3. Register a Movement from each driver and confirm it (Basic Console).
4. Register Conductor interface information.
5. Register and confirm a Conductor.
6. Execute the Conductor and check the results/history.

During Conductor execution, information can be passed between Movements by using a directory path shared across Movements (for Ansible driver targets). A work flow invoked via "Conductor call" has its own separate shared directory, so it cannot share this directory with Movements outside that work flow.

## Conductor Interface Information

Configures the directory path shared across Movements and the refresh interval for "Conductor Work Confirmation". Items: Conductor Interface ID (auto-numbered), status monitoring interval (in milliseconds, required, minimum 1000ms, around 1000ms recommended), remarks.

## Conductor Notification Destination Definition

Configures definitions of notifications sent during work execution.

| Item | Description | Required |
|---|---|---|
| Conductor Notification ID | Auto-numbered | - |
| Notification Name | Any name | Yes |
| Notification Destination URL | Destination URL | Yes |
| Header | HTTP header fields (JSON format) | Yes |
| Message | Content following the destination service's specification (ITA-specific variables can be used, described below) | Yes |
| PROXY URL / PORT | Specify if a proxy is required | Yes |
| Work Confirmation URL | FQDN used in the reserved variable for the work confirmation URL | Yes |
| Suppression Start/End Date-Time | Period during which notifications should be suppressed | Yes |
| Remarks | Free text | - |

ITA-specific variables usable in the message: `__CONDUCTOR_INSTANCE_ID__` (Conductor instance ID), `__CONDUCTOR_NAME__` (Conductor name), `__STATUS_ID__` (status ID), `__OPERATION_ID__`/`__OPERATION_NAME__` (operation), `__EXECUTION_USER__` (executing user), `__PARENT_CONDUCTOR_INSTANCE_ID__`/`__PARENT_CONDUCTOR_NAME__` (parent Conductor), `__TOP_CONDUCTOR_INSTANCE_ID__`/`__TOP_CONDUCTOR_NAME__` (top-level Conductor), `__ABORT_EXECUTE_FLAG__` (emergency stop flag), `__REGISTER_TIME__`/`__TIME_BOOK__`/`__TIME_START__`/`__TIME_END__` (registration/scheduled/start/end date-time), `__NOTICE_NAME__` (notification log), `__NOTE__` (remarks), `__JUMP_URL__` (work confirmation screen URL, uses the work confirmation URL).

Status ID mapping: 3 = Running, 4 = Running (delayed), 5 = Paused, 6 = Completed normally, 7 = Completed abnormally, 8 = Completed with warning, 9 = Emergency stopped, 10 = Reservation cancelled, 11 = Unexpected error.

Example of the work confirmation URL output (when the work confirmation URL (FQDN) is `http://localhost:38000`): `http://localhost:38000/org002/workspaces/workspace1/ita/?menu=conductor_confirmation&conductor_instance_id=X`

### Notification Destination Definition Examples

**Teams example**: Header `["Content-Type: application/json"]`, message `{"text": "Notification: __NOTICE_NAME__, Conductor name: __CONDUCTOR_NAME__, Conductor instance ID: __CONDUCTOR_INSTANCE_ID__, Status ID: __STATUS_ID__, Work URL: __JUMP_URL__"}`

**Slack example**: Specify the Slack Webhook URL as the destination; otherwise configured the same way as Teams.

**Example including proxy, notification suppression, and other settings**: In addition to destination URL, header, and message, you can configure PROXY URL/PORT, work confirmation URL, other options (a cURL option such as `{"CURLOPT_TIMEOUT":"10"}`), and the suppression start/end date-time.

### Notification Log Structure

```json
[
  {
    "conductor_status_id": "3",
    "exec_time": "2023/07/05 16:29:50",
    "result": [
      {
        "notice_name": "test",
        "notice_info": ["3","4","5"],
        "status_code": 200,
        "response.headers": {},
        "response.text": "1"
      }
    ]
  }
]
```

On failure, `status_code` becomes an error code (e.g. 400), `response.text` contains the error content, and `err_type` (e.g. `HTTPError`) is added.

## Conductor Edit/Work Execution

### Modes

| Mode | Description |
|---|---|
| Edit | Create a new Conductor (default mode). Selecting an existing Conductor via "Select" switches to view mode. |
| View | View-only mode for a Conductor (reached from "Details" in the Conductor List). "Edit" switches to update mode. |
| Update | Edit an existing Conductor ("Update" returns to view mode). |

### Nodes (work-flow parts)

| Node | Behavior |
|---|---|
| Conductor start | Starts the Conductor. |
| Conductor end | Ends the Conductor (if there are multiple, waits for all Conductor end nodes to finish). Choose an end status from "Normal" (default), "Warning", or "Abnormal"; when multiple End nodes are passed, the higher-priority status applies, in the order Normal < Warning < Abnormal. |
| Conductor pause | Pauses the work flow (resuming proceeds to the next process). |
| Conductor call | Invokes and executes another registered Conductor (if the called Conductor ends with a warning, it is treated the same as a normal end and does not affect the caller's status). An individual operation can be specified. |
| Conditional branch | Branches subsequent processing based on the result of the connected Movement/Conductor call (branchable statuses: normal end / abnormal end / emergency stop / preparation error / unexpected error / skip completed / warning end, up to 6 cases). Default is case1 = normal end, Other = everything else. |
| Parallel branch | Executes Movements/Conductor calls in parallel (the number of parallel branches depends on the ITA configuration and server specs; default is 2 branches, minimum 2). |
| Parallel merge | Executes the next process after all connected nodes have completed (default 2 branches, minimum 2). |
| Status file branch | Branches based on the content of a status file in a Movement's work result directory (default is if/else; conditions can be added or removed). |
| Various Movements | Executes a Movement. |

**Node constraints**: All nodes must have their IN/OUT connected. Parallel merge must be used in a pair with Parallel branch (a flow branched by Conditional branch cannot be merged with Parallel merge). Parallel branch, Conditional branch, Parallel merge, and Conductor pause cannot be connected consecutively to the same type of node. A Conductor that is currently being updated cannot be specified and updated via Conductor call.

**Status file branch reference target**: The `MOVEMENT_STATUS_FILE` (referenceable via the ITA-specific variable `__movement_status_filepath__`) under each Movement's work result directory. If the file does not exist, the "else" branch is taken. If the content has multiple lines, only the value before the first line break is evaluated.

### Node Detail Info Tab (Edit/Update mode)

- **Conductor tab (no node selected)**: ID (auto), name (required), update date/time (auto), notifications (multiple selectable per status, from Conductor Notification Destination Definition), Movement common display settings (node width, Movement name display format), remarks.
- **When a Movement is selected**: Movement ID/name (auto-displayed), skip (can also be changed on the work execution screen), individual operation (can execute using the selected operation; used to apply a concrete value registered under a different operation ID in "Assignment Value Management"), remarks.
- **When Conductor call is selected**: Skip, Conductor to call, individual operation.
- **When Conditional branch is selected**: Conditional branch settings (add/remove branches, up to 6).
- **When Parallel branch is selected**: Parallel branch settings (add/remove branches, default 2, minimum 2).
- **When Parallel merge is selected**: Case settings (add/remove merges, default 2, minimum 2).
- **When Conductor end is selected**: End status (normal/warning/abnormal).
- **When Status file branch is selected**: Status file branch settings, remarks.
- **When multiple nodes are selected (Node tab)**: Alignment operations — align left/center-horizontal/right/top/center-vertical/bottom, distribute horizontally/vertically.

### Available Operations (by mode)

| Operation | New (EDIT) | Update (VIEW) | Update (EDIT) |
|---|---|---|---|
| Save JSON / Load JSON | Yes | | |
| Undo / Redo | Yes | | Yes |
| Delete/Register selected node | Yes | | Yes |
| Reset | Yes | | |
| Edit | | Yes | Yes |
| Repurpose as new | | Yes | Yes |
| Update / Reload / Cancel | | | Yes |
| Snap to grid | Yes | | Yes |

Operations in view mode: Select (choose an existing Conductor to view), Edit, Execute work, Repurpose as new (copy and create new), New. Operations in update mode: Update, Reload (discard changes), Cancel (revert to pre-edit state), Full screen, Fit to screen (scale to show all nodes).

### Conductor Work Execution

Clicking "Execute work" in view mode displays the work execution settings screen.

| Item | Description | Required |
|---|---|---|
| Conductor to execute | The selected Conductor (auto-displayed) | - |
| Operation | Select from the operation list in the Basic Console | Yes |
| Schedule | Scheduled execution date/time (cannot be earlier than the current time) | - |
| Execute Work | Execute button | Yes |

At execution time, the operation and skip settings of a Movement/Conductor call can be individually changed, but this change is not reflected back into the registered Conductor Edit data — it only applies to that execution (**note the difference: individual specifications made in Edit/Update mode are saved on register/update, while individual specifications made on the work execution screen apply only to that run and are not saved**). Specifying a scheduled date/time creates a work reservation, which can be checked in Conductor Work History. At execution time, the common role of the access permissions configured for the selected Conductor and operation is inherited; execution is not possible if there is no common role.

## Conductor Work History

Manages completed Conductor work runs. Search the work history using the filter, and use "Details" to navigate to Conductor Work Confirmation. "Submitted Data Set (zip)" and "Result Data Set (zip)" let you download the execution files and logs of all Movements under the executed Conductor together (including terminal Movements in hierarchical structures).

## Conductor Work Confirmation

Displays the execution status of a Conductor. Clicking the execution status circle for a status of "running" or later navigates to each driver's "Work Status Confirmation". You can monitor the progress and, depending on the situation, submit "Cancel Reservation", "Release Pause", or "Emergency Stop".

**Note**: If you edit an already-executed Conductor in Conductor Edit/Work Execution, its state may differ from when it was executed, so "Details" may not display the processing status. When you want to edit and re-run an already-executed Conductor, it is recommended to create a separate Conductor using "Repurpose as new".

**Conductor tab** (no node selected): Conductor instance information (ID, name, status: not executed / not executed (reserved) / running / running (delayed) / paused / completed normally / completed abnormally / completed with warning / emergency stopped / reservation cancelled / unexpected error, start/end time, executing user, scheduled date/time, whether emergency-stopped), operation, remarks.

**Node tab** (node selected): Node instance information (ID, type, node ID (ID in the JSON structure), status: not executed / preparing / running / running (delayed) / completed normally / completed abnormally / unexpected error / emergency stopped / paused / preparation error / skip completed / completed with warning, status file (the Status file value, for Movements), start/end date-time), individual operation, remarks.

## Conductor Scheduled Work Execution

Manages Conductor work that runs periodically according to a schedule. The "Work History" button navigates to the Conductor Work History filtered to the execution targets of that scheduled work.

| Item | Description | Required |
|---|---|---|
| Scheduled Work Execution ID | Auto-numbered | - |
| Conductor Name | Select from the Conductor list | Yes |
| Operation Name | Select from the operation list | Yes |
| Status | See table below (auto) | - |
| Executing User | Carried over from the registering/updating user; becomes the Conductor's executing user when the scheduled run is registered | - |
| Schedule settings: Start date | Start date of the scheduled execution (the next execution date is updated to be on or after this date) | Yes |
| Schedule settings: End date | End date of the scheduled execution (status becomes "Completed" once the next execution date exceeds this date) | - |
| Schedule settings: Cycle | "Hour", "Day", "Week", "Month (by date)", "Month (by weekday)", "End of month" | Yes |
| Schedule settings: Interval | Execution interval based on the cycle | Yes |
| Schedule settings: Week number / Day of week | Required when the cycle is "Month (by weekday)" (day of week is also required for the "weekday" cycle) | Conditional |
| Schedule settings: Day | Required when the cycle is "Month (by date)" | Conditional |
| Schedule settings: Time | Required when the cycle is "Day", "Week", "Month (by date)", "Month (by weekday)", or "End of month" | Conditional |
| Work suspension period: Start/End | Both required if configured. No Conductor work is registered during this period | Conditional |
| Remarks | Free text | - |

### Status List

| Status | Description |
|---|---|
| Preparing | State immediately after registration. Becomes "Active" once the backyard process updates the next execution date. |
| Active | Operating normally. Registers work into the Conductor List a set amount of time (per the "Conductor Interval Time Setting") before the next execution date, then updates the next execution date. |
| Completed | The next execution date has passed the end date. No further work is registered. |
| Inconsistency Error | The schedule configuration values are invalid. |
| Association Error | Registration of work into the Conductor List failed. Registration/update continues as in "Active", but this state persists if it keeps failing. |
| Unexpected Error | A failure other than an inconsistency or association error occurred. |
| Conductor Decommissioned / Operation Decommissioned | The target Conductor or operation was decommissioned (restoring it returns the status to "Preparing"). |

The "Conductor Interval Time Setting" in the Admin Console's system settings configures how many minutes before the next execution date the work registration is performed.

**Note**: When migrating between different organizations via menu export/import, the executing user may end up in an ID-conversion-failed state; if scheduled work execution runs in that state, the status becomes "Association Error". In this case you need to update the record so the executing user is no longer in the ID-conversion-failed state.
