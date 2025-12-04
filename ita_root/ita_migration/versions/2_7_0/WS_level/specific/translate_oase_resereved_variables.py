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
import json
import re

from common_libs.common.dbconnect import *  # noqa: F403


def main(work_dir_path, ws_db):
    ###########################################################
    # translate oase resereved variables
    # 既にあった予約変数（EXASTRO_LAST_FETCHED_YY_MM_DDなど）をjinja2用の変数に置換を行う
    ###########################################################
    g.applogger.info("[Trace][start] translate oase resereved variables")
    common_db = DBConnectCommon()  # noqa: F405

    organization_id = g.ORGANIZATION_ID
    workspace_id = g.WORKSPACE_ID

    # organization単位のドライバ情報を取得する
    org_no_install_driver = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE ORGANIZATION_ID = '{}' AND DISUSE_FLAG = {}".format(organization_id, 0))[0]["NO_INSTALL_DRIVER"]
    common_db.db_disconnect()

    # oaseインストール済みの場合しか対応しない
    org_no_install_driver = json.loads(org_no_install_driver) if org_no_install_driver is not None else {}
    if 'oase' in org_no_install_driver:
        g.applogger.info("[Trace][skipped] translate oase resereved variables")
        return 0

    records = ws_db.table_select('T_OASE_EVENT_COLLECTION_SETTINGS')
    if len(records) == 0:
        return 0

    # トランザクション
    ws_db.db_transaction_start()

    for record in records:
        value = record["PARAMETER"]

        for variable in ["EXASTRO_LAST_FETCHED_YY_MM_DD", "EXASTRO_LAST_FETCHED_DD_MM_YY", "EXASTRO_LAST_FETCHED_TIMESTAMP"]:
            pattern = fr"{{{{( )*{variable}( )*}}}}"
            # レコードのPARAMETERカラムに入っている予約変数の値を{{}}つきに置換する
            # カラムに値がある、かつ、既に{{}}つきの変数が入っていることはない（パッチ当て環境などを考慮）、かつ、予約変数を利用している
            if value and re.search(pattern, value) is None and re.search(fr"{variable}", value):
                value = value.replace(variable, f"{{{{ {variable} }}}}")
                record["PARAMETER"] = value

                update_data = {
                    "EVENT_COLLECTION_SETTINGS_ID": record["EVENT_COLLECTION_SETTINGS_ID"],
                    "PARAMETER": value
                }
                ws_db.table_update('T_OASE_EVENT_COLLECTION_SETTINGS', update_data, "EVENT_COLLECTION_SETTINGS_ID", True)

    # コミット
    ws_db.db_commit()

    g.applogger.info("[Trace][end] translate oase resereved variables")
    return 0


