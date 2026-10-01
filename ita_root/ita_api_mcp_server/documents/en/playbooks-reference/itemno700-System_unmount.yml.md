# Ansible Legacy Default Playbook - System_unmount.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 700
- **playbook_name**: ~[Exastro standard] Unmount
- **playbook_file**: System_unmount.yml
## Overview
Unmounts the filesystem at `ITA_DFLT_mount_path` using `ansible.posix.mount` with `state: absent`, which also deletes the matching entry from /etc/fstab.
## Description
"ITA_DFLT_mount_path": Mount point (directory path) of the filesystem to be unmounted.
Because the module is called with state "absent", the filesystem is unmounted and the corresponding line is also removed from /etc/fstab, so the mount will not be restored at the next boot.
Only a single mount point is handled per run; the playbook has no loop, so one value should be specified.
## Keyword
- umount command
- remove fstab entry
- detach a volume
- storage maintenance
- permanently remove a mount
## Playbook
```yaml
- name: Unmount device.
  ansible.posix.mount:
    path: "{{ ITA_DFLT_mount_path }}"
    state: absent
```
