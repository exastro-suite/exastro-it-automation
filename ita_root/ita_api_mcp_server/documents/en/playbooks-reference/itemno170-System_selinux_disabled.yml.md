# Ansible Legacy Default Playbook - System_selinux_disabled.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 170
- **playbook_name**: ~[Exastro standard] Disable SELinux
- **playbook_file**: System_selinux_disabled.yml
## Overview
Sets SELinux to `disabled` with the `ansible.posix.selinux` module for the policy named in `ITA_DFLT_Policy_Name`, editing /etc/selinux/config; a reboot is needed to fully take effect.
## Description
This Playbook file changes the SELinux settings to "Disabled".
Make sure to specify a policy name in "ITA_DFLT_Policy_Name".
(E.g. targeted)
## Keyword
- SELINUX=disabled
- turn off mandatory access control
- troubleshoot AVC denial messages
- relax host security for installation
## Playbook
```yaml
# This Playbook file changes the SELinux settings to "Disabled".
# Make sure to specify a policy name in "ITA_DFLT_Policy_Name".
# (E.g. targeted)
- name: Change the SELinux policy state to disabled
  ansible.posix.selinux:
    policy: "{{ ITA_DFLT_Policy_Name }}"
    state: disabled
```
