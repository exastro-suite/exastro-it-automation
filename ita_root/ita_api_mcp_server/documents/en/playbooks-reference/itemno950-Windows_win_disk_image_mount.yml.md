# Ansible Legacy Default Playbook - Windows_win_disk_image_mount.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 950
- **playbook_name**: ~[Exastro standard][Win] Mount
- **playbook_file**: Windows_win_disk_image_mount.yml
## Overview
Mounts an ISO disk image on the Windows target host with `win_disk_image` (`state: present`), then prints the first mount path returned by the module.
## Description
"ITA_DFLT_mount_image_path": Path on the Windows target host of the ISO (disk image) file to be mounted. Only one image is handled per run; no list pairing is involved.
The module result is stored with register as "disk_image_out", so it is available to later tasks. The playbook itself outputs disk_image_out.mount_paths[0], which is the drive path assigned to the mounted image.
## Keyword
- Windows ISO mount
- Attach virtual drive
- Obtain mounted drive letter
- Mount installation media
## Playbook
```yaml
- name: Ensure an ISO is mounted
  community.windows.win_disk_image:
    image_path: "{{ ITA_DFLT_mount_image_path }}"
    state: present
  register: disk_image_out

- name: disk path
  ansible.builtin.debug:
    msg: "{{ disk_image_out.mount_paths[0] }}"
```
