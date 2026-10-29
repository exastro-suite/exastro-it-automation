# Ansible Legacy Default Playbook - Commands_script.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 670
- **playbook_name**: ~[Exastro standard] Transfer/Run script
- **playbook_file**: Commands_script.yml
## Overview
Uses the `script` module to copy the local script `ITA_DFLT_Script_Name` to the node and run it with __workflowdir__ and __conductor_workflowdir__ as its two arguments; registers the result.
## Description
This Playbook file transfers and executes script files specified by the "ITA_DFLT_Script_Name".
Doing so adds the following two arguments to the script file, allowing them to be used within said script.
First argument: __workflowdir__
Second argument: __conductor_workflowdir__
For example, if a file is output to "__workflowdir__" while the script is processing, the user will be able to retrieve it as result data after the Movement ends.
Similarly, by outputting a file to __conductor_workflowdir__ as a process within the script, it is possible to convey information to subsequent Movemenet after the Movement ends.
However, these functions are only enabled when running scripts on a nodes that has access to __workflowdir__ and __conductor_workflowdir__ (e.g. localhost).
The task results are displayed at debug level 3 (-vvv).
## Keyword
- run shell script on remote host
- pass arguments to a script
- share files between Movements
- shell script execution
## Playbook
```yaml
# This Playbook file transfers and executes script files specified by the "ITA_DFLT_Script_Name".
# Doing so adds the following two arguments to the script file, allowing them to be used within said script.
#  First argument: __workflowdir__
#  Second argument: __conductor_workflowdir__
# For example, if a file is output to "__workflowdir__" while the script is processing, the user will be able to retrieve it as result data after the Movement ends.
# Similarly, by outputting a file to __conductor_workflowdir__ as a process within the script, it is possible to convey information to subsequent Movemenet after the Movement ends.
# However, these functions are only enabled when running scripts on a nodes that has access to __workflowdir__ and __conductor_workflowdir__ (e.g. localhost).
# The task results are displayed at debug level 3 (-vvv).
- name: Run a script with arguments
  ansible.builtin.script: "{{ ITA_DFLT_Script_Name }} {{ __workflowdir__ }} {{ __conductor_workflowdir__ }}"
  register: ITA_RGST_Script_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_Script_Result
    verbosity: 3

```
