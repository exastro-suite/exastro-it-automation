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
from flask import g
from common_libs.common.exception import AppException


def get_ansible_interface_info(wsDb):
    """
    ANSIBLEインタフェース情報を取得
    
    Arguments:
        WsDb: db instance
    Returns:
        result: bool
        record or err_msg:
    """
    condition = 'WHERE `DISUSE_FLAG`=0'
    records = wsDb.table_select('T_ANSC_IF_INFO', condition)
    record_num = len(records)

    if record_num == 0:
        return False, "MSG-10048"
    elif record_num != 1:
        return False, "MSG-10049"

    return True, records[0]


def get_conductor_interface_info(wsDb):
    """
    Conductorインタフェース情報を取得
    
    Arguments:
        WsDb: db instance
    Returns:
        result: bool
        record or err_msg:
    """
    condition = 'WHERE `DISUSE_FLAG`=0'
    records = wsDb.table_select('T_COMN_CONDUCTOR_IF_INFO', condition)
    record_num = len(records)

    if record_num == 0:
        return False, "MSG-10065"
    elif record_num != 1:
        return False, "MSG-10066"

    return True, records[0]


def get_execution_process_info(wsDb, execution_no):
    """
    作業実行の情報を取得
    
    Arguments:
        WsDb: db instance
    Returns:
        result: bool
        record or err_msg:
    """
    condition = "WHERE `DISUSE_FLAG`=0 AND `EXECUTION_NO`=%s"
    records = wsDb.table_select('T_ANSR_EXEC_STS_INST', condition, [execution_no])

    if len(records) == 0:
        return False, "MSG-10047"

    return True, records[0]


def update_execution_record(wsDb, data):
    """
    作業実行の情報を更新
    
    Arguments:
        WsDb: db instance
        data: 更新データ
    Returns:
        result: bool
        record:
    """
    try:
        if "LAST_UPDATE_USER" not in data:
            data["LAST_UPDATE_USER"] = g.USER_ID
        result = wsDb.table_update('T_ANSR_EXEC_STS_INST', [data], 'EXECUTION_NO')
        return True, result
    except AppException as e:
        wsDb.db_rollback()
        raise AppException(e)
