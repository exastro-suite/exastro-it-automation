# Ansible Legacy Default Playbook - Windows_win_domain.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 790
- **playbook_name**: ~[Exastro standard][Win] Check Domain
- **playbook_file**: Windows_win_domain.yml
## Overview
Creates a new Active Directory domain in a new forest on the Windows target with `win_domain`, pairing each DNS domain name with its safe mode password; logging is suppressed.
## Description
"ITA_DFLT_dns_domain_name": Full DNS name of the Active Directory domain to create in a new forest (for example corp.example.com).
"ITA_DFLT_domain_safe_mode_password": Safe mode (Directory Services Restore Mode) administrator password set on the new domain controller.
Each of the variables can have multiple values specified at the same time (list type), and the values are paired positionally between the two lists.
Because the password is confidential, both the fact assignment and the domain creation task set no_log: true, so their details are kept out of the execution log (set it to false only when debugging).
## Keyword
- Active Directory domain controller promotion
- New forest creation
- DSRM safe mode password
- Windows Server dcpromo
## Playbook
```yaml
- name: Ensure ITA_DFLT_dns_domain_name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_dns_domain_name: "{{ ITA_DFLT_dns_domain_name }}"
  when: ITA_DFLT_dns_domain_name is defined

- name: Ensure ITA_DFLT_domain_safe_mode_password is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_domain_safe_mode_password: "{{ ITA_DFLT_domain_safe_mode_password }}"
  when: ITA_DFLT_domain_safe_mode_password is defined
  no_log: true

- name: Create new domain in a new forest on the target host
  ansible.windows.win_domain:
    dns_domain_name: "{{ item[0] }}"
    safe_mode_password: "{{ item[1] }}"
  loop: >-
    {{
      (ITA_DFLT_dns_domain_name if ITA_DFLT_dns_domain_name is sequence and ITA_DFLT_dns_domain_name is not string else [ITA_DFLT_dns_domain_name])
      | ansible.builtin.zip_longest(
          ITA_DFLT_domain_safe_mode_password if ITA_DFLT_domain_safe_mode_password is sequence and ITA_DFLT_domain_safe_mode_password is not string else [ITA_DFLT_domain_safe_mode_password]
        )
      | list
    }}
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）
```
