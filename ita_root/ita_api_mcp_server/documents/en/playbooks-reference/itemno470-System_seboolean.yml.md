# Ansible Legacy Default Playbook - System_seboolean.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 470
- **playbook_name**: ~[Exastro standard] Modify SELinux
- **playbook_file**: System_seboolean.yml
## Overview
Toggles SELinux booleans with the `ansible.posix.seboolean` module, pairing names, on/off states and persistence flags positionally with `zip_longest` across the three input lists.
## Description
This Playbook file changes the bool values for the names specified by "ITA_DFLT_Booleans_Name" using the values (true/false) specified by "ITA_DFLT_State" and uses the values (true/false) specified by "ITA_DFLT_Persistent" to configure the persistency of the files (If the files will keep the settings after reboot or not).
Each of the variables can have multiple specified at the same time (list type).
## Keyword
- setsebool -P
- SELinux permission tuning
- httpd_can_network_connect style flag
- mandatory access control adjustment
- allow blocked service behaviour
## Playbook
```yaml
# This Playbook file changes the bool values for the names specified by "ITA_DFLT_Booleans_Name"
# using the values (true/false) specified by "ITA_DFLT_State" and uses the values (true/false)
# specified by "ITA_DFLT_Persistent" to configure the persistency of the files
# (If the files will keep the settings after reboot or not).
# Each of the variables can have multiple specified at the same time (list type).
- name: Ensure ITA_DFLT_Booleans_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Booleans_Name: "{{ ITA_DFLT_Booleans_Name }}"
  when: ITA_DFLT_Booleans_Name is defined

- name: Ensure ITA_DFLT_State is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_State: "{{ ITA_DFLT_State }}"
  when: ITA_DFLT_State is defined

- name: Ensure ITA_DFLT_Persistent is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Persistent: "{{ ITA_DFLT_Persistent }}"
  when: ITA_DFLT_Persistent is defined

- name: Toggles SELinux booleans
  ansible.posix.seboolean:
    name: "{{ item[0] }}"
    state: "{{ item[1] }}"
    persistent: "{{ item[2] }}"
  loop: >-
    {{
      (ITA_DFLT_Booleans_Name if ITA_DFLT_Booleans_Name is sequence and ITA_DFLT_Booleans_Name is not string else [ITA_DFLT_Booleans_Name])
      | ansible.builtin.zip_longest(
          ITA_DFLT_State if ITA_DFLT_State is sequence and ITA_DFLT_State is not string else [ITA_DFLT_State],
          ITA_DFLT_Persistent if ITA_DFLT_Persistent is sequence and ITA_DFLT_Persistent is not string else [ITA_DFLT_Persistent]
        )
      | list
    }}
```
