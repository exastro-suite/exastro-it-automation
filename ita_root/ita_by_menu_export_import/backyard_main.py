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
import pandas as pd
import csv
from io import StringIO
import textwrap
from packaging import version
from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.dbconnect.dbconnect_ws_sandbox import DBConnectWsSandbox  # noqa: F401
from common_libs.common.storage_access import *  # noqa: F403
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format
from common_libs.loadtable import *  # noqa: F403
from common_libs.column import *  # noqa: F403
from common_libs.migration import *  # noqa: F403
from libs.functions.util import *
from pathlib import Path
import shutil
import subprocess
import time
import inspect
import re
import traceback

ita_lb_menu_info = {
    'menu_list': "T_COMN_MENU",
    'menu_table_link_list': "T_COMN_MENU_TABLE_LINK",
    'menu_column_link_list': "T_COMN_MENU_COLUMN_LINK",
    'role_menu_link_list': "T_COMN_ROLE_MENU_LINK"
}

# ドライバー共通で使用するテーブル
clear_uploadfiles_exclusion = {
    "10102": "T_COMN_MENU_GROUP"
}
clear_uploadfiles_exclusion_list = list(clear_uploadfiles_exclusion.keys())

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
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
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

        db_reconnention(objdbca, True) if objdbca else None
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

        # query length for show variables
        _sql = "show variables like 'max_allowed_packet';"
        _show_variables = objdbca.sql_execute(_sql)
        max_allowed_packet = _show_variables["max_allowed_packet"] if "max_allowed_packet" in _show_variables else 30000
        g.max_allowed_packet = max_allowed_packet

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
        g.applogger.info(f"{menu_name_rest_list=}")

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

        # KYMとITAのバージョン＋ドライバ情報取得、処理分岐
        import_info = get_import_config(execution_no_path)
        kym_version = import_info['kym_version']
        if import_info["import_mode"] == "same":
            # 同一バージョンへのインポート
            g.applogger.info(f"Import to same version({dp_mode=}:{kym_version=})")
            try:
                menu_import_exec_same_version(
                    objdbca,
                    workspace_id,
                    uploadfiles_dir,
                    rpt,
                    dp_mode,
                    menu_id_list,
                    menu_name_rest_list,
                    execution_no_path
                )
                pass
            except Exception as e:
                trace_msg = traceback.format_exc()
                g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
                raise e
        elif import_info["import_mode"] == "diff":

            # バージョン差分ありのインポート処理
            g.applogger.info(f"Import with version differences({dp_mode=})")
            try:
                menu_import_exec_difference_version(
                    objdbca,
                    import_info,
                    workspace_id,
                    uploadfiles_dir,
                    rpt,
                    dp_mode,
                    menu_id_list,
                    menu_name_rest_list,
                    execution_no_path
                )
            except Exception as e:
                trace_msg = traceback.format_exc()
                g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
                raise e

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
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        g.applogger.info(f"{record=}")
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
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        g.applogger.info(f"{record=}")

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


def _dp_preparation(objdbca, workspace_id, menu_name_rest_list, execution_no_path, imported_table_list, dp_mode, file_put_flg=True):
    tmp_msg = '_dp_preparation START: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # load_table.loadTableを使用するため特定のメニュー
    _base_menu_list = ['menu_list', 'menu_table_link_list', 'menu_column_link_list', 'role_menu_link_list']
    for _menu_name in _base_menu_list:
        if _menu_name in menu_name_rest_list:
            g.applogger.info(f"Target Menu: {_menu_name} START")

            # トランザクション開始
            db_reconnention(objdbca, True) if objdbca else None
            debug_msg = g.appmsg.get_log_message("BKY-20004", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_start()

            objmenu, file_path_info = _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, _menu_name, execution_no_path, imported_table_list, dp_mode)

            # コミット/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20005", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_end(True)

            # ファイル配置
            if file_put_flg:
                if _menu_name + '_JNL' in file_path_info:
                    _bulk_register_file(objdbca, objmenu, execution_no_path, _menu_name + '_JNL', file_path_info)
                if _menu_name in file_path_info:
                    _bulk_register_file(objdbca, objmenu, execution_no_path, _menu_name, file_path_info)

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

    file_info_list = {}
    if history_table_flag == '1':
        if dp_mode == '1':
            rpt.set_time(f"{menu_name_rest}: delete table jnl")
            delete_jnl_sql = "DELETE FROM {}".format(table_name + '_JNL')
            rpt.set_time(f"{menu_name_rest}: delete table jnl")
            objdbca.sql_execute(delete_jnl_sql, [])
        imported_table_list.append(table_name + '_JNL')
        rpt.set_time(f"{menu_name_rest}: register data jnl")
        objmenu, file_info_list[menu_name_rest + '_JNL' ] = _bulk_register_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest + '_JNL', menu_id, table_name + "_JNL", dp_mode)
        rpt.set_time(f"{menu_name_rest}: register data jnl")

    if dp_mode == '1':
        rpt.set_time(f"{menu_name_rest}: delete table")
        delete_sql = "DELETE FROM {}".format(table_name)
        objdbca.sql_execute(delete_sql, [])
        rpt.set_time(f"{menu_name_rest}: delete table")
    imported_table_list.append(table_name)
    rpt.set_time(f"{menu_name_rest}: register data")
    objmenu, file_info_list[menu_name_rest] = _bulk_register_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode)
    rpt.set_time(f"{menu_name_rest}: register data")

    menu_name_rest_list.remove(menu_name_rest)

    tmp_msg = '_basic_table_preparation END: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    return objmenu, file_info_list


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
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
            g.applogger.info(f"{execution_no=}, {status=}")
        objdbca.table_update(t_menu_export_import, data_list, 'EXECUTION_NO')

        # ログファイルの書き込み
        if file_path and error_msg and "EXEC_LOG" in data_list:
            file_open_write_close(file_path, 'w', error_msg)

    except Exception as msg:
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
        g.applogger.info(f"{execution_no=}, {status=}")
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


