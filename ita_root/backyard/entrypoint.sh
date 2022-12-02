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

while true
do
    # start_time=`date +%s`
    # echo "backyard_init start = "`date "+%Y-%m-%d %H:%M:%S"` >> /exastro/app.log

    cd /exastro
    # python3 backyard/backyard_init.py | tee -a /exastro/app.log
    python3 backyard/backyard_init.py

    # echo "backyard_init end = "`date "+%Y-%m-%d %H:%M:%S"` >> /exastro/app.log
    # end_time=`date +%s`
    # run_time=$((end_time - start_time))
    # echo "backyard_init execute-time = "$run_time >> /exastro/app.log

    sleep $EXECUTE_INTERVAL
done
