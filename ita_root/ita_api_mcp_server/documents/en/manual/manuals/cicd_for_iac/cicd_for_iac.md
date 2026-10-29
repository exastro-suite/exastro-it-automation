# Configuring and Using the CI/CD For IaC Feature

## Terminology

- **Link source material**: material inside the Git repository linked via the CI/CD For IaC feature.
- **Link target material**: material uploaded from the following menus of the Ansible-Driver, Terraform-Cloud/EP-Driver, and Terraform-CLI-Driver: Ansible-Legacy/Playbook Material Collection, Ansible-Pioneer/Interactive File Material Collection, Ansible-LegacyRole/Role Package Management, Ansible Common/File Management, Ansible Common/Template Management, Terraform-Cloud-EP/Module Material Collection, Terraform-Cloud-EP/Policy Management, Terraform-CLI/Module Material Collection.

## Feature overview

The CI/CD For IaC feature consists of two functions.

1. **Git integration function**: creates a clone of the Git repository inside ITA, periodically detects updates to the link source material, and lists them in the "Remote Repository Material" menu.
2. **Material linking function**: registers a link between link source material and link target material, and registers an operation/Movement for validating the link target material's behavior. When the link source material is updated, the link target material is automatically updated and a work execution is run via the validation operation/Movement.

## Menu structure

| No | Menu/Screen | Overview |
|---|---|---|
| 1 | Remote Repository | Manages Git repository information. |
| 2 | Remote Repository Material | Manages material information from the Git repository (hidden menu at install time). |
| 3 | Material Linking | Manages the link information between link source material and link target material. |

## Workflow

1. Register a Remote Repository (information about the Git repository to link).
2. Register a Material Link (link between link source material and link target material).
3. If needed, register an operation + Movement on the Material Link (for validating behavior on update).
4. Confirm that the link target material is automatically updated when the link source material is updated, and that the validation (work execution) runs.

## Remote Repository

Register information about the Git repository to link.

| Item | Description | Constraints |
|---|---|---|
| Remote repository name | Arbitrary name | Required, max 255 bytes |
| Remote repository (URL) | URL to pass to `git clone` | Required, max 255 bytes |
| Branch | Branch to clone (default branch if left blank) | Max 255 bytes |
| Protocol | https / SSH password authentication / SSH key authentication (with or without passphrase, currently unavailable) | Required |
| Visibility type | Public/Private (required when protocol is https) | - |
| Git account: user/password | Required when Visibility = Private. Since GitHub has discontinued password authentication, use a personal access token | Max 255 bytes each |
| SSH connection info: password | Linux user password for the SSH key (required for SSH password authentication) | Max 255 bytes |
| SSH connection info: passphrase | Passphrase for the key file (required for SSH key authentication) | Max 255 bytes |
| SSH connection info: connection parameters | Parameters set in the `GIT_SSH_COMMAND` environment variable (effective in Git 2.3+; by default the equivalent of `UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no` is applied) | Max 4000 bytes |
| Proxy: Address/Port | Set to reach the Git server from behind a proxy | Address max 255 bytes |
| Remote repository sync info: auto sync | True = sync periodically, False = do not sync automatically | Required, default: enabled |
| Remote repository sync info: interval (seconds) | Defaults to 60 seconds if left blank | Unit: seconds |
| Communication retry info: count/interval (ms) | Defaults to 3 times / 1000ms if left blank | - |
| Remarks | Free text | Max 4000 bytes |

Sync status display items: Status (blank = immediately after new registration/update/discard-restore; Normal; Abnormal = sync suspended; Resume = after pressing the Resume button), Detail info (cause on error, cleared on resume or update), Last date/time (last sync time, cleared on resume or update), Resume button (active only when abnormal).

## Material Linking

Links link source material to link target material, and registers an operation/Movement for validating the link target material's behavior. When the link source material is updated, the internal function automatically updates the link target material, runs the work execution via the validation operation/Movement, and displays the result.

| Item | Description | Constraints |
|---|---|---|
| Link target material name | A name that links to an item in the menu below, depending on the link target material type. Follows each menu's input rules | Required, max 255 bytes |
| Git repository (From): material path | Selected from the material paths registered in the Remote Repository menu | Required |
| Exastro IT Automation (To): link target material type | Requires the corresponding driver to be installed (see table below) | Required |
| Template Management: variable definition | Enter the variable definition when the link target material type is "Ansible Common/Template Management" (not needed for other types) | Max 4000 bytes |
| Ansible-Pioneer: interaction type / OS type | Select when the link target material type is "Ansible-Pioneer/Interactive File Material Collection" (not needed for other types) | - |
| Material sync info: auto sync | True = automatically update the link target material on Git update, False = do not update | Required, default: enabled |
| Delivery info: operation/Movement | Select the operation/Movement to run when the link target material is updated | - |
| Delivery info: dry run | True = run in dry-run mode (dry run for Ansible, plan check for Terraform), False/unselected = normal execution | - |
| Remarks | Free text | Max 4000 bytes |

Correspondence between link target material type, menu item, and required driver:

| Menu | Item | Required driver |
|---|---|---|
| Ansible-Legacy/Playbook Material Collection | Playbook material name | Ansible-Driver |
| Ansible-Pioneer/Interactive File Material Collection | No target item | Ansible-Driver |
| Ansible-LegacyRole/Role Package Management | Role package name | Ansible-Driver |
| Ansible Common/File Management | File-embedded variable name | Ansible-Driver |
| Ansible Common/Template Management | Template-embedded variable name | Ansible-Driver |
| Terraform-Cloud-EP/Module Material Collection, Policy Management | Module material name, Policy name | Terraform-Cloud/EP-Driver |
| Terraform-CLI/Module Material Collection | Module material name | Terraform-CLI-Driver |

Sync status display items: Material sync info status (blank / Normal / Abnormal = sync error or validation work execution failed / Resume), Detail info, Last date/time, Resume button (behaves the same as described above for Remote Repository). Delivery info detail info (error cause when work execution fails; since success does not imply no abnormality, the result must still be checked via each driver's work-status check, accessed from the Work Status Check button), Work instance No., Work Status Check button (active only when a work execution has occurred).

**Update flow for link target material**: detect a material update in the Git repository → compare the diff (including remarks) → if there is a diff, update the link target material → if Delivery info (operation/Movement) is configured, run the work execution → depending on the result, set the material sync info status to "Normal" or "Abnormal" (with the error cause in Detail info). If the link target material name is changed, the old record remains and a new record is created under the new name.

## Hidden menu: Remote Repository Material

The list of link source material is automatically updated by the internal function (do not manually add, update, or delete records). To display this menu, it must be restored via Role - Menu Link Management in the Management Console. Items: Remote repository name (list selection, required), Material path (max 4096 bytes, required; not displayed if the remote repository's sync status is "Abnormal"), Material type ("Roles directory" for Ansible-LegacyRole, "File" otherwise).

## Appendix: Notes on registering material in a Git repository

- Registering a Git repository containing a material name of 256 bytes or more causes `git clone` to fail.
- `git clone` also fails if the material name, including the file path, is 4096 bytes or more.

## Appendix: Notes on material linked to Role Package Management

You must create a parent directory containing a directory named `roles`, and place the role package files/directories under it. However, creating a `roles` directory directly under the **root directory of the Git repository** is not recognized as a directory that can be linked to Role Package Management (e.g. `roles` directly under the root is not recognized, but a subdirectory such as `sample/roles` is recognized). In the Material Linking menu's material path, select the recognized path (e.g. `sample/roles`).
