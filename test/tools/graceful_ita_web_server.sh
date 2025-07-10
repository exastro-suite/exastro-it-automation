#!/bin/bash

CONTAINER=exastro-ita-web-server-1
sudo docker exec "${CONTAINER}" httpd -k graceful
echo "[INFO] ${CONTAINER}  graceful succeceful."