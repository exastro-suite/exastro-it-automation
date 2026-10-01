# Ansible Legacy Default Playbook - System_service_enabled.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 230
- **playbook_name**: ~[Exastro standard] Enable service startup
- **playbook_file**: System_service_enabled.yml
## Overview
Calls `ansible.builtin.service` with `enabled: true` for each name in `ITA_DFLT_Services`, registering boot-time autostart without changing the current running state.
## Description
This Playbook file configures services specified by "ITA_DFLT_Services" to run on server startup.
"ITA_DFLT_Services" can specify multiple services (list type).
## Keyword
- chkconfig on
- autostart at boot
- SysV init script
- runlevel configuration
- service module rather than systemd module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Enable service
  ansible.builtin.service:
    name: "{{ item }}"
    enabled: true
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
