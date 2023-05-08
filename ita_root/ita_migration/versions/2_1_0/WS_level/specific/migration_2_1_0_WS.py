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

import os
from common_libs.common.dbconnect import *  # noqa: F403


def main(work_dir_path, db_conn):

    organization_id = db_conn.organization_id
    workspace_id = db_conn._workspace_id
    ws_db_name = db_conn._db

    # 同時実行数制御用のVIEW作成
    view_sql = "CREATE OR REPLACE VIEW V_ANSL_EXEC_STS_INST2 AS "
    view_sql += "SELECT %s as ORGANIZATION_ID, %s as WORKSPACE_ID, %s as WORKSPACE_DB, 'V_ANSL_EXEC_STS_INST2' AS VIEW_NAME, EXECUTE_HOST_NAME, "
    view_sql += "'Legacy' as DRIVER_NAME, 'L' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER "
    view_sql += "FROM T_ANSL_EXEC_STS_INST "
    view_sql += "WHERE DISUSE_FLAG = %s "
    db_conn.sql_execute(view_sql, [organization_id, workspace_id, ws_db_name, 0])
    view_sql = "CREATE OR REPLACE VIEW V_ANSP_EXEC_STS_INST2 AS "
    view_sql += "SELECT %s as ORGANIZATION_ID, %s as WORKSPACE_ID, %s as WORKSPACE_DB, 'V_ANSP_EXEC_STS_INST2' AS VIEW_NAME, EXECUTE_HOST_NAME, "
    view_sql += "'Pioneer' as DRIVER_NAME, 'P' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER "
    view_sql += "FROM T_ANSP_EXEC_STS_INST "
    view_sql += "WHERE DISUSE_FLAG = %s "
    db_conn.sql_execute(view_sql, [organization_id, workspace_id, ws_db_name, 0])
    view_sql = "CREATE OR REPLACE VIEW V_ANSR_EXEC_STS_INST2 AS "
    view_sql += "SELECT %s as ORGANIZATION_ID, %s as WORKSPACE_ID, %s as WORKSPACE_DB, 'V_ANSR_EXEC_STS_INST2' AS VIEW_NAME, EXECUTE_HOST_NAME, "
    view_sql += "'Legacy-Role' as DRIVER_NAME, 'R' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER "
    view_sql += "FROM T_ANSR_EXEC_STS_INST "
    view_sql += "WHERE DISUSE_FLAG = %s "
    db_conn.sql_execute(view_sql, [organization_id, workspace_id, ws_db_name, 0])

    org_root_db = DBConnectOrgRoot(organization_id)  # noqa: F405

    # 権限付与
    view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSL_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
    org_root_db.sql_execute(view_sql, [])
    view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSP_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
    org_root_db.sql_execute(view_sql, [])
    view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSR_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
    org_root_db.sql_execute(view_sql, [])

    return 0
