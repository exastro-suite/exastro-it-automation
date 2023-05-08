#   Copyright 2023 NEC Corporation
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
from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
import datetime
from common_libs.common.exception import AppException
from common_libs.common.util import get_exastro_platform_users
from common_libs.terraform_driver.common.Const import Const as TFCommonConst
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
import os
import json
import pathlib


def insert_execution_list(objdbca, run_mode, driver_id, operation_row=None, movement_row=None, scheduled_date=None, conductor_id=None, conductor_name=None, tf_workspace_name=None):  # noqa: E501
    """
        作業実行を登録
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            type: 1: '作業実行' or 2:'Plan確認' or 3:'パラメータ確認' or 4:'リソース削除'
            driver_id: ドライバ区分　'TERE(terraform_cloud_ep)' or 'TERC(terraform_cli)'
            operation_row: オペレーション情報
            movement_row: movement情報
            schedule_date: 予約日時 yyyy/mm/dd hh:mm:ss
            conductor_id: conductorID
            conductor_name: conductor name
        RETRUN:
            {"execution_no": "XXXXXXXX"}
    """
    # 変数定義
    user_id = g.USER_ID
    table_dict = {}
    table_dict["MENU_NAME"] = {}
    table_dict["MENU_NAME"][TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP] = TFCloudEPConst.RN_EXECUTION_LIST
    table_dict["MENU_NAME"][TFCommonConst.DRIVER_TERRAFORM_CLI] = TFCLIConst.RN_EXECUTION_LIST
    table_dict["MENU_ID"] = {}
    table_dict["MENU_ID"][TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP] = TFCloudEPConst.ID_EXECUTION_LIST
    table_dict["MENU_ID"][TFCommonConst.DRIVER_TERRAFORM_CLI] = TFCLIConst.ID_EXECUTION_LIST
    menu_name = table_dict["MENU_NAME"][driver_id]
    menu_id = table_dict["MENU_ID"][driver_id]
    exec_sts_inst_table_confg = {}
    now_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    # loadtyable.pyで使用するCOLUMN_NAME_RESTを取得
    rest_name_config = {}
    sql = "SELECT COL_NAME,COLUMN_NAME_REST FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = '%s' and DISUSE_FLAG = '0'" % (menu_id)
    restcolnamerow = objdbca.sql_execute(sql, [])
    for row in restcolnamerow:
        rest_name_config[row["COL_NAME"]] = row["COLUMN_NAME_REST"]

    # 予約日時が指定されている場合、型を変換
    if isinstance(scheduled_date, datetime.datetime):
        # yyyy-mm-dd hh:mm:ss -> yyyy/mm/dd hh:mm:ss
        scheduled_date = scheduled_date.strftime('%Y/%m/%d %H:%M:%S')

    # 実行種別の登録値を設定
    if g.LANGUAGE == 'ja':
        sql = "SELECT EXEC_MODE_NAME_JA AS EXEC_MODE_NAME FROM T_TERF_EXEC_MODE WHERE EXEC_MODE_ID = %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT EXEC_MODE_NAME_EN AS EXEC_MODE_NAME FROM T_TERF_EXEC_MODE WHERE EXEC_MODE_ID = %s AND DISUSE_FLAG = '0'"
    rows = objdbca.sql_execute(sql, [run_mode])
    # マスタなので件数チェックしない
    row = rows[0]
    exec_sts_inst_table_confg[rest_name_config["RUN_MODE"]] = row['EXEC_MODE_NAME']

    # 予約日時が指定されている場合「9:未実行(予約)」指定がなければ「1:未実行」
    status_id = '9' if scheduled_date else '1'

    # ステータスの登録値を設定
    if g.LANGUAGE == 'ja':
        sql = "SELECT EXEC_STATUS_NAME_JA AS EXEC_STATUS_NAME FROM T_TERF_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT EXEC_STATUS_NAME_EN AS EXEC_STATUS_NAME FROM T_TERF_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    rows = objdbca.sql_execute(sql, [status_id])
    # マスタなので件数チェックしない
    row = rows[0]
    exec_sts_inst_table_confg[rest_name_config["STATUS_ID"]] = row["EXEC_STATUS_NAME"]

    # ユーザーIDに紐づく名称取得
    user_list = search_user_list(objdbca)

    # 実行ユーザの登録値を設定
    exec_sts_inst_table_confg[rest_name_config["EXECUTION_USER"]] = user_list.get(user_id)

    # 登録日時の登録値を設定
    exec_sts_inst_table_confg[rest_name_config["TIME_REGISTER"]] = now_time

    # 実行種別により登録する値が異なる
    if run_mode == TFCommonConst.RUN_MODE_DESTROY:
        # 実行種別「リソース削除」の場合
        # tf_workspace_nameの存在有無を確認
        where_str = 'WHERE WORKSPACE_NAME = %s AND DISUSE_FLAG = %s'
        if driver_id == TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP:
            tf_work_record = objdbca.table_select(TFCloudEPConst.V_ORGANIZATION_WORKSPACE, where_str, [tf_workspace_name, 0])
        else:
            tf_work_record = objdbca.table_select(TFCLIConst.T_WORKSPACE, where_str, [tf_workspace_name, 0])
        if not tf_work_record:
            # 対処のTerraform Workspaceのレコードが存在しません。(tf_workspace_name: {})
            raise AppException("499-00918", [tf_workspace_name], [tf_workspace_name])

        # id/nameを取得
        tf_workspace_id = tf_work_record[0].get('WORKSPACE_ID')
        if driver_id == TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP:
            tf_workspace_name = tf_work_record[0].get('ORGANIZATION_WORKSPACE')
        else:
            tf_workspace_name = tf_work_record[0].get('WORKSPACE_NAME')

        # Movement/Terraform利用情報/workspace_idの登録値を設定
        column_workspace_id = driver_id + "_WORKSPACE_ID"
        exec_sts_inst_table_confg[rest_name_config["I_WORKSPACE_ID"]] = tf_workspace_id

        # Terraform Workspace名称の登録値を設定
        exec_sts_inst_table_confg[rest_name_config["I_WORKSPACE_NAME"]] = tf_workspace_name

    else:
        # 実行種別「通常」「Plan確認」「パラメータ確認」の場合
        # Movement/IDの登録値を設定
        exec_sts_inst_table_confg[rest_name_config["MOVEMENT_ID"]] = movement_row["MOVEMENT_ID"]

        # Movement/名称の登録値を設定
        exec_sts_inst_table_confg[rest_name_config["I_MOVEMENT_NAME"]] = movement_row["MOVEMENT_NAME"]

        # Movement/遅延タイマーの登録値を設定
        exec_sts_inst_table_confg[rest_name_config["I_TIME_LIMIT"]] = movement_row["TIME_LIMIT"]

        # Movement/Terraform利用情報/workspace_idの登録値を設定
        column_workspace_id = driver_id + "_WORKSPACE_ID"
        exec_sts_inst_table_confg[rest_name_config["I_WORKSPACE_ID"]] = movement_row[column_workspace_id]

        # 対象のWorkspace名称を取得
        where_str = 'WHERE WORKSPACE_ID = %s AND DISUSE_FLAG = %s'
        if driver_id == TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP:
            tf_work_record = objdbca.table_select(TFCloudEPConst.V_ORGANIZATION_WORKSPACE, where_str, [movement_row[column_workspace_id], 0])
        else:
            tf_work_record = objdbca.table_select(TFCLIConst.T_WORKSPACE, where_str, [movement_row[column_workspace_id], 0])

        if not tf_work_record:
            # メッセージ一覧から取得。Movementに紐付くWorkspaceが不正です。
            raise AppException("499-00919", [movement_row[column_workspace_id]], [movement_row[column_workspace_id]])

        # Terraform Workspace名称の登録値を設定
        if driver_id == TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP:
            tf_workspace_name = tf_work_record[0].get('ORGANIZATION_WORKSPACE')
        else:
            tf_workspace_name = tf_work_record[0].get('WORKSPACE_NAME')
        exec_sts_inst_table_confg[rest_name_config["I_WORKSPACE_NAME"]] = tf_workspace_name

        # オペレーション/Noの登録値を設定
        exec_sts_inst_table_confg[rest_name_config["OPERATION_ID"]] = operation_row["OPERATION_ID"]

        # オペレーション/名称の登録値を設定
        exec_sts_inst_table_confg[rest_name_config["I_OPERATION_NAME"]] = operation_row["OPERATION_NAME"]

        # 作業状況/予約日時
        exec_sts_inst_table_confg[rest_name_config["TIME_BOOK"]] = scheduled_date

        # 呼び出し元Conductor名の登録値を設定
        exec_sts_inst_table_confg[rest_name_config["CONDUCTOR_NAME"]] = conductor_name

        # 呼び出し元ConductorIDの登録値を設定
        exec_sts_inst_table_confg[rest_name_config["CONDUCTOR_INSTANCE_NO"]] = conductor_id

    # 廃止フラグの登録値を設定
    exec_sts_inst_table_confg[rest_name_config["DISUSE_FLAG"]] = '0'

    # 最終更新日時の登録値を設定
    exec_sts_inst_table_confg[rest_name_config["LAST_UPDATE_TIMESTAMP"]] = now_time

    # 最終更新者の登録値を設定
    exec_sts_inst_table_confg[rest_name_config["LAST_UPDATE_USER"]] = user_id

    # レコード登録RESTAPIを実行
    parameters = {
        "parameter": exec_sts_inst_table_confg,
        "type": "Register"
    }
    objmenu = load_table.loadTable(objdbca, menu_name)  # noqa: F405
    ret_array = objmenu.exec_maintenance(parameters, "", "", False, False)
    result = ret_array[0]
    if result is True:
        uuid = ret_array[1]["execution_no"]
    else:
        raise AppException("499-00701", [ret_array], [ret_array])

    return {"execution_no": uuid}


