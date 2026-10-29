# Ansible Legacy Default Playbook - Windows_win_regedit_delete.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1000
- **playbook_name**: ~[Exastro standard][Win] Remove registry
- **playbook_file**: Windows_win_regedit_delete.yml
## Overview
Deletes Windows registry entries with `win_regedit` and `state: absent`, pairing the registry path list and the entry name list positionally.
## Description
This Playbook file deletes the Registry value (entry).
The variables are as follows:
"ITA_DFLT_Regedit_Path": Registry Path name
"ITA_DFLT_Regedit_Name": Registry Entry name
Each of the variables can have multiple specified at the same time (list type).

## Keyword
- HKLM hive
- Undo registry customization
- Clean leftover application settings
- Purge registry property
## Playbook
```yaml
# This Playbook file deletes the Registry value (entry).
# The variables are as follows:
# "ITA_DFLT_Regedit_Path": Registry Path name
# "ITA_DFLT_Regedit_Name": Registry Entry name
# Each of the variables can have multiple specified at the same time (list type).
- name: Ensure ITA_DFLT_Regedit_Path is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Regedit_Path: "{{ ITA_DFLT_Regedit_Path }}"
  when: ITA_DFLT_Regedit_Path is defined

- name: Ensure ITA_DFLT_Regedit_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Regedit_Name: "{{ ITA_DFLT_Regedit_Name }}"
  when: ITA_DFLT_Regedit_Name is defined

- name: remove registry keys and values
  ansible.windows.win_regedit:
    path: "{{ item[0] }}"
    name: "{{ item[1] }}"
    state: absent
  loop: >-
    {{
      (ITA_DFLT_Regedit_Path if ITA_DFLT_Regedit_Path is sequence and ITA_DFLT_Regedit_Path is not string else [ITA_DFLT_Regedit_Path])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Regedit_Name if ITA_DFLT_Regedit_Name is sequence and ITA_DFLT_Regedit_Name is not string else [ITA_DFLT_Regedit_Name]
        )
      | list
    }}
```
