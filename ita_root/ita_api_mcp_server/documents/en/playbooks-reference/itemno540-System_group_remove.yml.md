# Ansible Legacy Default Playbook - System_group_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 540
- **playbook_name**: ~[Exastro standard] Remove group
- **playbook_file**: System_group_remove.yml
## Overview
Removes each group listed in `ITA_DFLT_Groups` from the target with the `group` module using `state: absent`, wrapping a single scalar value in a one-element list before looping.
## Description
This Playbook file deletes groups specified by "ITA_DFLT_Groups".
"ITA_DFLT_Groups" can specify multiple groups (list type).
## Keyword
- groupdel command
- /etc/group cleanup
- OS user and group management
- bulk group deprovisioning
- idempotent group removal
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Groups: "{{ ITA_DFLT_Groups }}"
  when: ITA_DFLT_Groups is defined

- name: Remove group
  ansible.builtin.group:
    name: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Groups if ITA_DFLT_Groups is sequence and ITA_DFLT_Groups is not string else [ITA_DFLT_Groups]
    }}
```
