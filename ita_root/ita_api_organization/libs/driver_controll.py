#   Copyright 2022 NEC Corporation
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


from flask import g  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
import re
import os
import datetime
import json
import pathlib
from common_libs.common.exception import AppException
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnslConstClass import AnslConst
from common_libs.ansible_driver.classes.AnspConstClass import AnspConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.functions.util import getAnsibleExecutDirPath
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst


def movement_registr_check(objdbca, parameter, menu_id, Required=False):
    """
        リクエストボディのMovement_id確認
        ARGS:
            objdbca:DB接続クラス  DBConnectWs()
            parameter: bodyの中身
            Required: リクエストボディのMovement_idが必須か
                      True:必須　False:任意
            menu_id: menu id
        RETRUN:
            movement情報
    """
    orchestra_id = {'execution_ansible_legacy': '1',
                    'execution_ansible_pioneer': '2',
                    'execution_ansible_role': '3',
                    TFCloudEPConst.RN_EXECTION: '4',
                    TFCLIConst.RN_EXECTION: '5'}

    keyName = "movement_name"
    if keyName in parameter:
        movement_name = parameter[keyName]
    else:
        movement_name = None
    if Required is True:
        if not movement_name:
            # リクエストボディにパラメータなし
            raise AppException("499-00908", [keyName], [keyName])
    if movement_name:
        # Movement情報取得
        sql = "SELECT * FROM T_COMN_MOVEMENT WHERE MOVEMENT_NAME = %s AND ITA_EXT_STM_ID = %s AND DISUSE_FLAG='0'"
        row = objdbca.sql_execute(sql, [movement_name, orchestra_id[menu_id]])
        if len(row) != 1:
            # Movement未登録
            raise AppException("499-00901", [movement_name], [movement_name])
        return row[0]


def operation_registr_check(objdbca, parameter, Required=False):
    """
        リクエストボディのoperation_id確認
        ARGS:
            objdbca:DB接続クラス  DBConnectWs()
            parameter: bodyの中身
            Required: リクエストボディのoperation_idが必須か
                      True:必須　False:任意
        RETRUN:
            オペレーション情報
    """
    keyName = "operation_name"
    if keyName in parameter:
        operation_name = parameter[keyName]
    else:
        operation_name = None
    if Required is True:
        if not operation_name:
            # リクエストボディにパラメータなし
            raise AppException("499-00908", [keyName], [keyName])
    if operation_name:
        # オペレーション情報取得
        sql = "SELECT * FROM T_COMN_OPERATION WHERE OPERATION_NAME = %s AND DISUSE_FLAG='0'"
        row = objdbca.sql_execute(sql, [operation_name])
        if len(row) != 1:
            # オペレーション未登録
            raise AppException("499-00902", [operation_name], [operation_name])
        return row[0]


def scheduled_format_check(parameter, useed=False):
    keyName = "schedule_date"
    if keyName in parameter:
        schedule_date = parameter[keyName]
    else:
        schedule_date = None

    if schedule_date:
        if useed is False:
            # 予約日時は不要
            raise AppException("499-00907", [], [])
        else:
            result = True
            # 予約時間のフォーマット確認
            match = re.findall(r"^[0-9]{4}/[0-9]{2}/[0-9]{2}[\s][0-9]{2}:[0-9]{2}:[0-9]{2}$", schedule_date)
            if len(match) == 0:
                result = False
            else:
                try:
                    # 予約時間を確認
                    schedule_date = datetime.datetime.strptime(schedule_date, '%Y/%m/%d %H:%M:%S')
                except Exception:
                    result = False
            if result is False:
                # 予約日時不正
                raise AppException("499-00906", [], [])
        return schedule_date


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

    # 該当の作業管理を取得(ID変換のためloadTableで取得)
    objmenu = load_table.loadTable(objdbca, target['execution_list'])
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

    path = getAnsibleExecutDirPath(target['ansConstObj'], execution_no)

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

    log_file_path = path + '/out/exec.log'
    if os.path.isfile(log_file_path):
        lcstr = pathlib.Path(log_file_path).read_text(encoding="utf-8")
        execution_info['progress']['execution_log']['exec_log']['exec.log'] = lcstr

    log_file_path = path + '/out/error.log'
    if os.path.isfile(log_file_path):
        lcstr = pathlib.Path(log_file_path).read_text(encoding="utf-8")
        execution_info['progress']['execution_log']['error_log'] = lcstr

    # 状態監視周期・進行状態表示件数
    where = ""
    tmp_data_list = objdbca.table_select("T_ANSC_IF_INFO", where)
    for tmp_row in tmp_data_list:
        execution_info['status_monitoring_cycle'] = tmp_row['ANSIBLE_REFRESH_INTERVAL']
        execution_info['number_of_rows_to_display_progress_status'] = tmp_row['ANSIBLE_TAILLOG_LINES']

    return execution_info


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
    TableDict["TABLE_NAME"][AnscConst.DF_LEGACY_DRIVER_ID] = AnslConst.vg_exe_ins_msg_table_name
    TableDict["TABLE_NAME"][AnscConst.DF_PIONEER_DRIVER_ID] = AnspConst.vg_exe_ins_msg_table_name
    TableDict["TABLE_NAME"][AnscConst.DF_LEGACY_ROLE_DRIVER_ID] = AnsrConst.vg_exe_ins_msg_table_name
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
        if not row['STATUS_ID'] == AnscConst.RESERVE:
            # ステータス取得
            where = "WHERE EXEC_STATUS_ID = " + row['STATUS_ID']
            tmp_data_list = objdbca.table_select("T_ANSC_EXEC_STATUS", where)
            for tmp_row in tmp_data_list:
                if g.LANGUAGE == 'ja':
                    status = tmp_row['EXEC_STATUS_NAME_JA']
                else:
                    status = tmp_row['EXEC_STATUS_NAME_EN']

            log_msg_args = [status]
            api_msg_args = [status]
            raise AppException("499-00910", log_msg_args, api_msg_args)

        # ステータスを予約取消に変更
        update_list = {'EXECUTION_NO': execution_no, 'STATUS_ID': AnscConst.RESERVE_CANCEL}
        # ret = objdbca.table_update(TableName, update_list, 'EXECUTION_NO', True)
        objdbca.table_update(TableName, update_list, 'EXECUTION_NO', True)
        objdbca.db_commit()

    result_msg = g.appmsg.get_api_message("MSG-10904", [execution_no])
    return result_msg
