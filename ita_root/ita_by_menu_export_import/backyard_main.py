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
import os
import datetime
import tarfile
from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.storage_access import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.column import *  # noqa: F403
from pathlib import Path
import shutil
import subprocess
import time
import inspect
import re
import traceback


def backyard_main(organization_id, workspace_id):
    g.applogger.debug("backyard_main ita_by_menu_export_import called")

    """
        メニュー作成機能backyardメイン処理
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETURN:

    """
    # DB接続
    tmp_msg = 'db connect'
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メイン処理開始
    debug_msg = g.appmsg.get_log_message("BKY-20001", [])
    g.applogger.debug(debug_msg)

    # メンテナンスモードのチェック
    try:
        maintenance_mode = get_maintenance_mode_setting()
        # data_update_stopの値が"1"の場合、メンテナンス中のためreturnする。
        if str(maintenance_mode['data_update_stop']) == "1":
            g.applogger.debug(g.appmsg.get_log_message("BKY-00005", []))
            return
    except Exception:
        # エラーログ出力
        g.applogger.error(g.appmsg.get_log_message("BKY-00008", []))
        return

    strage_path = os.environ.get('STORAGEPATH')
    workspace_path = strage_path + "/".join([organization_id, workspace_id])
    tmp_workspace_path = "/tmp/" + "/".join([organization_id, workspace_id])
    export_menu_dir = workspace_path + "/tmp/driver/export_menu"
    import_menu_dir = workspace_path + "/tmp/driver/import_menu"
    uploadfiles_dir = workspace_path + "/uploadfiles"
    uploadfiles_60103_dir = workspace_path + "/uploadfiles/60103"
    if not os.path.isdir(uploadfiles_60103_dir):
        os.makedirs(uploadfiles_60103_dir)
        g.applogger.debug("made uploadfiles/60103")

    # 一時使用領域(/tmp/<organization_id>/<workspace_id>配下)の初期化
    if os.path.isdir(tmp_workspace_path):
        g.applogger.debug(f"clear {tmp_workspace_path}")
        shutil.rmtree(tmp_workspace_path)
        os.makedirs(tmp_workspace_path)

    # テーブル名
    t_menu_export_import = 'T_MENU_EXPORT_IMPORT'  # メニューエクスポート・インポート管理

    # 「メニューエクスポート・インポート管理」から「実行中(ID:2)」のレコードを取得
    ret = objdbca.table_select(t_menu_export_import, 'WHERE STATUS = %s AND DISUSE_FLAG = %s ORDER BY LAST_UPDATE_TIMESTAMP ASC', [2, 0])

    # ステータス「実行中」の対象がある場合、なんらかの原因で「実行中」のまま止まってしまった対象であるため、「4:完了(異常)」に更新する。
    for record in ret:
        execution_no = str(record.get('EXECUTION_NO'))
        execution_type = str(record.get('EXECUTION_TYPE'))

        # バックアップファイルが存在する場合はリストア処理を実行する
        restoreTables(objdbca, workspace_path)
        restoreFiles(workspace_path, uploadfiles_dir)

        # 「メニューエクスポート・インポート管理」ステータスを「4:完了(異常)」に更新
        objdbca.db_transaction_start()

        status_id = "4"
        user_language = record.get('LANGUAGE')
        execute_log = record.get('EXECUTE_LOG')
        if not execute_log:
            log_prefix = "export" if execution_type == "1" else "import"
            execute_log = f"{log_prefix}_{execution_no}.log"
            g.appmsg.set_lang(user_language)
            type_name = "Export" if execution_type == "1" else "Import"
            msg = g.appmsg.get_api_message("MSG-140011", [type_name])
            g.appmsg.set_lang(g.LANGUAGE)
        result, msg = _update_t_menu_export_import(objdbca, execution_no, status_id, user_language, execute_log, msg)
        if not result:
            # エラーログ出力
            g.applogger.error(msg)
            continue
        objdbca.db_transaction_end(True)

    # backyard_execute_stopの値が"1"の場合、メンテナンス中のためreturnする。
    if str(maintenance_mode['backyard_execute_stop']) == "1":
        g.applogger.debug(g.appmsg.get_log_message("BKY-00006", []))
        return

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

        # execution_typeに応じたエクスポート/インポート処理を実行(メイン処理)
        if execution_type == "1":  # 1: エクスポート
            g.applogger.info("menu_export_exec START")
            main_func_result, msg, trace_msg = menu_export_exec(objdbca, record, workspace_id, export_menu_dir, uploadfiles_dir)
            g.applogger.info("menu_export_exec END")
        elif execution_type == "2":  # 2: インポート
            g.applogger.info("menu_import_exec START")
            main_func_result, msg, trace_msg = menu_import_exec(objdbca, record, workspace_id, workspace_path, uploadfiles_dir, uploadfiles_60103_dir)
            g.applogger.info("menu_import_exec END")
        # メイン処理がFalseの場合、異常系処理
        if not main_func_result:
            # エラーログ出力
            g.applogger.error(msg)

            # 「メニューエクスポート・インポート管理」ステータスを「4:完了(異常)」に更新
            objdbca.db_transaction_start()
            status = 4
            user_language = record.get('LANGUAGE')
            execute_log = record.get('EXECUTE_LOG')
            if not execute_log:
                log_prefix = "export" if execution_type == "1" else "import"
                execute_log = f"{log_prefix}_{execution_no}.log"
            result, msg = _update_t_menu_export_import(objdbca, execution_no, status, user_language, execute_log, msg, trace_msg)
            if not result:
                # エラーログ出力
                g.applogger.error(msg)
                continue
            objdbca.db_transaction_end(True)

            continue

        # 「メニューエクスポート・インポート管理」ステータスを「3:完了」に更新
        objdbca.db_transaction_start()
        status = 3
        result, msg = _update_t_menu_export_import(objdbca, execution_no, status)
        if not result:
            # エラーログ出力
            g.applogger.error(msg)
            continue
        objdbca.db_transaction_end(True)

    # 一時使用領域(/tmp/<organization_id>/<workspace_id>配下)の初期化
    if os.path.isdir(tmp_workspace_path):
        g.applogger.debug(f"clear {tmp_workspace_path}")
        shutil.rmtree(tmp_workspace_path)
        os.makedirs(tmp_workspace_path)

    # メイン処理終了
    debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    g.applogger.debug(debug_msg)
    return


