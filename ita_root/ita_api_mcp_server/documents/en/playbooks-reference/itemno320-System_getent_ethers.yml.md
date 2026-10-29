# Ansible Legacy Default Playbook - System_getent_ethers.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 320
- **playbook_name**: ~[Exastro standard] Get entry(ethers)
- **playbook_file**: System_getent_ethers.yml
## Overview
Reads `/etc/ethers` on the target host, extracts each MAC address found at the start of a line, and looks up every one of those addresses in the `ethers` database through the `getent` module, registering the per-address results as `ITA_DFLT_getent_ethers`.
## Description
For each MAC address listed in /etc/ethers, the corresponding hostname is retrieved. 
Entries that exist only in external databases (such as LDAP or NIS) are not included.
## Keyword
- MAC address to hostname mapping
- RARP host resolution
- hardware address lookup
- Ethernet address inventory
## Playbook
```yaml
- name: Read /etc/ethers
  ansible.builtin.slurp:
    src: /etc/ethers
  register: ITA_RGST_ethers_file
  failed_when: false

- name: A wrapper to the unix getent utility (ethers)
  ansible.builtin.getent:
    database: ethers
    key: "{{ item }}"
    fail_key: false
  loop: >-
    {{
      ITA_RGST_ethers_file.content | default('') | b64decode
      | regex_findall('(?m)^[ \t]*([0-9A-Fa-f]{1,2}(?::[0-9A-Fa-f]{1,2}){5})[ \t]')
    }}
  register: ITA_DFLT_getent_ethers
```
