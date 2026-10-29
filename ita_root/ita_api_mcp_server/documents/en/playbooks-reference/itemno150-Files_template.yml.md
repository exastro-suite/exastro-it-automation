# Ansible Legacy Default Playbook - Files_template.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 150
- **playbook_name**: ~[Exastro standard] Deploy template file
- **playbook_file**: Files_template.yml
## Overview
Renders each Jinja2 template in `ITA_DFLT_Template_Src_Files` with the `template` module and writes the result to the positionally paired path in `ITA_DFLT_Template_Dest_Files`.
## Description
This Playbook file deploys Templates specified by "ITA_DFLT_Template_Src_Files" to files specified by "ITA_DFLT_Template_Dest_Files".
"ITA_DFLT_Template_Src_Files" can specify multiple templates (list type).
"ITA_DFLT_Template_Dest_Files" can specify multiple files (list type).
## Keyword
- generate a config file from a template
- Jinja2 variable substitution
- parameterised configuration deployment
- per-host configuration generation
## Playbook
```yaml
- name: Ensure ITA_DFLT_Template_Src_Files is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Template_Src_Files: "{{ ITA_DFLT_Template_Src_Files }}"
  when: ITA_DFLT_Template_Src_Files is defined

- name: Ensure ITA_DFLT_Template_Dest_Files is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Template_Dest_Files: "{{ ITA_DFLT_Template_Dest_Files }}"
  when: ITA_DFLT_Template_Dest_Files is defined

- name: Create template files
  ansible.builtin.template:
    src: "{{ item[0] }}"
    dest: "{{ item[1] }}"
  loop: >-
    {{
      (ITA_DFLT_Template_Src_Files if ITA_DFLT_Template_Src_Files is sequence and ITA_DFLT_Template_Src_Files is not string else [ITA_DFLT_Template_Src_Files])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Template_Dest_Files if ITA_DFLT_Template_Dest_Files is sequence and ITA_DFLT_Template_Dest_Files is not string else [ITA_DFLT_Template_Dest_Files]
        )
      | list
    }}
```
