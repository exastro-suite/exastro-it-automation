# Ansible Legacy Default Playbook - Windows_win_copy_local-to-remote.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 800
- **playbook_name**: ~[Exastro standard][Win] Copy file
- **playbook_file**: Windows_win_copy_local-to-remote.yml
## Overview
Copies files from the Ansible control node to the Windows target host using `win_copy` with `remote_src: false`, pairing each source path with its destination path positionally.
## Description
"ITA_DFLT_Src_Files": Path of the source file on the Ansible control node (local side) to be copied.
"ITA_DFLT_Dest_Files": Path on the Windows target host where the corresponding source file is placed.
Each of the variables can have multiple values specified at the same time (list type), and the values are paired positionally between the two lists.
A value given as a single string is automatically treated as a one-element list.
## Keyword
- Windows file transfer
- Upload file to Windows host
- Push file from control node
- Distribute files to Windows server
## Playbook
```yaml
- name: Ensure ITA_DFLT_Src_Files is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Src_Files: "{{ ITA_DFLT_Src_Files }}"
  when: ITA_DFLT_Src_Files is defined

- name: Ensure ITA_DFLT_Dest_Files is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Dest_Files: "{{ ITA_DFLT_Dest_Files }}"
  when: ITA_DFLT_Dest_Files is defined

- name: Copy data from local to remote
  ansible.windows.win_copy:
    src: "{{ item[0] }}"
    dest: "{{ item[1] }}"
    remote_src: false
  loop: >-
    {{
      (ITA_DFLT_Src_Files if ITA_DFLT_Src_Files is sequence and ITA_DFLT_Src_Files is not string else [ITA_DFLT_Src_Files])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Dest_Files if ITA_DFLT_Dest_Files is sequence and ITA_DFLT_Dest_Files is not string else [ITA_DFLT_Dest_Files]
        )
      | list
    }}
```
