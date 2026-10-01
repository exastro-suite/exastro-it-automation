# Ansible Legacy Default Playbook - Windows_win_user_create-or-modify.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 780
- **playbook_name**: ~[Exastro standard][Win] Add user
- **playbook_file**: Windows_win_user_create-or-modify.yml
## Overview
Creates or updates Windows local users with `win_user` and `state: present`, taking name, password and group membership from three positionally zipped lists; `no_log` hides credentials.
## Description
This Playbook file creates the users specified with "ITA_DFLT_Win_User_Name" with the passwords specified with "ITA_DFLT_Win_Password". The users are put in the groups specified by "ITA_DFLT_Win_Groups".
"ITA_DFLT_Win_User_Name" can specify multiple templates (list type).
"ITA_DFLT_Win_Password" can specify multiple files (list type).
"ITA_DFLT_Win_Groups" can specify multiple files (list type).
## Keyword
- Local account provisioning
- Set a user password
- Add a user to the Administrators group
- Local Users and Groups management
## Playbook
```yaml
# This Playbook file creates the users specified with "ITA_DFLT_Win_User_Name" with the passwords specified with "ITA_DFLT_Win_Password". The users are put in the groups specified by "ITA_DFLT_Win_Groups".
# "ITA_DFLT_Win_User_Name" can specify multiple templates (list type).
# "ITA_DFLT_Win_Password" can specify multiple files (list type).
# "ITA_DFLT_Win_Groups" can specify multiple files (list type).
- name: Ensure ITA_DFLT_Win_User_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Win_User_Name: "{{ ITA_DFLT_Win_User_Name }}"
  when: ITA_DFLT_Win_User_Name is defined

- name: Ensure ITA_DFLT_Win_Password is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Win_Password: "{{ ITA_DFLT_Win_Password }}"
  when: ITA_DFLT_Win_Password is defined
  no_log: true

- name: Ensure ITA_DFLT_Win_Groups is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Win_Groups: "{{ ITA_DFLT_Win_Groups }}"
  when: ITA_DFLT_Win_Groups is defined

- name: Add user
  ansible.windows.win_user:
    name: "{{ item[0] }}"
    password: "{{ item[1] }}"
    state: present
    groups: "{{ item[2] }}"
  loop: >-
    {{
      (ITA_DFLT_Win_User_Name if ITA_DFLT_Win_User_Name is sequence and ITA_DFLT_Win_User_Name is not string else [ITA_DFLT_Win_User_Name])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Win_Password if ITA_DFLT_Win_Password is sequence and ITA_DFLT_Win_Password is not string else [ITA_DFLT_Win_Password],
          ITA_DFLT_Win_Groups if ITA_DFLT_Win_Groups is sequence and ITA_DFLT_Win_Groups is not string else [ITA_DFLT_Win_Groups]
        )
      | list
    }}
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）
```
