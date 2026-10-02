# Ansible Legacy Default Playbook - System_getent_protocols.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 400
- **playbook_name**: ~[Exastro standard] Get entry(protocols)
- **playbook_file**: System_getent_protocols.yml
## Overview
Queries the target's `protocols` database with the `getent` module, registering the protocol name and protocol number entries in `ITA_DFLT_getent_protocols`.
## Description
This Playbook file has no parameters. It always queries the fixed "protocols" database of the Target host (/etc/protocols), i.e. the known internet protocols with their official numbers and aliases, such as tcp, udp and icmp.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_protocols", so they are available to later tasks in the same Movement.
## Keyword
- /etc/protocols
- IP protocol number reference
- TCP UDP ICMP definitions
- network stack configuration audit
## Playbook
```yaml
- name: A wrapper to the unix getent utility (protocols)
  ansible.builtin.getent:
    database: protocols
  register: ITA_DFLT_getent_protocols
```
