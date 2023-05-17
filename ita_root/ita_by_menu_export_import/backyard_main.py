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
from common_libs.loadtable import *  # noqa: F403
from common_libs.common.exception import AppException  # noqa: F401
from pathlib import Path
import shutil
import subprocess
import time
import inspect


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

    strage_path = os.environ.get('STORAGEPATH')
    workspace_path = strage_path + "/".join([organization_id, workspace_id])
    export_menu_dir = workspace_path + "/tmp/driver/export_menu"
    import_menu_dir = workspace_path + "/tmp/driver/import_menu"
    uploadfiles_dir = workspace_path + "/uploadfiles"
    uploadfiles_60103_dir = workspace_path + "/uploadfiles/60103"
    if not os.path.isdir(uploadfiles_60103_dir):
        os.makedirs(uploadfiles_60103_dir)
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

        # execution_typeに応じたエクスポート/インポート処理を実行(メイン処理)
        if execution_type == "1":  # 1: エクスポート
            main_func_result, msg = menu_export_exec(objdbca, record, workspace_id, export_menu_dir, uploadfiles_dir)
        elif execution_type == "2":  # 2: インポート
            main_func_result, msg = menu_import_exec(objdbca, record, workspace_id, workspace_path, uploadfiles_dir, uploadfiles_60103_dir)

        # メイン処理がFalseの場合、異常系処理
        if not main_func_result:
            # エラーログ出力
            g.applogger.error(msg)

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

        # 「メニューエクスポート・インポート管理」ステータスを「3:完了」に更新
        objdbca.db_transaction_start()
        status = 3
        result, msg = _update_t_menu_export_import(objdbca, execution_no, status)
        if not result:
            # エラーログ出力
            g.applogger.error(msg)
            continue
        objdbca.db_transaction_end(True)

    # サービススキップファイルが存在する場合は削除する
    if os.path.exists(workspace_path + '/skip_all_service'):
        os.remove(workspace_path + '/skip_all_service')

    # メイン処理終了
    debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    g.applogger.debug(debug_msg)
    return


