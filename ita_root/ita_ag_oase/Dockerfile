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
ENV LANGUAGE=en
ENV STORAGEPATH=/storage/

ENV SERVICE_NAME=ita-ag-oase
ENV USER_ID=ita-ag-oase

RUN dnf install -y \
    gcc \
    openssh-clients \
    python39 \
    python39-devel \
    langpacks-en \
    wget \
    zip \
    unzip \
    sqlite \
&&  pip3.9 install --upgrade pip \
&&  pip3.9 install --upgrade setuptools \
&&  pip3.9 install --upgrade Flask \
&&  pip3.9 install --upgrade requests \
&&  pip3.9 install --upgrade pyyaml \
&&  pip3.9 install --upgrade pytz \
&&  pip3.9 install --upgrade pymysql \
&&  pip3.9 install --upgrade python-dotenv \
&&  pip3.9 install --upgrade chardet \
&&  pip3.9 install --upgrade pycryptodome \
&&  pip3.9 install --upgrade jmespath \
&&  pip3.9 install --upgrade imapclient \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME


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
    git \
    vim \
    diffutils \
    bind-utils \
    iputils \
&&  pip3.9 install --upgrade debugpy \
&&  pip3.9 install --upgrade flake8 \
&&  pip3.9 install --upgrade autopep8 \
&&  usermod -G wheel $USERNAME \
&&  echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

USER $USERNAME

RUN mkdir ~/.config \
&& mkdir ~/.vscode-server \
&& mkdir ~/.vscode-server-insiders

WORKDIR $APP_PATH

COPY ./ita_root/ita_ag_oase/ $APP_PATH/
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

COPY ./ita_root/ita_ag_oase/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/
COPY ./ita_root/agent/ $APP_PATH/agent/

USER root
RUN chmod a+x $APP_PATH/agent/entrypoint.sh
USER $USERNAME

ENTRYPOINT ["bash", "./agent/entrypoint.sh"]