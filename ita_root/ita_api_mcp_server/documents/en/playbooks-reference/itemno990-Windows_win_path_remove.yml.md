# Ansible Legacy Default Playbook - Windows_win_path_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 990
- **playbook_name**: ~[Exastro standard][Win] Remove path
- **playbook_file**: Windows_win_path_remove.yml
## Overview
Removes given path elements from a Windows PATH-style environment variable using `win_path` with `state: absent`, zipping the name, elements and scope lists positionally.
## Description
This Playbook file removes the environment variable names specified by "ITA_DFLT_Environment_Name" with the path element specified by "ITA_DFLT_Elements".
"ITA_DFLT_Scope" specifies the level at which the specified environment variable must be managed.
Each of the variables can have multiple specified at the same time (list type).
## Keyword
- Windows PATH variable cleanup
- Remove directory from PATH
- Machine versus user environment scope
- System environment variables
## Playbook
```yaml
# This Playbook file removes the environment variable names specified by "ITA_DFLT_Environment_Name" with the path element specified by "ITA_DFLT_Elements".
# "ITA_DFLT_Scope" specifies the level at which the specified environment variable must be managed.
# Each of the variables can have multiple specified at the same time (list type).
- name: Ensure ITA_DFLT_Environment_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Environment_Name: "{{ ITA_DFLT_Environment_Name }}"
  when: ITA_DFLT_Environment_Name is defined

- name: Ensure ITA_DFLT_Elements is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Elements: "{{ ITA_DFLT_Elements }}"
  when: ITA_DFLT_Elements is defined

- name: Ensure ITA_DFLT_Scope is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Scope: "{{ ITA_DFLT_Scope }}"
  when: ITA_DFLT_Scope is defined

- name: remove Windows path environment variables
  ansible.windows.win_path:
    name: "{{ item[0] }}"
    elements: "{{ item[1] }}"
    scope: "{{ item[2] }}"
    state: absent
  loop: >-
    {{
      (ITA_DFLT_Environment_Name if ITA_DFLT_Environment_Name is sequence and ITA_DFLT_Environment_Name is not string else [ITA_DFLT_Environment_Name])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Elements if ITA_DFLT_Elements is sequence and ITA_DFLT_Elements is not string else [ITA_DFLT_Elements],
          ITA_DFLT_Scope if ITA_DFLT_Scope is sequence and ITA_DFLT_Scope is not string else [ITA_DFLT_Scope]
        )
      | list
    }}
```
