# Ansible Legacy Default Playbook - Files_stat.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 260
- **playbook_name**: ~[Exastro standard] Find Filemaster
- **playbook_file**: Files_stat.yml
## Overview
Collects file-system metadata (existence, size, mode, owner, checksum) for every path in `ITA_DFLT_Target_Path` with the `stat` module and registers the looped results in `ITA_DFLT_Files_stat`.
## Description
"ITA_DFLT_Target_Path": Path of the file or directory whose status is to be retrieved. Multiple paths can be specified at the same time (list type); the task loops over each entry, and a single scalar value is automatically treated as a one-element list.
The gathered status of all paths is stored in the registered variable "ITA_DFLT_Files_stat", which is available to later tasks - for example to check "exists", a size or a checksum before deciding whether to act on a file.
This Playbook file only reads information and makes no change to the target node, and it prints nothing by itself, so it is normally combined with other Playbook files that consume the registered result.
## Keyword
- check whether a file exists
- file metadata inquiry
- pre-check before deployment
- file size and checksum
- read-only inspection
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Target_Path: "{{ ITA_DFLT_Target_Path }}"
  when: ITA_DFLT_Target_Path is defined

- name: Retrieve file or file system status
  ansible.builtin.stat:
    path: "{{ item }}"
  loop: >-
    {{
      ITA_DFLT_Target_Path if ITA_DFLT_Target_Path is sequence and ITA_DFLT_Target_Path is not string else [ITA_DFLT_Target_Path]
    }}
  register: ITA_DFLT_Files_stat
```