def menu_import_exec(objdbca, record, workspace_id, workspace_path, uploadfiles_dir, uploadfiles_60103_dir):
    msg = None
    rpt = RecordProcessingTimes()
    try:
        # サービススキップファイルを配置する
        f = Path(workspace_path + '/tmp/driver/import_menu/skip_all_service')
        f.touch()
        time.sleep(int(os.environ.get("EXECUTE_INTERVAL", 10)))


        execution_no = str(record.get('EXECUTION_NO'))
        file_name = str(record.get('FILE_NAME'))
        dp_mode = str(record.get('MODE'))
        json_storage_item = str(record.get('JSON_STORAGE_ITEM'))

        tmp_msg = "Target record data: {}, {}, {}, {}".format(execution_no, file_name, dp_mode, json_storage_item)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # KYMファイル
        ori_execution_no_path = uploadfiles_60103_dir + '/file_name/' + execution_no
        ori_file_path = ori_execution_no_path + '/' + file_name
        if os.path.isfile(ori_file_path) is False:
            # 対象ファイルなし
            raise AppException("MSG-140001", [file_name], [file_name])

        # 一時作業用: /tmp/<execution_no>
        execution_no_path = '/tmp/' + execution_no
        tmp_file_path = execution_no_path + '/' + file_name
        if not os.path.isdir(execution_no_path):
            os.makedirs(execution_no_path)

        # KYMファイルを一時作業用へコピー
        file_path = shutil.copyfile(ori_file_path, tmp_file_path)
        if os.path.isfile(tmp_file_path) is False:
            # 対象ファイルなし
            raise AppException("MSG-140002", [file_name], [file_name])

        # zip解凍
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.extractall(path=execution_no_path)

        if os.path.isfile(execution_no_path + '/T_COMN_MENU_TABLE_LINK_DATA') is False:
            # 対象ファイルなし
            _file_name = 'T_COMN_MENU_TABLE_LINK_DATA'
            raise AppException("MSG-140003", [_file_name], [_file_name])

        if os.path.isfile(execution_no_path + '/T_COMN_MENU_DATA') is False:
            # 対象ファイルなし
            _file_name = 'T_COMN_MENU_DATA'
            raise AppException("MSG-140003", [_file_name], [_file_name])

        if os.path.isfile(execution_no_path + '/MENU_NAME_REST_LIST') is False:
            # 対象ファイルなし
            _file_name = 'T_COMN_MENU_DATA'
            raise AppException("MSG-140003", [_file_name], [_file_name])
        # インポート対象メニュー取得
        menu_name_rest_list = json_storage_item.split(',')

        backupsql_dir = workspace_path + "/tmp/driver/import_menu/backup"
        backupsql_path = backupsql_dir + '/backup.sql'
        if not os.path.isdir(backupsql_dir):
            os.makedirs(backupsql_dir)
            g.applogger.debug("made backup_dir")
        menu_id_list = backup_table(objdbca, backupsql_path, menu_name_rest_list)

        backupfile_dir = workspace_path + "/tmp/driver/import_menu/uploadfiles"
        if not os.path.isdir(backupfile_dir):
            os.makedirs(backupfile_dir)
            g.applogger.debug("made backupfile_dir")
        fileBackup(backupfile_dir, uploadfiles_dir, menu_id_list)

        if dp_mode == '1':
            for menu_id in menu_id_list:
                menu_dir = uploadfiles_dir + '/' + menu_id
                # ディレクトリ存在チェック
                if os.path.isdir(menu_dir) is True:
                    shutil.rmtree(menu_dir)

        # 環境移行にて削除したテーブル名を記憶する用
        imported_table_list = []

        # load_table.loadTableを使用するため特定のメニューは事前に処理しておく
        _dp_preparation(objdbca, workspace_id, menu_name_rest_list, execution_no_path, imported_table_list, dp_mode)

        # 作成したview名を記憶する用
        tmp_table_list = []
        # インポート対象メニュー取得
        # T_COMN_MENU_TABLE_LINK_DATAファイル読み込み
        t_comn_menu_table_link_data = file_open_read_close(execution_no_path + '/T_COMN_MENU_TABLE_LINK_DATA')
        t_comn_menu_table_link_data_json = json.loads(t_comn_menu_table_link_data)
        # T_COMN_MENU_DATAファイル読み込み
        t_comn_menu_data = file_open_read_close(execution_no_path + '/T_COMN_MENU_DATA')
        t_comn_menu_data_json = json.loads(t_comn_menu_data)

        # インポート対象メニューを分類(ITA標準, パラメータシート作成)
        ita_default_menus = [_r for _r in t_comn_menu_table_link_data_json if _r['parameter'].get('table_name') is not None and not _r['parameter'].get('table_name').startswith('T_CMDB')]
        ita_create_menus =  [_r for _r in t_comn_menu_table_link_data_json if _r['parameter'].get('table_name') is not None and _r['parameter'].get('table_name').startswith('T_CMDB')]
        ita_create_menus = sorted(ita_create_menus, key=lambda x: x['parameter']['table_name'])

        rpt.set_time("import: ita_default_menus ")
        # ITA標準メニューのインポート
        import_table_and_data(
            objdbca,
            dp_mode,
            workspace_id,
            uploadfiles_dir,
            execution_no_path,
            ita_default_menus,
            imported_table_list,
            tmp_table_list,
            t_comn_menu_data_json,
            menu_name_rest_list,
            ita_base_menu_flg=True
        )
        rpt.set_time("import: ita_default_menus ")

        rpt.set_time("import: ita_create_menus ")
        # パラメータシート、データシートのインポート
        import_table_and_data(
            objdbca,
            dp_mode,
            workspace_id,
            uploadfiles_dir,
            execution_no_path,
            ita_create_menus,
            imported_table_list,
            tmp_table_list,
            t_comn_menu_data_json,
            menu_name_rest_list,
            ita_base_menu_flg=False
        )
        rpt.set_time("import: ita_create_menus ")

        if os.path.isfile(backupsql_path) is True:
            # 正常終了時はバックアップファイルを削除する
            os.remove(backupsql_path)

        if os.path.isdir(backupfile_dir):
            shutil.rmtree(backupfile_dir)

        if os.path.isdir(execution_no_path):
            # 展開した一時ファイル群の削除
            shutil.rmtree(execution_no_path)

        # 正常系リターン
        return True, msg, None
    except AppException as msg:
        trace_msg = traceback.format_exc()
        g.applogger.error(msg)
        g.applogger.info(trace_msg)
        trace_msg = None

        if objdbca._is_transaction is True:
            # コミット/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20005", [])
            g.applogger.error(debug_msg)
            objdbca.db_transaction_end(False)

        restoreTables(objdbca, workspace_path)
        restoreFiles(workspace_path, uploadfiles_dir)

        if os.path.isdir(execution_no_path):
            # 展開した一時ファイル群の削除
            shutil.rmtree(execution_no_path)


        # 異常系リターン
        return False, msg, trace_msg
    except Exception as msg:
        trace_msg = traceback.format_exc()
        g.applogger.error(msg)
        g.applogger.info(trace_msg)

        if objdbca._is_transaction is True:
            # コミット/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20005", [])
            g.applogger.error(debug_msg)
            objdbca.db_transaction_end(False)

        restoreTables(objdbca, workspace_path)
        restoreFiles(workspace_path, uploadfiles_dir)

        if os.path.isdir(execution_no_path):
            # 展開した一時ファイル群の削除
            shutil.rmtree(execution_no_path)


        # 異常系リターン
        return False, msg, trace_msg

    finally:
        # サービススキップファイルが存在する場合は削除する
        if os.path.exists(workspace_path + '/tmp/driver/import_menu/skip_all_service'):
            os.remove(workspace_path + '/tmp/driver/import_menu/skip_all_service')


def _dp_preparation(objdbca, workspace_id, menu_name_rest_list, execution_no_path, imported_table_list, dp_mode):
    tmp_msg = '_dp_preparation START: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # load_table.loadTableを使用するため特定のメニュー
    _base_menu_list = ['menu_list', 'menu_table_link_list', 'menu_column_link_list', 'role_menu_link_list']
    for _menu_name in _base_menu_list:
        if _menu_name in menu_name_rest_list:
            g.applogger.info(f"Target Menu: {_menu_name} START")

            # トランザクション開始
            debug_msg = g.appmsg.get_log_message("BKY-20004", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_start()

            _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, _menu_name, execution_no_path, imported_table_list, dp_mode)

            # コミット/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20005", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_end(True)

            g.applogger.info(f"Target Menu: {_menu_name} END")

    tmp_msg = '_dp_preparation END: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405


def _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, menu_name_rest, execution_no_path, imported_table_list, dp_mode):
    tmp_msg = '_basic_table_preparation START: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    rpt = RecordProcessingTimes()
    # 指定のメニューに紐づいたテーブルを削除し、インポートデータを登録する
    objmenu = _create_objmenu(objdbca, menu_name_rest_list, menu_name_rest)

    menu_id, table_name, history_table_flag = _menu_data_file_read(menu_name_rest, 'menu_id', execution_no_path)

    if history_table_flag == '1':
        if dp_mode == '1':
            rpt.set_time(f"{menu_name_rest}: delete table jnl")
            delete_jnl_sql = "DELETE FROM {}".format(table_name + '_JNL')
            rpt.set_time(f"{menu_name_rest}: delete table jnl")
            objdbca.sql_execute(delete_jnl_sql, [])
        imported_table_list.append(table_name + '_JNL')
        rpt.set_time(f"{menu_name_rest}: register data jnl")
        _register_history_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name)
        rpt.set_time(f"{menu_name_rest}: register data jnl")

    if dp_mode == '1':
        rpt.set_time(f"{menu_name_rest}: delete table")
        delete_sql = "DELETE FROM {}".format(table_name)
        objdbca.sql_execute(delete_sql, [])
        rpt.set_time(f"{menu_name_rest}: delete table")
    imported_table_list.append(table_name)
    rpt.set_time(f"{menu_name_rest}: register data")
    _register_basic_data(objdbca, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode, objmenu=objmenu)
    rpt.set_time(f"{menu_name_rest}: register data")

    menu_name_rest_list.remove(menu_name_rest)

    tmp_msg = '_basic_table_preparation END: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405


def _update_t_menu_export_import(objdbca, execution_no, status, user_language="en", execute_log=None, msg=None, trace_msg=None):
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
        # ログファイルの生成 ＋ data_listパラメータ追加
        log_filename = execute_log if execute_log is not None else f"{execution_no}.log"
        file_path = None
        error_msg = None
        try:
            if msg:
                # メッセージ生成
                if isinstance(msg, AppException):
                    g.appmsg.set_lang(user_language)
                    status_code, log_msg_args, api_msg_args = msg.args
                    _str_msg = g.appmsg.get_api_message(status_code, api_msg_args)
                    g.appmsg.set_lang(g.LANGUAGE)
                elif isinstance(msg, Exception):
                    _str_msg = msg
                else:
                    _str_msg = msg
                error_msg = f'{_str_msg} \n {trace_msg}' if trace_msg else f'{_str_msg}'

                # ログファイル配置準備
                rest_key = "execution_log"
                objmenu = load_table.loadTable(objdbca, "menu_export_import_list")
                objcolumn = FileUploadColumn(objdbca, objmenu.objtable, rest_key,'')
                file_path = objcolumn.get_file_data_path(execute_log, execution_no, target_uuid_jnl='', file_chk=False)
                dir_path = file_path.replace(log_filename, "")
                if not os.path.isdir(dir_path):
                    os.makedirs(dir_path)
                if file_path and error_msg:
                    data_list.setdefault("EXEC_LOG", log_filename)

        except Exception as e:
            trace_msg = traceback.format_exc()
            g.applogger.error(traceback.format_exc())
            g.applogger.info(trace_msg)
        objdbca.table_update(t_menu_export_import, data_list, 'EXECUTION_NO')

        # ログファイルの書き込み
        if file_path and error_msg and "EXEC_LOG" in data_list:
            file_open_write_close(file_path, 'w', error_msg)

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


