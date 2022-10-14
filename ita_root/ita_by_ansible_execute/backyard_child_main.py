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
import os
import sys
import re
import time
import json
import yaml
import glob
import inspect
import copy

from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.exception import AppException, ValidationException
from common_libs.common.util import get_timestamp, file_encode
from common_libs.loadtable import load_table
from common_libs.ci.util import log_err

from common_libs.ansible_driver.classes.AnsrConstClass import AnscConst, AnsrConst
from common_libs.ansible_driver.classes.ansible_execute import AnsibleExecute
from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg
from common_libs.ansible_driver.classes.CreateAnsibleExecFiles import CreateAnsibleExecFiles
from common_libs.ansible_driver.functions.util import getAnsibleExecutDirPath, get_AnsibleDriverTmpPath, getDataRelayStorageDir
from common_libs.ansible_driver.functions.ansibletowerlibs.AnsibleTowerExecute import AnsibleTowerExecution
from common_libs.driver.functions import operation_LAST_EXECUTE_TIMESTAMP_update

from libs import common_functions as cm


# ansible共通の定数をロード
ansc_const = AnscConst()
ansr_const = AnsrConst()


def backyard_child_main(organization_id, workspace_id):
    """
    [ita_by_ansible_executeの作業実行の子プロセス]
    main logicのラッパー
    """
    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
    args = sys.argv
    execution_no = args[3]
    driver_id = args[4]

    g.applogger.set_tag("EXECUTION_NO", execution_no)

    g.applogger.debug(g.appmsg.get_log_message("MSG-10720", [execution_no]))

    # db instance
    wsDb = DBConnectWs(workspace_id)  # noqa: F405

    # while True:
    #     time.sleep(1)

    try:
        result = main_logic(wsDb, execution_no, driver_id)
        if result[0] is True:
            # 正常終了
            g.applogger.info(g.appmsg.get_log_message("MSG-10721", [execution_no]))
        else:
            if len(result) == 2:
                log_err("main_logic:" + str(result[1]))
            update_status_error(wsDb, execution_no)
            g.applogger.info(g.appmsg.get_log_message("MSG-10722", [execution_no]))
    except AppException as e:
        update_status_error(wsDb, execution_no)
        g.applogger.info(g.appmsg.get_log_message("MSG-10722", [execution_no]))
        raise AppException(e)
    except Exception as e:
        update_status_error(wsDb, execution_no)
        g.applogger.info(g.appmsg.get_log_message("MSG-10722", [execution_no]))
        raise Exception(e)


def update_status_error(wsDb: DBConnectWs, execution_no):
    """
    異常終了と判定した場合のステータス更新
    
    Arguments:
        wsDb: DBConnectWs
        execution_no: 作業実行番号
    Returns:
        
    """
    timestamp = get_timestamp()
    wsDb.db_transaction_start()
    data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": ansc_const.EXCEPTION,
        "TIME_START": timestamp,
        "TIME_END": timestamp,
    }
    result = cm.update_execution_record(wsDb, data)
    if result[0] is True:
        wsDb.db_commit()
        g.applogger.info(g.appmsg.get_log_message("MSG-10735", [execution_no]))


def main_logic(wsDb: DBConnectWs, execution_no, driver_id):  # noqa: C901
    """
    main logic
    
    Arguments:
        wsDb: DBConnectWs
        execution_no: 作業実行番号
        driver_id: ドライバ識別子（AnscConst）
    Returns:
        bool
        err_msg
    """
    # 処理対象の作業インスタンス情報取得
    retBool, execute_data = cm.get_execution_process_info(wsDb, execution_no)
    if retBool is False:
        return False, g.appmsg.get_log_message(execute_data, [execution_no])
    execution_no = execute_data["EXECUTION_NO"]
    run_mode = execute_data['RUN_MODE']

    # ディレクトリを生成
    container_driver_path = getAnsibleExecutDirPath(driver_id, execution_no)

    work_dir = container_driver_path + "/in"
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    work_dir = container_driver_path + "/out"
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    work_dir = container_driver_path + "/.tmp"
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    work_dir = getDataRelayStorageDir() + "/driver/conductor/dummy"
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)

    # ANSIBLEインタフェース情報を取得
    retBool, result = cm.get_ansible_interface_info(wsDb)
    if retBool is False:
        return False, g.appmsg.get_log_message(result, [execution_no])
    ans_if_info = result

    # ansible実行に必要なファイル群を生成するクラス
    ansdrv = CreateAnsibleExecFiles(driver_id, ans_if_info, execution_no, execute_data['I_ENGINE_VIRTUALENV_NAME'], execute_data['I_ANSIBLE_CONFIG_FILE'], wsDb)  # noqa: E501

    # 	処理区分("1")、パラメータ確認、作業実行、ドライラン
    # 		代入値自動登録とパラメータシートからデータを抜く
    # 		該当のオペレーション、Movementのデータを代入値管理に登録
    # 一時的に呼ばないようにパッチ
    sub_value_auto_reg = SubValueAutoReg()
    try:
        sub_value_auto_reg.GetDataFromParameterSheet("1", execute_data["OPERATION_ID"], execute_data["MOVEMENT_ID"], execution_no, wsDb)
    except ValidationException as e:
        err_msg = g.appmsg.get_log_message(e)
        ansdrv.LocalLogPrint(
            os.path.basename(inspect.currentframe().f_code.co_filename),
            str(inspect.currentframe().f_lineno), err_msg)
        return False, err_msg

    # 実行モードが「パラメータ確認」の場合は終了
    if run_mode == ansc_const.CHK_PARA:
        wsDb.db_transaction_start()
        data = {
            "EXECUTION_NO": execution_no,
            "STATUS_ID": ansc_const.COMPLETE,
            "TIME_END": get_timestamp(),
        }
        result = cm.update_execution_record(wsDb, data)
        if result[0] is True:
            wsDb.db_commit()
            g.applogger.info(g.appmsg.get_log_message("MSG-10735", [execution_no]))
        return True,

    # # Conductorインタフェース情報を取得
    # retBool, result = cm.get_conductor_interface_info(wsDb)
    # if retBool is False:
    #     return False, g.appmsg.get_log_message(result, [execution_no])
    # conductor_interface_info = result

    # 投入オペレーションの最終実施日を更新する
    wsDb.db_transaction_start()
    result = operation_LAST_EXECUTE_TIMESTAMP_update(wsDb, execute_data["OPERATION_ID"])
    if result[0] is True:
        wsDb.db_commit()
        g.applogger.info(g.appmsg.get_log_message("BKY-10003", [execution_no]))

    # 処理対象の作業インスタンス実行
    g.applogger.debug("execute instance_execution")
    retBool, execute_data, result_data = instance_execution(wsDb, ansdrv, ans_if_info, execute_data, driver_id)

    # 実行結果から、処理対象の作業インスタンスのステータス更新
    if retBool is True:
        wsDb.db_transaction_start()
        if execute_data['FILE_INPUT']:
            zip_tmp_save_path = get_AnsibleDriverTmpPath() + "/" + execute_data['FILE_INPUT']
        else:
            zip_tmp_save_path = ''
            
        result = InstanceRecodeUpdate(wsDb, driver_id, execution_no, execute_data, 'FILE_INPUT', zip_tmp_save_path)

        if result[0] is True:
            wsDb.db_commit()
            g.applogger.info(g.appmsg.get_log_message("BKY-10004", [execute_data["STATUS_ID"], execution_no]))
        else:
            wsDb.db_rollback()
            return False, "InstanceRecodeUpdate->" + str(result[1])
    else:
        # 失敗
        return False, result_data
    
    # ステータスが実行中以外は終了
    if execute_data["STATUS_ID"] != ansc_const.PROCESSING:
        return False, g.appmsg.get_log_message("BKY-10005", [execute_data["STATUS_ID"], execution_no])

    # 実行結果から取得
    tower_host_list = result_data

    # [処理]処理対象インスタンス 作業確認の開始(作業No.:{})
    g.applogger.info(g.appmsg.get_log_message("MSG-10737", [execution_no]))

    check_interval = 3
    while True:
        time.sleep(check_interval)

        # 処理対象の作業インスタンス情報取得
        retBool, execute_data = cm.get_execution_process_info(wsDb, execution_no)
        if retBool is False:
            return False, execute_data
        clone_execute_data = execute_data
        # 実行結果の確認
        g.applogger.debug("execute instance_checkcondition")
        retBool, clone_execute_data, db_update_need = instance_checkcondition(wsDb, ansdrv, ans_if_info, clone_execute_data, driver_id, tower_host_list)  # noqa: E501

        # ステータスが更新されたか判定
        if db_update_need is True:
            # 処理対象の作業インスタンスのステータス更新           
            wsDb.db_transaction_start()
            if clone_execute_data['FILE_RESULT']:
                zip_tmp_save_path = get_AnsibleDriverTmpPath() + "/" + clone_execute_data['FILE_RESULT']
            else:
                zip_tmp_save_path = ''

            # ステータスが作業終了状態か判定
            if execute_data['STATUS_ID'] in [ansc_const.COMPLETE, ansc_const.FAILURE, ansc_const.EXCEPTION, ansc_const.SCRAM]:
                result = InstanceRecodeUpdate(wsDb, driver_id, execution_no, clone_execute_data, 'FILE_RESULT', zip_tmp_save_path)
            else:
                result = InstanceRecodeUpdate(wsDb, driver_id, execution_no, clone_execute_data, 'UPDATE', zip_tmp_save_path)

            if result[0] is True:
                wsDb.db_commit()
                g.applogger.info(g.appmsg.get_log_message("BKY-10004", [clone_execute_data["STATUS_ID"], execution_no]))
            else:
                wsDb.db_rollback()
                return False, "InstanceRecodeUpdate->" + str(result[1])

        if clone_execute_data['STATUS_ID'] in [ansc_const.COMPLETE, ansc_const.FAILURE, ansc_const.EXCEPTION, ansc_const.SCRAM]:
            break

    # [処理]処理対象インスタンス 作業確認の終了(作業No.:{})
    g.applogger.info(g.appmsg.get_log_message("MSG-10738", [execution_no]))

    return True,


