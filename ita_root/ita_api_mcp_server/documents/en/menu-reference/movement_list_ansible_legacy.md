# movement_list_ansible_legacy reference
## ansible_agent_execution_environment column
- The setting value differs depending on the value set for `execution_engine` in the `interface_info_ansible` menu.
    - If it is `Ansible Execution Agent`, the setting is required (an error will occur at execution time if not set).
        - For the value to set, if there is only one choice, set that choice; if there are multiple choices, confirm with the user which choice to set.
    - If it is other than `Ansible Execution Agent`, no setting is required.

## host_specific_format column
- It is determined by the setting values in the `device_list` menu of the target device.
    - If `ip_address` is set and `host_dns_name` is not set, set `IP`.
    - If `host_dns_name` is set and `ip_address` is not set, set `Host name`.

## header_section column
- Decide whether to add `become: true` based on whether root privileges are required.
- If it is unclear whether the task to be executed requires root privileges, confirm with the user whether root privileges are required and decide whether to add `become: true` accordingly.
