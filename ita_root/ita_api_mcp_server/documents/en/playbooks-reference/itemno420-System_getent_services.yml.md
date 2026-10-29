# Ansible Legacy Default Playbook - System_getent_services.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 420
- **playbook_name**: ~[Exastro standard] Get entry(services)
- **playbook_file**: System_getent_services.yml
## Overview
Queries the target's `services` database with the `getent` module, registering the service name, port number and protocol entries in `ITA_DFLT_getent_services`.
## Description
This Playbook file has no parameters. It always queries the fixed "services" database of the Target host (/etc/services), i.e. the known network services with their assigned port numbers, protocols and aliases.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_services", so they are available to later tasks in the same Movement.
## Keyword
- /etc/services
- well-known port numbers
- port to service name mapping
- firewall planning reference
## Playbook
```yaml
- name: A wrapper to the unix getent utility (services)
  ansible.builtin.getent:
    database: services
  register: ITA_DFLT_getent_services
```