def instance_execution(wsDb: DBConnectWs, ansdrv: CreateAnsibleExecFiles, ans_if_info, execute_data, driver_id):
    tower_host_list = {}

    execution_no = execute_data["EXECUTION_NO"]
    movement_id = execute_data["MOVEMENT_ID"]
    run_mode = execute_data['RUN_MODE']  # 処理対象のドライランモードのリスト
    conductor_instance_no = execute_data["CONDUCTOR_INSTANCE_NO"]

    # [処理]処理対象インスタンス 作業実行開始(作業No.:{})
    g.applogger.info(g.appmsg.get_log_message("MSG-10763", [execution_no]))

    # 処理対象の並列実行数のリストを格納 (pioneer)
    tgt_exec_count = execute_data['I_ANS_PARALLEL_EXE']
    if not tgt_exec_count or len(tgt_exec_count.strip()) == 0:
        tgt_exec_count = '0'

    # ANSIBLEインタフェース情報をローカル変数に格納
    ansible_exec_options = ans_if_info['ANSIBLE_EXEC_OPTIONS']
    # 2.0では不要 非コンテナ版の場合に有効にする。
    # ans_exec_user = ans_if_info['ANSIBLE_EXEC_USER']
    ans_exec_mode = ans_if_info['ANSIBLE_EXEC_MODE']

    # Ansibleコマンド実行ユーザー設定
    # 2.0では不要 非コンテナ版の場合に有効にする。
    # if not ans_exec_user or len(ans_exec_user.strip()) == 0:
    #    ans_exec_user = 'root'
    # ansdrv.setAnsibleExecuteUser(ans_exec_user)

    winrm_id = ""
    if driver_id == ansc_const.DF_LEGACY_ROLE_DRIVER_ID:
        winrm_id = execute_data["I_ANS_WINRM_ID"]

    # データベースからansibleで実行する情報取得し実行ファイル作成
    result = call_CreateAnsibleExecFiles(ansdrv, execute_data, driver_id, winrm_id)  # noqa: E501

    if result[0] is False:
        return False, execute_data, result[1]

    # ansible-playbookのオプションパラメータを確認
    movement_ansible_exec_option = getMovementAnsibleExecOption(wsDb, movement_id)

    if movement_ansible_exec_option is None:
        movement_ansible_exec_option = ""
    if ansible_exec_options is None:
        ansible_exec_options = ""

    option_parameter = ansible_exec_options + ' ' + movement_ansible_exec_option
    option_parameter = option_parameter.replace("--verbose", "-v")

    # Tower実行の場合にオプションパラメータをチェックする。
    if ans_exec_mode != ansc_const.DF_EXEC_MODE_ANSIBLE:
        # Pioneerの場合の並列実行数のパラメータ設定
        if driver_id == ansc_const.DF_PIONEER_DRIVER_ID:
            if tgt_exec_count != '0':
                option_parameter = option_parameter + " -f {} ".format(tgt_exec_count)

        # 重複除外用のオプションパラメータ
        result = getAnsiblePlaybookOptionParameter(
            wsDb,
            option_parameter)
        if result[0] is False:
            err_msg_ary = result[1]
            for err_msg in err_msg_ary:
                ansdrv.LocalLogPrint(
                    os.path.basename(inspect.currentframe().f_code.co_filename),
                    str(inspect.currentframe().f_lineno), err_msg)
            return False, execute_data, g.appmsg.get_log_message("BKY-00004", ["getAnsiblePlaybookOptionParameter", ",".join(err_msg_ary)])

        retBool, err_msg_ary, JobTemplatePropertyParameterAry, JobTemplatePropertyNameAry, param_arry_exc = result

    tmp_array_dirs = ansdrv.getAnsibleWorkingDirectories(ansr_const.vg_OrchestratorSubId_dir, execution_no)
    zip_data_source_dir = tmp_array_dirs[3]

    # ansible-playbookコマンド実行時のオプションパラメータを共有ディレクトリのファイルに出力
    with open(zip_data_source_dir + "/AnsibleExecOption.txt", "w") as f:
        f.write(option_parameter)

    # 投入データ用ZIPファイル作成
    retBool, err_msg, zip_input_file = createTmpZipFile(
        execution_no,
        zip_data_source_dir,
        'FILE_INPUT',
        'InputData_')

    if retBool is True:
        execute_data["FILE_INPUT"] = zip_input_file
    else:
        # ZIPファイル作成の作成に失敗しても、ログに出して次に進む
        g.applogger.warn(g.appmsg.get_log_message("BKY-00004", ["createTmpZipFile", err_msg]))

    # 準備で異常がなければ実行にうつる
    g.applogger.debug(g.appmsg.get_log_message("MSG-10761", [execution_no]))
    # 実行エンジンを判定
    if ans_exec_mode == ansc_const.DF_EXEC_MODE_ANSIBLE:
        ansible_execute = AnsibleExecute()
        retBool = ansible_execute.execute_construct(driver_id, execution_no, conductor_instance_no, "", "", ans_if_info['ANSIBLE_CORE_PATH'], ans_if_info['ANSIBLE_VAULT_PASSWORD'], run_mode, "")  # noqa: E501
        
        if retBool is True:
            execute_data["STATUS_ID"] = ansc_const.PROCESSING
            execute_data["TIME_START"] = get_timestamp()
        else:
            err_msg = ansible_execute.getLastError()
            if not isinstance(err_msg, str):
                err_msg = str(err_msg)
            ansdrv.LocalLogPrint(
                os.path.basename(inspect.currentframe().f_code.co_filename),
                str(inspect.currentframe().f_lineno), err_msg)
            return False, execute_data, err_msg
    else:
        uiexec_log_path = ansdrv.getAnsible_out_Dir() + "/exec.log"  # 使ってる？
        uierror_log_path = ansdrv.getAnsible_out_Dir() + "/error.log"  # 使ってる？
        multiple_log_mark = ""
        multiple_log_file_json_ary = ""

        Ansible_out_Dir = ansdrv.getAnsible_out_Dir()
        TowerProjectsScpPath = ansdrv.getTowerProjectsScpPath()
        TowerInstanceDirPath = ansdrv.getTowerInstanceDirPath()
        try:
            # execute_dataのSTATUS_ID/TIME_STARTはAnsibleTowerExecution内で設定
            # statusは使わない
            retBool, tower_host_list, execute_data, multiple_log_mark, multiple_log_file_json_ary, status, error_flag, warning_flag = AnsibleTowerExecution(  # noqa: E501
                driver_id,
                ansc_const.DF_EXECUTION_FUNCTION,
                ans_if_info,
                [],
                execute_data,
                Ansible_out_Dir,
                uiexec_log_path, uierror_log_path,
                multiple_log_mark, multiple_log_file_json_ary,
                "",
                JobTemplatePropertyParameterAry,
                JobTemplatePropertyNameAry,
                TowerProjectsScpPath,
                TowerInstanceDirPath,
                wsDb)

        except Exception as e:
            AnsibleTowerExecution(
                driver_id,
                ansc_const.DF_DELETERESOURCE_FUNCTION, 
                ans_if_info,
                [],
                execute_data,
                Ansible_out_Dir,
                uiexec_log_path, uierror_log_path,
                multiple_log_mark, multiple_log_file_json_ary,
                "",
                JobTemplatePropertyParameterAry,
                JobTemplatePropertyNameAry,
                TowerProjectsScpPath,
                TowerInstanceDirPath,
                wsDb)
            err_msg = g.appmsg.get_log_message("BKY-00004", ["AnsibleTowerExecution(DF_EXECUTION_FUNCTION)", e])
            ansdrv.LocalLogPrint(
                os.path.basename(inspect.currentframe().f_code.co_filename),
                str(inspect.currentframe().f_lineno), err_msg)
            return False, execute_data, err_msg

        # マルチログか判定
        if multiple_log_mark and execute_data['MULTIPLELOG_MODE'] != multiple_log_mark:
            execute_data['MULTIPLELOG_MODE'] = multiple_log_mark

    return True, execute_data, tower_host_list


