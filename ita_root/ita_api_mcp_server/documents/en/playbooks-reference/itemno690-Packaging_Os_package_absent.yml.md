# Ansible Legacy Default Playbook - Packaging_Os_package_absent.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 690
- **playbook_name**: ~[Exastro standard] Uninstall package
- **playbook_file**: Packaging_Os_package_absent.yml
## Overview
Uninstalls software with the generic `package` module (`state: absent`), which dispatches to whichever package manager the host uses, looping over `ITA_DFLT_Uninstall_Target_packages`.
## Description
"ITA_DFLT_Uninstall_Target_packages": Name of the package to be removed from the target host.
This variable can hold multiple values at the same time (list type) and each value is removed in turn; when a single string is given it is wrapped into a one-element list first, so either form is accepted. Because the generic `package` module is used instead of a distribution-specific one, the removal is carried out by whichever package manager Ansible detects on the target host (dnf, yum, apt, zypper, and so on), and the same Playbook can therefore be reused across different operating systems.
## Keyword
- OS-agnostic package removal
- erase software on any Linux
- automatic package manager detection
- mixed distribution fleet
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Uninstall_Target_packages: "{{ ITA_DFLT_Uninstall_Target_packages }}"
  when: ITA_DFLT_Uninstall_Target_packages is defined

- name: Uninstall packages with the generic OS package manager
  ansible.builtin.package:
    name: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Uninstall_Target_packages if ITA_DFLT_Uninstall_Target_packages is sequence and ITA_DFLT_Uninstall_Target_packages is not string else [ITA_DFLT_Uninstall_Target_packages]
    }}
```
