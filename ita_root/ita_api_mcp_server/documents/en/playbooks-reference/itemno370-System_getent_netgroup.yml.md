# Ansible Legacy Default Playbook - System_getent_netgroup.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 370
- **playbook_name**: ~[Exastro standard] Get entry(netgroup
- **playbook_file**: System_getent_netgroup.yml
## Overview
Queries the target's `netgroup` database with the `getent` module, registering the netgroup entries (host, user, domain triples) in `ITA_DFLT_getent_netgroup`.
## Description
This Playbook file has no parameters. It always queries the fixed "netgroup" database of the Target host, i.e. the netgroup definitions, each a set of (host, user, domain) triples used to group machines and accounts together.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_netgroup", so they are available to later tasks in the same Movement.
## Keyword
- NIS netgroup
- access control list of hosts and users
- LDAP netgroup inventory
- centralised account grouping
## Playbook
```yaml
- name: A wrapper to the unix getent utility (netgroup)
  ansible.builtin.getent:
    database: netgroup
  register: ITA_DFLT_getent_netgroup
```
