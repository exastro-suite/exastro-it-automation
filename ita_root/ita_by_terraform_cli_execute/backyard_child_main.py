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
import sys
import os
import subprocess

import glob

import copy
# import traceback

from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.exception import AppException, ValidationException
from common_libs.common.util import get_timestamp, file_encode, ky_encrypt
from common_libs.loadtable import load_table
from common_libs.ci.util import log_err

# from common_libs.terraform_driver.common.Const import Const
from common_libs.terraform_driver.cli.Const import Const

from common_libs.driver.functions import operation_LAST_EXECUTE_TIMESTAMP_update
from common_libs.ci.util import app_exception_driver_log, exception_driver_log, validation_exception_driver_log, validation_exception

from libs import common_functions as cm


# 定数をロード
const = Const()


def backyard_child_main(organization_id, workspace_id):
    """
    [ita_by_terraform_cli_executeの作業実行の子プロセス]
    main logicのラッパー
    """
    global const

    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
    args = sys.argv
    tf_workspace_id = args[3]
    execution_no = args[4]
    g.applogger.debug("tf_workspace_id=" + tf_workspace_id)
    g.applogger.debug("execution_no=" + execution_no)
    g.applogger.set_tag("EXECUTION_NO", execution_no)
    g.applogger.debug(g.appmsg.get_log_message("MSG-10720", [execution_no]))

    # db instance
    wsDb = DBConnectWs(workspace_id)  # noqa: F405

    try:
        result = main_logic(wsDb, tf_workspace_id, execution_no)
        if result[0] is True:
            # 正常終了
            g.applogger.debug(g.appmsg.get_log_message("MSG-10721", [tf_workspace_id, execution_no]))
        else:
            g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [tf_workspace_id, execution_no]))
    except AppException as e:
        update_status_error(wsDb, const, tf_workspace_id, execution_no)

        g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [tf_workspace_id, execution_no]))

        raise e
    except Exception as e:
        update_status_error(wsDb, const, tf_workspace_id, execution_no)

        g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [tf_workspace_id, execution_no]))

        raise e


def update_status_error(wsDb: DBConnectWs, ansConstObj, tf_workspace_id, execution_no):
    """
    異常終了と判定した場合のステータス更新

    Arguments:
        wsDb: DBConnectWs
        ansConstObj: ansible共通定数オブジェクト
        execution_no: 作業実行番号
    Returns:

    """
    global const

    timestamp = get_timestamp()

    wsDb.db_transaction_start()
    data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": const.STATUS_EXCEPTION,
        "TIME_START": timestamp,
        "TIME_END": timestamp,
    }
    result = cm.update_execution_record(wsDb, const, data)
    if result[0] is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10060", [execution_no, tf_workspace_id]))


