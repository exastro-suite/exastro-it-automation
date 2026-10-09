# Ansible Legacy Default Playbook - System_user_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 550
- **playbook_name**: ~[Exastro standard] Remove user
- **playbook_file**: System_user_remove.yml
## Overview
Deletes accounts with `ansible.builtin.user` using `state: absent` and `remove: true` for each name in `ITA_DFLT_User_Names`, so each user's home directory and mail spool are deleted too.
## Description
This Playbook file deletes users specified by "ITA_DFLT_User_Names".
"ITA_DFLT_User_Names" can specify multiple users (list type).

## Keyword
- userdel -r
- delete a Linux account
- remove home directory
- account deprovisioning
- purge user data
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_User_Names: "{{ ITA_DFLT_User_Names }}"
  when: ITA_DFLT_User_Names is defined

- name: Remove user
  ansible.builtin.user:
    name: "{{ item }}"
    state: absent
    remove: true
  loop: >-
    {{
      ITA_DFLT_User_Names if ITA_DFLT_User_Names is sequence and ITA_DFLT_User_Names is not string else [ITA_DFLT_User_Names]
    }}
```
