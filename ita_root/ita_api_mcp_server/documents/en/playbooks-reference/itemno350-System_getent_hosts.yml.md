# Ansible Legacy Default Playbook - System_getent_hosts.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 350
- **playbook_name**: ~[Exastro standard] Get entry(hosts)
- **playbook_file**: System_getent_hosts.yml
## Overview
Queries the target's `hosts` database with the `getent` module, registering the host-name-to-IP-address entries in `ITA_DFLT_getent_hosts` for use by later tasks.
## Description
This Playbook file has no parameters. It always queries the fixed "hosts" database of the Target host (/etc/hosts plus any other NSS source), i.e. the mapping between host names, aliases and IP addresses.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_hosts", so they are available to later tasks in the same Movement.
## Keyword
- /etc/hosts
- name resolution check
- static DNS mapping inventory
- hostname alias listing
## Playbook
```yaml
- name: A wrapper to the unix getent utility (hosts)
  ansible.builtin.getent:
    database: hosts
  register: ITA_DFLT_getent_hosts
```
