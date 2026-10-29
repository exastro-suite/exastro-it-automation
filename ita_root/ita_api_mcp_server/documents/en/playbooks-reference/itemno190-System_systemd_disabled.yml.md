# Ansible Legacy Default Playbook - System_systemd_disabled.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 190
- **playbook_name**: ~[Exastro standard] Disable systemd startup
- **playbook_file**: System_systemd_disabled.yml
## Overview
Calls `ansible.builtin.systemd` with `enabled: false` for each name in `ITA_DFLT_Services`, removing the unit's boot-time autostart link without changing its current active state.
## Description
This Playbook file removes the configuration that makes services specified by "ITA_DFLT_Services" to run on server startup.
ITA_DFLT_Services" can specify multiple services (list type).
## Keyword
- systemctl disable
- unit file autostart
- mask boot startup
- systemd unit management
- systemd module rather than service module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Disabled service
  ansible.builtin.systemd:
    name: "{{ item }}"
    enabled: false
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
