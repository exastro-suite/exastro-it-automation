# Ansible Legacy Default Playbook - System_reboot.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 510
- **playbook_name**: ~[Exastro standard] Reboot
- **playbook_file**: System_reboot.yml
## Overview
Reboots the target host with the `reboot` module and waits for it to come back, using `reboot_timeout` taken from `ITA_DFLT_Reboot_Timeout` or defaulting to 600 seconds.
## Description
This Playbook file reboots the Target host.
The user can specify timeout time with "ITA_DFLT_Reboot_Timeout".
## Keyword
- restart server
- shutdown -r now
- apply kernel or patch updates
- wait for host to come back online
- maintenance window operation
## Playbook
```yaml
# This Playbook file reboots the Target host.
# The user can specify timeout time with "ITA_DFLT_Reboot_Timeout".
- name: Reboot
  ansible.builtin.reboot:
    reboot_timeout: "{{ ITA_DFLT_Reboot_Timeout | default(600) }}"

```
