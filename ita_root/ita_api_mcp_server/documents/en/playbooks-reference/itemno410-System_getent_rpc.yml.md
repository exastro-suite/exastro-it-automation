# Ansible Legacy Default Playbook - System_getent_rpc.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 410
- **playbook_name**: ~[Exastro standard] Get entry(rpc)
- **playbook_file**: System_getent_rpc.yml
## Overview
Queries the target's `rpc` database with the `getent` module, registering the RPC program name and program number entries in `ITA_DFLT_getent_rpc`.
## Description
This Playbook file has no parameters. It always queries the fixed "rpc" database of the Target host (/etc/rpc), i.e. the Remote Procedure Call program names with their program numbers and aliases, as used by services such as NFS and the portmapper.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_rpc", so they are available to later tasks in the same Movement.
## Keyword
- /etc/rpc
- NFS portmapper program numbers
- rpcbind service inventory
- Remote Procedure Call reference data
## Playbook
```yaml
- name: A wrapper to the unix getent utility (rpc)
  ansible.builtin.getent:
    database: rpc
  register: ITA_DFLT_getent_rpc
```