def instance_checkcondition(wsDb: DBConnectWs, ansdrv: CreateAnsibleExecFiles, ans_if_info, execute_data, driver_id, tower_host_list):
    db_update_need = False

    TowerProjectsScpPath = ansdrv.getTowerProjectsScpPath()
    TowerInstanceDirPath = ansdrv.getTowerInstanceDirPath()

    execution_no = execute_data["EXECUTION_NO"]

    # ANSIBLEインタフェース情報をローカル変数に格納
    # 2.0では不要 非コンテナ版の場合に有効にする。
    # ans_exec_user = ans_if_info['ANSIBLE_EXEC_USER']
    ans_exec_mode = ans_if_info['ANSIBLE_EXEC_MODE']

    # Ansibleコマンド実行ユーザー設定
    # 2.0では不要 非コンテナ版の場合に有効にする。
    # if not ans_exec_user or len(ans_exec_user.strip()) == 0:
    #    ans_exec_user = 'root'

    # 実行エンジンを判定
    g.applogger.debug(g.appmsg.get_log_message("MSG-10741", [execution_no]))
    error_flag = 0
    if ans_exec_mode == ansc_const.DF_EXEC_MODE_ANSIBLE:
        ansible_execute = AnsibleExecute()
        status = ansible_execute.execute_statuscheck(driver_id, execution_no)

        # 想定外エラーはログを出す
        if status == ansc_const.EXCEPTION:
            err_msg = ansible_execute.getLastError()
            if not isinstance(err_msg, str):
                err_msg = str(err_msg)
            ansdrv.LocalLogPrint(
                os.path.basename(inspect.currentframe().f_code.co_filename),
                str(inspect.currentframe().f_lineno), err_msg)
    else:
        uiexec_log_path = ansdrv.getAnsible_out_Dir() + "/exec.log"  # 使ってる？
        uierror_log_path = ansdrv.getAnsible_out_Dir() + "/error.log"  # 使ってる？
        multiple_log_mark = ""
        multiple_log_file_json_ary = ""
        Ansible_out_Dir = ansdrv.getAnsible_out_Dir()
        status = 0

        retBool, tower_host_list, execute_data, multiple_log_mark, multiple_log_file_json_ary, status, error_flag, warning_flag = AnsibleTowerExecution(  # noqa: E501
            driver_id,
            ansc_const.DF_CHECKCONDITION_FUNCTION,
            ans_if_info,
            tower_host_list,
            execute_data,
            Ansible_out_Dir,
            uiexec_log_path, uierror_log_path,
            multiple_log_mark, multiple_log_file_json_ary,
            status,
            None,
            None,
            TowerProjectsScpPath,
            TowerInstanceDirPath,
            wsDb)

        # マルチログか判定
        if multiple_log_mark and execute_data['MULTIPLELOG_MODE'] != multiple_log_mark:
            execute_data['MULTIPLELOG_MODE'] = multiple_log_mark
            db_update_need = True
        # マルチログファイルリスト
        if multiple_log_file_json_ary and execute_data['LOGFILELIST_JSON'] != multiple_log_file_json_ary:
            execute_data['LOGFILELIST_JSON'] = multiple_log_file_json_ary
            db_update_need = True

        # 5:正常終了時
        # 6:完了(異常)
        # 7:想定外エラー
        # 8:緊急停止
        if status in [ansc_const.COMPLETE, ansc_const.FAILURE, ansc_const.EXCEPTION, ansc_const.SCRAM]:
            pass
        else:
            status = -1

    # 状態をログに出力
    g.applogger.debug(g.appmsg.get_log_message("BKY-10006", [execution_no, status]))

    # 5:正常終了時
    # 6:完了(異常)
    # 7:想定外エラー
    # 8:緊急停止
    if status in [ansc_const.COMPLETE, ansc_const.FAILURE, ansc_const.EXCEPTION, ansc_const.SCRAM] or error_flag != 0:
        db_update_need = True
        # 実行エンジンを判定
        if ans_exec_mode == ansc_const.DF_EXEC_MODE_ANSIBLE:
            pass
        else:
            # 実行結果ファイルをTowerから転送
            # 戻り値は確認しない
            multiple_log_mark = ""
            multiple_log_file_json_ary = ""
            AnsibleTowerExecution(
                driver_id,
                ansc_const.DF_RESULTFILETRANSFER_FUNCTION,
                ans_if_info,
                tower_host_list,
                execute_data,
                Ansible_out_Dir, uiexec_log_path,
                uierror_log_path,
                multiple_log_mark, multiple_log_file_json_ary,
                status,
                None,
                None,
                TowerProjectsScpPath,
                TowerInstanceDirPath,
                wsDb)

        tmp_array_dirs = ansdrv.getAnsibleWorkingDirectories(ansr_const.vg_OrchestratorSubId_dir, execution_no)
        zip_data_source_dir = tmp_array_dirs[4]

        # 結果データ用ZIPファイル作成
        retBool, err_msg, zip_result_file = createTmpZipFile(
            execution_no,
            zip_data_source_dir,
            'FILE_RESULT',
            'ResultData_')

        if retBool is True:
            execute_data['FILE_RESULT'] = zip_result_file
        else:
            # ZIPファイル作成の作成に失敗しても、ログに出して次に進む
            g.applogger.warn(g.appmsg.get_log_message("BKY-00004", ["createTmpZipFile", err_msg]))

    # statusによって処理を分岐
    if status != -1:
        execute_data["STATUS_ID"] = status
        execute_data["TIME_END"] = get_timestamp()
    else:
        # 遅延を判定
        # 遅延タイマを取得
        time_limit = int(execute_data['I_TIME_LIMIT']) if execute_data['I_TIME_LIMIT'] else None
        delay_flag = 0

        # ステータスが実行中(3)、かつ制限時間が設定されている場合のみ遅延判定する
        if execute_data["STATUS_ID"] == ansc_const.PROCESSING and time_limit:
            # 開始時刻(「エポック秒.マイクロ秒」)を生成(localタイムでutcタイムではない)
            rec_time_start = execute_data['TIME_START']
            starttime_unixtime = rec_time_start.timestamp()
            # 開始時刻(マイクロ秒)＋制限時間(分→秒)＝制限時刻(マイクロ秒)
            limit_unixtime = starttime_unixtime + (time_limit * 60)
            # 現在時刻(「エポック秒.マイクロ秒」)を生成(localタイムでutcタイムではない)
            now_unixtime = time.time()

            # 制限時刻と現在時刻を比較
            if limit_unixtime < now_unixtime:
                delay_flag = 1
                g.applogger.info(g.appmsg.get_log_message("MSG-10707", [execution_no]))
            else:
                g.applogger.info(g.appmsg.get_log_message("MSG-10708", [execution_no]))

        if delay_flag == 1:
            db_update_need = True
            # ステータスを「実行中(遅延)」とする
            execute_data["STATUS_ID"] = ansc_const.PROCESS_DELAYED

    # 実行エンジンを判定
    if ans_exec_mode != ansc_const.DF_EXEC_MODE_ANSIBLE:
        # 5:正常終了時
        # 6:完了(異常)
        # 7:想定外エラー
        # 8:緊急停止
        if status in [ansc_const.COMPLETE, ansc_const.FAILURE, ansc_const.EXCEPTION, ansc_const.SCRAM]:
            # [処理]Ansible Automation Controller クリーニング 開始(作業No.:{})
            g.applogger.debug(g.appmsg.get_log_message("MSG-10743", [execution_no]))

            # 戻り値は確認しない
            ret = AnsibleTowerExecution(
                driver_id,
                ansc_const.DF_DELETERESOURCE_FUNCTION,
                ans_if_info,
                tower_host_list,
                execute_data,
                Ansible_out_Dir,
                uiexec_log_path,
                uierror_log_path,
                multiple_log_mark,
                multiple_log_file_json_ary,
                status,
                None,
                None,
                TowerProjectsScpPath,
                TowerInstanceDirPath,
                wsDb)

            # [処理]Ansible Automation Controller クリーニング 終了(作業No.:{})
            g.applogger.debug(g.appmsg.get_log_message("MSG-10744", [execution_no]))

    return True, execute_data, db_update_need


