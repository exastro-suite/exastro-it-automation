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
import json
import os
import shutil

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import put_uploadfiles_jnl

def main(work_dir_path, ws_db):
    ###########################################################
    # jnl_patch_bug_2785
    ###########################################################
    g.applogger.info("[Trace][start] bug fix issue2785")

    common_db = DBConnectCommon()  # noqa: F405

    organization_id = g.ORGANIZATION_ID
    workspace_id = g.WORKSPACE_ID

    # organization単位のドライバ情報を取得する
    org_no_install_driver = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE ORGANIZATION_ID = '{}' AND DISUSE_FLAG = {}".format(organization_id, 0))[0]["NO_INSTALL_DRIVER"]
    common_db.db_disconnect()

    # oaseインストール済みの場合しか対応しない
    org_no_install_driver = json.loads(org_no_install_driver) if org_no_install_driver is not None else {}
    if 'oase' in org_no_install_driver:
        return 0

    table_name = "T_OASE_NOTIFICATION_TEMPLATE_COMMON"
    table_name_jnl = table_name + "_JNL"

    """v2.6までで、oaseがインストールされていない状態で作成し、後にoaseをインストールしたワークスペースへの対応
        対象の抽出条件と対処
            ・JOURNAL_SEQ_NOが{}-2のレコードがない場合に、jnlパッチをあてる
    """

    # 履歴内の{}-2のレコードがあれば、対象外
    jnl_id = "{}-2".format("1")
    jnl_record = ws_db.table_select(table_name_jnl, "WHERE `JOURNAL_SEQ_NO` = %s", [jnl_id])
    if len(jnl_record) != 0:
        return 0

    # jnl patchをかける
    ws_db.db_transaction_start()  # トランザクション

    src_dir = "versions/2_7_0/WS_level/specific/jnl_patch_bug_2785/"
    config_file_path = os.path.join(src_dir, "oase_config.json")
    dest_dir = os.path.join(work_dir_path, "uploadfiles")
    put_uploadfiles_jnl(ws_db, config_file_path, src_dir, dest_dir)
    # コミット
    ws_db.db_commit()

    g.applogger.info("[Trace][end] bug fix issue2785")
    return 0


