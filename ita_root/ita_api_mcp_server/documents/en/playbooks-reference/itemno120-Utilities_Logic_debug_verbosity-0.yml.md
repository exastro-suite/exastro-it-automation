# Ansible Legacy Default Playbook - Utilities_Logic_debug_verbosity-0.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 120
- **playbook_name**: ~[Exastro standard] Debug message (constant output)
- **playbook_file**: Utilities_Logic_debug_verbosity-0.yml
## Overview
Searches each path in `ITA_DFLT_Target_Path` with `ansible.builtin.find` (regex patterns, age and recurse filters), registers the result as `output`, and prints it with `debug` at `verbosity: 0`.
## Description
"ITA_DFLT_Target_Path": Directory to be searched. Multiple values can be specified at the same time (list type), and the find task is executed once per path.
"ITA_DFLT_Age": Age condition passed to the find module (for example "7d" for items older than seven days). Optional; defaults to "0s", which matches items of any age.
"ITA_DFLT_Name_Pattern": Pattern that the name must match. Optional; defaults to ".*" so that everything matches. Because use_regex is set to true, the value is interpreted as a regular expression, not as a shell glob.
"ITA_DFLT_Recurse": Whether subdirectories are searched as well. Optional; defaults to true.
file_type is fixed to "any", so regular files, directories and links are all returned. The search result is stored by register under the name "output", which later tasks can reference, and is then printed by a debug task with verbosity 0, meaning the result is always displayed even without any -v option.
## Keyword
- always display debug output
- list files matching a condition
- file inventory dump
- regular expression file search
- audit directory contents
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Target_Path: "{{ ITA_DFLT_Target_Path }}"
  when: ITA_DFLT_Target_Path is defined

- name: Return a list of files based on specific criteria
  ansible.builtin.find:
    age: "{{ ITA_DFLT_Age | default('0s') }}"
    file_type: any
    paths: "{{ item }}"
    patterns:
      - "{{ ITA_DFLT_Name_Pattern | default('.*') }}"
    recurse: "{{ ITA_DFLT_Recurse | default(true) }}"
    use_regex: true
  loop: >-
    {{
      ITA_DFLT_Target_Path if ITA_DFLT_Target_Path is sequence and ITA_DFLT_Target_Path is not string else [ITA_DFLT_Target_Path]
    }}
  register: output

- name: Print statements during execution
  ansible.builtin.debug:
    var: output
    verbosity: 0
```
