# Copyright 2022 NEC Corporation#
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
from backyard_libs.ansible_driver.classes import *  # noqa: F403
from backyard_libs.ansible_driver.functions import util


def backyard_main(organization_id, workspace_id):
    g.applogger.debug("backyard_main ita_by_ansible_pioneer_vars_listup called")

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 実行準備
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    # 環境情報設定
    # 言語情報
    # if 'LANGUAGE' not in g:
    g.LANGUAGE = 'en'
    # if 'USER_ID' not in g:
    g.USER_ID = '20301'

    proc_loaded_row_id = 203

    # DB接続準備
    ws_db = DBConnectWs(workspace_id)  # noqa: F405

    # 関連データベースが更新されバックヤード処理が必要か判定
    if not has_changes_related_tables(ws_db, proc_loaded_row_id):
        g.applogger.debug("No changes, skip workflow.")
        return

    # 各インスタンス準備
    g.applogger.debug("[Trace] Read all related table.")
    dialog_table = DialogTable(ws_db)  # noqa: F405
    dialog_table.store_dbdata_in_memory()

    tpl_table = TemplateTable(ws_db)  # noqa: F405
    tpl_table.store_dbdata_in_memory()

    mov_table = MovementTable(ws_db)  # noqa: F405
    mov_table.store_dbdata_in_memory()

    mov_material_link_table = MovementMaterialLinkTable(ws_db)  # noqa: F405
    mov_material_link_table.store_dbdata_in_memory()

    mov_vars_link_table = MovementVarsLinkTable(ws_db)  # noqa: F405
    mov_vars_link_table.store_dbdata_in_memory(contain_disused_data=True)

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # メイン処理開始
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    g.applogger.debug("[Trace] Start extracting variables.")
    # 対話ファイル素材集変数チェック
    tpl_vars_dict = tpl_table.extract_variable()
    dialog_vars_dict = dialog_table.extract_variable(tpl_vars_dict)

    # Movement変数チェック（Movement - Role 変数紐づけ、Movement追加オプション）
    mov_records = mov_table.get_stored_records()
    mov_matl_lnk_records = mov_material_link_table.get_stored_records()

    mov_vars_dict = util.extract_variable_for_movement(mov_records, mov_matl_lnk_records, dialog_vars_dict)

    # 作業実行時変数チェック（具体値を確認しTPFある場合は変数を追加する）
    mov_vars_dict = util.extract_variable_for_execute(mov_vars_dict, tpl_vars_dict, ws_db)

    # Movement変数 登録・廃止
    mov_vars_link_table.register_and_discard(mov_vars_dict)

    # DBコミット
    ws_db.db_commit()

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 終了処理
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # DB切断
    ws_db.db_disconnect()

    g.applogger.debug("backyard_main ita_by_ansible_pioneer_vars_listup end")


def has_changes_related_tables(ws_db, proc_loaded_row_id):

    where_str = " WHERE  ROW_ID = %s AND (LOADED_FLG is NULL OR LOADED_FLG <> '1')"
    bind_value_list = [proc_loaded_row_id]
    not_loaded_count = ws_db.table_count("T_COMN_PROC_LOADED_LIST", where_str, bind_value_list)

    return (not_loaded_count > 0)