def _bulk_register_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode="1"):
    """
        インポート一括処理用
        ARGS:
            objdbca: DBConnectWs()
            objmenu: load_table.bulkLoadTable()
            workspace_id: workspace_id
            execution_no_path: 一時作業用: /tmp/<execution_no>
            menu_name_rest: menu_name_rest
            menu_id: menu_id
            table_name: table_name
            dp_mode: 1: 環境移行 / 2:時刻指定
        RETURN:
            objmenu
    """
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    organization_id = g.get("ORGANIZATION_ID")
    workspace_id = g.get("WORKSPACE_ID")

    pk = objmenu.get_primary_key()

    file_info_list = []
    ita_lb_mnr_list = [
        'menu_list',
        'menu_table_link_list',
        'menu_column_link_list',
    ]
    if objmenu.menu in ita_lb_mnr_list and dp_mode == "2" and not table_name.endswith("_JNL"):
        # 時刻指定でLoadTable系メニューの場合、「<table_name>_DATA」を使用
        data_file_name = f"{ita_lb_menu_info[objmenu.menu]}_DATA"
        # DATAファイル確認
        if os.path.isfile(execution_no_path + '/' + data_file_name) is False:
            # 対象ファイルなし
            raise AppException("MSG-140003", [data_file_name], [data_file_name])

        # DATAファイル読み込み
        sql_data = file_open_read_close(execution_no_path + '/' + data_file_name)
        json_sql_data = json.loads(sql_data)
        g.applogger.debug(addline_msg('{}'.format(f"{menu_name_rest}, {table_name}, {len(json_sql_data)}")))  # noqa: F405

        # _DATAファイルの追加
        _json_sql_data = []
        if os.path.isfile(execution_no_path + '/' + menu_name_rest) is True:
            # DATAファイル読み込み
            sql_data = file_open_read_close(execution_no_path + '/' + menu_name_rest)
            _json_sql_data = json.loads(sql_data)
            g.applogger.debug(addline_msg('{}'.format(f"{menu_name_rest}, {table_name}, {len(_json_sql_data)}")))  # noqa: F405
        if len(_json_sql_data) != 0:
            ret_t_comn_menu_column_link = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COL_NAME = %s', [menu_id, pk])  # noqa: E501
            pk_name = ret_t_comn_menu_column_link[0].get('COLUMN_NAME_REST') if len(ret_t_comn_menu_column_link) != 0 \
                else None
            if pk_name:
                _id_list =  [jsd["parameter"].get(pk_name) for jsd in json_sql_data if "parameter" in jsd]
                [json_sql_data.append(_jsd) for _jsd in _json_sql_data if "parameter" in _jsd and _jsd["parameter"][pk_name] not in _id_list]
    else:
        # DATAファイル確認
        if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
            # 対象ファイルなし
            raise AppException("MSG-140003", [menu_name_rest], [menu_name_rest])

        # DATAファイル読み込み
        sql_data = file_open_read_close(execution_no_path + '/' + menu_name_rest)
        json_sql_data = json.loads(sql_data)
        g.applogger.debug(addline_msg('{}'.format(f"{menu_name_rest}, {table_name}, {len(json_sql_data)}")))  # noqa: F405
        if len(json_sql_data) == 0:
            g.applogger.info(f"{menu_name_rest}: recode 0.")
            return objmenu, file_info_list

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


    # 環境移行、パラメータシートの場合
    if dp_mode == '1' and table_name.startswith('T_CMDB'):
        chk_pk_sql = "SELECT COUNT(*) FROM `" + table_name + "` ;"
        chk_pk_record = objdbca.sql_execute(chk_pk_sql, [])
        record_count = list(chk_pk_record[0].values())[0]
        # 同一テーブルで処理済みの場合、SKIP
        if record_count == 0 and len(json_sql_data) == 0:
            g.applogger.info(f"{menu_name_rest}: target 0. ")
            return objmenu, file_info_list
        elif record_count != 0 and record_count == len(json_sql_data):
            g.applogger.info(f"{menu_name_rest}: already imported. ")
            return objmenu, file_info_list

    # rest_name -> column_name変換 + 値変換対応(PasswordColumn、ロール名)
    _json_p_data = []
    _json_f_data = []
    pk_name = None
    delete_ids = []
    chk_pk_sql = f" SELECT * FROM `{table_name}`"
    chk_pk_record = objdbca.sql_execute(chk_pk_sql, [])
    for json_record in json_sql_data:
        file_param = json_record['file']
        param = json_record['parameter']

        # 移行先に主キーの重複データが既に存在するか確認
        if dp_mode == "2" and table_name.endswith("_JNL"):
            journal_id = param['journal_id']
            if len(chk_pk_record) != 0:
                _chk_pk_record = [_ck for _ck in chk_pk_record if journal_id == _ck["JOURNAL_SEQ_NO"]]
                # 主キーが重複する場合は既存データを削除してからINSERTする
                if len(_chk_pk_record) == 1:
                    delete_ids.append(journal_id)
        elif dp_mode == "2":
            if pk_name is None:
                # 移行先に主キーの重複データが既に存在するか確認
                ret_t_comn_menu_column_link = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COL_NAME = %s', [menu_id, pk])  # noqa: E501
                pk_name = ret_t_comn_menu_column_link[0].get('COLUMN_NAME_REST')

            pk_value = param[pk_name]
            if len(chk_pk_record) != 0:
                # 主キーが重複する場合は既存データを削除してからINSERTする
                _chk_pk_record = [_ck for _ck in chk_pk_record if pk_value == _ck[pk]]
                if len(_chk_pk_record) == 1:
                    delete_ids.append(pk_value)

        param['last_update_date_time'] = get_timestamp().strftime('%Y/%m/%d %H:%M:%S.%f')
        param['last_updated_user'] = g.USER_ID

        # PasswordColumn, ロール名置換対象の場合
        replace_role_menus = ['role_menu_link_list', 'menu_role_creation_info', 'role_menu_link_list_JNL', 'menu_role_creation_info_JNL']
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

        _json_p_data.append(colname_parameter[0])
        _json_f_data.append(
            {
                "file": json_record.get("file") if isinstance(json_record.get("file"), dict) else {},
                "file_path": json_record.get("file_path") if isinstance(json_record.get("file_path"), dict) else {}
            }
        )

    if delete_ids != []:
        # 主キーが重複する場合は既存データを削除してからINSERTする
        _pk = "JOURNAL_SEQ_NO" if table_name.endswith("_JNL") else pk
        _ids = delete_ids
        n = int(len(_ids)) if g.max_allowed_packet >= 40 * len(_ids) else int(g.max_allowed_packet / 40)
        for i in range(0, len(_ids), n):
            _prepared_list = ','.join(list(map(lambda a: "%s", _ids[i: i+n])))
            delete_table_sql = f"DELETE FROM `{table_name}` WHERE `{_pk}` in ({_prepared_list})"
            g.applogger.debug(f"{delete_table_sql} {_ids[i: i+n]}")
            objdbca.sql_execute(delete_table_sql, _ids[i: i+n])

    # LOAD DATA LOCAL INFILE用CSV変換
    try:
        _tmp_dir = f"{execution_no_path}/_tmp"
        os.makedirs(_tmp_dir, exist_ok=True)  if not os.path.isdir(_tmp_dir) else None
        json_path = f"{_tmp_dir}/{table_name}.json"
        csv_path = f"/{_tmp_dir}/{table_name}.csv"
        g.applogger.debug(f"{os.path.isdir(_tmp_dir)} {_tmp_dir=}")

        with open(json_path, 'w') as f :
            json.dump(_json_p_data, f, ensure_ascii=False, indent=4)
        json_open = open(json_path, 'r')
        json_data = json.dumps(json.load(json_open)).replace(r'\\',r'\\\\')

        get_column_sql = f"SHOW COLUMNS FROM `{table_name}`"
        columns_row = objdbca.sql_execute(get_column_sql)
        column_type = {_r["Field"]:_r["Type"] for _r in columns_row}
        column_list = list(column_type.keys())
        # 予期せぬ小数点付きの値への対応
        dtyp = {}
        for ck, cv in column_type.items():
            dtyp[ck] = "object"

        df = pd.read_json(StringIO(json_data), orient='records', dtype=dtyp)
        df = df.where(df.notnull(), None)
        g.applogger.debug(df.dtypes)
        g.applogger.debug(df)
        df.to_csv(csv_path, index=False)
        csv_header = list(pd.read_csv(csv_path, header=0).columns)
        target_fields = [ck for ck in csv_header if ck in column_list]

        # LOAD DATA LOCAL INFILE
        query_str = textwrap.dedent("""
            LOAD DATA LOCAL INFILE  '{csv_path}'
            INTO TABLE `{table_name}`
            FIELDS TERMINATED BY ','
            ENCLOSED BY '"'
            LINES TERMINATED BY '\n'
            IGNORE 1 ROWS
        """).format(csv_path=csv_path, table_name=table_name).strip()

        # add (Colmun,,,,) & add SET Colmun = NULLIF(@{Colmun}, '')
        set_column_str = "\n("
        for ck in target_fields:
            set_column_str = set_column_str +f"@{ck}, \n"
        set_column_str = set_column_str[:-3]
        set_column_str = set_column_str + ")\n"
        set_column_str = set_column_str + "SET\n"
        for ck in target_fields:
            set_column_str = set_column_str + f"{ck} =  NULLIF(@{ck}, ''),"
        set_column_str = set_column_str[:-1]
        query_str = query_str + set_column_str

        g.applogger.debug(query_str)  # noqa: F405
        objdbca.sql_execute(query_str)

    except Exception as e:
        trace_msg = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        raise e
    finally:
        os.remove(csv_path) if os.path.isfile(csv_path) else None
        os.remove(json_path) if os.path.isfile(json_path) else None
        file_info_list = _json_f_data

    return objmenu, file_info_list


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
        journal_type = json_storage_item.get('journal_type', "1")

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
        file_open_write_close(menus_data_path, 'w', json.dumps(menus_data, indent=4))

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
        file_open_write_close(parent_menus_data_path, 'w', json.dumps(menu_group_id_dict, indent=4))

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
            # objmenu = load_table.loadTable(objdbca, menu)   # noqa: F405
            db_reconnention(objdbca, True) if objdbca else None
            objmenu = load_table.bulkLoadTable(objdbca, menu)   # noqa: F405
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

            g.applogger.info(addline_msg('{}'.format(f'{menu}')))
            filter_mode = 'export'
            status_code, result, msg = objmenu.rest_export_filter(filter_parameter, filter_mode, abolished_type, journal_type)
            if status_code != '000-00000':
                log_msg_args = [msg]
                api_msg_args = [msg]
                raise AppException(status_code, log_msg_args, api_msg_args)

            # 履歴テーブル
            db_reconnention(objdbca, True) if objdbca else None
            objmenu = load_table.bulkLoadTable(objdbca, menu)   # noqa: F405
            history_flag = objmenu.get_objtable().get('MENUINFO').get('HISTORY_TABLE_FLAG')
            if history_flag == '1':
                filter_mode = 'export_jnl'
                g.applogger.info(addline_msg('{}'.format(f'{menu+ "_JNL"}')))
                # 廃止を含まない場合、本体のテーブルの廃止状態を確認してデータ取得
                status_code, result_jnl, msg = objmenu.rest_export_filter(filter_parameter_jnl, filter_mode, abolished_type, journal_type)
                if status_code != '000-00000':
                    log_msg_args = [msg]
                    api_msg_args = [msg]
                    raise AppException(status_code, log_msg_args, api_msg_args)

            # データ配置、ファイル収集
            DB_path = dir_path + '/' + menu
            _collect_files(objmenu, dir_path, menu, result)
            file_open_write_close(DB_path, 'w', json.dumps(result, ensure_ascii=False, indent=4))

            if history_flag == '1':
                DB_path = dir_path + '/' + menu + '_JNL'
                _collect_files(objmenu, dir_path, menu + '_JNL', result_jnl)
                file_open_write_close(DB_path, 'w', json.dumps(result_jnl, ensure_ascii=False, indent=4))

        # 対象のDBのテーブル定義を出力（sqldump用
        db_reconnention(objdbca, True) if objdbca else None
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
        # objmenu = load_table.loadTable(objdbca, 'menu_list')   # noqa: F405
        objmenu = load_table.bulkLoadTable(objdbca, 'menu_list')   # noqa: F405
        filter_parameter = {"discard": {"LIST": ["0"]}, "menu_name_rest": {"LIST": menu_list}}
        filter_mode = 'export'
        status_code, result, msg = objmenu.rest_export_filter(filter_parameter, filter_mode)
        if status_code != '000-00000':
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException(status_code, log_msg_args, api_msg_args)
        file_open_write_close(t_comn_menu_data_path, 'w', json.dumps(result, ensure_ascii=False, indent=4))

        # インポート時に利用するMENU_NAME_REST_LISTを作成する
        menu_name_rest_list = ",".join(menu_list)
        menu_name_rest_path = dir_path + '/MENU_NAME_REST_LIST'
        file_open_write_close(menu_name_rest_path, 'w', menu_name_rest_list)

        # インポート時に利用するT_COMN_MENU_TABLE_LINK_DATAを作成する
        t_comn_menu_table_link_data_path = dir_path + '/T_COMN_MENU_TABLE_LINK_DATA'
        # objmenu = load_table.loadTable(objdbca, 'menu_table_link_list')   # noqa: F405
        objmenu = load_table.bulkLoadTable(objdbca, 'menu_table_link_list')   # noqa: F405
        filter_parameter = {"discard": {"LIST": ["0"]}, "uuid": {"LIST": table_definition_id_list}}
        filter_mode = 'export'
        status_code, result, msg = objmenu.rest_export_filter(filter_parameter, filter_mode)
        if status_code != '000-00000':
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException(status_code, log_msg_args, api_msg_args)
        file_open_write_close(t_comn_menu_table_link_data_path, 'w', json.dumps(result, ensure_ascii=False, indent=4))

        # インポート時に利用するT_COMN_MENU_COLUMN_LINK_DATAを作成する
        t_comn_menu_column_link_data_path = dir_path + '/T_COMN_MENU_COLUMN_LINK_DATA'
        objmenu = load_table.bulkLoadTable(objdbca, 'menu_column_link_list')   # noqa: F405
        result = get_t_comn_menu_column_link(objdbca, objmenu, menu_id_list)
        file_open_write_close(t_comn_menu_column_link_data_path, 'w', json.dumps(result, ensure_ascii=False, indent=4))

        # アップロード時に利用するDP_INFOファイルを作成する
        dp_info = {
            "DP_MODE": mode,
            "ABOLISHED_TYPE": abolished_type,
            "JOURNAL_TYPE": journal_type,
            "SPECIFIED_TIMESTAMP": specified_time
        }
        dp_info_path = dir_path + '/DP_INFO'
        file_open_write_close(dp_info_path, 'w', json.dumps(dp_info, indent=4))

        # ロール-メニュー紐付管理のロール置換用にエクスポート時のWORKSPACE_IDを確保しておく
        workspace_id_path = dir_path + '/WORKSPACE_ID'
        file_open_write_close(workspace_id_path, 'w', workspace_id)

        # アップロード時のバージョン差異チェック用にエクスポート時のVERSIONを確保しておく
        common_db = DBConnectCommon()
        version_data = get_ita_version(common_db)
        version_path = dir_path + '/VERSION'
        file_open_write_close(version_path, 'w', version_data["version"])
        common_db.db_disconnect()

        # エクスポート環境のドライバ情報をDRIVERSに確保しておく
        installed_driver_path = dir_path + '/DRIVERS'
        ita_drivers = list(version_data["installed_driver_en"].keys())
        no_installed_driver = version_data["no_installed_driver"] if "no_installed_driver" in version_data else []
        [ita_drivers.remove(nid) for nid in no_installed_driver if nid in ita_drivers]
        installed_driver_list = json.dumps(ita_drivers, indent=4)
        file_open_write_close(installed_driver_path, 'w', installed_driver_list)

        # エクスポート環境のワークスペースDB(SQL)を確保しておく
        wsdb_sql_path = f"{os.getenv('PYTHONPATH')}sql"
        expoet_db_sql_path = dir_path + '/sql'
        if os.path.isdir(wsdb_sql_path):
            shutil.copytree(wsdb_sql_path, expoet_db_sql_path)

        # インポート環境で対応が必要なメニュー-カラム-カラムクラスを確保しておく
        # 暗号化、ファイル配置、ロール置換
        action_column_info = _collect_action_column_class(objdbca)
        installed_driver_path = dir_path + '/ACTION_COLUMN_LIST'
        installed_driver_list = json.dumps(action_column_info, indent=4)
        file_open_write_close(installed_driver_path, 'w', installed_driver_list)

        # データをtar.gzにまとめる
        gztar_path = dir_path + '.tar.gz'
        with tarfile.open(gztar_path, 'w:gz') as tar:
            tar.add(dir_path, arcname="")

        # kymファイルに変換(拡張子変更)
        kym_name = dir_name + '.kym'
        kym_path = export_menu_dir + '/' + kym_name
        shutil.move(gztar_path, kym_path)

        # tmpに作成したデータは削除する
        shutil.rmtree(dir_path)

        db_reconnention(objdbca, True) if objdbca else None

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
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        g.applogger.info(f"{record=}, {workspace_id=}, {export_menu_dir=}")
        trace_msg = None

        # エラー時はtmpの作業ファイルを削除する
        if os.path.isdir(export_menu_dir):
            shutil.rmtree(export_menu_dir)
        # 異常系リターン
        return False, msg, trace_msg
    except Exception as msg:
        trace_msg = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        g.applogger.info(f"{record=}, {workspace_id=}, {export_menu_dir=}")

        # エラー時はtmpの作業ファイルを削除する
        if os.path.isdir(export_menu_dir):
            shutil.rmtree(export_menu_dir)

        # 異常系リターン
        return False, msg, trace_msg

