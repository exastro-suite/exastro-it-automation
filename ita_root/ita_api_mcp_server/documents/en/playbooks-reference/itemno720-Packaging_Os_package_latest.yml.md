# Ansible Legacy Default Playbook - Packaging_Os_package_latest.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 720
- **playbook_name**: ~[Exastro standard] Update package
- **playbook_file**: Packaging_Os_package_latest.yml
## Overview
Updates software to its latest version with the generic `package` module (`state: latest`), which dispatches to the host's own package manager, looping over `ITA_DFLT_Update_Target_packages`.
## Description
"ITA_DFLT_Update_Target_packages": Name of the package to be updated to the latest available version on the target host.
This variable can hold multiple values at the same time (list type) and each value is updated in turn; when a single string is given it is wrapped into a one-element list first, so either form is accepted. Because the generic `package` module is used instead of a distribution-specific one, the update is performed by whichever package manager Ansible detects on the target host (dnf, yum, apt, zypper, and so on), and the same Playbook can therefore be reused across different operating systems.
## Keyword
- cross-distribution package upgrade
- apply patches on any Linux
- automatic package manager detection
- software version refresh
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Update_Target_packages: "{{ ITA_DFLT_Update_Target_packages }}"
  when: ITA_DFLT_Update_Target_packages is defined

- name: Update packages with the generic OS package manager
  ansible.builtin.package:
    name: "{{ item }}"
    state: latest
  loop: >-
    {{
      ITA_DFLT_Update_Target_packages if ITA_DFLT_Update_Target_packages is sequence and ITA_DFLT_Update_Target_packages is not string else [ITA_DFLT_Update_Target_packages]
    }}
```
