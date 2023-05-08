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
from common_libs.loadtable import *
import os
import pathlib
import textwrap
import shutil
import datetime
from common_libs.common import *  # noqa: F403
from common_libs.common.exception import AppException

"""
  Excel共通モジュール
"""

def setStatus(taskId, status, objdbca=None, is_register_history=True):
    """

    ステータスの更新

    Arguments:
        taskId: タスクID
        statusId: ステータスD
        objdbca: DBオブジェクト
    Returns:
        実行結果
    """

    objdbca.db_transaction_start()
    try:
        # 通常テーブルで更新
        target = {
            "STATUS": status,
            "EXECUTION_NO": taskId,
            "LAST_UPDATE_USER": g.USER_ID
        }

        objdbca.table_update("T_BULK_EXCEL_EXPORT_IMPORT", target, "EXECUTION_NO", is_register_history)

        objdbca.db_transaction_end(True)

    except Exception as msg:
        objdbca.db_transaction_end(False)
        return False, msg

    return True, None

def getExportedMenuIDList(taskId, export_path):
    """

    エクスポートするメニューIDの一覧取得

    Arguments:
        taskId: タスクID
        export_path: エクスポート先パス
    Returns:
        メニューID
    """
    if not os.path.exists(export_path + "/" + taskId + "/MENU_ID_LIST"):
        return False

    json = pathlib.Path(export_path + "/" + taskId + "/MENU_ID_LIST").read_text()
    menuIdAry = json.loads(json)
    return menuIdAry

def getMenuInfoByMenuId(menuNameRest, objdbca=None):
    """

    メニュー情報

    Arguments:
        menuNameRest: メニューREST名
        objdbca: DBオブジェクト
    Returns:
        実行結果
    """
    sql = "SELECT "
    sql += " T_COMN_MENU.MENU_ID, T_COMN_MENU.MENU_NAME_JA, T_COMN_MENU.MENU_GROUP_ID, T_COMN_MENU_GROUP.MENU_GROUP_NAME_JA, T_COMN_MENU_GROUP.MENU_GROUP_NAME_EN "
    sql += "FROM T_COMN_MENU "
    sql += "LEFT OUTER JOIN "
    sql += " T_COMN_MENU_GROUP "
    sql += "ON T_COMN_MENU.MENU_GROUP_ID = T_COMN_MENU_GROUP.MENU_GROUP_ID "
    sql += "WHERE T_COMN_MENU.MENU_NAME_REST = %s "
    sql += "AND T_COMN_MENU.DISUSE_FLAG = 0 "
    sql += "AND T_COMN_MENU_GROUP.DISUSE_FLAG = 0 "

    data_list = objdbca.sql_execute(sql, [menuNameRest])

    data = []
    for data in data_list:
        if data is None or len(data) == 0:
            return []

    return data

def dumpResultMsg(msg, taskId, uploadDir):
    """

    dump結果のファイル作成

    Arguments:
        msg: メニューID
        taskId: DBオブジェクト
        uploadDir:
    Returns:
        実行結果
    """
    resultFileName = "ResultData_" + taskId + ".log"
    uploadFilePath = uploadDir + "/" + taskId + "/" + resultFileName

    # ファイルの作成
    if not os.path.isdir(uploadDir + "/" + taskId):
        os.makedirs(uploadDir + "/" + taskId)
        os.chmod(uploadDir + "/" + taskId, 0o777)
    if os.path.exists(uploadFilePath):
        with open(uploadFilePath, 'a') as f:
            f.write(msg)
        f.close()
    else:
        pathlib.Path(uploadFilePath).write_text(msg + "\n", encoding="utf-8")

    return True

