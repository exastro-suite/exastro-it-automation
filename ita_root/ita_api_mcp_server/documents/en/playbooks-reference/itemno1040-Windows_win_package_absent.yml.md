# Ansible Legacy Default Playbook - Windows_win_package_absent.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 1040
- **playbook_name**: ~[Exastro standard][Win] Uninstall package
- **playbook_file**: Windows_win_package_absent.yml
## Overview
Uninstalls Windows packages with `win_package` (`state: absent`), pairing installer path, product ID and arguments positionally and registering the result for a verbosity-3 debug.
## Description
"ITA_DFLT_Install_Target_packages": Path of the installer (local path, URL or UNC path) used to uninstall the package. It is omitted from the module call when no value is supplied.
"ITA_DFLT_Install_Target_packages_product_id": Product ID (GUID) of the package to uninstall, used to identify the installed product.
"ITA_DFLT_Install_Target_packages_with_args": Additional arguments passed to the uninstaller, such as silent or no-restart switches.
The three variables can each have multiple values specified at the same time (list type) and are paired positionally across the three lists; a position with no value is omitted from the module call.
The result of the uninstall task is stored with register as "ITA_RGST_WinPackageInstall_Result", which later tasks can reference; the playbook prints it with a debug task that only shows at verbosity level 3 or higher.
## Keyword
- Windows software removal
- MSI silent uninstall
- Product GUID lookup
- Remove installed application
## Playbook
```yaml
- name: Ensure ITA_DFLT_Install_Target_packages is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Install_Target_packages: "{{ ITA_DFLT_Install_Target_packages }}"
  when: ITA_DFLT_Install_Target_packages is defined

- name: Ensure ITA_DFLT_Install_Target_packages_product_id is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Install_Target_packages_product_id: "{{ ITA_DFLT_Install_Target_packages_product_id }}"
  when: ITA_DFLT_Install_Target_packages_product_id is defined

- name: Ensure ITA_DFLT_Install_Target_packages_with_args is recognized
  ansible.builtin.set_fact:
    ITA_DFLT_Install_Target_packages_with_args: "{{ ITA_DFLT_Install_Target_packages_with_args }}"
  when: ITA_DFLT_Install_Target_packages_with_args is defined

- name: Uninstall package
  ansible.windows.win_package:
    path: "{{ item[0] | default(omit) }}"
    product_id: "{{ item[1] | default(omit) }}"
    arguments: "{{ item[2] | default(omit) }}"
    state: absent
  loop: >-
    {{
      (ITA_DFLT_Install_Target_packages if ITA_DFLT_Install_Target_packages is sequence and ITA_DFLT_Install_Target_packages is not string else [ITA_DFLT_Install_Target_packages])
      | ansible.builtin.zip_longest(
          ITA_DFLT_Install_Target_packages_product_id if ITA_DFLT_Install_Target_packages_product_id is sequence and ITA_DFLT_Install_Target_packages_product_id is not string else [ITA_DFLT_Install_Target_packages_product_id],
          ITA_DFLT_Install_Target_packages_with_args if ITA_DFLT_Install_Target_packages_with_args is sequence and ITA_DFLT_Install_Target_packages_with_args is not string else [ITA_DFLT_Install_Target_packages_with_args]
        )
      | list
    }}
  register: ITA_RGST_WinPackageInstall_Result

- name: Debug the result
  ansible.builtin.debug:
    var: ITA_RGST_WinPackageInstall_Result
    verbosity: 3
```
