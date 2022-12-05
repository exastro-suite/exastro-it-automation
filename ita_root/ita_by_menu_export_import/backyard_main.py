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
import json
import re
import ast
from flask import g
# from common_libs.common.exception import AppException
from common_libs.common import *  # noqa: F403


def backyard_main(organization_id, workspace_id):
    """
        メニュー作成機能backyardメイン処理
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETRUN:

    """
    # メイン処理開始
    debug_msg = g.appmsg.get_log_message("BKY-20001", [])
    g.applogger.debug(debug_msg)

    print("★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆")

    # # テーブル名
    # t_menu_create_history = 'T_MENU_CREATE_HISTORY'  # メニュー作成履歴

    # # DB接続
    # objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # # 「メニュー作成履歴」から「未実行(ID:1)」のレコードを取得
    # ret = objdbca.table_select(t_menu_create_history, 'WHERE STATUS_ID = %s AND DISUSE_FLAG = %s', [1, 0])

    # # 0件なら処理を終了
    # if not ret:
    #     debug_msg = g.appmsg.get_log_message("BKY-20003", [])
    #     g.applogger.debug(debug_msg)

    #     debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    #     g.applogger.debug(debug_msg)
    #     return

    # for record in ret:
    #     history_id = str(record.get('HISTORY_ID'))
    #     menu_create_id = str(record.get('MENU_CREATE_ID'))
    #     create_type = str(record.get('CREATE_TYPE'))

    #     # 「メニュー作成履歴」ステータスを「2:実行中」に更新
    #     objdbca.db_transaction_start()
    #     status_id = "2"
    #     result, msg = _update_t_menu_create_history(objdbca, history_id, status_id)
    #     if not result:
    #         # エラーログ出力
    #         g.applogger.error(msg)
    #         continue
    #     objdbca.db_transaction_end(True)

    #     # トランザクション開始
    #     debug_msg = g.appmsg.get_log_message("BKY-20004", [])
    #     g.applogger.debug(debug_msg)
    #     objdbca.db_transaction_start()

    #     # create_typeに応じたレコード登録/更新処理を実行(メイン処理)
    #     if create_type == "1":  # 1: 新規作成
    #         debug_msg = g.appmsg.get_log_message("BKY-20019", [menu_create_id, 'create_new'])
    #         g.applogger.debug(debug_msg)
    #         main_func_result, msg = menu_create_exec(objdbca, menu_create_id, 'create_new')

    #     elif create_type == "2":  # 2: 初期化
    #         debug_msg = g.appmsg.get_log_message("BKY-20019", [menu_create_id, 'initialize'])
    #         g.applogger.debug(debug_msg)
    #         main_func_result, msg = menu_create_exec(objdbca, menu_create_id, 'initialize')

    #     elif create_type == "3":  # 3: 編集
    #         debug_msg = g.appmsg.get_log_message("BKY-20019", [menu_create_id, 'edit'])
    #         g.applogger.debug(debug_msg)
    #         main_func_result, msg = menu_create_exec(objdbca, menu_create_id, 'edit')

    #     # メイン処理がFalseの場合、異常系処理
    #     if not main_func_result:
    #         # エラーログ出力
    #         g.applogger.error(msg)

    #         # ロールバック/トランザクション終了
    #         debug_msg = g.appmsg.get_log_message("BKY-20006", [])
    #         g.applogger.debug(debug_msg)
    #         objdbca.db_transaction_end(False)

    #         # 「メニュー作成履歴」ステータスを「4:完了(異常)」に更新
    #         objdbca.db_transaction_start()
    #         status_id = 4
    #         result, msg = _update_t_menu_create_history(objdbca, history_id, status_id)
    #         if not result:
    #             # エラーログ出力
    #             g.applogger.error(msg)
    #             continue
    #         objdbca.db_transaction_end(True)

    #         continue

    #     # 「メニュー定義一覧」の対象レコードの「メニュー作成状態」を「2: 作成済み」に変更
    #     menu_create_done_status_id = "2"
    #     result, msg = _update_t_menu_define(objdbca, menu_create_id, menu_create_done_status_id)
    #     if not result:
    #         # ロールバック/トランザクション終了
    #         debug_msg = g.appmsg.get_log_message("BKY-20006", [])
    #         g.applogger.debug(debug_msg)
    #         objdbca.db_transaction_end(False)

    #         # エラーログ出力
    #         g.applogger.error(msg)
    #         continue

    #     # コミット/トランザクション終了
    #     debug_msg = g.appmsg.get_log_message("BKY-20005", [])
    #     g.applogger.debug(debug_msg)
    #     objdbca.db_transaction_end(True)

    #     # 「メニュー作成履歴」ステータスを「3:完了」に更新
    #     objdbca.db_transaction_start()
    #     status_id = 3
    #     result, msg = _update_t_menu_create_history(objdbca, history_id, status_id)
    #     if not result:
    #         # エラーログ出力
    #         g.applogger.error(msg)
    #         continue
    #     objdbca.db_transaction_end(True)

    # # メイン処理終了
    # debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    # g.applogger.debug(debug_msg)
    return


