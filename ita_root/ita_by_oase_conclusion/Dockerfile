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

FROM    registry.access.redhat.com/ubi9/ubi-init:9.4 as common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH
ENV PYTHONPATH=/exastro/
ENV USER_ID=110102
ENV EXECUTE_INTERVAL=1
ENV LANGUAGE=en
ENV STORAGEPATH=/storage/
ENV DB_CONNECT_TIMEOUT=10
ENV DB_CONNECT_RETRY_SLEEP_TIME=0.5
ENV DB_CONNECT_RETRY_LIMIT=2
ENV SERVICE_NAME=ita-by-oase-conclusion
ENV NOTIFICATION_BUFFER_SIZE=100

ENV EVALUATE_LATENT_INFINITE_LOOP_LIMIT=1000
# ハングアップ監視用ファイル
ENV FILE_PATH_LIVENESS=/tmp/liveness

ENV PATH /opt/pypy/bin:$PATH

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    set -eux; \
    dnf install -y \
    gcc \
    openssh-clients \
    langpacks-en \
    wget \
    zip \
    unzip \
    bzip2 \
    jq \
    python3.11 \
    python3.11-devel \
    python3.11-pip \
&&  alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 100 \
&&  alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1000000 
# &&  alternatives --set python3 /usr/bin/python3.11 \
#\
# start pypy install  
RUN set -eux; \
    python_version="3.11" \
&&  pypy_version="7.3" \
&&  platform="linux" \
&&  unameArch="$(uname -m)" \
&&  case "$unameArch" in \
        'x86_64' | 'x64' | 'amd64') arch='x64'; ;; \
        'aarch64') arch='aarch64'; ;; \
        'i686' | 'i386' | 'x86') arch='i686'; ;; \
        *) echo >&2 "error: current architecture ($unameArch) does not have a corresponding PyPy binary release"; exit 1 ;; \
    esac \
&&  pypy_download_url=$( \
        wget --progress=dot:giga -O- https://downloads.python.org/pypy/versions.json \
        | jq \
            --arg pypy_version "$pypy_version" \
            --arg python_version "$python_version" \
            --arg platform "$platform" \
            --arg arch "$arch" \
            -r \
            ''' \
            map( \
                select( \
                    .stable \
                    and (.pypy_version | startswith($ARGS.named.pypy_version)) \
                    and (.python_version | startswith($ARGS.named.python_version)) \
                ) \
            ) \
            | sort_by(-(.pypy_version | ltrimstr($ARGS.named.pypy_version + ".") | tonumber)) \
            | first.files[] \
            | select(.platform == $ARGS.named.platform and .arch == $ARGS.named.arch).download_url \
            ''' \
    ) \
&&  wget --progress=dot:giga -O pypy.tar.bz2 "${pypy_download_url}" \
&&  mkdir /opt/pypy \
&&  tar -xjC /opt/pypy --strip-components=1 -f pypy.tar.bz2 \
&&  find /opt/pypy/lib* -depth -type d -a \( -name test -o -name tests \) -exec rm -rf '{}' + \
&&  rm pypy.tar.bz2 \
&&  dnf remove -y bzip2 jq \
&&  ln -sv '/opt/pypy/bin/pypy3' /usr/local/bin/ \
&&  alternatives --install /usr/bin/python3 python3 /opt/pypy/bin/python3.11 50 \
&&  alternatives --set python3 /opt/pypy/bin/python3.11 \
&&  alternatives --install /usr/bin/pip3.11 pip3.11 /opt/pypy/bin/pip3.11 50 \
&&  alternatives --set pip3.11 /opt/pypy/bin/pip3.11 \
&&  python3 -m ensurepip \
&&  pip3.11 install --disable-pip-version-check --no-cache-dir --no-compile 'wheel<0.46' \
&& 	find /opt/pypy -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' + \
# end pypy install
&&  pip3.11 install poetry==1.8.4 \
&&  poetry config virtualenvs.create false \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME

WORKDIR $APP_PATH

COPY ./ita_root/ita_by_oase_conclusion/pyproject.toml ./ita_root/ita_by_oase_conclusion/poetry.lock $APP_PATH/

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    poetry install --only first_install \
&&  poetry install --without develop_build

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

COPY ./ita_root/ita_by_oase_conclusion/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/
COPY ./ita_root/backyard/ $APP_PATH/backyard/

ENTRYPOINT ["bash", "./backyard/entrypoint.sh"]

#
# Build for production
#
FROM    common_build
ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

USER $USERNAME
WORKDIR $APP_PATH

COPY ./ita_root/ita_by_oase_conclusion/ $APP_PATH/
COPY ./ita_root/common_libs/ $APP_PATH/common_libs/
COPY ./ita_root/messages/ $APP_PATH/messages/
COPY ./ita_root/backyard/ $APP_PATH/backyard/

USER root
RUN chmod a+x $APP_PATH/backyard/entrypoint.sh
USER $USERNAME

ENTRYPOINT ["bash", "./backyard/entrypoint.sh"]
