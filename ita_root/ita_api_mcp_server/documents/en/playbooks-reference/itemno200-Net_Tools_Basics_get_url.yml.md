# Ansible Legacy Default Playbook - Net_Tools_Basics_get_url.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 200
- **playbook_name**: ~[Exastro standard] Download URL
- **playbook_file**: Net_Tools_Basics_get_url.yml
## Overview
Downloads every URL in `ITA_DFLT_Download_URL` onto the target node with `get_url`, saving them under `ITA_DFLT_Destination_Directory`, which falls back to "/tmp/".
## Description
"ITA_DFLT_Download_URL": URL to be downloaded over HTTP, HTTPS or FTP. Multiple URLs can be specified at the same time (list type); the task loops over each one, and a single scalar value is automatically treated as a one-element list.
"ITA_DFLT_Destination_Directory": Directory (or absolute file path) on the target node where the downloaded data is written. Optional - defaults to "/tmp/" when it is not given.
The same destination is applied to every URL in the loop, so it is not paired per URL; give a directory ending in "/" when downloading several files, otherwise each download would overwrite the same file. The download is performed by the target node itself, which therefore needs network access to the URL.
## Keyword
- fetch an installer from the internet
- wget or curl equivalent
- download an artifact to a server
- HTTP file retrieval
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Download_URL: "{{ ITA_DFLT_Download_URL }}"
  when: ITA_DFLT_Download_URL is defined

- name: Downloads files from HTTP, HTTPS, or FTP to node
  ansible.builtin.get_url:
    url: "{{ item }}"
    dest: "{{ ITA_DFLT_Destination_Directory | default('/tmp/') }}"
  loop: >-
    {{
      ITA_DFLT_Download_URL if ITA_DFLT_Download_URL is sequence and ITA_DFLT_Download_URL is not string else [ITA_DFLT_Download_URL]
    }}
```
