# Ansible Legacy Default Playbook - Windows_win_service_started.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1080
- **playbook_name**: ~[Exastro standard][Win]Start service
- **playbook_file**: Windows_win_service_started.yml
## Overview
Starts each listed Windows service with `win_service` using `state: started`; the startup mode is not altered.
## Description
This Playbook file starts services specified by "ITA_DFLT_Service_Name".
"ITA_DFLT_Service_Name" can specify multiple service names (list type).
## Keyword
- Bring a Windows service online
- Recover a stopped service
- sc start equivalent
- Service state running
## Playbook
```yaml
# This Playbook file starts services specified by "ITA_DFLT_Service_Name".
# "ITA_DFLT_Service_Name" can specify multiple service names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Service_Name: "{{ ITA_DFLT_Service_Name }}"
  when: ITA_DFLT_Service_Name is defined

- name: start Windows services
  ansible.windows.win_service:
    name: "{{ item }}"
    state: started
  loop: >-
    {{
      ITA_DFLT_Service_Name if ITA_DFLT_Service_Name is sequence and ITA_DFLT_Service_Name is not string else [ITA_DFLT_Service_Name]
    }}
```
