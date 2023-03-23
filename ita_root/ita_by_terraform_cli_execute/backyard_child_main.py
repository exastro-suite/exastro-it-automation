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
import time
import json
from shlex import quote
from zc import lockfile
from zc.lockfile import LockError

from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.exception import AppException
from common_libs.common.util import get_timestamp, ky_encrypt
from common_libs.driver.functions import operation_LAST_EXECUTE_TIMESTAMP_update
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
from common_libs.terraform_driver.common.SubValueAutoReg import SubValueAutoReg

from libs import common_functions as cm


# 基本情報
execution_no = ""
tf_workspace_id = ""
# パス
base_dir = ""
workspace_work_dir = ""  # CLI実行場所
exe_lock_file_path = ""  # ロックファイル
result_file_path = ""  # 実行内容を記録したファイル
default_tfvars_file_path = ""  # terraform.tfvars
secure_tfvars_file_path = ""  # secure.tfvars
emergency_stop_file_path = ""  # 緊急停止ファイル
tmp_execution_dir = ""  # zipファイル（投入・結果）作成の作業場所

input_matter_arr = []  # 投入ファイルに必要なファイルリスト
result_matter_arr = []  # 結果ファイルに必要なファイルリスト

input_zip_file_name = ""  # 投入ファイルのパス
result_zip_file_name = ""  # 結果ファイルのパス
#
secure_tfvars_flg = False  # secure.tfvarsが存在している


def backyard_child_main(organization_id, workspace_id):
    """
    [ita_by_terraform_cli_executeの作業実行の子プロセス]
    main logicのラッパー
    """
    global execution_no
    global tf_workspace_id
    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
    args = sys.argv
    tf_workspace_id = args[3]
    execution_no = args[4]
    g.applogger.debug("tf_workspace_id=" + tf_workspace_id)
    g.applogger.debug("execution_no=" + execution_no)
    g.applogger.set_tag("EXECUTION_NO", execution_no)
    g.applogger.debug(g.appmsg.get_log_message("MSG-10720", [execution_no, tf_workspace_id]))

    # db instance
    wsDb = DBConnectWs(workspace_id)  # noqa: F405

    execute_data = {}

    try:
        result, execute_data = main_logic(wsDb)
        if result is True:
            # 正常終了
            g.applogger.debug(g.appmsg.get_log_message("MSG-10721", [execution_no, tf_workspace_id]))
        else:
            g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [execution_no, tf_workspace_id]))
    except AppException as e:
        update_status_error(wsDb, execute_data)

        g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [execution_no, tf_workspace_id]))

        raise e
    except Exception as e:
        update_status_error(wsDb, execute_data)

        g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [execution_no, tf_workspace_id]))

        raise e


