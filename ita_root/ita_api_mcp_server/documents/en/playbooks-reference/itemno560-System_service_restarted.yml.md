# Ansible Legacy Default Playbook - System_service_restarted.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 560
- **playbook_name**: ~[Exastro standard] Restart service
- **playbook_file**: System_service_restarted.yml
## Overview
Calls `ansible.builtin.service` with `state: restarted` for each name in `ITA_DFLT_Services`, stopping and starting each one unconditionally.
## Description
This Playbook file restarts services specified by "ITA_DFLT_Services".
"ITA_DFLT_Services" can specify multiple services (list type).

## Keyword
- bounce a daemon
- apply configuration changes to a running process
- SysV init restart
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
    state: restarted
  loop: >-
    {{
      ITA_DFLT_Services if ITA_DFLT_Services is sequence and ITA_DFLT_Services is not string else [ITA_DFLT_Services]
    }}
```
