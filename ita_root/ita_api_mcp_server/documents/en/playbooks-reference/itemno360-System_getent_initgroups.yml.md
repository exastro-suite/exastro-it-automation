# Ansible Legacy Default Playbook - System_getent_initgroups.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 360
- **playbook_name**: ~[Exastro standard] Get entry(initgroups)
- **playbook_file**: System_getent_initgroups.yml
## Overview
Queries the target's `initgroups` database with the `getent` module, registering the supplementary groups a user receives at login in `ITA_DFLT_getent_initgroups`.
## Description
This Playbook file has no parameters. It always queries the fixed "initgroups" database of the Target host, i.e. the list of supplementary groups that each user is placed in when logging in.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_initgroups", so they are available to later tasks in the same Movement.
## Keyword
- secondary group membership
- user privilege assignment audit
- login session groups
- NSS initgroups source
## Playbook
```yaml
- name: A wrapper to the unix getent utility (initgroups)
  ansible.builtin.getent:
    database: initgroups
  register: ITA_DFLT_getent_initgroups
```
