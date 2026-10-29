# Ansible Legacy Default Playbook - Windows_win_group_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 980
- **playbook_name**: ~[Exastro standard][Win] Remove group
- **playbook_file**: Windows_win_group_remove.yml
## Overview
Deletes the specified local groups from the Windows target host by calling `win_group` with `state: absent` once for each group name given.
## Description
"ITA_DFLT_Remove_groups": Name of the local group to delete from the Windows target host.
The variable can have multiple values specified at the same time (list type), and the removal task is repeated for each group name; a single string value is automatically treated as a one-element list.
## Keyword
- Windows local group deletion
- Remove security group
- Revoke group based access
- Windows account cleanup
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Remove_groups: "{{ ITA_DFLT_Remove_groups }}"
  when: ITA_DFLT_Remove_groups is defined

- name: Remove groups
  ansible.windows.win_group:
    name: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Remove_groups if ITA_DFLT_Remove_groups is sequence and ITA_DFLT_Remove_groups is not string else [ITA_DFLT_Remove_groups]
    }}
```
