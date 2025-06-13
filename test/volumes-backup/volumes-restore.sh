#!/bin/bash

#   Copyright 2025 NEC Corporation
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

BASEDIR=$(realpath $(dirname "$0"))
BASENAME=$(basename "$0")
REPOROOT=$(realpath "${BASEDIR}/../..")

CONTAINER_PREFIX="exastro"
BACKUP_DIR="${BASEDIR}/backup-data"


if [ -n "$1" ]; then
    RESTORE_FILE="$1"
    if [ ! -e "${RESTORE_FILE}" ]; then
        echo "Error: Not found backup file: $1"
        exit 1
    fi

else
    RESTORE_FILE=$(ls -t ${BACKUP_DIR}/backup_volumes-*.tgz | head -n 1)
    if [ -z "${RESTORE_FILE}" ]; then
        echo "Error: Not found backup file"
        exit 1
    fi
fi

echo "---------------------------------------------------------------------------------"
echo "-- Start ${BASENAME}"
echo "---------------------------------------------------------------------------------"

echo
echo "-- Start Container pause"
sudo docker container pause ${CONTAINER_PREFIX}-keycloak-1
sudo docker container pause ${CONTAINER_PREFIX}-platform-db-1
sudo docker container pause ${CONTAINER_PREFIX}-ita-mariadb-1
if [ "$(sudo docker ps -f name=${CONTAINER_PREFIX}-ita-mongodb-1 -q | wc -l)" -eq 1 ]; then
    sudo docker container pause "${CONTAINER_PREFIX}-ita-mongodb-1"
fi

echo
echo "-- Crean volumes"
sudo rm -rf "${REPOROOT}/.volumes/*"

echo
echo "-- Restore volumes : ${RESTORE_FILE}"
sudo tar xvfz "${RESTORE_FILE}" -C "${REPOROOT}" > /dev/null
echo "tar command exit code($?)"

echo
echo "-- Start Container restart"
sudo docker container restart ${CONTAINER_PREFIX}-ita-mariadb-1
sudo docker container restart ${CONTAINER_PREFIX}-platform-db-1
sudo docker container restart ${CONTAINER_PREFIX}-keycloak-1
if [ "$(sudo docker ps -f name=${CONTAINER_PREFIX}-ita-mongodb-1 -q | wc -l)" -eq 1 ]; then
    sudo docker container restart "${CONTAINER_PREFIX}-ita-mongodb-1"
fi

echo "---------------------------------------------------------------------------------"
echo "-- Finish ${BASENAME}"
echo "---------------------------------------------------------------------------------"
exit 0
