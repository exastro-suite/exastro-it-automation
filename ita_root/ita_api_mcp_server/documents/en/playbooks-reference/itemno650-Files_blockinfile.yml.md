# Ansible Legacy Default Playbook - Files_blockinfile.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 650
- **playbook_name**: ~[Exastro standard] Text block operation
- **playbook_file**: Files_blockinfile.yml
## Overview
Uses `blockinfile` to insert, replace or remove a marker-delimited text block in the file given by `ITA_DFLT_file_path`; marker, anchor and block body are optional, and state defaults to present.
## Description
"ITA_DFLT_file_path": Path of the file on the target node to be edited. This is the only variable with no default, so it must always be given.
"ITA_DFLT_block_marker": Marker line template used to delimit the managed block (it must contain {mark}). Optional - when not given the option is omitted and the blockinfile module's own default marker ("# BEGIN/END ANSIBLE MANAGED BLOCK") is used.
"ITA_DFLT_block_state": Either "present" to insert/update the block or "absent" to delete it. Defaults to "present".
"ITA_DFLT_insertafter": Regular expression (or "EOF"/"BOF") indicating the position after which the block is inserted. Optional - when not given the option is omitted and the block is placed at the end of the file.
"ITA_DFLT_block_string": The multi-line text written between the markers. Optional - when omitted with state "present" an empty block containing only the markers is produced.
Because the block is identified by its markers, re-running the Playbook file updates the existing block instead of appending a duplicate.
## Keyword
- edit configuration file idempotently
- Ansible managed block in config file
- multi-line text insertion
- remove a text block from a file
## Playbook
```yaml
- name: Insert or replace text blocks.
  ansible.builtin.blockinfile:
    path: "{{ ITA_DFLT_file_path }}"
    marker: "{{ ITA_DFLT_block_marker | default(omit) }}"
    state: "{{ ITA_DFLT_block_state | default('present') }}"
    insertafter: "{{ ITA_DFLT_insertafter | default(omit) }}"
    block: "{{ ITA_DFLT_block_string | default(omit) }}"
```
