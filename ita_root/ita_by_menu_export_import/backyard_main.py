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
import base64
import datetime
import tarfile
import mimetypes
import secrets
from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.common.exception import AppException  # noqa: F401
from pathlib import Path
import shutil
import subprocess

def backyard_main(organization_id, workspace_id):
    """
        メニュー作成機能backyardメイン処理
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETURN:

    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メイン処理開始
    debug_msg = g.appmsg.get_log_message("BKY-20001", [])
    g.applogger.debug(debug_msg)

    strage_path = os.environ.get('STORAGEPATH')
    export_menu_dir = strage_path + "/".join([organization_id, workspace_id]) + "/tmp/driver/export_menu"
    import_menu_dir = strage_path + "/".join([organization_id, workspace_id]) + "/tmp/driver/import_menu"
    uploadfiles_dir = strage_path + "/".join([organization_id, workspace_id]) + "/uploadfiles/60103"
    if not os.path.isdir(uploadfiles_dir):
        os.makedirs(uploadfiles_dir)
        g.applogger.debug("made uploadfiles/60103")

    # テーブル名
    t_menu_export_import = 'T_MENU_EXPORT_IMPORT'  # メニューエクスポート・インポート管理

    # 「メニューエクスポート・インポート管理」から「未実行(ID:1)」のレコードを取得(最終更新日時の古い順から処理)
    ret = objdbca.table_select(t_menu_export_import, 'WHERE STATUS = %s AND DISUSE_FLAG = %s ORDER BY LAST_UPDATE_TIMESTAMP ASC', [1, 0])

    # 0件なら処理を終了
    if not ret:
        debug_msg = g.appmsg.get_log_message("BKY-20003", [])
        g.applogger.debug(debug_msg)

        debug_msg = g.appmsg.get_log_message("BKY-20002", [])
        g.applogger.debug(debug_msg)
        return

    for record in ret:
        execution_no = str(record.get('EXECUTION_NO'))
        execution_type = str(record.get('EXECUTION_TYPE'))

        # 「メニューエクスポート・インポート管理」ステータスを「2:実行中」に更新
        objdbca.db_transaction_start()
        status = "2"
        result, msg = _update_t_menu_export_import(objdbca, execution_no, status)
        if not result:
            # エラーログ出力
            g.applogger.error(msg)
            continue
        objdbca.db_transaction_end(True)

        # トランザクション開始
        debug_msg = g.appmsg.get_log_message("BKY-20004", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_start()

        # execution_typeに応じたエクスポート/インポート処理を実行(メイン処理)
        if execution_type == "1":  # 1: エクスポート
            main_func_result, msg = menu_export_exec(objdbca, record, export_menu_dir)
        elif execution_type == "2":  # 1: インポート
            main_func_result, msg = menu_import_exec(objdbca, record, import_menu_dir, uploadfiles_dir)

        # メイン処理がFalseの場合、異常系処理
        if not main_func_result:
            # エラーログ出力
            g.applogger.error(msg)

            # ロールバック/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20006", [])
            g.applogger.debug(debug_msg)
            objdbca.db_transaction_end(False)

            # 「メニューエクスポート・インポート管理」ステータスを「4:完了(異常)」に更新
            objdbca.db_transaction_start()
            status = 4
            result, msg = _update_t_menu_export_import(objdbca, execution_no, status)
            if not result:
                # エラーログ出力
                g.applogger.error(msg)
                continue
            objdbca.db_transaction_end(True)

            continue

        # コミット/トランザクション終了
        debug_msg = g.appmsg.get_log_message("BKY-20005", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_end(True)

        # 「メニューエクスポート・インポート管理」ステータスを「3:完了」に更新
        objdbca.db_transaction_start()
        status = 3
        result, msg = _update_t_menu_export_import(objdbca, execution_no, status)
        if not result:
            # エラーログ出力
            g.applogger.error(msg)
            continue
        objdbca.db_transaction_end(True)

    # メイン処理終了
    debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    g.applogger.debug(debug_msg)
    return

def menu_import_exec(objdbca, record, import_menu_dir, uploadfiles_dir):
    msg = None
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    try:
        execution_no = str(record.get('EXECUTION_NO'))
        file_name = str(record.get('FILE_NAME'))

        execution_no_path = uploadfiles_dir + '/file_name/' + execution_no

        file_path = execution_no_path + '/' + file_name

        if os.path.isfile(file_path) is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])

        # zip解凍
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.extractall(path=execution_no_path)

        if os.path.isfile(execution_no_path + '/MENU_NAME_REST_LIST') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])

        # MENU_NAME_REST_LISTファイル読み込み
        menu_name_rest_list = Path(execution_no_path + '/MENU_NAME_REST_LIST').read_text(encoding='utf-8').split(',')

        for menu_name_rest in menu_name_rest_list:
            # テーブルが存在するか確認する
            # 対象のDBのテーブル定義を出力（sqldump
            menu_id_sql = " SELECT MENU_ID, MENU_NAME_REST  FROM `T_COMN_MENU` WHERE `DISUSE_FLAG` <> 1 AND `MENU_NAME_REST` = %s "
            t_comn_menu_record = objdbca.sql_execute(menu_id_sql, [menu_name_rest])

            # テーブルが存在しない場合は作成する
            if len(t_comn_menu_record) == 0:
                # T_COMN_MENU_DATAからデータを取得して登録する
                objmenu = load_table.loadTable(objdbca, 'menu_list')   # noqa: F405
                # T_COMN_MENU_DATAファイル読み込み
                t_comn_menu_data = Path(execution_no_path + '/T_COMN_MENU_DATA').read_text(encoding='utf-8')
                t_comn_menu_data_json = json.loads(t_comn_menu_data)

                for record in t_comn_menu_data_json:
                    param = record['parameter']
                    tmp_menu_name_rest = param.get('menu_name_rest')
                    if tmp_menu_name_rest == menu_name_rest:
                        # 該当レコードをT_COMN_MENUに登録
                        tmp_menu_id = param.get('menu_id')
                        # 登録用パラメータを作成
                        file_param = record['file']
                        # 登録用パラメータを作成
                        parameters = {
                            "file": {
                                "file_name": file_param
                            },
                            "parameter": param,
                            "type": "Register"
                        }

                        # 登録を実行
                        exec_result = objmenu.exec_maintenance(parameters, tmp_menu_id, "", False, False, True, False, True)  # noqa: E999
                        if not exec_result[0]:
                            result_msg = _format_loadtable_msg(exec_result[2])
                            result_msg = json.dumps(result_msg, ensure_ascii=False)
                            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

                # 該当レコードをT_COMN_MENU_TABLE_LINKに登録
                # MENU_ID_TABLE_LISTファイル読み込み
                menu_id_table_list = Path(execution_no_path + '/MENU_ID_TABLE_LIST').read_text(encoding='utf-8')
                for menu_id_table in menu_id_table_list:
                    menu_id = menu_id_table.get('MENU_ID')
                    if tmp_menu_id == menu_id:
                        table_name = menu_id_table.get('TABLE_NAME')

                        # DBデータファイル読み込み
                        db_data_path = execution_no_path + '/' + table_name + '.sql'
                        db_data = Path(execution_no_path + '/' + table_name + '.sql').read_text(encoding='utf-8')
                        idx = db_data.find("CREATE TABLE")
                        create_table_str = db_data[idx:]
                        print(create_table_str)
                        # テーブルを作成
                        objdbca.sqlfile_execute(db_data_path)

                        # 該当レコードを作成したテーブルに登録
            else:
                menu_id = t_comn_menu_record[0].get('MENU_ID')
                table_name_sql = " SELECT TABLE_NAME FROM `T_COMN_MENU_TABLE_LINK` WHERE `DISUSE_FLAG` <> 1 AND `MENU_ID` = %s "
                t_comn_menu_table_link_record = objdbca.sql_execute(table_name_sql, [menu_id])
                table_name = t_comn_menu_table_link_record[0].get('TABLE_NAME')

                # DATAファイル読み込み
                if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
                    # 対象ファイルなし
                    raise AppException("499-00905", [], [])

                # DATAファイル読み込み
                sql_data = Path(execution_no_path + '/' + menu_name_rest).read_text(encoding='utf-8')
                json_sql_data = json.loads(sql_data)

                # データを登録する
                objmenu = load_table.loadTable(objdbca, menu_name_rest)   # noqa: F405
                pk = objmenu.get_primary_key()

                pass_column = ["8", "25", "26"]
                pass_column_list = []
                ret_pass_column = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_CLASS IN %s', [menu_id, pass_column])  # noqa: E501
                if len(ret_pass_column) != 0:
                    for record in ret_pass_column:
                        pass_col_name_rest = record['COLUMN_NAME_REST']
                        pass_column_list.append(pass_col_name_rest)

                for json_record in json_sql_data:
                    file_param = json_record['file']
                    param = json_record['parameter']

                    # 移行先に主キーの重複データが既に存在するか確認
                    param_type = "Register"
                    ret_t_comn_menu_column_link = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COL_NAME = %s', [menu_id, pk])  # noqa: E501
                    pk_name = ret_t_comn_menu_column_link[0].get('COLUMN_NAME_REST')

                    pk_value = param[pk_name]
                    chk_pk_sql = " SELECT * FROM `" + table_name + "` WHERE `" + pk + "` = '" + pk_value + "'"
                    chk_pk_record = objdbca.sql_execute(chk_pk_sql, [])
                    if len(chk_pk_record) != 0:
                        # 主キーが重複する場合は更新で上書きする
                        param_type = "Update"

                    # PasswordColumnかを判定
                    for k, v in param.items():
                        if k in pass_column_list:
                            if v is not None:
                                v = ky_encrypt(v)
                                param[k] = v

                    # 登録用パラメータを作成
                    parameters = {
                        "file": {
                            "file_name": file_param
                        },
                        "parameter": param,
                        "type": param_type
                    }

                    # import_mode=Trueで登録を実行
                    exec_result = objmenu.exec_maintenance(parameters, pk_value, "", False, False, True, False, True)  # noqa: E999
                    if not exec_result[0]:
                        result_msg = _format_loadtable_msg(exec_result[2])
                        result_msg = json.dumps(result_msg, ensure_ascii=False)
                        raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

        # 正常系リターン
        return True, msg

    except Exception as msg:
        # エラー時はtmpの作業ファイルを削除する
        # shutil.rmtree(import_menu_dir)

        # 異常系リターン
        return False, msg

def menu_export_exec(objdbca, record, export_menu_dir):  # noqa: C901
    """
        メニューエクスポート実行
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            record: メニューエクスポートの対象となる「メニューエクスポート・インポート管理」のレコード
            export_menu_dir: export_menuディレクトリのパス
        RETURN:
            boolean, msg
    """
    msg = None

    try:
        execution_no = str(record.get('EXECUTION_NO'))
        json_storage_item = json.loads(str(record.get('JSON_STORAGE_ITEM')))
        mode = json_storage_item.get('mode')
        abolished_type = json_storage_item.get('abolished_type')
        specified_time = json_storage_item.get('specified_time')

        # 対象のDBの存在チェック
        menu_list = json_storage_item["menu"]
        for menu in menu_list:
            # メニューの存在確認
            _check_menu_info(menu, objdbca)

        dir_name = 'ita_exportdata_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        dir_path = export_menu_dir + '/' + dir_name
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
            g.applogger.debug("made export_dir")

        # 更新系テーブル取得
        filter_parameter = {}
        if mode == '1' and abolished_type == '1':
            # 環境移行/廃止を含む
            filter_parameter = {}
        elif mode == '1' and abolished_type == '2':
            # 環境移行/廃止を含まない
            filter_parameter = {"discard": {"LIST": ["0"]}}
        elif mode == '2' and abolished_type == '1':
            # 時刻指定/廃止を含む
            filter_parameter = {"LAST_UPDATE_TIMESTAMP": {"LIST": [specified_time]}}
        elif mode == '2' and abolished_type == '2':
            # 時刻指定/廃止を含まない
            filter_parameter = {"discard": {"LIST": ["0"]}, "LAST_UPDATE_TIMESTAMP": {"LIST": [specified_time]}}

        filter_mode = 'export'
        for menu in menu_list:
            DB_path = dir_path + '/' + menu
            objmenu = load_table.loadTable(objdbca, menu)   # noqa: F405
            status_code, result, msg = objmenu.rest_filter(filter_parameter, filter_mode)
            if status_code != '000-00000':
                log_msg_args = [msg]
                api_msg_args = [msg]
                raise AppException(status_code, log_msg_args, api_msg_args)

            with open(DB_path, 'w') as f:
                json.dump(result, f, ensure_ascii=False)

        # 対象のDBのテーブル定義を出力（sqldump用
        menu_id_sql = " SELECT * FROM `T_COMN_MENU` WHERE `DISUSE_FLAG` <> 1 AND `MENU_NAME_REST` IN %s "
        t_comn_menu_record = objdbca.sql_execute(menu_id_sql, [menu_list])
        menu_id_dict = {}
        menu_id_list = []
        for record in t_comn_menu_record:
            menu_id = record.get('MENU_ID')
            menu_name_rest = record.get('MENU_NAME_REST')
            menu_id_list.append(menu_id)
            menu_id_dict[menu_id] = menu_name_rest

        table_name_sql = " SELECT * FROM `T_COMN_MENU_TABLE_LINK` WHERE `DISUSE_FLAG` <> 1 AND `MENU_ID` IN %s "
        t_comn_menu_table_link_record = objdbca.sql_execute(table_name_sql, [menu_id_list])
        table_name_list = []
        for record in t_comn_menu_table_link_record:
            table_name = record.get('TABLE_NAME')
            table_name_list.append(table_name)
            view_name = record.get('VIEW_NAME')
            if view_name is not None:
                table_name_list.append(view_name)
            history_table_flag = record.get('HISTORY_TABLE_FLAG')
            if history_table_flag == '1':
                table_name_list.append(table_name + '_JNL')

        db_user = os.environ.get('DB_ADMIN_USER')
        db_password = os.environ.get('DB_ADMIN_PASSWORD')
        db_host = os.environ.get('DB_HOST')
        db_database = objdbca._db

        for table_name in table_name_list:
            sqldump_path = dir_path + '/' + table_name + '.sql'
            sqldump_sql = 'mysqldump --single-transaction --opt '
            sqldump_sql += '-u ' + db_user + ' '
            sqldump_sql += '-p' + db_password + ' '
            sqldump_sql += '-h ' + db_host + ' '
            sqldump_sql += db_database + ' '
            # 定義のみdumpするオプション
            sqldump_sql += '--no-data' + ' '
            sqldump_sql += table_name

            sp_sqldump = subprocess.run(sqldump_sql, capture_output=True, text=True, shell=True).stdout
            with open(sqldump_path, 'w', encoding='utf-8') as f:
                f.write(sp_sqldump)

        # インポート時に利用するMENU_NAME_REST_LISTを作成する
        menu_name_rest_list = ",".join(menu_list)
        menu_name_rest_path = dir_path + '/' + 'MENU_NAME_REST_LIST'
        with open(menu_name_rest_path, "w") as f:
            f.write(menu_name_rest_list)

        # インポート時に利用するT_COMN_MENU_DATAを作成する
        t_comn_menu_data_path = dir_path + '/T_COMN_MENU_DATA'
        objmenu = load_table.loadTable(objdbca, 'menu_list')   # noqa: F405
        filter_parameter = {"discard": {"LIST": ["0"]}, "menu_name_rest": {"LIST": menu_list}}
        status_code, result, msg = objmenu.rest_filter(filter_parameter, filter_mode)
        if status_code != '000-00000':
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException(status_code, log_msg_args, api_msg_args)
        with open(t_comn_menu_data_path, 'w') as f:
            json.dump(result, f, ensure_ascii=False)

        # インポート時に利用するMENU_ID_TABLE_LISTを作成する
        menu_id_table_list_path = dir_path + '/MENU_ID_TABLE_LIST'
        objmenu = load_table.loadTable(objdbca, 'menu_table_link_list')   # noqa: F405
        filter_parameter = {"discard": {"LIST": ["0"]}, "menu_id": {"LIST": [menu_id_list]}}
        status_code, result, msg = objmenu.rest_filter(filter_parameter, filter_mode)
        if status_code != '000-00000':
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException(status_code, log_msg_args, api_msg_args)
        with open(menu_id_table_list_path, 'w') as f:
            json.dump(result, f, ensure_ascii=False)

        # アップロード時に利用するDP_INFOファイルを作成する
        dp_info = {
            "DP_MODE": mode,
            "ABOLISHED_TYPE": abolished_type,
            "SPECIFIED_TIMESTAMP": specified_time
        }
        dp_info_path = dir_path + '/' + 'DP_INFO'
        with open(dp_info_path, "w") as f:
            json.dump(dp_info, f)

        # データをtar.gzにまとめる
        gztar_path = shutil.make_archive(base_name=dir_path, format="gztar", root_dir=dir_path)

        # kymファイルに変換(拡張子変更)
        kym_name = dir_name + '.kym'
        kym_path = export_menu_dir + '/' + kym_name
        shutil.move(gztar_path, kym_path)

        # tmpに作成したデータは削除する
        shutil.rmtree(dir_path)

        # 対象レコードの最終更新日時を取得
        export_import_sql = " SELECT * FROM `T_MENU_EXPORT_IMPORT` WHERE `DISUSE_FLAG` <> 1 AND `EXECUTION_NO` = %s "
        t_menu_export_import_record = objdbca.sql_execute(export_import_sql, [execution_no])
        for record in t_menu_export_import_record:
            last_update_taimestamp = record.get('LAST_UPDATE_TIMESTAMP')

        # ファイル名更新用パラメータを作成
        parameters = {
            "file": {
                "file_name": file_encode(kym_path)
            },
            "parameter": {
                "file_name": kym_name,
                "last_update_date_time": last_update_taimestamp.strftime('%Y/%m/%d %H:%M:%S.%f'),
            },
            "type": "Update"
        }

        # 「メニューエクスポート・インポート管理」のファイル名を更新
        objmenu = load_table.loadTable(objdbca, 'menu_export_import_list')
        exec_result = objmenu.exec_maintenance(parameters, execution_no, "", False, False, True)  # noqa: E999
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

        # 更新が正常に終了したらtmpの作業ファイルを削除する
        os.remove(kym_path)

        # 正常系リターン
        return True, msg

    except Exception as msg:
        # エラー時はtmpの作業ファイルを削除する
        shutil.rmtree(export_menu_dir)

        # 異常系リターン
        return False, msg

def _update_t_menu_export_import(objdbca, execution_no, status):
    """
        「メニューエクスポート・インポート管理」の対象レコードを更新。対象が無ければレコードを新規登録する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            execution_no: 「メニューエクスポート・インポート管理」対象レコードのUUID
            status: ステータスID(1:未実行, 2:実行中, 3:完了, 4:完了(異常))
        RETURN:
            result, msg, ret_data
    """
    # テーブル名
    t_menu_export_import = 'T_MENU_EXPORT_IMPORT'
    try:
        # 「メニューエクスポート・インポート管理」の対象レコードのステータスを更新
        data_list = {
            "EXECUTION_NO": execution_no,
            "STATUS": status,
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        objdbca.table_update(t_menu_export_import, data_list, 'EXECUTION_NO')

    except Exception as msg:
        return False, msg

    return True, None

def _format_loadtable_msg(loadtable_msg):
    """
        【内部呼び出し用】loadTableから受け取ったバリデーションエラーメッセージをフォーマットする
        ARGS:
            loadtable_msg: loadTableから返却されたメッセージ(dict)
        RETURN:
            format_msg
    """
    result_msg = {}
    for key, value_list in loadtable_msg.items():
        msg_list = []
        for value in value_list:
            msg_list.append(value.get('msg'))
        result_msg[key] = msg_list

    return result_msg

def _check_menu_info(menu, wsdb_istc=None):
    """
    check_menu_info

    Arguments:
        menu: menu_name_rest
        wsdb_istc: (class)DBConnectWs Instance
    return:
        (dict)T_COMN_MENUの該当レコード
    """
    if not wsdb_istc:
        wsdb_istc = DBConnectWs(g.get('WORKSPACE_ID'))  # noqa: F405

    menu_record = wsdb_istc.table_select('T_COMN_MENU', 'WHERE `MENU_NAME_REST` = %s AND `DISUSE_FLAG` = %s', [menu, 0])
    if not menu_record:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00002", log_msg_args, api_msg_args)  # noqa: F405

    return menu_record
