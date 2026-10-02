# Ansible Legacy Default Playbook - Files_file_mkdir.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 100
- **playbook_name**: ~[Exastro standard] Create directory
- **playbook_file**: Files_file_mkdir.yml
## Overview
Creates each directory listed in `ITA_DFLT_Create_Directories` on the target node with the `file` module and state directory; a single scalar value is wrapped into a one-element list.
## Description
This Playbook file creates directories specified by "ITA_DFLT_Create_Directories".
"ITA_DFLT_Create_Directories" can specify multiple directories (list type).
## Keyword
- mkdir -p on a remote host
- ensure a directory exists
- create a folder hierarchy
- directory provisioning
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Create_Directories: "{{ ITA_DFLT_Create_Directories }}"
  when: ITA_DFLT_Create_Directories is defined

- name: Create directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
  loop: >-
    {{
      ITA_DFLT_Create_Directories if ITA_DFLT_Create_Directories is sequence and ITA_DFLT_Create_Directories is not string else [ITA_DFLT_Create_Directories]
    }}
```
