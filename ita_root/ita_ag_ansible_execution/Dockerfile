#   Copyright 2024 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
ARG USERNAME=app_user
ARG GROUPNAME=app_user
ARG APP_PATH=/exastro

FROM    registry.access.redhat.com/ubi8/ubi-init as common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH
ENV PYTHONPATH=/exastro/
ENV LANGUAGE=en
ENV STORAGEPATH=/storage/

ENV SERVICE_NAME=ita-ag-ansible-execution
ENV USER_ID=ita-ag-ansible-execution

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    dnf install -y \
    podman-docker \
    gcc \
    openssh-clients \
    python39 \
    python39-devel \
    langpacks-en \
    wget \
    zip \
    unzip \

&&  pip3.9 install poetry==1.6.0 \
&&  poetry config virtualenvs.create false \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME

WORKDIR $APP_PATH

COPY ./ita_root/ita_ag_ansible_execution/pyproject.toml ./ita_root/ita_ag_ansible_execution/poetry.lock $APP_PATH/

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    poetry install --only first_install

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    poetry install --without develop_build

#
# Build for development
#   Specify options when creating this image: --target develop_build
#
FROM    common_build as develop_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    dnf install -y \
    sudo \
    git \
    vim \
    diffutils \
    bind-utils \
    iputils \
&&  usermod -G wheel $USERNAME \
&&  echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    poetry install --with develop_build

USER $USERNAME

RUN mkdir ~/.config \
&& mkdir ~/.vscode-server \
&& mkdir ~/.vscode-server-insiders

WORKDIR $APP_PATH

COPY ./ita_root/ita_ag_ansible_execution/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/
COPY ./ita_root/agent/ $APP_PATH/agent/

#
# Build for production
#
FROM    common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

USER $USERNAME
WORKDIR $APP_PATH

COPY ./ita_root/ita_ag_ansible_execution/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/
COPY ./ita_root/agent/ $APP_PATH/agent/

USER root
RUN chmod a+x $APP_PATH/agent/entrypoint.sh
USER $USERNAME

ENTRYPOINT ["bash", "./agent/entrypoint.sh"]
