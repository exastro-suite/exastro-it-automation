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

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs


def main(work_dir_path, wsdb):
    # ###########################################################
    # # 【OASE】元データを保管するコレクションevent_collectionを削除 #2557
    # ###########################################################
    g.applogger.info("[Trace] drop the collection of mongodb 'event_collection'")
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

    ws_mong = MONGOConnectWs()
    ws_mong.collection("event_collection").drop()
    ws_mong.disconnect()

    return 0

