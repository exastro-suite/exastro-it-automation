# Ansible Legacy Default Playbook - System_getent_group.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 330
- **playbook_name**: ~[Exastro standard] Get entry(group)
- **playbook_file**: System_getent_group.yml
## Overview
Uses the `getent` module on the `group` database to enumerate the groups defined on the host with their GIDs and member lists, registering the output as `ITA_DFLT_getent_group`.
## Description
This Playbook file takes no parameters. The database name `group` is fixed in the task and no key is specified, so every group entry the host publishes (normally the contents of /etc/group plus any directory service configured in the name service switch) is enumerated, each with its password placeholder, group ID, and member list.
The lookup result is stored with `register` under the name "ITA_DFLT_getent_group", so later tasks in the same run can reference it; the module also sets the collected entries as the fact `getent_group`.
## Keyword
- list OS groups and GIDs
- etc group audit
- group membership inventory
- account and permission review
## Playbook
```yaml
- name: A wrapper to the unix getent utility (group)
  ansible.builtin.getent:
    database: group
  register: ITA_DFLT_getent_group
```