def menu_import_exec(objdbca, record, workspace_id, workspace_path, uploadfiles_dir, uploadfiles_60103_dir):
    msg = None

    try:
        # サービススキップファイルを配置する
        f = Path(workspace_path + '/skip_all_service')
        f.touch()
        time.sleep(int(os.environ.get("EXECUTE_INTERVAL", 10)))

        execution_no = str(record.get('EXECUTION_NO'))
        file_name = str(record.get('FILE_NAME'))
        dp_mode = str(record.get('MODE'))
        json_storage_item = str(record.get('JSON_STORAGE_ITEM'))

        tmp_msg = "Target record data: {}, {}, {}, {}".format(execution_no, file_name, dp_mode, json_storage_item)
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        execution_no_path = uploadfiles_60103_dir + '/file_name/' + execution_no
        file_path = execution_no_path + '/' + file_name
        if os.path.isfile(file_path) is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])

        # zip解凍
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.extractall(path=execution_no_path)

        if os.path.isfile(execution_no_path + '/T_COMN_MENU_TABLE_LINK_DATA') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])

        if os.path.isfile(execution_no_path + '/T_COMN_MENU_DATA') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])

        if os.path.isfile(execution_no_path + '/MENU_NAME_REST_LIST') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])
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

        # 環境移行にて削除したテーブル名を記憶する用
        deleted_table_list = []

        # 環境移行モードの場合はDELETE→INSERTするので特定のメニューは事前に退避しておく
        if dp_mode == '1':
            _dp_preparation(objdbca, workspace_id, menu_name_rest_list, execution_no_path, deleted_table_list)

        # 作成したview名を記憶する用
        tmp_table_list = []
        # インポート対象メニュー取得
        # T_COMN_MENU_TABLE_LINK_DATAファイル読み込み
        t_comn_menu_table_link_data = Path(execution_no_path + '/T_COMN_MENU_TABLE_LINK_DATA').read_text(encoding='utf-8')
        t_comn_menu_table_link_data_json = json.loads(t_comn_menu_table_link_data)
        # T_COMN_MENU_DATAファイル読み込み
        t_comn_menu_data = Path(execution_no_path + '/T_COMN_MENU_DATA').read_text(encoding='utf-8')
        t_comn_menu_data_json = json.loads(t_comn_menu_data)
        for record in t_comn_menu_table_link_data_json:
            param = record['parameter']
            # menu_id = param.get('uuid')
            menu_id = param.get('menu_name')
            table_name = param.get('table_name')
            view_name = param.get('view_name')
            history_table_flag = param.get('history_table_flag')

            tmp_msg = "Target import record data: {}, {}, {}, {}".format(menu_id, table_name, view_name, history_table_flag)
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

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

            # 環境移行モードの場合、既存のデータは全て削除してからデータをインポートする
            if dp_mode == '1':
                tmp_msg = "check information_schema.tables START: {}".format(table_name)
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                chk_table_sql = " SELECT TABLE_NAME FROM information_schema.tables WHERE `TABLE_NAME` = %s "
                chk_table_rtn = objdbca.sql_execute(chk_table_sql, [table_name])

                tmp_msg = "check information_schema.tables END: {}".format(table_name)
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                if len(chk_table_rtn) != 0:
                    # uploadfiles配下のデータを削除する
                    if os.path.isdir(uploadfiles_dir + '/' + menu_id):
                        shutil.rmtree(uploadfiles_dir + '/' + menu_id)

                # DBデータファイル読み込み
                db_data_path = execution_no_path + '/' + table_name + '.sql'
                jnl_db_data_path = execution_no_path + '/' + table_name + '_JNL.sql'

                if table_name not in deleted_table_list:
                    tmp_msg = "DROP and CREATE TABLE START: {}".format(db_data_path)
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                    # テーブルを作成
                    objdbca.sqlfile_execute(db_data_path)

                    tmp_msg = "DROP and CREATE TABLE END: {}".format(db_data_path)
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                    deleted_table_list.append(table_name)
                    if os.path.isfile(jnl_db_data_path):
                        tmp_msg = "DROP and CREATE JNL START: {}".format(jnl_db_data_path)
                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                        # 履歴テーブルを作成
                        objdbca.sqlfile_execute(jnl_db_data_path)
                        deleted_table_list.append(table_name + '_JNL')

                        tmp_msg = "DROP and CREATE JNL END: {}".format(jnl_db_data_path)
                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                if view_name:
                    if table_name.startswith('T_CMDB'):
                        # 一度作成したview名は記憶する
                        if view_name not in tmp_table_list:
                            tmp_table_list.append(view_name)

                            tmp_msg = "check information_schema.views START: {}".format(view_name)
                            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            chk_view_sql = " SELECT TABLE_NAME FROM information_schema.views WHERE `TABLE_NAME` = %s "
                            chk_view_rtn = objdbca.sql_execute(chk_view_sql, [view_name])

                            tmp_msg = "check information_schema.views END: {}".format(view_name)
                            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            if len(chk_view_rtn) != 0:
                                tmp_msg = "DROP VIEW START: {}".format(view_name)
                                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                                drop_view_sql = "DROP VIEW IF EXISTS `{}`".format(view_name)
                                objdbca.sql_execute(drop_view_sql, [])

                                tmp_msg = "DROP VIEW END: {}".format(view_name)
                                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            # DBデータファイル読み込み
                            view_data_path = execution_no_path + '/' + view_name
                            if os.path.isfile(view_data_path):
                                tmp_msg = "CREATE VIEW START: {}".format(view_data_path)
                                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                                objdbca.sqlfile_execute(view_data_path)

                                tmp_msg = "CREATE VIEW END: {}".format(view_data_path)
                                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            objmenu = _register_data(objdbca, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name)
            if history_table_flag == '1':
                _register_history_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name)

        if os.path.isfile(backupsql_path) is True:
            # 正常終了時はバックアップファイルを削除する
            os.remove(backupsql_path)

        if os.path.isdir(backupfile_dir):
            shutil.rmtree(backupfile_dir)

        # 正常系リターン
        return True, msg

    except Exception as msg:
        restoreTables(objdbca, workspace_path)
        restoreFiles(workspace_path, uploadfiles_dir)

        # コミット/トランザクション終了
        debug_msg = g.appmsg.get_log_message("BKY-20005", [])
        g.applogger.error(debug_msg)
        objdbca.db_transaction_end(False)

        # 異常系リターン
        return False, msg


