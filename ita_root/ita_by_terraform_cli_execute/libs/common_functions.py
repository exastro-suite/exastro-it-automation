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


# def get_interface_info(wsDb, const):
#     """
#     インタフェース情報を取得

#     Arguments:
#         WsDb: db instance
#     Returns:
#         result: bool
#         record or err_msg:
#     """
#     condition = 'WHERE `DISUSE_FLAG`=0'
#     records = wsDb.table_select(const.T_IF_INFO, condition)
#     record_num = len(records)

#     if record_num == 0:
#         return False, "MSG-10048"
#     elif record_num != 1:
#         return False, "MSG-10049"

#     return True, records[0]


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


def get_execution_process_info(wsDb, const, execution_no):
    """
    作業実行の情報を取得

    Arguments:
        WsDb: db instance
        const: 共通定数オブジェクト
        execution_no: 作業番号
    Returns:
        result: bool
        record or err_msg:
    """
    condition = "WHERE `DISUSE_FLAG`=0 AND `EXECUTION_NO`=%s"
    records = wsDb.table_select(const.T_EXEC_STS_INST, condition, [execution_no])

    if len(records) == 0:
        return False, "MSG-10047"

    return True, records[0]


def update_execution_record(wsDb, const, update_data):
    """
    作業実行の情報を更新

    Arguments:
        WsDb: db instance
        const: 共通定数オブジェクト
        update_data: 更新データ
    Returns:
        result: bool
        record:
    """
    try:
        sql = "SELECT * FROM {} WHERE EXECUTION_NO=%s".format(const.T_EXEC_STS_INST)
        rows = wsDb.sql_execute(sql, [update_data['EXECUTION_NO']])
        res_data = rows[0]

        if "TIME_START" in update_data and res_data["TIME_START"]:
            del update_data["TIME_START"]
        if "TIME_END" in update_data and res_data["TIME_END"]:
            del update_data["TIME_END"]
        if "LAST_UPDATE_USER" not in update_data:
            update_data["LAST_UPDATE_USER"] = g.USER_ID

        result = wsDb.table_update(const.T_EXEC_STS_INST, [update_data], 'EXECUTION_NO')

        if result is False:
            wsDb.db_rollback()
            return False, None
        # transactionは呼び元で管理したいので、commitだけはやらない
        # else:
        #     wsDb.db_commit()

        for column, value in update_data.items():
            res_data[column] = value

        return True, res_data
    except AppException as e:
        wsDb.db_rollback()
        raise AppException(e)
