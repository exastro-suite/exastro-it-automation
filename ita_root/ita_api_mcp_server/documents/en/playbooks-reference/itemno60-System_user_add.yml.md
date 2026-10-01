# Ansible Legacy Default Playbook - System_user_add.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 60
- **playbook_name**: ~[Exastro standard] Add user
- **playbook_file**: System_user_add.yml
## Overview
Creates accounts with `ansible.builtin.user` (`state: present`), pairing each name in `ITA_DFLT_User_Names` with the primary group in `ITA_DFLT_User_Group_Names` positionally via zip_longest.
## Description
This Playbook file registers users specified by "ITA_DFLT_User_Names" to groups specified by "ITA_DFLT_User_Group_Names".
"ITA_DFLT_User_Names" can specify multiple users (list type).
"ITA_DFLT_Group_Names" can specify multiple groups (list type).
## Keyword
- useradd
- create a Linux account
- primary group assignment
- account provisioning
- home directory creation
## Playbook
```yaml
- name: Ensure ITA_DFLT_User_Names is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_User_Names: "{{ ITA_DFLT_User_Names }}"
  when: ITA_DFLT_User_Names is defined

- name: Ensure ITA_DFLT_User_Group_Names is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_User_Group_Names: "{{ ITA_DFLT_User_Group_Names }}"
  when: ITA_DFLT_User_Group_Names is defined

- name: Add user
  ansible.builtin.user:
    name: "{{ item[0] }}"
    group: "{{ item[1] }}"
    state: present
  loop: >-
    {{
      (ITA_DFLT_User_Names if ITA_DFLT_User_Names is sequence and ITA_DFLT_User_Names is not string else [ITA_DFLT_User_Names])
      | ansible.builtin.zip_longest(
          ITA_DFLT_User_Group_Names if ITA_DFLT_User_Group_Names is sequence and ITA_DFLT_User_Group_Names is not string else [ITA_DFLT_User_Group_Names]
        )
      | list
    }}
```
