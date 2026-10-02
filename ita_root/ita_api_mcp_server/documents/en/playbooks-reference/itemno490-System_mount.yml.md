# Ansible Legacy Default Playbook - System_mount.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 490
- **playbook_name**: ~[Exastro standard] Mount
- **playbook_file**: System_mount.yml
## Overview
Mounts a device with the `ansible.posix.mount` module using `state: mounted`, which both mounts the filesystem now and records a matching permanent entry in /etc/fstab.
## Description
"ITA_DFLT_mount_path": Mount point directory on the Target host where the device is attached. It is created if it does not exist.
"ITA_DFLT_mount_src": Device or remote share to mount, for example /dev/sdb1, a UUID= or LABEL= specification, or an NFS "server:/export" path.
"ITA_DFLT_mount_fstype": Filesystem type of the device, for example xfs, ext4 or nfs.
"ITA_DFLT_mount_opts": Optional comma-separated mount options such as "defaults,noatime". It is filtered through "default(omit)", so when the variable is not supplied the option is dropped and the module default is used.
Because "state: mounted" is used, the mount point is mounted immediately and the entry is also persisted in /etc/fstab so that it is remounted after a reboot. Each variable takes a single value, so one run of this Playbook file configures one mount point.
## Keyword
- /etc/fstab persistent entry
- attach disk or NFS share
- storage volume provisioning
- mount point configuration
- remount after reboot
## Playbook
```yaml
- name: Mount up device.
  ansible.posix.mount:
    path: "{{ ITA_DFLT_mount_path }}"
    src: "{{ ITA_DFLT_mount_src }}"
    fstype: "{{ ITA_DFLT_mount_fstype }}"
    opts: "{{ ITA_DFLT_mount_opts | default(omit) }}"
    state: mounted
```