def _collect_files(objmenu, dir_path, menu, parameters):
    """ Copy file or decrypt the file and place
            FileUploadColumn
            FileUploadEncryptColumn
    Args:
        objmenu (object): loadtable
        dir_path (str): workdir path
        menu (str): menu_name_rest
        parameters (list): parameter, [{"parameter":{}, "file":{}, "file_path":{}}]
    """
    # ファイルアップロード系の項目
    fileup_columns = [_k for _k in objmenu.restkey_list if objmenu.get_col_class_name(_k) in ["FileUploadColumn", "FileUploadEncryptColumn"]]
    if fileup_columns == []:
        #  ファイルアップロード系がない場合、終了
        g.applogger.debug(addline_msg('{}'.format(f'FileUploadColumn does not exist, so it will be skipped')))
        return

    _files_path =  f"{dir_path}"
    g.applogger.info(addline_msg('{}'.format(f"{menu} {len(parameters)}, {fileup_columns}")))
    for _p in parameters:
        for _pk in fileup_columns:
            _pd =  _p["file_path"].get(_pk)
            _cnt = list(set(_pd.values())) if _pd is not None else []
            if len(_cnt) == 0 or (len(_cnt) == 1 and None in _cnt):
                # 対象ファイルがない場合SKIP
                g.applogger.debug(addline_msg('{}'.format(f'target file does not exist, so it will be skipped')))
                continue
            tmp_file_path = f"{_files_path}{_pd['src']}"
            tmp_dir_path = tmp_file_path.replace(_pd['name'], "")
            entity_path = _pd["ori_src"] if _pd["entity"] == "" else _pd["entity"]

            if os.path.isfile(tmp_file_path):
                # 配置済みの場合SKIP
                g.applogger.debug(addline_msg('{}'.format(f'File does not exist: {tmp_file_path} ')))
                continue

            # ファイルをコピー or 複合化して配置
            os.makedirs(tmp_dir_path, exist_ok=True)
            g.applogger.debug(addline_msg('{}'.format(f'{_pd["class_name"]} {entity_path} {tmp_file_path}')))
            g.applogger.debug(addline_msg('{}'.format(f'Copy src file. {os.path.isfile(entity_path)} {entity_path}')))
            if _pd['class_name'] == "FileUploadColumn":
                shutil.copyfile(entity_path, tmp_file_path)
            elif _pd['class_name'] == "FileUploadEncryptColumn":
                file_decode_upload_file(entity_path, tmp_file_path)
            g.applogger.debug(addline_msg('{}'.format(f'Copy dst file. {os.path.isfile(tmp_file_path)} {tmp_file_path}')))