def _register_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode="1"):
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    # DATAファイル確認
    if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
        # 対象ファイルなし
        raise AppException("MSG-140003", [menu_name_rest], [menu_name_rest])

    # DATAファイル読み込み
    sql_data = file_open_read_close(execution_no_path + '/' + menu_name_rest)
    json_sql_data = json.loads(sql_data)

    # WORKSPACE_IDファイル確認
    export_workspace_id = ''
    if os.path.isfile(execution_no_path + '/WORKSPACE_ID'):
        # エクスポートした環境のワークスペース名を取得
        export_workspace_id = file_open_read_close(execution_no_path + '/WORKSPACE_ID')

    # データを登録する
    pk = objmenu.get_primary_key()

    # パスワードカラムを取得する
    pass_column = ["8", "25", "26"]
    pass_column_list = []
    ret_pass_column = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_CLASS IN %s', [menu_id, pass_column])  # noqa: E501
    pass_column_list = [record['COLUMN_NAME_REST'] for record in ret_pass_column] if len(ret_pass_column) != 0 else []

    # 環境移行、パラメータシートの場合
    if dp_mode == '1' and table_name.startswith('T_CMDB'):
        chk_pk_sql = "SELECT COUNT(*) FROM `" + table_name + "` ;"
        chk_pk_record = objdbca.sql_execute(chk_pk_sql, [])
        record_count = list(chk_pk_record[0].values())[0]
        # 同一テーブルで処理済みの場合、SKIP
        if record_count == 0 and len(json_sql_data) == 0:
            g.applogger.info(f"{menu_name_rest}: target 0. ")
            return objmenu
        elif record_count != 0 and record_count == len(json_sql_data):
            g.applogger.info(f"{menu_name_rest}: already imported. ")
            return objmenu

    for json_record in json_sql_data:
        file_param = json_record['file']
        for k, v in file_param.items():
            if isinstance(v, str):
                v = v.encode()
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
            # 最終更新日時のフォーマット
            last_update_timestamp = chk_pk_record[0].get('LAST_UPDATE_TIMESTAMP')
            last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
            param['last_update_date_time'] = last_update_date_time

        # PasswordColumn, ロール名置換対象の場合
        replace_role_menus = ['role_menu_link_list', 'menu_role_creation_info']
        if menu_name_rest in replace_role_menus or len(pass_column_list) != 0:
            # PasswordColumnかを判定
            for _pass_column in pass_column_list:
                if _pass_column in param and param[_pass_column] is not None:
                    param[_pass_column] = ky_encrypt(param[_pass_column])

            # ロール名をインポート先に置換
            if menu_name_rest in replace_role_menus:
                param = replace_role_name(workspace_id, export_workspace_id, param)

        # 登録用パラメータを作成
        parameters = {
            "file": file_param,
            "parameter": param,
            "type": param_type
        }

        tmp_msg = "Target register data: {}, {}".format(parameters.get("type"), parameters.get("parameter"))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        objmenu.reset_message()
        if param_type == 'Register':
            exec_result = objmenu.exec_maintenance(parameters, pk_value, "", True, False, True, False, True)  # noqa: E999
            if not exec_result[0]:
                result_msg = _format_loadtable_msg(exec_result[2])
                result_msg = json.dumps(result_msg, ensure_ascii=False)
                raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
        elif param_type == 'Update':
            # import_mode=Trueで登録を実行
            exec_result = objmenu.exec_maintenance(parameters, pk_value, "", True, False, True, False, True)  # noqa: E999
            if not exec_result[0]:
                result_msg = _format_loadtable_msg(exec_result[2])
                result_msg = json.dumps(result_msg, ensure_ascii=False)
                raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー


    return objmenu


def _register_basic_data(objdbca, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode, objmenu=None):
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    # DATAファイル読み込み
    sql_data = file_open_read_close(execution_no_path + '/' + menu_name_rest)
    json_sql_data = json.loads(sql_data)

    # WORKSPACE_IDファイル確認
    export_workspace_id = ''
    if os.path.isfile(execution_no_path + '/WORKSPACE_ID'):
        # エクスポートした環境のワークスペース名を取得
        export_workspace_id = file_open_read_close(execution_no_path + '/WORKSPACE_ID')

    # データを登録する
    if objmenu is None:
        objmenu = load_table.loadTable(objdbca, menu_name_rest)   # noqa: F405
    pk = objmenu.get_primary_key()

    # ファイルアップロード系カラムを取得する
    file_column = ["9", "20"]  # [FileUploadColumn, FileUploadEncryptColumn]
    file_column_list = []
    ret_file_column = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_CLASS IN %s AND DISUSE_FLAG = %s', [menu_id, file_column, 0])  # noqa: E501
    file_column_list = [record['COLUMN_NAME_REST'] for record in ret_file_column] if len(ret_file_column) != 0 else []

    # PKの rest_key取得
    _pk_rest_name = objmenu.get_rest_key(objmenu.get_primary_key())

    for json_record in json_sql_data:
        param = json_record['parameter']

        # 移行先に主キーの重複データが既に存在するか確認
        param_type = "Register"
        if dp_mode == '2':
            ret_t_comn_menu_column_link = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COL_NAME = %s', [menu_id, pk])  # noqa: E501
            pk_name = ret_t_comn_menu_column_link[0].get('COLUMN_NAME_REST')
            pk_value = param[pk_name]
            chk_pk_sql = " SELECT * FROM `" + table_name + "` WHERE `" + pk + "` = '" + pk_value + "'"
            chk_pk_record = objdbca.sql_execute(chk_pk_sql, [])
            if len(chk_pk_record) != 0:
                # 主キーが既に存在する場合
                param_type = "Update"

        # 最終更新者をバックヤードユーザに設定
        param['last_updated_user'] = g.get('USER_ID')

        # ロール-メニュー紐付管理個別処理
        if menu_name_rest == 'role_menu_link_list':
            # 「_エクスポート元ワークスペース名-admin」ロールを
            # 「_インポート先ワークスペース名-admin」に置換する
            search_str = '_' + export_workspace_id + '-admin'
            if param['role_name'] == search_str:
                param['role_name'] = '_' + workspace_id + '-admin'

        colname_parameter = objmenu.convert_restkey_colname(param, [])

        if param_type == 'Register':
            result = objdbca.table_insert(table_name, colname_parameter, pk)
        elif param_type == 'Update':
            result = objdbca.table_update(table_name, colname_parameter, pk)

        # ファイル関連カラムの設定取得、リンク生成
        if 'file' not in json_record or len(file_column_list) == 0:
            continue

        # 履歴テーブルのチェックID取得
        chk_jnl_sql = " SELECT TABLE_NAME FROM information_schema.tables WHERE `TABLE_NAME` = %s "
        chk_jnl_record = objdbca.sql_execute(chk_jnl_sql, [table_name + "_JNL"])
        if len(chk_jnl_record) == 0:
            continue

        chk_jnl_sql = " SELECT * FROM `" + table_name + "_JNL" + "` WHERE `" + pk + "` = '" + param[_pk_rest_name] + "'" + " ORDER BY LAST_UPDATE_TIMESTAMP DESC "
        chk_jnl_record = objdbca.sql_execute(chk_jnl_sql, [])
        if len(chk_jnl_record) == 0:
            continue

        # ファイルが無い場合はSKIP
        file_param = json_record['file']
        if file_param is not None and len(file_param) == 0:
            continue

        # ファイルリンク生成
        # symlink : ~/old/<journal_id>/<file> -> ~/<file>
        for file_column in file_column_list:
            col_class_name = objmenu.get_col_class_name(file_column)
            objcolumn = objmenu.get_columnclass(file_column, "Register")
            if col_class_name in ["FileUploadColumn", "FileUploadEncryptColumn"]:
                if param.get(file_column):
                    file_path = objcolumn.get_file_data_path(param[file_column], param[_pk_rest_name], None, False)
                    # 履歴IDからファイル実体のパス特定
                    for _jnls in chk_jnl_record:
                        journal_id = _jnls.get("JOURNAL_SEQ_NO")
                        old_file_path = objcolumn.get_file_data_path(param[file_column], param[_pk_rest_name], journal_id, False)
                        if os.path.isfile(old_file_path):
                            break
                    # symlink
                    if os.path.isfile(old_file_path) and file_path:
                        if os.path.islink(file_path):
                            os.unlink(file_path)
                        os.symlink(old_file_path, file_path)


