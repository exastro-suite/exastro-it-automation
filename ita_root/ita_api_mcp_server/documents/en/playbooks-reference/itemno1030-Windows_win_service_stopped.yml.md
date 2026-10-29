# Ansible Legacy Default Playbook - Windows_win_service_stopped.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1030
- **playbook_name**: ~[Exastro standard][Win] Stop service
- **playbook_file**: Windows_win_service_stopped.yml
## Overview
Stops each listed Windows service with `win_service` using `state: stopped`; the startup mode is not altered.
## Description
This Playbook file stops services specified by "ITA_DFLT_Service_Name".
"ITA_DFLT_Service_Name" can specify multiple service names (list type).
## Keyword
- Take a Windows service offline
- Maintenance window service shutdown
- sc stop equivalent
- Service state not running
## Playbook
```yaml
# This Playbook file stops services specified by "ITA_DFLT_Service_Name".
# "ITA_DFLT_Service_Name" can specify multiple service names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Service_Name: "{{ ITA_DFLT_Service_Name }}"
  when: ITA_DFLT_Service_Name is defined

- name: stop Windows services
  ansible.windows.win_service:
    name: "{{ item }}"
    state: stopped
  loop: >-
    {{
      ITA_DFLT_Service_Name if ITA_DFLT_Service_Name is sequence and ITA_DFLT_Service_Name is not string else [ITA_DFLT_Service_Name]
    }}
```
