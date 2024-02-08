
# FROM    registry.access.redhat.com/ubi8/ubi-init as develop_build
FROM almalinux:8 as develop_build

# WORKDIR /etc/dnf.repos.d
WORKDIR /etc/yum.repos.d
RUN for i in `ls -1`;do sed -i.org -e "/^gpgcheck.*/i sslverify=0" $i;done

WORKDIR /
# RUN dnf -y install dovecot \
RUN yum -y install dovecot \
    postfix \
    mailx \
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
