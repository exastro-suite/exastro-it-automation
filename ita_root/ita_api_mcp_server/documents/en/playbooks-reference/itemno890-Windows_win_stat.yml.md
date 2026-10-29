# Ansible Legacy Default Playbook - Windows_win_stat.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 890
- **playbook_name**: ~[Exastro standard][Win] Get file status
- **playbook_file**: Windows_win_stat.yml
## Overview
Collects metadata for each supplied Windows path with `win_stat`, using `follow: true` so links are resolved to their target; no `register` is used, so results appear only in the run log.
## Description
This Playbook file acquires the file path information specified by "ITA_DFLT_File_Path".
"ITA_DFLT_File_Path" can specify multiple file paths (list type).
## Keyword
- Check whether a file exists on Windows
- File size, timestamp and checksum
- Filesystem inventory
- Pre-check before deployment
## Playbook
```yaml
# This Playbook file acquires the file path information specified by "ITA_DFLT_File_Path".
# "ITA_DFLT_File_Path" can specify multiple file paths (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_File_Path: "{{ ITA_DFLT_File_Path }}"
  when: ITA_DFLT_File_Path is defined

- name: Get information about Windows files
  ansible.windows.win_stat:
    path: "{{ item }}"
    follow: true
  loop: >-
    {{
      ITA_DFLT_File_Path if ITA_DFLT_File_Path is sequence and ITA_DFLT_File_Path is not string else [ITA_DFLT_File_Path]
    }}
  
```
