# Ansible Legacy Default Playbook - System_getent_initgroups.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 360
- **playbook_name**: ~[Exastro standard] Get entry(initgroups)
- **playbook_file**: System_getent_initgroups.yml
## Overview
Enumerates every user in the `passwd` database on the target host, then looks up each user name in the `initgroups` database through the `getent` module, registering the per-user supplementary group results as `ITA_DFLT_getent_initgroups`.
## Description
For users listed by getent passwd, the GIDs of their supplementary groups (secondary groups) can be obtained. 
The primary group is not included. 
In cases where enumeration is disabled in SSSD, users from external databases (such as LDAP or AD) may not be included.
## Keyword
- secondary group membership
- supplementary group GID lookup
- user privilege assignment audit
- NSS initgroups source
## Playbook
```yaml
- name: Get users from the passwd database
  ansible.builtin.getent:
    database: passwd
  register: ITA_RGST_getent_passwd
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）

- name: A wrapper to the unix getent utility (initgroups)
  ansible.builtin.getent:
    database: initgroups
    key: "{{ item }}"
    fail_key: false
  loop: "{{ ITA_RGST_getent_passwd.ansible_facts.getent_passwd.keys() | list }}"
  register: ITA_DFLT_getent_initgroups
```
