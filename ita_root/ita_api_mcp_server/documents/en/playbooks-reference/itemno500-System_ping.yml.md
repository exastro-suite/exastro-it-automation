# Ansible Legacy Default Playbook - System_ping.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 500
- **playbook_name**: ~[Exastro standard] Ping
- **playbook_file**: System_ping.yml
## Overview
Calls the `ping` module with no options, verifying that the target host is reachable and that a working Python interpreter answers; it takes no parameters and changes nothing.
## Description
This Playbook file connects to the Target host and checks for usable Python.
Note that as this Playbook file does not contain variables that can be externally controlled, we do not recommend using it linked to a Movement alone, but together with other Playbook files.
## Keyword
- connectivity health check
- pre-flight smoke test
- verify managed node readiness
- troubleshoot unreachable host
- no-op idempotent test
## Playbook
```yaml
# This Playbook file connects to the Target host and checks for usable Python.
# Note that as this Playbook file does not contain variables that can be externally controlled, we do not recommend using it linked to a Movement alone, but together with other Playbook files.
- name: ping
  ansible.builtin.ping:

```
