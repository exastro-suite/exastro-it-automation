# Ansible Legacy Default Playbook - Windows_win_updates_partial.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1070
- **playbook_name**: ~[Exastro standard][Win] Update (partial)
- **playbook_file**: Windows_win_updates_partial.yml
## Overview
Installs only the updates whose title or KB matches the accept list, via `win_updates` with `category_names: '*'` filtered by `accept_list` and `reboot: true` for automatic restart.
## Description
This Playbook material installs a list of update titles or KB numbers specified in "ITA_DFLT_Win_Update_Accept_List".
Note that this Platbook file specifies "category_names" with "＊".
"ITA_DFLT_Win_Update_Accept_List" can specify multiple items (list type).
## Keyword
- Selective patching
- Install a specific KB number
- Targeted hotfix deployment
- Update allowlist filter
## Playbook
```yaml
# This Playbook material installs a list of update titles or KB numbers specified in "ITA_DFLT_Win_Update_Accept_List".
# Note that this Platbook file specifies "category_names" with "＊".
# "ITA_DFLT_Win_Update_Accept_List" can specify multiple items (list type).
- name: Download and install Windows updates and restart（partial）
  ansible.windows.win_updates:
    category_names: '*'
    accept_list: "{{ ITA_DFLT_Win_Update_Accept_List }}"
    reboot: true
```
