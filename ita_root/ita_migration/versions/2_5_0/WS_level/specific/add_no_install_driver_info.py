#   Copyright 2024 NEC Corporation
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
from common_libs.common.dbconnect import *  # noqa: F403


def main(work_dir_path, db_conn):
    # ###########################################################
    # # workspace単位のINFOテーブルに必要であればドライバ情報を追加
    # ###########################################################
    g.applogger.info("[Trace] Begin Add driver information if necessary to the info table for each workspace")
    common_db = DBConnectCommon()  # noqa: F405

    organization_id = g.ORGANIZATION_ID
    workspace_id = g.WORKSPACE_ID

    # organization単位のドライバ情報を取得する
    org_no_install_driver = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE ORGANIZATION_ID = '{}' AND DISUSE_FLAG = {}".format(organization_id, 0))[0]["NO_INSTALL_DRIVER"]
    common_db.db_disconnect()

    # workspace単位のドライバ情報の更新が必要な場合のみ処理を行う
    if org_no_install_driver is not None:
        org_db = DBConnectOrg(organization_id)  # noqa: F405
        primary_key = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE WORKSPACE_ID = '{}' AND DISUSE_FLAG = {}".format(workspace_id, 0))[0]['PRIMARY_KEY']

        # t_comn_workspace_db_infoテーブルのNO_INSTALL_DRIVERを更新する
        org_db.db_transaction_start()
        data = {
            'PRIMARY_KEY': primary_key,
            'NO_INSTALL_DRIVER': org_no_install_driver,
        }
        org_db.table_update('T_COMN_WORKSPACE_DB_INFO', data, 'PRIMARY_KEY')
        org_db.db_commit()
        org_db.db_disconnect()

    return 0
