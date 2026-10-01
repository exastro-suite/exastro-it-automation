# Ansible Legacy Default Playbook - System_service_started.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 610
- **playbook_name**: ~[Exastro standard] Start service
- **playbook_file**: System_service_started.yml
## Overview
Calls `ansible.builtin.service` with `state: started` for each name in `ITA_DFLT_Services`, bringing up any that are not already running (idempotent).
## Description
This Playbook file starts services specified by "ITA_DFLT_Services".
"ITA_DFLT_Services" can specify multiple services (list type).
## Keyword
- bring up a daemon
- ensure process is running
- SysV init start
- service module rather than systemd module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Start service
  ansible.builtin.service:
    name: "{{ item }}"
    state: started
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