def _register_history_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode="1"):
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    menu_name_rest += '_JNL'
    history_table_name = table_name + "_JNL"

    # DATAファイル確認
    if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
        # 対象ファイルなし
        raise AppException("MSG-140003", [menu_name_rest], [menu_name_rest])

    # DATAファイル読み込み
    sql_data = file_open_read_close(execution_no_path + '/' + menu_name_rest)
    json_sql_data = json.loads(sql_data)

    # WORKSPACE_IDファイル確認
    export_workspace_id = ''
    if os.path.isfile(execution_no_path + '/WORKSPACE_ID'):
        # エクスポートした環境のワークスペース名を取得
        export_workspace_id = file_open_read_close(execution_no_path + '/WORKSPACE_ID')

    # パスワードカラムを取得する
    pass_column = ["8", "25", "26"]
    pass_column_list = []
    ret_pass_column = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_CLASS IN %s', [menu_id, pass_column])  # noqa: E501
    pass_column_list = [record['COLUMN_NAME_REST'] for record in ret_pass_column] if len(ret_pass_column) != 0 else []

    # ファイルアップロード系カラムを取得する
    file_column = ["9", "20"]  # [FileUploadColumn, FileUploadEncryptColumn]
    file_column_list = []
    ret_file_column = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_CLASS IN %s AND DISUSE_FLAG = %s', [menu_id, file_column, 0])  # noqa: E501
    file_column_list = [record['COLUMN_NAME_REST'] for record in ret_file_column] if len(ret_file_column) != 0 else []

    # PKの rest_key取得
    _pk_rest_name = objmenu.get_rest_key(objmenu.get_primary_key())

    # 環境移行、パラメータシートの場合
    if dp_mode == '1' and table_name.startswith('T_CMDB'):
        chk_pk_sql = "SELECT COUNT(*) FROM `" + history_table_name + "` ;"
        chk_pk_record = objdbca.sql_execute(chk_pk_sql, [])
        record_count = list(chk_pk_record[0].values())[0]
        # 同一テーブルで処理済みの場合、SKIP
        if record_count == 0 and len(json_sql_data) == 0:
            g.applogger.info(f"{menu_name_rest}: target 0. ")
            return objmenu
        elif record_count != 0 and record_count == len(json_sql_data):
            g.applogger.info(f"{menu_name_rest}: already imported. ")
            return objmenu

    for json_record in json_sql_data:
        file_param = json_record['file']
        for k, v in file_param.items():
            if isinstance(v, str):
                v = v.encode()
        param = json_record['parameter']

        # 移行先に主キーの重複データが既に存在するか確認
        journal_id = param['journal_id']
        chk_pk_sql = " SELECT * FROM `" + history_table_name + "` WHERE `JOURNAL_SEQ_NO` = '" + journal_id + "'"
        chk_pk_record = objdbca.sql_execute(chk_pk_sql, [])
        if len(chk_pk_record) != 0:
            # 主キーが重複する場合は既存データを削除してからINSERTする
            delete_table_sql = "DELETE FROM `" + history_table_name + "` WHERE `JOURNAL_SEQ_NO` = '" + journal_id + "'"
            objdbca.sql_execute(delete_table_sql, [])

            # 最終更新日時のフォーマット
            last_update_timestamp = chk_pk_record[0].get('LAST_UPDATE_TIMESTAMP')
            last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
            param['last_update_date_time'] = last_update_date_time

        # PasswordColumn, ロール名置換対象の場合
        replace_role_menus = ['role_menu_link_list_JNL', 'menu_role_creation_info_JNL']
        if menu_name_rest in replace_role_menus or len(pass_column_list) != 0:
            # PasswordColumnかを判定
            for _pass_column in pass_column_list:
                if _pass_column in param and param[_pass_column] is not None:
                    param[_pass_column] = ky_encrypt(param[_pass_column])

            # ロール名をインポート先に置換
            if menu_name_rest in replace_role_menus:
                param = replace_role_name(workspace_id, export_workspace_id, param)

        colname_parameter = objmenu.convert_restkey_colname(param, [])

        if isinstance(colname_parameter, dict):
            colname_parameter = [colname_parameter]

        is_last_res = True
        journal_id = param['journal_id']
        journal_datetime = param['journal_datetime']
        journal_action = param['journal_action']
        for data in colname_parameter:
            add_data = {}

            add_data['JOURNAL_SEQ_NO'] = journal_id
            add_data['JOURNAL_REG_DATETIME'] = journal_datetime
            add_data['JOURNAL_ACTION_CLASS'] = journal_action

            data['LAST_UPDATE_USER'] = g.get('USER_ID')
            # make history data
            history_data = dict(data, **add_data)

            # make sql statement
            column_list = list(history_data.keys())
            prepared_list = list(map(lambda a: "%s", column_list))
            value_list = list(history_data.values())

            sql = "INSERT INTO `{}` ({}) VALUES ({})".format(history_table_name, ','.join(column_list), ','.join(prepared_list))

            res = objdbca.sql_execute(sql, value_list)
            if res is False:
                is_last_res = False
                break

            # upload file : ~/old/<journal_id>/<file>
            for file_column in file_column_list:
                col_class_name = objmenu.get_col_class_name(file_column)
                objcolumn = objmenu.get_columnclass(file_column, "Register")
                if col_class_name in ["FileUploadColumn", "FileUploadEncryptColumn"]:
                    old_file_path = objcolumn.get_file_data_path(param[file_column], param[_pk_rest_name], journal_id, False)
                    if old_file_path and param.get(file_column) and file_param.get(file_column):
                        old_dir_path = old_file_path.replace(param[file_column], "")

                        if not os.path.isdir(old_dir_path):
                            os.makedirs(old_dir_path)

                        _tmp_old_file_path = old_file_path.replace("/storage/", "/tmp/")
                        if os.path.isfile(_tmp_old_file_path):
                            os.remove(_tmp_old_file_path)

                        if not os.path.isfile(old_file_path):
                            if col_class_name == "FileUploadColumn":
                                upload_file(old_file_path, file_param[file_column])  # noqa: F405
                            elif col_class_name == "FileUploadEncryptColumn":
                                encrypt_upload_file(old_file_path, file_param[file_column])  # noqa: F405

                        _tmp_old_file_path = old_file_path.replace("/storage/", "/tmp/")
                        if os.path.isfile(_tmp_old_file_path):
                            os.remove(_tmp_old_file_path)
                else:
                    pass

    return objmenu


