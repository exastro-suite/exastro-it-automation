#!/bin/bash

BASENAME=$(basename "$0")
BASEPATH=$(dirname "$0")

# check docker-compose command
which docker-compose &> /dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] not found docker-compose command"
    exit 1
fi

# check command parameter
if [ $# -ne 1 ]; then
    echo "[ERROR] Usage : ${BASENAME} dumpfile_path"
    exit 1
fi

PARAM_DUMPFILE_PATH=$1
PARAM_DUMPFILE=$(basename "${PARAM_DUMPFILE_PATH}")

TMPPATH=/tmp

if [ -f "${PARAM_DUMPFILE}" ]; then
    echo "[ERROR] not found dumpfile : ${PARAM_DUMPFILE}"
    exit 1
fi

# pause keycloak
docker-compose -p devcontainer pause keycloak

# import db
docker cp ${PARAM_DUMPFILE_PATH} devcontainer-platform-db-1:${TMPPATH}/${PARAM_DUMPFILE}
docker exec -it devcontainer-platform-db-1 bash -c "mysql -u root --password=\${MYSQL_ROOT_PASSWORD} < ${TMPPATH}/${PARAM_DUMPFILE}"

# restart keycloak
docker-compose -p devcontainer restart keycloak

echo "[INFO] ${BASENAME} Succeceful."
