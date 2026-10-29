# Ansible Legacy Default Playbook - Net_Tools_Basics_slurp.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 460
- **playbook_name**: ~[Exastro standard] Load file
- **playbook_file**: Net_Tools_Basics_slurp.yml
## Overview
Reads the single file named by `ITA_DFLT_Target_File` from the target node with the `slurp` module and stores its Base64-encoded content in the registered variable `ITA_DFLT_Files_text`.
## Description
"ITA_DFLT_Target_File": Path of the file on the target node to be read. Only one file can be given, because the task has no loop.
The slurp module returns the file content Base64-encoded, and it is kept in the registered variable "ITA_DFLT_Files_text", which later tasks can reference; apply the b64decode filter to the "content" field of that variable when the plain text is needed.
The file is only read and never modified, so this Playbook file is typically combined with other Playbook files that act on the retrieved content.
## Keyword
- read file contents into a variable
- inspect configuration file content
- base64 decode file content
- capture file text for a later task
## Playbook
```yaml
- name: Slurps a file from remote nodes
  ansible.builtin.slurp:
    src: "{{ ITA_DFLT_Target_File }}"
  register: ITA_DFLT_Files_text
```
