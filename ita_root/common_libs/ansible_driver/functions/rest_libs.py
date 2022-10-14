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

from common_libs.common import *
from common_libs.loadtable import *
import os
import datetime
from common_libs.common.exception import AppException
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.ansible_execute import AnsibleExecute
from common_libs.common.util import file_encode, get_exastro_platform_users
from common_libs.ansible_driver.functions.util import *
from common_libs.ansible_driver.functions.util import getMovementAnsibleCnfUploadDirPath
from common_libs.ansible_driver.classes.ansibletowerlibs.RestApiCaller import RestApiCaller
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiWorkflowJobs import AnsibleTowerRestApiWorkflowJobs


def insert_execution_list(objdbca, run_mode, driver_id, operation_row, movement_row, scheduled_date, conductor_id, conductor_name):
    """
        作業実行を登録
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            type: 1: '作業実行' or 2:'ドライラン' or 3:'パラメータ確認'
            driver_id: ドライバ区分　AnscConst().DF_LEGACY_ROLE_DRIVER_ID
            operation_row: オペレーション情報
            movement_row: movement情報
            schedule_date: 予約日時 yyyy/mm/dd hh:mm:ss
            conductor_id: conductorID
            conductor_name: conductor name
        RETRUN:
            {"execution_no": "aaaaaaaaaaaaaaaaaaaaa"}
    """
    user_id = g.USER_ID
    objAnsc = AnscConst()
    TableDict = {}
    TableDict["MENU"] = {}
    TableDict["MENU"][objAnsc.DF_LEGACY_DRIVER_ID] = "Not supported"
    TableDict["MENU"][objAnsc.DF_PIONEER_DRIVER_ID] = "Not supported"
    TableDict["MENU"][objAnsc.DF_LEGACY_ROLE_DRIVER_ID] = "execution_list_ansible_role"
    MenuName = TableDict["MENU"][driver_id]

    # loadtyable.pyで使用するCOLUMN_NAME_RESTを取得
    RestNameConfig = {}
    sql = "SELECT COL_NAME,COLUMN_NAME_REST FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = '20412' and DISUSE_FLAG = '0'"
    restcolnamerow = objdbca.sql_execute(sql, [])
    for row in restcolnamerow:
        RestNameConfig[row["COL_NAME"]] = row["COLUMN_NAME_REST"]

    ExecStsInstTableConfig = {}

    if isinstance(scheduled_date, datetime.datetime):
        # yyyy-mm-dd hh:mm:ss -> yyyy/mm/dd hh:mm:ss
        scheduled_date = scheduled_date.strftime('%Y/%m/%d %H:%M:%S')
        
    # ansibleインターフェース情報取得
    sql = "SELECT * FROM T_ANSC_IF_INFO WHERE DISUSE_FLAG='0'"
    inforow = objdbca.sql_execute(sql, [])
    # 件数判定はしない
    inforow = inforow[0]

    nowTime = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    
    # 作業管理に追加するレコード生成
    
    # 実行種別
    if g.LANGUAGE == 'ja':
        sql = "SELECT EXEC_MODE_NAME_JA AS NAME FROM T_ANSC_EXEC_MODE WHERE EXEC_MODE_ID = %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT EXEC_MODE_NAME_EN AS NAME  FROM T_ANSC_EXEC_MODE WHERE EXEC_MODE_ID = %s AND DISUSE_FLAG = '0'"
    rows = objdbca.sql_execute(sql, [run_mode])
    # マスタなので件数チェックしない
    row = rows[0]
    ExecStsInstTableConfig[RestNameConfig["RUN_MODE"]] = row['NAME']

    if scheduled_date:
        status = objAnsc.RESERVE
    else:
        status = objAnsc.NOT_YET
    # ステータス:未実行
    if g.LANGUAGE == 'ja':
        sql = "SELECT EXEC_STATUS_NAME_JA AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID	= %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT EXEC_STATUS_NAME_EN AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID	= %s AND DISUSE_FLAG = '0'"
    rows = objdbca.sql_execute(sql, [status])
    # マスタなので件数チェックしない
    row = rows[0]
    ExecStsInstTableConfig[RestNameConfig["STATUS_ID"]] = row["NAME"]
    
    # 実行エンジン
    sql = "SELECT NAME FROM T_ANSC_EXEC_ENGINE WHERE ID = %s AND DISUSE_FLAG = '0'"
    ExecMode = inforow['ANSIBLE_EXEC_MODE']
    rows = objdbca.sql_execute(sql, [ExecMode])
    # マスタなので件数チェックしない
    row = rows[0]
    ExecStsInstTableConfig[RestNameConfig["EXEC_MODE"]] = row["NAME"]

    # 呼出元Conductor
    ExecStsInstTableConfig[RestNameConfig["CONDUCTOR_NAME"]] = conductor_name

    # ユーザーIDに紐づく名称取得
    user_list = search_user_list(objdbca)
    # 実行ユーザ
    ExecStsInstTableConfig[RestNameConfig["EXECUTION_USER"]] = user_list[user_id]

    # 登録日時
    ExecStsInstTableConfig[RestNameConfig["TIME_REGISTER"]] = nowTime

    # Movement/ID
    ExecStsInstTableConfig[RestNameConfig["MOVEMENT_ID"]] = movement_row["MOVEMENT_ID"]

    # Movement/名称
    ExecStsInstTableConfig[RestNameConfig["I_MOVEMENT_NAME"]] = movement_row["MOVEMENT_NAME"]

    # Movement/遅延タイマー
    ExecStsInstTableConfig[RestNameConfig["I_TIME_LIMIT"]] = movement_row["TIME_LIMIT"]

    # Movement/Ansible利用情報/ホスト指定形式
    if g.LANGUAGE == 'ja':
        sql = "SELECT HOST_DESIGNATE_TYPE_NAME_JA AS NAME FROM T_COMN_HOST_DESIGNATE_TYPE WHERE HOST_DESIGNATE_TYPE_ID = %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT HOST_DESIGNATE_TYPE_NAME_EN AS NAME FROM T_COMN_HOST_DESIGNATE_TYPE WHERE HOST_DESIGNATE_TYPE_ID = %s AND DISUSE_FLAG = '0'"
    rows = objdbca.sql_execute(sql, [movement_row["ANS_HOST_DESIGNATE_TYPE_ID"]])
    # マスタなので件数チェックしない
    row = rows[0]
    ExecStsInstTableConfig[RestNameConfig["I_ANS_HOST_DESIGNATE_TYPE_ID"]] = row["NAME"]

    # 2.0では不要なので廃止レコードにしている
    # Movement/Ansible利用情報/並列実行数
    # ExecStsInstTableConfig[RestNameConfig["I_ANS_PARALLEL_EXE"]] = movement_row["ANS_PARALLEL_EXE"]

    # Movement/Ansible利用情報/WinRM接続
    if movement_row["ANS_WINRM_ID"]:
        sql = "SELECT FLAG_NAME FROM T_COMN_BOOLEAN_FLAG WHERE FLAG_ID = %s AND DISUSE_FLAG = '0'"
        rows = objdbca.sql_execute(sql, [movement_row["ANS_WINRM_ID"]])
        # マスタなので件数チェックしない
        row = rows[0]
    else:
        row["FLAG_NAME"] = None
    ExecStsInstTableConfig[RestNameConfig["I_ANS_WINRM_ID"]] = row["FLAG_NAME"]

    # Movement/Ansible利用情報/ヘッダーセクション
    ExecStsInstTableConfig[RestNameConfig["I_ANS_PLAYBOOK_HED_DEF"]] = movement_row["ANS_PLAYBOOK_HED_DEF"]

    if ExecMode == objAnsc.DF_EXEC_MODE_ANSIBLE:
        # Movement/Ansible-Core利用情報/virtualenv
        # ゴミになるので実行エンジンがansibleの場合のみ設定
        ExecStsInstTableConfig[RestNameConfig["I_ENGINE_VIRTUALENV_NAME"]] = movement_row["ANS_ENGINE_VIRTUALENV_NAME"]

    if ExecMode == objAnsc.DF_EXEC_MODE_AAC:
        # Movement/AnsibleAutomationController利用情報/実行環境
        # ゴミになるので実行エンジンがAnsibleAutomationControllerの場合のみ設定
        ExecStsInstTableConfig[RestNameConfig["I_EXECUTION_ENVIRONMENT_NAME"]] = movement_row["ANS_EXECUTION_ENVIRONMENT_NAME"]

    # Movement/ansible.cfg
    uploadfiles = {}
    AnsibleCfgFile = movement_row["ANS_ANSIBLE_CONFIG_FILE"]
    AnsibleCfgData = None
    if AnsibleCfgFile:
        ExecStsInstTableConfig[RestNameConfig["I_ANSIBLE_CONFIG_FILE"]] = movement_row["ANS_ANSIBLE_CONFIG_FILE"]
        path = "{}/{}/{}".format(getMovementAnsibleCnfUploadDirPath(), movement_row["MOVEMENT_ID"], AnsibleCfgFile)
        if os.path.isfile(path) is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])
        AnsibleCfgData = file_encode(path)
        if AnsibleCfgData is False:
            # エンコード失敗
            raise AppException("499-00909", [], [])
        
        uploadfiles = {RestNameConfig["I_ANSIBLE_CONFIG_FILE"]: AnsibleCfgData}

    # オペレーション/No.
    ExecStsInstTableConfig[RestNameConfig["OPERATION_ID"]] = operation_row["OPERATION_ID"]
    
    # オペレーション/名称
    ExecStsInstTableConfig[RestNameConfig["I_OPERATION_NAME"]] = operation_row["OPERATION_NAME"]

    # 入力データ/投入データ
    # ExecStsInstTableConfig[RestNameConfig["FILE_INPUT"]]

    # 出力データ/結果データ
    # ExecStsInstTableConfig[RestNameConfig["FILE_RESULT"]]

    # 作業状況/予約日時
    ExecStsInstTableConfig[RestNameConfig["TIME_BOOK"]] = scheduled_date

    # 作業状況/開始日時
    # ExecStsInstTableConfig[RestNameConfig["TIME_START"]]

    # 作業状況/終了日時
    # ExecStsInstTableConfig[RestNameConfig["TIME_END"]]

    # 2.0では不要なので廃止レコードにしている
    # 収集状況/ステータス
    # ExecStsInstTableConfig[RestNameConfig["COLLECT_STATUS"]]
    # 収集状況/収集ログ
    # ExecStsInstTableConfig[RestNameConfig["COLLECT_LOG"]]
    # Conductorインスタンス番号

    if conductor_id:                           
        ExecStsInstTableConfig[RestNameConfig["CONDUCTOR_INSTANCE_NO"]] = conductor_id

    # オプションパラメータ
    # ExecStsInstTableConfig[RestNameConfig["I_ANS_EXEC_OPTIONS"]] = str(inforow['ANSIBLE_EXEC_OPTIONS']) + ' ' + str(movement_row['ANS_EXEC_OPTIONS'])
    # 分割された実行ログ情報
    # ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]]
    # 実行ログ分割フラグ
    # ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]]

    # 備考
    # ExecStsInstTableConfig[RestNameConfig["NOTE"]]

    # 廃止フラグ
    ExecStsInstTableConfig[RestNameConfig["DISUSE_FLAG"]] = '0'

    # 最終更新日時
    ExecStsInstTableConfig[RestNameConfig["LAST_UPDATE_TIMESTAMP"]] = nowTime

    # 最終更新者
    ExecStsInstTableConfig[RestNameConfig["LAST_UPDATE_USER"]] = user_id

    parameters = {
        "parameter": ExecStsInstTableConfig,
        "file": uploadfiles,
        "type": "Register"
    }
    objmenu = load_table.loadTable(objdbca, MenuName)
    retAry = objmenu.exec_maintenance(parameters, "", "", False, False)
    # (False, '499-00201', {'host_specific_format': [{'status_code': '', 'msg_args': '', 'msg': '..'},,,]})
    result = retAry[0]
    if result is True:
        uuid = retAry[1]["execution_no"]
    else:
        raise AppException("499-00701", [retAry], [retAry])

    return {"execution_no": uuid}


