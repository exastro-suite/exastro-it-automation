# Ansible Legacy Default Playbook - Files_copy_workdir-copy-wd-to-cwd.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 70
- **playbook_name**: ~[Exastro standard] Copy directory (WD to CWD)
- **playbook_file**: Files_copy_workdir-copy-wd-to-cwd.yml
## Overview
Runs `copy` delegated to localhost to copy the entire contents of __workflowdir__ into __conductor_workflowdir__; it references no user-settable variables.
## Description
This Playbook file copies files stored in "__workflowdir__" to "__conductor_workflowdir__".
 The "__conductor_workflowdir__" files are accesible from subsequent Movements are the Movement ends.
Use this for transfering information over Movements.
Note that as this Playbook file does not contain variables that can be externally controlled, we do not recommend using it linked to a Movement alone, but together with other Playbook files.
## Keyword
- pass data between Conductor nodes
- work directory handover
- share artifacts across Movements
- localhost delegation
## Playbook
```yaml
# This Playbook file copies files stored in "__workflowdir__" to "__conductor_workflowdir__".
# The "__conductor_workflowdir__" files are accesible from subsequent Movements are the Movement ends.
# Use this for transfering information over Movements.
# Note that as this Playbook file does not contain variables that can be externally controlled, we do not recommend using it linked to a Movement alone, but together with other Playbook files.
- name: Copy data from workdir to conductor_workdir
  ansible.builtin.copy:
    src: "{{ __workflowdir__ }}/"
    dest: "{{ __conductor_workflowdir__ }}/"
  delegate_to: localhost
```
