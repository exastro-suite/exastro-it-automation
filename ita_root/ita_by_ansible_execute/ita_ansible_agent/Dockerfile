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

FROM    registry.access.redhat.com/ubi8/ubi-init
ARG USERNAME
ARG GROUPNAME

RUN dnf install -y \
    openssh-clients \
    python39 \
    python39-devel \
    sshpass \
&&  pip3.9 install --upgrade pip setuptools \
&&  pip3.9 install \
    ansible \
    pexpect \
    pywinrm \
    boto3 \
    paramiko \
    boto \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME

COPY ./ita_root/ita_by_ansible_execute/ita_ansible_agent/config/centos8.repo /etc/yum.repos.d/centos8.repo
RUN dnf install -y --enablerepo=baseos expect

COPY ./ita_root/ita_by_ansible_execute/ita_ansible_agent/config/ansible.cfg /etc/ansible/ansible.cfg

USER $USERNAME

CMD ["ansible-playbook"]