def call_CreateAnsibleExecFiles(ansdrv: CreateAnsibleExecFiles, execute_data, driver_id, winrm_id):
    execution_no = execute_data["EXECUTION_NO"]
    conductor_instance_no = execute_data["CONDUCTOR_INSTANCE_NO"]
    operation_id = execute_data["OPERATION_ID"]
    movement_id = execute_data["MOVEMENT_ID"]
    # ホストアドレス指定方式（I_ANS_HOST_DESIGNATE_TYPE_ID）
    # null or 1 がIP方式 2 がホスト名方式
    hostaddres_type = execute_data['I_ANS_HOST_DESIGNATE_TYPE_ID']

    exec_mode = execute_data["EXEC_MODE"]
    exec_playbook_hed_def = execute_data["I_ANS_PLAYBOOK_HED_DEF"]
    exec_option = execute_data["I_ANS_EXEC_OPTIONS"]

    hostlist = {}
    hostostypelist = {}
    hostinfolist = {}  # 機器一覧ホスト情報
    playbooklist = {}
    dialogfilelist = {}

    host_vars = []
    pioneer_template_host_vars = {}
    vault_vars = {}
    vault_host_vars_file_list = {}
    host_child_vars = []
    DB_child_vars_master = []

    # Legacy-Role対応
    rolenamelist = []
    role_rolenamelist = {}
    role_rolevarslist = {}
    role_roleglobalvarslist = {}
    role_rolepackage_id = ""

    MultiArray_vars_list = {}
    All_vars_list = []

    def_vars_list = {}
    def_array_vars_list = {}

    result = ansdrv.CreateAnsibleWorkingDir(ansr_const.vg_OrchestratorSubId_dir, execution_no, operation_id, hostaddres_type,
                                            winrm_id,
                                            movement_id,
                                            role_rolenamelist,
                                            role_rolevarslist,
                                            role_roleglobalvarslist,
                                            role_rolepackage_id,
                                            def_vars_list,
                                            def_array_vars_list,
                                            conductor_instance_no)

    retBool, role_rolenamelist, role_rolevarslist, role_roleglobalvarslist, role_rolepackage_id, def_vars_list, def_array_vars_list = result
    if retBool is False:
        return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.CreateAnsibleWorkingDir", "error occured"])

    result = ansdrv.AnsibleEnginVirtualenvPathCheck()
    if result is False:
        return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.AnsibleEnginVirtualenvPathCheck", "error occured"])

    result = ansdrv.getDBHostList(
        execution_no,
        movement_id,
        operation_id,
        hostlist,
        hostostypelist,
        hostinfolist,
        winrm_id)
    retBool, hostlist, hostostypelist, hostinfolist = result
    if retBool is False:
        return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.getDBHostList", "error occured"])

    if driver_id == ansc_const.DF_LEGACY_DRIVER_ID:
        # データベースからPlayBookファイルを取得
        #    playbooklist:     子PlayBookファイル返却配列
        #                     [INCLUDE順序][素材管理Pkey]=>素材ファイル
        result = ansdrv.getDBLegacyPlaybookList(movement_id, playbooklist)
        retBool, playbooklist = result
        if retBool is False:
            return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.getDBLegacyPlaybookList", "error occured"])
    elif driver_id == ansc_const.DF_PIONEER_DRIVER_ID:
        # データベースから対話ファイルを取得
        #    dialogfilelist:     子PlayBookファイル返却配列
        #                     [ホスト名(IP)][INCLUDE順番][素材管理Pkey]=対話ファイル
        result = ansdrv.getDBPioneerDialogFileList(movement_id, operation_id, dialogfilelist, hostostypelist)
        retBool, dialogfilelist = result
        if retBool is False:
            return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.getDBPioneerDialogFileList", "error occured"])
    elif driver_id == ansc_const.DF_LEGACY_ROLE_DRIVER_ID:
        # データベースからロール名を取得
        #    rolenamelist:     ロール名返却配列
        #                     [実行順序][ロールID(Pkey)]=>ロール名
        result = ansdrv.getDBLegactRoleList(movement_id, rolenamelist)
        retBool, rolenamelist = result
        if retBool is False:
            return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.getDBLegactRoleList", "error occured"])

    # Legacy-Role 多次元配列　恒久版対応
    if driver_id == ansc_const.DF_LEGACY_DRIVER_ID or driver_id == ansc_const.DF_PIONEER_DRIVER_ID:
        #  データベースから変数情報を取得する。
        result = ansdrv.getDBVarList(
            movement_id,
            operation_id,
            host_vars,
            pioneer_template_host_vars,
            vault_vars,
            vault_host_vars_file_list,
            host_child_vars,
            DB_child_vars_master)
        retBool, host_vars, pioneer_template_host_vars, vault_vars, vault_host_vars_file_list, host_child_vars, DB_child_vars_master = result
        if retBool is False:
            return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.getDBVarList", "error occured"])
    elif driver_id == ansc_const.DF_LEGACY_ROLE_DRIVER_ID:
        # データベースから変数情報を取得する。
        #   $host_vars:        変数一覧返却配列
        #                      [ホスト名(IP)][ 変数名 ]=>具体値
        result = ansdrv.getDBRoleVarList(execution_no,
                                         movement_id, operation_id, host_vars, MultiArray_vars_list, All_vars_list)
        retBool, host_vars, MultiArray_vars_list, All_vars_list = result
        if retBool is False:
            return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.getDBRoleVarList", "error occured"])

    host_vars = ansdrv.addSystemvars(host_vars, hostinfolist)

    # Legacy-Role 多次元配列　恒久版対応
    # ansibleで実行するファイル作成
    result = ansdrv.CreateAnsibleWorkingFiles(
        hostlist,
        host_vars,
        pioneer_template_host_vars,
        vault_vars,
        vault_host_vars_file_list,
        playbooklist,
        dialogfilelist,
        rolenamelist,
        role_rolenamelist,
        role_rolevarslist,
        role_roleglobalvarslist,
        hostinfolist,
        host_child_vars,
        DB_child_vars_master,
        MultiArray_vars_list,
        def_vars_list,
        def_array_vars_list,
        exec_mode,
        exec_playbook_hed_def,
        exec_option)
    if retBool is False:
        return False, g.appmsg.get_log_message("BKY-00004", ["CreateAnsibleExecFiles.CreateAnsibleWorkingFiles", "error occured"])

    return True, ""