def get_execution_info(objdbca, target, execution_no):
    """
        作業実行の状態取得
        ARGS:
            objdbca:DB接続クラス  DBConnectWs()
            target: 作業実行メニューのRest名(execution_list)とテーブル名(table_name)
            execution_no: 作業実行No
        RETRUN:
            data
    """
    base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
    execution_list_menu_name_rest = target['execution_list']

    # 該当の作業管理を取得(ID変換のためloadTableで取得)
    objmenu = load_table.loadTable(objdbca, execution_list_menu_name_rest)  # noqa: F405
    filter_parameter = {
        "execution_no": {"LIST": [execution_no]}
    }
    tmp_result = objmenu.rest_filter(filter_parameter)

    # 該当する作業管理が存在しない
    if len(tmp_result[1]) != 1:
        log_msg_args = [execution_no]
        api_msg_args = [execution_no]
        raise AppException("499-00903", log_msg_args, api_msg_args)

    # 隠しカラムを取得するために作業管理をSQLでも検索
    where = "WHERE EXECUTION_NO = %s"
    data_list = objdbca.table_select(target['table_name'], where, [execution_no])
    # 該当する作業管理が存在しない
    if len(data_list) is None or len(data_list) == 0:
        log_msg_args = [execution_no]
        api_msg_args = [execution_no]
        raise AppException("499-00903", log_msg_args, api_msg_args)

    table_row = data_list[0]

    execution_info = {}
    # 作業管理
    execution_info['execution_list'] = tmp_result[1][0]
    # ステータスIDはコード値も返却
    execution_info['status_id'] = table_row['STATUS_ID']

    # ログ情報
    execution_info['progress'] = {}
    execution_info['progress']['execution_log'] = {}
    execution_info['progress']['execution_log']['exec_log'] = {}
    if execution_list_menu_name_rest == TFCloudEPConst.RN_EXECUTION_LIST:
        path = base_dir + TFCloudEPConst.DIR_EXECUTE + '/' + execution_no
    else:
        path = base_dir + TFCLIConst.DIR_EXECUTE + '/' + execution_no

    # print("対象のパスは：")
    # print(path)
    if table_row['MULTIPLELOG_MODE'] == 1:
        if not table_row['LOGFILELIST_JSON']:
            list_log = []
        else:
            list_log = json.loads(table_row['LOGFILELIST_JSON'])
        for log in list_log:
            log_file_path = path + '/out/' + log
            if os.path.isfile(log_file_path):
                lcstr = pathlib.Path(log_file_path).read_text(encoding="utf-8")
                execution_info['progress']['execution_log']['exec_log'][log] = lcstr

    log_file_path = path + '/out/error.log'
    if os.path.isfile(log_file_path):
        lcstr = pathlib.Path(log_file_path).read_text(encoding="utf-8")
        execution_info['progress']['execution_log']['error_log'] = lcstr

    # 状態監視周期・進行状態表示件数
    if execution_list_menu_name_rest == TFCloudEPConst.RN_EXECUTION_LIST:
        if_info_table = TFCloudEPConst.T_IF_INFO
    else:
        if_info_table = TFCLIConst.T_IF_INFO
    where = ""
    tmp_data_list = objdbca.table_select(if_info_table, where)
    for tmp_row in tmp_data_list:
        execution_info['status_monitoring_cycle'] = tmp_row['TERRAFORM_REFRESH_INTERVAL']
        execution_info['number_of_rows_to_display_progress_status'] = tmp_row['TERRAFORM_TAILLOG_LINES']

    return execution_info


