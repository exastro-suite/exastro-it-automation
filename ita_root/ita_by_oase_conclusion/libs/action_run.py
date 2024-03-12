# Copyright 2024 NEC Corporation#
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

from common_libs.conductor.classes.exec_util import *
# from common_libs.oase.const import oaseConst

def action_run(objdbca, action_log_row):
    conductor_class_id = action_log_row["CONDUCTOR_INSTANCE_ID"]
    operation_id = action_log_row["OPERATION_ID"]

    return conductor_execute(objdbca, conductor_class_id, operation_id)

def conductor_execute(wsDb, conductor_class_id, operation_id):
    """
    conductorを実行する（関数を呼ぶ）
    ARGS:
        wsDb:DB接続クラス  DBConnectWs()
        conductor_class_id:
        operation_id:
    RETURN:
    """
    objcbkl = ConductorExecuteBkyLibs(wsDb)  # noqa: F405
    parameter = {"conductor_class_id": conductor_class_id, "operation_id": operation_id}
    _res = objcbkl.conductor_execute_no_transaction(parameter)
    return _res
