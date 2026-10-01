# Ansible Legacy Default Playbook - Packaging_Os_rpm_key_remove.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 530
- **playbook_name**: ~[Exastro standard] Remove RPM key
- **playbook_file**: Packaging_Os_rpm_key_remove.yml
## Overview
Deletes trusted GPG keys from the RPM keyring with the `rpm_key` module and `state: absent`, looping over each value of `ITA_DFLT_Gpg_Key_Ids`.
## Description
This Playbok file deletes GPG keys specified by "ITA_DFLT_Gpg_Keys" from the RPM database.
"ITA_DFLT_Gpg_Keys" can specify multiple GPG keys (list type).
## Keyword
- untrust repository signing key
- remove public key from yum
- revoke RPM signing key
- keyring cleanup
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Gpg_Key_Ids: "{{ ITA_DFLT_Gpg_Key_Ids }}"
  when: ITA_DFLT_Gpg_Key_Ids is defined

- name: Remove gpg key
  ansible.builtin.rpm_key:
    key: "{{ item }}"
    state: absent
  loop: >-
    {{
      ITA_DFLT_Gpg_Key_Ids if ITA_DFLT_Gpg_Key_Ids is sequence and ITA_DFLT_Gpg_Key_Ids is not string else [ITA_DFLT_Gpg_Key_Ids]
    }}
```
