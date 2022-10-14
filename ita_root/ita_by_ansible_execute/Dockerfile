#   Copyright 2022 NEC Corporation
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
ENV USER_ID=20101
ENV EXECUTE_INTERVAL=1
ENV LANGUAGE=en
ENV STORAGEPATH=/storage/
ENV CONTAINER_BASE=docker
ENV DEFAULT_LOCAL_TMP=/tmp

RUN dnf install -y \
    gcc \
    python39 \
    python39-devel \
    python39-mod_wsgi \
    langpacks-en \
    wget \
    zip \
    unzip \
    openssh-clients \
    git \
&&  curl -kL https://storage.googleapis.com/kubernetes-release/release/v1.24.3/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
&&  chmod +x /usr/local/bin/kubectl \
&&  pip3.9 install --upgrade pip setuptools \
&&  pip3.9 install \
    Flask \
    requests \
    pyyaml \
    pytz \
    pymysql \
    python-dotenv \
    chardet \
    dictknife \
    ansible \
    kubernetes \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME

COPY ./ita_root/ita_by_ansible_execute/config/centos8.repo /etc/yum.repos.d/centos8.repo

RUN dnf install -y --enablerepo=baseos expect

#
# Build for development
#   Specify options when creating this image: --target develop_build
#
FROM    common_build as develop_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

RUN dnf install -y \
    sudo \
    vim \
    diffutils \
    bind-utils \
    iputils \
&&  curl -fsSL https://get.docker.com/builds/Linux/x86_64/docker-17.05.0-ce.tgz | tar -xzC /usr/local/bin --strip=1 docker/docker \
&&  curl -kL https://github.com/docker/compose/releases/download/v2.5.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose \
&&  chmod +x /usr/local/bin/docker-compose \
&&  pip3.9 install \
    debugpy \
    flake8 \
    autopep8 \
&&  usermod -G wheel $USERNAME \
&&  echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

USER $USERNAME

RUN mkdir ~/.config

WORKDIR $APP_PATH

COPY ./ita_root/ita_by_ansible_execute/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/
COPY ./ita_root/backyard/ $APP_PATH/backyard/

#
# Build for production
#
FROM    common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

WORKDIR $APP_PATH

COPY ./ita_root/ita_by_ansible_execute/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/
COPY ./ita_root/backyard/ $APP_PATH/backyard/


ENTRYPOINT ["backyard/entrypoint.sh"]