def main_logic(wsDb: DBConnectWs, tf_workspace_id, execution_no):  # noqa: C901
    """
    main logic

    Arguments:
        wsDb: DBConnectWs
        tf_workspace_id : terraformのworkspace-id
        execution_no: 作業実行番号
    Returns:
        bool
        err_msg
    """
    global const

    # 処理対象の作業インスタンス情報取得
    retBool, execute_data = cm.get_execution_process_info(wsDb, const, execution_no)
    if retBool is False:
        err_log = g.appmsg.get_log_message(execute_data, [execution_no])
        raise Exception(err_log)

    execution_no = execute_data['EXECUTION_NO']
    # tf_workspace_id = execute_data['I_WORKSPACE_ID']
    run_mode = execute_data['RUN_MODE']

    # 代入値自動登録とパラメータシートからデータを抜く
    # 		該当のオペレーション、Movementのデータを代入値管理に登録
    # 一時的に呼ばないように
    # sub_value_auto_reg = SubValueAutoReg(wsDb, tf_workspace_id)
    # try:
    #     sub_value_auto_reg.get_data_from_parameter_sheet(execute_data["OPERATION_ID"], execute_data["MOVEMENT_ID"], execution_no)
    # except ValidationException as e:
    #     raise ValidationException(e)

    # 実行モードが「パラメータ確認」の場合は終了
    if run_mode == const.RUN_MODE_PARAM:
        timestamp = get_timestamp()
        wsDb.db_transaction_start()
        data = {
            "EXECUTION_NO": execution_no,
            "STATUS_ID": const.STATUS_COMPLETE,
            "TIME_START": timestamp,
            "TIME_END": timestamp,
        }
        result = cm.update_execution_record(wsDb, const, data)
        if result[0] is True:
            wsDb.db_commit()
            g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no]))
        return True,

    # 処理対象の作業インスタンス実行
    retBool, execute_data = instance_execution(wsDb, execute_data)

    # # 実行結果から、処理対象の作業インスタンスのステータス更新
    if retBool is False:
        # ステータスを想定外エラーに設定
        execute_data["STATUS_ID"] = const.STATUS_EXCEPTION
        execute_data["TIME_START"] = get_timestamp()
        execute_data["TIME_END"] = get_timestamp()

    # ステータスが実行中以外は終了（緊急停止）
    if execute_data["STATUS_ID"] != const.STATUS_PROCESSING:
        return False, g.appmsg.get_log_message("BKY-10005", [execute_data["STATUS_ID"], execution_no])

    # # [処理]処理対象インスタンス 作業確認の開始(作業No.:{})
    # g.applogger.debug(g.appmsg.get_log_message("MSG-10737", [execution_no]))

    # check_interval = 3
    # while True:
    #     time.sleep(check_interval)

    #     # 処理対象の作業インスタンス情報取得
    #     retBool, execute_data = cm.get_execution_process_info(wsDb, const, execution_no)
    #     if retBool is False:
    #         return False, execute_data
    #     clone_execute_data = execute_data
    #     # 実行結果の確認
    #     retBool, clone_execute_data, db_update_need = instance_checkcondition(wsDb, ansdrv, ans_if_info, clone_execute_data, driver_id, tower_host_list)  # noqa: E501

    #     # ステータスが更新されたか判定
    #     if db_update_need is True:
    #         # 処理対象の作業インスタンスのステータス更新
    #         wsDb.db_transaction_start()
    #         if clone_execute_data['FILE_RESULT']:
    #             zip_tmp_save_path = get_AnsibleDriverTmpPath() + "/" + clone_execute_data['FILE_RESULT']
    #         else:
    #             zip_tmp_save_path = ''

    #         # ステータスが作業終了状態か判定
    #         if execute_data['STATUS_ID'] in [const.STATUS_COMPLETE, const.STATUS_FAILURE, const.STATUS_EXCEPTION, const.STATUS_SCRAM]:
    #             result = InstanceRecodeUpdate(wsDb, driver_id, execution_no, clone_execute_data, 'FILE_RESULT', zip_tmp_save_path)
    #         else:
    #             result = InstanceRecodeUpdate(wsDb, driver_id, execution_no, clone_execute_data, 'UPDATE', zip_tmp_save_path)

    #         if result[0] is True:
    #             wsDb.db_commit()
    #             g.applogger.debug(g.appmsg.get_log_message("BKY-10004", [clone_execute_data["STATUS_ID"], execution_no]))
    #         else:
    #             wsDb.db_rollback()
    #             return False, "InstanceRecodeUpdate->" + str(result[1])

    #     if clone_execute_data['STATUS_ID'] in [const.STATUS_COMPLETE, const.STATUS_FAILURE, const.STATUS_EXCEPTION, const.STATUS_SCRAM]:
    #         break

    # [処理]処理対象インスタンス 作業確認の終了(作業No.:{})
    g.applogger.debug(g.appmsg.get_log_message("MSG-10738", [execution_no]))

    return True,