def main_logic(wsDb: DBConnectWs):  # noqa: C901
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
    global base_dir
    global workspace_work_dir
    global exe_lock_file_path
    global result_file_path
    global default_tfvars_file_path
    global secure_tfvars_file_path
    global emergency_stop_file_path
    global tmp_execution_dir

    # 処理対象の作業インスタンス情報取得
    retBool, execute_data = cm.get_execution_process_info(wsDb, TFCLIConst, execution_no)
    if retBool is False:
        err_log = g.appmsg.get_log_message(execute_data, [execution_no])
        raise Exception(err_log)

    run_mode = execute_data['RUN_MODE']
    movement_id = execute_data['MOVEMENT_ID']
    operation_id = execute_data['OPERATION_ID']

    # 「代入値管理」へのレコード登録実行。resultにはboolが、msgにはエラー時のメッセージが入る。
    sub_value_auto_reg = SubValueAutoReg(wsDb, TFCLIConst, operation_id, movement_id, execution_no)
    result, msg = sub_value_auto_reg.set_assigned_value_from_parameter_sheet()
    if result is False:
        g.applogger.error(msg)
        return False, execute_data

    # 実行モードが「パラメータ確認」の場合は終了
    if run_mode == TFCLIConst.RUN_MODE_PARAM:
        wsDb.db_transaction_start()
        update_data = {
            "EXECUTION_NO": execution_no,
            "STATUS_ID": TFCLIConst.STATUS_COMPLETE,
            "TIME_END": get_timestamp(),
        }
        result, execute_data = cm.update_execution_record(wsDb, TFCLIConst, update_data)
        if result is True:
            wsDb.db_commit()
            g.applogger.debug(g.appmsg.get_log_message("MSG-10731", [execution_no]))

        return True, execute_data

    # 緊急停止のチェック
    ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data)
    if ret_emgy is False:
        return True, execute_data

    # パスの生成
    base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
    workspace_work_dir = base_dir + TFCLIConst.DIR_WORK + "/{}/work".format(tf_workspace_id)  # CLI実行場所
    tmp_execution_dir = base_dir + TFCLIConst.DIR_TEMP + "/" + execution_no  # zipファイル（投入・結果）作成の作業場所

    exe_lock_file_path = workspace_work_dir + "/.tf_exec_lock"  # ロックファイル
    result_file_path = workspace_work_dir + "/result.txt"  # 実行内容を記録したファイル

    default_tfvars_file_path = workspace_work_dir + "/terraform.tfvars"  # terraform.tfvars
    secure_tfvars_file_path = workspace_work_dir + "/secure.tfvars"  # secure.tfvars
    emergency_stop_file_path = workspace_work_dir + "/" + TFCLIConst.FILE_EMERGENCY_STOP  # 緊急停止ファイル

    if os.path.exists(workspace_work_dir) is False:
        return False, execute_data

    os.makedirs(tmp_execution_dir, exist_ok=True)
    os.chmod(tmp_execution_dir, 0o777)

    # 前回の実行ファイルの削除
    # destroy以外・・・stateファイル以外の全てを削除
    # destroy・・・・・↓（前回実行状態にする）
    # ロックファイル、結果ファイル、緊急停止ファイルは必ず削除
    rm_list = []
    rm_list.append(quote(exe_lock_file_path))
    rm_list.append(quote(result_file_path))
    rm_list.append(quote(emergency_stop_file_path))

    if run_mode != TFCLIConst.RUN_MODE_DESTROY:
        cmd = '/bin/rm -fr *.tf *.tfvars {}' + ' '.join(rm_list)
        subprocess.run(cmd, shell=True, cwd=workspace_work_dir)
    else:
        cmd = '/bin/rm -fr {}' + ' '.join(rm_list)
        subprocess.run(cmd, shell=True, cwd=workspace_work_dir)

    # 変数ファイルの準備
    PrepareVarsFile(wsDb, execute_data)

    # 緊急停止のチェック
    ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data)
    if ret_emgy is False:
        True, execute_data

    # 処理対象の作業インスタンス実行
    retBool, execute_data = instance_execution(wsDb, execute_data)

    # 実行結果から、処理対象の作業インスタンスのステータス更新
    if retBool is False:
        # ステータスを想定外エラーに設定
        update_status_error(wsDb, execute_data)
        return False, execute_data

    return True, execute_data


