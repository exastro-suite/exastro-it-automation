#!/bin/bash
#
#   Copyright 2026 NEC Corporation
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
#

SHELL_DIR=$(realpath $(dirname $0))

DOCKER_COMMAND=$(which docker)

CONTAINER_ID_ITA_QDRANT=$(sudo ${DOCKER_COMMAND} ps -f name=ita-qdrant -q)
if [ -n "${CONTAINER_ID_ITA_QDRANT}" ]; then
    echo "RESTART CONTAINER ita-qdrant"
    sudo ${DOCKER_COMMAND} restart "${CONTAINER_ID_ITA_QDRANT}"
fi