def instance_execution(wsDb: DBConnectWs, execute_data):
    global const

    module_matter_id_arr = []  # モジュール素材IDを格納する配列
    module_matter_arr = []  # モジュール素材情報を格納する配列
    input_matter_arr = []  # 投入ファイル情報を格納する配列
    input_zip_file_name = ""
    result_matter_arr = []  # 結果ファイル情報を格納する配列
    result_zip_file_name = ""

    vars_set_flag = False  # 変数追加処理を行うかの判定
    vars_data_arr = []  # 対象の変数を格納する配列

    variable_tfvars = []  #  terraform.tfvarsに書き込むkey=value
    secure_tfvars = []  #  secure.tfvarsに書き込むkey=value
    secure_tfvars_flg = False  # secure.tfvarsが存在している

    # パス
    workspace_work_dir = ""  # CLI実行場所
    exe_lock_file_path = ""  # ロックファイル
    resut_file_path = ""  # 実行内容を記録したファイル
    default_tfvars_file_path = ""  # terraform.tfvars
    secure_tfvars_file_path = ""  # secure.tfvars
    emergency_stop_file_path = ""  # 緊急停止ファイル

    # 作業実行データ
    execution_no = execute_data['EXECUTION_NO']
    tf_workspace_id = execute_data['I_WORKSPACE_ID']
    # tf_workspace_name_org = execute_data['I_WORKSPACE_NAME']
    run_mode = execute_data['RUN_MODE']
    pattern_id = execute_data['PATTERN_ID']
    conductor_instance_no = execute_data["CONDUCTOR_INSTANCE_NO"]

    # [処理]処理対象インスタンス 作業実行開始(作業No.:{})
    g.applogger.debug(g.appmsg.get_log_message("MSG-10763", [execution_no]))

    # logファイルを生成
    base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
    log_dir = base_dir + const.DIR_EXECUTE + "/{}/out/".format(execution_no)

    error_log = log_dir + "/error.log"
    init_log = log_dir + "/init.log"
    plan_log = log_dir + "/plan.log"
    error_log = log_dir + "/apply.log"

    os.makedirs(log_dir, exist_ok=True)
    os.chmod(log_dir, 0o777)

    # ディレクトリを準備
    workspace_work_dir = base_dir + const.DIR_WORK + "/{}/work".format(tf_workspace_id);  # CLI実行場所

    exe_lock_file_path = workspace_work_dir + "/.tf_exec_lock";  # ロックファイル
    resut_file_path = workspace_work_dir + "/result.txt";  # 実行内容を記録したファイル

    default_tfvars_file_path = workspace_work_dir + "/terraform.tfvars"  # terraform.tfvars
    secure_tfvars_file_path = workspace_work_dir + "/secure.tfvars"  # secure.tfvars
    emergency_stop_file_path = workspace_work_dir + "/emergency_stop"  # 緊急停止ファイル

    if os.path.exists(workspace_work_dir) is False:
        return False,

    # 前回の実行ファイルの削除
    # destroy以外・・・tfファイルなど、stateファイル以外の全てを削除
    # destroy・・・・・結果ファイル・ロックファイルのみを削除（前回実行状態にする）
    rm_list = [exe_lock_file_path, resut_file_path, emergency_stop_file_path]  # ロックファイル、結果ファイル、緊急停止ファイル

    if run_mode != const.RUN_MODE_DESTROY:
        cmd = '/bin/rm -fr *.tf *.tfvars {}'.format(" ".join(rm_list))
        subprocess.run(cmd, cwd=workspace_work_dir, shell=True)
    else:
        cmd = '/bin/rm -fr {}'.format(" ".join(rm_list))
        subprocess.run(cmd, cwd=workspace_work_dir, shell=True)

    # 緊急停止のチェック
    ret_emgy = IsEmergencyStop()
    if ret_emgy is False:
        True,

    # WORKSPACE_IDから対象Workspace(B_TERRAFORM_CLI_WORKSPACES)のレコードを取得して、workspace名をキャッシュ
    condition = """WHERE `DISUSE_FLAG`=0 AND WORKSPACE_ID = %s"""
    records = wsDb.table_select(const.T_WORKSPACE, condition, [tf_workspace_id])
    if len(records) == 0:
        False, ""
    tf_workspace_name = records[0]['WORKSPACE_NAME']

    if run_mode != const.RUN_MODE_DESTROY:
        # PATTERN_IDからMovement詳細のレコードを取得
        condition = "WHERE  DISUSE_FLAG = '0' AND PATTERN_ID in ({}) ".format(pattern_id)
        records = wsDb.table_select(const.T_MOVEMENT_MODULE, condition, [])

        for record in records:
            module_matter_id_arr.append(record['MODULE_MATTER_ID'])


        # 投入オペレーションの最終実施日を更新する
        wsDb.db_transaction_start()
        result = operation_LAST_EXECUTE_TIMESTAMP_update(wsDb, execute_data["OPERATION_ID"])
        if result[0] is True:
            wsDb.db_commit()
            g.applogger.debug(g.appmsg.get_log_message("BKY-10003", [execution_no]))

        # Moduleのファイル名を取得
        module_matter_id_arr_str = ','.join(module_matter_id_arr)
        condition = "WHERE  DISUSE_FLAG = '0' AND MODULE_MATTER_ID in ({}) ".format(module_matter_id_arr_str)
        records = wsDb.table_select(const.T_MODULE, condition, [])

        if len(records) == 0:
            # Movementに紐づくModuleが存在しません(MovementID:{})
            False, "{}".format(pattern_id)
        for record in records:
            module_matter_arr[record['MODULE_MATTER_ID']] = {
                "matter_name": record['MODULE_MATTER_NAME'],
                "matter_file_name": record['MODULE_MATTER_FILE']
            }

        # 作業実行ディレクトリに、対象のModuleファイルをコピー
        for module_matter_id, val in module_matter_arr.items():
            matter_file_path = "{}/{}/{}/".format(const.DIR_MODULE, module_matter_id, val["matter_file_name"])
            cmd = '/bin/cp -rfp {} {}/.'.format(matter_file_path, workspace_work_dir)

            # 投入ファイルのリストに追加
            input_matter_arr.append(workspace_work_dir + "/" + val["matter_file_name"])

        # operation_noとpattern_idから変数名と代入値を取得
        vars_set_flag = False
        # 処理
        vars_set_flag = True

        # Movementに紐づく代入値がある場合、代入値(Variables)登録処理を実行
        if vars_set_flag is True:
            # 処理
            sensitiveFlag = False
            ary_vars_data = []
            for vars_link_id, data in ary_vars_data.items():
                # 処理

                # 変数のkey&valueをキャッシュ
                var_kv_str_row = makeKVStrRow(var_key, var_value, varsTypeID)
                if sensitiveFlag is False:
                    variable_tfvars.append(var_kv_str_row)
                else:
                    secure_tfvars.append(var_kv_str_row)

            if len(variable_tfvars) > 0:
                # 投入ファイルのリストに追加
                input_matter_arr.append(default_tfvars_file_path)
                # 変数のkey&valueをtfvarsファイルに書き込み
                str_variable_tfvars = "\n".join(variable_tfvars)
                with open(default_tfvars_file_path, 'w', encoding='UTF-8') as f:
                    f.write(str_variable_tfvars)
            if len(secure_tfvars) > 0:
                # 変数のkey&valueをtfvarsファイルに書き込み
                str_secure_tfvars = "\n".join(secure_tfvars)
                with open(secure_tfvars_file_path, 'w', encoding='UTF-8') as f:
                    f.write(str_secure_tfvars)
                # secure.tfvarsが存在
                secure_tfvars_flg = True
    else:
        # 投入ファイルのリストに追加
        input_matter_arr.append(workspace_work_dir + "/*.tf")
        input_matter_arr.append(default_tfvars_file_path)

        # secure.tfvarsが存在
        if os.path.isdir(secure_tfvars_file_path) is True:
            secure_tfvars_flg = True

    # 投入ファイル:ZIPファイルを作成する(ITAダウンロード用)
    retBool, err_msg, zip_input_file = createTmpZipFile(
        execution_no,
        zip_data_source_dir,
        'FILE_INPUT',
        'InputData_')

    if retBool is True:
        execute_data["FILE_INPUT"] = zip_input_file
    else:
        # ZIPファイル作成の作成に失敗しても、ログに出して次に進む
        execute_data["FILE_INPUT"] = None
        g.applogger.error(g.appmsg.get_log_message("BKY-00004", ["createTmpZipFile", err_msg]))

    # ステータスを実行中に更新
    # ログリストを保存

    # 準備で異常がなければ実行にうつる
    g.applogger.debug(g.appmsg.get_log_message("MSG-10761", [execution_no]))
    # 実行エンジンを判定
    ansible_execute = AnsibleExecute()
    if not ans_if_info['ANSIBLE_VAULT_PASSWORD']:
        ans_if_info['ANSIBLE_VAULT_PASSWORD'] = ky_encrypt(const.DF_ANSIBLE_VAULT_PASSWORD)
    retBool = ansible_execute.execute_construct(const, execution_no, conductor_instance_no, "", "", ans_if_info['ANSIBLE_CORE_PATH'], ans_if_info['ANSIBLE_VAULT_PASSWORD'], run_mode, "")  # noqa: E501

    if retBool is True:
        execute_data["STATUS_ID"] = const.STATUS_PROCESSING
        execute_data["TIME_START"] = get_timestamp()
    else:
        # ステータスを想定外エラーに設定
        execute_data["STATUS_ID"] = const.STATUS_EXCEPTION
        execute_data["TIME_START"] = get_timestamp()
        execute_data["TIME_END"] = get_timestamp()

        err_msg = ansible_execute.getLastError()
        if not isinstance(err_msg, str):
            err_msg = str(err_msg)
        ansdrv.LocalLogPrint(
            os.path.basename(inspect.currentframe().f_code.co_filename),
            str(inspect.currentframe().f_lineno), err_msg)
        return False, execute_data, err_msg

    return True, execute_data, tower_host_list


