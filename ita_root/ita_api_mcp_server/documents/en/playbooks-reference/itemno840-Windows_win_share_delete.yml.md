# Ansible Legacy Default Playbook - Windows_win_share_delete.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 840
- **playbook_name**: ~[Exastro standard][Win] Delete shared settings
- **playbook_file**: Windows_win_share_delete.yml
## Overview
Removes Windows SMB shares with `win_share` and `state: absent`, looping over each supplied share name; the underlying folder itself is kept.
## Description
This Playbook file deletes shared names specified by "ITA_DFLY_Share_Name".
"ITA_DFLT_Share_Name" can specify multiple share names (list type).
## Keyword
- SMB share removal
- Unshare a Windows folder
- Stop network sharing
- Decommission a file share
## Playbook
```yaml
# This Playbook file deletes shared names specified by "ITA_DFLY_Share_Name".
# "ITA_DFLT_Share_Name" can specify multiple share names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Share_Name: "{{ ITA_DFLT_Share_Name }}"
  when: ITA_DFLT_Share_Name is defined

- name: delete Windows shares
  ansible.windows.win_share:
    name: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Share_Name if ITA_DFLT_Share_Name is sequence and ITA_DFLT_Share_Name is not string else [ITA_DFLT_Share_Name]
    }}
```