def _dp_preparation(objdbca, workspace_id, menu_name_rest_list, execution_no_path, deleted_table_list):
    tmp_msg = '_dp_preparation START: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    if 'menu_list' in menu_name_rest_list:
        _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, 'menu_list', execution_no_path, deleted_table_list)

    if 'menu_table_link_list' in menu_name_rest_list:
        _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, 'menu_table_link_list', execution_no_path, deleted_table_list)

    if 'menu_column_link_list' in menu_name_rest_list:
        _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, 'menu_column_link_list', execution_no_path, deleted_table_list)

    if 'role_menu_link_list' in menu_name_rest_list:
        _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, 'role_menu_link_list', execution_no_path, deleted_table_list)

    tmp_msg = '_dp_preparation END: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405


def _basic_table_preparation(objdbca, workspace_id, menu_name_rest_list, menu_name_rest, execution_no_path, deleted_table_list):
    tmp_msg = '_basic_table_preparation START: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 指定のメニューに紐づいたテーブルを削除し、インポートデータを登録する
    objmenu = _create_objmenu(objdbca, menu_name_rest_list, menu_name_rest)

    menu_id, table_name, history_table_flag = _menu_data_file_read(menu_name_rest, 'menu_id', execution_no_path)
    delete_sql = "DELETE FROM {}".format(table_name)
    objdbca.sql_execute(delete_sql, [])
    deleted_table_list.append(table_name)
    _register_basic_data(objdbca, workspace_id, execution_no_path, menu_name_rest, table_name, objmenu=objmenu)
    if history_table_flag == '1':
        delete_jnl_sql = "DELETE FROM {}".format(table_name + '_JNL')
        objdbca.sql_execute(delete_jnl_sql, [])
        deleted_table_list.append(table_name + '_JNL')
        _register_history_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name)
    menu_name_rest_list.remove(menu_name_rest)

    tmp_msg = '_basic_table_preparation END: '
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405


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