def getMovementAnsibleExecOption(wsDb, movement_id):
    condition = 'WHERE `DISUSE_FLAG`=0 AND MOVEMENT_ID = %s'
    records = wsDb.table_select('V_ANSR_MOVEMENT', condition, [movement_id])

    return records[0]['ANS_EXEC_OPTIONS']


def getAnsiblePlaybookOptionParameter(wsDb, option_parameter):
    res_retBool = True
    JobTemplatePropertyParameterAry = {}
    JobTemplatePropertyNameAry = {}
    param_arry_exc = {}
    err_msg_arr = []
    verbose_cnt = 0

    # Towerが扱えるオプションパラメータ取得
    job_template_property_info = getJobTemplateProperty(wsDb)

    param = "-__dummy__ " + option_parameter.strip() + ' '
    param_arr = re.split(r'\s-', param)
    # 無効なオプションパラメータが設定されていないか判定
    for param_string in param_arr:
        if param_string and param_string.strip() == '-__dummy__':
            continue

        hit = False
        chk_param_string = '-' + param_string + ' '
        for job_template_property_record in job_template_property_info:
            if job_template_property_record['KEY_NAME']:
                key_string = job_template_property_record['KEY_NAME'].strip() if job_template_property_record['KEY_NAME'] else ''
                if key_string != "":
                    if re.match(key_string, chk_param_string):
                        hit = True
                        break
            if job_template_property_record['SHORT_KEY_NAME']:
                key_string = job_template_property_record['SHORT_KEY_NAME'].strip() if job_template_property_record['SHORT_KEY_NAME'] else ''
                if key_string != "":
                    if re.match(key_string, chk_param_string):
                        hit = True
                        break
        
        if hit is False:
            err_msg_arr.append(g.appmsg.get_log_message("MSG-10634", [chk_param_string.strip()]));

    if len(err_msg_arr) != 0:
        # err_msg
        return False, err_msg_arr

    # 除外された場合のリスト
    param_arry_exc = copy.copy(param_arr)

    for job_template_property_record in job_template_property_info:

        #  除外リストの初期化
        excist_list = []
        # KEY SHRT_KEYチェック用配列の初期化
        key_short_chk = []
        # tags skipのvalue用の配列の初期化
        tag_skip_value_key = []
        tag_skip_Value_key_s = []

        JobTemplatePropertyNameAry[job_template_property_record['PROPERTY_NAME']] = 0

        if job_template_property_record['KEY_NAME']:
            retBool, err_msg_arr, excist_list, tag_skip_value_key, verbose_cnt = makeJobTemplateProperty(
                job_template_property_record['KEY_NAME'],
                job_template_property_record['PROPERTY_TYPE'],
                job_template_property_record['PROPERTY_NAME'],
                param_arr,
                err_msg_arr,
                excist_list,
                tag_skip_value_key,
                verbose_cnt)

            # 重複データの場合のみ
            excist_count = len(excist_list)
            i = 0
            if excist_count >= 1:
                for excist_elm in excist_list:
                    # 最後のデータは削除しない
                    if excist_count - 1 == i:
                        # KEYのチェックデータ格納
                        key_short_chk.append(excist_elm)
                        break
                    j = 0
                    for elm_ary in param_arry_exc:
                        # 除外リストと一致した場合
                        if excist_elm == elm_ary:
                            # 要素を削除
                            param_arry_exc.pop(j)
                            break
                        j = j + 1
                    i = i + 1
                    
            if retBool is False:
                res_retBool = False
            
            # 除外リストの初期化
            excist_list = []

        if job_template_property_record['SHORT_KEY_NAME']:
            retBool, err_msg_arr, excist_list, tag_skip_Value_key_s, verbose_cnt = makeJobTemplateProperty(
                job_template_property_record['SHORT_KEY_NAME'],
                job_template_property_record['PROPERTY_TYPE'],
                job_template_property_record['PROPERTY_NAME'],
                param_arr,
                err_msg_arr,
                excist_list,
                tag_skip_Value_key_s,
                verbose_cnt)

            # 重複データの場合のみ
            excist_count = len(excist_list)
            i = 0
            if excist_count >= 1:
                for excist_elm in excist_list:
                    # 最後のデータは削除しない
                    if excist_count - 1 == i:
                        # KEYのチェックデータ格納
                        key_short_chk.append(excist_elm)
                        break
                    j = 0
                    for elm_ary in param_arry_exc:
                        # 除外リストと一致した場合
                        if excist_elm == elm_ary:
                            # 要素を削除
                            param_arry_exc.pop(j)
                            break
                        j = j + 1
                    i = i + 1
                    
            if retBool is False:
                res_retBool = False
            
        # KEY SHORTのチェック
        k = 0
        if len(key_short_chk) >= 2:
            # KEY SHORTそれぞれ存在する場合,先頭データを削除
            for param_arry_exc_key_chk in param_arry_exc:
                if param_arry_exc_key_chk == key_short_chk[0]:
                    param_arry_exc.pop(k)
                    break
                if param_arry_exc_key_chk == key_short_chk[1]:
                    param_arry_exc.pop(k)
                k = k + 1

        # tags,skipの場合','区切りに修正する
        if 'job_tags' == job_template_property_record['PROPERTY_NAME'] or 'skip_tags' == job_template_property_record['PROPERTY_NAME']:
            # tags,skipの場合、','区切りにしてデータを渡す（文字列整形）
            values_param = ''
            ll = 0
            m = 0
            for param_arr_tmp_tab_skip in param_arr:
                chk_param_string = '-' + param_arr_tmp_tab_skip + ' '
                # KEYのtagsのvalueを取得
                if re.match(r'--tags=', chk_param_string) and r'--tags=' == job_template_property_record['KEY_NAME']:
                    values_param = values_param + tag_skip_value_key[ll] + ','
                    ll = ll + 1
                # KEYのskipのvalueを取得
                if re.match(r'--skip-tags=', chk_param_string) and r'--skip-tags=' == job_template_property_record['KEY_NAME']:
                    values_param = values_param + tag_skip_value_key[ll] + ','
                    ll = ll + 1
                # KEY SHORTのtagsのvalueを取得
                if re.match(r'-t[\s]+', chk_param_string) and r'-t[\s]+' == job_template_property_record['SHORT_KEY_NAME']:
                    values_param = values_param + tag_skip_Value_key_s[m] + ','
                    m = m + 1

            # 末尾の','を削除
            values_param = values_param.rstrip(',')

            # リストのデータを書き換え
            n = 0
            for param_arr_tmp_key_chg in param_arry_exc:
                chk_param_string_chg = '-' + param_arr_tmp_key_chg + ' '
                if re.match(r'--tags=', chk_param_string_chg) and r'--tags=' == job_template_property_record['KEY_NAME']:
                    # 要素を書き換え
                    param_arry_exc[n] = '-tags=' + values_param
                    break
                if re.match(r'--skip-tags=', chk_param_string_chg) and r'--skip-tags=' == job_template_property_record['KEY_NAME']:
                    # 要素を書き換え
                    param_arry_exc[n] = '-skip-tags=' + values_param
                    break
                if re.match(r'-t[\s]+', chk_param_string_chg) and r'-t[\s]+' == job_template_property_record['SHORT_KEY_NAME']:
                    # 要素を書き換え
                    param_arry_exc[n] = 't ' + values_param
                    break
                n = n + 1

        # JobTemplatePropertyParameterAryの作成
        if job_template_property_record['KEY_NAME'] and len(job_template_property_record['KEY_NAME'].strip()) != 0:
            retBool, JobTemplatePropertyParameterAry = makeJobTemplatePropertyParameterAry(
                job_template_property_record['KEY_NAME'],
                job_template_property_record['PROPERTY_TYPE'],
                job_template_property_record['PROPERTY_NAME'],
                JobTemplatePropertyParameterAry,
                param_arry_exc,
                verbose_cnt)
            if retBool is False:
                res_retBool = False
        if job_template_property_record['SHORT_KEY_NAME'] and len(job_template_property_record['SHORT_KEY_NAME'].strip()) != 0:
            retBool, JobTemplatePropertyParameterAry = makeJobTemplatePropertyParameterAry(
                job_template_property_record['SHORT_KEY_NAME'],
                job_template_property_record['PROPERTY_TYPE'],
                job_template_property_record['PROPERTY_NAME'],
                JobTemplatePropertyParameterAry,
                param_arry_exc,
                verbose_cnt)
            if retBool is False:
                res_retBool = False

    return res_retBool, err_msg_arr, JobTemplatePropertyParameterAry, JobTemplatePropertyNameAry, param_arry_exc


