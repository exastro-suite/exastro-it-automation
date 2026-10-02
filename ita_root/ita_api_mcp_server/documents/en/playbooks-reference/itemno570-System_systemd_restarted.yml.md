# Ansible Legacy Default Playbook - System_systemd_restarted.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 570
- **playbook_name**: ~[Exastro standard] Restart systemd
- **playbook_file**: System_systemd_restarted.yml
## Overview
Calls `ansible.builtin.systemd` with `state: restarted` and `daemon_reload: true` for each name in `ITA_DFLT_Services`, so edited unit files are re-read before each unit is restarted.
## Description
This Playbook file reboots services specified by "ITA_DFLT_Services".
"ITA_DFLT_Services" can specify multiple services (list type).
## Keyword
- systemctl restart
- systemctl daemon-reload
- bounce a systemd unit
- apply unit file changes
- systemd module rather than service module
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Services: "{{ ITA_DFLT_Services }}"
  when: ITA_DFLT_Services is defined

- name: Restart service
  ansible.builtin.systemd:
    name: "{{ item }}"
    state: restarted
    daemon_reload: true
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
