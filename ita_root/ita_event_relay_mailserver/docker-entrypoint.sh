#!/bin/bash
cat /etc/hosts | sed '/::/d' > /etc/hosts.new
cat /etc/hosts.new > /etc/hosts
mkdir /etc/sslcerts
openssl req -x509 -newkey rsa:2048 -keyout /etc/sslcerts/key.pem -out /etc/sslcerts/cert.pem -days 365 -nodes -subj "/CN=ita-mailserver"
exec /sbin/init