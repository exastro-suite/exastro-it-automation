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
ENV DEFAULT_LANGUAGE=ja
ENV STORAGEPATH=/storage/
ENV LISTEN_PORT             8000
ENV APACHE_PID_DIR          /var/run_$USERNAME/httpd/pid
ENV APACHE_SOCKET_DIR       /var/run_$USERNAME/httpd/socket
ENV APACHE_USERNAME         $USERNAME
ENV APACHE_GROUPNAME        $GROUPNAME

RUN dnf install -y \
    gcc \
    httpd \
    httpd-devel \
    python39 \
    python39-devel \
    python39-mod_wsgi \
    langpacks-en \
    wget \
    unzip \
&&  pip3.9 install --upgrade pip setuptools \
&&  pip3.9 install \
    Flask \
    connexion \
    six \
    requests \
    pyyaml \
    pytz \
    markdown \
    pymysql \
    python-dotenv \
    openpyxl \
    chardet \
&&  pip3.9 install \
    connexion[swagger-ui] \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME \
&&  setcap 'cap_net_bind_service=+ep' /usr/sbin/httpd \
&&  chown $USERNAME:$GROUPNAME /var/log/httpd \
&&  mkdir -p $APACHE_PID_DIR \
&&  chown $USERNAME:$GROUPNAME $APACHE_PID_DIR \
&&  mkdir -p $APACHE_SOCKET_DIR \
&&  chown $USERNAME:$GROUPNAME $APACHE_SOCKET_DIR

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
&&  pip3.9 install \
    debugpy \
    flake8 \
    autopep8 \
    ansible \
&&  usermod -G wheel $USERNAME \
&&  echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

USER $USERNAME

RUN mkdir ~/.config

WORKDIR $APP_PATH

COPY ./ita_root/ita_api_organization/config/httpd.conf/httpd.conf /etc/httpd/conf/httpd.conf
COPY ./ita_root/ita_api_organization/config/httpd.conf/wsgi.conf /etc/httpd/conf.d/wsgi.conf

COPY ./ita_root/ita_api_organization/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/

CMD ["httpd","-D","FOREGROUND"]

#
# Build for production
#
FROM    common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

WORKDIR $APP_PATH

COPY ./ita_root/ita_api_organization/config/httpd.conf/httpd.conf /etc/httpd/conf/httpd.conf
COPY ./ita_root/ita_api_organization/config/httpd.conf/wsgi.conf /etc/httpd/conf.d/wsgi.conf

COPY ./ita_root/ita_api_organization/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/

USER $USERNAME

CMD ["httpd","-D","FOREGROUND"]
