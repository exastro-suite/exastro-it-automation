# Ansible Legacy Default Playbook - Files_lineinfile.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 660
- **playbook_name**: ~[Exastro standard] Text line operation
- **playbook_file**: Files_lineinfile.yml
## Overview
Uses `lineinfile` to make the line matching `ITA_DFLT_regexp` in `ITA_DFLT_file_path` equal to `ITA_DFLT_line_string`, or to delete it when state is absent; state defaults to present.
## Description
"ITA_DFLT_file_path": Path of the file on the target node to be edited.
"ITA_DFLT_regexp": Regular expression used to locate the line to act on. With state "present" the last matching line is rewritten, and when nothing matches the line is appended to the file.
"ITA_DFLT_line_string": The exact line to insert or to replace the matched line with.
"ITA_DFLT_line_state": Either "present" to ensure the line exists or "absent" to remove matching lines. Optional - defaults to "present".
The first three variables are referenced without a default, so all of them must be supplied; only one file and one line are handled per run because the task has no loop.
## Keyword
- change a setting in a config file
- replace a line matching a regex
- append a line if missing
- sed-style file edit
## Playbook
```yaml
- name: Insert or replace text lines.
  ansible.builtin.lineinfile:
    path: "{{ ITA_DFLT_file_path }}"
    regexp: "{{ ITA_DFLT_regexp }}"
    line: "{{ ITA_DFLT_line_string }}"
    state: "{{ ITA_DFLT_line_state | default('present') }}"
```
