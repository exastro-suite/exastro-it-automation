# Ansible Legacy Default Playbook - Files_copy_remote-to-remote.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 90
- **playbook_name**: ~[Exastro standard] Copy file (within host)
- **playbook_file**: Files_copy_remote-to-remote.yml
## Overview
Copies files inside the target host itself - `copy` is called with remote_src true - pairing each source in `ITA_DFLT_Src_Files` positionally with a destination in `ITA_DFLT_Dest_Files`.
## Description
This Playbook file copies local files specified by "ITA_DFLT_Src_Files" to remote files specified by "ITA_DFLT_Dest_Files".
"ITA_DFLT_Src_Files" can specify multiple files (list type).
"ITA_DFLT_Dest_Files" can specify multiple files (list type).
## Keyword
- duplicate a file on the same host
- copy within a server
- back up a file in place
- remote_src copy
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

- name: Copy data from remote to remote
  ansible.builtin.copy:
    src: "{{ item[0] }}"
    dest: "{{ item[1] }}"
    remote_src: true
  loop: >-
    {{
      (ITA_DFLT_Src_Files if ITA_DFLT_Src_Files is sequence and ITA_DFLT_Src_Files is not string else [ITA_DFLT_Src_Files])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Dest_Files if ITA_DFLT_Dest_Files is sequence and ITA_DFLT_Dest_Files is not string else [ITA_DFLT_Dest_Files]
        )
      | list
    }}
```
