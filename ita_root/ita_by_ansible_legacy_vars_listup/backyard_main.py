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
    g.applogger.debug("backyard_main ita_by_ansible_legacy_vars_listup called")
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 実行準備
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    # 環境情報設定
    # 言語情報
    # if 'LANGUAGE' not in g:
    g.LANGUAGE = 'en'
    # if 'USER_ID' not in g:
    g.USER_ID = '20201'

    proc_loaded_row_id = 202

    # DB接続準備
    ws_db = DBConnectWs(workspace_id)  # noqa: F405

    # トランザクション開始
    ws_db.db_transaction_start()

    # 関連データベースが更新されバックヤード処理が必要か判定
    if not has_changes_related_tables(ws_db, proc_loaded_row_id):
        g.applogger.debug("No changes, skip workflow.")
        # トランザクション終了
        ws_db.db_transaction_end(False)
        # DB切断
        ws_db.db_disconnect()
        return

    # 各インスタンス準備
    g.applogger.debug("[Trace] Read all related table.")
    playbook_table = PlaybookTable(ws_db)  # noqa: F405
    playbook_table.store_dbdata_in_memory()

    tpl_table = TemplateTable(ws_db)  # noqa: F405
    tpl_table.store_dbdata_in_memory()

    device_table = DeviceTable(ws_db)  # noqa: F405
    device_table.store_dbdata_in_memory()

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
    # Playbook素材集変数チェック
    tpl_vars_dict = tpl_table.extract_variable()
    playbook_vars_dict = playbook_table.extract_variable(tpl_vars_dict)

    # Movement変数チェック（Movement - Playbook 変数紐づけ、Movement追加オプション）
    mov_records = mov_table.get_stored_records()
    mov_matl_lnk_records = mov_material_link_table.get_stored_records()

    mov_vars_dict = util.extract_variable_for_movement(mov_records, mov_matl_lnk_records, playbook_vars_dict, ws_db)

    # 作業実行時変数チェック（具体値を確認しTPFある場合は変数を追加する、作業対象ホストのインベントリファイル追加オプション）
    device_vars_dict = device_table.extract_variable()
    mov_vars_dict = util.extract_variable_for_execute(mov_vars_dict, tpl_vars_dict, device_vars_dict, ws_db)

    # Movement変数 登録・廃止
    mov_vars_link_table.register_and_discard(mov_vars_dict)

    # バックヤード処理実行フラグを更新
    has_changes_related_tables_off(ws_db, proc_loaded_row_id)

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 終了処理
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    # DBコミット
    ws_db.db_commit()

    # トランザクション終了
    ws_db.db_transaction_end(True)

    # DB切断
    ws_db.db_disconnect()

    g.applogger.debug("backyard_main ita_by_ansible_legacy_vars_listup end")


def has_changes_related_tables(ws_db, proc_loaded_row_id):

    where_str = " WHERE  ROW_ID = %s AND (LOADED_FLG is NULL OR LOADED_FLG <> '1')"
    bind_value_list = [proc_loaded_row_id]
    not_loaded_count = ws_db.table_count("T_COMN_PROC_LOADED_LIST", where_str, bind_value_list)

    return (not_loaded_count > 0)

def has_changes_related_tables_off(ws_db, proc_loaded_row_id):
    # バックヤード処理実行フラグを更新
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "1", "ROW_ID": proc_loaded_row_id}
    primary_key_name = "ROW_ID"
    ret = ws_db.table_update(table_name, data_list, primary_key_name, False)