def instance_execution(wsDb: DBConnectWs, execute_data):
    global input_matter_arr
    global result_matter_arr

    # 作業実行データ
    # tf_workspace_name_org = execute_data['I_WORKSPACE_NAME']
    run_mode = execute_data['RUN_MODE']
    conductor_instance_no = execute_data["CONDUCTOR_INSTANCE_NO"]

    # [処理]処理対象インスタンス 作業実行開始(作業No.:{})
    g.applogger.debug(g.appmsg.get_log_message("MSG-10763", [execution_no]))

    # logファイルを生成
    log_dir = base_dir + TFCLIConst.DIR_EXECUTE + "/{}/out/".format(execution_no)

    error_log = log_dir + "error.log"
    init_log = log_dir + "init.log"
    plan_log = log_dir + "plan.log"
    apply_log = log_dir + "apply.log"

    os.makedirs(log_dir, exist_ok=True)
    os.chmod(log_dir, 0o777)

    # 投入ZIPファイルを作成する(ITAダウンロード用)
    # エラーを無視する
    is_zip = MakeInputZipFile()

    # ステータスを実行中に更新
    wsDb.db_transaction_start()
    update_data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": TFCLIConst.STATUS_PROCESSING,
    }
    if is_zip is True:
        update_data["FILE_INPUT"] = input_zip_file_name
    # ログリストを保存
    logfilelist_json = ["init.log", "plan.log"]
    if TFCLIConst.RUN_MODE_APPLY or TFCLIConst.RUN_MODE_DESTROY:
        logfilelist_json.append("apply.log")
    update_data["LOGFILELIST_JSON"] = json.dumps(logfilelist_json)
    update_data["MULTIPLELOG_MODE"] = 1
    result, execute_data = cm.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10731", [execution_no]))

    # 準備で異常がなければ、terraformコマンドの実行にうつる
    g.applogger.debug(g.appmsg.get_log_message("MSG-10761", [execution_no]))
    # ファイルによる実行中の排他ロック
    try:
        lock = lockfile.LockFile(exe_lock_file_path)
    except LockError:
        g.applogger.debug('lock-error')
        return False, execute_data

    # 更新するステータスの初期値
    update_status = TFCLIConst.STATUS_COMPLETE

    # initコマンド
    command = ["terraform", "init", "-no-color"]
    ret_status, execute_data = ExecCommand(wsDb, execute_data, command, init_log, error_log, True)
    if ret_status != TFCLIConst.STATUS_COMPLETE:
        update_status = ret_status
    result_matter_arr.append(error_log)
    result_matter_arr.append(workspace_work_dir + "/.terraform.lock.hcl")
    result_matter_arr.append(init_log)

    if ret_status == TFCLIConst.STATUS_COMPLETE:
        # 緊急停止のチェック
        ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data)
        if ret_emgy is False:
            True, execute_data

        # planコマンド
        command_options = ["-no-color", "-input=false"]
        if secure_tfvars_flg is True:
            command_options.append("-var-file secure.tfvars")
        if run_mode != TFCLIConst.RUN_MODE_DESTROY:
            command = ["terraform", "plan"]
            command.extend(command_options)
        else:
            command = ["terraform", "plan", "-destroy"]
            command.extend(command_options)

        ret_status, execute_data = ExecCommand(wsDb, execute_data, command, plan_log, error_log)
        if ret_status != TFCLIConst.STATUS_COMPLETE:
            update_status = ret_status
        result_matter_arr.append(plan_log)

    if ret_status == TFCLIConst.STATUS_COMPLETE:
        # 緊急停止のチェック
        ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data)
        if ret_emgy is False:
            True, execute_data

        # applyコマンド
        command_options = ["-no-color", "-auto-approve"]
        if secure_tfvars_flg is True:
            command_options.append("-var-file secure.tfvars")
        if run_mode == TFCLIConst.RUN_MODE_APPLY:
            command = ["terraform", "apply"]
            command.extend(command_options)
        # destroyコマンド
        elif run_mode == TFCLIConst.RUN_MODE_DESTROY:
            command = ["terraform", "destroy"]
            command.extend(command_options)

        ret_status, execute_data = ExecCommand(wsDb, execute_data, command, apply_log, error_log)
        if ret_status != TFCLIConst.STATUS_COMPLETE:
            update_status = ret_status
        result_matter_arr.append(apply_log)

        # stateファイルの暗号化
        # エラーを無視する
        SaveEncryptStateFile(execute_data)

    lock.close()

    # 結果ZIPファイルを作成する(ITAダウンロード用)
    # エラーを無視する
    result_matter_arr.append(result_file_path)
    is_zip = MakeResultZipFile()

    # Conductorからの実行時、output出力結果を格納する


    # 最終ステータスを更新
    wsDb.db_transaction_start()
    update_data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": update_status,
        "TIME_END": get_timestamp(),
    }
    if is_zip is True:
        update_data["FILE_RESULT"] = result_zip_file_name

    result, execute_data = cm.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10733", [execution_no]))

    return True, execute_data


def update_status_error(wsDb: DBConnectWs, execute_data):
    """
    異常終了と判定した場合のステータス更新

    Arguments:
        wsDb: DBConnectWs
        tf_workspace_id: terraformのワークスペースID
        execution_no: 作業実行番号
    Returns:

    """
    wsDb.db_transaction_start()
    update_data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": TFCLIConst.STATUS_EXCEPTION,
        "TIME_END": get_timestamp(),
    }
    if len(input_matter_arr) > 0 and "FILE_INPUT" not in execute_data:
        is_zip = MakeResultZipFile()
        if is_zip is True:
            update_data["FILE_INPUT"] = input_zip_file_name
    elif len(result_matter_arr) > 0 and "FILE_RESULT" not in execute_data:
        is_zip = MakeInputZipFile()
        if is_zip is True:
            update_data["FILE_RESULT"] = result_zip_file_name

    result, execute_data = cm.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no, tf_workspace_id]))


