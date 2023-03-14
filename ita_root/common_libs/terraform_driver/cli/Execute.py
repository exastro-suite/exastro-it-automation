#   Copyright 2023 NEC Corporation
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
from flask import g
import os
import pathlib

from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
from common_libs.common.exception import AppException


def execution_scram(objdbca, execution_no):
    """
        緊急停止を実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            execution_no: 作業実行ID
        RETRUN:
            boolean
    """
    # ステータスを確認するのでテーブルをロック
    objdbca.table_lock(TFCLIConst.T_EXEC_STS_INST)

    # 作業実行IDの対象が存在することを確認
    where_str = 'WHERE EXECUTION_NO = %s AND DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCLIConst.T_EXEC_STS_INST, where_str, [execution_no, 0])
    if not ret:
        # 指定された作業番号が存在しない。
        raise AppException("499-00903", [execution_no], [execution_no])
    t_exec_sts_inst_record = ret[0]

    # ステータスが「実行中」「実行中(遅延)」であるかを判定
    status_id = t_exec_sts_inst_record.get('STATUS_ID')
    if not str(status_id) == TFCLIConst.STATUS_PROCESSING and not str(status_id) == TFCLIConst.STATUS_PROCESS_DELAYED:
        # ステータスが「実行中」「実行中(遅延)」以外の場合は、緊急停止対象外のため終了
        if g.LANGUAGE == 'ja':
            sql = "SELECT EXEC_STATUS_NAME_JA AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
        else:
            sql = "SELECT EXEC_STATUS_NAME_EN AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
        rows = objdbca.sql_execute(sql, [str(status_id)])
        row = rows[0]
        #  緊急停止できる状態ではない
        raise AppException("499-00904", [row["NAME"]], [row["NAME"]])

    # 緊急停止処理を実行
    tf_workspace_id = t_exec_sts_inst_record.get('I_WORKSPACE_ID')
    base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
    workspace_work_dir = base_dir + TFCLIConst.DIR_WORK + "/{}/work".format(tf_workspace_id)  # CLI実行場所
    emergency_stop_file_path = workspace_work_dir + "/" + TFCLIConst.FILE_EMERGENCY_STOP  # 緊急停止ファイル
    p = pathlib.Path(emergency_stop_file_path)
    p.touch(mode=0o777, exist_ok=False)  # ファイルが既にあればException

    return True
