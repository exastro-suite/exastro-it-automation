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

def main(work_dir_path, wsdb):
    # ###########################################################
    # # 2607
    # ###########################################################
    g.applogger.info("[Trace] bug fix issue2607")
    common_db = DBConnectCommon()  # noqa: F405

    organization_id = g.ORGANIZATION_ID
    workspace_id = g.WORKSPACE_ID

    # organization単位のドライバ情報を取得する
    org_no_install_driver = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE ORGANIZATION_ID = '{}' AND DISUSE_FLAG = {}".format(organization_id, 0))[0]["NO_INSTALL_DRIVER"]
    common_db.db_disconnect()
    # terraformインストールしていない場合は行なわない
    org_no_install_driver = json.loads(org_no_install_driver) if org_no_install_driver is not None else {}
    if 'terraform_cli' in org_no_install_driver and 'terraform_cloud_ep' in org_no_install_driver:
        return 0

    terraform_cloud_ep_flg = False
    terraform_cli_flg = False
    if 'terraform_cloud_ep' not in org_no_install_driver:
        terraform_cloud_ep_flg = True
    if 'terraform_cli' not in org_no_install_driver:
        terraform_cli_flg = True

    if terraform_cloud_ep_flg is True:
        column_list, primary_key_list = wsdb.table_columns_get('T_TERE_VALUE_AUTOREG')
        if 'MENU_NAME_REST' not in column_list:
            sql = "ALTER TABLE T_TERE_VALUE_AUTOREG ADD COLUMN MENU_NAME_REST VARCHAR(40) AFTER VALUE_AUTOREG_ID;"
            wsdb.sql_execute(sql)
            sql = "ALTER TABLE T_TERE_VALUE_AUTOREG_JNL ADD  COLUMN MENU_NAME_REST VARCHAR(40) AFTER VALUE_AUTOREG_ID;"
            wsdb.sql_execute(sql)

    if terraform_cli_flg is True:
        column_list, primary_key_list = wsdb.table_columns_get('T_TERC_VALUE_AUTOREG')
        if 'MENU_NAME_REST' not in column_list:
            sql = "ALTER TABLE T_TERC_VALUE_AUTOREG ADD COLUMN MENU_NAME_REST VARCHAR(40) AFTER VALUE_AUTOREG_ID;"
            wsdb.sql_execute(sql)
            sql = "ALTER TABLE T_TERC_VALUE_AUTOREG_JNL ADD  COLUMN MENU_NAME_REST VARCHAR(40) AFTER VALUE_AUTOREG_ID;"
            wsdb.sql_execute(sql)

    return 0
