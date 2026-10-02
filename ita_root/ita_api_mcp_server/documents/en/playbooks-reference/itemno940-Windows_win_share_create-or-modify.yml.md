# Ansible Legacy Default Playbook - Windows_win_share_create-or-modify.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 940
- **playbook_name**: ~[Exastro standard][Win] Modify/create shared settings
- **playbook_file**: Windows_win_share_create-or-modify.yml
## Overview
Creates or updates Windows SMB folder shares with `win_share`, taking name, description, path, list visibility and full/change/read ACLs from seven positionally zipped lists.
## Description
This Playbook file configures shared settings for Windows folders.
The variables are as follows:
"ITA_DFLT_Share_Name": Share name
"ITA_DFLT_Description": Share description
"ITA_DFLT_Directory_Path": Path of Share Directory
"ITA_DFLT_Filelist_Permission": Access base list
"ITA_DFLT_Full_Control": List of users who need to get full access (divide with comma).※1
"ITA_DFLT_Change": List over users who will get access to read and write (divide with comma).※1
"ITA__DFLT_Read_Only": List over users who will get access to read (divide with comma).※1
Each of the variables can have multiple specified at the same time (list type).
※1 Assumes that null link is set to "True" in the Automatic substitute value registration settings.
## Keyword
- SMB file sharing
- Network share permissions
- Share ACL for users and groups
- Folder sharing setup
- Share browsing visibility
## Playbook
```yaml
# This Playbook file configures shared settings for Windows folders.
# The variables are as follows:
# "ITA_DFLT_Share_Name": Share name
# "ITA_DFLT_Description": Share description
# "ITA_DFLT_Directory_Path": Path of Share Directory
# "ITA_DFLT_Filelist_Permission": Access base list
# "ITA_DFLT_Full_Control": List of users who need to get full access (divide with comma).※1
# "ITA_DFLT_Change": List over users who will get access to read and write (divide with comma).※1
# "ITA_DFLT_Read_Only": List over users who will get access to read (divide with comma).※1
# Each of the variables can have multiple specified at the same time (list type).
# ※1 Assumes that null link is set to "True" in the Automatic substitute value registration settings.
- name: Ensure ITA_DFLT_Share_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Share_Name: "{{ ITA_DFLT_Share_Name }}"
  when: ITA_DFLT_Share_Name is defined

- name: Ensure ITA_DFLT_Description is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Description: "{{ ITA_DFLT_Description }}"
  when: ITA_DFLT_Description is defined

- name: Ensure ITA_DFLT_Directory_Path is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Directory_Path: "{{ ITA_DFLT_Directory_Path }}"
  when: ITA_DFLT_Directory_Path is defined

- name: Ensure ITA_DFLT_Filelist_Permission is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Filelist_Permission: "{{ ITA_DFLT_Filelist_Permission }}"
  when: ITA_DFLT_Filelist_Permission is defined

- name: Ensure ITA_DFLT_Full_Control is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Full_Control: "{{ ITA_DFLT_Full_Control }}"
  when: ITA_DFLT_Full_Control is defined

- name: Ensure ITA_DFLT_Change is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Change: "{{ ITA_DFLT_Change }}"
  when: ITA_DFLT_Change is defined

- name: Ensure ITA_DFLT_Read_Only is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Read_Only: "{{ ITA_DFLT_Read_Only }}"
  when: ITA_DFLT_Read_Only is defined

- name: Add or change Windows shares
  ansible.windows.win_share:
    name: "{{ item[0] }}"
    description: "{{ item[1] }}"
    path: "{{ item[2] }}"
    list: "{{ item[3] }}"
    full: "{{ item[4] | default(omit) }}"
    change: "{{ item[5] | default(omit) }}"
    read: "{{ item[6] | default(omit) }}"
  when: item[0] | default('', true) | length > 0
  loop: >-
    {{
      (ITA_DFLT_Share_Name if ITA_DFLT_Share_Name is sequence and ITA_DFLT_Share_Name is not string else [ITA_DFLT_Share_Name])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Description if ITA_DFLT_Description is sequence and ITA_DFLT_Description is not string else [ITA_DFLT_Description],
          ITA_DFLT_Directory_Path if ITA_DFLT_Directory_Path is sequence and ITA_DFLT_Directory_Path is not string else [ITA_DFLT_Directory_Path],
          ITA_DFLT_Filelist_Permission if ITA_DFLT_Filelist_Permission is sequence and ITA_DFLT_Filelist_Permission is not string else [ITA_DFLT_Filelist_Permission],
          ITA_DFLT_Full_Control if ITA_DFLT_Full_Control is sequence and ITA_DFLT_Full_Control is not string else [ITA_DFLT_Full_Control],
          ITA_DFLT_Change if ITA_DFLT_Change is sequence and ITA_DFLT_Change is not string else [ITA_DFLT_Change],
          ITA_DFLT_Read_Only if ITA_DFLT_Read_Only is sequence and ITA_DFLT_Read_Only is not string else [ITA_DFLT_Read_Only]
        )
      | list
    }}
```