def getJobTemplateProperty(wsDb):
    res = []

    condition = 'WHERE `DISUSE_FLAG`=0'
    records = wsDb.table_select('T_ANSC_TWR_JOBTP_PROPERTY', condition)

    for record in records:
        data = {
            'KEY_NAME': record['KEY_NAME'],
            'SHORT_KEY_NAME': record['SHORT_KEY_NAME'],
            'PROPERTY_TYPE': record['PROPERTY_TYPE'],
            'PROPERTY_NAME': record['PROPERTY_NAME'],
            'TOWERONLY': record['TOWERONLY']
        }
        res.append(data)

    return res

def makeJobTemplateProperty(key_string, property_type, property_name, param_arr, err_msg_arr, excist_list, tag_skip_value_key, verbose_cnt):
    res_retBool = True

    for param_string in param_arr:
        chk_param_string = '-' + param_string + ' '
        if re.match(key_string, chk_param_string):
            property_arr = re.split(r'^{}'.format(key_string), chk_param_string)
            # MSG-10553 = "値が設定されていないオプションパラメータがあります。(パラメータ: {})"
            # MSG-10554 = "重複しているオプションパラメータがあります。(パラメータ: {})"
            # MSG-10555 = "不正なオプションパラメータがあります。(パラメータ: {})"

            # chk_param_stringを除外リストに設定(追加)
            excist_list.append(param_string)

            if property_type == ansc_const.DF_JobTemplateKeyValueProperty:
                if not property_arr[1] or len(property_arr[1].strip()) == 0:
                    err_msg_arr.append(g.appmsg.get_log_message("MSG-10553", [chk_param_string]))
                    res_retBool = False
                if property_name in ['forks', 'job_slice_count']:
                    if not str.isdecimal(property_arr[1].strip()):
                        err_msg_arr.append(g.appmsg.get_log_message("MSG-10555", [chk_param_string]))
                        res_retBool = False
                # tags skipの対応
                if property_name in ['job_tags', 'skip_tags']:
                    tag_skip_value_key.append(property_arr[1].strip())

            elif property_type == ansc_const.DF_JobTemplateVerbosityProperty:
                # v以外の文字列があったらエラーにする
                if property_arr[1] and len(property_arr[1].strip()) != 0:
                    err_msg_arr.append(g.appmsg.get_log_message("MSG-10555", [chk_param_string]))
                    res_retBool = False
                    continue

                for ch in param_string.strip():
                    if ch != 'v':
                        err_msg_arr.append(g.appmsg.get_log_message("MSG-10555", [chk_param_string]))
                        res_retBool = False
                        continue

                verbose_cnt = verbose_cnt + len(param_string.strip())

            elif property_type == ansc_const.DF_JobTemplatebooleanTrueProperty:
                if property_arr[1] and len(property_arr[1].strip()) != 0:
                    err_msg_arr.append(g.appmsg.get_log_message("MSG-10555", [chk_param_string]))
                    res_retBool = False

            elif property_type == ansc_const.DF_JobTemplateExtraVarsProperty:
                if not property_arr[1] or len(property_arr[1].strip()) == 0:
                    err_msg_arr.append(g.appmsg.get_log_message("MSG-10553", [chk_param_string]))
                    res_retBool = False
                else:
                    ext_var_string = property_arr[1].strip()
                    ret = makeExtraVarsParameter(ext_var_string)
                    if ret is False:
                        err_msg_arr.append(g.appmsg.get_log_message("MSG-10555", [chk_param_string]))
                        res_retBool = False

    return res_retBool, err_msg_arr, excist_list, tag_skip_value_key, verbose_cnt

