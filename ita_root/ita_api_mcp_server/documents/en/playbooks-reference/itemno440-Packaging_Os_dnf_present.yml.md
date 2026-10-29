# Ansible Legacy Default Playbook - Packaging_Os_dnf_present.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 440
- **playbook_name**: ~[Exastro standard] Install dnf
- **playbook_file**: Packaging_Os_dnf_present.yml
## Overview
Ensures packages exist on a Red Hat-family host using the `dnf` module with `state: present`, looping over `ITA_DFLT_Install_Target_packages`; the registered result is printed at verbosity 3.
## Description
This Playbook file installs packages specified by "ITA_DFLT_Install_Target_packages".
"ITA_DFLT_Install_Target_packages" can specify multiple files (list type).
The task results are displayed at debug level 3 (-vvv).
## Keyword
- RPM installation on RHEL
- yum family package manager
- middleware provisioning
- idempotent package presence
## Playbook
```yaml
# This Playbook file installs packages specified by "ITA_DFLT_Install_Target_packages".
# "ITA_DFLT_Install_Target_packages" can specify multiple files (list type).
# The task results are displayed at debug level 3 (-vvv).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Install_Target_packages: "{{ ITA_DFLT_Install_Target_packages }}"
  when: ITA_DFLT_Install_Target_packages is defined

- name: Install packages with the dnf package manager
  ansible.builtin.dnf:
    name: "{{ item }}"
    state: present
  loop: >-
    {{
      ITA_DFLT_Install_Target_packages if ITA_DFLT_Install_Target_packages is sequence and ITA_DFLT_Install_Target_packages is not string else [ITA_DFLT_Install_Target_packages]
    }}
  register: ITA_RGST_DnfInstall_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_DnfInstall_Result
    verbosity: 3

```