# コマンド実行
def ExecCommand(wsDb, execute_data, command, cmd_log, error_log, init_flg=False):
    time_limit = execute_data['I_TIME_LIMIT']  # 遅延タイマ
    current_status = execute_data['STATUS_ID']

    # すでに結果ファイルが存在していた（重複処理が走らなければ、ありえない)
    if init_flg is True and os.path.exists(result_file_path):
        g.applogger.debug("result.txt still exists")
        return TFCLIConst.STATUS_EXCEPTION, execute_data

    str_command = " ".join(command)
    g.applogger.debug(str_command)
    command.insert(0, "sudo")  # sudo権限
    proc = subprocess.Popen(command, cwd=workspace_work_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 結果ファイルにコマンドとPIDを書き込む
    str_body = str_command + " : PID=" + str(proc.pid) + "\n"
    if init_flg is True:
        with open(result_file_path, mode='w', encoding='UTF-8') as f:
            f.write(str_body)
    else:
        with open(result_file_path, mode='a', encoding='UTF-8') as f:
            f.write(str_body)

    # ステータスが実行中(3)、かつ制限時間が設定されている場合のみ遅延判定する
    delay_flag = False
    if current_status == TFCLIConst.STATUS_PROCESSING and time_limit:
        check_interval = 3
        while True:
            time.sleep(check_interval)

            # 開始時刻(「エポック秒.マイクロ秒」)を生成(localタイムでutcタイムではない)
            rec_time_start = execute_data['TIME_START']
            starttime_unixtime = rec_time_start.timestamp()
            # 開始時刻(マイクロ秒)＋制限時間(分→秒)＝制限時刻(マイクロ秒)
            limit_unixtime = starttime_unixtime + (time_limit * 60)
            # 現在時刻(「エポック秒.マイクロ秒」)を生成(localタイムでutcタイムではない)
            now_unixtime = time.time()
            # 制限時刻と現在時刻を比較
            if limit_unixtime < now_unixtime:
                delay_flag = True
                g.applogger.debug(g.appmsg.get_log_message("MSG-10707", [execution_no]))
            else:
                g.applogger.debug(g.appmsg.get_log_message("MSG-10708", [execution_no]))

            if delay_flag is True:
                # ステータスを「実行中(遅延)」とする
                wsDb.db_transaction_start()
                update_data = {
                    "EXECUTION_NO": execution_no,
                    "STATUS_ID": TFCLIConst.STATUS_PROCESS_DELAYED,
                }
                result, execute_data = cm.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
                if result is True:
                    wsDb.db_commit()
                    g.applogger.debug(g.appmsg.get_log_message("MSG-10732", [execution_no]))
                    break

            # プロセスが実行中はNoneを返す
            if proc.poll() is not None:
                # 終了判定
                break

    # 結果を受け取る
    stdout_data, stderr_data = proc.communicate()

    with open(cmd_log, mode='w', encoding='UTF-8') as f:
        f.write(stdout_data)

    with open(error_log, mode='w', encoding='UTF-8') as f:
        f.write(stderr_data)

    exit_status = proc.returncode
    if exit_status == 0:
        # 正常終了した場合
        update_status = TFCLIConst.STATUS_COMPLETE
        str_body = "COMPLETED(0)\n"
    else:
        # 異常終了した場合
        update_status = TFCLIConst.STATUS_FAILURE
        str_body = "PREVENTED({})\n".format(exit_status)

    # 結果を書き込む
    with open(result_file_path, mode='a', encoding='UTF-8') as f:
        f.write(str_body)

    return update_status, execute_data


# tfvarsファイルに書き込む行データを作成
def MakeKVStrRow(key, value, type_id):
    str_row = ''

    if (type_id == '' or type_id == '1' or type_id == '18') or not value:
        str_row = '{} = "{}"'.format(key, value)
    else:
        str_row = '{} = {}'.format(key, value)

    return str_row


# 投入zipファイルを作成
def MakeInputZipFile():
    global input_zip_file_name

    # ファイル名の定義
    input_zip_file_name = 'InputData_' + execution_no + '.zip'

    # ZIPファイルを作成
    command = ['zip', '-j', tmp_execution_dir + "/" + input_zip_file_name]
    command.extend(input_matter_arr)
    # g.applogger.debug(command)
    cp = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # g.applogger.debug(cp)
    if cp.returncode != 0:
        # zipファイルの作成に失敗しました
        # g.applogger.debug(cp.returncode)
        # g.applogger.debug(cp.stdout)
        g.applogger.error(g.appmsg.get_log_message("BKY-00004", ["Creating InputZipFile", ""]))
        return False

    return True


def MakeResultZipFile():
    global result_zip_file_name

    # ファイル名の定義
    result_zip_file_name = 'ResultData_' + execution_no + '.zip'

    # ZIPファイルを作成
    command = ['zip', '-j', tmp_execution_dir + "/" + result_zip_file_name]
    command.extend(result_matter_arr)
    # g.applogger.debug(command)
    cp = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # g.applogger.debug(cp)
    if cp.returncode != 0:
        # zipファイルの作成に失敗しました
        # g.applogger.debug(cp.returncode)
        # g.applogger.debug(cp.stdout)
        g.applogger.error(g.appmsg.get_log_message("BKY-00004", ["Creating ResultZipFile", ""]))
        return False

    return True


# terraformのstateファイルを暗号化
def SaveEncryptStateFile(execute_data):
    global result_matter_arr

    try:
        # 1:tfstate
        org_state_file = workspace_work_dir + "/terraform.tfstate"
        encrypt_state_file = tmp_execution_dir + "/terraform.tfstate"

        if os.path.isfile(org_state_file) is False:
            return True
        else:
            # stateファイルの中身を取得
            str_body = ""
            with open(org_state_file, mode='r', encoding='UTF-8') as f:
                str_body = f.read()

        # ファイルに中身を新規書き込み
        str_encrypt_body = ky_encrypt(str_body)
        with open(encrypt_state_file, mode='w', encoding='UTF-8') as f:
            f.write(str_encrypt_body)
        # 結果ファイルのリストに追加
        result_matter_arr.append(encrypt_state_file)

        # 2:tfstate.backup
        org_state_file = workspace_work_dir + "/terraform.tfstate.backup"
        encrypt_state_file = tmp_execution_dir + "/terraform.tfstate.backup"

        if os.path.isfile(org_state_file) is False:
            return True
        else:
            # stateファイルの中身を取得
            str_body = ""
            with open(org_state_file, mode='r', encoding='UTF-8') as f:
                str_body = f.read()

        # ファイルに中身を新規書き込み
        str_encrypt_body = ky_encrypt(str_body)
        with open(encrypt_state_file, mode='w', encoding='UTF-8') as f:
            f.write(str_encrypt_body)
        # 結果ファイルのリストに追加
        result_matter_arr.append(encrypt_state_file)

        return True
    except Exception as e:
        g.applogger.error(e)
        return False


# 緊急停止の処理
def IsEmergencyStop(wsDb: DBConnectWs, execute_data):
    # 緊急停止ファイルの存在有無
    if os.path.exists(emergency_stop_file_path) is False:
        return True, execute_data

    # 緊急停止を検知しました
    g.applogger.debug(g.appmsg.get_log_message("MSG-10763", [execution_no]))

    # 結果ファイルがあれば作る
    if len(result_matter_arr) > 0:
        MakeResultZipFile()

    # ステータスを緊急停止に更新
    wsDb.db_transaction_start()
    update_data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": TFCLIConst.STATUS_SCRAM,
        "TIME_END": get_timestamp()
    }
    if len(input_matter_arr) > 0 and not execute_data["FILE_INPUT"]:
        is_zip = MakeResultZipFile()
        if is_zip is True:
            update_data["FILE_INPUT"] = input_zip_file_name
    elif len(result_matter_arr) > 0 and not execute_data["FILE_RESULT"]:
        is_zip = MakeInputZipFile()
        if is_zip is True:
            update_data["FILE_RESULT"] = result_zip_file_name

    result, execute_data = cm.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10736", [execution_no]))

    return False, execute_data


