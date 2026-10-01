# Ansible Legacy Default Playbook - System_systemd_stopped.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 640
- **playbook_name**: ~[Exastro standard] Stop systemd
- **playbook_file**: System_systemd_stopped.yml
## Overview
Calls `ansible.builtin.systemd` with `state: stopped` for each name in `ITA_DFLT_Services`; it deactivates the running units only and does not remove or delete anything.
## Description
This Playbook file deletes services specified by "ITA_DFLT_Services".
"ITA_DFLT_Services" can specify multiple services (list type).
## Keyword
- systemctl stop
- deactivate a systemd unit
- maintenance outage window
- systemd module rather than service module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Stop service
  ansible.builtin.systemd:
    name: "{{ item }}"
    state: stopped
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
