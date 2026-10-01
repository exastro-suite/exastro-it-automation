# Ansible Legacy Default Playbook - System_authorized_key_add.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 30
- **playbook_name**: ~[Exastro standard] Add Authorized key
- **playbook_file**: System_authorized_key_add.yml
## Overview
Registers SSH public keys with the `authorized_key` module (`state: present`), pairing `ITA_DFLT_Users` and `ITA_DFLT_Authorized_Keys` positionally with `zip_longest`.
## Description
This Playbook file registers SSH authentication keys specified by "ITA_DFLT_Authorized_Keys" to users specified by "ITA_DFLT_Users".
"ITA_DFLT_Users" can specify multiple users (list type).
"ITA_DFLT_Authorized_Keys" can specify multiple SSH authentication keys (list type).
## Keyword
- enable SSH public key login
- passwordless SSH access
- authorized_keys file management
- grant remote shell to operator
## Playbook
```yaml
- name: Ensure ITA_DFLT_Users is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Users: "{{ ITA_DFLT_Users }}"
  when: ITA_DFLT_Users is defined

- name: Ensure ITA_DFLT_Authorized_Keys is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Authorized_Keys: "{{ ITA_DFLT_Authorized_Keys }}"
  when: ITA_DFLT_Authorized_Keys is defined

- name: Add authorized key
  ansible.posix.authorized_key:
    user: "{{ item[0] }}"
    key: "{{ item[1] }}"
    state: present
  loop: >-
    {{
      (ITA_DFLT_Users if ITA_DFLT_Users is sequence and ITA_DFLT_Users is not string else [ITA_DFLT_Users])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Authorized_Keys if ITA_DFLT_Authorized_Keys is sequence and ITA_DFLT_Authorized_Keys is not string else [ITA_DFLT_Authorized_Keys]
        )
      | list
    }}
```
