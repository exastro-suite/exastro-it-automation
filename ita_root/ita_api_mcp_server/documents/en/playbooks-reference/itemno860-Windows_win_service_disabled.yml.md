# Ansible Legacy Default Playbook - Windows_win_service_disabled.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 860
- **playbook_name**: ~[Exastro standard][Win] Disable service startup
- **playbook_file**: Windows_win_service_disabled.yml
## Overview
Sets each listed Windows service to `start_mode: disabled` with `win_service` so it can no longer start automatically; the current running state is left untouched.
## Description
This Playbook file deactivates "automatic boot mode" for the services specified by "ITA_DFL_Service_Name".
"ITA_DFLT_Service_Name" can specify multiple service names (list type).
## Keyword
- Prevent service auto-start
- Service startup type
- Harden server by turning off services
- Services console startup type
## Playbook
```yaml
# This Playbook file deactivates "automatic boot mode" for the services specified by "ITA_DFL_Service_Name".
# "ITA_DFLT_Service_Name" can specify multiple service names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Service_Name: "{{ ITA_DFLT_Service_Name }}"
  when: ITA_DFLT_Service_Name is defined

- name: Disable automatic startup of Windows services
  ansible.windows.win_service:
    name: "{{ item }}"
    start_mode: disabled
  loop: >-
    {{
      ITA_DFLT_Service_Name if ITA_DFLT_Service_Name is sequence and ITA_DFLT_Service_Name is not string else [ITA_DFLT_Service_Name]
    }}
```
