# Ansible Legacy Default Playbook - System_selinux_permissive.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 220
- **playbook_name**: ~[Exastro standard] Enable SELinux (permissive)
- **playbook_file**: System_selinux_permissive.yml
## Overview
Switches SELinux into permissive mode with `ansible.posix.selinux` (`state: permissive`), using the policy named in `ITA_DFLT_Policy_Name`, so denials are logged but not enforced.
## Description
This Playbook file changes the SELinux settings to "Permissive".
Make sure to specify a policy name in "ITA_DFLT_Policy_Name".
(E.g. targeted)
## Keyword
- SELinux enforcement mode
- setenforce 0
- log denials without blocking
- targeted policy
- relax mandatory access control
## Playbook
```yaml
# This Playbook file changes the SELinux settings to "Permissive".
# Make sure to specify a policy name in "ITA_DFLT_Policy_Name".
# (E.g. targeted)
- name: Change the SELinux policy state to permissive
  ansible.posix.selinux:
    policy: "{{ ITA_DFLT_Policy_Name }}"
    state: permissive
```
