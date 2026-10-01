# Ansible Legacy Default Playbook - Files_unarchive.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 160
- **playbook_name**: ~[Exastro standard] Deploy/unzip files
- **playbook_file**: Files_unarchive.yml
## Overview
Unpacks each archive in `ITA_DFLT_Target_File_Name` into the positionally paired directory from `ITA_DFLT_Dest_Directory` using `unarchive` with default options (source taken from the controller).
## Description
This Playbook file unzips archived files specified by "ITA_DFLT_Target_File_Name" and extracts the files to directories specified by "ITA_DFLT_Dest_Directory".
"ITA_DFLT_Target_File_Name" can specify multiple compressed files (list type).
"ITA_DFLT_Dest_Directory" can specify multiple directories (list type).

## Additional description
- This Playbook uses `ansible.builtin.unarchive` without specifying `remote_src` (default `remote_src: no`). Therefore, the archive specified in `ITA_DFLT_Target_File_Name` **must exist on the Ansible control node (local) side**. This single task both transfers the archive to the target host and extracts it.
- The `FileUploadColumn` item of the parameter sheet can be linked to `ITA_DFLT_Target_File_Name`. Since uploaded archives are placed on the control node, they can be transferred and extracted directly by this Playbook.
- **You cannot first place the archive on the target host using something like `Files_copy_local-to-remote.yml` and then pass that remote path to `ITA_DFLT_Target_File_Name`.** Because `remote_src: no` is used, this task looks for the same path on the control node as the extraction source and fails. If you want to extract an archive that already exists on the remote host, prepare a separate Playbook with `remote_src: yes` specified.
- The target host must have the extraction command appropriate to the archive format installed (e.g. `unzip` for zip files). Please install the relevant package beforehand.
## Keyword
- extract a tar or zip archive
- install from a tarball
- deploy an application bundle
- decompress files on a server
## Playbook
```yaml
# This Playbook file unzips archived files specified by "ITA_DFLT_Target_File_Name" and extracts the files to directories specified by "ITA_DFLT_Dest_Directory".
# "ITA_DFLT_Target_File_Name" can specify multiple compressed files (list type).
# "ITA_DFLT_Dest_Directory" can specify multiple directories (list type).
- name: Ensure ITA_DFLT_Target_File_Name is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Target_File_Name: "{{ ITA_DFLT_Target_File_Name }}"
  when: ITA_DFLT_Target_File_Name is defined

- name: Ensure ITA_DFLT_Dest_Directory is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Dest_Directory: "{{ ITA_DFLT_Dest_Directory }}"
  when: ITA_DFLT_Dest_Directory is defined

- name: Unpacks an archive after (optionally) copying it from the local machine
  ansible.builtin.unarchive:
    src: "{{ item[0] }}"
    dest: "{{ item[1] }}"
  loop: >-
    {{
      (ITA_DFLT_Target_File_Name if ITA_DFLT_Target_File_Name is sequence and ITA_DFLT_Target_File_Name is not string else [ITA_DFLT_Target_File_Name])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Dest_Directory if ITA_DFLT_Dest_Directory is sequence and ITA_DFLT_Dest_Directory is not string else [ITA_DFLT_Dest_Directory]
        )
      | list
    }}
```
