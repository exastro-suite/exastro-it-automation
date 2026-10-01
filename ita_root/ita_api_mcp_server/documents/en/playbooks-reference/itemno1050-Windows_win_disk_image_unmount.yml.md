# Ansible Legacy Default Playbook - Windows_win_disk_image_unmount.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1050
- **playbook_name**: ~[Exastro standard][Win] Unmount
- **playbook_file**: Windows_win_disk_image_unmount.yml
## Overview
Unmounts (detaches) the specified ISO disk image from the Windows target host by calling `win_disk_image` with `state: absent`.
## Description
"ITA_DFLT_mount_image_path": Path of the ISO (disk image) file that is currently mounted on the Windows target host and is to be unmounted.
This is the only parameter and a single value is used directly, so there is no loop or list pairing. The image path must match the one used when the image was mounted.
## Keyword
- Windows ISO unmount
- Detach virtual drive
- Eject disk image
- Release mounted media
## Playbook
```yaml
- name: Unmount ISO
  community.windows.win_disk_image:
    image_path: "{{ ITA_DFLT_mount_image_path }}"
    state: absent
```
