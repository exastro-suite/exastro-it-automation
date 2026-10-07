#   Copyright 2026 NEC Corporation
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
ARG EMBEDDING_MODEL=snowflake/snowflake-arctic-embed-xs
ARG EMBEDDING_MODEL_CACHE_PATH=/embedding_model

FROM    registry.access.redhat.com/ubi9/ubi-init:9.4 as common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH
ARG EMBEDDING_MODEL
ARG EMBEDDING_MODEL_CACHE_PATH

ENV PYTHONPATH=/exastro/
ENV DEFAULT_LANGUAGE=ja
ENV STORAGEPATH=/storage/
ENV LISTEN_PORT             8000
ENV APACHE_PID_DIR          /var/run_$USERNAME/httpd/pid
ENV APACHE_SOCKET_DIR       /var/run_$USERNAME/httpd/socket
ENV APACHE_TIMEOUT          300
ENV APACHE_USERNAME         $USERNAME
ENV APACHE_GROUPNAME        $GROUPNAME
ENV DB_CONNECT_TIMEOUT=10
ENV DB_CONNECT_RETRY_SLEEP_TIME=0.5
ENV DB_CONNECT_RETRY_LIMIT=2
ENV SERVICE_NAME=ita-api-mcp-server

ENV WSGI_PROCESSES=1
ENV WSGI_THREADS=15
ENV WSGI_MAX_REQUESTS=2000
ENV WSGI_GRACEFUL_TIMEOUT=300

# EMBEDDING MODEL設定
ENV EMBEDDING_MODEL             $EMBEDDING_MODEL
ENV EMBEDDING_MODEL_CACHE_PATH  $EMBEDDING_MODEL_CACHE_PATH

# ハイブリッドスコアにおけるベクトルスコアの重み(0.0-1.0)。値が大きいほど
# ベクトル検索(意味的な類似度)を重視し、小さいほどキーワードマッチングを重視する。
ENV HYBRID_SEARCH_ALPHA 0.9

# キーワードスコア計算において、タイトルへのマッチをテキストへのマッチの
# 何倍重視するかの重み。
ENV TITLE_MATCH_WEIGHT  3

# menu filterツールのfile=yesで最大取得可能なレコード件数
ENV MENU_FILTER_FILE_RECORD_LIMIT 5

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    dnf install -y \
    gcc \
    hostname \
    httpd \
    httpd-devel \
    langpacks-en \
    wget \
    zip \
    unzip \
    python3.11 \
    python3.11-devel \
    python3.11-mod_wsgi \
    python3.11-pip \
    --exclude=python3.11-setuptools \
&&  alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1000000 \
&&  alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 100 \
&&  alternatives --set python3 /usr/bin/python3.11 \
&&  pip3.11 install poetry==1.8.4 \
&&  poetry config virtualenvs.create false \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME \
&&  setcap 'cap_net_bind_service=+ep' /usr/sbin/httpd \
&&  chown $USERNAME:$GROUPNAME /var/log/httpd \
&&  mkdir -p $APACHE_PID_DIR \
&&  chown $USERNAME:$GROUPNAME $APACHE_PID_DIR \
&&  mkdir -p $APACHE_SOCKET_DIR \
&&  chown $USERNAME:$GROUPNAME $APACHE_SOCKET_DIR

WORKDIR $APP_PATH

COPY ./ita_root/ita_api_mcp_server/pyproject.toml ./ita_root/ita_api_mcp_server/poetry.lock $APP_PATH/

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    poetry install --only first_install

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    poetry install --without develop_build

# embedding_modelのダウンロード
COPY ./ita_root/ita_api_mcp_server/download_embedding_model.py $APP_PATH/

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    mkdir -p $EMBEDDING_MODEL_CACHE_PATH \
&&  python3 $APP_PATH/download_embedding_model.py --model-name $EMBEDDING_MODEL --cache-path $EMBEDDING_MODEL_CACHE_PATH \
&&  chown -R $USERNAME:$GROUPNAME $EMBEDDING_MODEL_CACHE_PATH

ENV HF_HUB_OFFLINE 1
ENV TRANSFORMERS_OFFLINE 1

#
# Build for development
#   Specify options when creating this image: --target develop_build
#
FROM    common_build as develop_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo \
&&  dnf install -y \
    sudo \
    git \
    zip \
    vim \
    diffutils \
    bind-utils \
    iputils \
    docker-ce-cli \
    jq \
&&  usermod -G wheel $USERNAME \
&&  echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers \
&&  echo "%${GROUPNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    poetry install --with develop_build

USER $USERNAME

RUN mkdir ~/.config \
&& mkdir ~/.vscode-server \
&& mkdir ~/.vscode-server-insiders

WORKDIR $APP_PATH

COPY ./ita_root/ita_api_mcp_server/config/httpd.conf/httpd.conf /etc/httpd/conf/httpd.conf
COPY ./ita_root/ita_api_mcp_server/config/httpd.conf/wsgi.conf /etc/httpd/conf.d/wsgi.conf

COPY ./ita_root/ita_api_mcp_server/ $APP_PATH/
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

COPY ./ita_root/ita_api_mcp_server/config/httpd.conf/httpd.conf /etc/httpd/conf/httpd.conf
COPY ./ita_root/ita_api_mcp_server/config/httpd.conf/wsgi.conf /etc/httpd/conf.d/wsgi.conf

COPY ./ita_root/ita_api_mcp_server/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/

USER $USERNAME

CMD ["httpd","-D","FOREGROUND"]
