
# FROM    registry.access.redhat.com/ubi9/ubi-init as develop_build
FROM almalinux:9.4 as develop_build

# WORKDIR /etc/dnf.repos.d
WORKDIR /etc/yum.repos.d
RUN for i in `ls -1`;do sed -i.org -e "/^gpgcheck.*/i sslverify=0" $i;done

WORKDIR /
# RUN dnf -y install dovecot \

RUN --mount=type=secret,id=host_certificate_file,dst=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
    yum -y install dovecot \
    postfix \
#    mailx \
    s-nail \
    telnet \
    rsyslog \
    passwd \
    openssl \
&& echo '[ -f /usr/sbin/rsyslogd ] && /usr/sbin/rsyslogd' >> $HOME/.bash_profile \
&& sed -i -e '/$ModLoad imjournal/s/^/#/' /etc/rsyslog.conf \
&& sed -i -e 's/$OmitLocalLogging on/$OmitLocalLogging off/' /etc/rsyslog.conf \
&& sed -i -e '/$IMJournalStateFile/s/^/#/' /etc/rsyslog.conf \
&& ln -s /usr/lib/systemd/system/dovecot.service /etc/systemd/system/multi-user.target.wants/dovecot.service \
&& ln -s /usr/lib/systemd/system/postfix.service /etc/systemd/system/multi-user.target.wants/postfix.service

COPY ./ita_root/ita_oase_mailserver/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
