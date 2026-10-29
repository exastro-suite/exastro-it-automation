# Ansible Legacy Default Playbook - Utilities_Logic_pause_in-minutes.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 590
- **playbook_name**: ~[Exastro standard] Sleep (minutes)
- **playbook_file**: Utilities_Logic_pause_in-minutes.yml
## Overview
Pauses the playbook run with the `ansible.builtin.pause` module for the number of minutes specified, via the module's `minutes` option.
## Description
This Playbook file uses the time specified in "ITA_DFLT_Sleep_Minutes" to pause (sleep) Jobs and Jobflows.
## Keyword
- Wait between job steps
- Delay workflow execution
- Sleep timer in Jobflow
- Throttle automation timing
## Playbook
```yaml
# This Playbook file uses the time specified in "ITA_DFLT_Sleep_Minutes" to pause (sleep) Jobs and Jobflows.
- name: pause
  ansible.builtin.pause:
    minutes: "{{ ITA_DFLT_Sleep_Minutes }}"

```