def search_user_list(objdbca):
    """
        データリストを検索する
        ARGS:
            なし
        RETRUN:
            データリスト
    """
    users_list = {}
    user_env = g.LANGUAGE.upper()
    usr_name_col = "USER_NAME_{}".format(user_env)
    table_name = "T_COMN_BACKYARD_USER"
    where_str = "WHERE DISUSE_FLAG='0'"
    bind_value_list = []

    return_values = objdbca.table_select(table_name, where_str, bind_value_list)

    for bk_user in return_values:
        users_list[bk_user['USER_ID']] = bk_user[usr_name_col]

    user_id = g.get('USER_ID')
    if user_id not in users_list:
        pf_users = get_exastro_platform_users()

        users_list.update(pf_users)

    return users_list


def reserve_cancel(objdbca, driver_id, execution_no):
    """
        予約取消
        ARGS:
            objdbca:DB接続クラス  DBConnectWs()
            driver_id: ドライバ区分
            execution_no: 作業実行No
        RETRUN:
            status: SUCCEED
            execution_no: 作業No
    """
    TableDict = {}
    TableDict["TABLE_NAME"] = {}
    TableDict["TABLE_NAME"][TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP] = TFCloudEPConst.T_EXEC_STS_INST
    TableDict["TABLE_NAME"][TFCommonConst.DRIVER_TERRAFORM_CLI] = TFCLIConst.T_EXEC_STS_INST
    TableName = TableDict["TABLE_NAME"][driver_id]

    # 該当の作業実行のステータス取得
    where = "WHERE EXECUTION_NO = %s"
    objdbca.table_lock([TableName])
    data_list = objdbca.table_select(TableName, where, [execution_no])

    # 該当する作業実行が存在しない
    if len(data_list) is None or len(data_list) == 0:
        log_msg_args = [execution_no]
        api_msg_args = [execution_no]
        raise AppException("499-00903", log_msg_args, api_msg_args)

    for row in data_list:
        # ステータスが未実行(予約)でない
        if not row['STATUS_ID'] == TFCommonConst.STATUS_RESERVE:
            # ステータス取得
            where = "WHERE EXEC_STATUS_ID = " + row['STATUS_ID']
            tmp_data_list = objdbca.table_select(TFCommonConst.T_EXEC_STATUS, where)
            for tmp_row in tmp_data_list:
                if g.LANGUAGE == 'ja':
                    status = tmp_row['EXEC_STATUS_NAME_JA']
                else:
                    status = tmp_row['EXEC_STATUS_NAME_EN']

            log_msg_args = [status]
            api_msg_args = [status]
            raise AppException("499-00910", log_msg_args, api_msg_args)

        # ステータスを予約取消に変更
        update_list = {'EXECUTION_NO': execution_no, 'STATUS_ID': TFCommonConst.STATUS_RESERVE_CANCEL}
        objdbca.table_update(TableName, update_list, 'EXECUTION_NO', True)
        objdbca.db_commit()

    result_msg = g.appmsg.get_api_message("MSG-10904", [execution_no])
    return result_msg
