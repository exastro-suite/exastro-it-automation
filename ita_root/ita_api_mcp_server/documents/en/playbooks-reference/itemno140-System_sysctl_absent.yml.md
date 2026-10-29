# Ansible Legacy Default Playbook - System_sysctl_absent.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 140
- **playbook_name**: ~[Exastro standard] Delete sysctl
- **playbook_file**: System_sysctl_absent.yml
## Overview
Calls `ansible.posix.sysctl` with `state: absent` and `reload: true` for each entry in `ITA_DFLT_Parameter_Names`, deleting the kernel parameter line and reloading sysctl immediately.
## Description
This Playbook file removes Parameter names specified by "ITA_DFLT_Parameter_Names" from sysctl.
"ITA_DFLT_Parameter_Names" can specify multiple parameter names(list type).
## Keyword
- kernel parameter removal
- /etc/sysctl.conf cleanup
- revert kernel tuning
- sysctl -p reload
- kernel runtime tuning rollback
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Parameter_Names: "{{ ITA_DFLT_Parameter_Names }}"
  when: ITA_DFLT_Parameter_Names is defined

- name: Remove parameter
  ansible.posix.sysctl:
    name: "{{ item }}"
    state: absent
    reload: true
  loop: >-
    {{
      ITA_DFLT_Parameter_Names if ITA_DFLT_Parameter_Names is sequence and ITA_DFLT_Parameter_Names is not string else [ITA_DFLT_Parameter_Names]
    }}

```
