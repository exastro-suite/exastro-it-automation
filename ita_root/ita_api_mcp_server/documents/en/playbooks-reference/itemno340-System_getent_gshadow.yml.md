# Ansible Legacy Default Playbook - System_getent_gshadow.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 340
- **playbook_name**: ~[Exastro standard] Get entry(gshadow)
- **playbook_file**: System_getent_gshadow.yml
## Overview
Queries the target's `gshadow` database with the `getent` module, registering the shadowed group password entries in `ITA_DFLT_getent_gshadow`; `no_log: true` hides the sensitive output.
## Description
This Playbook file has no parameters. It always queries the fixed "gshadow" database of the Target host (/etc/gshadow), i.e. the shadowed group password file holding group encrypted passwords, administrators and members.
The retrieved entries are stored in the registered variable "ITA_DFLT_getent_gshadow", so they are available to later tasks in the same Movement.
Because the data is confidential, the task sets "no_log: true" and the retrieved values are therefore not written to the execution log (change it to false when debugging).
## Keyword
- /etc/gshadow
- NSS name service switch lookup
- group account security audit
- credential inventory collection
## Playbook
```yaml
- name: A wrapper to the unix getent utility (gshadow)
  ansible.builtin.getent:
    database: gshadow
  register: ITA_DFLT_getent_gshadow
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）
```
