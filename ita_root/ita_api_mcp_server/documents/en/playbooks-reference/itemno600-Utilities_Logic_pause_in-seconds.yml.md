# Ansible Legacy Default Playbook - Utilities_Logic_pause_in-seconds.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 600
- **playbook_name**: ~[Exastro standard] Sleep (seconds)
- **playbook_file**: Utilities_Logic_pause_in-seconds.yml
## Overview
Pauses the playbook run with the `ansible.builtin.pause` module for the number of seconds specified, via the module's `seconds` option.
## Description
This Playbook file uses the time specified in "ITA_DFLT_Sleep_Seconds" to pause (sleep) Jobs and Jobflows.
## Keyword
- Short wait between tasks
- Delay execution by seconds
- Sleep timer in Jobflow
- Brief pause before next step
## Playbook
```yaml
# This Playbook file uses the time specified in "ITA_DFLT_Sleep_Seconds" to pause (sleep) Jobs and Jobflows.
- name: pause
  ansible.builtin.pause:
    seconds: "{{ ITA_DFLT_Sleep_Seconds }}"

```
