#   Copyright 2025 NEC Corporation
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

import inspect
from flask import g
import json
import os


def main(work_dir_path, ws_db):
    """t_comn_conductor_regularly_listのmigration対応(Issue#2872)

    Args:
        work_dir_path (str): 作業フォルダパス / Work directory path
        ws_db (obj): ワークスペースDB接続オブジェクト / Workspace DB connection object

    Returns:
        int: 0:正常終了 / Normal termination
             0以外:異常終了 / Abnormal termination
    """
    
    g.applogger.info(f"[Trace][start] {os.path.splitext(os.path.basename(inspect.currentframe().f_code.co_filename))[0]}")

    # t_comn_conductor_regularly_list の更新
    # Update of t_comn_conductor_regularly_list
    table_name = "T_COMN_CONDUCTOR_REGULARLY_LIST"
    table_name_jnl = table_name + "_JNL"

    # 冪等性があるので、トランザクションは発行しない
    # Since idempotent, do not issue a transaction

    # 曜日分更新（纏めてでもよいが、確実に更新するために１曜日単位で実行）
    # Update each weekday individually to ensure reliable execution (batch update is possible but not recommended)
    for i in range(7):
        parameter = {
            "pattern_day_of_week_id": f'{i + 1}',
            "pattern_day_of_week_id_json_str": json.dumps({"id": [str(i + 1)]})
        }
        
        # 曜日ごとに更新
        # Update for each day of the week
        for table in [table_name, table_name_jnl]:
            sql = f"UPDATE `{table}` SET PATTERN_DAY_OF_WEEK_ID = %(pattern_day_of_week_id_json_str)s WHERE PATTERN_DAY_OF_WEEK_ID IS NOT NULL AND PATTERN_DAY_OF_WEEK_ID = %(pattern_day_of_week_id)s"
            g.applogger.debug(f"{sql=}")
            ws_db.sql_execute(sql, parameter)

    ws_db.db_commit()

    g.applogger.info(f"[Trace][end] {os.path.splitext(os.path.basename(inspect.currentframe().f_code.co_filename))[0]}")

    return 0
