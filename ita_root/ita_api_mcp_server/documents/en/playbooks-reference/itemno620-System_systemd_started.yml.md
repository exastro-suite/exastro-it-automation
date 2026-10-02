# Ansible Legacy Default Playbook - System_systemd_started.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 620
- **playbook_name**: ~[Exastro standard] Start systemd
- **playbook_file**: System_systemd_started.yml
## Overview
Calls `ansible.builtin.systemd` with `state: started` for each name in `ITA_DFLT_Services`, activating any unit that is not already running (idempotent).
## Description
This Playbook file starts services specified by "ITA_DFLT_Services".
"ITA_DFLT_Services" can specify multiple services (list type).
## Keyword
- systemctl start
- bring up a systemd unit
- ensure unit is active
- systemd module rather than service module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Start service
  ansible.builtin.systemd:
    name: "{{ item }}"
    state: started
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
