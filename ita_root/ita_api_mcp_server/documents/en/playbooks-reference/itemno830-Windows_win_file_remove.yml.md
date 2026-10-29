# Ansible Legacy Default Playbook - Windows_win_file_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 830
- **playbook_name**: ~[Exastro standard][Win] Delete File/Folder
- **playbook_file**: Windows_win_file_remove.yml
## Overview
Deletes the specified files or folders on the Windows target host with `win_file` using `state: absent`; a folder is removed together with its contents.
## Description
"ITA_DFLT_Remove_File_or_Directory": Path of the file or folder to delete on the Windows target host. When the path points to a folder, the folder and everything under it are removed recursively.
The variable can have multiple values specified at the same time (list type), and the deletion task is repeated for each path; a single string value is automatically treated as a one-element list.
## Keyword
- Windows delete folder recursively
- Remove file from Windows host
- Clean up temporary files
- Erase directory tree
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Remove_File_or_Directory: "{{ ITA_DFLT_Remove_File_or_Directory }}"
  when: ITA_DFLT_Remove_File_or_Directory is defined

- name: Recursively remove directory or remove file
  ansible.windows.win_file:
    path: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Remove_File_or_Directory if ITA_DFLT_Remove_File_or_Directory is sequence and ITA_DFLT_Remove_File_or_Directory is not string else [ITA_DFLT_Remove_File_or_Directory]
    }}
```
