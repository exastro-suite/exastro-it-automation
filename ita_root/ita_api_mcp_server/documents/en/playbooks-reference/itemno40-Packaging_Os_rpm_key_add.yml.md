# Ansible Legacy Default Playbook - Packaging_Os_rpm_key_add.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 40
- **playbook_name**: ~[Exastro standard] Add RPM key
- **playbook_file**: Packaging_Os_rpm_key_add.yml
## Overview
Imports GPG keys into the RPM keyring with the `rpm_key` module and `state: present`, looping over each value of `ITA_DFLT_Gpg_Keys` (a key URL, local file path, or key ID).
## Description
This Playbook file registers GPG keys specified by "ITA_DFLT_Gpg_Keys" to the RPM database.
"ITA_DFLT_Gpg_Keys" can specify multiple GPG keys (list type).
## Keyword
- trust repository signing key
- import public key for yum
- RPM signature verification
- prepare repository before install
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Gpg_Keys: "{{ ITA_DFLT_Gpg_Keys }}"
  when: ITA_DFLT_Gpg_Keys is defined

- name: Add gpg key
  ansible.builtin.rpm_key:
    key: "{{ item }}"
    state: present
  loop: >-
    {{
      ITA_DFLT_Gpg_Keys if ITA_DFLT_Gpg_Keys is sequence and ITA_DFLT_Gpg_Keys is not string else [ITA_DFLT_Gpg_Keys]
    }}
```