def instance_checkcondition(wsDb: DBConnectWs, if_info, execute_data):
    global const

    db_update_need = False


    execution_no = execute_data["EXECUTION_NO"]

    # ANSIBLEインタフェース情報をローカル変数に格納
    # 2.0では不要 非コンテナ版の場合に有効にする。
    # ans_exec_user = ans_if_info['ANSIBLE_EXEC_USER']
    ans_exec_mode = ans_if_info['ANSIBLE_EXEC_MODE']

    # 実行エンジンを判定
    g.applogger.debug(g.appmsg.get_log_message("MSG-10741", [execution_no]))
    error_flag = 0
    if ans_exec_mode == const.DF_EXEC_MODE_ANSIBLE:
        ansible_execute = AnsibleExecute()
        status = ansible_execute.execute_statuscheck(const, execution_no)

        # 想定外エラーはログを出す
        if status == const.STATUS_EXCEPTION:
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
            const.DF_CHECKCONDITION_FUNCTION,
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
        if multiple_log_mark and str(execute_data['MULTIPLELOG_MODE']) != multiple_log_mark:
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
        if status in [const.STATUS_COMPLETE, const.STATUS_FAILURE, const.STATUS_EXCEPTION, const.STATUS_SCRAM]:
            pass
        else:
            status = -1

    # 状態をログに出力
    g.applogger.debug(g.appmsg.get_log_message("BKY-10006", [execution_no, status]))

    # 5:正常終了時
    # 6:完了(異常)
    # 7:想定外エラー
    # 8:緊急停止
    if status in [const.STATUS_COMPLETE, const.STATUS_FAILURE, const.STATUS_EXCEPTION, const.STATUS_SCRAM] or error_flag != 0:
        db_update_need = True
        # 実行エンジンを判定
        if ans_exec_mode == const.DF_EXEC_MODE_ANSIBLE:
            pass
        else:
            # 実行結果ファイルをTowerから転送
            # 戻り値は確認しない
            multiple_log_mark = ""
            multiple_log_file_json_ary = ""
            AnsibleTowerExecution(
                driver_id,
                const.DF_RESULTFILETRANSFER_FUNCTION,
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

        tmp_array_dirs = ansdrv.getAnsibleWorkingDirectories(const.vg_OrchestratorSubId_dir, execution_no)
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
        if status == const.STATUS_PROCESSING and execute_data["STATUS_ID"] == const.STATUS_PROCESS_DELAYED:
            pass
        else:
            execute_data["STATUS_ID"] = status
            execute_data["TIME_END"] = get_timestamp()

    # 遅延を判定
    # 遅延タイマを取得
    time_limit = int(execute_data['I_TIME_LIMIT']) if execute_data['I_TIME_LIMIT'] else None
    delay_flag = 0

    # ステータスが実行中(3)、かつ制限時間が設定されている場合のみ遅延判定する
    if execute_data["STATUS_ID"] == const.STATUS_PROCESSING and time_limit:
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
            g.applogger.debug(g.appmsg.get_log_message("MSG-10707", [execution_no]))
        else:
            g.applogger.debug(g.appmsg.get_log_message("MSG-10708", [execution_no]))

    if delay_flag == 1:
        db_update_need = True
        # ステータスを「実行中(遅延)」とする
        execute_data["STATUS_ID"] = const.STATUS_PROCESS_DELAYED

    # 実行エンジンを判定
    if ans_exec_mode != const.DF_EXEC_MODE_ANSIBLE:
        # 5:正常終了時
        # 6:完了(異常)
        # 7:想定外エラー
        # 8:緊急停止
        if status in [const.STATUS_COMPLETE, const.STATUS_FAILURE, const.STATUS_EXCEPTION, const.STATUS_SCRAM]:
            # [処理]Ansible Automation Controller クリーニング 開始(作業No.:{})
            g.applogger.debug(g.appmsg.get_log_message("MSG-10743", [execution_no]))

            # 戻り値は確認しない
            AnsibleTowerExecution(
                driver_id,
                const.DF_DELETERESOURCE_FUNCTION,
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


def IsEmergencyStop():
    global execution_no
    global const
    global workspace_work_dir

    # 緊急停止を検知しました
    g.applogger.debug(g.appmsg.get_log_message("MSG-10763", [execution_no]))

    pass


def makeKVStrRow(key, value, type_id):
    str_row = ''

    if (type_id == '' or type_id == '1' or type_id == '18') or not value:
        str_row = '{} = "{}"'.format(key, value)
    else:
        str_row = '{} = {}'.format(key, value)

    return str_row


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
        driver_id: ドライバ区分
        execution_no: 作業番号
        execute_data: 更新内容配列
        update_column_name: 更新対象のFileUpLoadColumn名
        zip_tmp_save_path: 一時的に作成したzipファイルのパス
    RETRUN:
        True/False, errormsg
    """
    global const

    TableDict = {}
    TableDict["MENU_REST"] = {}
    TableDict["MENU_REST"][const.DF_LEGACY_DRIVER_ID] = "execution_list_ansible_legacy"
    TableDict["MENU_REST"][const.DF_PIONEER_DRIVER_ID] = "execution_list_ansible_pioneer"
    TableDict["MENU_REST"][const.DF_LEGACY_ROLE_DRIVER_ID] = "execution_list_ansible_role"
    TableDict["MENU_ID"] = {}
    TableDict["MENU_ID"][const.DF_LEGACY_DRIVER_ID] = "20210"
    TableDict["MENU_ID"][const.DF_PIONEER_DRIVER_ID] = "20312"
    TableDict["MENU_ID"][const.DF_LEGACY_ROLE_DRIVER_ID] = "20412"
    TableDict["TABLE"] = {}
    TableDict["TABLE"][const.DF_LEGACY_DRIVER_ID] = const.vg_exe_ins_msg_table_name
    TableDict["TABLE"][const.DF_PIONEER_DRIVER_ID] = const.vg_exe_ins_msg_table_name
    TableDict["TABLE"][const.DF_LEGACY_ROLE_DRIVER_ID] = const.vg_exe_ins_msg_table_name
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
        if execute_data["FILE_INPUT"]:
            ExecStsInstTableConfig[RestNameConfig["FILE_INPUT"]] = execute_data["FILE_INPUT"]  # 入力データ/投入データ

        ExecStsInstTableConfig[RestNameConfig["TIME_START"]] = execute_data['TIME_START'].strftime('%Y/%m/%d %H:%M:%S')
        # 終了時間が設定されていない場合がある
        if execute_data['TIME_END']:
            ExecStsInstTableConfig[RestNameConfig["TIME_END"]] = execute_data['TIME_END'].strftime('%Y/%m/%d %H:%M:%S')
        if "MULTIPLELOG_MODE" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]] = execute_data["MULTIPLELOG_MODE"]
        if "LOGFILELIST_JSON" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]] = execute_data["LOGFILELIST_JSON"]

    # 実行終了の場合
    if update_column_name == "FILE_RESULT":
        if execute_data["FILE_RESULT"]:
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
    retAry = objmenu.exec_maintenance(parameters, execution_no, "", False, False, True)
    result = retAry[0]
    if result is False:
        return False, str(retAry)
    else:
        return True, ""
