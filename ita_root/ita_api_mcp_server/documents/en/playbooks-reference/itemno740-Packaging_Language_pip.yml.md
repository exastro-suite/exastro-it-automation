# Ansible Legacy Default Playbook - Packaging_Language_pip.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 740
- **playbook_name**: ~[Exastro standard] pip
- **playbook_file**: Packaging_Language_pip.yml
## Overview
Installs Python packages with the `pip` module, looping over the values of `ITA_DFLT_Target_Package_Name`, which is first normalised so that either a single string or a list can be supplied.
## Description
This Playbook file installs package names specified by "ITA_DFLT_Target_Package_Name".
Nothing will happen if the specified package names are already installed.
"ITA_DFLT_Target_Package_Name" can specify multiple package names (list type).
## Keyword
- Python library dependencies
- PyPI module installation
- Python runtime environment setup
- idempotent library install
## Playbook
```yaml
# This Playbook file installs package names specified by "ITA_DFLT_Target_Package_Name".
# Nothing will happen if the specified package names are already installed.
# "ITA_DFLT_Target_Package_Name" can specify multiple package names (list type).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Target_Package_Name: "{{ ITA_DFLT_Target_Package_Name }}"
  when: ITA_DFLT_Target_Package_Name is defined

- name: Manages Python library dependencies
  ansible.builtin.pip:
    name: "{{ item }}"
  loop: >-
    {{
      ITA_DFLT_Target_Package_Name if ITA_DFLT_Target_Package_Name is sequence and ITA_DFLT_Target_Package_Name is not string else [ITA_DFLT_Target_Package_Name]
    }}
```
