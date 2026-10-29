# Ansible Legacy Default Playbook - Commands_command.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 580
- **playbook_name**: ~[Exastro standard] Run command
- **playbook_file**: Commands_command.yml
## Overview
Passes the string in `ITA_DFLT_Command_String` to the `command` module to run it on each target node, registers the output as `ITA_RGST_Command_Result` and prints it with `debug`.
## Description
This Playbook file is simple.
It passes the variable given string, "ITA_DFLT_Command_String", to the Ansible command module and executes it.
The task results are displayed at debug level 3 (-vvv).
## Keyword
- remote command execution
- run OS command on managed node
- command without shell interpretation
- capture command stdout
## Playbook
```yaml
# This Playbook file is simple. 
# It passes the variable given string, "ITA_DFLT_Command_String", to the Ansible command module and executes it.
# The task results are displayed at debug level 3 (-vvv).
- name: Execute commands on targets
  ansible.builtin.command: "{{ ITA_DFLT_Command_String }}"
  register: ITA_RGST_Command_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_Command_Result
    verbosity: 3

```