def execution_scram(objdbca, driver_id, execution_no):
    """
        緊急停止
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            driver_id: ドライバ区分　AnscConst().DF_LEGACY_ROLE_DRIVER_ID
            execution_no: 作業番号
        RETRUN:
            True
    """
    user_id = g.USER_ID
    objAnsc = AnscConst()
    TableDict = {}
    TableDict["TABLE"] = {}
    TableDict["TABLE"][objAnsc.DF_LEGACY_DRIVER_ID] = "Not supported"
    TableDict["TABLE"][objAnsc.DF_PIONEER_DRIVER_ID] = "Not supported"
    TableDict["TABLE"][objAnsc.DF_LEGACY_ROLE_DRIVER_ID] = "T_ANSR_EXEC_STS_INST"
    
    TableName = TableDict["TABLE"][driver_id]

    # ステータスを確認するのでテーブルをロック
    objdbca.table_lock(TableName)

    # 作業番号存在確認
    sql = "SELECT * FROM " + TableName + " WHERE EXECUTION_NO = %s AND DISUSE_FLAG = '0'"
    execrows = objdbca.sql_execute(sql, [execution_no])
    if len(execrows) == 0:
        # 指定された作業番号が存在しない。
        raise AppException("499-00903", [execution_no], [execution_no])
    else:
        execrow = execrows[0]
        # ステータスが実行中か実行中(遅延)かを判定
        if execrow["STATUS_ID"] != objAnsc.PROCESSING and execrow["STATUS_ID"] != objAnsc.PROCESS_DELAYED:
            if g.LANGUAGE == 'ja':
                sql = "SELECT EXEC_STATUS_NAME_JA AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
            else:
                sql = "SELECT EXEC_STATUS_NAME_EN AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
            rows = objdbca.sql_execute(sql, [execrow["STATUS_ID"]])
            row = rows[0]
            #  緊急停止できる状態ではない
            raise AppException("499-00904", [row["NAME"]], [row["NAME"]])

        if execrow["EXEC_MODE"] == objAnsc.DF_EXEC_MODE_ANSIBLE:
            objAnsCore = AnsibleExecute()
            # Ansible-Core 緊急停止
            objAnsCore.execute_abort(driver_id, execution_no)
        else:
            # ansibleインターフェース情報取得
            sql = "SELECT * FROM T_ANSC_IF_INFO WHERE DISUSE_FLAG='0'"
            inforow = objdbca.sql_execute(sql, [])
            # 件数判定はしない
            inforow = inforow[0]
            if not inforow["ANSTWR_HOST_ID"]:
                # Ansibleインタフェース情報の代表ホスト」が未登録です。
                raise AppException("499-00912", [execution_no], [execution_no])
            proxySetting = {}
            proxySetting["address"] = inforow["ANSIBLE_PROXY_ADDRESS"]
            proxySetting["port"] = inforow["ANSIBLE_PROXY_PORT"]

            sql = "SELECT * FROM T_ANSC_TOWER_HOST WHERE ANSTWR_HOST_ID = %s AND DISUSE_FLAG='0'"
            towerrows = objdbca.sql_execute(sql, [inforow["ANSTWR_HOST_ID"]])
            if len(towerrows) == 0:
                # Ansible Automation Controllerホスト一覧にホストが未登録
                raise AppException("499-00913", [execution_no], [execution_no])
            towerrow = towerrows[0]

            # Tower緊急停止
            objTower = RestApiCaller(inforow["ANSTWR_PROTOCOL"], towerrow["ANSTWR_HOSTNAME"], inforow["ANSTWR_PORT"], inforow["ANSTWR_AUTH_TOKEN"], proxySetting)
            objTower.authorize()
            response_array = AnsibleTowerRestApiWorkflowJobs().cancelRelatedCurrnetExecution(objTower, execution_no)
            if response_array['success'] is False:
                # エラー詳細が付加されているか判定
                if "errorMessage" in response_array['responseContents']:
                    errmsg = response_array['responseContents']["errorMessage"]
                else:
                    # エラー詳細が付加されていない場合、responseContentsを設定
                    errmsg = str(response_array['responseContents'])

                # 緊急停止失敗
                raise AppException("499-00911", [execution_no, errmsg], [execution_no, errmsg])
        return True


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
