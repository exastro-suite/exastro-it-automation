# Ansible Legacy Default Playbook - Windows_win_user_delete.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1010
- **playbook_name**: ~[Exastro standard][Win] Remove user
- **playbook_file**: Windows_win_user_delete.yml
## Overview
Deletes Windows local user accounts with `win_user` and `state: absent`, looping over each supplied user name.
## Description
This Playbook file deletes users specified by "ITA_DFLT_Win_User_Name".
"ITA_DFLT_Win_User_Name" can specify multiple user names (list type).
## Keyword
- Local account removal
- Offboard a user
- Revoke local login access
- Local Users and Groups management
## Playbook
```yaml
# This Playbook file deletes users specified by "ITA_DFLT_Win_User_Name".
# "ITA_DFLT_Win_User_Name" can specify multiple user names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Win_User_Name: "{{ ITA_DFLT_Win_User_Name }}"
  when: ITA_DFLT_Win_User_Name is defined

- name: Delete user
  ansible.windows.win_user:
    name: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Win_User_Name if ITA_DFLT_Win_User_Name is sequence and ITA_DFLT_Win_User_Name is not string else [ITA_DFLT_Win_User_Name]
    }}
```
