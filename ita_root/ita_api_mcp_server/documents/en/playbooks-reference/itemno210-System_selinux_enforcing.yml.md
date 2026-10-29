# Ansible Legacy Default Playbook - System_selinux_enforcing.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 210
- **playbook_name**: ~[Exastro standard] Enable SELinux (enforcing)
- **playbook_file**: System_selinux_enforcing.yml
## Overview
Sets SELinux to `enforcing` with the `ansible.posix.selinux` module for the policy named in `ITA_DFLT_Policy_Name`, writing /etc/selinux/config so policy violations are blocked and logged.
## Description
This Playbook file changes the SELinux settings to "Enforcing".
Make sure to specify a policy name in "ITA_DFLT_Policy_Name".
(E.g. targeted)
## Keyword
- setenforce 1
- turn mandatory access control fully on
- security hardening and compliance
- block and audit policy violations
## Playbook
```yaml
# This Playbook file changes the SELinux settings to "Enforcing".
# Make sure to specify a policy name in "ITA_DFLT_Policy_Name".
# (E.g. targeted)
- name: Change the SELinux policy state to enforcing
  ansible.posix.selinux:
    policy: "{{ ITA_DFLT_Policy_Name }}"
    state: enforcing
```
