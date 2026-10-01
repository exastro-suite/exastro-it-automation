# Ansible Legacy Default Playbook - Windows_win_template.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 850
- **playbook_name**: ~[Exastro standard][Win] Deploy template file
- **playbook_file**: Windows_win_template.yml
## Overview
Renders Jinja2 template files onto the Windows target with `win_template`, writing each source file into its positionally paired destination directory under the source file's basename.
## Description
This Playbook file deploys Templates specified by "ITA_DFLT_Win_Template_Dest_Director" to files specified by "ITA_DFLT_Win_Template_Dest_Directory".
"ITA_DFLT_Win_Template_Src_File_Name" can specify multiple templates (list type).
"ITA_DFLT_Win_Template_Dest_Directory" can specify multiple files (list type).
## Keyword
- Jinja2 variable substitution
- Generate configuration files
- Push rendered config to Windows
- Template based file deployment
## Playbook
```yaml
- name: Ensure ITA_DFLT_Win_Template_Src_File_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Win_Template_Src_File_Name: "{{ ITA_DFLT_Win_Template_Src_File_Name }}"
  when: ITA_DFLT_Win_Template_Src_File_Name is defined

- name: Ensure ITA_DFLT_Win_Template_Dest_Directory is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Win_Template_Dest_Directory: "{{ ITA_DFLT_Win_Template_Dest_Directory }}"
  when: ITA_DFLT_Win_Template_Dest_Directory is defined

- name: Fetch files from remote nodes
  ansible.windows.win_template:
    src: "{{ item[0] }}"
    dest: "{{ item[1] }}\\{{ item[0] | basename }}"
  loop: >-
    {{
      (ITA_DFLT_Win_Template_Src_File_Name if ITA_DFLT_Win_Template_Src_File_Name is sequence and ITA_DFLT_Win_Template_Src_File_Name is not string else [ITA_DFLT_Win_Template_Src_File_Name])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Win_Template_Dest_Directory if ITA_DFLT_Win_Template_Dest_Directory is sequence and ITA_DFLT_Win_Template_Dest_Directory is not string else [ITA_DFLT_Win_Template_Dest_Directory]
        )
      | list
    }}
```
