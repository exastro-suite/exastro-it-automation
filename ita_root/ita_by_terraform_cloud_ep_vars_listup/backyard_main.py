# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from flask import g
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.common.vars_list_up_function import *  # noqa: F403
from common_libs.terraform_driver.common.member_vars_function import *  # noqa: F403


def backyard_main(organization_id, workspace_id):
    # メイン処理開始
    g.applogger.debug(g.appmsg.get_log_message("BKY-00001"))

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # バックヤード起動フラグのID
    proc_load_id = 801

    # 関連データベースが更新されバックヤード処理が必要か判定
    ret = has_changes_related_tables(objdbca, proc_load_id)  # noqa: F405
    if not ret:
        g.applogger.debug(g.appmsg.get_log_message("BKY-50001"))
        return

    # Module素材集に登録されているレコードから、Module-変数紐付テーブルを更新する
    g.applogger.debug(g.appmsg.get_log_message("BKY-50002"))
    result = set_module_vars_link(objdbca, TFCloudEPConst)  # noqa: F405
    if not result:
        # 後続の処理が成立しないためreturnする
        return

    # Movement-Module紐付に登録されているレコードから、Movement-Module変数紐付テーブルを更新する
    g.applogger.debug(g.appmsg.get_log_message("BKY-50003"))
    result = set_movement_var_link(objdbca, TFCloudEPConst)  # noqa: F405
    if not result:
        # 後続の処理が成立しないためreturnする
        return

    # Movement-Module変数紐付に登録されているレコードから、Movement-メンバー変数紐付テーブルを更新する
    g.applogger.debug(g.appmsg.get_log_message("BKY-50004"))
    result = set_movement_var_member_link(objdbca, TFCloudEPConst)  # noqa: F405
    if not result:
        # returnする
        return

    # バックヤード処理実行フラグを更新
    # トランザクション開始
    objdbca.db_transaction_start()
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "1", "ROW_ID": proc_load_id}
    primary_key_name = "ROW_ID"
    ret = objdbca.table_update(table_name, data_list, primary_key_name, False)
    if not ret:
        g.applogger.error(g.appmsg.get_log_message("BKY-50118", []))
        # トランザクション終了(異常)
        objdbca.db_transaction_end(False)
    else:
        # トランザクション終了(正常)
        objdbca.db_transaction_end(True)

    # 終了
    return
