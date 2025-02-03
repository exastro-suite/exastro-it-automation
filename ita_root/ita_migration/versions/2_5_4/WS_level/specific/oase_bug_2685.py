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
import datetime

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.oase.const import oaseConst


def main(work_dir_path, ws_db):
    ###########################################################
    # oase_bug_2685py
    # T_OASE_EVENT_COLLECTION_PROGRESSの古いデータを削除
    #  最新レコード以外の、24Hを過ぎたものが対象
    ###########################################################
    g.applogger.info("[Trace][start] bug fix issue2685")

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

    # イベント収集設定テーブルからEVENT_COLLECTION_SETTINGS_IDを抽出
    data_list = ws_db.table_select(oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS)  # noqa: F841
    event_collection_settings_id_list = [data['EVENT_COLLECTION_SETTINGS_ID'] for data in data_list]

    # 24Hを過ぎた
    event_collections_progress_ttl = int(24 * 60 * 60)
    fetched_time_limit = int(datetime.datetime.now().timestamp()) - event_collections_progress_ttl

    for event_collection_settings_id in event_collection_settings_id_list:
        # イベント収集経過テーブルからfetched_timeの最新1件を取得
        data_list = ws_db.table_select(oaseConst.T_OASE_EVENT_COLLECTION_PROGRESS, "WHERE EVENT_COLLECTION_SETTINGS_ID = %s ORDER BY `FETCHED_TIME` DESC LIMIT 1", [event_collection_settings_id])
        if len(data_list) == 0:
            continue

        # 最新レコードのIDは退避
        event_collection_id = data_list[0]['EVENT_COLLECTION_ID']

        # 削除対象のデータがあるか
        ret = ws_db.table_count(oaseConst.T_OASE_EVENT_COLLECTION_PROGRESS, "WHERE `FETCHED_TIME` < %s and `EVENT_COLLECTION_ID` != %s and `EVENT_COLLECTION_SETTINGS_ID` = %s", [fetched_time_limit, event_collection_id, event_collection_settings_id])  # noqa: F841
        # g.applogger.info(f"{event_collection_id=}")
        # g.applogger.info(f"{event_collection_settings_id=}")
        # g.applogger.info(f"{ret=}")

        # 削除
        if ret > 0:
            ws_db.db_transaction_start()
            ret = ws_db.table_permanent_delete(oaseConst.T_OASE_EVENT_COLLECTION_PROGRESS, "WHERE `FETCHED_TIME` < %s and `EVENT_COLLECTION_ID` != %s and `EVENT_COLLECTION_SETTINGS_ID` = %s", [fetched_time_limit, event_collection_id, event_collection_settings_id])  # noqa: F841
            ws_db.db_transaction_end(True)

    g.applogger.info("[Trace][end] bug fix issue2685")
    return 0