def menu_export_exec(objdbca, record, workspace_id, export_menu_dir, uploadfiles_dir):  # noqa: C901
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
        specified_time = json_storage_item.get('specified_timestamp')
        tmp_msg = "Target record data: {}, {}, {}, {}, {}".format(execution_no, json_storage_item, mode, abolished_type, specified_time)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        dir_name = 'ita_exportdata_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        dir_path = export_menu_dir + '/' + dir_name
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
            g.applogger.debug("made export_dir")

        # 対象のDBの存在チェック
        menu_list = json_storage_item["menu"]

        menu_group_list = []
        # 親メニューグループのデータ記憶用
        parent_menu_group_id_list = []
        for menu in menu_list:
            # メニューの存在確認
            menu_info_record = _check_menu_info(menu, objdbca)

            add_menu_group = {}
            menu_group_id = menu_info_record.get('MENU_GROUP_ID')
            for menu_group in menu_group_list:
                if menu_group_id == menu_group['id']:
                    add_menu_group = menu_group
                    break
            else:
                parent_menu_group_id = menu_info_record.get('PARENT_MENU_GROUP_ID')
                if parent_menu_group_id not in parent_menu_group_id_list:
                    # 親グループのIDを記憶していく
                    parent_menu_group_id_list.append(parent_menu_group_id)
                add_menu_group['parent_id'] = parent_menu_group_id
                add_menu_group['id'] = menu_group_id
                add_menu_group['menu_group_name_ja'] = menu_info_record.get('MENU_GROUP_NAME_JA')
                add_menu_group['menu_group_name_en'] = menu_info_record.get('MENU_GROUP_NAME_EN')
                add_menu_group['disp_seq'] = menu_info_record.get('GROUP_DISP_SEQ')
                add_menu_group['menus'] = []
                menu_group_list.append(add_menu_group)

            add_menu = {}
            add_menu['id'] = menu_info_record.get('MENU_ID')
            add_menu['menu_name_ja'] = menu_info_record.get('MENU_NAME_JA')
            add_menu['menu_name_en'] = menu_info_record.get('MENU_NAME_EN')
            add_menu['menu_name_rest'] = menu_info_record.get('MENU_NAME_REST')
            add_menu['disp_seq'] = menu_info_record.get('DISP_SEQ')
            add_menu_group['menus'].append(add_menu)

        menus_data = {
            "menu_groups": menu_group_list,
        }
        menus_data_path = dir_path + '/MENU_GROUPS'
        file_open_write_close(menus_data_path, 'w', json.dumps(menus_data))

        menu_group_id_dict = {}
        for menu_group_id in parent_menu_group_id_list:
            menu_id_sql = " SELECT * FROM `T_COMN_MENU_GROUP` WHERE `DISUSE_FLAG` <> 1 AND `MENU_GROUP_ID` = %s "
            t_comn_menu_group_record = objdbca.sql_execute(menu_id_sql, [menu_group_id])
            menu_group_name_dict = {}
            for record in t_comn_menu_group_record:
                menu_group_id = record.get('MENU_GROUP_ID')
                menu_group_name_dict['MENU_GROUP_NAME_JA'] = record.get('MENU_GROUP_NAME_JA')
                menu_group_name_dict['MENU_GROUP_NAME_EN'] = record.get('MENU_GROUP_NAME_EN')
                menu_group_name_dict['DISP_SEQ'] = record.get('DISP_SEQ')
                menu_group_id_dict[menu_group_id] = menu_group_name_dict

        parent_menus_data_path = dir_path + '/PARENT_MENU_GROUPS'
        file_open_write_close(parent_menus_data_path, 'w', json.dumps(menu_group_id_dict))

        # 更新系テーブル取得
        filter_parameter = {}
        filter_parameter_jnl = {}
        if mode == '1' and abolished_type == '1':
            # 環境移行/廃止を含む
            filter_parameter = {}
        elif mode == '1' and abolished_type == '2':
            # 環境移行/廃止を含まない
            filter_parameter = {"discard": {'NORMAL': '0'}}
            filter_parameter_jnl = {}
        elif mode == '2' and abolished_type == '1':
            # 時刻指定/廃止を含む
            filter_parameter = {"last_update_date_time": {"RANGE": {'START': specified_time}}}
            filter_parameter_jnl = {"LAST_UPDATE_TIMESTAMP": specified_time}
        elif mode == '2' and abolished_type == '2':
            # 時刻指定/廃止を含まない
            filter_parameter = {"discard": {'NORMAL': '0'}, "last_update_date_time": {"RANGE": {'START': specified_time}}}
            filter_parameter_jnl = {"LAST_UPDATE_TIMESTAMP": specified_time}

        for menu in menu_list:
            DB_path = dir_path + '/' + menu
            objmenu = load_table.loadTable(objdbca, menu)   # noqa: F405

            if menu == 'movement_list_ansible_legacy':
                filter_parameter["orchestrator"] = {"LIST": ['Ansible Legacy']}
            elif menu == 'movement_list_ansible_pioneer':
                filter_parameter["orchestrator"] = {"LIST": ['Ansible Pioneer']}
            elif menu == 'movement_list_ansible_role':
                filter_parameter["orchestrator"] = {"LIST": ['Ansible Legacy Role']}
            elif menu == 'movement_list_terraform_cloud_ep':
                filter_parameter["orchestrator"] = {"LIST": ['Terraform Cloud/EP']}
            elif menu == 'movement_list_terraform_cli':
                filter_parameter["orchestrator"] = {"LIST": ['Terraform CLI']}

            filter_mode = 'export'
            status_code, result, msg = objmenu.rest_export_filter(filter_parameter, filter_mode)
            if status_code != '000-00000':
                log_msg_args = [msg]
                api_msg_args = [msg]
                raise AppException(status_code, log_msg_args, api_msg_args)

            file_open_write_close(DB_path, 'w', json.dumps(result, ensure_ascii=False))

            # 履歴テーブル
            history_flag = objmenu.get_objtable().get('MENUINFO').get('HISTORY_TABLE_FLAG')
            if history_flag == '1':
                DB_path = dir_path + '/' + menu + '_JNL'
                filter_mode = 'export_jnl'

                # 廃止を含まない場合、本体のテーブルの廃止状態を確認してデータ取得
                status_code, result, msg = objmenu.rest_export_filter(filter_parameter_jnl, filter_mode, abolished_type)
                if status_code != '000-00000':
                    log_msg_args = [msg]
                    api_msg_args = [msg]
                    raise AppException(status_code, log_msg_args, api_msg_args)
                file_open_write_close(DB_path, 'w', json.dumps(result, ensure_ascii=False))

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
        table_definition_id_list = []
        for record in t_comn_menu_table_link_record:
            table_definition_id_list.append(record.get('TABLE_DEFINITION_ID'))
            table_name = record.get('TABLE_NAME')
            table_name_list.append(table_name)
            history_table_flag = record.get('HISTORY_TABLE_FLAG')
            if history_table_flag == '1':
                table_name_list.append(table_name + '_JNL')

            if table_name.startswith('T_CMDB'):
                view_name = record.get('VIEW_NAME')
                if view_name is not None:
                    show_create_sql = 'SHOW CREATE VIEW `%s` ' % (view_name)
                    rec = objdbca.sql_execute(show_create_sql, [])
                    create_view_str = rec[0]['Create View']
                    # Create文から余計な文言を切り取る
                    end_pos = create_view_str.find(' VIEW ')
                    create_view_str = create_view_str[:6] + create_view_str[end_pos:]
                    create_view_str = create_view_str.replace('CREATE VIEW', 'CREATE OR REPLACE VIEW')
                    view_data_path = dir_path + '/' + view_name
                    file_open_write_close(view_data_path, 'w', create_view_str)

                    if history_table_flag == '1':
                        view_name_jnl = view_name + '_JNL'
                        show_create_sql = 'SHOW CREATE VIEW `%s` ' % (view_name_jnl)
                        rec = objdbca.sql_execute(show_create_sql, [])
                        create_view_str = rec[0]['Create View']
                        # Create文から余計な文言を切り取る
                        end_pos = create_view_str.find(' VIEW ')
                        create_view_str = create_view_str[:6] + create_view_str[end_pos:]
                        create_view_str = create_view_str.replace('CREATE VIEW', 'CREATE OR REPLACE VIEW')
                        view_data_path = dir_path + '/' + view_name_jnl
                        file_open_write_close(view_data_path, 'w', create_view_str)

        db_user = os.environ.get('DB_ADMIN_USER')
        db_password = os.environ.get('DB_ADMIN_PASSWORD')
        db_host = os.environ.get('DB_HOST')
        db_database = objdbca._db

        for table_name in table_name_list:
            sqldump_path = dir_path + '/' + table_name + '.sql'

            cmd = ["mysqldump", "--single-transaction", "--opt", "-u", db_user, "-p" + db_password, "-h", db_host, "--skip-column-statistics", "--set-gtid-purged=OFF", db_database, "--no-data", table_name]
            # 時刻指定の場合、DROP TABLE文を追加しないようオプションを追加
            if mode == '2':
                cmd.append("--skip-add-drop-table")

            sp_sqldump = subprocess.run(cmd, capture_output=True, text=True)

            if sp_sqldump.stdout == '' and sp_sqldump.returncode != 0:
                msg = sp_sqldump.stderr
                log_msg_args = [msg]
                api_msg_args = [msg]
                raise AppException("499-00201", [log_msg_args], [api_msg_args])

            sqldump_result = re.sub(r'DEFINER[ ]*=[ ]*[^*]*\*/', r'*/', sp_sqldump.stdout)
            if mode == '2':
                # 時刻指定の場合、dump結果を一部編集する
                sqldump_result = sqldump_result.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS')
            file_open_write_close(sqldump_path, 'w', sqldump_result)

        # インポート時に利用するT_COMN_MENU_DATAを作成する
        t_comn_menu_data_path = dir_path + '/T_COMN_MENU_DATA'
        objmenu = load_table.loadTable(objdbca, 'menu_list')   # noqa: F405
        filter_parameter = {"discard": {"LIST": ["0"]}, "menu_name_rest": {"LIST": menu_list}}
        filter_mode = 'export'
        status_code, result, msg = objmenu.rest_export_filter(filter_parameter, filter_mode)
        if status_code != '000-00000':
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException(status_code, log_msg_args, api_msg_args)
        file_open_write_close(t_comn_menu_data_path, 'w', json.dumps(result, ensure_ascii=False))

        # インポート時に利用するMENU_NAME_REST_LISTを作成する
        menu_name_rest_list = ",".join(menu_list)
        menu_name_rest_path = dir_path + '/MENU_NAME_REST_LIST'
        file_open_write_close(menu_name_rest_path, 'w', menu_name_rest_list)

        # インポート時に利用するT_COMN_MENU_TABLE_LINK_DATAを作成する
        t_comn_menu_table_link_data_path = dir_path + '/T_COMN_MENU_TABLE_LINK_DATA'
        objmenu = load_table.loadTable(objdbca, 'menu_table_link_list')   # noqa: F405
        filter_parameter = {"discard": {"LIST": ["0"]}, "uuid": {"LIST": table_definition_id_list}}
        filter_mode = 'export'
        status_code, result, msg = objmenu.rest_export_filter(filter_parameter, filter_mode)
        if status_code != '000-00000':
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException(status_code, log_msg_args, api_msg_args)
        file_open_write_close(t_comn_menu_table_link_data_path, 'w', json.dumps(result, ensure_ascii=False))

        # アップロード時に利用するDP_INFOファイルを作成する
        dp_info = {
            "DP_MODE": mode,
            "ABOLISHED_TYPE": abolished_type,
            "SPECIFIED_TIMESTAMP": specified_time
        }
        dp_info_path = dir_path + '/DP_INFO'
        file_open_write_close(dp_info_path, 'w', json.dumps(dp_info))

        # ロール-メニュー紐付管理のロール置換用にエクスポート時のWORKSPACE_IDを確保しておく
        workspace_id_path = dir_path + '/WORKSPACE_ID'
        file_open_write_close(workspace_id_path, 'w', workspace_id)

        # アップロード時のバージョン差異チェック用にエクスポート時のVERSIONを確保しておく
        common_db = DBConnectCommon()
        version_data = _collect_ita_version(common_db)
        version_path = dir_path + '/VERSION'
        file_open_write_close(version_path, 'w', version_data["version"])

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
                "discard": "0"
            },
            "type": "Update"
        }

        # 「メニューエクスポート・インポート管理」のファイル名を更新
        objmenu = load_table.loadTable(objdbca, 'menu_export_import_list')

        # トランザクション開始
        debug_msg = g.appmsg.get_log_message("BKY-20004", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_start()

        exec_result = objmenu.exec_maintenance(parameters, execution_no, "", False, False, True, False, True)  # noqa: E999

        # コミット/トランザクション終了
        debug_msg = g.appmsg.get_log_message("BKY-20005", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_end(True)

        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

        # 更新が正常に終了したらtmpの作業ファイルを削除する
        os.remove(kym_path)

        # 正常系リターン
        return True, msg, None
    except AppException as msg:
        trace_msg = traceback.format_exc()
        g.applogger.error(msg)
        g.applogger.info(trace_msg)
        trace_msg = None

        # エラー時はtmpの作業ファイルを削除する
        if os.path.isdir(export_menu_dir):
            shutil.rmtree(export_menu_dir)
        # 異常系リターン
        return False, msg, trace_msg
    except Exception as msg:
        trace_msg = traceback.format_exc()
        g.applogger.error(msg)
        g.applogger.info(trace_msg)

        # エラー時はtmpの作業ファイルを削除する
        if os.path.isdir(export_menu_dir):
            shutil.rmtree(export_menu_dir)

        # 異常系リターン
        return False, msg, trace_msg


def _collect_ita_version(common_db):
    """
        ITAのバージョン情報を取得する
        ARGS:
            common_db:DB接クラス  DBConnectCommon()
        RETRUN:
            version_data
    """

    # 変数定義
    lang = g.get('LANGUAGE')

    # 『バージョン情報』テーブルからバージョン情報を取得
    ret = common_db.table_select('T_COMN_VERSION', 'WHERE DISUSE_FLAG = %s', [0])

    # 件数確認
    if len(ret) != 1:
        raise AppException("499-00601")

    if lang == 'ja':
        installed_driver = json.loads(ret[0].get('INSTALLED_DRIVER_JA'))
    else:
        installed_driver = json.loads(ret[0].get('INSTALLED_DRIVER_EN'))

    version_data = {
        "version": ret[0].get('VERSION'),
        "installed_driver": installed_driver
    }

    return version_data


def _create_objmenu(objdbca, menu_name_rest_list, target_menu):
    # menu_name_rest_listの中にあるtarget_tableのobjmenuを作成して返す
    objmenu = None
    for menu_name_rest in menu_name_rest_list:
        if menu_name_rest == target_menu:
            objmenu = load_table.loadTable(objdbca, target_menu)
            break
    return objmenu


def _menu_data_file_read(menu_name_rest, pk, execution_no_path):
    # T_COMN_MENU_DATA、MENU_ID_TABLE_LISTファイルを読み取り
    # menu_idとtable_nameを返す
    t_comn_menu_data = file_open_read_close(execution_no_path + '/T_COMN_MENU_DATA')
    t_comn_menu_data_json = json.loads(t_comn_menu_data)

    menu_id = ''
    for record in t_comn_menu_data_json:
        param = record['parameter']
        tmp_menu_name_rest = param.get('menu_name_rest')
        if tmp_menu_name_rest == menu_name_rest:
            menu_id = param.get(pk)
            break

    table_name = ''
    history_table_flag = ''
    t_comn_menu_table_link_data = file_open_read_close(execution_no_path + '/T_COMN_MENU_TABLE_LINK_DATA')
    t_comn_menu_table_link_data_json = json.loads(t_comn_menu_table_link_data)
    for record in t_comn_menu_table_link_data_json:
        param = record['parameter']
        menu_id_tmp = param.get('uuid')
        if menu_id == menu_id_tmp:
            table_name = param.get('table_name')
            history_table_flag = param.get('history_table_flag')
            break

    return menu_id, table_name, history_table_flag


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

    sql = (
        "SELECT TAB_B.MENU_GROUP_ID, TAB_B.MENU_GROUP_NAME_JA, TAB_B.MENU_GROUP_NAME_EN, TAB_B.PARENT_MENU_GROUP_ID, "
        "TAB_A.MENU_ID, TAB_A.MENU_NAME_JA, TAB_A.MENU_NAME_EN, TAB_A.MENU_NAME_REST, "
        "TAB_A.DISP_SEQ, TAB_B.DISP_SEQ GROUP_DISP_SEQ "
        "FROM `T_COMN_MENU` TAB_A "
        "INNER JOIN T_COMN_MENU_GROUP TAB_B "
        "ON TAB_A.MENU_GROUP_ID=TAB_B.MENU_GROUP_ID "
        "WHERE TAB_A.MENU_NAME_REST=%s "
        "AND TAB_A.DISUSE_FLAG=%s "
    )

    menu_record = wsdb_istc.sql_execute(sql, [menu, 0])
    if not menu_record:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00002", log_msg_args, api_msg_args)  # noqa: F405

    return menu_record[0]


def addline_msg(msg=''):
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line


def backup_table(objdbca, sqldump_path, menu_name_rest_list):
    """
        テーブルをバックアップする
        ARGS:
            tableAry: バックアップするテーブル名のリスト
        RETURN:
            boolean
    """
    g.applogger.debug("backup_table start")

    db_user = os.environ.get('DB_ADMIN_USER')
    db_password = os.environ.get('DB_ADMIN_PASSWORD')
    db_host = os.environ.get('DB_HOST')
    db_database = objdbca._db

    # REST名からmenu_idを取得
    menu_id_sql = " SELECT `MENU_ID` FROM `T_COMN_MENU` WHERE `MENU_NAME_REST` IN %s "
    t_comn_menu_record = objdbca.sql_execute(menu_id_sql, [menu_name_rest_list])
    menu_id_list = []
    for record in t_comn_menu_record:
        menu_id = record.get('MENU_ID')
        menu_id_list.append(menu_id)

    # menu_idからtable_nameを取得
    table_name_sql = " SELECT * FROM `T_COMN_MENU_TABLE_LINK` WHERE `MENU_ID` IN %s "
    t_comn_menu_table_link_record = objdbca.sql_execute(table_name_sql, [menu_id_list])
    table_name_list = []
    for record in t_comn_menu_table_link_record:
        table_name = record.get('TABLE_NAME')
        table_name_list.append(table_name)
        history_table_flag = record.get('HISTORY_TABLE_FLAG')
        if history_table_flag == '1':
            table_name_list.append(table_name + '_JNL')

    cmd = ["mysqldump", "--single-transaction", "--opt", "-u", db_user, "-p" + db_password, "-h", db_host, "--skip-column-statistics", "--set-gtid-purged=OFF", db_database]

    cmd += table_name_list

    sp_sqldump = subprocess.run(cmd, capture_output=True, text=True)

    if sp_sqldump.stdout == '' and sp_sqldump.returncode != 0:
        msg = sp_sqldump.stderr
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException("MSG-140004", [log_msg_args], [api_msg_args])

    sqldump_result = re.sub(r'DEFINER[ ]*=[ ]*[^*]*\*/', r'*/', sp_sqldump.stdout)
    file_open_write_close(sqldump_path, 'w', sqldump_result)

    g.applogger.debug("backup_table end")
    return menu_id_list


def restoreTables(objdbca, workspace_path):
    # テーブルをリストアする

    g.applogger.debug("restoreTables start")
    backup_dir = workspace_path + "/tmp/driver/import_menu/backup"
    backupsql_path = backup_dir + '/backup.sql'

    if os.path.isfile(backupsql_path) is False:
        # バックアップファイルが無い場合は処理終了
        return

    objdbca.sqlfile_execute(backupsql_path)

    if os.path.isfile(backupsql_path) is True:
        # リストア終了時にバックアップファイルを削除する
        os.remove(backupsql_path)

    g.applogger.debug("restoreTables end")


def fileBackup(backupfile_dir, uploadfiles_dir, menu_id_list):
    # backupfile_dir : workspace_path + "/tmp/driver/import_menu/uploadfiles"
    # uploadfiles_dir : workspace_path + "/uploadfiles"
    g.applogger.debug("fileBackup start")

    # uploadfiles配下のディレクトリ一覧を記憶しておく
    files = os.listdir(uploadfiles_dir)
    dir_list = []
    for f in files:
        if os.path.isdir(os.path.join(uploadfiles_dir, f)):
            dir_list.append(f)
    dir_list_str = ",".join(dir_list)
    dir_list_path = backupfile_dir + '/UPLOADFILES_DIR_LIST'
    file_open_write_close(dir_list_path, 'w', dir_list_str)

    # インポート対象メニューのMENU_IDリスト
    menu_id_list_str = ",".join(menu_id_list)
    menu_id_list_path = backupfile_dir + '/BACKUP_MENU_ID_LIST'
    file_open_write_close(menu_id_list_path, 'w', menu_id_list_str)

    for menu_id in menu_id_list:
        menu_dir = uploadfiles_dir + '/' + menu_id
        # ディレクトリ存在チェック
        if os.path.isdir(menu_dir) is False:
            continue

        # ファイル一覧取得
        resAry = []
        for curDir, dirs, files in os.walk(menu_dir):
            for file in files:
                resAry.append(os.path.join(curDir, file))

        # コピー
        cmd = ["cp", "-rp", menu_dir, backupfile_dir]
        sp_copy = subprocess.run(cmd, capture_output=True, text=True)

        if sp_copy.returncode != 0:
            msg = sp_copy.stderr
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException("MSG-140005", [log_msg_args], [api_msg_args])

        # コピーできたかを確認する
        for path in resAry:
            if not os.path.exists(path):
                msg = g.appmsg.get_api_message("MSG-30036")
                log_msg_args = [msg]
                api_msg_args = [msg]
                raise AppException("MSG-140005", [log_msg_args], [api_msg_args])

    g.applogger.debug("fileBackup end")


def restoreFiles(workspace_path, uploadfiles_dir):
    # uploadfiles_dir : workspace_path + "/uploadfiles"
    # ディレクトリとファイルをリストアする
    g.applogger.debug("restoreFiles start")
    backupfile_dir = workspace_path + "/tmp/driver/import_menu/uploadfiles/"

    if os.path.isdir(backupfile_dir) is False:
        return

    # インポート前にuploadfiles配下にあったディレクトリ一覧
    if os.path.isfile(backupfile_dir + '/UPLOADFILES_DIR_LIST') is False:
        # 対象ファイルなし
        raise AppException("MSG-140006", [], [])

    # バックアップ対象メニュー取得
    uploadfiles_dir_list = file_open_read_close(backupfile_dir + '/UPLOADFILES_DIR_LIST')
    uploadfiles_dir_list = uploadfiles_dir_list.split(',')

    # インポート前のuploadfiles配下に無いディレクトリは削除する
    files = os.listdir(uploadfiles_dir)
    for f in files:
        if f not in uploadfiles_dir_list:
            shutil.rmtree(uploadfiles_dir + '/' + f)

    if os.path.isfile(backupfile_dir + '/BACKUP_MENU_ID_LIST') is False:
        # 対象ファイルなし
        raise AppException("MSG-140007", [], [])

    # バックアップ対象メニュー取得
    backup_menu_id_list = file_open_read_close(backupfile_dir + '/BACKUP_MENU_ID_LIST')
    backup_menu_id_list = backup_menu_id_list.split(',')

    for dir in backup_menu_id_list:
        if os.path.isdir(uploadfiles_dir + '/' + dir):
            # インポート途中のファイルがあると不整合を起こすので削除する
            shutil.rmtree(uploadfiles_dir + '/' + dir)
            if os.path.isdir(backupfile_dir + '/' + dir):
                os.mkdir(uploadfiles_dir + '/' + dir)
            else:
                continue
        elif os.path.isdir(backupfile_dir + '/' + dir) is False:
            # バックアップにもuploadfilesにも対象メニューのディレクトリが存在しない場合はcontinue
            continue

        # コピー
        cmd = ["cp", "-rp", backupfile_dir + dir, uploadfiles_dir]
        sp_copy = subprocess.run(cmd, capture_output=True, text=True)

        if sp_copy.returncode != 0:
            msg = sp_copy.stderr
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException("MSG-140007", log_msg_args, api_msg_args)

    # リストア終了時にバックアップ用フォルダを削除する
    shutil.rmtree(backupfile_dir)

    g.applogger.debug("restoreFiles end")


def replace_role_name(workspace_id, export_workspace_id, param, rest_key_name="role_name"):
    # 「_エクスポート元ワークスペース名-admin」を「_インポート先ワークスペース名-admin」に置換する
    search_str = '_' + export_workspace_id + '-admin'
    if param[rest_key_name] == search_str:
        param[rest_key_name] = '_' + workspace_id + '-admin'
    return param


def file_open_write_close(path, mode, value, encoding='utf-8', file_del=True):
    """
    file write operation. (oprn-write-close)
    Args:
        path: file path
        mode: file open mode
        value: write value
        encoding: encoding type. Defaults to 'utf-8'.
        file_del: delete flg. Defaults to True.
    """
    try:
        objsw = storage_write()
        objsw.open(path, mode=mode)
        objsw.write(value)
        objsw.close(file_del)
        if os.path.isfile(objsw.make_temp_path(path)):
            os.remove(objsw.make_temp_path(path))
    except Exception as e:
        raise AppException("MSG-140009", [e], [e])

def file_open_read_close(path, encoding='utf-8'):
    """
    file read operation. (oprn-write-close)
    Args:
        path: file path
        encoding: encoding type. Defaults to 'utf-8'.
    Raises:
        AppException
    Returns:
        value: file data
    """
    try:
        objsr = storage_read_text()
        value = objsr.read_text(path, encoding)
        return value
    except Exception as e:
        raise AppException("MSG-140010", [e], [e])


def import_table_and_data(
    objdbca,
    dp_mode,
    workspace_id,
    uploadfiles_dir,
    execution_no_path,
    menus_list,
    imported_table_list,
    tmp_table_list,
    t_comn_menu_data_json,
    menu_name_rest_list,
    ita_base_menu_flg=False):
    """
    import table and data(record, file)
        default menu:
            1. DELETE FROM
            2. Register record and Placement file
            transaction from 1 to 2
        parameter-sheets:
            1. DROP and CREATE TABLE,
            2. DROP and CREATE VIEW,
            3. Register record and Placement file
            transaction with 3
        - Execute DELETE TABLE , DROP and CREATE TABLE/VIEW when dp_mode 1
    Args:
    """

    rpt = RecordProcessingTimes()
    for record in menus_list:
        param = record['parameter']
        # menu_id = param.get('uuid')
        menu_id = param.get('menu_name')
        table_name = param.get('table_name')
        view_name = param.get('view_name')
        history_table_flag = param.get('history_table_flag')
        hostgroup_flag = param.get('hostgroup_flag')

        tmp_msg = "Target import record data: {}, {}, {}, {}".format(menu_id, table_name, view_name, history_table_flag)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        menu_name_rest = ''
        for menu_data_record in t_comn_menu_data_json:
            param = menu_data_record['parameter']
            tmp_menu_id = param.get('menu_id')
            if tmp_menu_id == menu_id:
                menu_name_rest = param.get('menu_name_rest')
                break

        if menu_name_rest not in menu_name_rest_list:
            # _dp_preparation()で既に処理していた場合はスキップする
            continue

        g.applogger.info(f"Target Menu: {menu_name_rest} START")

        # 環境移行モードの場合、uploadfiles配下のデータを削除する
        if dp_mode == '1':
            if table_name not in imported_table_list:
                if hostgroup_flag == "1" and table_name.endswith("_SV") and \
                    table_name.replace("_SV", "") in imported_table_list:
                    pass
                elif hostgroup_flag == "1" and table_name + "_SV" in imported_table_list:
                    pass
                else:
                    rpt.set_time(f"{menu_name_rest}: clear uploadfiles")
                    tmp_msg = "check information_schema.tables START: {}".format(table_name)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                    chk_table_sql = " SELECT TABLE_NAME FROM information_schema.tables WHERE `TABLE_NAME` = %s "
                    chk_table_rtn = objdbca.sql_execute(chk_table_sql, [table_name])

                    tmp_msg = "check information_schema.tables END: {}".format(table_name)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    if len(chk_table_rtn) != 0:
                        # uploadfiles配下のデータを削除する
                        if os.path.isdir(uploadfiles_dir + '/' + menu_id):
                            shutil.rmtree(uploadfiles_dir + '/' + menu_id)
                    rpt.set_time(f"{menu_name_rest}: clear uploadfiles")
            create_table_flg = True
        else:
            # 環境移行モードでテーブル有無の確認
            tmp_msg = "check information_schema.tables START: {}".format(table_name)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            chk_table_sql = " SELECT TABLE_NAME FROM information_schema.tables WHERE `TABLE_NAME` = %s "
            chk_table_rtn = objdbca.sql_execute(chk_table_sql, [table_name])
            create_table_flg = True if len(chk_table_rtn) == 0 else False

            tmp_msg = "check information_schema.tables END: {}".format(table_name)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # DBデータファイル読み込み
        db_data_path = execution_no_path + '/' + table_name + '.sql'
        jnl_db_data_path = execution_no_path + '/' + table_name + '_JNL.sql'

        # 環境移行モードの場合、データ削除実施, 環境移行モードでテーブル無しの場合テーブル作成
        if dp_mode == '1' or (dp_mode == '2' and create_table_flg):
            # 標準メニュー: DELETE TABLE -> データ登録までトランザクション
            # パラメータシート:  データ登録でトランザクション
            if table_name not in imported_table_list:
                if table_name.startswith('T_CMDB'):
                    tmp_msg = "DROP and CREATE TABLE START: {}".format(db_data_path)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    rpt.set_time(f"{menu_name_rest}: drop and create table")
                    # テーブルを作成
                    objdbca.sqlfile_execute(db_data_path)
                    rpt.set_time(f"{menu_name_rest}: drop and create table")
                    tmp_msg = "DROP and CREATE TABLE END: {}".format(db_data_path)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                    imported_table_list.append(table_name)
                    if os.path.isfile(jnl_db_data_path):
                        rpt.set_time(f"{menu_name_rest}: drop and create table jnl")
                        tmp_msg = "DROP and CREATE JNL START: {}".format(jnl_db_data_path)
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                        # 履歴テーブルを作成
                        objdbca.sqlfile_execute(jnl_db_data_path)
                        imported_table_list.append(table_name + '_JNL')

                        tmp_msg = "DROP and CREATE JNL END: {}".format(jnl_db_data_path)
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        rpt.set_time(f"{menu_name_rest}: drop and create table jnl")
                else:
                    if objdbca._is_transaction is False and ita_base_menu_flg is True:
                        # トランザクション開始
                        debug_msg = g.appmsg.get_log_message("BKY-20004", [])
                        g.applogger.info(debug_msg)
                        objdbca.db_transaction_start()

                    truncate_sql = "DELETE FROM {}".format(table_name)
                    rpt.set_time(f"{menu_name_rest}: delete table")
                    truncate_rtn = objdbca.sql_execute(truncate_sql, [])
                    rpt.set_time(f"{menu_name_rest}: delete table")
                    imported_table_list.append(table_name)
                    if os.path.isfile(jnl_db_data_path):
                        truncate_sql = "DELETE FROM {}".format(table_name + '_JNL')
                        rpt.set_time(f"{menu_name_rest}: delete table jnl")
                        truncate_rtn = objdbca.sql_execute(truncate_sql, [])
                        rpt.set_time(f"{menu_name_rest}: delete table jnl")
                        imported_table_list.append(table_name + '_JNL')

            if view_name:
                if table_name.startswith('T_CMDB'):
                    # 一度作成したview名は記憶する
                    if view_name not in tmp_table_list:
                        rpt.set_time(f"{menu_name_rest}: drop and create view")
                        tmp_table_list.append(view_name)

                        tmp_msg = "check information_schema.views START: {}".format(view_name)
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                        chk_view_sql = " SELECT TABLE_NAME FROM information_schema.views WHERE `TABLE_NAME` = %s "
                        chk_view_rtn = objdbca.sql_execute(chk_view_sql, [view_name])

                        tmp_msg = "check information_schema.views END: {}".format(view_name)
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        if len(chk_view_rtn) != 0:
                            tmp_msg = "DROP VIEW START: {}".format(view_name)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            drop_view_sql = "DROP VIEW IF EXISTS `{}`".format(view_name)
                            objdbca.sql_execute(drop_view_sql, [])

                            tmp_msg = "DROP VIEW END: {}".format(view_name)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                        # DBデータファイル読み込み
                        view_data_path = execution_no_path + '/' + view_name
                        if os.path.isfile(view_data_path):
                            tmp_msg = "CREATE VIEW START: {}".format(view_data_path)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            objdbca.sqlfile_execute(view_data_path)

                            tmp_msg = "CREATE VIEW END: {}".format(view_data_path)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                        rpt.set_time(f"{menu_name_rest}: drop and create view")

                        if history_table_flag == '1':
                            rpt.set_time(f"{menu_name_rest}: drop and create view jnl")
                            view_name_jnl = view_name + '_JNL'
                            tmp_msg = "check information_schema.views START: {}".format(view_name_jnl)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            chk_view_sql = " SELECT TABLE_NAME FROM information_schema.views WHERE `TABLE_NAME` = %s "
                            chk_view_rtn = objdbca.sql_execute(chk_view_sql, [view_name_jnl])

                            tmp_msg = "check information_schema.views END: {}".format(view_name_jnl)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            if len(chk_view_rtn) != 0:
                                tmp_msg = "DROP VIEW START: {}".format(view_name_jnl)
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                                drop_view_sql = "DROP VIEW IF EXISTS `{}`".format(view_name_jnl)
                                objdbca.sql_execute(drop_view_sql, [])

                                tmp_msg = "DROP VIEW END: {}".format(view_name_jnl)
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            # DBデータファイル読み込み
                            view_data_path = execution_no_path + '/' + view_name_jnl
                            if os.path.isfile(view_data_path):
                                tmp_msg = "CREATE VIEW START: {}".format(view_data_path)
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                                objdbca.sqlfile_execute(view_data_path)

                                tmp_msg = "CREATE VIEW END: {}".format(view_data_path)
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            rpt.set_time(f"{menu_name_rest}: drop and create view jnl")
                else:
                    pass

        if objdbca._is_transaction is False and ita_base_menu_flg is False:
            # トランザクション開始
            debug_msg = g.appmsg.get_log_message("BKY-20004", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_start()

        objmenu = load_table.loadTable(objdbca, menu_name_rest)
        if history_table_flag == '1':
            rpt.set_time(f"{menu_name_rest}:  register data jnl")
            objmenu = _register_history_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode)
            rpt.set_time(f"{menu_name_rest}:  register data jnl")
        rpt.set_time(f"{menu_name_rest}: register data")
        objmenu = _register_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode)
        rpt.set_time(f"{menu_name_rest}: register data")

        if objdbca._is_transaction:
            # コミット/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20005", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_end(True)
            objdbca._is_transaction = False

        g.applogger.info(f"Target Menu: {menu_name_rest} END")

class RecordProcessingTimes():
    def __init__(self) -> None:
        self.data = {}

    def start(self, key):
        self.data.setdefault(key, {})
        self.data[key].setdefault("start", time.perf_counter())

    def end(self, key):
        self.data.setdefault(key, {})
        self.data[key].setdefault("end", time.perf_counter())

    def set_time(self, key):
        try:
            self.data.setdefault(key, {})
            if "start" not in self.data[key]:
                self.start(key)
            elif "end" not in self.data[key]:
                self.end(key)
            if "start" in self.data[key] and "end" in self.data[key]:
                self.result(key)
        except:
            pass
    def result(self, key):
        try:
            if key in self.data and "start" in self.data[key] and "end" in self.data[key]:
                d_time = self.data[key]["end"] - self.data[key]["start"]
                res =f"{key}: {d_time}"
            elif key in self.data and "start" in self.data[key] and "end" not in self.data[key]:
                self.end(key)
                d_time = self.data[key]["end"] - self.data[key]["start"]
                res =f"{key}: {d_time}"
            else:
                res = f"{key}: Failed"
            g.applogger.info(res)  # noqa: F405
        except:
            res = None
        return res
