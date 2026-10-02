# Ansible Legacy Default Playbook - Windows_win_service_enabled.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 880
- **playbook_name**: ~[Exastro standard][Win] Enable service startup
- **playbook_file**: Windows_win_service_enabled.yml
## Overview
Sets each listed Windows service to `start_mode: auto` with `win_service` so it starts automatically at boot; the current running state is left untouched.
## Description
This Playbook file changes the boot mode for services specified by "ITA_DFLT_Service_Name" to automatic.
"Ita_DFLT_Service_Name" can specify multiple service names (list type).
## Keyword
- Service startup type
- Auto-start at boot
- Ensure service survives a reboot
- Services console automatic
## Playbook
```yaml
# This Playbook file changes the boot mode for services specified by "ITA_DFLT_Service_Name" to automatic.
# "Ita_DFLT_Service_Name" can specify multiple service names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Service_Name: "{{ ITA_DFLT_Service_Name }}"
  when: ITA_DFLT_Service_Name is defined

- name: Automatic startup settings for Windows services
  ansible.windows.win_service:
    name: "{{ item }}"
    start_mode: auto
  loop: >-
    {{
      ITA_DFLT_Service_Name if ITA_DFLT_Service_Name is sequence and ITA_DFLT_Service_Name is not string else [ITA_DFLT_Service_Name]
    }}
```
