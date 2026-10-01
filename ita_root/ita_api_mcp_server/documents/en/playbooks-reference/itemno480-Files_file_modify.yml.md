# Ansible Legacy Default Playbook - Files_file_modify.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 480
- **playbook_name**: ~[Exastro standard] Modify permissions
- **playbook_file**: Files_file_modify.yml
## Overview
Sets the permission mode of each path using the `file` module, pairing `ITA_DFLT_Target_Path` positionally with `ITA_DFLT_Mode`; owner, group and state are left untouched.
## Description
This Playbook file changes permissions specified by "ITA_DFLT_Mode" for the files/directories specified by "ITA_DFLT_Target_Path".
"ITA_DFLT_Target_Path" can specify multiple file/directories (list type).
"TA_DFLT_Mode" can specify multiple permissions (list type).
## Keyword
- chmod a remote file
- file permission bits
- octal mode change
- harden file access rights
## Playbook
```yaml
- name: Ensure ITA_DFLT_Target_Path is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Target_Path: "{{ ITA_DFLT_Target_Path }}"
  when: ITA_DFLT_Target_Path is defined

- name: Ensure ITA_DFLT_Mode is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Mode: "{{ ITA_DFLT_Mode }}"
  when: ITA_DFLT_Mode is defined

- name: Modify permission
  ansible.builtin.file:
    path: "{{ item[0] }}"
    mode: "{{ item[1] }}"
  loop: >-
    {{
      (ITA_DFLT_Target_Path if ITA_DFLT_Target_Path is sequence and ITA_DFLT_Target_Path is not string else [ITA_DFLT_Target_Path])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Mode if ITA_DFLT_Mode is sequence and ITA_DFLT_Mode is not string else [ITA_DFLT_Mode]
        )
      | list
    }}
```
