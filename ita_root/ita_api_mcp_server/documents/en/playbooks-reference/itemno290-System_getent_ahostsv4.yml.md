# Ansible Legacy Default Playbook - System_getent_ahostsv4.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 290
- **playbook_name**: ~[Exastro standard] Get entry(ahostsv4)
- **playbook_file**: System_getent_ahostsv4.yml
## Overview
Uses the `getent` module on the `ahostsv4` database to enumerate host name and address entries restricted to IPv4, registering the output as `ITA_DFLT_getent_ahostsv4`.
## Description
This Playbook file takes no parameters. The database name `ahostsv4` is fixed in the task and no key is specified, so the whole host database reachable through the name service switch is enumerated, limited to IPv4 addresses.
The lookup result is stored with `register` under the name "ITA_DFLT_getent_ahostsv4", so later tasks in the same run can reference it; the module also sets the collected entries as the fact `getent_ahostsv4`.
## Keyword
- IPv4 address resolution
- A record style lookup
- name service switch lookup
- IPv4 only host inventory
## Playbook
```yaml
- name: A wrapper to the unix getent utility (ahostsv4)
  ansible.builtin.getent:
    database: ahostsv4
  register: ITA_DFLT_getent_ahostsv4
```
