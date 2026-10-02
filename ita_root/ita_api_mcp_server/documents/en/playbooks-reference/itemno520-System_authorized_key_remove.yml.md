# Ansible Legacy Default Playbook - System_authorized_key_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 520
- **playbook_name**: ~[Exastro standard] Remove Authorized key
- **playbook_file**: System_authorized_key_remove.yml
## Overview
Deletes SSH public keys with the `authorized_key` module (`state: absent`), pairing `ITA_DFLT_Users` and `ITA_DFLT_Authorized_Keys` positionally with `zip_longest`.
## Description
This Playbook file removes SSH authentication keys specified by "ITA_DFLT_Authorized_Keys" from users specified by "ITA_DFLT_Users".
"ITA_DFLT_Users" can specify multiple users (list type).
"ITA_DFLT_Authorized_Keys" can specify multiple SSH authentication keys (list type).
## Keyword
- revoke SSH access
- delete authorized_keys entry
- offboard a user account
- SSH key rotation
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

- name: Remove authorized key
  ansible.posix.authorized_key:
    user: "{{ item[0] }}"
    key: "{{ item[1] }}"
    state: absent
  loop: >-
    {{
      (ITA_DFLT_Users if ITA_DFLT_Users is sequence and ITA_DFLT_Users is not string else [ITA_DFLT_Users])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Authorized_Keys if ITA_DFLT_Authorized_Keys is sequence and ITA_DFLT_Authorized_Keys is not string else [ITA_DFLT_Authorized_Keys]
        )
      | list
    }}
```
