# Ansible Legacy Default Playbook - Windows_win_service_restarted.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1020
- **playbook_name**: ~[Exastro standard][Win] Restart service
- **playbook_file**: Windows_win_service_restarted.yml
## Overview
Restarts each listed Windows service with `win_service` using `state: restarted`; the startup mode is not altered.
## Description
This Playbook file restarts services specified by "ITA_DFLT_Service_Name".
"ITA_DFLT_Service_Name" can specify multiple service names (list type).

## Keyword
- Apply configuration change to a service
- Bounce a Windows service
- Service recycle
- sc stop and start equivalent
## Playbook
```yaml
# This Playbook file restarts services specified by "ITA_DFLT_Service_Name".
# "ITA_DFLT_Service_Name" can specify multiple service names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Service_Name: "{{ ITA_DFLT_Service_Name }}"
  when: ITA_DFLT_Service_Name is defined

- name: restart Windows services
  ansible.windows.win_service:
    name: "{{ item }}"
    state: restarted
  loop: >-
    {{
      ITA_DFLT_Service_Name if ITA_DFLT_Service_Name is sequence and ITA_DFLT_Service_Name is not string else [ITA_DFLT_Service_Name]
    }}
```
