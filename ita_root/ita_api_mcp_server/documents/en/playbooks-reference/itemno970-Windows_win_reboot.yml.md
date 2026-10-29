# Ansible Legacy Default Playbook - Windows_win_reboot.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 970
- **playbook_name**: ~[Exastro standard][Win] Reboot
- **playbook_file**: Windows_win_reboot.yml
## Overview
Reboots the Windows target host with `win_reboot`, setting `reboot_timeout` from `ITA_DFLT_Reboot_Timeout` and falling back to 600 seconds when that variable is undefined.
## Description
This Playbook file reboots the Target host.
The user can specify timeout time with "ITA_DFLT_Reboot_Timeout".
## Keyword
- Windows machine restart
- Wait for host to come back online
- Planned server reboot
- Apply change requiring restart
## Playbook
```yaml
# This Playbook file reboots the Target host.
# The user can specify timeout time with "ITA_DFLT_Reboot_Timeout".
- name: Reboot a windows machine
  ansible.windows.win_reboot:
    reboot_timeout: "{{ ITA_DFLT_Reboot_Timeout | default(600) }}"
```
