# Ansible Legacy Default Playbook - System_service_stopped.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 630
- **playbook_name**: ~[Exastro standard] Stop service
- **playbook_file**: System_service_stopped.yml
## Overview
Calls `ansible.builtin.service` with `state: stopped` for each name in `ITA_DFLT_Services`; it only halts the running processes and does not uninstall or delete anything.
## Description
This Playbook file stops services specified by "ITA_DFLT_Services".
"ITA_DFLT_Services" can specify multiple services (list type).

## Keyword
- shut down a daemon
- halt running process
- SysV init stop
- maintenance outage window
- service module rather than systemd module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Stop service
  ansible.builtin.service:
    name: "{{ item }}"
    state: stopped
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
