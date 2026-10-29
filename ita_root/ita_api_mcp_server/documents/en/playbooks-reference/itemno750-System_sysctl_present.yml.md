# Ansible Legacy Default Playbook - System_sysctl_present.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 750
- **playbook_name**: ~[Exastro standard] sysctly settings
- **playbook_file**: System_sysctl_present.yml
## Overview
Calls `ansible.posix.sysctl` with `state: present` and `reload: true`, pairing `ITA_DFLT_Parameter_Names` with `ITA_DFLT_Parameter_Values` positionally via a zip_longest loop.
## Description
This Playbook file registers Parameter names specified by "ITA_DFLT_Parameter_Names" and values specified by "ITA_DFLT_Parameter_Values" to sysctl.
"ITA_DFLT_Parameter_Names" can specify multiple parameter names (list type).
"ITA_DFLT_Parameter_Values" can specify multiple values (list type).
## Keyword
- kernel parameter tuning
- /etc/sysctl.conf entry
- set kernel runtime value
- sysctl -p reload
- persistent kernel setting
## Playbook
```yaml
- name: Ensure ITA_DFLT_Parameter_Names is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Parameter_Names: "{{ ITA_DFLT_Parameter_Names }}"
  when: ITA_DFLT_Parameter_Names is defined

- name: Ensure ITA_DFLT_Parameter_Values is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Parameter_Values: "{{ ITA_DFLT_Parameter_Values }}"
  when: ITA_DFLT_Parameter_Values is defined

- name: Entry parameter
  ansible.posix.sysctl:
    name: "{{ item[0] }}"
    value: "{{ item[1] }}"
    state: present
    reload: true
  loop: >-
    {{
      (ITA_DFLT_Parameter_Names if ITA_DFLT_Parameter_Names is sequence and ITA_DFLT_Parameter_Names is not string else [ITA_DFLT_Parameter_Names])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Parameter_Values if ITA_DFLT_Parameter_Values is sequence and ITA_DFLT_Parameter_Values is not string else [ITA_DFLT_Parameter_Values]
        )
      | list
    }}
```
