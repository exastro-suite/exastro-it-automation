# Ansible Legacy Default Playbook - System_getent_passwd.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 390
- **playbook_name**: ~[Exastro standard] Get entry(passwd)
- **playbook_file**: System_getent_passwd.yml
## Overview
Queries the target's `passwd` database with the `getent` module, registering every user account entry in `ITA_DFLT_getent_passwd`; `no_log: true` suppresses the output as sensitive.
## Description
This Playbook file has no parameters. It always queries the fixed "passwd" database of the Target host (/etc/passwd plus any other NSS source), i.e. every user account with its UID, GID, home directory and login shell.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_passwd", so they are available to later tasks in the same Movement.
Because the data is confidential, the task sets "no_log: true" and the retrieved values are therefore not written to the execution log (change it to false when debugging).
## Keyword
- /etc/passwd
- list OS users and UIDs
- login shell and home directory audit
- user inventory collection
## Playbook
```yaml
- name: A wrapper to the unix getent utility (passwd)
  ansible.builtin.getent:
    database: passwd
  register: ITA_DFLT_getent_passwd
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）
```
