# Ansible Legacy Default Playbook - System_getent_netgroup.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 370
- **playbook_name**: ~[Exastro standard] Get entry(netgroup
- **playbook_file**: System_getent_netgroup.yml
## Overview
Reads `/etc/netgroup` on the target host, extracts each netgroup name found at the start of a line, and looks up every one of those names in the `netgroup` database through the `getent` module, registering the per-netgroup results as `ITA_DFLT_getent_netgroup`.
## Description
For each netgroup listed in /etc/netgroup, its members (host, user, and domain combinations) are retrieved. 
Netgroups that exist only in external databases (such as LDAP or NIS) are not included.
## Keyword
- netgroup member lookup
- host user domain triples
- NIS netgroup inventory
- access control list of hosts and users
## Playbook
```yaml
- name: Read /etc/netgroup
  ansible.builtin.slurp:
    src: /etc/netgroup
  register: ITA_RGST_netgroup_file
  failed_when: false

- name: A wrapper to the unix getent utility (netgroup)
  ansible.builtin.getent:
    database: netgroup
    key: "{{ item }}"
    fail_key: false
  loop: >-
    {{
      ITA_RGST_netgroup_file.content | default('') | b64decode
      | regex_findall('(?m)^([^ \t#(]+)[ \t]')
    }}
  register: ITA_DFLT_getent_netgroup
```
