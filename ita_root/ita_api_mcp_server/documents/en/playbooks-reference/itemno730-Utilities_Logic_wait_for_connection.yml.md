# Ansible Legacy Default Playbook - Utilities_Logic_wait_for_connection.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 730
- **playbook_name**: ~[Exastro standard] Wait for connection
- **playbook_file**: Utilities_Logic_wait_for_connection.yml
## Overview
Blocks until the target host is reachable and usable via `wait_for_connection`; the pre-poll delay defaults to 0 seconds and the timeout defaults to 600 seconds when not given.
## Description
This Playbook file makes the workflow wait until the Target host can be used or reached.
The user can specify how long to wait until the polling starts with "ITA_DFLT_Wait_Delay" and the maximum wait time with "ITA_DFLT_Wait_Timeout".
## Keyword
- Wait for reboot to complete
- Host availability polling
- Connection retry timeout
- Readiness check before next task
## Playbook
```yaml
# This Playbook file makes the workflow wait until the Target host can be used or reached.
# The user can specify how long to wait until the polling starts with "ITA_DFLT_Wait_Delay" and the maximum wait time with "ITA_DFLT_Wait_Timeout".
- name: Wait until remote system is reachable/usable
  ansible.builtin.wait_for_connection:
    delay: "{{ ITA_DFLT_Wait_Delay | default(0) }}"
    timeout: "{{ ITA_DFLT_Wait_Timeout | default(600) }}"

```
