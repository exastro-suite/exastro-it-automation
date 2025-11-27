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

from flask import g
import traceback
import json
from pymongo import ASCENDING

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import arrange_stacktrace_format
from common_libs.common.mongoconnect.const import Const as mongoConst
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs


def main(work_dir_path, wsdb):
    ############################################################
    # 【OASE】インデックスの追加
    ############################################################
    g.applogger.info("[Trace][start] create index mongodb 'labeled_event_collection'")
    # mongodbに対するアップデートなので、migrationのときしか実行しない（menu-export-importの対象外とするため）
    if g.SERVICE_NAME != "ita-migration":
        g.applogger.info("[Trace][skipped] create index mongodb 'labeled_event_collection'")
        return 0

    common_db = DBConnectCommon()  # noqa: F405

    organization_id = g.ORGANIZATION_ID
    workspace_id = g.WORKSPACE_ID

    # organization単位のドライバ情報を取得する
    org_no_install_driver = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE ORGANIZATION_ID = '{}' AND DISUSE_FLAG = {}".format(organization_id, 0))[0]["NO_INSTALL_DRIVER"]
    common_db.db_disconnect()

    # oaseインストール済みの場合しか対応しない
    org_no_install_driver = json.loads(org_no_install_driver) if org_no_install_driver is not None else {}
    if 'oase' in org_no_install_driver:
        g.applogger.info("[Trace][skipped] create index mongodb 'labeled_event_collection'")
        return 0

    try:
        ws_mongo = MONGOConnectWs()
        labeled_event_collection = ws_mongo.collection(mongoConst.LABELED_EVENT_COLLECTION)
        # 既存のインデックス情報を取得し、その中にインデックス名が見つかれば、抜ける
        index_list = labeled_event_collection.index_information()
        if "duplicate_check" in index_list:
            g.applogger.info("[Trace] Index[duplicate_check] already exists in 'labeled_event_collection'")
            ws_mongo.disconnect()
            return 0

        labeled_event_collection.create_index([("labels._exastro_fetched_time", ASCENDING), ("exastro_created_at", ASCENDING)], name="duplicate_check")
        ws_mongo.disconnect()
    except Exception:
        t = traceback.format_exc()
        g.applogger.error(arrange_stacktrace_format(t))

    g.applogger.info("[Trace][end] create index mongodb 'labeled_event_collection'")
    return 0