def makeJobTemplatePropertyParameterAry(key_string, property_type, property_name, JobTemplatePropertyParameterAry, param_arr, verbose_cnt):
    retBool = True

    for param_string in param_arr:
        chk_param_string = '-' + param_string + ' '

        if not re.match(r'^{}'.format(key_string), chk_param_string):
            continue

        proper_ary = re.split(r'^{}'.format(key_string), chk_param_string)
        if not proper_ary[1]:
            proper_ary[1] = ''

        if property_type == ansc_const.DF_JobTemplateKeyValueProperty:
            JobTemplatePropertyParameterAry[property_name] = proper_ary[1].strip()
            break
        elif property_type == ansc_const.DF_JobTemplateVerbosityProperty:
            if verbose_cnt >= 6:
                verbose_cnt = 5
            JobTemplatePropertyParameterAry[property_name] = verbose_cnt
            break
        elif property_type == ansc_const.DF_JobTemplatebooleanTrueProperty:
            JobTemplatePropertyParameterAry[property_name] = True
        elif property_type == ansc_const.DF_JobTemplateExtraVarsProperty:
            ext_var_string = proper_ary[1].strip().strip("\"").strip("\'")
            ext_var_string = ext_var_string.replace("\\n", "\n")
            JobTemplatePropertyParameterAry[property_name] = ext_var_string

    return retBool, JobTemplatePropertyParameterAry


def makeExtraVarsParameter(ext_var_string):
    ext_var_string = ext_var_string.strip("\"").strip("\'")
    ext_var_string = ext_var_string.replace("\\n", "\n")

    # JSON形式のチェック
    try:
        json.loads(ext_var_string)
        return True
    except json.JSONDecodeError:
        pass
    
    # YAML形式のチェック
    try:
        yaml.safe_load(ext_var_string)
        return True
    except Exception:
        pass

    return False

