#   Copyright 2026 NEC Corporation
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

import inspect
from flask import g
import os


def main(work_dir_path, ws_db):
    """T_COMN_MENUテーブルのEXPORT_PERMISSION_CHECK_FLGを設定

    Args:
        work_dir_path (str): 作業フォルダパス / Work directory path
        ws_db (obj): ワークスペースDB接続オブジェクト / Workspace DB connection object

    Returns:
        int: 0:正常終了 / Normal termination
             0以外:異常終了 / Abnormal termination
    """

    g.applogger.info(f"[Trace][start] {os.path.splitext(os.path.basename(inspect.currentframe().f_code.co_filename))[0]}")

    table_name = "T_COMN_MENU"
    table_name_jnl = table_name + "_JNL"

    # FLAG=0にすべきメニューIDのリスト（環境移行用の内部定義メニュー）
    # List of MENU_IDs that should have FLAG=0 (internal definition menus for environment migration)
    #
    # ワークスペース作成時のロールメニュー紐付パターン：
    # Role-menu link patterns at workspace creation:
    #   - パターン1: PRIVILEGE=2 (閲覧のみ) + DISUSE=1 (廃止済み) - 24件
    #   - パターン2: PRIVILEGE=1 (メンテナンス可) + DISUSE=1 (廃止済み) - 9件
    #   - パターン3: PRIVILEGE=2 (閲覧のみ) + DISUSE=0 (有効) - 1件 (50102のみ)
    #
    flag_0_menu_ids = [
        # workspace (3)
        '10203', '10204', '10205',
        # ansible (8)
        '20107', '20114', '20204', '20306', '20401', '20405', '20413', '20414',
        # menu_create (8)
        '50102', '50103', '50104', '50106', '50107', '50110', '50111', '50112',
        # hostgroup (1)
        '70104',
        # terraform_cloud_ep (4)
        '80118', '80119', '80120', '80121',
        # terraform_cli (4)
        '90112', '90113', '90114', '90115',
        # cicd (1)
        '100102',
    ]

    # トランザクション開始
    # Start transaction
    ws_db.db_transaction_start()

    g.applogger.info("[Trace] Step 1: Set EXPORT_PERMISSION_CHECK_FLG = 1 for all menus (default: permission check enabled)")

    # ステップ1: 全メニューのEXPORT_PERMISSION_CHECK_FLGを1に設定（デフォルト：権限チェックする）
    # Step 1: Set EXPORT_PERMISSION_CHECK_FLG = 1 for all menus (default: permission check enabled)
    # ユーザー作成メニューも含めてすべてのメニューを権限チェック対象にする
    for table in [table_name, table_name_jnl]:
        sql = f"UPDATE `{table}` SET EXPORT_PERMISSION_CHECK_FLG = 1"
        g.applogger.debug(f"{sql=}")
        ws_db.sql_execute(sql)

    g.applogger.info(f"[Trace] Step 2: Set EXPORT_PERMISSION_CHECK_FLG = 0 for {len(flag_0_menu_ids)} internal definition menus")

    # ステップ2: 指定された内部定義メニューのEXPORT_PERMISSION_CHECK_FLGを0に設定（権限チェックスキップ）
    # Step 2: Set EXPORT_PERMISSION_CHECK_FLG = 0 for specified internal definition menus (skip permission check)
    if flag_0_menu_ids:
        for table in [table_name, table_name_jnl]:
            # IN句用のプレースホルダを作成
            placeholders = ', '.join(['%s'] * len(flag_0_menu_ids))
            sql = f"UPDATE `{table}` SET EXPORT_PERMISSION_CHECK_FLG = 0 WHERE MENU_ID IN ({placeholders})"
            g.applogger.debug(f"{sql=}")
            ws_db.sql_execute(sql, flag_0_menu_ids)

    # トランザクションコミット
    # Commit transaction
    ws_db.db_commit()

    g.applogger.info(f"[Trace][end] {os.path.splitext(os.path.basename(inspect.currentframe().f_code.co_filename))[0]}")

    return 0
