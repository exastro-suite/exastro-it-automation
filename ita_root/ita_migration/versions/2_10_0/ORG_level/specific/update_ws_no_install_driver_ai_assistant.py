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

import inspect
import json
from flask import g
import os


AI_ASSISTANT_DRIVER_NAME = "ai_assistant"


def main(work_dir_path, org_db):
    """T_COMN_WORKSPACE_DB_INFOテーブルのNO_INSTALL_DRIVERにai_assistantを設定

    2.9.0のマイグレーションでは、既存オーガナイゼーションのNO_INSTALL_DRIVERにのみai_assistantを追加しており、
    既存ワークスペースのNO_INSTALL_DRIVERは更新していない。
    そのままだとドライバ追加APIでai_assistantを有効にしても、ワークスペースはインストール済みと判定されSQLが実行されないため、
    オーガナイゼーションでai_assistantが無効の場合に限り、ワークスペースのNO_INSTALL_DRIVERにもai_assistantを追加する。

    The 2.9.0 migration added ai_assistant only to NO_INSTALL_DRIVER of existing organizations,
    and did not update NO_INSTALL_DRIVER of existing workspaces.
    In that state, enabling ai_assistant with the driver add API treats the workspaces as already installed and skips the SQL,
    so ai_assistant is also added to NO_INSTALL_DRIVER of the workspaces, only when ai_assistant is disabled in the organization.

    Args:
        work_dir_path (str): 作業フォルダパス / Work directory path
        org_db (obj): オーガナイゼーションDB接続オブジェクト / Organization DB connection object

    Returns:
        int: 0:正常終了 / Normal termination
             0以外:異常終了 / Abnormal termination
    """

    g.applogger.info(f"[Trace][start] {os.path.splitext(os.path.basename(inspect.currentframe().f_code.co_filename))[0]}")

    # オーガナイゼーションでai_assistantが有効の場合は何もしない
    # Do nothing if ai_assistant is enabled in the organization
    org_no_install_driver_json = org_db.get_no_install_driver()
    org_no_install_driver = json.loads(org_no_install_driver_json) if org_no_install_driver_json else []
    if AI_ASSISTANT_DRIVER_NAME not in org_no_install_driver:
        g.applogger.info(f"[Trace] SKIP BECAUSE {AI_ASSISTANT_DRIVER_NAME} IS INSTALLED IN ORGANIZATION.")
        g.applogger.info(f"[Trace][end] {os.path.splitext(os.path.basename(inspect.currentframe().f_code.co_filename))[0]}")
        return 0

    workspace_data_list = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`=0")

    # トランザクション開始
    # Start transaction
    org_db.db_transaction_start()

    for workspace_data in workspace_data_list:
        ws_no_install_driver_json = workspace_data.get('NO_INSTALL_DRIVER')
        ws_no_install_driver = json.loads(ws_no_install_driver_json) if ws_no_install_driver_json else []
        if AI_ASSISTANT_DRIVER_NAME in ws_no_install_driver:
            continue

        ws_no_install_driver.append(AI_ASSISTANT_DRIVER_NAME)
        data = {
            'PRIMARY_KEY': workspace_data['PRIMARY_KEY'],
            'NO_INSTALL_DRIVER': json.dumps(ws_no_install_driver),
        }
        org_db.table_update('T_COMN_WORKSPACE_DB_INFO', data, 'PRIMARY_KEY')
        g.applogger.info(f"[Trace] Add {AI_ASSISTANT_DRIVER_NAME} to NO_INSTALL_DRIVER of workspace(workspace_id={workspace_data['WORKSPACE_ID']})")

    # トランザクションコミット
    # Commit transaction
    org_db.db_commit()

    g.applogger.info(f"[Trace][end] {os.path.splitext(os.path.basename(inspect.currentframe().f_code.co_filename))[0]}")

    return 0
