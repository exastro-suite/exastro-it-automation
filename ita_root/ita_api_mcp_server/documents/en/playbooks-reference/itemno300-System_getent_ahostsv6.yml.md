# Ansible Legacy Default Playbook - System_getent_ahostsv6.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 300
- **playbook_name**: ~[Exastro standard] Get entry(ahostsv6)
- **playbook_file**: System_getent_ahostsv6.yml
## Overview
Uses the `getent` module on the `ahostsv6` database to enumerate host name and address entries restricted to IPv6, registering the output as `ITA_DFLT_getent_ahostsv6`.
## Description
This Playbook file takes no parameters. The database name `ahostsv6` is fixed in the task and no key is specified, so the whole host database reachable through the name service switch is enumerated, limited to IPv6 addresses.
The lookup result is stored with `register` under the name "ITA_DFLT_getent_ahostsv6", so later tasks in the same run can reference it; the module also sets the collected entries as the fact `getent_ahostsv6`.
## Keyword
- IPv6 address resolution
- AAAA record style lookup
- name service switch lookup
- IPv6 readiness check
## Playbook
```yaml
- name: A wrapper to the unix getent utility (ahostsv6)
  ansible.builtin.getent:
    database: ahostsv6
  register: ITA_DFLT_getent_ahostsv6
```
