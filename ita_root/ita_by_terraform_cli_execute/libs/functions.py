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
import subprocess
import os

# from common_libs.common.exception import AppException
from common_libs.common.util import file_encode
from common_libs.loadtable import load_table


def get_execution_process_info(wsDb, const, execution_no):
    """
    作業実行の情報を取得

    Arguments:
        WsDb: db instance
        const: 共通定数オブジェクト
        execution_no: 作業番号
    Returns:
        result: bool
        record or err_msg:
    """
    condition = "WHERE `DISUSE_FLAG`=0 AND `EXECUTION_NO`=%s"
    records = wsDb.table_select(const.T_EXEC_STS_INST, condition, [execution_no])

    if len(records) == 0:
        return False, g.appmsg.get_log_message("MSG-10047", [execution_no])

    return True, records[0]


def update_execution_record(wsDb, const, update_data, tmp_execution_dir=""):
    """
    作業実行の情報を更新

    Arguments:
        WsDb: db instance
        const: 共通定数オブジェクト
        update_data: 更新データ
        tmp_execution_dir: zipファイルのある一時格納のベースディレクトリ
    Returns:
        result: bool
        record:
    """
    execution_no = update_data['EXECUTION_NO']

    sql = "SELECT * FROM {} WHERE EXECUTION_NO=%s".format(const.T_EXEC_STS_INST)
    rows = wsDb.sql_execute(sql, [execution_no])
    execute_data = rows[0]

    # 必要のない更新項目を落とす
    if "TIME_START" in update_data and execute_data["TIME_START"]:
        del update_data["TIME_START"]
    if "TIME_END" in update_data and execute_data["TIME_END"]:
        del update_data["TIME_END"]
    if "LAST_UPDATE_USER" not in update_data:
        update_data["LAST_UPDATE_USER"] = g.USER_ID

    # uploadするカラムを特定
    file_upload_column_name = ""
    if "FILE_INPUT" in update_data:
        file_upload_column_name = "FILE_INPUT"
    elif "FILE_RESULT" in update_data:
        file_upload_column_name = "FILE_RESULT"

    if file_upload_column_name == "":
        # ファイルアップロードがなし　→　ただのアップデート
        result = wsDb.table_update(const.T_EXEC_STS_INST, [update_data], 'EXECUTION_NO')

        if result is False:
            wsDb.db_rollback()
            return False, None
        # transactionは呼び元で管理したいので、commitだけはやらない
        # else:
        #     wsDb.db_commit()
    else:
        # ファイルアップロードがあり
        # loadtyable.pyで使用するCOLUMN_NAME_RESTを取得
        file_upload(wsDb, const, update_data, execute_data, file_upload_column_name, tmp_execution_dir)

    for column, value in update_data.items():
        execute_data[column] = value

    return True, execute_data


def file_upload(wsDb, const, update_data, execute_data, file_upload_column_name, tmp_execution_dir):
    execution_no = update_data['EXECUTION_NO']
    menu_id = const.ID_EXECUTION_LIST

    rest_name_config = {}
    # あえて廃止にしている項目もあり、要確認が必要
    sql = "SELECT COL_NAME,COLUMN_NAME_REST FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = %s and DISUSE_FLAG = '0'"
    rows = wsDb.sql_execute(sql, [menu_id])
    for row in rows:
        rest_name_config[row["COL_NAME"]] = row["COLUMN_NAME_REST"]

    # 作業番号
    execute_table_paramater = {}
    execute_table_paramater[rest_name_config["EXECUTION_NO"]] = execution_no

    # ステータス
    if g.LANGUAGE == 'ja':
        sql = "SELECT EXEC_STATUS_NAME_JA AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT EXEC_STATUS_NAME_EN AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    rows = wsDb.sql_execute(sql, [update_data["STATUS_ID"]])
    execute_table_paramater[rest_name_config["STATUS_ID"]] = rows[0]["NAME"]

    if "TIME_START" in update_data:
        execute_table_paramater[rest_name_config["TIME_START"]] = update_data['TIME_START'].strftime('%Y/%m/%d %H:%M:%S')
    if "TIME_END" in update_data:
        execute_table_paramater[rest_name_config["TIME_END"]] = update_data['TIME_END'].strftime('%Y/%m/%d %H:%M:%S')
    if "MULTIPLELOG_MODE" in update_data:
        execute_table_paramater[rest_name_config["MULTIPLELOG_MODE"]] = update_data["MULTIPLELOG_MODE"]
    if "LOGFILELIST_JSON" in update_data:
        execute_table_paramater[rest_name_config["LOGFILELIST_JSON"]] = update_data["LOGFILELIST_JSON"]

    # 投入データ/結果データ用zip
    uploadfiles = {}
    zip_tmp_save_path = ""
    if file_upload_column_name == "FILE_INPUT":
        # 出力データ
        execute_table_paramater[rest_name_config["FILE_INPUT"]] = update_data["FILE_INPUT"]
        zip_tmp_save_path = tmp_execution_dir + "/" + update_data["FILE_INPUT"]
    elif file_upload_column_name == "FILE_RESULT":
        # 結果データ
        execute_table_paramater[rest_name_config["FILE_RESULT"]] = update_data["FILE_RESULT"]
        zip_tmp_save_path = tmp_execution_dir + "/" + update_data["FILE_RESULT"]

    if os.path.isfile(zip_tmp_save_path):
        # zipファイルをエンコードする
        ZipDataData = file_encode(zip_tmp_save_path)
        if ZipDataData is False:
            # エンコード失敗
            msgstr = g.appmsg.get_api_message("BKY-52001", [execution_no])
            g.applogger.error(msgstr)
            return False, msgstr
        uploadfiles = {rest_name_config[file_upload_column_name]: ZipDataData}

        # 一時的に作成したzipファイル削除
        subprocess.run(['/bin/rm', '-fr', '*'], cwd=tmp_execution_dir)

    # 最終更新日時
    execute_table_paramater[rest_name_config["LAST_UPDATE_TIMESTAMP"]] = execute_data['LAST_UPDATE_TIMESTAMP'].strftime('%Y/%m/%d %H:%M:%S.%f')  # noqa:E501

    # load_tableで更新
    parameters = {
        "parameter": execute_table_paramater,
        "file": uploadfiles,
        "type": "Update"
    }
    menu_name = "execution_list_terraform_cli"
    objmenu = load_table.loadTable(wsDb, menu_name)
    retAry = objmenu.exec_maintenance(parameters, execution_no, "", False, False, True)
    if retAry[0] is False:
        raise Exception(str(retAry))

    return True
