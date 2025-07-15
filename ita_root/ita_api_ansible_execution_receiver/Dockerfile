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

FROM    exastro/exastro-it-automation-api-ansible-execution-receiver:2.5.2 as common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH
ENV DB_CONNECT_TIMEOUT=10
ENV DB_CONNECT_RETRY_SLEEP_TIME=0.5
ENV DB_CONNECT_RETRY_LIMIT=2


COPY ./ita_root/common_libs/common/exception.py $APP_PATH/common_libs/common/exception.py
COPY ./ita_root/common_libs/common/dbconnect/dbconnect_common.py $APP_PATH/common_libs/common/dbconnect/dbconnect_common.py
COPY ./ita_root/common_libs/common/dbconnect/dbconnect_org.py $APP_PATH/common_libs/common/dbconnect/dbconnect_org.py
COPY ./ita_root/common_libs/common/dbconnect/dbconnect_ws_sandbox.py $APP_PATH/common_libs/common/dbconnect/dbconnect_ws_sandbox.py
COPY ./ita_root/common_libs/common/dbconnect/dbconnect_ws.py $APP_PATH/common_libs/common/dbconnect/dbconnect_ws.py
COPY ./ita_root/common_libs/common/dbconnect/dbdisuse_check.py $APP_PATH/common_libs/common/dbconnect/dbdisuse_check.py


#
# Build for development
#   Specify options when creating this image: --target develop_build
#
FROM    common_build as develop_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH
USER root

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    dnf install -y \
    sudo \
    git \
    zip \
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

COPY ./ita_root/ita_api_ansible_execution_receiver/config/httpd.conf/httpd.conf /etc/httpd/conf/httpd.conf
COPY ./ita_root/ita_api_ansible_execution_receiver/config/httpd.conf/wsgi.conf /etc/httpd/conf.d/wsgi.conf

# COPY ./ita_root/ita_api_ansible_execution_receiver/ $APP_PATH/
# COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
# COPY ./ita_root/messages/ $APP_PATH/messages/

# CMD ["httpd","-D","FOREGROUND"]

#
# Build for production
#
FROM    common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

# WORKDIR $APP_PATH

# COPY ./ita_root/ita_api_ansible_execution_receiver/config/httpd.conf/httpd.conf /etc/httpd/conf/httpd.conf
# COPY ./ita_root/ita_api_ansible_execution_receiver/config/httpd.conf/wsgi.conf /etc/httpd/conf.d/wsgi.conf

# COPY ./ita_root/ita_api_ansible_execution_receiver/ $APP_PATH/
# COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
# COPY ./ita_root/messages/ $APP_PATH/messages/

# USER $USERNAME

# CMD ["httpd","-D","FOREGROUND"]
