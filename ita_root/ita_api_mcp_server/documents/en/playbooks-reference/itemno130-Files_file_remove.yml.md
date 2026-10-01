# Ansible Legacy Default Playbook - Files_file_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 130
- **playbook_name**: ~[Exastro standard] Delete files/Directories
- **playbook_file**: Files_file_remove.yml
## Overview
Deletes each path in `ITA_DFLT_Remove_File_or_Directory` with the `file` module and state absent, so directories go recursively; registers `ITA_RGST_Absent_Result` and debugs it.
## Description
This Playbook file deletes packages specified by "ITA_DFLT_Remove_File_or_Directory".
"ITA_DFLT_Remove_File_or_Directory" can specify multiple files (list type).
The task results are displayed at debug level 3 (-vvv).
## Keyword
- delete files and folders
- recursive directory removal
- clean up temporary files
- rm -rf equivalent
## Playbook
```yaml
# This Playbook file deletes packages specified by "ITA_DFLT_Remove_File_or_Directory".
# "ITA_DFLT_Remove_File_or_Directory" can specify multiple files (list type).
# The task results are displayed at debug level 3 (-vvv).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Remove_File_or_Directory: "{{ ITA_DFLT_Remove_File_or_Directory }}"
  when: ITA_DFLT_Remove_File_or_Directory is defined

- name: Recursively remove directory or remove file
  ansible.builtin.file:
    path: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Remove_File_or_Directory if ITA_DFLT_Remove_File_or_Directory is sequence and ITA_DFLT_Remove_File_or_Directory is not string else [ITA_DFLT_Remove_File_or_Directory]
    }}
  register: ITA_RGST_Absent_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_Absent_Result
    verbosity: 3

```
