# Ansible Legacy Default Playbook - Windows_win_get_url.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 870
- **playbook_name**: ~[Exastro standard][Win] Download URL
- **playbook_file**: Windows_win_get_url.yml
## Overview
Downloads files over HTTP, HTTPS or FTP onto the Windows target host with `win_get_url`, storing every URL in one destination folder that defaults to %windir%\Temp.
## Description
"ITA_DFLT_Download_URL": URL of the file to download by HTTP, HTTPS or FTP. Multiple URLs can be specified at the same time (list type) and the download task is repeated for each one.
"ITA_DFLT_Destination_Directory": Folder on the Windows target host in which the downloaded files are saved. It is optional; when it is not specified, "%windir%\Temp" is used. The same destination applies to all URLs, so it is not paired with the URL list.
## Keyword
- Windows download file from internet
- Fetch installer onto Windows host
- wget equivalent for Windows
- Save remote file to temp folder
## Playbook
```yaml
- name: Ensure ITA variable is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Download_URL: "{{ ITA_DFLT_Download_URL }}"
  when: ITA_DFLT_Download_URL is defined

- name: Downloads files from HTTP, HTTPS, or FTP to node
  ansible.windows.win_get_url:
    url: "{{ item }}"
    dest: "{{ ITA_DFLT_Destination_Directory | default ('%windir%\\Temp') }}"
  loop: >-
    {{
      ITA_DFLT_Download_URL if ITA_DFLT_Download_URL is sequence and ITA_DFLT_Download_URL is not string else [ITA_DFLT_Download_URL]
    }}
```