def _collect_action_column_class(objdbca):
    """
    追加処理ありのカラムクラスの取得
        Role関連
            18: "RoleIDColumn"
        暗号化処理関連
            8:  "PasswordColumn"
            16: "SensitiveSingleTextColumn"
            17: "SensitiveMultiTextColumn"
        ファイル関連
            9:  "FileUploadColumn"
            20: "FileUploadEncryptColumn"
    """
    query_str = textwrap.dedent("""
        SELECT
            TAB_B.`MENU_NAME_REST`,
            TAB_A.`COLUMN_NAME_REST`,
            TAB_C.`COLUMN_CLASS_NAME`
        FROM
            `T_COMN_MENU_COLUMN_LINK` TAB_A
        JOIN `T_COMN_MENU` TAB_B ON
            (TAB_A.`MENU_ID` = TAB_B.`MENU_ID`)
        JOIN `T_COMN_COLUMN_CLASS` TAB_C ON
            (
                TAB_A.`COLUMN_CLASS` = TAB_C.`COLUMN_CLASS_ID`
            )
        WHERE
            TAB_A.`DISUSE_FLAG` = 0
        AND TAB_B.`DISUSE_FLAG` = 0
        AND TAB_A.`COLUMN_CLASS` IN ('18', '8', '16', '17', '9', '20')
        ;
    """).format().strip()

    ret = objdbca.sql_execute(query_str)
    result ={}
    for _r in ret:
        result.setdefault(_r["MENU_NAME_REST"],{})
        result[_r["MENU_NAME_REST"]].setdefault(_r["COLUMN_NAME_REST"], _r["COLUMN_CLASS_NAME"])
    return result


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
        trace_msg = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        g.applogger.info(f"{path=}, {mode=}, {encoding=} {file_del=}")
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
        trace_msg = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        g.applogger.info(f"{path=}, {encoding=}")
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
    file_path_info={},
    file_put_flg=True,
    ita_base_menu_flg=False,
    ws_db_sb=None,
    ):
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
        objdbca: DBConnectWs()
        dp_mode: 1: clear table [環境移行] / 2: duplicate record override [時刻指定]
        workspace_id: workspace_id
        uploadfiles_dir:  /storage/organization_id/workspace_id/uploadfiles
        execution_no_path: /tmp/execution_no
        menus_list: read & json.loads() /T_COMN_MENU_TABLE_LINK_DATA
        imported_table_list: imported table list
        tmp_table_list:  created view list
        t_comn_menu_data_json: read & json.loads() /T_COMN_MENU_DATA
        menu_name_rest_list: record["JSON_STORAGE_ITEM"]
        file_path_info={},
        ita_base_menu_flg=False,
        ws_db_sb=None

    Return:
        file_path_info: { menu_name_rest: [ file: {}, file_path {}] }
    """

    rpt = RecordProcessingTimes()
    for record in menus_list:
        db_reconnention(objdbca) if objdbca else None
        db_reconnention(ws_db_sb) if ws_db_sb else None
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
                            shutil.rmtree(uploadfiles_dir + '/' + menu_id) \
                                if menu_id not in clear_uploadfiles_exclusion_list else None
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
                        db_reconnention(objdbca, True) if objdbca else None
                        db_reconnention(ws_db_sb, True) if ws_db_sb else None
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
            db_reconnention(objdbca, True) if objdbca else None
            db_reconnention(ws_db_sb, True) if ws_db_sb else None
            debug_msg = g.appmsg.get_log_message("BKY-20004", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_start()

        # 0件なら次へ
        objmenu = None
        # loadTable() for objdbcaの接続先 / インポート用一時作業DB(ita_sd_*)
        if ws_db_sb is None:
            objmenu = load_table.loadTable(objdbca, menu_name_rest)
        else:
            objmenu = load_table.loadTable(ws_db_sb, menu_name_rest)
        if get_record_count(execution_no_path, menu_name_rest) != 0:
            if history_table_flag == '1':
                rpt.set_time(f"{menu_name_rest}:  register data jnl")
                if ws_db_sb is None:
                    # objdbcaの接続先にインポート[KYMのデータから]
                    objmenu, file_path_info[menu_name_rest + '_JNL'] = _bulk_register_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest + '_JNL', menu_id, table_name + "_JNL", dp_mode)
                else:
                    # ワークスペースのDB(ita_ws_*)にインポート[インポート用の一時作業DB(ita_sd_*)から]
                    objmenu, file_path_info[menu_name_rest + '_JNL'] = _export_sandboxdb_bulk_register_maindb(objdbca, ws_db_sb, objmenu, workspace_id, execution_no_path, menu_name_rest + '_JNL', menu_id, table_name + "_JNL", file_path_info, dp_mode)
                rpt.set_time(f"{menu_name_rest}:  register data jnl")
            rpt.set_time(f"{menu_name_rest}: register data")
            if ws_db_sb is None:
                # objdbcaの接続先にインポート[KYMのデータから]
                objmenu, file_path_info[menu_name_rest] = _bulk_register_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, dp_mode)
            else:
                # ワークスペースのDB(ita_ws_*)にインポート[インポート用の一時作業DB(ita_sd_*)から]
                objmenu, file_path_info[menu_name_rest + '_JNL'] = _export_sandboxdb_bulk_register_maindb(objdbca, ws_db_sb, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, file_path_info, dp_mode)
            rpt.set_time(f"{menu_name_rest}: register data")
        else:
            g.applogger.info(f"{menu_name_rest} import recode 0.")

        if objdbca._is_transaction:
            # コミット/トランザクション終了
            debug_msg = g.appmsg.get_log_message("BKY-20005", [])
            g.applogger.info(debug_msg)
            objdbca.db_transaction_end(True)
            objdbca._is_transaction = False

        # ファイル配置
        if file_put_flg and objmenu:
            if menu_name_rest + '_JNL' in file_path_info:
                _bulk_register_file(objdbca, objmenu, execution_no_path, menu_name_rest + '_JNL', file_path_info)
            if menu_name_rest in file_path_info:
                _bulk_register_file(objdbca, objmenu, execution_no_path, menu_name_rest, file_path_info)

        g.applogger.info(f"Target Menu: {menu_name_rest} END")

    return file_path_info

def file_decode_upload_file(src_path, dst_path):
    """
    Decrypt and place encrypted files

    Arguments:
        src_path: Decode target filepath
        dst_path: output target filepath
    Returns:
        dst_path string
    """
    is_file = os.path.isfile(src_path)
    if not is_file:
        return ""

    # #2079 /storage配下は/tmpを経由してアクセスする
    obj = storage_base()
    storage_flg = obj.path_check(src_path)
    if storage_flg is True:
        # /storage
        tmp_file_path = obj.make_temp_path(src_path)
        # /storageから/tmpにコピー
        shutil.copy2(src_path, tmp_file_path)
    else:
        # not /storage
        tmp_file_path = src_path

    with open(tmp_file_path, "rb") as f:
        text = f.read().decode()
    f.close()

    if storage_flg is True:
        # /tmpゴミ掃除
        if os.path.isfile(tmp_file_path) is True:
            os.remove(tmp_file_path)

    text_decrypt = ky_decrypt(text)

    upload_file(dst_path, base64.b64encode(text_decrypt.encode()).decode(), mode="bw")

    return dst_path

def get_t_comn_menu_column_link(objdbca, objmenu, menu_id_list):
    """T_COMN_MENU_COLUMN_LINK_DATAを作成
    Args:
        objdbca (_type_): DBConnectWs()
        objmenu (_type_):  load_table.bulkLoadTable()
        menu_id_list (_type_): menu_id list selected when exporting
    """
    _prepared_list = ','.join(list(map(lambda a: "%s", menu_id_list)))
    str_where = f"WHERE `DISUSE_FLAG` = '0' "
    str_where = f"{str_where} AND `MENU_ID` in ({_prepared_list})" \
        if len(menu_id_list) != 0 else f"{str_where}"
    tmp_result = objdbca.table_select(objmenu.get_table_name(), str_where, menu_id_list)
    primary_key = objmenu.get_primary_key()
    result =[]
    # RESTパラメータへキー変換
    for rows in tmp_result:
        target_uuid = rows.get(primary_key)
        target_uuid_jnl = rows.get("JOURNAL_SEQ_NO")
        filter_mode = 'export'
        rest_parameter, rest_file, rest_file_path = objmenu.convert_colname_restkey(
            rows, target_uuid, target_uuid_jnl, filter_mode)
        result.append(
            {
                'parameter': rest_parameter,
                'file': rest_file,
                'file_path': rest_file_path
            }
        )
    return result

def menu_import_exec_same_version(
    objdbca,
    workspace_id,
    uploadfiles_dir,
    rpt,
    dp_mode,
    menu_id_list,
    menu_name_rest_list,
    execution_no_path):

    """
        同一バージョンへのインポート処理
        (KYM -> workspace db Import)

        ARGS:
            objdbca: DBConnectWs()
            workspace_id: workspace_id
            uploadfiles_dir:  /storage/<organization_id>/<workspace_id>/uploadfiles
            rpt: RecordProcessingTimes()
            dp_mode: 1: clear table [環境移行] / 2: duplicate record override [時刻指定]
            menu_id_list: [menu_id]
            menu_name_rest_list: record["JSON_STORAGE_ITEM"]
            execution_no_path: /tmp/<execution_no>
    """

    if dp_mode == '1':
        for menu_id in menu_id_list:
            menu_dir = uploadfiles_dir + '/' + menu_id
            # ディレクトリ存在チェック
            if os.path.isdir(menu_dir) is True:
                shutil.rmtree(menu_dir)

    # 環境移行にて削除したテーブル名を記憶する用
    imported_table_list = []
    db_reconnention(objdbca) if objdbca else None
    # load_table.loadTableを使用するため特定のメニューは事前に処理しておく
    _dp_preparation(objdbca, workspace_id, menu_name_rest_list, execution_no_path, imported_table_list, dp_mode)
    db_reconnention(objdbca) if objdbca else None
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
        {},
        file_put_flg=True,
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
        {},
        file_put_flg=True,
        ita_base_menu_flg=False
    )
    rpt.set_time("import: ita_create_menus ")

def menu_import_exec_difference_version(
    objdbca,
    import_info,
    workspace_id,
    uploadfiles_dir,
    rpt,
    dp_mode,
    menu_id_list,
    menu_name_rest_list,
    execution_no_path):

    """
        バージョン違いのインポート処理
        (KYM -> sandbox db Import -> (migrate) -> workspace db Import -> (migrate) )
            create sandboxdb & connect sandboxdb: execute workspace create sql
            import kym -> sandboxdb
            migrate sandboxdb(sql)
            import sandboxdb -> workspacedb: LOAD DATA LOCAL INFILE
            migrate workspace(file)
            migrate workspace(specific)
            delete sandboxdb
        ARGS:
            objdbca: DBConnectWs()
            import_info: get_import_config()
            workspace_id: workspace_id
            uploadfiles_dir:  /storage/<organization_id>/<workspace_id>/uploadfiles
            rpt: RecordProcessingTimes()
            dp_mode: 1: clear table [環境移行] / 2: duplicate record override [時刻指定]
            menu_id_list: [menu_id]
            menu_name_rest_list: record["JSON_STORAGE_ITEM"]
            execution_no_path: /tmp/<execution_no>
    """
    try:
        # create & connect sandboxdb
        connect_info, ws_db_sb = preparation_sandbox_workspace(workspace_id)
        file_path_info = {}

        # import kym->sandboxdb
        file_path_info = sandbox_workspace_menu_import(
            ws_db_sb,
            workspace_id,
            uploadfiles_dir,
            rpt,
            dp_mode,
            menu_name_rest_list,
            execution_no_path)

        # migrate db
        exec_ws_migration(import_info, ws_db_sb, "db")

        # import sandboxdb - >workspacedb: LOAD DATA LOCAL INFILE
        import_from_sandbox_to_maindb(
            objdbca,
            ws_db_sb,
            workspace_id,
            uploadfiles_dir,
            rpt,
            dp_mode,
            menu_id_list,
            menu_name_rest_list,
            file_path_info,
            execution_no_path)

        # migrate file
        exec_ws_migration(import_info, objdbca, "file")

        # migrate jnl
        exec_ws_migration(import_info, objdbca, "jnl")

        # migrate specific
        exec_ws_migration(import_info, objdbca, "specific")

        # clear uploadfiles exclusion menu
        clear_uploadfiles_for_exclusion(objdbca, clear_uploadfiles_exclusion)

    finally:
        # delete sandboxdb
        sandbox_workspace_delete(connect_info)

def get_import_config(execution_no_path):
    """
        インポート用の情報取得(バージョン、ドライバ)
    Args:
        execution_no_path: 一時作業用: /tmp/<execution_no>
    Returns:
        info: {}
    """
    import_config = {
        "import_mode" : "same", # same: 同一バージョン / diff: バージョン差分あり
        "ita_version": None,
        "kym_version": None,
        "drivers": None,
        # "import_drivers": None,
        "ita_drivers": None,
        "kym_drivers": None,
        "no_install_driver": None,
    }
    # get ita version & install drivers
    common_db = DBConnectCommon()
    version_data = get_ita_version(common_db)
    ita_version = version_data["version"]
    ita_drivers = list(version_data["installed_driver"].keys())
    no_installed_driver = version_data["no_installed_driver"] if "no_installed_driver" in version_data else []
    [ita_drivers.remove(nid) for nid in no_installed_driver if nid in ita_drivers]
    default_installed_driver = version_data["default_installed_driver"] if "default_installed_driver" in version_data else []

    common_db.db_disconnect()

    # get kym version & install drivers
    kym_version = file_open_read_close(execution_no_path + '/VERSION')
    kym_drivers = file_open_read_close(execution_no_path + '/DRIVERS')
    kym_drivers = json.loads(kym_drivers)

    import_config["kym_version"] = kym_version
    import_config["ita_version"] = ita_version

    # check version： 1. v2.5.0以上か 2.itaとkymでバージョン差分あるか
    if (version.parse("2.5.0") <= version.parse(kym_version)):
        if (version.parse(ita_version) < version.parse(kym_version)):
            raise AppException("MSG-140015", [kym_version, ita_version], [kym_version, ita_version])
        if (version.parse(ita_version) == version.parse(kym_version)):
            import_config["import_mode"] = "same"
        else:
            import_config["import_mode"] = "diff"
    else:
        g.applogger.debug(f"The version of kym used is not allowed. {kym_version=}")
        raise AppException("MSG-140012", [kym_version], [kym_version])

    # check drivers
    no_kym_driver = [_d for _d in kym_drivers if _d not in ita_drivers] \
        if isinstance(kym_drivers, list) and isinstance(ita_drivers, list) else []

    if len(no_kym_driver) != 0:
        [no_kym_driver.remove(_dd) for _dd in default_installed_driver if _dd in no_kym_driver]
        no_kym_driver_log = ",".join(no_kym_driver)
        no_kym_driver_lang = "\n".join([f'・{version_data["installed_driver"].get(ndk)}' for ndk in no_kym_driver])
        log_msg_args = [no_kym_driver_log]
        api_msg_args = [no_kym_driver_lang]
        raise AppException("MSG-140013",log_msg_args, api_msg_args)  # noqa: F405

    import_config["drivers"] = True
    # import_config["import_drivers"] = ita_drivers
    [ita_drivers.remove(_dd) for _dd in default_installed_driver if _dd in ita_drivers]
    [kym_drivers.remove(_dd) for _dd in default_installed_driver if _dd in kym_drivers]
    import_config["ita_drivers"] = ita_drivers
    import_config["kym_drivers"] = kym_drivers

    if kym_drivers != ita_drivers:
        import_config["import_mode"] = "diff"

    org_db = DBConnectOrg()  # noqa: F405
    no_install_driver_tmp = org_db.get_no_install_driver()
    no_install_driver = [] if no_install_driver_tmp is None or \
        len(no_install_driver_tmp) == 0 else json.loads(no_install_driver_tmp)
    import_config["no_install_driver"] = no_install_driver

    g.applogger.info(f"{import_config=}")

    return import_config

def preparation_sandbox_workspace(workspace_id):
    """
        一時作業用DBの作成
    Args:
        workspace_id: workspace_id
    Returns:
        connect_info: user, password, db name
        ws_db_sb: DBConnectWsSandbox()
    """
    # create sandboxdb & execute workspace sql
    connect_info = sandbox_workspace_create(workspace_id)
    # connect sandboxdb
    ws_db_sb = DBConnectWsSandbox(
        connect_info["db_username"],
        ky_encrypt(connect_info["db_user_password"]),
        connect_info["ws_db_name"]
    )
    return connect_info, ws_db_sb

def exec_ws_migration(import_info, objdbca, mode="db"):
    """
        migration処理呼び出し
    Args:
        import_info:  user, password, db name
        objdbca: DBConnectWsSandbox() or DBConnectWs()
        mode: db:DBパッチ, file:ファイル配置, jnl:履歴 specific:特別処理
    """
    try:
        g.applogger.info(f"Begin sandbox migration. ({mode=})")
        g.APPPATH = os.path.dirname(__file__)
        # version.listファイル読み込み
        version_list_path = os.path.join(g.APPPATH, "version.list")
        version_list = read_version_list(version_list_path)
        kym_version = import_info["kym_version"]
        ita_version = import_info["ita_version"]

        # kym_version が含まれていたら、それ以降のversion_listを返す
        if kym_version in version_list:
            index = version_list.index(kym_version)
            del version_list[:(index + 1)]
        else:
            raise AppException("MSG-140014", [kym_version], [kym_version])

        versions = version_list
        if len(versions) == 0:
            g.applogger.info(f"No need to work.{mode=}")
            return 0

        g.applogger.info(f"migration target {versions=}")

        # バージョンアップ
        for version in versions:
            # 対象バージョンのディレクトリ確認
            g.APPPATH = os.path.dirname(__file__)
            version_dir = version.replace('.', '_')
            version_dir_path = os.path.join(g.APPPATH, "versions", version_dir)
            ws_worker = Migration(
                os.path.join(version_dir_path, "WS_level"),
                os.path.join(os.environ.get('STORAGEPATH'), g.ORGANIZATION_ID, g.WORKSPACE_ID),
                objdbca,
                import_info["no_install_driver"])

            g.applogger.info(f"Execute sandbox migration: {version}")
            migration_execute(ws_worker, mode)
            if kym_version == version or ita_version == version:
                break

        g.applogger.info("End sandbox migration.")

    except Exception as e:
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
        raise e

def migration_execute(ws_worker, mode="db"):
    """
    migration実行処理振り分け
    Args:
        ws_worker: Migration()
        mode: db:DBパッチ, file:ファイル配置, specific:特別処理
    """
    g.applogger.info("[Trace] Begin WS migrate.")

    g.applogger.info(f"ws_worker.migrate_{mode}")
    if mode == "db":
        ws_worker.migrate_db()
    elif mode == "file":
        ws_worker.migrate_file()
    elif mode == "jnl":
        ws_worker.migrate_jnl()
    elif mode == "specific":
        ws_worker.migrate_specific()

    g.applogger.info("[Trace] End WS migrate.")

    return

def sandbox_workspace_create(workspace_id):  # noqa: E501
    """
    インポート作業用の一時使用Workspaceを作成する
    ARGS:
        workspace_id: workspace_id
    RETURN:
        connect_info { ws_db_name: "", db_username: "", db_user_password: ""}
    """
    connect_info = {
        "ws_db_name": None,
        "db_username": None,
        "db_user_password": None,
    }

    role_id = '_' + workspace_id + '-admin'

    org_db = DBConnectOrg()  # noqa: F405
    # get no install driver list
    no_install_driver_tmp = org_db.get_no_install_driver()
    if no_install_driver_tmp is None or len(no_install_driver_tmp) == 0:
        no_install_driver = []
    else:
        no_install_driver = json.loads(no_install_driver_tmp)

    try:
        # make workspace-db connect infomation
        ws_db_name, db_username, db_user_password = org_db.userinfo_generate("ITA_SD")

        connect_info["ws_db_name"] = ws_db_name
        connect_info["db_username"] = db_username
        connect_info["db_user_password"] = db_user_password

        # connect organization-db as root user
        org_root_db = DBConnectOrgRoot()  # noqa: F405

        # create workspace-databse
        org_root_db.database_create(ws_db_name)
        g.applogger.debug(f"sandbox database create:{ws_db_name}")

        # create workspace-user and grant user privileges
        org_root_db.user_create(db_username, db_user_password, ws_db_name)
        g.applogger.debug(f"sandbox user create:{db_username}")

        # create table & insert record
        ws_db_sb = DBConnectWsSandbox(db_username, ky_encrypt(db_user_password), ws_db_name)  # noqa: F405

        sql_list = [
            ['workspace.sql', 'workspace_master.sql'],
            ['menu_create.sql', 'menu_create_master.sql'],
            ['conductor.sql', 'conductor_master.sql'],
            ['ansible.sql', 'ansible_master.sql'],
            ['export_import.sql', 'export_import_master.sql'],
            ['compare.sql', 'compare_master.sql'],
            ['terraform_common.sql', 'terraform_common_master.sql'],
            ['terraform_cloud_ep.sql', 'terraform_cloud_ep_master.sql'],
            ['terraform_cli.sql', 'terraform_cli_master.sql'],
            ['hostgroup.sql', 'hostgroup_master.sql'],
            ['cicd.sql', 'cicd_master.sql'],
            ['oase.sql', 'oase_master.sql'],
        ]
        last_update_timestamp = str(get_timestamp())

        for sql_files in sql_list:
            ddl_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[0]
            dml_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[1]

            # インストールしないドライバに指定されているSQLは実行しない
            if (sql_files[0] == 'terraform_common.sql' and 'terraform_cloud_ep' in no_install_driver and 'terraform_cli' in no_install_driver) or \
                    (sql_files[0] == 'terraform_cloud_ep.sql' and 'terraform_cloud_ep' in no_install_driver) or \
                    (sql_files[0] == 'terraform_cli.sql' and 'terraform_cli' in no_install_driver) or \
                    (sql_files[0] == 'cicd.sql' and 'ci_cd' in no_install_driver) or \
                    (sql_files[0] == 'oase.sql' and 'oase' in no_install_driver):
                continue

            # create table of workspace-db
            ws_db_sb.sqlfile_execute(ddl_file)
            g.applogger.debug("executed " + ddl_file)

            # insert initial data of workspace-db
            db_reconnention(ws_db_sb, True) if ws_db_sb else None
            ws_db_sb.db_transaction_start()
            # #2079 /storage配下ではないので対象外
            with open(dml_file, "r") as f:
                sql_list = f.read().split(";\n")
                for sql in sql_list:
                    if re.fullmatch(r'[\s\n\r]*', sql):
                        continue

                    sql = sql.replace("_____DATE_____", "STR_TO_DATE('" + last_update_timestamp + "','%Y-%m-%d %H:%i:%s.%f')")

                    prepared_list = []
                    trg_count = sql.count('__ROLE_ID__')
                    if trg_count > 0:
                        prepared_list = list(map(lambda a: role_id, range(trg_count)))
                        sql = ws_db_sb.prepared_val_escape(sql).replace('\'__ROLE_ID__\'', '%s')

                    ws_db_sb.sql_execute(sql, prepared_list)
            g.applogger.debug("executed " + dml_file)
            ws_db_sb.db_commit()

    except Exception as e:
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
        raise e
    finally:
        if 'org_root_db' in locals():
            org_root_db.db_disconnect()

        if 'org_db' in locals():
            org_db.db_disconnect()

        if 'ws_db_sb' in locals():
            ws_db_sb.db_disconnect()

    return connect_info


def sandbox_workspace_delete(connect_info):  # noqa: E501
    """
        インポート作業用の一時使用Workspaceを削除する
    Args:
        import_info:  user, password, db name
    """
    try:
        # drop ws-db and ws-db-user
        org_root_db = DBConnectOrgRoot()
        g.applogger.info(f"DBConnectOrgRoot")
        org_root_db.connection_kill(connect_info['ws_db_name'], connect_info['db_username'])
        g.applogger.info(f"connection_kill")
        org_root_db.database_drop(connect_info['ws_db_name'])
        g.applogger.info(f"database_drop: {connect_info['ws_db_name']}")
        org_root_db.user_drop(connect_info['db_username'])
        g.applogger.info(f"user_drop: {connect_info['db_username']}")
        org_root_db.db_disconnect()
    except Exception as e:
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
        raise e
    finally:
        if 'org_root_db' in locals():
            org_root_db.db_disconnect()

def sandbox_workspace_menu_import(
    objdbca,
    workspace_id,
    uploadfiles_dir,
    rpt,
    dp_mode,
    menu_name_rest_list,
    execution_no_path):
    """
        インポート作業用の一時使用WorkspaceDBへインポート
    Args:
        objdbca: DBConnectWs()
        workspace_id: workspace_id
        uploadfiles_dir:  /storage/<organization_id>/<workspace_id>/uploadfiles
        rpt: RecordProcessingTimes()
        dp_mode: 1: clear table [環境移行] / 2: duplicate record override [時刻指定]
        menu_name_rest_list: record["JSON_STORAGE_ITEM"]
        execution_no_path: /tmp/<execution_no>
    Returns:
        file_path_info: { menu_name_rest: [ file: {}, file_path {}] }
    """
    # 環境移行にて削除したテーブル名を記憶する用
    imported_table_list = []

    db_reconnention(objdbca) if objdbca else None
    # load_table.loadTableを使用するため特定のメニューは事前に処理しておく
    _dp_preparation(objdbca, workspace_id, menu_name_rest_list, execution_no_path, imported_table_list, "2", file_put_flg=False)
    db_reconnention(objdbca) if objdbca else None
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

    file_path_info = {}

    rpt.set_time("import: ita_default_menus ")
    # ITA標準メニューのインポート
    _file_path_info_def = import_table_and_data(
        objdbca,
        "2",
        workspace_id,
        uploadfiles_dir,
        execution_no_path,
        ita_default_menus,
        imported_table_list,
        tmp_table_list,
        t_comn_menu_data_json,
        menu_name_rest_list,
        file_path_info={},
        file_put_flg=False,
        ita_base_menu_flg=True
    )
    rpt.set_time("import: ita_default_menus ")

    rpt.set_time("import: ita_create_menus ")
    # パラメータシート、データシートのインポート
    _file_path_info_cm = import_table_and_data(
        objdbca,
        "2",
        workspace_id,
        uploadfiles_dir,
        execution_no_path,
        ita_create_menus,
        imported_table_list,
        tmp_table_list,
        t_comn_menu_data_json,
        menu_name_rest_list,
        file_path_info={},
        file_put_flg=False,
        ita_base_menu_flg=False
    )
    rpt.set_time("import: ita_create_menus ")

    file_path_info.update(_file_path_info_def)
    file_path_info.update(_file_path_info_cm)

    _tmp_dir = f"{execution_no_path}/_tmp"
    if os.path.isdir(_tmp_dir) is True:
        shutil.rmtree(_tmp_dir)
        os.makedirs(_tmp_dir, exist_ok=True)

    return file_path_info

def import_from_sandbox_to_maindb(
    objdbca,
    ws_db_sb,
    workspace_id,
    uploadfiles_dir,
    rpt,
    dp_mode,
    menu_id_list,
    menu_name_rest_list,
    file_path_info,
    execution_no_path):
    """
        インポート用の一時作業DBからワークスペースDBへのインポート
    Args:
        objdbca: DBConnectWs()
        ws_db_sb: DBConnectWsSandbox()
        workspace_id: workspace_id
        uploadfiles_dir:  /storage/<organization_id>/<workspace_id>/uploadfiles
        rpt: RecordProcessingTimes()
        dp_mode: 1: clear table [環境移行] / 2: duplicate record override [時刻指定]
        menu_id_list: [menu_id]
        menu_name_rest_list: record["JSON_STORAGE_ITEM"]
        file_path_info: { menu_name_rest: [ file: {}, file_path {}] }
        execution_no_path: /tmp/<execution_no>
    """
    if dp_mode == '1':
        for menu_id in menu_id_list:
            menu_dir = uploadfiles_dir + '/' + menu_id
            # ディレクトリ存在チェック
            if os.path.isdir(menu_dir) is True:
                shutil.rmtree(menu_dir) \
                    if menu_id not in clear_uploadfiles_exclusion_list else None

    # 環境移行にて削除したテーブル名を記憶する用
    imported_table_list = []
    # 作成したview名を記憶する用
    tmp_table_list = []

    # インポート対象メニュー取得
    # T_COMN_MENU_TABLE_LINK_DATAファイル読み込み
    t_comn_menu_table_link_data = file_open_read_close(execution_no_path + '/T_COMN_MENU_TABLE_LINK_DATA')
    t_comn_menu_table_link_data_json = json.loads(t_comn_menu_table_link_data)
    # T_COMN_MENU_DATAファイル読み込み
    t_comn_menu_data = file_open_read_close(execution_no_path + '/T_COMN_MENU_DATA')
    t_comn_menu_data_json = json.loads(t_comn_menu_data)

    # インポート対象メニューを分類(LoadTable関連、ITA標準, パラメータシート作成)
    base_menu_name_list, base_table_list = (list(ita_lb_menu_info.keys()), list(ita_lb_menu_info.values()))
    ita_lb_menus = [_r for _r in t_comn_menu_table_link_data_json if _r['parameter'].get('table_name') is not None and _r['parameter'].get('table_name') in base_table_list]
    ita_default_menus = [_r for _r in t_comn_menu_table_link_data_json if _r['parameter'].get('table_name') is not None and not _r['parameter'].get('table_name').startswith('T_CMDB')]
    ita_create_menus =  [_r for _r in t_comn_menu_table_link_data_json if _r['parameter'].get('table_name') is not None and _r['parameter'].get('table_name').startswith('T_CMDB')]
    ita_create_menus = sorted(ita_create_menus, key=lambda x: x['parameter']['table_name'])

    # ITA共通機能使用メニューのファイル情報設定
    _file_path_info_base = get_file_path_info_base_menus(execution_no_path, base_menu_name_list)
    file_path_info.update(_file_path_info_base)

    rpt.set_time("import: ita_loadtable_use_menus ")
    # ITA共通機能使用メニューのインポート
    import_table_and_data(
        objdbca,
        dp_mode,
        workspace_id,
        uploadfiles_dir,
        execution_no_path,
        ita_lb_menus,
        imported_table_list,
        tmp_table_list,
        t_comn_menu_data_json,
        base_menu_name_list,
        file_path_info,
        file_put_flg=True,
        ita_base_menu_flg=True,
        ws_db_sb=ws_db_sb
    )
    rpt.set_time("import: ita_loadtable_use_menus ")

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
        file_path_info,
        file_put_flg=True,
        ita_base_menu_flg=True,
        ws_db_sb=ws_db_sb
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
        file_path_info,
        file_put_flg=True,
        ita_base_menu_flg=False,
        ws_db_sb=ws_db_sb
    )
    rpt.set_time("import: ita_create_menus ")

def _export_sandboxdb_bulk_register_maindb(objdbca, ws_db_sb, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name, file_path_info, dp_mode="1"):
    """
        インポート一括処理用
        ARGS:
            objdbca: DBConnectWs()
            ws_db_sb: DBConnectWsSandbox()
            objmenu: load_table.bulkLoadTable()
            workspace_id: workspace_id
            execution_no_path: 一時作業用: /tmp/<execution_no>
            menu_name_rest: menu_name_rest
            menu_id: menu_id
            table_name: table_name
            file_path_info: { menu_name_rest: [ file: {}, file_path {}] }
            dp_mode: 1: 環境移行 / 2:時刻指定
        RETURN:
            objmenu
    """
    pk = objmenu.get_primary_key()

    _record_count = get_record_count(execution_no_path, menu_name_rest)
    if _record_count == 0:
        # KYMの対象レコードが0件の場合スキップする
        tmp_msg = f" Skip due to 0 recode :{menu_name_rest}"
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return objmenu, []

    # インポート対象件数
    sbrc_count = ws_db_sb.table_count(table_name)
    if sbrc_count == 0:
        return objmenu, []
    else:
        if dp_mode == "2":
            _pk = "JOURNAL_SEQ_NO" if table_name.endswith("_JNL") else pk
            str_sql = f"SELECT `{_pk}` FROM `{table_name}`"
            _rows = ws_db_sb.sql_execute(str_sql)
            _ids = [_r[_pk] for _r in _rows]
            n = int(len(_ids)) if g.max_allowed_packet >= 40 * len(_ids) else int(g.max_allowed_packet / 40)
            for i in range(0, len(_ids), n):
                _prepared_list = ','.join(list(map(lambda a: "%s", _ids[i: i+n])))
                delete_table_sql = f"DELETE FROM `{table_name}` WHERE `{_pk}` in ({_prepared_list})"
                objdbca.sql_execute(delete_table_sql, _ids[i: i+n])
        sb_rows = ws_db_sb.table_select(table_name)

    # LOAD DATA LOCAL INFILE用CSV変換
    try:
        _tmp_dir = f"{execution_no_path}/_tmp"
        os.makedirs(_tmp_dir, exist_ok=True)  if not os.path.isdir(_tmp_dir) else None
        json_path = f"{_tmp_dir}/{table_name}.json"
        csv_path = f"/{_tmp_dir}/{table_name}.csv"
        g.applogger.debug(f"{os.path.isdir(_tmp_dir)} {_tmp_dir=}")

        with open(json_path, 'w') as f :
            json.dump(sb_rows, f, ensure_ascii=False, indent=4, default=json_serial)
        json_open = open(json_path, 'r')
        json_data = json.dumps(json.load(json_open)).replace(r'\\',r'\\\\')

        get_column_sql = f"SHOW COLUMNS FROM `{table_name}`"
        columns_row = objdbca.sql_execute(get_column_sql)
        column_type = {_r["Field"]:_r["Type"] for _r in columns_row}
        column_list = list(column_type.keys())
        # 予期せぬ小数点付きの値への対応
        dtyp = {}
        for ck, cv in column_type.items():
            dtyp[ck] = "object"

        df = pd.read_json(StringIO(json_data), orient='records', dtype=dtyp)
        df = df.where(df.notnull(), None)
        g.applogger.debug(df.dtypes)
        g.applogger.debug(df)
        df.to_csv(csv_path, index=False)
        csv_header = list(pd.read_csv(csv_path, header=0).columns)
        target_fields = [ck for ck in csv_header if ck in column_list]

        # LOAD DATA LOCAL INFILE
        query_str = textwrap.dedent("""
            LOAD DATA LOCAL INFILE  '{csv_path}'
            INTO TABLE `{table_name}`
            FIELDS TERMINATED BY ','
            ENCLOSED BY '"'
            LINES TERMINATED BY '\n'
            IGNORE 1 ROWS
        """).format(csv_path=csv_path, table_name=table_name).strip()

        # add (Colmun,,,,) & add SET Colmun = NULLIF(@{Colmun}, '')
        set_column_str = "\n("
        for ck in target_fields:
            set_column_str = set_column_str +f"@{ck}, \n"
        set_column_str = set_column_str[:-3]
        set_column_str = set_column_str + ")\n"
        set_column_str = set_column_str + "SET\n"
        for ck in target_fields:
            set_column_str = set_column_str + f"{ck} =  NULLIF(@{ck}, ''),"
        set_column_str = set_column_str[:-1]
        query_str = query_str + set_column_str

        g.applogger.debug(query_str)  # noqa: F405
        g.applogger.debug((os.path.isfile(csv_path), csv_path))
        objdbca.sql_execute(query_str)
    except Exception as e:
        trace_msg = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        raise e
    finally:
        os.remove(csv_path) if os.path.isfile(csv_path) else None
        os.remove(json_path) if os.path.isfile(json_path) else None
        pass

    return objmenu, []


def _bulk_register_file(objdbca, objmenu, execution_no_path, menu_name_rest, file_info_list):
    """
        インポート一括処理用
        ARGS:
            objdbca: DBConnectWs()
            objmenu: load_table.bulkLoadTable()
            execution_no_path: 一時作業用: /tmp/<execution_no>
            menu_name_rest: menu_name_rest
        RETURN:
            objmenu
    """
    # t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    organization_id = g.get("ORGANIZATION_ID")
    workspace_id = g.get("WORKSPACE_ID")
    jnl_flg = True if menu_name_rest.endswith("_JNL") else False
    # ファイルアップロード系カラムを取得する
    file_column = ["9", "20"]  # [FileUploadColumn, FileUploadEncryptColumn]
    ret_file_column = [oc for ok, oc in objmenu.get_objcols().items() if oc.get("COLUMN_CLASS", "-") in file_column]
    file_column_list = [record.get('COLUMN_NAME_REST') for record in ret_file_column] if len(ret_file_column) != 0 else []

    _json_f_data = file_info_list[menu_name_rest] if menu_name_rest in file_info_list else []

    # ファイルアップロード系カラムの配置処理
    if len(file_column_list) == 0:
        g.applogger.debug(f"{menu_name_rest}: Skip due to 0 file upload targets")
        return

    g.applogger.debug(f"{menu_name_rest}: 'File upload & symlink")
    # ファイル配置: 各レコード->ファイル項目
    for _jfd in _json_f_data:
        for _jfk, _jfv in _jfd["file_path"].items():
            if _jfv is None:
                # file_pathがNoneの時、SKIP
                continue

            if isinstance(_jfv, dict):
                # path
                f_src_dir = f"/storage/{organization_id}/{workspace_id}{_jfv['src'].replace(_jfv['name'], '')}"
                f_src = f"/storage/{organization_id}/{workspace_id}{_jfv['src']}"
                # f_dst_dir = f"/storage/{organization_id}/{workspace_id}{_jfv['dst'].replace(_jfv['name'], '')}"
                f_dst = f"/storage/{organization_id}/{workspace_id}{_jfv['dst']}"
                tmp_f_src = f_src.replace("/storage/", "/tmp/")
                tmp_f_entity = f"{execution_no_path}{_jfv['src']}"

                g.applogger.debug(f"{os.path.isfile(tmp_f_entity)} {tmp_f_entity}")
                if not os.path.isfile(tmp_f_entity):
                    # KYMファイル解凍後のuploadfiles配下にファイルが無い場合、SKIP
                    g.applogger.info(f"{tmp_f_entity} does not exist, so it will be skipped")
                    continue

                # makedirs -> remove
                os.makedirs(f_src_dir) if not os.path.isdir(f_src_dir) else None
                os.remove(tmp_f_src) if os.path.isfile(tmp_f_src) else None
                os.remove(f_src) if jnl_flg and os.path.isfile(f_src) else None

                # upload_file
                if _jfv['class_name'] == "FileUploadEncryptColumn":
                    objsr = storage_read()
                    objsr.open(tmp_f_entity, mode="rb")
                    tmp_f_entity_f = base64.b64encode(objsr.read()).decode()
                    objsr.close()
                    encrypt_upload_file(f_src, tmp_f_entity_f, mode="w")
                else:
                    shutil.copyfile(tmp_f_entity, f_src)

                # symlink
                if os.path.isfile(f_src):
                    os.unlink(f_dst) if os.path.islink(f_dst) else None
                    os.symlink(f_src, f_dst)
    return


def clear_uploadfiles_for_exclusion(objdbca, target_menus):
    """
        特定のuploadfiles配下のレコード無しディレクトリのクリア
    Args:
        objdbca (_type_): _description_
        target_menus (_type_): _description_

    Raises:
        Exception: _description_
    """
    f_column = ["9", "20"]
    file_column_list = {}
    ret_file_column = objdbca.table_select(
        'T_COMN_MENU_COLUMN_LINK',
        'WHERE COLUMN_CLASS IN %s', [f_column])  # noqa: E501
    [[file_column_list.setdefault(rfc.get('MENU_ID'), []), file_column_list[rfc.get('MENU_ID')].append(rfc.get('COLUMN_NAME_REST'))]\
        for rfc in ret_file_column if rfc.get('MENU_ID') is not None]

    for menuid, table_name in target_menus.items():
        column_list, primary_key_list = objdbca.table_columns_get(table_name)
        primary_key = primary_key_list[0]
        sql = f"SELECT `{primary_key}` FROM `{table_name}`"
        _rows = objdbca.sql_execute(sql)
        ids = [_r[primary_key] for _r in _rows]
        dirlist = []
        for rest_column in file_column_list[menuid]:
            menu_path = os.path.join(os.environ.get('STORAGEPATH'), g.ORGANIZATION_ID, g.WORKSPACE_ID, "uploadfiles", menuid, rest_column)
            [dirlist.append(d) for d in os.listdir(menu_path) if os.path.isdir(os.path.join(menu_path, d))]
            gvg_dirs = [_id for _id in dirlist if _id not in ids]
            for id in gvg_dirs:
                garbage_dir = os.path.join(menu_path, id)
                g.applogger.info(f"clear {garbage_dir=}")
                shutil.rmtree(garbage_dir) if os.path.isdir(garbage_dir) else None

def json_serial(obj):
    """
    json_serial: datetime, date -> str
    Args:
        obj:
    Returns:
        xxxx :
    """
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()

def get_file_path_info_base_menus(execution_no_path, menu_list):
    result = {}
    for menu_name_rest in menu_list:
        # DATAファイル確認
        if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
            # _DATAファイルのみ
            g.applogger.info(f"_DATA file only")
            continue

        # DATAファイル読み込み
        sql_data = file_open_read_close(execution_no_path + '/' + menu_name_rest)
        json_sql_data = json.loads(sql_data)
        if len(json_sql_data) == 0:
            g.applogger.info(f"{menu_name_rest}: target 0.")
            continue
        _file_path_info = []
        for json_record in json_sql_data:
            _file_path_info.append(
                {
                    "file": json_record.get("file") if isinstance(json_record.get("file"), dict) else {},
                    "file_path": json_record.get("file_path") if isinstance(json_record.get("file_path"), dict) else {}
                }
            )
        result[menu_name_rest] = _file_path_info
    return result

def get_record_count(execution_no_path, menu_name_rest):
    result = 0

    # DATAファイル確認
    if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
        # 対象ファイルなし
        raise AppException("MSG-140003", [menu_name_rest], [menu_name_rest])
    # DATAファイル読み込み
    sql_data = file_open_read_close(execution_no_path + '/' + menu_name_rest)
    json_sql_data = json.loads(sql_data)
    result = len(json_sql_data) if isinstance(json_sql_data, list) else 0

    return result

def db_reconnention(obj,force=False):
    """ check connection DBConnect<XX> (reconnect)
    Args:
        obj : DBConnect<xxx>()
    """
    try:
        obj.sql_execute("SELECT 1;")
        connect = True
    except:
        connect = False

    if force or connect is False:
        g.applogger.info(f"{obj=}: reconnect.")
        obj.db_disconnect()
        obj.db_connect()

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
            trace_msg = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
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
            trace_msg = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
            res = None
        return res
