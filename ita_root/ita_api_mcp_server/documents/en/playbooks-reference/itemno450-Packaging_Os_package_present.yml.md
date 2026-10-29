# Ansible Legacy Default Playbook - Packaging_Os_package_present.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 450
- **playbook_name**: ~[Exastro standard] Install package
- **playbook_file**: Packaging_Os_package_present.yml
## Overview
Installs software with the generic `package` module (`state: present`), letting Ansible choose the host's own package manager, looping over the values of `ITA_DFLT_Install_Target_packages`.
## Description
"ITA_DFLT_Install_Target_packages": Name of the package to be installed on the target host.
This variable can hold multiple values at the same time (list type) and each value is installed in turn; when a single string is given it is wrapped into a one-element list first, so either form is accepted. Because the generic `package` module is used instead of a distribution-specific one, the installation is performed by whichever package manager Ansible detects on the target host (dnf, yum, apt, zypper, and so on), and nothing happens for packages that are already present.
## Keyword
- cross-distribution software install
- install package on any Linux
- automatic package manager detection
- server build out
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Install_Target_packages: "{{ ITA_DFLT_Install_Target_packages }}"
  when: ITA_DFLT_Install_Target_packages is defined

- name: Install packages with the generic OS package manager
  ansible.builtin.package:
    name: "{{ item }}"
    state: present
  loop: >-
    {{
      ITA_DFLT_Install_Target_packages if ITA_DFLT_Install_Target_packages is sequence and ITA_DFLT_Install_Target_packages is not string else [ITA_DFLT_Install_Target_packages]
    }}
```
