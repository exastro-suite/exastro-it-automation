# Ansible Legacy Default Playbook - Files_fetch.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 250
- **playbook_name**: ~[Exastro standard] Fetch files
- **playbook_file**: Files_fetch.yml
## Overview
Fetches every file in `ITA_DFLT_Target_File_Name` from the target nodes into __workflowdir__ using `fetch`, registering `ITA_RGST_Fetch_Result` and dumping it with `debug`.
## Description
This Playbook file stores files specified by "ITA_DFLT_Target_File_Name" to "__workflowdir__".
"ITA_DFLT_Target_File_name" can specify multiple files (list type).
Files stored in "__workflowdir__" can be retrieved as result data after the Movement ends.
The task results are displayed at debug level 3 (-vvv).
## Keyword
- collect logs from servers
- download a file from a managed node
- gather evidence files to the controller
- configuration backup retrieval
## Playbook
```yaml
# This Playbook file stores files specified by "ITA_DFLT_Target_File_Name" to "__workflowdir__".
# "ITA_DFLT_Target_File_name" can specify multiple files (list type).
# Files stored in "__workflowdir__" can be retrieved as result data after the Movement ends.
# The task results are displayed at debug level 3 (-vvv).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Target_File_Name: "{{ ITA_DFLT_Target_File_Name }}"
  when: ITA_DFLT_Target_File_Name is defined

- name: Fetch files from remote nodes
  ansible.builtin.fetch:
    src: "{{ item }}"
    dest: "{{ __workflowdir__ }}"
  loop: >-
    {{
      ITA_DFLT_Target_File_Name if ITA_DFLT_Target_File_Name is sequence and ITA_DFLT_Target_File_Name is not string else [ITA_DFLT_Target_File_Name]
    }}
  register: ITA_RGST_Fetch_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_Fetch_Result
    verbosity: 3

```
