# Ansible Legacy Default Playbook - System_getent_aliases.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 310
- **playbook_name**: ~[Exastro standard] Get entry(aliases)
- **playbook_file**: System_getent_aliases.yml
## Overview
Uses the `getent` module on the `aliases` database to enumerate the mail alias entries defined on the host, registering the output as `ITA_DFLT_getent_aliases`.
## Description
This Playbook file takes no parameters. The database name `aliases` is fixed in the task and no key is specified, so every mail alias entry the host publishes (normally the contents of /etc/aliases) is enumerated, each alias with its expansion targets.
The lookup result is stored with `register` under the name "ITA_DFLT_getent_aliases", so later tasks in the same run can reference it; the module also sets the collected entries as the fact `getent_aliases`.
## Keyword
- mail alias list
- etc aliases inventory
- sendmail or postfix alias audit
- mail forwarding destinations
## Playbook
```yaml
- name: A wrapper to the unix getent utility (aliases)
  ansible.builtin.getent:
    database: aliases
  register: ITA_DFLT_getent_aliases
```
