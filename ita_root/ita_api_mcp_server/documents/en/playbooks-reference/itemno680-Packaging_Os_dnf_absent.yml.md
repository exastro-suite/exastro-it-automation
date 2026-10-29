# Ansible Legacy Default Playbook - Packaging_Os_dnf_absent.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 680
- **playbook_name**: ~[Exastro standard] Uninstall dnf
- **playbook_file**: Packaging_Os_dnf_absent.yml
## Overview
Removes packages from a Red Hat-family host with the `dnf` module and `state: absent`, looping over `ITA_DFLT_Uninstall_Target_packages`; the registered result is printed at verbosity 3.
## Description
This Playbook file uninstalls packages specified by "ITA_DFLT_Uninstall_Target_packages".
"ITA_DFLT_Uninstall_Target_packages" can specify multiple packages (list type).
The task results are displayed at debug level 3 (-vvv).

## Keyword
- RPM package removal on RHEL
- erase installed software
- yum family package manager
- clean up unused middleware
## Playbook
```yaml
# This Playbook file uninstalls packages specified by "ITA_DFLT_Uninstall_Target_packages".
# "ITA_DFLT_Uninstall_Target_packages" can specify multiple packages (list type).
# The task results are displayed at debug level 3 (-vvv).
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Uninstall_Target_packages: "{{ ITA_DFLT_Uninstall_Target_packages }}"
  when: ITA_DFLT_Uninstall_Target_packages is defined

- name: Uninstall packages with the dnf package manager
  ansible.builtin.dnf:
    name: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Uninstall_Target_packages if ITA_DFLT_Uninstall_Target_packages is sequence and ITA_DFLT_Uninstall_Target_packages is not string else [ITA_DFLT_Uninstall_Target_packages]
    }}
  register: ITA_RGST_DnfUninstall_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_DnfUninstall_Result
    verbosity: 3
```
