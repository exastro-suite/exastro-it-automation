# Ansible Legacy Default Playbook - Files_find.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 270
- **playbook_name**: ~[Exastro standard] Find file list
- **playbook_file**: Files_find.yml
## Overview
Searches each directory in `ITA_DFLT_Target_Path` with the `find` module using a regex name pattern plus age and file-type filters, recursing by default, and always prints the hits.
## Description
"ITA_DFLT_Target_Path": Directory to be searched. Multiple directories can be specified at the same time (list type); the task loops over each one, and a single scalar value is automatically treated as a one-element list.
"ITA_DFLT_Age": Age filter handed to the find module, for example "7d" for entries older than seven days or "-1w" for ones newer than a week. Optional - defaults to "0s", which selects entries of any age.
"ITA_DFLT_File_Type": Kind of entry to return: "file", "directory", "link" or "any". Optional - defaults to "any".
"ITA_DFLT_Name_Pattern": Pattern matched against entry names. use_regex is fixed to true, so this is always interpreted as a regular expression, not a shell glob. Optional - defaults to ".*", which matches everything.
"ITA_DFLT_Recurse": Whether to descend into subdirectories. Optional - defaults to true.
Only "ITA_DFLT_Target_Path" has to be supplied; every other variable falls back to its default.
The search results for all directories are stored in the registered variable "ITA_RGST_File_Lists", which later tasks can reference, and a debug task prints that variable unconditionally (verbosity 0) so the file list always appears in the execution log.
## Keyword
- search files by pattern
- list old files for cleanup
- regular expression filename search
- file inventory audit
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Target_Path: "{{ ITA_DFLT_Target_Path }}"
  when: ITA_DFLT_Target_Path is defined

- name: Return a list of files based on specific criteria
  ansible.builtin.find:
    age: "{{ ITA_DFLT_Age | default('0s') }}"
    file_type: "{{ ITA_DFLT_File_Type | default('any') }}"
    paths: "{{ item }}"
    patterns:
      - "{{ ITA_DFLT_Name_Pattern | default('.*') }}"
    recurse: "{{ ITA_DFLT_Recurse | default(true) }}"
    use_regex: true
  loop: >-
    {{
      ITA_DFLT_Target_Path if ITA_DFLT_Target_Path is sequence and ITA_DFLT_Target_Path is not string else [ITA_DFLT_Target_Path]
    }}
  register: ITA_RGST_File_Lists

- name: Print a list of files
  ansible.builtin.debug:
    var: ITA_RGST_File_Lists
    verbosity: 0
```