def _register_data(objdbca, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name):
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    # DATAファイル確認
    if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
        # 対象ファイルなし
        raise AppException("499-00905", [], [])

    # DATAファイル読み込み
    sql_data = Path(execution_no_path + '/' + menu_name_rest).read_text(encoding='utf-8')
    json_sql_data = json.loads(sql_data)

    # WORKSPACE_IDファイル確認
    export_workspace_id = ''
    if os.path.isfile(execution_no_path + '/WORKSPACE_ID'):
        # エクスポートした環境のワークスペース名を取得
        export_workspace_id = Path(execution_no_path + '/WORKSPACE_ID').read_text(encoding='utf-8')

    # データを登録する
    objmenu = load_table.loadTable(objdbca, menu_name_rest, dp_mode=True)   # noqa: F405
    pk = objmenu.get_primary_key()

    # パスワードカラムを取得する
    pass_column = ["8", "25", "26"]
    pass_column_list = []
    ret_pass_column = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_CLASS IN %s', [menu_id, pass_column])  # noqa: E501
    if len(ret_pass_column) != 0:
        for record in ret_pass_column:
            # pass_col_name = record['COL_NAME']
            pass_col_name_rest = record['COLUMN_NAME_REST']
            pass_column_list.append(pass_col_name_rest)

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

        # PasswordColumnかを判定
        for k, v in param.items():
            if k in pass_column_list:
                if v is not None:
                    v = ky_encrypt(v)
                    param[k] = v

        # ロール-メニュー紐付管理個別処理
        if menu_name_rest == 'role_menu_link_list':
            # 「_エクスポート元ワークスペース名-admin」ロールを
            # 「_インポート先ワークスペース名-admin」に置換する
            search_str = '_' + export_workspace_id + '-admin'
            if param['role_name'] == search_str:
                param['role_name'] = '_' + workspace_id + '-admin'

        # 登録用パラメータを作成
        parameters = {
            "file": file_param,
            "parameter": param,
            "type": param_type
        }

        tmp_msg = "Target register data: {}".format(parameters)
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # トランザクション開始
        debug_msg = g.appmsg.get_log_message("BKY-20004", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_start()

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

        # コミット/トランザクション終了
        debug_msg = g.appmsg.get_log_message("BKY-20005", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_end(True)

    return objmenu


def _register_basic_data(objdbca, workspace_id, execution_no_path, menu_name_rest, table_name, objmenu=None):
    # DATAファイル読み込み
    sql_data = Path(execution_no_path + '/' + menu_name_rest).read_text(encoding='utf-8')
    json_sql_data = json.loads(sql_data)

    # WORKSPACE_IDファイル確認
    export_workspace_id = ''
    if os.path.isfile(execution_no_path + '/WORKSPACE_ID'):
        # エクスポートした環境のワークスペース名を取得
        export_workspace_id = Path(execution_no_path + '/WORKSPACE_ID').read_text(encoding='utf-8')

    # データを登録する
    if objmenu is None:
        objmenu = load_table.loadTable(objdbca, menu_name_rest, dp_mode=True)   # noqa: F405
    pk = objmenu.get_primary_key()

    for json_record in json_sql_data:
        param = json_record['parameter']

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

        # トランザクション開始
        debug_msg = g.appmsg.get_log_message("BKY-20004", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_start()

        result = objdbca.table_insert(table_name, colname_parameter, pk)

        # コミット/トランザクション終了
        debug_msg = g.appmsg.get_log_message("BKY-20005", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_end(True)


def _register_history_data(objdbca, objmenu, workspace_id, execution_no_path, menu_name_rest, menu_id, table_name):
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'

    menu_name_rest += '_JNL'
    history_table_name = table_name + "_JNL"

    # DATAファイル確認
    if os.path.isfile(execution_no_path + '/' + menu_name_rest) is False:
        # 対象ファイルなし
        raise AppException("499-00905", [], [])

    # DATAファイル読み込み
    sql_data = Path(execution_no_path + '/' + menu_name_rest).read_text(encoding='utf-8')
    json_sql_data = json.loads(sql_data)

    # WORKSPACE_IDファイル確認
    export_workspace_id = ''
    if os.path.isfile(execution_no_path + '/WORKSPACE_ID'):
        # エクスポートした環境のワークスペース名を取得
        export_workspace_id = Path(execution_no_path + '/WORKSPACE_ID').read_text(encoding='utf-8')

    # パスワードカラムを取得する
    pass_column = ["8", "25", "26"]
    pass_column_list = []
    ret_pass_column = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID = %s AND COLUMN_CLASS IN %s', [menu_id, pass_column])  # noqa: E501
    if len(ret_pass_column) != 0:
        for record in ret_pass_column:
            # pass_col_name = record['COL_NAME']
            pass_col_name_rest = record['COLUMN_NAME_REST']
            pass_column_list.append(pass_col_name_rest)

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

        # PasswordColumnかを判定
        for k, v in param.items():
            if k in pass_column_list:
                if v is not None:
                    v = ky_encrypt(v)
                    param[k] = v

        # ロール-メニュー紐付管理個別処理
        if menu_name_rest == 'role_menu_link_list_JNL':
            # 「_エクスポート元ワークスペース名-admin」ロールを
            # 「_インポート先ワークスペース名-admin」に置換する
            search_str = '_' + export_workspace_id + '-admin'
            if param['role_name'] == search_str:
                param['role_name'] = '_' + workspace_id + '-admin'

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
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        dir_name = 'ita_exportdata_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        dir_path = export_menu_dir + '/' + dir_name
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
            g.applogger.debug("made export_dir")

        # 対象のDBの存在チェック
        menu_list = json_storage_item["menu"]

        menu_group_list = []
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
                add_menu_group['parent_id'] = menu_info_record.get('PARENT_MENU_GROUP_ID')
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
        with open(menus_data_path, "w") as f:
            json.dump(menus_data, f)

        # 更新系テーブル取得
        filter_parameter = {}
        filter_parameter_jnl = {}
        if mode == '1' and abolished_type == '1':
            # 環境移行/廃止を含む
            filter_parameter = {}
        elif mode == '1' and abolished_type == '2':
            # 環境移行/廃止を含まない
            filter_parameter = {"discard": {"LIST": ["0"]}}
            filter_parameter_jnl = {"DISUSE_FLAG": "0"}
        elif mode == '2' and abolished_type == '1':
            # 時刻指定/廃止を含む
            filter_parameter = {"last_update_date_time": {"RANGE": {'START': specified_time}}}
            filter_parameter_jnl = {"LAST_UPDATE_TIMESTAMP": specified_time}
        elif mode == '2' and abolished_type == '2':
            # 時刻指定/廃止を含まない
            filter_parameter = {"discard": {"LIST": ["0"]}, "last_update_date_time": {"RANGE": {'START': specified_time}}}
            filter_parameter_jnl = {"DISUSE_FLAG": "0", "LAST_UPDATE_TIMESTAMP": specified_time}

        for menu in menu_list:
            DB_path = dir_path + '/' + menu
            objmenu = load_table.loadTable(objdbca, menu, dp_mode=True)   # noqa: F405

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

            with open(DB_path, 'w') as f:
                json.dump(result, f, ensure_ascii=False)

            # 履歴テーブル
            history_flag = objmenu.get_objtable().get('MENUINFO').get('HISTORY_TABLE_FLAG')
            if history_flag == '1':
                DB_path = dir_path + '/' + menu + '_JNL'
                filter_mode = 'jnl_all'

                status_code, result, msg = objmenu.rest_export_filter(filter_parameter_jnl, filter_mode)
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
        table_definition_id_list = []
        for record in t_comn_menu_table_link_record:
            table_definition_id_list.append(record.get('TABLE_DEFINITION_ID'))
            table_name = record.get('TABLE_NAME')
            table_name_list.append(table_name)
            if table_name.startswith('T_CMDB'):
                view_name = record.get('VIEW_NAME')
                if view_name is not None:
                    show_create_sql = 'SHOW CREATE VIEW `%s` ' % (view_name)
                    rec = objdbca.sql_execute(show_create_sql, [])
                    create_view_str = rec[0]['Create View']
                    # Create文から余計な文言を切り取る
                    end_pos = create_view_str.find(' VIEW ')
                    create_view_str = create_view_str[:7] + create_view_str[end_pos:]
                    view_data_path = dir_path + '/' + view_name
                    with open(view_data_path, "w") as f:
                        f.write(create_view_str)
            history_table_flag = record.get('HISTORY_TABLE_FLAG')
            if history_table_flag == '1':
                table_name_list.append(table_name + '_JNL')

        db_user = os.environ.get('DB_ADMIN_USER')
        db_password = os.environ.get('DB_ADMIN_PASSWORD')
        db_host = os.environ.get('DB_HOST')
        db_database = objdbca._db

        for table_name in table_name_list:
            sqldump_path = dir_path + '/' + table_name + '.sql'

            cmd = ["mysqldump", "--single-transaction", "--opt", "-u", db_user, "-p" + db_password, "-h", db_host, "--skip-column-statistics", db_database, "--no-data", table_name]

            sp_sqldump = subprocess.run(cmd, capture_output=True, text=True)

            if sp_sqldump.stdout == '' and sp_sqldump.returncode != 0:
                msg = sp_sqldump.stderr
                log_msg_args = [msg]
                api_msg_args = [msg]
                raise AppException("499-00201", [log_msg_args], [api_msg_args])
            with open(sqldump_path, 'w', encoding='utf-8') as f:
                f.write(sp_sqldump.stdout)

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
        with open(t_comn_menu_data_path, 'w') as f:
            json.dump(result, f, ensure_ascii=False)

        # インポート時に利用するMENU_NAME_REST_LISTを作成する
        menu_name_rest_list = ",".join(menu_list)
        menu_name_rest_path = dir_path + '/MENU_NAME_REST_LIST'
        with open(menu_name_rest_path, "w") as f:
            f.write(menu_name_rest_list)

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
        with open(t_comn_menu_table_link_data_path, 'w') as f:
            json.dump(result, f, ensure_ascii=False)

        # アップロード時に利用するDP_INFOファイルを作成する
        dp_info = {
            "DP_MODE": mode,
            "ABOLISHED_TYPE": abolished_type,
            "SPECIFIED_TIMESTAMP": specified_time
        }
        dp_info_path = dir_path + '/DP_INFO'
        with open(dp_info_path, "w") as f:
            json.dump(dp_info, f)

        # ロール-メニュー紐付管理のロール置換用にエクスポート時のWORKSPACE_IDを確保しておく
        workspace_id_path = dir_path + '/WORKSPACE_ID'
        with open(workspace_id_path, "w") as f:
            f.write(workspace_id)

        # アップロード時のバージョン差異チェック用にエクスポート時のVERSIONを確保しておく
        common_db = DBConnectCommon()
        version_data = _collect_ita_version(common_db)
        version_path = dir_path + '/VERSION'
        with open(version_path, "w") as f:
            f.write(version_data["version"])

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

        # トランザクション開始
        debug_msg = g.appmsg.get_log_message("BKY-20004", [])
        g.applogger.debug(debug_msg)
        objdbca.db_transaction_start()

        exec_result = objmenu.exec_maintenance(parameters, execution_no, "", False, False, True)  # noqa: E999

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
        return True, msg

    except Exception as msg:
        # エラー時はtmpの作業ファイルを削除する
        if os.path.isdir(export_menu_dir):
            shutil.rmtree(export_menu_dir)

        # 異常系リターン
        return False, msg


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
            objmenu = load_table.loadTable(objdbca, target_menu, dp_mode=True)
            break
    return objmenu


def _menu_data_file_read(menu_name_rest, pk, execution_no_path):
    # T_COMN_MENU_DATA、MENU_ID_TABLE_LISTファイルを読み取り
    # menu_idとtable_nameを返す
    t_comn_menu_data = Path(execution_no_path + '/T_COMN_MENU_DATA').read_text(encoding='utf-8')
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
    t_comn_menu_table_link_data = Path(execution_no_path + '/T_COMN_MENU_TABLE_LINK_DATA').read_text(encoding='utf-8')
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

    cmd = ["mysqldump", "--single-transaction", "--opt", "-u", db_user, "-p" + db_password, "-h", db_host, "--skip-column-statistics", db_database]
    cmd += table_name_list

    sp_sqldump = subprocess.run(cmd, capture_output=True, text=True)

    if sp_sqldump.stdout == '' and sp_sqldump.returncode != 0:
        msg = sp_sqldump.stderr
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException("499-00201", [log_msg_args], [api_msg_args])
    with open(sqldump_path, 'w', encoding='utf-8') as f:
        f.write(sp_sqldump.stdout)

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

    g.applogger.debug("restoreTables end")


def fileBackup(backupfile_dir, uploadfiles_dir, menu_id_list):
    g.applogger.debug("fileBackup start")
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
            raise AppException("499-00201", [log_msg_args], [api_msg_args])

        # コピーできたかを確認する
        for path in resAry:
            if not os.path.exists(path):
                msg = g.appmsg.get_api_message("MSG-30036")
                log_msg_args = [msg]
                api_msg_args = [msg]
                raise AppException("499-00201", [log_msg_args], [api_msg_args])

    g.applogger.debug("fileBackup end")


def restoreFiles(workspace_path, uploadfiles_dir):
    # ディレクトリとファイルをリストアする
    g.applogger.debug("restoreFiles start")
    backupfile_dir = workspace_path + "/tmp/driver/import_menu/uploadfiles/"

    dir_info = os.listdir(backupfile_dir)
    for dir in dir_info:
        if os.path.isdir(uploadfiles_dir + '/' + dir):
            # インポート途中のファイルがあると不整合を起こすので削除する
            shutil.rmtree(uploadfiles_dir + '/' + dir)
            os.mkdir(uploadfiles_dir + '/' + dir)

        # コピー
        cmd = ["cp", "-rp", backupfile_dir + dir, uploadfiles_dir]
        sp_copy = subprocess.run(cmd, capture_output=True, text=True)

        if sp_copy.returncode != 0:
            msg = sp_copy.stderr
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException("499-00201", [log_msg_args], [api_msg_args])

    g.applogger.debug("restoreFiles end")
