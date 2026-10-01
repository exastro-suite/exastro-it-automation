# Ansible Legacy Default Playbook - System_getent_ethers.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 320
- **playbook_name**: ~[Exastro standard] Get entry(ethers)
- **playbook_file**: System_getent_ethers.yml
## Overview
Uses the `getent` module on the `ethers` database to enumerate the MAC address to host name mappings defined on the host, registering the output as `ITA_DFLT_getent_ethers`.
## Description
This Playbook file takes no parameters. The database name `ethers` is fixed in the task and no key is specified, so every Ethernet address entry the host publishes (normally the contents of /etc/ethers) is enumerated, pairing each hardware address with a host name.
The lookup result is stored with `register` under the name "ITA_DFLT_getent_ethers", so later tasks in the same run can reference it; the module also sets the collected entries as the fact `getent_ethers`.
## Keyword
- MAC address to host mapping
- etc ethers inventory
- hardware address lookup
- RARP and bootp host registration
## Playbook
```yaml
- name: A wrapper to the unix getent utility (ethers)
  ansible.builtin.getent:
    database: ethers
  register: ITA_DFLT_getent_ethers
```
