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
from common_libs.common.util import get_timestamp
from common_libs.common.exception import AppException
from flask import g


def operation_LAST_EXECUTE_TIMESTAMP_update(wsDb, operation_id):
    try:
        # 最終実施日を設定する
        data = {
            "OPERATION_ID": operation_id,
            "LAST_EXECUTE_TIMESTAMP": get_timestamp(),
            "LAST_UPDATE_USER": g.USER_ID
        }
        result = wsDb.table_update('T_COMN_OPERATION', [data], 'OPERATION_ID')
        return True, result
    except AppException as e:
        wsDb.db_rollback()
        raise AppException(e)
