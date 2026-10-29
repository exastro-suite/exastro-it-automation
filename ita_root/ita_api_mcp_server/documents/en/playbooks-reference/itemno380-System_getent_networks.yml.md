# Ansible Legacy Default Playbook - System_getent_networks.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 380
- **playbook_name**: ~[Exastro standard] Get entry(networks)
- **playbook_file**: System_getent_networks.yml
## Overview
Queries the target's `networks` database with the `getent` module, registering the network-name-to-network-number entries in `ITA_DFLT_getent_networks`.
## Description
This Playbook file has no parameters. It always queries the fixed "networks" database of the Target host (/etc/networks), i.e. the mapping between symbolic network names and their network numbers.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_networks", so they are available to later tasks in the same Movement.
## Keyword
- /etc/networks
- subnet alias inventory
- IP addressing reference data
- network naming configuration
## Playbook
```yaml
- name: A wrapper to the unix getent utility (networks)
  ansible.builtin.getent:
    database: networks
  register: ITA_DFLT_getent_networks
```
