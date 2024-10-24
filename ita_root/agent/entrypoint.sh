#!/bin/bash

# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
set -eu

if [ $# -eq 4 ]; then
    export ENVFILEPATH=$1
    export PYTHONPATH=$2/
    export STORAGEPATH=$3
    export PYTHONCMD=$4
else
    PYTHONPATH=/exastro
    PYTHONCMD=python3
fi

while true
do
    # start_time=`date +%s`
    # echo "agent_init start = "`date "+%Y-%m-%d %H:%M:%S"` >> /exastro/app.log

    cd ${PYTHONPATH}
    # python3 agent/agent_init.py | tee -a /exastro/app.log
    # python3 agent/agent_init.py or ~~/poetry run python3 agent/agent_init.py
    ${PYTHONCMD} agent/agent_init.py

    # echo "agent_init end = "`date "+%Y-%m-%d %H:%M:%S"` >> /exastro/app.log
    # end_time=`date +%s`
    # run_time=$((end_time - start_time))
    # echo "agent_init execute-time = "$run_time >> /exastro/app.log

done
