# execute-driver / dryrun-driver / get-driver-status tool reference

## Driver Execution Tools - Menu Name Reference
### Tool and Menu Mapping

| Tool | Correct Menu Name | Purpose |
|------|------------------|---------|
| `execute-driver` | `execution_ansible_legacy` | Start execution |
| `dryrun-driver` | `execution_ansible_legacy` | Start dry-run |
| `get-driver-status` | `check_operation_status_ansible_legacy` | Check status |

### Important
- **Execution menus** (`execution_*`): For starting operations
- **Status menus** (`check_operation_status_*`): For checking execution status
- Do not use the execution menu for status checks.

### Example Flow
```javascript
// 1. Start execution
execute-driver({
menu: "execution_ansible_legacy",
movement_name: "...",
operation_name: "..."
})
returns execution_no

// 2. Check status
get-driver-status({
    menu: "check_operation_status_ansible_legacy",  // ← Different menu!
    execution_no: "..."
})
```

### Menu Patterns by Driver Type
- Ansible-Legacy: execution_ansible_legacy / check_operation_status_ansible_legacy
- Ansible-Pioneer: execution_ansible_pioneer / check_operation_status_ansible_pioneer
- Ansible-Role: execution_ansible_role / check_operation_status_ansible_role
- Terraform: Similar pattern

### Check status
- **Important (server-side monitoring):** When you call `execute-driver` or `dryrun-driver`, the server automatically monitors execution until it reaches a final state, and returns the confirmed result inside the `driver_execution` object in the tool result. If `driver_execution.monitored_by_server` is `true`, follow `driver_execution.instruction`:

    - If `driver_execution.completed` is `true`: execution has already finished with `driver_execution.final_status`. **Do not call `get-driver-status`, `execute-driver`, or `dryrun-driver` again.** Report the final status to the user and end the conversation.

    - If `driver_execution.completed` is `false`: execution has already started, but server-side monitoring ended before it reached a final state. **Do not re-run `execute-driver` / `dryrun-driver`.** Report the situation to the user.

- Only if the tool result does not contain a `driver_execution` object (i.e., server-side monitoring is unavailable) should you call `get-driver-status` yourself, specifying `execution_no`, and repeatedly check (every 5 seconds) until `status` reaches one of the following final states.
final states:
    - `Completed`
    - `Completed (error)`
    - `Unexpected error`
    - `Emergency stop`
    - `Unexecuted (schedule)`
    - `Schedule canceled`