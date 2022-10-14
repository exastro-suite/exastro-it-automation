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
    
    # テーブル名
    t_menu_create_history = 'T_MENU_CREATE_HISTORY'  # メニュー作成履歴
    
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405
    
    # 「メニュー作成履歴」から「未実行(ID:1)」のレコードを取得
    ret = objdbca.table_select(t_menu_create_history, 'WHERE STATUS_ID = %s AND DISUSE_FLAG = %s', [1, 0])
    
    # 0件なら処理を終了
    if not ret:
        debug_msg = g.appmsg.get_log_message("BKY-20003", [])
        g.applogger.debug(debug_msg)
        
        debug_msg = g.appmsg.get_log_message("BKY-20002", [])
        g.applogger.debug(debug_msg)
        return
    
    for record in ret:
        history_id = str(record.get('HISTORY_ID'))
        menu_create_id = str(record.get('MENU_CREATE_ID'))
        create_type = str(record.get('CREATE_TYPE'))
        
        # 「メニュー作成履歴」ステータスを「2:実行中」に更新
        objdbca.db_transaction_start()
        status_id = "2"
        result, msg = _update_t_menu_create_history(objdbca, history_id, status_id)
        if not result:
            # エラーログ出力
            g.applogger.error(msg)
            continue
        objdbca.db_transaction_end(True)
        
        # トランザクション開始
        debug_msg = g.appmsg.get_log_message("BKY-20004", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_start()
        
        # create_typeに応じたレコード登録/更新処理を実行(メイン処理)
        if create_type == "1":  # 1: 新規作成
            debug_msg = g.appmsg.get_log_message("BKY-20019", [menu_create_id, 'create_new'])
            g.applogger.debug(debug_msg)
            main_func_result, msg = menu_create_exec(objdbca, menu_create_id, 'create_new')
        
        elif create_type == "2":  # 2: 初期化
            debug_msg = g.appmsg.get_log_message("BKY-20019", [menu_create_id, 'initialize'])
            g.applogger.debug(debug_msg)
            main_func_result, msg = menu_create_exec(objdbca, menu_create_id, 'initialize')
        
        elif create_type == "3":  # 3: 編集
            debug_msg = g.appmsg.get_log_message("BKY-20019", [menu_create_id, 'edit'])
            g.applogger.debug(debug_msg)
            main_func_result, msg = menu_create_exec(objdbca, menu_create_id, 'edit')
        
        # メイン処理がFalseの場合、異常系処理
        if not main_func_result:
            # エラーログ出力
            g.applogger.error(msg)
            
            # ロールバック/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20006", [])
            g.applogger.debug(debug_msg)
            objdbca.db_transaction_end(False)
            
            # 「メニュー作成履歴」ステータスを「4:完了(異常)」に更新
            objdbca.db_transaction_start()
            status_id = 4
            result, msg = _update_t_menu_create_history(objdbca, history_id, status_id)
            if not result:
                # エラーログ出力
                g.applogger.error(msg)
                continue
            objdbca.db_transaction_end(True)
            
            continue
        
        # 「メニュー定義一覧」の対象レコードの「メニュー作成状態」を「2: 作成済み」に変更
        menu_create_done_status_id = "2"
        result, msg = _update_t_menu_define(objdbca, menu_create_id, menu_create_done_status_id)
        if not result:
            # ロールバック/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20006", [])
            g.applogger.debug(debug_msg)
            objdbca.db_transaction_end(False)
            
            # エラーログ出力
            g.applogger.error(msg)
            continue
        
        # コミット/トランザクション終了
        debug_msg = g.appmsg.get_log_message("BKY-20005", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_end(True)
        
        # 「メニュー作成履歴」ステータスを「3:完了」に更新
        objdbca.db_transaction_start()
        status_id = 3
        result, msg = _update_t_menu_create_history(objdbca, history_id, status_id)
        if not result:
            # エラーログ出力
            g.applogger.error(msg)
            continue
        objdbca.db_transaction_end(True)
    
    # メイン処理終了
    debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    g.applogger.debug(debug_msg)
    return


def menu_create_exec(objdbca, menu_create_id, create_type):  # noqa: C901
    """
        メニュー作成実行
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_create_id: メニュー作成の対象となる「メニュー定義一覧」のレコードのID
            create_type: 「新規作成(create_new」「初期化(initialize)」「編集(edit)」のいずれか
        RETRUN:
            boolean, msg
    """
    # テーブル/ビュー名
    t_comn_column_group = 'T_COMN_COLUMN_GROUP'
    
    try:
        # メニュー作成用の各テーブルからレコードを取得
        debug_msg = g.appmsg.get_log_message("BKY-20007", [])
        g.applogger.debug(debug_msg)
        result, \
            msg, \
            record_t_menu_define, \
            record_t_menu_column_group, \
            record_t_menu_column, \
            record_t_menu_unique_constraint, \
            record_t_menu_role, \
            record_t_menu_other_link, \
            record_v_menu_reference_item \
            = _collect_menu_create_data(objdbca, menu_create_id)  # noqa: E501
        if not result:
            raise Exception(msg)
        
        # テーブル名を生成
        create_table_name = 'T_CMDB_' + str(menu_create_id)
        create_table_name_jnl = 'T_CMDB_' + str(menu_create_id) + '_JNL'
        create_view_name = 'V_CMDB_' + str(menu_create_id)
        create_view_name_jnl = 'V_CMDB_' + str(menu_create_id) + '_JNL'
        
        # シートタイプを取得
        sheet_type = str(record_t_menu_define.get('SHEET_TYPE'))
        
        # 縦メニュー利用の有無を取得
        vertical_flag = True if str(record_t_menu_define.get('VERTICAL')) == "1" else False
        
        # シートタイプによる処理の分岐
        file_upload_only_flag = False
        if sheet_type == "1":  # パラメータシート(ホスト/オペレーションあり)
            # テーブル名/ビュー名を生成
            create_table_name = 'T_CMDB_' + str(menu_create_id)
            create_table_name_jnl = 'T_CMDB_' + str(menu_create_id) + '_JNL'
            create_view_name = 'V_CMDB_' + str(menu_create_id)
            create_view_name_jnl = 'V_CMDB_' + str(menu_create_id) + '_JNL'
            
            if vertical_flag:
                # パラメータシート(縦メニュー利用あり)用テーブル作成SQL
                sql_file_path = "./sql/parameter_sheet_cmdb_vertical.sql"
            else:
                # パラメータシート用テーブル作成SQL
                sql_file_path = "./sql/parameter_sheet_cmdb.sql"
            
            # ループパターン(対象メニューグループのリスト)を設定
            target_menu_group_list = ['MENU_GROUP_ID_INPUT', 'MENU_GROUP_ID_SUBST', 'MENU_GROUP_ID_REF']
            
            # ファイルアップロードカラムのみの構成の場合、シートタイプを「4: パラメータシート(ファイルアップロードあり)」として扱う
            file_upload_only_flag = _check_file_upload_column(record_t_menu_column)
        
        elif sheet_type == "2":  # データシート
            # 「データシート」かつ「項目が0件」の場合はエラー判定
            if not record_t_menu_column:
                msg = g.appmsg.get_log_message("BKY-20202", [])
                raise Exception(msg)
            
            # テーブル名を生成
            create_table_name = 'T_CMDB_' + str(menu_create_id)
            create_table_name_jnl = 'T_CMDB_' + str(menu_create_id) + '_JNL'
            create_view_name = None
            create_view_name_jnl = None
            
            # データシート用テーブル作成SQL
            sql_file_path = "./sql/data_sheet_cmdb.sql"
            
            # ループパターン(対象メニューグループのリスト)を設定
            target_menu_group_list = ['MENU_GROUP_ID_INPUT']
        
        else:
            msg = g.appmsg.get_log_message("BKY-20201", [sheet_type])
            raise Exception(msg)
        
        # 「新規作成」「初期化」の場合のみ、テーブル作成SQLを実行
        if create_type == 'create_new' or create_type == 'initialize':
            debug_msg = g.appmsg.get_log_message("BKY-20008", [create_table_name, create_table_name_jnl])
            g.applogger.debug(debug_msg)
            with open(sql_file_path, "r") as f:
                file = f.read()
                if sheet_type == "1":  # パラメータシート(ホスト/オペレーションあり)
                    file = file.replace('____CMDB_TABLE_NAME____', create_table_name)
                    file = file.replace('____CMDB_TABLE_NAME_JNL____', create_table_name_jnl)
                    file = file.replace('____CMDB_VIEW_NAME____', create_view_name)
                    file = file.replace('____CMDB_VIEW_NAME_JNL____', create_view_name_jnl)
                elif sheet_type == "2":  # データシート
                    file = file.replace('____CMDB_TABLE_NAME____', create_table_name)
                    file = file.replace('____CMDB_TABLE_NAME_JNL____', create_table_name_jnl)
                sql_list = file.split(";\n")
                for sql in sql_list:
                    if re.fullmatch(r'[\s\n\r]*', sql) is None:
                        objdbca.sql_execute(sql)
        
        # カラムグループ登録の処理に必要な形式にフォーマット
        result, msg, dict_t_menu_column_group, target_column_group_list = _format_column_group_data(record_t_menu_column_group, record_t_menu_column)
        if not result:
            raise Exception(msg)
        
        # 「他メニュー連携」を利用する処理に必要な形式にフォーマット
        result, msg, dict_t_menu_other_link = _format_other_link(record_t_menu_other_link)
        if not result:
            raise Exception(msg)
        
        # 「初期化」「編集」の場合のみ以下の処理を実施
        if create_type == 'initialize' or create_type == 'edit':
            debug_msg = g.appmsg.get_log_message("BKY-20009", [])
            g.applogger.debug(debug_msg)
            
            # 対象のメニューについて、現在登録されているメニュー用のレコードを廃止する
            result, msg = _disuse_menu_create_record(objdbca, record_t_menu_define)
            if not result:
                raise Exception(msg)
            
            # 利用していないメニューグループのメニューを廃止
            result, msg = _disuse_t_comn_menu(objdbca, record_t_menu_define, target_menu_group_list)
            if not result:
                raise Exception(msg)
        
        # 対象メニューグループ分だけ処理をループ
        input_menu_uuid = None
        for menu_group_col_name in target_menu_group_list:
            # デバッグログ用文言
            target_menu_group_type = "Input"
            if menu_group_col_name == "MENU_GROUP_ID_SUBST":
                target_menu_group_type = "Substitution value auto-registration"
            elif menu_group_col_name == "MENU_GROUP_ID_REF":
                target_menu_group_type = "Reference"
            
            # 「新規作成」の場合「メニュー管理」にレコードを登録
            if create_type == 'create_new':
                debug_msg = g.appmsg.get_log_message("BKY-20010", [target_menu_group_type])
                g.applogger.debug(debug_msg)
                result, msg, ret_data = _insert_t_comn_menu(objdbca, sheet_type, record_t_menu_define, menu_group_col_name, record_t_menu_column)
                if not result:
                    raise Exception(msg)
            
            # 「初期化」「編集」の場合「メニュー管理」のレコードを更新および登録
            if create_type == 'initialize' or create_type == 'edit':
                debug_msg = g.appmsg.get_log_message("BKY-20011", [target_menu_group_type])
                g.applogger.debug(debug_msg)
                result, msg, ret_data = _update_t_comn_menu(objdbca, sheet_type, record_t_menu_define, menu_group_col_name, record_t_menu_column)
                if not result:
                    raise Exception(msg)
            
            # 「メニュー管理」に登録したレコードのuuidを取得
            menu_uuid = ret_data[0].get('MENU_ID')
            if menu_group_col_name == "MENU_GROUP_ID_INPUT":
                input_menu_uuid = menu_uuid
            
            # 「ロール-メニュー紐付管理」にレコードを登録
            debug_msg = g.appmsg.get_log_message("BKY-20012", [target_menu_group_type])
            g.applogger.debug(debug_msg)
            result, msg = _insert_t_comn_role_menu_link(objdbca, menu_uuid, record_t_menu_role)
            if not result:
                raise Exception(msg)
            
            # 「メニュー-テーブル紐付管理」にレコードを登録
            debug_msg = g.appmsg.get_log_message("BKY-20013", [target_menu_group_type])
            g.applogger.debug(debug_msg)
            result, msg = _insert_t_comn_menu_table_link(objdbca, sheet_type, vertical_flag, file_upload_only_flag, create_table_name, create_view_name, menu_uuid, record_t_menu_define, record_t_menu_unique_constraint, menu_group_col_name)  # noqa: E501
            if not result:
                raise Exception(msg)
            
            # 「カラムグループ管理」にレコードを登録(対象メニューグループ「入力用」の場合のみ実施)
            if menu_group_col_name == "MENU_GROUP_ID_INPUT":
                debug_msg = g.appmsg.get_log_message("BKY-20014", [target_menu_group_type])
                g.applogger.debug(debug_msg)
                result, msg = _insert_t_comn_column_group(objdbca, target_column_group_list, dict_t_menu_column_group)
                if not result:
                    raise Exception(msg)
                
                # 「カラムグループ管理」から全てのレコードを取得
                record_t_comn_column_group = objdbca.table_select(t_comn_column_group, 'WHERE DISUSE_FLAG = %s', [0])
                
                # 「カラムグループ管理」のレコードのidをkeyにしたdict型に整形
                dict_t_comn_column_group = {}
                for record in record_t_comn_column_group:
                    dict_t_comn_column_group[record.get('COL_GROUP_ID')] = {
                        "pa_col_group_id": record.get('PA_COL_GROUP_ID'),
                        "col_group_name_ja": record.get('COL_GROUP_NAME_JA'),
                        "col_group_name_en": record.get('COL_GROUP_NAME_EN'),
                        "full_col_group_name_ja": record.get('FULL_COL_GROUP_NAME_JA'),
                        "full_col_group_name_en": record.get('FULL_COL_GROUP_NAME_EN'),
                    }
            
            # 「メニュー-カラム紐付管理」にレコードを登録
            debug_msg = g.appmsg.get_log_message("BKY-20015", [target_menu_group_type])
            g.applogger.debug(debug_msg)
            result, msg = _insert_t_comn_menu_column_link(objdbca, sheet_type, vertical_flag, menu_uuid, input_menu_uuid, dict_t_comn_column_group, dict_t_menu_column_group, record_t_menu_column, dict_t_menu_other_link, record_v_menu_reference_item, menu_group_col_name)  # noqa: E501
            if not result:
                raise Exception(msg)
            
            # 「メニュー定義-テーブル紐付管理」にレコードを登録
            debug_msg = g.appmsg.get_log_message("BKY-20016", [target_menu_group_type])
            g.applogger.debug(debug_msg)
            result, msg = _insert_t_menu_table_link(objdbca, menu_uuid, create_table_name, create_table_name_jnl)
            if not result:
                raise Exception(msg)
            
            # 対象メニューグループ「入力用」の場合のみ実施
            if menu_group_col_name == "MENU_GROUP_ID_INPUT":
                # 「他メニュー連携」にレコードを登録
                debug_msg = g.appmsg.get_log_message("BKY-20017", [target_menu_group_type])
                g.applogger.debug(debug_msg)
                result, msg = _insert_t_menu_other_link(objdbca, menu_uuid, create_table_name, record_t_menu_column)
                if not result:
                    raise Exception(msg)
                
                # 「参照項目情報」にレコードを登録
                debug_msg = g.appmsg.get_log_message("BKY-20018", [target_menu_group_type])
                g.applogger.debug(debug_msg)
                result, msg = _insert_t_menu_reference_item(objdbca, menu_uuid, create_table_name, record_t_menu_column)
                if not result:
                    raise Exception(msg)
        
        # 正常系リターン
        return True, msg
        
    except Exception as msg:
        # 異常系リターン
        return False, msg


def _collect_menu_create_data(objdbca, menu_create_id):
    """
        メニュー作成対象の必要レコードををすべて取得する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_create_id: メニュー作成の対象となる「メニュー定義一覧」のレコードのID
        RETRUN:
            result,
            msg,
            record_t_menu_define, # 「メニュー定義一覧」から対象のレコード(1件)
            record_t_menu_column_group, # 「カラムグループ作成情報」のレコード(全件)
            record_t_menu_column, # 「メニュー項目作成情報」から対象のレコード(複数)
            record_t_menu_unique_constraint, 「一意制約(複数項目)作成情報」からレコード(1件)
            record_t_menu_role, # 「メニューロール作成情報」から対象のレコード(複数)
            record_t_menu_other_link # 「他メニュー連携」のレコード(全件)
            record_v_menu_reference_item # 「参照項目情報」のレコード(全件)
    """
    # テーブル/ビュー名
    t_menu_define = 'T_MENU_DEFINE'  # メニュー定義一覧
    t_menu_column_group = 'T_MENU_COLUMN_GROUP'  # カラムグループ作成情報
    t_menu_column = 'T_MENU_COLUMN'  # メニュー項目作成情報
    t_menu_unique_constraint = 'T_MENU_UNIQUE_CONSTRAINT'  # 一意制約(複数項目)作成情報
    t_menu_role = 'T_MENU_ROLE'  # メニューロール作成情報
    t_menu_other_link = 'T_MENU_OTHER_LINK'  # 他メニュー連携
    v_menu_reference_item = 'V_MENU_REFERENCE_ITEM'  # 参照項目情報(VIEW)
    
    try:
        # 「メニュー定義一覧」から対象のレコードを取得
        record_t_menu_define = objdbca.table_select(t_menu_define, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
        if not record_t_menu_define:
            msg = g.appmsg.get_log_message("BKY-20203", [menu_create_id])
            raise Exception(msg)
        record_t_menu_define = record_t_menu_define[0]
        
        # 「カラムグループ作成情報」から全てのレコードを取得
        record_t_menu_column_group = objdbca.table_select(t_menu_column_group, 'WHERE DISUSE_FLAG = %s', [0])
        
        # 「メニュー項目作成情報」から対象のレコードを取得
        record_t_menu_column = objdbca.table_select(t_menu_column, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s ORDER BY DISP_SEQ ASC', [menu_create_id, 0])  # noqa: E501
        
        # 「一意制約(複数項目)作成情報」から対象のレコードを取得
        record_t_menu_unique_constraint = objdbca.table_select(t_menu_unique_constraint, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])  # noqa: E501
        if record_t_menu_unique_constraint:
            record_t_menu_unique_constraint = record_t_menu_unique_constraint[0]
        
        # 「メニューロール作成情報」から対象のレコードを取得
        record_t_menu_role = objdbca.table_select(t_menu_role, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
        if not record_t_menu_role:
            msg = g.appmsg.get_log_message("BKY-20204", [])
            raise Exception(msg)
        
        # 「他メニュー連携」から全てのレコードを取得
        record_t_menu_other_link = objdbca.table_select(t_menu_other_link, 'WHERE DISUSE_FLAG = %s', [0])
        
        # 「参照項目情報」から全てのレコードを取得
        record_v_menu_reference_item = objdbca.table_select(v_menu_reference_item, 'WHERE DISUSE_FLAG = %s', [0])
    
    except Exception as msg:
        return False, msg, None, None, None, None, None, None, None
    
    return True, None, record_t_menu_define, record_t_menu_column_group, record_t_menu_column, record_t_menu_unique_constraint, record_t_menu_role, record_t_menu_other_link, record_v_menu_reference_item  # noqa: E501


def _insert_t_comn_menu(objdbca, sheet_type, record_t_menu_define, menu_group_col_name, record_t_menu_column):
    """
        「メニュー管理」メニューのテーブルにレコードを追加する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            sheet_type: シートタイプ
            record_t_menu_define: 「メニュー定義一覧」の対象のレコード
            menu_group_col_name: 対象メニューグループ名
            record_t_menu_column: 「メニュー項目作成情報」の対象のレコード一覧
        RETRUN:
            boolean, msg, ret_data
    """
    # テーブル名
    t_comn_menu = 'T_COMN_MENU'
    
    try:
        # メニュー名(rest)は対象メニューグループが「代入値自動登録」「参照用」の場合は末尾に_subst, _refを結合する。
        menu_name_rest = record_t_menu_define.get('MENU_NAME_REST')
        if menu_group_col_name == "MENU_GROUP_ID_SUBST":
            menu_name_rest = menu_name_rest + "_subst"
        elif menu_group_col_name == "MENU_GROUP_ID_REF":
            menu_name_rest = menu_name_rest + "_ref"
        
        # バリデーションチェック1: 同一のmenu_name_restが登録されている場合はエラー判定
        ret = objdbca.table_select(t_comn_menu, 'WHERE MENU_NAME_REST = %s AND DISUSE_FLAG = %s', [menu_name_rest, 0])
        if ret:
            msg = g.appmsg.get_log_message("BKY-20205", [menu_name_rest])
            raise Exception(msg)
        
        # バリデーションチェック2: 同じメニューグループ内で同じmenu_name_jaかmenu_name_enが登録されている場合はエラー判定
        menu_name_ja = record_t_menu_define.get('MENU_NAME_JA')
        menu_name_en = record_t_menu_define.get('MENU_NAME_EN')
        target_menu_group_id = record_t_menu_define.get(menu_group_col_name)
        ret = objdbca.table_select(t_comn_menu, 'WHERE MENU_GROUP_ID = %s AND (MENU_NAME_JA = %s OR MENU_NAME_EN = %s) AND DISUSE_FLAG = %s', [target_menu_group_id, menu_name_ja, menu_name_en, 0])  # noqa: E501
        if ret:
            msg = g.appmsg.get_log_message("BKY-20206", [])
            raise Exception(msg)
        
        # シートタイプ毎にソートキーを生成
        sort_key = None
        if sheet_type == "1":
            # オペレーション、ホスト名の順でソート（後ろに記載したほうが優先される）
            sort_key = '[{"ASC":"host_name"}, {"ASC":"operation_name_disp"}]'
        elif sheet_type == "2":
            # 項目の中でDISP_SEQが一番若い対象をソートキーとする
            sort_key_target_record = record_t_menu_column[0]
            sort_key_column_name_rest = sort_key_target_record.get('COLUMN_NAME_REST')
            sort_key = '[{{"ASC":"{}"}}]'.format(sort_key_column_name_rest)
        
        # 「メニュー管理」にレコードを登録
        data_list = {
            "MENU_GROUP_ID": target_menu_group_id,
            "MENU_NAME_JA": menu_name_ja,
            "MENU_NAME_EN": menu_name_en,
            "MENU_NAME_REST": menu_name_rest,
            "DISP_SEQ": record_t_menu_define.get('DISP_SEQ'),
            "AUTOFILTER_FLG": "1",
            "INITIAL_FILTER_FLG": "0",
            "SORT_KEY": sort_key,
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'MENU_ID'
        ret_data = objdbca.table_insert(t_comn_menu, data_list, primary_key_name)
        
    except Exception as msg:
        return False, msg, None
    
    return True, None, ret_data


def _update_t_comn_menu(objdbca, sheet_type, record_t_menu_define, menu_group_col_name, record_t_menu_column):
    """
        「メニュー管理」の対象レコードを更新。対象が無ければレコードを新規登録する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            record_t_menu_define: 「メニュー定義一覧」の対象のレコード
            menu_group_col_name: 対象メニューグループ名
            record_t_menu_column: 「メニュー項目作成情報」の対象のレコード一覧
        RETRUN:
            result, msg, ret_data
    """
    # テーブル名
    t_comn_menu = 'T_COMN_MENU'
    try:
        # メニュー名(rest)は対象メニューグループが「代入値自動登録」「参照用」の場合は末尾に_subst, _refを結合する。
        menu_name_rest = record_t_menu_define.get('MENU_NAME_REST')
        if menu_group_col_name == "MENU_GROUP_ID_SUBST":
            menu_name_rest = menu_name_rest + "_subst"
        elif menu_group_col_name == "MENU_GROUP_ID_REF":
            menu_name_rest = menu_name_rest + "_ref"
        
        # 対象メニューグループIDを取得
        target_menu_group_id = record_t_menu_define.get(menu_group_col_name)
        
        # シートタイプ毎にソートキーを生成
        sort_key = None
        if sheet_type == "1":
            # オペレーション、ホスト名の順でソート（後ろに記載したほうが優先される）
            sort_key = '[{"ASC":"host_name"}, {"ASC":"operation_name_disp"}]'
        elif sheet_type == "2":
            # 項目の中でDISP_SEQが一番若い対象をソートキーとする
            sort_key_target_record = record_t_menu_column[0]
            sort_key_column_name_rest = sort_key_target_record.get('COLUMN_NAME_REST')
            sort_key = '[{{"ASC":"{}"}}]'.format(sort_key_column_name_rest)
        
        # 更新対象のレコードを特定
        ret = objdbca.table_select(t_comn_menu, 'WHERE MENU_GROUP_ID = %s AND MENU_NAME_REST = %s AND DISUSE_FLAG = %s', [target_menu_group_id, menu_name_rest, 0])  # noqa: E501
        if ret:
            menu_id = ret[0].get('MENU_ID')
            # 「メニュー管理」のレコードを更新
            data_list = {
                "MENU_ID": menu_id,
                "MENU_GROUP_ID": target_menu_group_id,
                "MENU_NAME_JA": record_t_menu_define.get('MENU_NAME_JA'),
                "MENU_NAME_EN": record_t_menu_define.get('MENU_NAME_EN'),
                "DISP_SEQ": record_t_menu_define.get('DISP_SEQ'),
                "AUTOFILTER_FLG": "1",
                "INITIAL_FILTER_FLG": "0",
                "SORT_KEY": sort_key,
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            ret_data = objdbca.table_update(t_comn_menu, data_list, 'MENU_ID')
        else:
            # 更新対象が無い場合はFalseをReturnし、レコードの新規登録
            result, msg, ret_data = _insert_t_comn_menu(objdbca, sheet_type, record_t_menu_define, menu_group_col_name, record_t_menu_column)
            if not result:
                raise Exception(msg)
        
    except Exception as msg:
        return False, msg, None
    
    return True, None, ret_data


def _insert_t_comn_role_menu_link(objdbca, menu_uuid, record_t_menu_role):
    """
        「ロール-メニュー紐付管理」メニューのテーブルにレコードを追加する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_uuid: 対象のメニュー（「メニュー管理」のレコード）のUUID
            record_t_menu_role: 「メニュー-ロール作成情報」の対象レコード一覧
        RETRUN:
            result, msg
    """
    # テーブル名
    t_comn_role_menu_link = 'T_COMN_ROLE_MENU_LINK'
    
    try:
        if record_t_menu_role:
            for record in record_t_menu_role:
                role_id = record.get('ROLE_ID')
                data_list = {
                    "MENU_ID": menu_uuid,
                    "ROLE_ID": role_id,
                    "PRIVILEGE": 1,
                    "DISUSE_FLAG": "0",
                    "LAST_UPDATE_USER": g.get('USER_ID')
                }
                primary_key_name = 'LINK_ID'
                objdbca.table_insert(t_comn_role_menu_link, data_list, primary_key_name)
    
    except Exception as msg:
        return False, msg
    
    return True, None


def _insert_t_comn_menu_table_link(objdbca, sheet_type, vertical_flag, file_upload_only_flag, create_table_name, create_view_name, menu_uuid, record_t_menu_define, record_t_menu_unique_constraint, menu_group_col_name):  # noqa: E501
    """
        「メニュー-テーブル紐付管理」メニューのテーブルにレコードを追加する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            sheet_type: シートタイプ
            vertical_flag: 縦メニュー利用の有無
            file_upload_only_flag: Trueの場合、シートタイプを「4: パラメータシート(ファイルアップロードあり)」とする
            create_table_name: 作成した対象のテーブル名
            create_view_name: 作成した対象のビュー名
            menu_uuid: 対象のメニュー（「メニュー管理」のレコード）のUUID
            record_t_menu_define: 「メニュー定義一覧」の対象のレコード
            record_t_menu_unique_constraint: 「一意制約(複数項目)作成情報」の対象のレコード
            menu_group_col_name: 対象メニューグループ名
        RETRUN:
            result, msg
    """
    # テーブル名
    t_comn_menu_table_link = 'T_COMN_MENU_TABLE_LINK'
    
    try:
        # バリデーションチェック1: 同一のメニューID(MENU_ID)が登録されている場合はエラー判定
        ret = objdbca.table_select(t_comn_menu_table_link, 'WHERE MENU_ID = %s AND DISUSE_FLAG = %s', [menu_uuid, 0])
        if ret:
            msg = g.appmsg.get_log_message("BKY-20207", [menu_uuid])
            raise Exception(msg)
        
        # 対象メニューグループで変更がある値の設定
        row_insert_flag = "1"
        row_update_flag = "1"
        row_disuse_flag = "1"
        row_reuse_flag = "1"
        substitution_value_link_flag = "0"
        if menu_group_col_name == "MENU_GROUP_ID_SUBST":
            row_insert_flag = "0"
            row_update_flag = "0"
            row_disuse_flag = "0"
            row_reuse_flag = "0"
            substitution_value_link_flag = "1"
        elif menu_group_col_name == "MENU_GROUP_ID_REF":
            row_insert_flag = "0"
            row_update_flag = "0"
            row_disuse_flag = "0"
            row_reuse_flag = "0"
        
        # 一意制約(複数項目)の値を取得(対象メニューグループが「入力用」の場合のみ)
        unique_constraint = None
        if menu_group_col_name == "MENU_GROUP_ID_INPUT" and record_t_menu_unique_constraint:
            unique_constraint = str(record_t_menu_unique_constraint.get('UNIQUE_CONSTRAINT_ITEM'))
        
        # シートタイプが「1:パラメータシート（ホスト/オペレーションあり）」の場合は、「ホスト/オペレーション」の一意制約(複数項目)を追加(対象メニューグループが「入力用」の場合のみ)
        # また、縦メニュー利用がある場合は「ホスト/オペレーション/代入順序」の一意制約(複数項目)を追加する。
        if menu_group_col_name == "MENU_GROUP_ID_INPUT" and sheet_type == "1":
            if unique_constraint:
                tmp_unique_constraint = json.loads(unique_constraint)
                if vertical_flag:
                    add_unique_constraint = ["operation_name_select", "host_name", "input_order"]
                else:
                    add_unique_constraint = ["operation_name_select", "host_name"]
                if tmp_unique_constraint:
                    tmp_unique_constraint.insert(0, add_unique_constraint)
                else:
                    tmp_unique_constraint = add_unique_constraint
                unique_constraint = json.dumps(tmp_unique_constraint)
            else:
                if vertical_flag:
                    unique_constraint = '[["operation_name_select", "host_name", "input_order"]]'
                else:
                    unique_constraint = '[["operation_name_select", "host_name"]]'
        
        # シートタイプが「1: パラメータシート（ホスト/オペレーションあり）」かつ「参照用」メニューグループの場合、シートタイプを「5: 参照用（ホスト/オペレーションあり）」とする。
        if sheet_type == "1" and menu_group_col_name == "MENU_GROUP_ID_REF":
            sheet_type = "5"
        
        # シートタイプが「1: パラメータシート（ホスト/オペレーションあり）」かつfile_upload_only_flagがTrueの場合、シートタイプを「4: パラメータシート（ファイルアップロードあり）」とする。
        if sheet_type == "1" and file_upload_only_flag:
            sheet_type = "4"
        
        # 「メニュー-テーブル紐付管理」にレコードを登録
        data_list = {
            "MENU_ID": menu_uuid,
            "TABLE_NAME": create_table_name,
            "VIEW_NAME": create_view_name,
            "PK_COLUMN_NAME_REST": "uuid",
            "MENU_INFO_JA": record_t_menu_define.get('DESCRIPTION_JA'),
            "MENU_INFO_EN": record_t_menu_define.get('DESCRIPTION_EN'),
            "SHEET_TYPE": sheet_type,
            "HISTORY_TABLE_FLAG": "1",
            "INHERIT": "0",
            "VERTICAL": record_t_menu_define.get('VERTICAL'),
            "ROW_INSERT_FLAG": row_insert_flag,
            "ROW_UPDATE_FLAG": row_update_flag,
            "ROW_DISUSE_FLAG": row_disuse_flag,
            "ROW_REUSE_FLAG": row_reuse_flag,
            "SUBSTITUTION_VALUE_LINK_FLAG": substitution_value_link_flag,
            "UNIQUE_CONSTRAINT": unique_constraint,
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'TABLE_DEFINITION_ID'
        objdbca.table_insert(t_comn_menu_table_link, data_list, primary_key_name)
    
    except Exception as msg:
        return False, msg
    
    return True, None


def _insert_t_comn_column_group(objdbca, target_column_group_list, dict_t_menu_column_group):
    """
        「カラムグループ管理」メニューのテーブルにレコードを追加する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            target_column_group_list: シートタイプ
            dict_t_menu_column_group: 作成した対象のテーブル名
        RETRUN:
            result, msg
    """
    # テーブル名
    t_comn_column_group = 'T_COMN_COLUMN_GROUP'
    
    try:
        for column_group_id in target_column_group_list:
            target_column_group_data = dict_t_menu_column_group.get(column_group_id)
            if not target_column_group_data:
                continue
            
            # 「パラメータ」を必ず最親のカラムグループ名とするため、「パラメータ」のレコード情報を取得
            param_name_ja = 'パラメータ'
            param_name_en = 'Parameter'
            ret = objdbca.table_select(t_comn_column_group, 'WHERE (FULL_COL_GROUP_NAME_JA = %s OR FULL_COL_GROUP_NAME_EN = %s) AND DISUSE_FLAG = %s', [param_name_ja, param_name_en, 0])  # noqa: E501
            if not ret:
                msg = g.appmsg.get_log_message("BKY-20208", [])
                raise Exception(msg)
            param_col_group_id = ret[0].get('COL_GROUP_ID')
            
            # 対象のカラムグループのフルカラムグループ名(ja/en)がすでに登録されている場合はスキップ。
            full_col_group_name_ja = param_name_ja + '/' + str(target_column_group_data.get('full_col_group_name_ja'))  # フルカラムグループ名に「パラメータ/」を足した名前  # noqa: E501
            full_col_group_name_en = param_name_en + '/' + str(target_column_group_data.get('full_col_group_name_en'))  # フルカラムグループ名に「Parameter/」を足した名前  # noqa: E501
            ret = objdbca.table_select(t_comn_column_group, 'WHERE (FULL_COL_GROUP_NAME_JA = %s OR FULL_COL_GROUP_NAME_EN = %s) AND DISUSE_FLAG = %s', [full_col_group_name_ja, full_col_group_name_en, 0])  # noqa: E501
            if ret:
                continue
            
            # 親カラムグループがある場合は、親カラムグループのIDを取得
            pa_col_group_id = target_column_group_data.get('pa_col_group_id')
            if pa_col_group_id:
                pa_column_group_data = dict_t_menu_column_group.get(pa_col_group_id)
                pa_full_col_group_name_ja = param_name_ja + '/' + str(pa_column_group_data.get('full_col_group_name_ja'))  # フルカラムグループ名に「パラメータ/」を足した名前  # noqa: E501
                pa_full_col_group_name_en = param_name_en + '/' + str(pa_column_group_data.get('full_col_group_name_en'))  # フルカラムグループ名に「Parameter/」を足した名前  # noqa: E501
                ret = objdbca.table_select(t_comn_column_group, 'WHERE (FULL_COL_GROUP_NAME_JA = %s OR FULL_COL_GROUP_NAME_EN = %s) AND DISUSE_FLAG = %s', [pa_full_col_group_name_ja, pa_full_col_group_name_en, 0])  # noqa: E501
                if not ret:
                    msg = g.appmsg.get_log_message("BKY-20210", [pa_full_col_group_name_en])
                    raise Exception(msg)
                
                pa_target_id = ret[0].get('COL_GROUP_ID')
            
            # 親カラムグループが無い場合、「パラメータ」を親カラムグループとして指定する
            else:
                pa_target_id = param_col_group_id
                                
            # 「カラムグループ管理」に登録を実行
            data_list = {
                "PA_COL_GROUP_ID": pa_target_id,
                "COL_GROUP_NAME_JA": target_column_group_data.get('col_group_name_ja'),
                "COL_GROUP_NAME_EN": target_column_group_data.get('col_group_name_en'),
                "FULL_COL_GROUP_NAME_JA": full_col_group_name_ja,
                "FULL_COL_GROUP_NAME_EN": full_col_group_name_en,
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COL_GROUP_ID'
            objdbca.table_insert(t_comn_column_group, data_list, primary_key_name)
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _insert_t_comn_menu_column_link(objdbca, sheet_type, vertical_flag, menu_uuid, input_menu_uuid, dict_t_comn_column_group, dict_t_menu_column_group, record_t_menu_column, dict_t_menu_other_link, record_v_menu_reference_item, menu_group_col_name):  # noqa: E501, C901
    """
        「メニュー-カラム紐付管理」メニューのテーブルにレコードを追加する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            sheet_type: シートタイプ
            vertical_flag: 縦メニュー利用の有無
            menu_uuid: メニュー作成の対象となる「メニュー管理」のレコードのID
            input_menu_uuid: メニュー作成の対象となる「メニュー管理」のレコードのID（「入力用」メニューグループに作成したもの）
            dict_t_comn_column_group: 「カラムグループ管理」のレコードのidをkeyにしたdict
            dict_t_menu_column_group: 「カラムグループ作成情報」のレコードのidをkeyにしたdict
            record_t_menu_column:「メニュー項目作成情報」の対象のレコード一覧
            dict_t_menu_other_link: 「他メニュー連携」のレコードのidをkeyにしたdict
            record_v_menu_reference_item: 「参照項目情報」のレコード一覧
            menu_group_col_name: 対象メニューグループ名
        RETRUN:
            boolean, msg
    """
    try:
        # テーブル名
        t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'
        t_comn_column_group = 'T_COMN_COLUMN_GROUP'
        
        # 表示順序用変数
        disp_seq_num = 10
        
        # 「項番」用のレコードを登録
        res_valid, msg = _check_column_validation(objdbca, menu_uuid, "uuid")
        if not res_valid:
            raise Exception(msg)
        
        data_list = {
            "MENU_ID": menu_uuid,
            "COLUMN_NAME_JA": "項番",
            "COLUMN_NAME_EN": "uuid",
            "COLUMN_NAME_REST": "uuid",
            "COL_GROUP_ID": None,
            "COLUMN_CLASS": 1,  # SingleTextColumn
            "COLUMN_DISP_SEQ": disp_seq_num,
            "REF_TABLE_NAME": None,
            "REF_PKEY_NAME": None,
            "REF_COL_NAME": None,
            "REF_SORT_CONDITIONS": None,
            "REF_MULTI_LANG": 0,  # False
            "REFERENCE_ITEM": None,
            "SENSITIVE_COL_NAME": None,
            "FILE_UPLOAD_PLACE": None,
            "BUTTON_ACTION": None,
            "COL_NAME": "ROW_ID",
            "SAVE_TYPE": None,
            "AUTO_INPUT": 1,  # True
            "INPUT_ITEM": 0,  # False
            "VIEW_ITEM": 1,  # True
            "UNIQUE_ITEM": 1,  # True
            "REQUIRED_ITEM": 1,  # True
            "AUTOREG_HIDE_ITEM": 1,  # True
            "AUTOREG_ONLY_ITEM": 0,  # False
            "INITIAL_VALUE": None,
            "VALIDATE_OPTION": None,
            "VALIDATE_REG_EXP": None,
            "BEFORE_VALIDATE_REGISTER": None,
            "AFTER_VALIDATE_REGISTER": None,
            "DESCRIPTION_JA": "自動採番のため編集不可。実行処理種別が【登録】の場合、空白のみ可。",
            "DESCRIPTION_EN": "Cannot edit because of auto-numbering. Must be blank when execution process type is [Register].",  # noqa: E501
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'COLUMN_DEFINITION_ID'
        objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
        
        # 表示順序を加算
        disp_seq_num = int(disp_seq_num) + 10
        
        # シートタイプが「1: パラメータシート（ホスト/オペレーションあり）」の場合のみ
        if sheet_type == "1":
            # 「ホスト名」用のレコードを作成
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, "host_name")
            if not res_valid:
                raise Exception(msg)
            
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": "ホスト名",
                "COLUMN_NAME_EN": "Host name",
                "COLUMN_NAME_REST": "host_name",
                "COL_GROUP_ID": None,
                "COLUMN_CLASS": 7,  # IDColumn
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": "T_ANSC_DEVICE",
                "REF_PKEY_NAME": "SYSTEM_ID",
                "REF_COL_NAME": "HOST_NAME",
                "REF_SORT_CONDITIONS": None,
                "REF_MULTI_LANG": 0,  # False
                "REFERENCE_ITEM": None,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": None,
                "BUTTON_ACTION": None,
                "COL_NAME": "HOST_ID",
                "SAVE_TYPE": None,
                "AUTO_INPUT": 0,  # False
                "INPUT_ITEM": 1,  # True
                "VIEW_ITEM": 1,  # True
                "UNIQUE_ITEM": 0,  # False
                "REQUIRED_ITEM": 1,  # True
                "AUTOREG_HIDE_ITEM": 1,  # True
                "AUTOREG_ONLY_ITEM": 0,  # False
                "INITIAL_VALUE": None,
                "VALIDATE_OPTION": None,
                "VALIDATE_REG_EXP": None,
                "BEFORE_VALIDATE_REGISTER": None,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": "[元データ]Ansible共通/機器一覧",
                "DESCRIPTION_EN": "[Original data] Ansible Common/Device list",
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
            
            # カラムグループ「オペレーション」の情報を取得
            operation_name_ja = 'オペレーション'
            operation_name_en = 'Operation'
            ret = objdbca.table_select(t_comn_column_group, 'WHERE (FULL_COL_GROUP_NAME_JA = %s OR FULL_COL_GROUP_NAME_EN = %s) AND DISUSE_FLAG = %s', [operation_name_ja, operation_name_en, 0])  # noqa: E501
            if not ret:
                msg = g.appmsg.get_log_message("BKY-20209", [])
                raise Exception(msg)
            operation_col_group_id = ret[0].get('COL_GROUP_ID')
            
            # 「オペレーション(日付:オペレーション名)」用のレコードを作成
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, "operation_name_select")
            if not res_valid:
                raise Exception(msg)
            
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": "オペレーション名",
                "COLUMN_NAME_EN": "Operation name",
                "COLUMN_NAME_REST": "operation_name_select",
                "COL_GROUP_ID": operation_col_group_id,  # カラムグループ「オペレーション」
                "COLUMN_CLASS": 7,  # IDColumn
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": "V_COMN_OPERATION",
                "REF_PKEY_NAME": "OPERATION_ID",
                "REF_COL_NAME": "OPERATION_DATE_NAME",
                "REF_SORT_CONDITIONS": None,
                "REF_MULTI_LANG": 0,  # False
                "REFERENCE_ITEM": None,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": None,
                "BUTTON_ACTION": None,
                "COL_NAME": "OPERATION_ID",
                "SAVE_TYPE": None,
                "AUTO_INPUT": 0,  # False
                "INPUT_ITEM": 1,  # True
                "VIEW_ITEM": 0,  # False
                "UNIQUE_ITEM": 0,  # False
                "REQUIRED_ITEM": 1,  # True
                "AUTOREG_HIDE_ITEM": 1,  # True
                "AUTOREG_ONLY_ITEM": 0,  # False
                "INITIAL_VALUE": None,
                "VALIDATE_OPTION": None,
                "VALIDATE_REG_EXP": None,
                "BEFORE_VALIDATE_REGISTER": None,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": "[元データ]基本コンソール/オペレーション一覧",
                "DESCRIPTION_EN": "[Original data] Basic console/Operation list",
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
            
            # 「オペレーション名」用のレコードを作成
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, "operation_name_disp")
            if not res_valid:
                raise Exception(msg)
            
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": "オペレーション名",
                "COLUMN_NAME_EN": "Operation name",
                "COLUMN_NAME_REST": "operation_name_disp",
                "COL_GROUP_ID": operation_col_group_id,  # カラムグループ「オペレーション」
                "COLUMN_CLASS": 1,  # SingleTextColumn
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": None,
                "REF_PKEY_NAME": None,
                "REF_COL_NAME": None,
                "REF_SORT_CONDITIONS": None,
                "REF_MULTI_LANG": 0,  # False
                "REFERENCE_ITEM": None,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": None,
                "BUTTON_ACTION": None,
                "COL_NAME": "OPERATION_NAME",
                "SAVE_TYPE": None,
                "AUTO_INPUT": 0,  # False
                "INPUT_ITEM": 2,  # 2:入力欄非表示
                "VIEW_ITEM": 1,  # True
                "UNIQUE_ITEM": 0,  # False
                "REQUIRED_ITEM": 0,  # False
                "AUTOREG_HIDE_ITEM": 1,  # True
                "AUTOREG_ONLY_ITEM": 0,  # False
                "INITIAL_VALUE": None,
                "VALIDATE_OPTION": None,
                "VALIDATE_REG_EXP": None,
                "BEFORE_VALIDATE_REGISTER": None,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": "[元データ]基本コンソール/オペレーション一覧",
                "DESCRIPTION_EN": "[Original data] Basic console/Operation list",
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
            
            # 「オペレーション(基準日時)」用のレコードを作成
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, "base_datetime")
            if not res_valid:
                raise Exception(msg)
            
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": "基準日時",
                "COLUMN_NAME_EN": "Base datetime",
                "COLUMN_NAME_REST": "base_datetime",
                "COL_GROUP_ID": operation_col_group_id,  # カラムグループ「オペレーション」
                "COLUMN_CLASS": 5,  # DateTimeColumn
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": None,
                "REF_PKEY_NAME": None,
                "REF_COL_NAME": None,
                "REF_SORT_CONDITIONS": None,
                "REF_MULTI_LANG": 0,  # False
                "REFERENCE_ITEM": None,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": None,
                "BUTTON_ACTION": None,
                "COL_NAME": "BASE_TIMESTAMP",
                "SAVE_TYPE": None,
                "AUTO_INPUT": 1,  # True
                "INPUT_ITEM": 0,  # False
                "VIEW_ITEM": 1,  # True
                "UNIQUE_ITEM": 0,  # False
                "REQUIRED_ITEM": 0,  # False
                "AUTOREG_HIDE_ITEM": 1,  # True
                "AUTOREG_ONLY_ITEM": 0,  # False
                "INITIAL_VALUE": None,
                "VALIDATE_OPTION": None,
                "VALIDATE_REG_EXP": None,
                "BEFORE_VALIDATE_REGISTER": None,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": "基本コンソール/オペレーション一覧の「最終実行日時」に値がある場合は「最終実行日時」、値が無い場合は「実施予定日時」",
                "DESCRIPTION_EN": "If \"Last execute date\" of \"Basic console / operation list\" has a value, \"Last execution date\" is displayed, otherwise \"Scheduled date for execution\" is displayed.",  # noqa: E501
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
            
            # 「オペレーション(実施予定日)」用のレコードを作成
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, "operation_date")
            if not res_valid:
                raise Exception(msg)
            
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": "実施予定日",
                "COLUMN_NAME_EN": "Operation date",
                "COLUMN_NAME_REST": "operation_date",
                "COL_GROUP_ID": operation_col_group_id,  # カラムグループ「オペレーション」
                "COLUMN_CLASS": 5,  # DateTimeColumn
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": None,
                "REF_PKEY_NAME": None,
                "REF_COL_NAME": None,
                "REF_SORT_CONDITIONS": None,
                "REF_MULTI_LANG": 0,  # False
                "REFERENCE_ITEM": None,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": None,
                "BUTTON_ACTION": None,
                "COL_NAME": "OPERATION_DATE",
                "SAVE_TYPE": None,
                "AUTO_INPUT": 1,  # True
                "INPUT_ITEM": 0,  # False
                "VIEW_ITEM": 1,  # True
                "UNIQUE_ITEM": 0,  # False
                "REQUIRED_ITEM": 0,  # False
                "AUTOREG_HIDE_ITEM": 1,  # True
                "AUTOREG_ONLY_ITEM": 0,  # False
                "INITIAL_VALUE": None,
                "VALIDATE_OPTION": None,
                "VALIDATE_REG_EXP": None,
                "BEFORE_VALIDATE_REGISTER": None,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": "[元データ]基本コンソール/オペレーション一覧",
                "DESCRIPTION_EN": "[Original data] Basic console/Operation list",
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
            
            # 「オペレーション(最終実行日時)」用のレコードを作成
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, "last_execute_timestamp")
            if not res_valid:
                raise Exception(msg)
            
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": "最終実行日時",
                "COLUMN_NAME_EN": "Last execute datetime",
                "COLUMN_NAME_REST": "last_execute_timestamp",
                "COL_GROUP_ID": operation_col_group_id,  # カラムグループ「オペレーション」
                "COLUMN_CLASS": 5,  # DateTimeColumn
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": None,
                "REF_PKEY_NAME": None,
                "REF_COL_NAME": None,
                "REF_SORT_CONDITIONS": None,
                "REF_MULTI_LANG": 0,  # False
                "REFERENCE_ITEM": None,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": None,
                "BUTTON_ACTION": None,
                "COL_NAME": "LAST_EXECUTE_TIMESTAMP",
                "SAVE_TYPE": None,
                "AUTO_INPUT": 1,  # True
                "INPUT_ITEM": 0,  # False
                "VIEW_ITEM": 1,  # True
                "UNIQUE_ITEM": 0,  # False
                "REQUIRED_ITEM": 0,  # False
                "AUTOREG_HIDE_ITEM": 1,  # True
                "AUTOREG_ONLY_ITEM": 0,  # False
                "INITIAL_VALUE": None,
                "VALIDATE_OPTION": None,
                "VALIDATE_REG_EXP": None,
                "BEFORE_VALIDATE_REGISTER": None,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": "[元データ]基本コンソール/オペレーション一覧",
                "DESCRIPTION_EN": "[Original data] Basic console/Operation list",
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
            
            # 縦メニュー利用ありの場合のみ「代入順序」用のレコードを作成
            if vertical_flag:
                res_valid, msg = _check_column_validation(objdbca, menu_uuid, "input_order")
                if not res_valid:
                    raise Exception(msg)
                
                data_list = {
                    "MENU_ID": menu_uuid,
                    "COLUMN_NAME_JA": "代入順序",
                    "COLUMN_NAME_EN": "Input order",
                    "COLUMN_NAME_REST": "input_order",
                    "COL_GROUP_ID": None,
                    "COLUMN_CLASS": 3,  # NumColumn
                    "COLUMN_DISP_SEQ": disp_seq_num,
                    "REF_TABLE_NAME": None,
                    "REF_PKEY_NAME": None,
                    "REF_COL_NAME": None,
                    "REF_SORT_CONDITIONS": None,
                    "REF_MULTI_LANG": 0,  # False
                    "REFERENCE_ITEM": None,
                    "SENSITIVE_COL_NAME": None,
                    "FILE_UPLOAD_PLACE": None,
                    "BUTTON_ACTION": None,
                    "COL_NAME": "INPUT_ORDER",
                    "SAVE_TYPE": None,
                    "AUTO_INPUT": 0,  # False
                    "INPUT_ITEM": 1,  # True
                    "VIEW_ITEM": 1,  # True
                    "UNIQUE_ITEM": 0,  # False
                    "REQUIRED_ITEM": 1,  # True
                    "AUTOREG_HIDE_ITEM": 1,  # True
                    "AUTOREG_ONLY_ITEM": 0,  # False
                    "INITIAL_VALUE": None,
                    "VALIDATE_OPTION": None,
                    "VALIDATE_REG_EXP": None,
                    "BEFORE_VALIDATE_REGISTER": None,
                    "AFTER_VALIDATE_REGISTER": None,
                    "DESCRIPTION_JA": "代入順序となる値を入力します。",
                    "DESCRIPTION_EN": "Enter the values that will be the input order.",
                    "DISUSE_FLAG": "0",
                    "LAST_UPDATE_USER": g.get('USER_ID')
                }
                primary_key_name = 'COLUMN_DEFINITION_ID'
                objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
                
                # 表示順序を加算
                disp_seq_num = int(disp_seq_num) + 10
        
        # カラムグループ「パラメータ」の情報を取得
        param_name_ja = 'パラメータ'
        param_name_en = 'Parameter'
        ret = objdbca.table_select(t_comn_column_group, 'WHERE (FULL_COL_GROUP_NAME_JA = %s OR FULL_COL_GROUP_NAME_EN = %s) AND DISUSE_FLAG = %s', [param_name_ja, param_name_en, 0])  # noqa: E501
        if not ret:
            msg = g.appmsg.get_log_message("BKY-20208", [])
            raise Exception(msg)
        param_col_group_id = ret[0].get('COL_GROUP_ID')
        
        # 「メニュー作成機能で作成した項目」の対象の数だけループスタート
        for record in record_t_menu_column:
            column_name_rest = record.get('COLUMN_NAME_REST')
            column_class = str(record.get('COLUMN_CLASS'))
            
            # 初期値に登録する値を生成
            ret, msg, initial_value = _create_initial_value(record)
            if not ret:
                raise Exception(msg)
            
            # バリデーションに登録する値を生成
            ret, msg, validate_option, validate_regular_expression = _create_validate_option(record)
            if not ret:
                raise Exception(msg)
            
            # IDColumn用の値
            ref_table_name = None
            ref_pkey_name = None
            ref_col_name = None
            ref_sort_conditions = None
            ref_multi_lang = 0
            reference_item = None
            reference_item_list = []
            str_convert_reference_item_list = None
            set_before_function = None
            
            # カラムクラスが「5:日時」「6:日付」の場合は代入値自動登録対象外とするため、autoreg_hide_itemを1とする。
            autoreg_hide_item = 0
            if column_class == "5" or column_class == "6":
                autoreg_hide_item = 1
            
            # カラムクラスが「プルダウン選択」の場合、「他メニュー連携」のレコードからIDColumnに必要なデータを取得し変数に格納
            if column_class == "7":
                other_menu_link_id = record.get('OTHER_MENU_LINK_ID')
                target_other_menu_link_record = dict_t_menu_other_link.get(other_menu_link_id)
                ref_table_name = target_other_menu_link_record.get('REF_TABLE_NAME')
                ref_pkey_name = target_other_menu_link_record.get('REF_PKEY_NAME')
                ref_sort_conditions = target_other_menu_link_record.get('REF_SORT_CONDITIONS')
                ref_multi_lang = target_other_menu_link_record.get('REF_MULTI_LANG')
                menu_create_flag = target_other_menu_link_record.get('MENU_CREATE_FLAG')
                if str(menu_create_flag) == "1":
                    ref_col_name = target_other_menu_link_record.get('REF_COL_NAME_REST')
                    column_class = "21"  # JsonIDColumn
                else:
                    ref_col_name = target_other_menu_link_record.get('REF_COL_NAME')
                
                other_link_target_column_class = target_other_menu_link_record.get('COLUMN_CLASS')
                # 参照元のカラムクラスが「5:日時」「6:日付」の場合は代入値自動登録対象外とするため、autoreg_hide_itemを1とする。
                if other_link_target_column_class == "5" or other_link_target_column_class == "6":
                    autoreg_hide_item = 1
                
                # 「参照項目」情報を取得
                reference_item = record.get('REFERENCE_ITEM')
                if reference_item:
                    reference_item_list = ast.literal_eval(reference_item)
                    set_before_function = "set_reference_value"
                    if type(reference_item_list) is not list:
                        msg = g.appmsg.get_log_message("BKY-20212", [reference_item])
                        raise Exception(msg)
                    
                    # reference_itemの中のcolumn_name_restを「_ref_X」形式に変換
                    convert_reference_item_list = []
                    for ref_count, target_column_name_rest in enumerate(reference_item_list, 1):
                        ref_column_name_rest = str(column_name_rest) + "_ref_" + str(ref_count)
                        convert_reference_item_list.append(ref_column_name_rest)
                    str_convert_reference_item_list = json.dumps(convert_reference_item_list)
            
            # カラムクラスが「ファイルアップロード」の場合かつ、「代入値自動登録用」「参照用」メニューの場合、ファイルの格納先を指定する。
            file_upload_place = None
            if column_class == "9":
                if menu_group_col_name == "MENU_GROUP_ID_SUBST" or menu_group_col_name == "MENU_GROUP_ID_REF":
                    file_upload_place = "/uploadfiles/{}/{}".format(input_menu_uuid, column_name_rest)
                
            # 「カラムグループ作成情報」のIDから同じフルカラムグループ名の対象を「カラムグループ管理」から探しIDを指定
            col_group_id = None
            tmp_col_group_id = record.get('CREATE_COL_GROUP_ID')
            target_t_menu_column_group = dict_t_menu_column_group.get(tmp_col_group_id)
            if target_t_menu_column_group:
                t_full_col_group_name_ja = param_name_ja + '/' + str(target_t_menu_column_group.get('full_col_group_name_ja'))  # フルカラムグループ名に「パラメータ/」を足した名前  # noqa: E501
                t_full_col_group_name_en = param_name_en + '/' + str(target_t_menu_column_group.get('full_col_group_name_en'))  # フルカラムグループ名に「Paramater/」を足した名前  # noqa: E501
                for key_id, target_t_comn_column_group in dict_t_comn_column_group.items():
                    c_full_col_group_name_ja = target_t_comn_column_group.get('full_col_group_name_ja')
                    c_full_col_group_name_en = target_t_comn_column_group.get('full_col_group_name_en')
                    # フルカラムグループ名が一致している対象のカラムグループ管理IDを指定
                    if (t_full_col_group_name_ja == c_full_col_group_name_ja) or (t_full_col_group_name_en == c_full_col_group_name_en):
                        col_group_id = key_id
                        break
            # カラムグループが無い場合「パラメータ」をカラムグループとして指定する
            else:
                col_group_id = param_col_group_id
            
            # 「メニュー作成機能で作成した項目」用のレコードを作成
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, column_name_rest)
            if not res_valid:
                raise Exception(msg)
            
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": record.get('COLUMN_NAME_JA'),
                "COLUMN_NAME_EN": record.get('COLUMN_NAME_EN'),
                "COLUMN_NAME_REST": column_name_rest,
                "COL_GROUP_ID": col_group_id,
                "COLUMN_CLASS": column_class,
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": ref_table_name,
                "REF_PKEY_NAME": ref_pkey_name,
                "REF_COL_NAME": ref_col_name,
                "REF_SORT_CONDITIONS": ref_sort_conditions,
                "REF_MULTI_LANG": ref_multi_lang,
                "REFERENCE_ITEM": str_convert_reference_item_list,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": file_upload_place,
                "BUTTON_ACTION": None,
                "COL_NAME": "DATA_JSON",
                "SAVE_TYPE": "JSON",
                "AUTO_INPUT": 0,  # False
                "INPUT_ITEM": 1,  # True
                "VIEW_ITEM": 1,  # True
                "UNIQUE_ITEM": record.get('UNIQUED'),
                "REQUIRED_ITEM": record.get('REQUIRED'),
                "AUTOREG_HIDE_ITEM": autoreg_hide_item,
                "AUTOREG_ONLY_ITEM": 0,  # False
                "INITIAL_VALUE": initial_value,
                "VALIDATE_OPTION": validate_option,
                "VALIDATE_REG_EXP": validate_regular_expression,
                "BEFORE_VALIDATE_REGISTER": set_before_function,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": record.get('DESCRIPTION_JA'),
                "DESCRIPTION_EN": record.get('DESCRIPTION_EN'),
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
            
            # 「参照項目」がある場合、参照項目用のレコードを作成
            if reference_item_list:
                for ref_count, target_column_name_rest in enumerate(reference_item_list, 1):
                    ref_column_name_rest = str(column_name_rest) + "_ref_" + str(ref_count)
                    # 「参照項目情報」から対象のレコードを特定
                    for ref_item_record in record_v_menu_reference_item:
                        reference_link_id = ref_item_record.get('LINK_ID')
                        reference_column_name_rest = ref_item_record.get('COLUMN_NAME_REST')
                        sensitive_flag = ref_item_record.get('SENSITIVE_FLAG')
                        
                        # ColumnClassを選定
                        ref_column_class = column_class
                        if column_class == "7" and sensitive_flag == "1":  # 親のプルダウン選択がIDColumnかつsensitive_flagが1(True)なら「25:PasswordIDColumn」とする
                            ref_column_class = "25"
                        elif column_class == "21" and sensitive_flag == "1":  # 親のプルダウン選択がJsonIDColumnかつsensitive_flagが1(True)なら「26:JsonPasswordIDColumn」とする  # noqa: E501
                            ref_column_class = "26"
                        if target_column_name_rest == reference_column_name_rest and other_menu_link_id == reference_link_id:
                            res_valid, msg = _check_column_validation(objdbca, menu_uuid, ref_column_name_rest)
                            if not res_valid:
                                raise Exception(msg)
                            
                            # カラムクラスが「5:日時」「6:日付」の場合は代入値自動登録対象外とするため、autoreg_hide_itemを1とする。
                            autoreg_hide_item = 0
                            if column_class == "5" or column_class == "6":
                                autoreg_hide_item = 1
                            
                            data_list = {
                                "MENU_ID": menu_uuid,
                                "COLUMN_NAME_JA": ref_item_record.get('COLUMN_NAME_JA'),
                                "COLUMN_NAME_EN": ref_item_record.get('COLUMN_NAME_EN'),
                                "COLUMN_NAME_REST": ref_column_name_rest,
                                "COL_GROUP_ID": col_group_id,  # 直前に作成したIDColumnの項目と同じカラムグループを採用する
                                "COLUMN_CLASS": ref_column_class,  # 「7:IDColumn」or「21:JsonIDColumn」or「25:PasswordIDColumn」or「26:JsonPasswordIDColumn」
                                "COLUMN_DISP_SEQ": disp_seq_num,
                                "REF_TABLE_NAME": ref_item_record.get('REF_TABLE_NAME'),
                                "REF_PKEY_NAME": ref_item_record.get('REF_PKEY_NAME'),
                                "REF_COL_NAME": ref_item_record.get('REF_COL_NAME'),
                                "REF_SORT_CONDITIONS": ref_item_record.get('REF_SORT_CONDITIONS'),
                                "REF_MULTI_LANG": ref_item_record.get('REF_MULTI_LANG'),
                                "REFERENCE_ITEM": None,
                                "SENSITIVE_COL_NAME": None,
                                "FILE_UPLOAD_PLACE": None,
                                "BUTTON_ACTION": None,
                                "COL_NAME": "DATA_JSON",
                                "SAVE_TYPE": "JSON",
                                "AUTO_INPUT": 0,  # False
                                "INPUT_ITEM": 2,  # 2:入力欄非表示
                                "VIEW_ITEM": 1,  # True
                                "UNIQUE_ITEM": 0,  # False
                                "REQUIRED_ITEM": 0,  # False
                                "AUTOREG_HIDE_ITEM": autoreg_hide_item,
                                "AUTOREG_ONLY_ITEM": 0,  # False
                                "INITIAL_VALUE": None,
                                "VALIDATE_OPTION": None,
                                "VALIDATE_REG_EXP": None,
                                "BEFORE_VALIDATE_REGISTER": None,
                                "AFTER_VALIDATE_REGISTER": None,
                                "DESCRIPTION_JA": ref_item_record.get('DESCRIPTION_JA'),
                                "DESCRIPTION_EN": ref_item_record.get('DESCRIPTION_EN'),
                                "DISUSE_FLAG": "0",
                                "LAST_UPDATE_USER": g.get('USER_ID')
                            }
                            primary_key_name = 'COLUMN_DEFINITION_ID'
                            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
                            
                            # 表示順序を加算
                            disp_seq_num = int(disp_seq_num) + 10
        
        # 「メニュー作成機能で作成した項目」が0件の場合、特殊な項目を作成
        if not record_t_menu_column:
            res_valid, msg = _check_column_validation(objdbca, menu_uuid, "no_item")
            if not res_valid:
                raise Exception(msg)
            validate_option = '{"min_length": 0,"max_length": 255}'
            data_list = {
                "MENU_ID": menu_uuid,
                "COLUMN_NAME_JA": "(項目なし)",
                "COLUMN_NAME_EN": "(No item)",
                "COLUMN_NAME_REST": "no_item",
                "COL_GROUP_ID": None,
                "COLUMN_CLASS": "1",
                "COLUMN_DISP_SEQ": disp_seq_num,
                "REF_TABLE_NAME": None,
                "REF_PKEY_NAME": None,
                "REF_COL_NAME": None,
                "REF_SORT_CONDITIONS": None,
                "REF_MULTI_LANG": 0,  # False
                "REFERENCE_ITEM": None,
                "SENSITIVE_COL_NAME": None,
                "FILE_UPLOAD_PLACE": None,
                "BUTTON_ACTION": None,
                "COL_NAME": "DATA_JSON",
                "SAVE_TYPE": None,
                "AUTO_INPUT": 0,  # False
                "INPUT_ITEM": 2,  # 2:入力欄非表示
                "VIEW_ITEM": 0,  # False
                "UNIQUE_ITEM": 1,  # True
                "REQUIRED_ITEM": 1,  # True
                "AUTOREG_HIDE_ITEM": 0,  # False
                "AUTOREG_ONLY_ITEM": 1,  # True
                "INITIAL_VALUE": None,
                "VALIDATE_OPTION": validate_option,
                "VALIDATE_REG_EXP": None,
                "BEFORE_VALIDATE_REGISTER": None,
                "AFTER_VALIDATE_REGISTER": None,
                "DESCRIPTION_JA": "代入値自動登録設定用の項目",
                "DESCRIPTION_EN": "Item for substitution value auto-registration setting",
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            primary_key_name = 'COLUMN_DEFINITION_ID'
            objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
            
            # 表示順序を加算
            disp_seq_num = int(disp_seq_num) + 10
        
        # 「備考」用のレコードを作成
        res_valid, msg = _check_column_validation(objdbca, menu_uuid, "remarks")
        if not res_valid:
            raise Exception(msg)
        
        validate_option = '{"min_length": 0,"max_length": 4000}'
        data_list = {
            "MENU_ID": menu_uuid,
            "COLUMN_NAME_JA": "備考",
            "COLUMN_NAME_EN": "Remarks",
            "COLUMN_NAME_REST": "remarks",
            "COL_GROUP_ID": None,
            "COLUMN_CLASS": 12,  # NoteColumn
            "COLUMN_DISP_SEQ": disp_seq_num,
            "REF_TABLE_NAME": None,
            "REF_PKEY_NAME": None,
            "REF_COL_NAME": None,
            "REF_SORT_CONDITIONS": None,
            "REF_MULTI_LANG": 0,  # False
            "REFERENCE_ITEM": None,
            "SENSITIVE_COL_NAME": None,
            "FILE_UPLOAD_PLACE": None,
            "BUTTON_ACTION": None,
            "COL_NAME": "NOTE",
            "SAVE_TYPE": None,
            "AUTO_INPUT": 0,  # False
            "INPUT_ITEM": 1,  # True
            "VIEW_ITEM": 1,  # True
            "UNIQUE_ITEM": 0,  # False
            "REQUIRED_ITEM": 0,  # False
            "AUTOREG_HIDE_ITEM": 1,  # True
            "AUTOREG_ONLY_ITEM": 0,  # False
            "INITIAL_VALUE": None,
            "VALIDATE_OPTION": validate_option,
            "VALIDATE_REG_EXP": None,
            "BEFORE_VALIDATE_REGISTER": None,
            "AFTER_VALIDATE_REGISTER": None,
            "DESCRIPTION_JA": "自由記述欄。レコードの廃止・復活時にも記載可能。",
            "DESCRIPTION_EN": "Comments section. Can comment when removing or res...",
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'COLUMN_DEFINITION_ID'
        objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
        
        # 表示順序を加算
        disp_seq_num = int(disp_seq_num) + 10
        
        # 「廃止フラグ」用のレコードを作成
        res_valid, msg = _check_column_validation(objdbca, menu_uuid, "discard")
        if not res_valid:
            raise Exception(msg)
        
        data_list = {
            "MENU_ID": menu_uuid,
            "COLUMN_NAME_JA": "廃止フラグ",
            "COLUMN_NAME_EN": "Discard",
            "COLUMN_NAME_REST": "discard",
            "COL_GROUP_ID": None,
            "COLUMN_CLASS": 1,  # SingleTextColumn
            "COLUMN_DISP_SEQ": disp_seq_num,
            "REF_TABLE_NAME": None,
            "REF_PKEY_NAME": None,
            "REF_COL_NAME": None,
            "REF_SORT_CONDITIONS": None,
            "REF_MULTI_LANG": 0,  # False
            "REFERENCE_ITEM": None,
            "SENSITIVE_COL_NAME": None,
            "FILE_UPLOAD_PLACE": None,
            "BUTTON_ACTION": None,
            "COL_NAME": "DISUSE_FLAG",
            "SAVE_TYPE": None,
            "AUTO_INPUT": 1,  # True
            "INPUT_ITEM": 1,  # True
            "VIEW_ITEM": 1,  # True
            "UNIQUE_ITEM": 0,  # False
            "REQUIRED_ITEM": 1,  # True
            "AUTOREG_HIDE_ITEM": 1,  # True
            "AUTOREG_ONLY_ITEM": 0,  # False
            "INITIAL_VALUE": None,
            "VALIDATE_OPTION": None,
            "VALIDATE_REG_EXP": None,
            "BEFORE_VALIDATE_REGISTER": None,
            "AFTER_VALIDATE_REGISTER": None,
            "DESCRIPTION_JA": "廃止フラグ。復活以外のオペレーションは不可",
            "DESCRIPTION_EN": "Discard flag. Cannot do operation other than resto...",
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'COLUMN_DEFINITION_ID'
        objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
        
        # 表示順序を加算
        disp_seq_num = int(disp_seq_num) + 10
        
        # 「最終更新日時」用のレコードを作成
        res_valid, msg = _check_column_validation(objdbca, menu_uuid, "last_update_date_time")
        if not res_valid:
            raise Exception(msg)
        
        data_list = {
            "MENU_ID": menu_uuid,
            "COLUMN_NAME_JA": "最終更新日時",
            "COLUMN_NAME_EN": "Last update date/time",
            "COLUMN_NAME_REST": "last_update_date_time",
            "COL_GROUP_ID": None,
            "COLUMN_CLASS": 13,  # LastUpdateDateColumn
            "COLUMN_DISP_SEQ": disp_seq_num,
            "REF_TABLE_NAME": None,
            "REF_PKEY_NAME": None,
            "REF_COL_NAME": None,
            "REF_SORT_CONDITIONS": None,
            "REF_MULTI_LANG": 0,  # False
            "REFERENCE_ITEM": None,
            "SENSITIVE_COL_NAME": None,
            "FILE_UPLOAD_PLACE": None,
            "BUTTON_ACTION": None,
            "COL_NAME": "LAST_UPDATE_TIMESTAMP",
            "SAVE_TYPE": None,
            "AUTO_INPUT": 1,  # True
            "INPUT_ITEM": 0,  # False
            "VIEW_ITEM": 1,  # True
            "UNIQUE_ITEM": 0,  # False
            "REQUIRED_ITEM": 1,  # True
            "AUTOREG_HIDE_ITEM": 1,  # True
            "AUTOREG_ONLY_ITEM": 0,  # False
            "INITIAL_VALUE": None,
            "VALIDATE_OPTION": None,
            "VALIDATE_REG_EXP": None,
            "BEFORE_VALIDATE_REGISTER": None,
            "AFTER_VALIDATE_REGISTER": None,
            "DESCRIPTION_JA": "レコードの最終更新日。自動登録のため編集不可。",
            "DESCRIPTION_EN": "Last update date of record. Cannot edit because of...",
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'COLUMN_DEFINITION_ID'
        objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
        
        # 表示順序を加算
        disp_seq_num = int(disp_seq_num) + 10
        
        # 「最終更新者」用のレコードを作成
        res_valid, msg = _check_column_validation(objdbca, menu_uuid, "last_updated_user")
        if not res_valid:
            raise Exception(msg)
        
        data_list = {
            "MENU_ID": menu_uuid,
            "COLUMN_NAME_JA": "最終更新者",
            "COLUMN_NAME_EN": "Last updated by",
            "COLUMN_NAME_REST": "last_updated_user",
            "COL_GROUP_ID": None,
            "COLUMN_CLASS": 14,  # LastUpdateUserColumn
            "COLUMN_DISP_SEQ": disp_seq_num,
            "REF_TABLE_NAME": None,
            "REF_PKEY_NAME": None,
            "REF_COL_NAME": None,
            "REF_SORT_CONDITIONS": None,
            "REF_MULTI_LANG": 0,  # False
            "REFERENCE_ITEM": None,
            "SENSITIVE_COL_NAME": None,
            "FILE_UPLOAD_PLACE": None,
            "BUTTON_ACTION": None,
            "COL_NAME": "LAST_UPDATE_USER",
            "SAVE_TYPE": None,
            "AUTO_INPUT": 1,  # True
            "INPUT_ITEM": 0,  # False
            "VIEW_ITEM": 1,  # True
            "UNIQUE_ITEM": 0,  # False
            "REQUIRED_ITEM": 1,  # True
            "AUTOREG_HIDE_ITEM": 1,  # True
            "AUTOREG_ONLY_ITEM": 0,  # False
            "INITIAL_VALUE": None,
            "VALIDATE_OPTION": None,
            "VALIDATE_REG_EXP": None,
            "BEFORE_VALIDATE_REGISTER": None,
            "AFTER_VALIDATE_REGISTER": None,
            "DESCRIPTION_JA": "更新者。ログインユーザのIDが自動的に登録される。編集不可。",
            "DESCRIPTION_EN": "Updated by. Login user ID is automatically registe...",
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'COLUMN_DEFINITION_ID'
        objdbca.table_insert(t_comn_menu_column_link, data_list, primary_key_name)
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _update_t_menu_define(objdbca, menu_create_id, menu_create_done_status_id):
    """
        「メニュー定義一覧」メニューのレコードを更新する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_create_id: 対象の「メニュー定義一覧」のレコードのUUID
            menu_create_done_status_id: 作成状態のID「1:未作成」,「2:作成済み」
        RETRUN:
            result, msg
    """
    # テーブル名
    t_menu_define = 'T_MENU_DEFINE'
    
    try:
        t_menu_define_record = objdbca.table_select(t_menu_define, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
        target_menu_create_done_status = str(t_menu_define_record[0].get('MENU_CREATE_DONE_STATUS'))
        if target_menu_create_done_status == '1':
            data_list = {
                "MENU_CREATE_ID": menu_create_id,
                "MENU_CREATE_DONE_STATUS": menu_create_done_status_id,
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            objdbca.table_update(t_menu_define, data_list, 'MENU_CREATE_ID')
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _insert_t_menu_table_link(objdbca, menu_uuid, create_table_name, create_table_name_jnl):
    """
        「メニュー定義-テーブル紐付管理」メニューのテーブルにレコードを追加する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_uuid: 対象のメニュー（「メニュー管理」のレコード）のUUID
            create_table_name: 作成した対象のテーブル名
            create_table_name_jnl: 作成した対象の履歴用テーブル名
        RETRUN:
            result, msg
    """
    # テーブル名
    t_menu_table_link = 'T_MENU_TABLE_LINK'
    
    try:
        data_list = {
            "MENU_ID": menu_uuid,
            "MENU_NAME_REST": menu_uuid,
            "TABLE_NAME": create_table_name,
            "KEY_COL_NAME": "ROW_ID",
            "TABLE_NAME_JNL": create_table_name_jnl,
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        primary_key_name = 'MENU_TABLE_LINK_ID'
        objdbca.table_insert(t_menu_table_link, data_list, primary_key_name)
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _insert_t_menu_other_link(objdbca, menu_uuid, create_table_name, record_t_menu_column):
    """
        「他メニュー連携」メニューのテーブルにレコードを追加する。また、同一内容の廃止済みレコードがある場合は復活処理をする。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_uuid: 対象のメニュー（「メニュー管理」のレコード）のUUID
            create_table_name: 作成した対象のテーブル名
            record_t_menu_column: 「メニュー項目作成情報」の対象のレコード一覧
        RETRUN:
            result, msg
    """
    # テーブル名
    t_menu_other_link = 'T_MENU_OTHER_LINK'
    
    try:
        # 他メニュー連携の対象とするカラムクラス一覧(1:SingleTextColumn, 2:MultiTextColumn, 3:NumColumn, 4:FloatColumn, 5:DateTimeColumn, 6:DateColumn, 10:HostInsideLinkTextColumn)  # noqa: E501
        target_column_class_list = ["1", "2", "3", "4", "5", "6", "10"]
        for record in record_t_menu_column:
            column_class = str(record.get('COLUMN_CLASS'))
            required = str(record.get('REQUIRED'))
            uniqued = str(record.get('UNIQUED'))
            
            # カラムクラスが他メニュー連携の対象かつ、必須かつ、一意制約の場合登録を実施
            if column_class in target_column_class_list and required == "1" and uniqued == "1":
                column_name_rest = record.get('COLUMN_NAME_REST')
                column_disp_name_ja = record.get('COLUMN_NAME_JA')
                column_disp_name_en = record.get('COLUMN_NAME_EN')
                
                # 廃止済みレコードの中から「MENU_ID」「REF_TABLE_NAME」「REF_COL_NAME_REST」「COLUMN_CLASS」が一致しているレコードを検索
                sql_where = 'WHERE MENU_ID = %s AND REF_TABLE_NAME = %s AND REF_COL_NAME_REST = %s AND COLUMN_CLASS = %s AND DISUSE_FLAG = %s'
                sql_bind = [menu_uuid, create_table_name, column_name_rest, column_class, 1]
                ret = objdbca.table_select(t_menu_other_link, sql_where, sql_bind)
                if ret:
                    # 条件が一致するレコードがある場合は復活処理(カラム表示名のみ更新対象)
                    link_id = ret[0].get('LINK_ID')
                    data = {
                        'LINK_ID': link_id,
                        "COLUMN_DISP_NAME_JA": column_disp_name_ja,
                        "COLUMN_DISP_NAME_EN": column_disp_name_en,
                        'DISUSE_FLAG': "0"
                    }
                    objdbca.table_update(t_menu_other_link, data, "LINK_ID")
                    
                else:
                    # 条件が一致するレコードが無い場合は新規登録
                    data_list = {
                        "MENU_ID": menu_uuid,
                        "COLUMN_DISP_NAME_JA": column_disp_name_ja,
                        "COLUMN_DISP_NAME_EN": column_disp_name_en,
                        "REF_TABLE_NAME": create_table_name,
                        "REF_PKEY_NAME": "ROW_ID",
                        "REF_COL_NAME": "DATA_JSON",
                        "REF_COL_NAME_REST": column_name_rest,
                        "REF_SORT_CONDITIONS": None,
                        "REF_MULTI_LANG": "0",
                        "COLUMN_CLASS": column_class,
                        "MENU_CREATE_FLAG": "1",
                        "DISUSE_FLAG": "0",
                        "LAST_UPDATE_USER": g.get('USER_ID')
                    }
                    primary_key_name = 'LINK_ID'
                    objdbca.table_insert(t_menu_other_link, data_list, primary_key_name)
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _insert_t_menu_reference_item(objdbca, menu_uuid, create_table_name, record_t_menu_column):
    """
        「参照項目情報」メニューのテーブルにレコードを追加する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_uuid: 対象のメニュー（「メニュー管理」のレコード）のUUID
            create_table_name: 作成した対象のテーブル名
            record_t_menu_column: 「メニュー項目作成情報」の対象のレコード一覧
        RETRUN:
            result, msg
    """
    # テーブル名
    t_menu_other_link = 'T_MENU_OTHER_LINK'
    t_menu_reference_item = 'T_MENU_REFERENCE_ITEM'
    
    try:
        # 「他メニュー連携」テーブルで対象のメニューIDのレコードを取得
        ret = objdbca.table_select(t_menu_other_link, 'WHERE MENU_ID = %s AND DISUSE_FLAG = %s', [menu_uuid, 0])  # noqa: E501
        if not ret:
            # 対象が無い場合は登録処理を実施せずにreturn
            return True, None
        
        for other_menu_record in ret:
            other_menu_link_column_name_rest = other_menu_record.get('REF_COL_NAME_REST')
            link_id = other_menu_record.get('LINK_ID')
            disp_seq_num = 10
            for column_record in record_t_menu_column:
                column_name_rest = column_record.get('COLUMN_NAME_REST')
                # 「他メニュー連携」のカラム名(rest)と「メニュー項目作成情報」のカラム名(rest)が同一の場合はスキップ
                if other_menu_link_column_name_rest == column_name_rest:
                    continue
                
                # 参照項目の対象とするカラムクラス一覧(1:SingleTextColumn, 2:MultiTextColumn, 3:NumColumn, 4:FloatColumn, 5:DateTimeColumn, 6:DateColumn, 8:PasswordColumn, 9:FileUploadColumn, 10:HostInsideLinkTextColumn)  # noqa: E501
                target_column_class_list = ["1", "2", "3", "4", "5", "6", "8", "9", "10"]
                column_class = column_record.get('COLUMN_CLASS')
                
                # カラムクラスが参照項目の対象であれば、「参照項目情報」にレコードを登録
                if column_class in target_column_class_list:
                    column_name_ja = column_record.get('COLUMN_NAME_JA')
                    column_name_en = column_record.get('COLUMN_NAME_EN')
                    description_ja = column_record.get('DESCRIPTION_JA')
                    description_en = column_record.get('DESCRIPTION_EN')
                    
                    # パスワードカラムはSENSITIVE_FLAGをTrueにする
                    if str(column_class) == "8":
                        sensitive_flag = "1"  # True
                    else:
                        sensitive_flag = "0"  # False
                    
                    data_list = {
                        "LINK_ID": link_id,
                        "DISP_SEQ": disp_seq_num,
                        "COLUMN_CLASS": column_class,
                        "COLUMN_NAME_JA": column_name_ja,
                        "COLUMN_NAME_EN": column_name_en,
                        "COLUMN_NAME_REST": column_name_rest,
                        "REF_COL_NAME": column_name_rest,
                        "REF_SORT_CONDITIONS": None,
                        "REF_MULTI_LANG": "0",  # False
                        "SENSITIVE_FLAG": sensitive_flag,
                        "DESCRIPTION_JA": description_ja,
                        "DESCRIPTION_EN": description_en,
                        "DISUSE_FLAG": "0",
                        "LAST_UPDATE_USER": g.get('USER_ID')
                    }
                    primary_key_name = 'REFERENCE_ID'
                    objdbca.table_insert(t_menu_reference_item, data_list, primary_key_name)
                    
                    # 表示順序を加算
                    disp_seq_num = int(disp_seq_num) + 10
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _update_t_menu_create_history(objdbca, history_id, status_id):
    """
        「メニュー管理」の対象レコードを更新。対象が無ければレコードを新規登録する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            history_id: 「メニュー作成履歴」対象レコードのUUID
            status_id: ステータスID(1:未実施, 2:実行中, 3:完了, 4:完了(異常))
        RETRUN:
            result, msg, ret_data
    """
    # テーブル名
    t_menu_create_history = 'T_MENU_CREATE_HISTORY'
    try:
        # 「メニュー作成履歴」の対象レコードのステータスを更新
        data_list = {
            "HISTORY_ID": history_id,
            "STATUS_ID": status_id,
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        objdbca.table_update(t_menu_create_history, data_list, 'HISTORY_ID')
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _create_validate_option(record):
    """
        「メニュー-カラム紐付管理」メニューのテーブルにレコードを追加する際のvalidate_optionの値を生成する。
        ARGS:
            record: 「メニュー項目作成情報」のレコード
        RETRUN:
            boolean, msg, validate_option, validate_regular_expression
    """
    try:
        validate_option = None
        validate_regular_expression = None
        tmp_validate_option = {}
        column_class = str(record.get('COLUMN_CLASS'))
        
        # カラムクラスに応じて処理を分岐
        if column_class == "1":  # SingleTextColumn
            single_max_length = record.get('SINGLE_MAX_LENGTH')
            single_regular_expression = str(record.get('SINGLE_REGULAR_EXPRESSION'))
            tmp_validate_option['min_length'] = "0"
            tmp_validate_option['max_length'] = single_max_length
            if single_regular_expression:
                validate_regular_expression = single_regular_expression
            
        elif column_class == "2":  # MultiTextColumn
            multi_max_length = record.get('MULTI_MAX_LENGTH')
            multi_regular_expression = str(record.get('MULTI_REGULAR_EXPRESSION'))
            tmp_validate_option['min_length'] = "0"
            tmp_validate_option['max_length'] = multi_max_length
            if multi_regular_expression:
                validate_regular_expression = multi_regular_expression
            
        elif column_class == "3":  # NumColumn
            num_min = record.get('NUM_MIN')
            num_max = record.get('NUM_MAX')
            if num_min:
                tmp_validate_option["int_min"] = num_min
            if num_max:
                tmp_validate_option["int_max"] = num_max
            
        elif column_class == "4":  # FloatColumn
            float_min = record.get('FLOAT_MIN')
            float_max = record.get('FLOAT_MAX')
            float_digit = record.get('FLOAT_DIGIT')
            if float_min:
                tmp_validate_option["float_min"] = float_min
            if float_max:
                tmp_validate_option["float_max"] = float_max
            if float_digit:
                tmp_validate_option["float_digit"] = float_digit
            else:
                tmp_validate_option["float_digit"] = "14"  # 桁数の指定が無い場合「14」を固定値とする。
            
        elif column_class == "8":  # PasswordColumn
            password_max_length = str(record.get('PASSWORD_MAX_LENGTH'))
            tmp_validate_option['min_length'] = "0"
            tmp_validate_option['max_length'] = password_max_length
        elif column_class == "9":  # FileUploadColumn
            upload_max_size = str(record.get('FILE_UPLOAD_MAX_SIZE'))
            if upload_max_size:
                tmp_validate_option["upload_max_size"] = upload_max_size
            
        elif column_class == "10":  # HostInsideLinkTextColumn
            link_max_length = str(record.get('LINK_MAX_LENGTH'))
            tmp_validate_option['min_length'] = "0"
            tmp_validate_option['max_length'] = link_max_length
        
        # tmp_validate_optionをjson形式に変換
        if tmp_validate_option:
            validate_option = json.dumps(tmp_validate_option)
    
    except Exception as msg:
        return False, msg, None, None
    
    return True, None, validate_option, validate_regular_expression


def _create_initial_value(record):
    """
        「メニュー-カラム紐付管理」メニューのテーブルにレコードを追加する際のinitial_valueの値を生成する。
        ARGS:
            record: 「メニュー項目作成情報」のレコード
        RETRUN:
            boolean, msg, initial_value
    """
    try:
        column_class = str(record.get('COLUMN_CLASS'))
        
        # カラムクラスに応じて処理を分岐
        initial_value = None
        if column_class == "1":  # SingleTextColumn
            initial_value = record.get('SINGLE_DEFAULT_VALUE')
        elif column_class == "2":  # MultiTextColumn
            initial_value = record.get('MULTI_DEFAULT_VALUE')
        elif column_class == "3":  # NumColumn
            initial_value = record.get('NUM_DEFAULT_VALUE')
        elif column_class == "4":  # FloatColumn
            initial_value = record.get('FLOAT_DEFAULT_VALUE')
        elif column_class == "5":  # DateTimeColumn
            initial_value = record.get('DATETIME_DEFAULT_VALUE')
        elif column_class == "6":  # DateColumn
            initial_value = record.get('DATE_DEFAULT_VALUE')
        elif column_class == "7":  # IDColumn
            initial_value = record.get('OTHER_MENU_LINK_DEFAULT_VALUE')
        elif column_class == "10":  # HostInsideLinkTextColumn
            initial_value = record.get('LINK_DEFAULT_VALUE')
        
        # 「空白」の場合もデータベース上にNullを登録させるためNoneを挿入
        if not initial_value:
            initial_value = None
    
    except Exception as msg:
        return False, msg, None
    
    return True, None, initial_value


def _check_column_validation(objdbca, menu_uuid, column_name_rest):
    """
        「メニュー-カラム紐付管理」メニューのテーブルにレコードを追加する際に、「MENU_ID」と「COLUMN_NAME_REST」で同じ組み合わせがあるかどうかのチェックをする。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            menu_uuid: メニュー作成の対象となる「メニュー管理」のレコードのID
            column_name_rest: カラム名(rest)
        RETRUN:
            boolean, msg
    """
    # テーブル名
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'
    
    # 「メニュー-カラム紐付管理」に同じメニューIDとカラム名(rest)のレコードが存在する場合はFalseをreturnする。
    ret = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_NAME_REST = %s AND DISUSE_FLAG = %s', [menu_uuid, column_name_rest, 0])  # noqa: E501
    if ret:
        msg = g.appmsg.get_log_message("BKY-20211", [menu_uuid, column_name_rest])
        return False, msg
    
    return True, None


def _format_column_group_data(record_t_menu_column_group, record_t_menu_column):
    """
        カラムグループ登録の処理に必要な形式(idをkeyにしたdict型)にフォーマット
        ARGS:
            record_t_menu_column_group: 「カラムグループ作成情報」のレコード一覧
            record_t_menu_column: 「メニュー項目作成情報」のレコード一覧
        RETRUN:
            boolesn,
            msg,
            dict_t_menu_column_group,  # 「カラムグループ作成情報」のレコードのidをkeyにしたdict型に整形
            target_column_group_list,  # 使用されているカラムグループIDの親をたどり、最終的に使用されるすべてのカラムグループIDのlist
            
    """
    try:
        # 「カラムグループ作成情報」のレコードのidをkeyにしたdict型に整形
        dict_t_menu_column_group = {}
        for record in record_t_menu_column_group:
            dict_t_menu_column_group[record.get('CREATE_COL_GROUP_ID')] = {
                "pa_col_group_id": record.get('PA_COL_GROUP_ID'),
                "col_group_name_ja": record.get('COL_GROUP_NAME_JA'),
                "col_group_name_en": record.get('COL_GROUP_NAME_EN'),
                "full_col_group_name_ja": record.get('FULL_COL_GROUP_NAME_JA'),
                "full_col_group_name_en": record.get('FULL_COL_GROUP_NAME_EN'),
            }
        
        # 「メニュー項目作成情報」のレコードから、使用されているカラムグループのIDを抽出
        tmp_target_column_group_list = []
        for record in record_t_menu_column:
            target_id = record.get('CREATE_COL_GROUP_ID')
            # 対象のカラムグループIDをlistに追加
            if target_id:
                tmp_target_column_group_list.append(target_id)
        
        # 重複したIDをマージ
        tmp_target_column_group_list = list(dict.fromkeys(tmp_target_column_group_list))
        
        # 使用されているカラムグループIDの親をたどり、最終的に使用されるすべてのカラムグループIDをlistに格納
        target_column_group_list = []
        for column_group_id in tmp_target_column_group_list:
            end_flag = False
            while not end_flag:
                target = dict_t_menu_column_group.get(column_group_id)
                
                # 自分自身のIDをlistの先頭に格納
                target_column_group_list.insert(0, column_group_id)
                if target:
                    pa_col_group_id = target.get('pa_col_group_id')
                else:
                    msg = g.appmsg.get_log_message("BKY-20213", [])
                    raise Exception(msg)
                
                if pa_col_group_id:
                    # 親のIDを対象のIDにしてループ継続
                    column_group_id = pa_col_group_id
                else:
                    # 親が無いためループ終了
                    end_flag = True
        
        # 重複したIDをマージ
        target_column_group_list = list(dict.fromkeys(target_column_group_list))
    
    except Exception as msg:
        return False, msg, None, None
    
    return True, None, dict_t_menu_column_group, target_column_group_list


def _format_other_link(record_t_menu_other_link):
    """
        「他メニュー連携」を利用する処理に必要な形式(idをkeyにしたdict型)にフォーマット
        ARGS:
            record_t_menu_column_group: 「カラムグループ作成情報」のレコード一覧
            record_t_menu_column: 「メニュー項目作成情報」のレコード一覧
        RETRUN:
            boolean,
            msg,
            dict_t_menu_other_link,  # 「他メニュー連携」のレコードのidをkeyにしたdict型に整形
            
    """
    try:
        # 「カラムグループ作成情報」のレコードのidをkeyにしたdict型に整形
        dict_t_menu_other_link = {}
        for record in record_t_menu_other_link:
            dict_t_menu_other_link[record.get('LINK_ID')] = record
    
    except Exception as msg:
        return False, msg, None
    
    return True, None, dict_t_menu_other_link


def _disuse_menu_create_record(objdbca, record_t_menu_define):
    """
        「初期化」「編集」実行時に、対象のメニューに関連するレコードを廃止する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            record_t_menu_define: 「メニュー定義一覧」の対象のレコード
        RETRUN:
            result, msg
            
    """
    # テーブル名
    t_comn_menu = 'T_COMN_MENU'
    t_comn_role_menu_link = 'T_COMN_ROLE_MENU_LINK'
    t_comn_menu_table_link = 'T_COMN_MENU_TABLE_LINK'
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'
    t_menu_table_link = 'T_MENU_TABLE_LINK'
    t_menu_other_link = 'T_MENU_OTHER_LINK'
    t_menu_reference_item = 'T_MENU_REFERENCE_ITEM'
    v_menu_reference_item = 'V_MENU_REFERENCE_ITEM'
    
    try:
        # 対象の「メニュー定義一覧」のメニュー名(rest)を取得
        menu_name_rest = record_t_menu_define.get('MENU_NAME_REST')
        menu_name_rest_subst = menu_name_rest + '_subst'
        menu_name_rest_ref = menu_name_rest + '_ref'
        menu_name_rest_list = [menu_name_rest, menu_name_rest_subst, menu_name_rest_ref]
        
        # 「メニュー管理」から対象のレコードを特定し、listに格納
        target_menu_id_list = []
        for name in menu_name_rest_list:
            ret = objdbca.table_select(t_comn_menu, 'WHERE MENU_NAME_REST = %s AND DISUSE_FLAG = %s', [name, 0])
            if ret:
                target_menu_id_list.append(ret[0].get('MENU_ID'))
        
        # 対象のメニューIDに紐づいたレコードを廃止
        for menu_id in target_menu_id_list:
            # 「ロール-メニュー紐付管理」にて対象のレコードを廃止
            data = {
                'MENU_ID': menu_id,
                'DISUSE_FLAG': "1"
            }
            objdbca.table_update(t_comn_role_menu_link, data, "MENU_ID")
            
            # 「メニュー-テーブル紐付管理」にて対象のレコードを廃止
            data = {
                'MENU_ID': menu_id,
                'DISUSE_FLAG': "1"
            }
            objdbca.table_update(t_comn_menu_table_link, data, "MENU_ID")
            
            # 「メニュー-カラム紐付管理」にて対象のレコードを廃止
            data = {
                'MENU_ID': menu_id,
                'DISUSE_FLAG': "1"
            }
            objdbca.table_update(t_comn_menu_column_link, data, "MENU_ID")
            
            # 「メニュー定義-テーブル紐付管理」にて対象のレコードを廃止
            data = {
                'MENU_ID': menu_id,
                'DISUSE_FLAG': "1"
            }
            objdbca.table_update(t_menu_table_link, data, "MENU_ID")
            
            # 「参照項目」にて対象のレコードを廃止
            # 廃止レコードのUUIDを特定するため、VIEWから対象レコードを取得
            ret = objdbca.table_select(v_menu_reference_item, 'WHERE MENU_ID = %s AND DISUSE_FLAG = %s', [menu_id, 0])
            if ret:
                for record in ret:
                    reference_id = record.get('REFERENCE_ID')
                    data = {
                        'REFERENCE_ID': reference_id,
                        'DISUSE_FLAG': "1"
                    }
                    objdbca.table_update(t_menu_reference_item, data, "REFERENCE_ID")
            
            # 「他メニュー連携」にて対象のレコードを廃止
            data = {
                'MENU_ID': menu_id,
                'DISUSE_FLAG': "1"
            }
            objdbca.table_update(t_menu_other_link, data, "MENU_ID")
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _disuse_t_comn_menu(objdbca, record_t_menu_define, target_menu_group_list):
    """
        利用していないメニューグループのメニューを廃止する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            record_t_menu_define: 「メニュー定義一覧」の対象のレコード
            target_menu_group_list: 対象メニューグループのカラム名一覧
        RETRUN:
            result, msg
            
    """
    # テーブル名
    t_comn_menu = 'T_COMN_MENU'
    
    try:
        # メニュー名(rest)は対象メニューグループが「代入値自動登録」「参照用」の場合は末尾に_subst, _refを結合する。
        menu_name_rest = record_t_menu_define.get('MENU_NAME_REST')
        menu_name_rest_subst = menu_name_rest + "_subst"
        menu_name_rest_ref = menu_name_rest + "_ref"
        target_menu_name_rest_list = [menu_name_rest, menu_name_rest_subst, menu_name_rest_ref]
        
        # 「メニュー定義一覧」の対象メニューグループ
        menu_group_id_input = record_t_menu_define.get('MENU_GROUP_ID_INPUT')
        menu_group_id_subst = record_t_menu_define.get('MENU_GROUP_ID_SUBST')
        menu_group_id_ref = record_t_menu_define.get('MENU_GROUP_ID_REF')
        target_menu_group_id_list = [menu_group_id_input, menu_group_id_subst, menu_group_id_ref]
        
        # 「メニュー管理」から対象のメニュー名(rest)のレコードを取得
        ret = objdbca.table_select(t_comn_menu, 'WHERE MENU_NAME_REST IN (%s, %s, %s) AND DISUSE_FLAG = %s', [menu_name_rest, menu_name_rest_subst, menu_name_rest_ref, 0])  # noqa: E501
        for record in ret:
            # 対象のメニュー名(rest)および対象メニューグループが一致するかをチェック
            c_menu_group_id = record.get('MENU_GROUP_ID')
            c_menu_name_rest = record.get('MENU_NAME_REST')
            if (c_menu_name_rest in target_menu_name_rest_list) and (c_menu_group_id in target_menu_group_id_list):
                continue
            else:
                # 一致が無い場合、利用しないメニューであるためレコードを廃止する
                menu_id = record.get('MENU_ID')
                data = {
                    'MENU_ID': menu_id,
                    'DISUSE_FLAG': "1"
                }
                objdbca.table_update(t_comn_menu, data, "MENU_ID")
        
    except Exception as msg:
        return False, msg
    
    return True, None


def _check_file_upload_column(record_t_menu_column):
    """
        作成する項目がファイルアップロードカラムのみの場合Trueを返却
        ARGS:
            record_t_menu_column: 「メニュー項目作成情報」の対象のレコード一覧
        RETRUN:
            boolean
            
    """
    file_upload_only_flag = False
    
    # カラムクラスが「9: ファイルアップロード」のみの場合、flagをTrueにする。
    for record in record_t_menu_column:
        column_class_id = str(record.get('COLUMN_CLASS'))
        if not column_class_id == "9":
            file_upload_only_flag = False
            break
        
        file_upload_only_flag = True
        
    return file_upload_only_flag
