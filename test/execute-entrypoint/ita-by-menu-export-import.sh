#!/bin/bash
DOCKER_CMD=$(which docker)
sudo ${DOCKER_CMD} exec -it exastro-ita-by-menu-export-import-1 bash /exastro/backyard/entrypoint.sh