def PrepareVarsFile(wsDb: DBConnectWs, execute_data):
    global secure_tfvars_flg

    module_matter_id_str_arr = []  # モジュール素材IDを格納する配列
    module_matter_arr = {}  # モジュール素材情報を格納する配列

    vars_set_flag = False  # 変数追加処理を行うかの判定
    vars_data_arr = {}  # 対象の変数を格納する配列

    variable_tfvars = []  # terraform.tfvarsに書き込むkey=value
    secure_tfvars = []  # secure.tfvarsに書き込むkey=value

    # 作業実行データ
    run_mode = execute_data['RUN_MODE']
    movement_id = execute_data['MOVEMENT_ID']
    operation_id = execute_data['OPERATION_ID']

    # WORKSPACE_IDから対象Workspace(B_TERRAFORM_CLI_WORKSPACES)のレコードを取得して、workspace名をキャッシュ
    # condition = """WHERE `DISUSE_FLAG`=0 AND WORKSPACE_ID = %s"""
    # records = wsDb.table_select(TFCLIConst.T_WORKSPACE, condition, [tf_workspace_id])
    # if len(records) == 0:
    #     False, execute_data
    # tf_workspace_name = records[0]['WORKSPACE_NAME']

    if run_mode != TFCLIConst.RUN_MODE_DESTROY:
        # 投入オペレーションの最終実施日を更新する
        result = operation_LAST_EXECUTE_TIMESTAMP_update(wsDb, operation_id)
        if result[0] is True:
            g.applogger.debug(g.appmsg.get_log_message("BKY-10003", [execution_no]))

        # MOVEMENT_IDからMovement詳細のレコードを取得
        condition = "WHERE DISUSE_FLAG = '0' AND MOVEMENT_ID = %s"
        records = wsDb.table_select(TFCLIConst.T_MOVEMENT_MODULE, condition, [movement_id])

        for record in records:
            module_matter_id_str_arr.append("'" + record['MODULE_MATTER_ID'] + "'")

        # Moduleのファイル名を取得
        module_matter_id_str_arr_concat = ','.join(module_matter_id_str_arr)
        condition = "WHERE DISUSE_FLAG = '0' AND MODULE_MATTER_ID in ({}) ".format(module_matter_id_str_arr_concat)
        records = wsDb.table_select(TFCLIConst.T_MODULE, condition, [])

        if len(records) == 0:
            # Movementに紐づくModuleが存在しません(MovementID:{})
            return False, execute_data
        for record in records:
            module_matter_arr[record['MODULE_MATTER_ID']] = {
                "matter_name": record['MODULE_MATTER_NAME'],
                "matter_file_name": record['MODULE_MATTER_FILE']
            }

        # 作業実行ディレクトリに、対象のModuleファイルをコピー
        for module_matter_id, val in module_matter_arr.items():
            matter_file_path = "{}{}/{}/{}".format(base_dir, TFCLIConst.DIR_MODULE, module_matter_id, val["matter_file_name"])
            cp = subprocess.run(['/bin/cp', '-rfp', matter_file_path, workspace_work_dir + '/.'])
            if cp.returncode != 0 or cp.stderr:
                # 対象のModuleファイルをコピーに失敗しました
                g.applogger.debug(cp)
                g.applogger.error(g.appmsg.get_log_message("BKY-00004", ["Copying ModuleFile", ""]))
                return False, execute_data

            # 投入ファイルのリストに追加
            input_matter_arr.append(workspace_work_dir + "/" + val["matter_file_name"])

        # operation_noとmovement_idから変数名と代入値を取得
        # sql = "SELECT \
        #     {}.MODULE_VARS_LINK_ID, \
        #     ".format()

        # records = wsDb.sql_execute(sql, [movement_id])
        # # 代入値（変数）の有無フラグ
        # vars_set_flag = False if len(records) == 0 else True
        # vars_list = []
        # member_vars_link_id_list = []
        # for record in records:
        #     if "MEMBER_VARS" in record and record["MEMBER_VARS"] is not None:
        #         # メンバー変数
        #         member_vars_link_id_list.append(record)
        #     else:
        #         vars_list.append(record)


        # Movementに紐づく代入値がある場合、代入値(Variables)登録処理を実行
        if vars_set_flag is True:
            # 処理
            sensitiveFlag = False
            for vars_link_id, data in vars_data_arr.items():
                # 処理

                # 変数のkey&valueをキャッシュ
                var_kv_str_row = MakeKVStrRow(var_key, var_value, varsTypeID)
                if sensitiveFlag is False:
                    variable_tfvars.append(var_kv_str_row)
                else:
                    secure_tfvars.append(var_kv_str_row)

            if len(variable_tfvars) > 0:
                # 投入ファイルのリストに追加
                input_matter_arr.append(default_tfvars_file_path)
                # 変数のkey&valueをtfvarsファイルに書き込み
                str_variable_tfvars = "\n".join(variable_tfvars)
                with open(default_tfvars_file_path, mode='w', encoding='UTF-8') as f:
                    f.write(str_variable_tfvars)
            if len(secure_tfvars) > 0:
                # 変数のkey&valueをtfvarsファイルに書き込み
                str_secure_tfvars = "\n".join(secure_tfvars)
                with open(secure_tfvars_file_path, mode='w', encoding='UTF-8') as f:
                    f.write(str_secure_tfvars)
                # secure.tfvarsが存在
                secure_tfvars_flg = True
    else:
        # 投入ファイルのリストに追加
        input_matter_arr.append(workspace_work_dir + "/*.tf")
        input_matter_arr.append(default_tfvars_file_path)

        # secure.tfvarsが存在
        if os.path.exists(secure_tfvars_file_path) is True:
            secure_tfvars_flg = True
