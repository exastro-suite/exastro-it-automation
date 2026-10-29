# Ansible Legacy Default Playbook - System_getent_shadow.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 430
- **playbook_name**: ~[Exastro standard] Get entry(shadow)
- **playbook_file**: System_getent_shadow.yml
## Overview
Queries the target's `shadow` database with the `getent` module, registering the encrypted password and password-aging entries in `ITA_DFLT_getent_shadow`; `no_log: true` hides the output.
## Description
This Playbook file has no parameters. It always queries the fixed "shadow" database of the Target host (/etc/shadow), i.e. the encrypted user passwords together with the password aging and account expiry fields.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_shadow", so they are available to later tasks in the same Movement.
Because the data is confidential, the task sets "no_log: true" and the retrieved values are therefore not written to the execution log (change it to false when debugging).
## Keyword
- /etc/shadow
- password hash audit
- account expiry and aging policy check
- locked account detection
## Playbook
```yaml
- name: A wrapper to the unix getent utility (shadow)
  ansible.builtin.getent:
    database: shadow
  register: ITA_DFLT_getent_shadow
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）
```
