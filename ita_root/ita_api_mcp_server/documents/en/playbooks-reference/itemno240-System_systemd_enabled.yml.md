# Ansible Legacy Default Playbook - System_systemd_enabled.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 240
- **playbook_name**: ~[Exastro standard] Enable systemd startup
- **playbook_file**: System_systemd_enabled.yml
## Overview
Calls `ansible.builtin.systemd` with `enabled: true` for each name in `ITA_DFLT_Services`, creating the unit's boot-time autostart link without changing its current active state.
## Description
This Playbook file configures services specified by "ITA_DFLT_Services" to run on server startup.
"ITA_DFLT_Services" can specify multiple services (list type).
## Keyword
- systemctl enable
- unit file autostart
- start unit at boot
- systemd unit management
- systemd module rather than service module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Enabled service
  ansible.builtin.systemd:
    name: "{{ item }}"
    enabled: true
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
