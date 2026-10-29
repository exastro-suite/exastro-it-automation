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
- ステータスチェックには実行メニューを使用しないでください。

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
- **重要（サーバー側監視）:** `execute-driver` または `dryrun-driver` を呼び出すと、サーバーは実行が最終状態に達するまで自動的に監視し、確認済みの結果をツール結果の `driver_execution` オブジェクト内に返します。`driver_execution.monitored_by_server` が `true` の場合は、`driver_execution.instruction` に従ってください:
]
    - `driver_execution.completed` が `true` の場合：実行は既に `driver_execution.final_status` で終了しています。**`get-driver-status`、`execute-driver`、または `dryrun-driver` を再度呼び出さないでください。** 最終ステータスをユーザーに報告し、会話を終了してください。

    - `driver_execution.completed` が `false` の場合：実行は既に開始されていますが、最終状態に達する前にサーバー側の監視が終了しました。**`execute-driver` / `dryrun-driver` を再実行しないでください。** 状況をユーザーに報告してください。

- ツールの結果に `driver_execution` オブジェクトが含まれていない場合 (サーバー側の監視が利用できない場合) に限り、`get-driver-status` を自分で呼び出し、`execution_no` を指定して、`status` が次の最終状態のいずれかに達するまで (5 秒ごとに) 繰り返しチェックする必要があります。
final states:
    - `Completed`
    - `Completed (error)`
    - `Unexpected error`
    - `Emergency stop`
    - `Unexecuted (schedule)`
    - `Schedule canceled`