def zip(execution_no, dirPath, status_id, zipFileName, objdbca):
    """

    ディレクトリ配下をzipに固める

    Arguments:
        execution_no: 作業番号
        dirPath: zipにするディレクトリのある個所
        status: ステータス
        zipFileName: ファイル名
    Returns:
        実行結果
    """

    result = False
    shutil.make_archive(base_name=dirPath + "/tmp_zip", format="zip", root_dir=dirPath + "/tmp_zip")

    objdbca.db_transaction_start()

    try:
        # 対象レコードの更新前の情報を取得
        export_import_sql = " SELECT * FROM T_BULK_EXCEL_EXPORT_IMPORT WHERE DISUSE_FLAG <> 1 AND EXECUTION_NO = %s "
        data_list = objdbca.sql_execute(export_import_sql, [execution_no])
        for data in data_list:
            last_update_taimestamp = data['LAST_UPDATE_TIMESTAMP']

        # ステータス取得
        status_data = objdbca.table_select("T_DP_STATUS_MASTER", 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [status_id, 0])
        for data in status_data:
            if g.LANGUAGE == "ja":
                status = data["TASK_STATUS_NAME_JA"]
            else:
                status = data["TASK_STATUS_NAME_EN"]

        # ファイル更新用パラメータを作成
        parameters = {
            "file": {
                "file_name": file_encode(dirPath + "/tmp_zip.zip")
            },
            "parameter": {
                "file_name": zipFileName,
                "status": status,
                "last_updated_user": g.USER_ID,
                "last_update_date_time": last_update_taimestamp.strftime('%Y/%m/%d %H:%M:%S.%f'),
            },
            "type": "Update"
        }

        objmenu = load_table.loadTable(objdbca, 'bulk_excel_export_import_list')
        retAry = objmenu.exec_maintenance(parameters, execution_no, "", False, False, True)  # noqa: E999
        result = retAry[0]
        if result is False:
            raise AppException("499-00701", [retAry], [retAry])

        objdbca.db_transaction_end(True)

    except Exception:
        objdbca.db_transaction_end(False)
        return False

    return result

def registerResultFile(taskId, objdbca):
    """

    dump結果ファイルの登録

    Arguments:
        taskId: タスクID
        RESULT_PATH: ResultDataの出力先
    Returns:
        実行結果
    """

    resultFileName = "ResultData_" + taskId + ".log"

    objdbca.db_transaction_start()
    try:
        # 通常テーブルで更新
        target = {
            "RESULT_FILE": resultFileName,
            "EXECUTION_NO": taskId,
            "LAST_UPDATE_USER": g.USER_ID
        }

        objdbca.table_update("T_BULK_EXCEL_EXPORT_IMPORT", target, "EXECUTION_NO", False)

        objdbca.db_transaction_end(True)

    except Exception:
        objdbca.db_transaction_end(False)
        return False

    return True

def check_menu_info(menu, wsdb_istc=None):
    """
    check_menu_info

    Arguments:
        menu: menu_name_rest
        wsdb_istc: (class)DBConnectWs Instance
    Returns:
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

def check_sheet_type(menu, sheet_type_list, wsdb_istc=None):
    """
    check_sheet_type

    Arguments:
        menu: menu_name_rest
        sheet_type_list: (list)許容するシートタイプのリスト,falseの場合はシートタイプのチェックを行わない
        wsdb_istc: (class)DBConnectWs Instance
    Returns:
        (dict)T_COMN_MENU_TABLE_LINKの該当レコード
    """
    if not wsdb_istc:
        wsdb_istc = DBConnectWs(g.get('WORKSPACE_ID'))  # noqa: F405

    query_str = textwrap.dedent("""
        SELECT * FROM `T_COMN_MENU_TABLE_LINK` TAB_A
            LEFT JOIN `T_COMN_MENU` TAB_B ON ( TAB_A.`MENU_ID` = TAB_B.`MENU_ID`)
        WHERE TAB_B.`MENU_NAME_REST` = %s AND
              TAB_A.`DISUSE_FLAG`='0' AND
              TAB_B.`DISUSE_FLAG`='0'
    """).strip()

    menu_table_link_record = wsdb_istc.sql_execute(query_str, [menu])

    if not menu_table_link_record:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00003", log_msg_args, api_msg_args)  # noqa: F405

    if sheet_type_list and menu_table_link_record[0].get('SHEET_TYPE') not in sheet_type_list:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00001", log_msg_args, api_msg_args)  # noqa: F405

    return menu_table_link_record