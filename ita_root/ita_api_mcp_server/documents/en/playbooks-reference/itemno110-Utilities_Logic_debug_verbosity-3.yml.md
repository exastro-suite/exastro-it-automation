# Ansible Legacy Default Playbook - Utilities_Logic_debug_verbosity-3.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 110
- **playbook_name**: ~[Exastro standard] Debug message (-vvv display)
- **playbook_file**: Utilities_Logic_debug_verbosity-3.yml
## Overview
Prints the variable named in `ITA_DFLT_Debug_Target` using `ansible.builtin.debug` with `verbosity: 3`, so the value is shown only when the run is executed with -vvv or higher.
## Description
"ITA_DFLT_Debug_Target": Name of the variable whose contents are to be output. The value is passed to the debug module's "var" option, so specify the variable name itself rather than a message string.
The debug task sets verbosity to 3, so the output is suppressed during a normal run and appears only when Ansible is executed with the -vvv option or a higher verbosity level. This makes the playbook suitable for investigation output that should not clutter ordinary execution logs.
The playbook consists of this single task, takes no other parameters, and does not register any variable.
## Keyword
- show output only with -vvv
- verbose logging level
- inspect a variable value
- troubleshooting a playbook
- suppress output in normal runs
## Playbook
```yaml
- name: Print statements during execution
  ansible.builtin.debug:
    var: "{{ ITA_DFLT_Debug_Target }}"
    verbosity: 3
```
