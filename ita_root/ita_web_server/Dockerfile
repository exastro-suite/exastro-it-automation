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

FROM    registry.access.redhat.com/ubi8/ubi-init

ARG USERNAME
ARG GROUPNAME
ARG APP_PATH

ENV LISTEN_PORT             80
ENV APACHE_PID_DIR          /var/run_$USERNAME/httpd/pid
ENV APACHE_SOCKET_DIR       /var/run_$USERNAME/httpd/socket
ENV APACHE_USERNAME         $USERNAME
ENV APACHE_GROUPNAME        $GROUPNAME

RUN dnf install -y httpd \
&&  groupadd $GROUPNAME \
&&  useradd -m -s /bin/bash -g $GROUPNAME $USERNAME \
&&  setcap 'cap_net_bind_service=+ep' /usr/sbin/httpd \
&&  chown $USERNAME:$GROUPNAME /var/log/httpd \
&&  mkdir -p $APACHE_PID_DIR \
&&  chown $USERNAME:$GROUPNAME $APACHE_PID_DIR \
&&  mkdir -p $APACHE_SOCKET_DIR \
&&  chown $USERNAME:$GROUPNAME $APACHE_SOCKET_DIR

COPY ./ita_root/ita_web_server/contents/ /var/www/html/
COPY ./ita_root/ita_web_server/config/httpd.conf/httpd.conf /etc/httpd/conf/httpd.conf
COPY ./ita_root/ita_web_server/config/httpd.conf/rewrite.conf /etc/httpd/conf.d/rewrite.conf

USER $USERNAME

CMD ["httpd","-D","FOREGROUND"]
