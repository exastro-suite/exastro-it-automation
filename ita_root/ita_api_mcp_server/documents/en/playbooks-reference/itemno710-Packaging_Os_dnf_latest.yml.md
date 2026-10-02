# Ansible Legacy Default Playbook - Packaging_Os_dnf_latest.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 710
- **playbook_name**: ~[Exastro standard] Update dnf
- **playbook_file**: Packaging_Os_dnf_latest.yml
## Overview
Upgrades packages to the newest available version with the `dnf` module and `state: latest`, looping over `ITA_DFLT_Update_Target_packages`; the registered result is printed at verbosity 3.
## Description
This Playbook file updates packages specified by "ITA_DFLT_Update_Target_packages" to the latest version available.
"ITA_DFLT_Update_Target_packages" can specify multiple files (list type).
The task results are displayed at debug level 3 (-vvv).
## Keyword
- RPM upgrade on RHEL
- apply security patches
- yum family package manager
- keep middleware current
## Playbook
```yaml
# This Playbook file updates packages specified by "ITA_DFLT_Update_Target_packages" to the latest version available.
# "ITA_DFLT_Update_Target_packages" can specify multiple files (list type).
# The task results are displayed at debug level 3 (-vvv).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Update_Target_packages: "{{ ITA_DFLT_Update_Target_packages }}"
  when: ITA_DFLT_Update_Target_packages is defined

- name: Update packages with the dnf package manager
  ansible.builtin.dnf:
    name: "{{ item }}"
    state: latest
  loop: >-
    {{
      ITA_DFLT_Update_Target_packages if ITA_DFLT_Update_Target_packages is sequence and ITA_DFLT_Update_Target_packages is not string else [ITA_DFLT_Update_Target_packages]
    }}
  register: ITA_RGST_DnfUpdate_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_DnfUpdate_Result
    verbosity: 3

```
