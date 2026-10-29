# Ansible Legacy Default Playbook - Windows_win_file_mkdir.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 820
- **playbook_name**: ~[Exastro standard][Win] Create folder
- **playbook_file**: Windows_win_file_mkdir.yml
## Overview
Creates the specified folders on the Windows target host with `win_file` using `state: directory`, running the task once for every path supplied.
## Description
"ITA_DFLT_Create_Directory": Path of the folder to create on the Windows target host. Missing parent folders are created as well, and an already existing folder is left unchanged.
The variable can have multiple values specified at the same time (list type), and the task is repeated for each path; a single string value is automatically treated as a one-element list.
## Keyword
- Windows create directory
- mkdir on Windows host
- Prepare folder structure
- Ensure folder exists
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Create_Directory: "{{ ITA_DFLT_Create_Directory }}"
  when: ITA_DFLT_Create_Directory is defined

- name: Create folders
  ansible.windows.win_file:
    path: "{{ item }}"
    state: directory
  loop: >-
    {{
      ITA_DFLT_Create_Directory if ITA_DFLT_Create_Directory is sequence and ITA_DFLT_Create_Directory is not string else [ITA_DFLT_Create_Directory]
    }}
```
