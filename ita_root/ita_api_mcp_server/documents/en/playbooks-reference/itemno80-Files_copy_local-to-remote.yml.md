# Ansible Legacy Default Playbook - Files_copy_local-to-remote.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 80
- **playbook_name**: ~[Exastro standard] Copy file
- **playbook_file**: Files_copy_local-to-remote.yml
## Overview
Copies files listed in `ITA_DFLT_Src_Files` from the Ansible control node to the matching paths in `ITA_DFLT_Dest_Files` via `copy` with remote_src false; the two lists are paired positionally.
## Description
This Playbook file copies local files specified by "ITA_DFLT_Src_Files" to remote files specified by "ITA_DFLT_Dest_Files".
"ITA_DFLT_Src_Files" can specify multiple files (list type).
"ITA_DFLT_Dest_Files" can specify multiple files (list type).

## Additional description
- The `FileUploadColumn` item in the parameter sheet can be linked to `ITA_DFLT_Src_Files`.
## Keyword
- upload file to server
- file distribution to nodes
- scalar or list input accepted
- push files from the Ansible controller
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
  ansible.builtin.copy:
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
