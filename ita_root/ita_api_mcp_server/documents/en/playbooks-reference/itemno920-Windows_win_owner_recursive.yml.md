# Ansible Legacy Default Playbook - Windows_win_owner_recursive.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 920
- **playbook_name**: ~[Exastro standard][Win] Modify owner (with recursion)
- **playbook_file**: Windows_win_owner_recursive.yml
## Overview
Changes the owner of specified Windows files or folders to a given user with `win_owner` and `recurse: true`, so items under each folder also receive the new owner.
## Description
"ITA_DFLT_Change_owner_paths": Path of the file or folder whose owner is to be changed. For a folder, the owner of all subfolders and files below it is changed as well.
"ITA_DFLT_Change_owner_users": User (or group) to set as the new owner of the corresponding path.
Each of the variables can have multiple values specified at the same time (list type), and the values are paired positionally between the two lists.
## Keyword
- Windows file ownership
- Recursive ownership change
- takeown entire folder tree
- Reassign owner of subfolders
## Playbook
```yaml
- name: Ensure ITA_DFLT_Change_owner_paths is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Change_owner_paths: "{{ ITA_DFLT_Change_owner_paths }}"
  when: ITA_DFLT_Change_owner_paths is defined

- name: Ensure ITA_DFLT_Change_owner_users is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Change_owner_users: "{{ ITA_DFLT_Change_owner_users }}"
  when: ITA_DFLT_Change_owner_users is defined

- name: Change the owner of folders recursively.
  ansible.windows.win_owner:
    path: "{{ item[0] }}"
    user: "{{ item[1] }}"
    recurse: true
  loop: >-
    {{
      (ITA_DFLT_Change_owner_paths if ITA_DFLT_Change_owner_paths is sequence and ITA_DFLT_Change_owner_paths is not string else [ITA_DFLT_Change_owner_paths])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Change_owner_users if ITA_DFLT_Change_owner_users is sequence and ITA_DFLT_Change_owner_users is not string else [ITA_DFLT_Change_owner_users]
        )
      | list
    }}
```
