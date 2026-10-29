# Ansible Legacy Default Playbook - System_group_add.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 50
- **playbook_name**: ~[Exastro standard] Add group
- **playbook_file**: System_group_add.yml
## Overview
Creates each group listed in `ITA_DFLT_Groups` on the target with the `group` module using `state: present`, wrapping a single scalar value in a one-element list before looping.
## Description
This Playbook file registers groups specified by "ITA_DFLT_Groups".
"ITA_DFLT_Groups" can specify multiple groups (list type).
## Keyword
- groupadd command
- /etc/group entry creation
- OS user and group management
- bulk group provisioning
- idempotent group creation
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Groups: "{{ ITA_DFLT_Groups }}"
  when: ITA_DFLT_Groups is defined

- name: Add group
  ansible.builtin.group:
    name: "{{ item }}"
    state: present
  loop: >-
    {{
      ITA_DFLT_Groups if ITA_DFLT_Groups is sequence and ITA_DFLT_Groups is not string else [ITA_DFLT_Groups]
    }}
```