def createTmpZipFile(execution_no, zip_data_source_dir, zip_type, zip_file_pfx):
    ########################################
    # 処理内容
    #  入力/結果ZIPファイル作成
    #
    # Arugments:
    #  execution_no:               作業実行番号
    #  zip_data_source_dir:        zipファイルの[圧縮元]の資材ディレクトリ
    #  zip_type:                   入力/出力の区分
    #                                   入力:FILE_INPUT   出力:FILE_RESULT
    #  zip_file_pfx:               zipファイル名のプレフィックス
    #                                 入力:InputData_   出力:ResultData_
    #
    # Returns:
    #   true:正常　false:異常
    #   zip_file_name:           ZIPファイル名返却
    ########################################
    err_msg = ""
    zip_file_name = ""
    zip_temp_save_dir = ""
    if len(glob.glob(zip_data_source_dir + "/*")) > 0:
        # ----ZIPファイルを作成する
        zip_file_name = zip_file_pfx + execution_no + '.zip'
        # 圧縮先
        zip_temp_save_dir = get_AnsibleDriverTmpPath()

        # OSコマンドでzip圧縮する
        tmp_str_command = "cd " + zip_data_source_dir + "; zip -r " + zip_temp_save_dir + "/" + zip_file_name + " . -x ssh_key_files/* -x winrm_ca_files/*"  # noqa: E501

        os.system(tmp_str_command)

        # zipファイルの存在を確認
        zip_temp_save_path = zip_temp_save_dir + "/" + zip_file_name
        if not os.path.exists(zip_temp_save_path):
            err_msg = g.appmsg.get_log_message("MSG-10252", [zip_type, zip_temp_save_path])
            False, err_msg, zip_file_name, zip_temp_save_dir

        # [処理]結果ディレクトリを圧縮(圧縮ファイル:{})
        g.applogger.debug(g.appmsg.get_log_message("MSG-10783", [zip_type, os.path.basename(zip_temp_save_path)]))
    return True, err_msg, zip_file_name


def InstanceRecodeUpdate(wsDb, driver_id, execution_no, execute_data, update_column_name, zip_tmp_save_path):
    """
    作業管理更新

    ARGS:
        wsDb:DB接クラス  DBConnectWs()
        driver_id: ドライバ区分　AnscConst().DF_LEGACY_ROLE_DRIVER_ID
        execution_no: 作業番号
        execute_data: 更新内容配列
        update_column_name: 更新対象のFileUpLoadColumn名
        zip_tmp_save_path: 一時的に作成したzipファイルのパス
    RETRUN:
        True/False, errormsg
    """

    TableDict = {}
    TableDict["MENU_REST"] = {}
    TableDict["MENU_REST"][AnscConst.DF_LEGACY_DRIVER_ID] = "Not supported"
    TableDict["MENU_REST"][AnscConst.DF_PIONEER_DRIVER_ID] = "Not supported"
    TableDict["MENU_REST"][AnscConst.DF_LEGACY_ROLE_DRIVER_ID] = "execution_list_ansible_role"
    TableDict["MENU_ID"] = {}
    TableDict["MENU_ID"][AnscConst.DF_LEGACY_DRIVER_ID] = "Not supported"
    TableDict["MENU_ID"][AnscConst.DF_PIONEER_DRIVER_ID] = "Not supported"
    TableDict["MENU_ID"][AnscConst.DF_LEGACY_ROLE_DRIVER_ID] = "20412"
    TableDict["TABLE"] = {}
    TableDict["TABLE"][AnscConst.DF_LEGACY_DRIVER_ID] = "Not supported"
    TableDict["TABLE"][AnscConst.DF_PIONEER_DRIVER_ID] = "Not supported"
    TableDict["TABLE"][AnscConst.DF_LEGACY_ROLE_DRIVER_ID] = "T_ANSR_EXEC_STS_INST"
    MenuName = TableDict["MENU_REST"][driver_id]
    MenuId = TableDict["MENU_ID"][driver_id]

    # loadtyable.pyで使用するCOLUMN_NAME_RESTを取得
    RestNameConfig = {}
    # あえて廃止にしている項目もあり、要確認が必要
    sql = "SELECT COL_NAME,COLUMN_NAME_REST FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = %s and DISUSE_FLAG = '0'"
    restcolnamerow = wsDb.sql_execute(sql, [MenuId])
    for row in restcolnamerow:
        RestNameConfig[row["COL_NAME"]] = row["COLUMN_NAME_REST"]

    ExecStsInstTableConfig = {}

    # 作業番号
    ExecStsInstTableConfig[RestNameConfig["EXECUTION_NO"]] = execution_no

    # ステータス
    if g.LANGUAGE == 'ja':
        sql = "SELECT EXEC_STATUS_NAME_JA AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT EXEC_STATUS_NAME_EN AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    rows = wsDb.sql_execute(sql, [execute_data["STATUS_ID"]])
    # マスタなので件数チェックしない
    row = rows[0]
    ExecStsInstTableConfig[RestNameConfig["STATUS_ID"]] = row["NAME"]

    # 入力データ/投入データ／出力データ/結果データ用zipデータ
    uploadfiles = {}
    if update_column_name == "FILE_INPUT" or update_column_name == "FILE_RESULT":
        if zip_tmp_save_path:
            ZipDataData = file_encode(zip_tmp_save_path)
            if ZipDataData is False:
                # エンコード失敗
                msgstr = g.appmsg.get_api_message("499-00909", [])
                return False, msgstr
            uploadfiles = {RestNameConfig[update_column_name]: ZipDataData}

    # 実行中の場合
    if update_column_name == "FILE_INPUT":
        ExecStsInstTableConfig[RestNameConfig["FILE_INPUT"]] = execute_data["FILE_INPUT"]  # 入力データ/投入データ
        ExecStsInstTableConfig[RestNameConfig["TIME_START"]] = execute_data['TIME_START'].strftime('%Y/%m/%d %H:%M:%S')
        if "MULTIPLELOG_MODE" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]] = execute_data["MULTIPLELOG_MODE"]
        if "LOGFILELIST_JSON" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]] = execute_data["LOGFILELIST_JSON"]

    # 実行終了の場合
    if update_column_name == "FILE_RESULT":
        ExecStsInstTableConfig[RestNameConfig["FILE_RESULT"]] = execute_data["FILE_RESULT"]  # 出力データ/結果データ
        ExecStsInstTableConfig[RestNameConfig["TIME_END"]] = execute_data['TIME_END'].strftime('%Y/%m/%d %H:%M:%S')
        # MULTIPLELOG_MODEとLOGFILELIST_JSONが廃止レコードになっているので0にする
        if "MULTIPLELOG_MODE" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]] = execute_data["MULTIPLELOG_MODE"]
        if "LOGFILELIST_JSON" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]] = execute_data["LOGFILELIST_JSON"]

    # その他の場合
    if update_column_name == "UPDATE":
        if "MULTIPLELOG_MODE" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]] = execute_data["MULTIPLELOG_MODE"]
        if "LOGFILELIST_JSON" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]] = execute_data["LOGFILELIST_JSON"]

    # 最終更新日時
    ExecStsInstTableConfig[RestNameConfig["LAST_UPDATE_TIMESTAMP"]] = execute_data['LAST_UPDATE_TIMESTAMP'].strftime('%Y/%m/%d %H:%M:%S.%f')

    parameters = {
        "parameter": ExecStsInstTableConfig,
        "file": uploadfiles,
        "type": "Update"
    }
    objmenu = load_table.loadTable(wsDb, MenuName)
    retAry = objmenu.exec_maintenance(parameters, execution_no, "", False, False)
    result = retAry[0]
    if result is False:
        return False, str(retAry)
    else:
        return True, ""
