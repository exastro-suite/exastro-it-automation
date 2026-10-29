# Ansible Legacy Default Playbook - Windows_win_regedit_create-or-modify.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 930
- **playbook_name**: ~[Exastro standard][Win] Modify/add registry
- **playbook_file**: Windows_win_regedit_create-or-modify.yml
## Overview
Creates or updates Windows registry entries with `win_regedit`, setting path, name, data and type from four lists that are zipped together positionally.
## Description
This Playbook file adds or edits registry keys and values.
The variables are as follows:
"ITA_DFLT_Regedit_Path": Registry Path name
"ITA_DFLT_Regedit_Name": Registry Entry name
"ITA_DFLT_Regedit_Data": Registry Entry value
"ITA_DFLT_Regedit_Type": Registry value Data type
Each of the variables can have multiple specified at the same time (list type).
## Keyword
- HKLM hive
- REG_SZ and REG_DWORD value types
- OS tuning through the registry
- Idempotent registry configuration
## Playbook
```yaml
# This Playbook file adds or edits registry keys and values.
# The variables are as follows:
# "ITA_DFLT_Regedit_Path": Registry Path name
# "ITA_DFLT_Regedit_Name": Registry Entry name
# "ITA_DFLT_Regedit_Data": Registry Entry value
# "ITA_DFLT_Regedit_Type": Registry value Data type
# Each of the variables can have multiple specified at the same time (list type).
- name: Ensure ITA_DFLT_Regedit_Path is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Regedit_Path: "{{ ITA_DFLT_Regedit_Path }}"
  when: ITA_DFLT_Regedit_Path is defined

- name: Ensure ITA_DFLT_Regedit_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Regedit_Name: "{{ ITA_DFLT_Regedit_Name }}"
  when: ITA_DFLT_Regedit_Name is defined

- name: Ensure ITA_DFLT_Regedit_Data is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Regedit_Data: "{{ ITA_DFLT_Regedit_Data }}"
  when: ITA_DFLT_Regedit_Data is defined

- name: Ensure ITA_DFLT_Regedit_Type is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Regedit_Type: "{{ ITA_DFLT_Regedit_Type }}"
  when: ITA_DFLT_Regedit_Type is defined

- name: Add, change registry keys and values
  ansible.windows.win_regedit:
    path: "{{ item[0] }}"
    name: "{{ item[1] }}"
    data: "{{ item[2] }}"
    type: "{{ item[3] }}"
  loop: >-
    {{
      (ITA_DFLT_Regedit_Path if ITA_DFLT_Regedit_Path is sequence and ITA_DFLT_Regedit_Path is not string else [ITA_DFLT_Regedit_Path])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Regedit_Name if ITA_DFLT_Regedit_Name is sequence and ITA_DFLT_Regedit_Name is not string else [ITA_DFLT_Regedit_Name],
          ITA_DFLT_Regedit_Data if ITA_DFLT_Regedit_Data is sequence and ITA_DFLT_Regedit_Data is not string else [ITA_DFLT_Regedit_Data],
          ITA_DFLT_Regedit_Type if ITA_DFLT_Regedit_Type is sequence and ITA_DFLT_Regedit_Type is not string else [ITA_DFLT_Regedit_Type]
        )
      | list
    }}
```
