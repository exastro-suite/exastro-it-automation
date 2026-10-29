# How to Customize the Ansible Execution Environment

This explains how to customize the Ansible execution environment used by ITA. With Ansible-Core, you can either insert a customization step during the build (docker-compose edition only) or use a pre-customized image. With Ansible Execution Agent or Ansible Automation Platform, you can customize the execution environment using ansible-builder.

## Customizing with Ansible-Core

### Adding a Customization Step to the Build (docker-compose edition only)

Check `ANSIBLE_AGENT_IMAGE` / `ANSIBLE_AGENT_IMAGE_TAG` / `ANSIBLE_AGENT_BASE_IMAGE` / `ANSIBLE_AGENT_BASE_IMAGE_TAG` in `~/exastro-docker-compose/.env` (default values when commented out: `ANSIBLE_AGENT_IMAGE=my-exastro-ansible-agent`, tag = the ITA version, base image = `exastro/exastro-it-automation-by-ansible-agent`). If an existing image is present, remove it with `docker rmi` first.

The build uses `~/exastro-docker-compose/ita_by_ansible_execute/templates/docker-compose.yml` and `work/Dockerfile`, so customizations should be written into these two files (from ITA 2.6.0 onward, the default base image's Python/pip is Python3.11/pip3.11).

**Example: adding a collection** — add the following to the Dockerfile (specify the libraries listed in the collection's official documentation):

```dockerfile
RUN ansible-galaxy collection install [collection name to install] \
&& pip3.11 install [libraries required by the collection]
```

If a transparent proxy is performing SSL/TLS inspection, add `--ignore-certs` (e.g. `ansible-galaxy collection install --ignore-certs ...`) to avoid certificate errors (installing a custom CA certificate is also an option for certificate validation).

**Example: a custom module** — place the module file at `~/exastro-docker-compose/ita_by_ansible_execute/templates/work/my_module.py`, grant read permission (`chmod a+r`), and add the following to the Dockerfile.

```dockerfile
RUN mkdir -p /home/app_user/.ansible/plugins/modules
COPY my_module.py /home/app_user/.ansible/plugins/modules/
```

After editing, the image is rebuilt the next time work is executed with Ansible-Core (a `returned a non-zero code: 1` error indicates a build failure).

### Using a Pre-customized Image

Check the target image on the image repository server (on Kubernetes, using the `latest` or `none` tag prevents the local image from being used, so a different tag is recommended), then export it with `docker save <image>:<tag> | gzip -c > /tmp/custom-docker-image.tar.gz`.

**docker-compose edition**: transfer the tar.gz to the target server, load it with `docker load < /tmp/custom-docker-image.tar.gz`, verify with `docker images`, edit `ANSIBLE_AGENT_IMAGE`/`ANSIBLE_AGENT_IMAGE_TAG` in `.env`, and apply with `sh setup.sh install`.

**Kubernetes edition**: transfer the tar.gz to all nodes, load it with `ctr images -n k8s.io import /tmp/custom-docker-image.tar.gz`, edit `exastro-it-automation.ita-by-ansible-execute.extraEnv.ANSIBLE_AGENT_IMAGE`/`ANSIBLE_AGENT_IMAGE_TAG` in `values.yaml`, and apply with `helm upgrade` and `kubectl rollout restart deploy/ita-by-ansible-execute`.

## Customizing with Ansible Execution Agent

The general flow on the ITA side is: register an execution environment definition template (`Ansible Common → Execution Environment Definition Template Management`), register the values to substitute into the template (in the free edition, directly as Jinja variables in the template; in the paid edition, via the "Execution Environment Parameter Definition" parameter sheet), register an execution environment (`Ansible Common → Execution Environment Management`) that links the two, and then set the execution environment name in the target Movement's "Ansible Execution Agent Connection Information".

### Example: Using a Collection (Free Edition Base Image)

An example adding the `azure.azcollection` collection to the base image `registry.access.redhat.com/ubi9/ubi-init:latest`.

The execution environment definition template (template name `azure_ee_template`) is a Jinja2 template like the following.

```yaml+jinja
version: 3
build_arg_defaults:
  ANSIBLE_GALAXY_CLI_COLLECTION_OPTS: '--ignore-certs'
images:
  base_image:
    name: {{ image }}
dependencies:
  ansible_core:
    package_pip: {{ ansible_core }}
  ansible_runner:
    package_pip: {{ ansible_runner }}
  system: {{ bindep_file }}
  python: {{ python_requirements_file }}
{% if galaxy_requirements_file == "" %}
{% else %}
  galaxy: {{ galaxy_requirements_file }}
{% endif %}
  python_interpreter:
    package_system: "python3.11"
    python_path: "/usr/bin/python3.11"
additional_build_steps:
  append_base:
    - RUN /usr/bin/python3.11 -m pip install --upgrade pip
options:
  package_manager_path: {{ package_manager_path }}
  user: root
```

Register in Execution Environment Management: an execution environment name (e.g. `azure_ee_ubi9`), execution environment build method "ITA", tag name (e.g. `azure_ee_image_ubi9`), execution environment definition name (use the initial data entry "~[Exastro standard] default (galaxy collection is azure only)"), and template name (`azure_ee_template`). Set the execution environment name (`azure_ee_ubi9`) in the "Execution environment" field of the target Movement's Ansible Execution Agent connection information (ansible-builder parameters are usually not needed, though `-v 3` etc. can be set for debugging).

### Example: Using a Collection (Paid Edition Base Image)

Using the base image `registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel9:latest`. Run `podman login registry.redhat.io` on the Agent beforehand.

In the "Execution Environment Parameter Definition" parameter sheet (`Input → Execution Environment Parameter Definition`), register execution_environment_name (e.g. `azure_ee`), image (the base image above), ansible_core (e.g. `ansible_core==2.16.0`), ansible_runner, bindep_file (`systemd-devel`/`gcc`/`python3.11-devel`), python_requirements_file (`pywinrm`/`setuptools`/`pexpect`/`boto3`/`paramiko`/`boto`/`certifi`), galaxy_requirements_file (`collections:\n - azure.azcollection`), and package_manager_path (`/usr/bin/microdnf`). The template, Execution Environment Management, and Movement settings are the same as in the free edition (specify "Execution Environment Parameter Definition/azure_ee" as the execution environment definition name).

### Example: Using a Custom Module (Agent)

Place `/tmp/ansible_module/my_module.py` on the Agent and grant read permission. In the execution environment definition template (e.g. `my_module_ubi9_template`), copy the module file via `additional_build_files`, and add `COPY _build/configs/my_module.py /usr/share/ansible/plugins/modules/` under `additional_build_steps.append_base`. Use the initial data entry "~[Exastro standard] default (no galaxy collection)" as the execution environment definition name; the Execution Environment Management and Movement settings are the same as above.

## Customizing with Ansible Automation Platform

The same procedure can also be used when Ansible Automation Platform (Cloud) is selected as the execution engine (the only difference for Cloud is that files no longer need to be placed in the ITA working directory — the way execution environments are specified does not change).

Common flow: install `ansible-builder` on the ControlNode (`dnf install --enablerepo=ansible-automation-platform-2.4-for-rhel-8-x86_64-rpms ansible-builder`) → prepare the definition files (`execution-environment.yml`, `galaxy-requirements.yml`, `python-requirements.txt`, `bindep.txt`) in the same directory → build the image with `ansible-builder build -t <tag name>` → verify with `podman images` → export with `podman save` to a tar file and copy it to the awx user on the ControlNode/ExecutionNode with `podman load` → register it as an execution environment in the AAP admin UI → set the name registered in AAP as the execution environment in the ITA-side Movement's "Ansible Automation Controller Connection Information".

**Example: using a collection (free edition)**: set base_image in `execution-environment.yml` to `registry.access.redhat.com/ubi9/ubi-init:latest`, `azure.azcollection` in galaxy-requirements.yml, `pywinrm`/`setuptools`/`pexpect`/`boto3`/`paramiko`/`boto`/`certifi` in python-requirements.txt, and `openssh-clients`/`sshpass`/`expect` in bindep.txt.

**Example: using a collection (paid edition)**: use `registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel9:latest` as base_image, requiring `podman login registry.redhat.io` beforehand. bindep.txt becomes `systemd-devel`/`gcc`/`python3.11-devel`, and package_manager_path becomes `/usr/bin/microdnf` (other file contents are the same as the free edition).

**Example: using a custom module**: place the module at `/tmp/ansible_module/my_module.py` on the ControlNode and grant read permission, then add `additional_build_files` (`src: /tmp/ansible_module/my_module.py`, `dest: configs`) and `COPY _build/configs/my_module.py /usr/share/ansible/plugins/modules/` under `additional_build_steps.append_base` in `execution-environment.yml`.

In every case, once the build finishes, "Complete! The build context can be found at: ..." is displayed, and the image can be verified with `podman images`. Copy the image for the ControlNode's awx user via `podman save` → `chown awx:awx` → `podman load`, transfer it to the ExecutionNode and `podman load` it there as well, then register it in AAP's execution environment management screen.
