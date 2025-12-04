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
import os
import shutil

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import put_uploadfiles_jnl

def main(work_dir_path, ws_db):
    ###########################################################
    # waste_oase_template
    # v2.4でOASEを利用していないのに、OASEテンプレートが誤って作成されてしまう問題の修正
    ###########################################################
    g.applogger.info("[Trace][start] bug fix waste_oase_template")

    common_db = DBConnectCommon()  # noqa: F405

    organization_id = g.ORGANIZATION_ID
    workspace_id = g.WORKSPACE_ID

    # organization単位のドライバ情報を取得する
    org_no_install_driver = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE ORGANIZATION_ID = '{}' AND DISUSE_FLAG = {}".format(organization_id, 0))[0]["NO_INSTALL_DRIVER"]
    common_db.db_disconnect()

    # oaseインストール済みの場合は対応不要
    org_no_install_driver = json.loads(org_no_install_driver) if org_no_install_driver is not None else {}
    if 'oase' not in org_no_install_driver:
        g.applogger.info("[Trace][skipped] bug fix waste_oase_template")
        return 0

    file_dir = os.path.join(work_dir_path, "uploadfiles", "110102")
    try:
        shutil.rmtree(file_dir)
    except FileNotFoundError:
        g.applogger.info("[Trace][skipped] bug fix waste_oase_template shutil.rmtree skipped. No such file or directory: {}".format(file_dir))
        return 0
    except Exception as e:
        g.applogger.error("[Error] bug fix waste_oase_template shutil.rmtree failed: {}".format(str(e)))

    g.applogger.info("[Trace][end] bug fix waste_oase_template")
    return 0


