# Ansible Legacy Default Playbook - System_getent_ahosts.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 280
- **playbook_name**: ~[Exastro standard] Get entry(ahosts)
- **playbook_file**: System_getent_ahosts.yml
## Overview
Uses the `getent` module on the `ahosts` database to enumerate host name and address entries for all address families (IPv4 and IPv6), registering the output as `ITA_DFLT_getent_ahosts`.
## Description
This Playbook file takes no parameters. The database name `ahosts` is fixed in the task and no key is specified, so the whole host database reachable through the name service switch is enumerated, returning addresses of every address family.
The lookup result is stored with `register` under the name "ITA_DFLT_getent_ahosts", so later tasks in the same run can reference it; the module also sets the collected entries as the fact `getent_ahosts`.
## Keyword
- host name resolution check
- list hosts file entries
- name service switch lookup
- collect address inventory
## Playbook
```yaml
- name: A wrapper to the unix getent utility (ahosts)
  ansible.builtin.getent:
    database: ahosts
  register: ITA_DFLT_getent_ahosts
```
