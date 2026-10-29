# Ansible Legacy Default Playbook - Windows_win_group_add.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 760
- **playbook_name**: ~[Exastro standard][Win] Add group
- **playbook_file**: Windows_win_group_add.yml
## Overview
Creates local groups on the Windows target host with `win_group` (`state: present`), pairing each group name with its description positionally in the loop.
## Description
"ITA_DFLT_Create_group_names": Name of the local group to create on the Windows target host.
"ITA_DFLT_Create_group_discriptions": Description text set on the corresponding group (note that the variable name itself is spelled "discriptions").
Each of the variables can have multiple values specified at the same time (list type), and the values are paired positionally between the two lists.
## Keyword
- Windows local group creation
- Add security group
- Group description text
- Windows account management
## Playbook
```yaml
- name: Ensure ITA_DFLT_Create_group_names is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Create_group_names: "{{ ITA_DFLT_Create_group_names }}"
  when: ITA_DFLT_Create_group_names is defined

- name: Ensure ITA_DFLT_Create_group_discriptions is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Create_group_discriptions: "{{ ITA_DFLT_Create_group_discriptions }}"
  when: ITA_DFLT_Create_group_discriptions is defined

- name: Create new groups
  ansible.windows.win_group:
    name: "{{ item[0] }}"
    description: "{{ item[1] }}"
    state: present
  loop: >-
    {{
      (ITA_DFLT_Create_group_names if ITA_DFLT_Create_group_names is sequence and ITA_DFLT_Create_group_names is not string else [ITA_DFLT_Create_group_names])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Create_group_discriptions if ITA_DFLT_Create_group_discriptions is sequence and ITA_DFLT_Create_group_discriptions is not string else [ITA_DFLT_Create_group_discriptions]
        )
      | list
    }}
```
