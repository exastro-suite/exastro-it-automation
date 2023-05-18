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
from common_libs.common.util import get_timestamp, ky_encrypt, ky_decrypt
from common_libs.ci.util import log_err
from common_libs.driver.functions import operation_LAST_EXECUTE_TIMESTAMP_update
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
from common_libs.terraform_driver.common.SubValueAutoReg import SubValueAutoReg
from common_libs.terraform_driver.common.by_execute import \
    get_type_info, encode_hcl, get_member_vars_ModuleVarsLinkID_for_hcl, generate_member_vars_array_for_hcl
from libs import functions as func


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
    retBool, execute_data = func.get_execution_process_info(wsDb, TFCLIConst, execution_no)
    if retBool is False:
        log_err(execute_data)
        return False, execute_data

    run_mode = execute_data['RUN_MODE']
    movement_id = execute_data['MOVEMENT_ID']
    operation_id = execute_data['OPERATION_ID']

    # 「代入値管理」へのレコード登録実行。resultにはboolが、msgにはエラー時のメッセージが入る。
    sub_value_auto_reg = SubValueAutoReg(wsDb, TFCLIConst, operation_id, movement_id, execution_no)
    result, msg = sub_value_auto_reg.set_assigned_value_from_parameter_sheet()
    if result is False:
        # log_err(msg)
        return False, execute_data

    # 実行モードが「パラメータ確認」の場合は終了
    if run_mode == TFCLIConst.RUN_MODE_PARAM:
        wsDb.db_transaction_start()
        update_data = {
            "EXECUTION_NO": execution_no,
            "STATUS_ID": TFCLIConst.STATUS_COMPLETE,
            "TIME_END": get_timestamp(),
        }
        result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data)
        if result is True:
            wsDb.db_commit()
            g.applogger.debug(g.appmsg.get_log_message("MSG-10731", [execution_no]))

        return True, execute_data

    # 緊急停止のチェック
    ret_emgy, execute_data = is_emergency_stop(wsDb, execute_data)
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
    prepare_vars_file(wsDb, execute_data)

    # 緊急停止のチェック
    ret_emgy, execute_data = is_emergency_stop(wsDb, execute_data)
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
    is_zip = make_input_zip_file()

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
    result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10731", [execution_no]))

    # 準備で異常がなければ、terraformコマンドの実行にうつる
    g.applogger.debug(g.appmsg.get_log_message("MSG-10761", [execution_no]))
    # ファイルによる実行中の排他ロック
    try:
        lock = lockfile.LockFile(exe_lock_file_path)
    except LockError:
        log_err(g.appmsg.get_log_message('BKY-52002', [execution_no]))
        return False, execute_data

    # 更新するステータスの初期値
    update_status = TFCLIConst.STATUS_COMPLETE

    # initコマンド
    command = ["terraform", "init", "-no-color"]
    ret_status, execute_data = exec_command(wsDb, execute_data, command, init_log, error_log, True)
    if ret_status != TFCLIConst.STATUS_COMPLETE:
        update_status = ret_status
    result_matter_arr.append(error_log)
    result_matter_arr.append(workspace_work_dir + "/.terraform.lock.hcl")
    result_matter_arr.append(init_log)

    if ret_status == TFCLIConst.STATUS_COMPLETE:
        # 緊急停止のチェック
        ret_emgy, execute_data = is_emergency_stop(wsDb, execute_data)
        if ret_emgy is False:
            True, execute_data

        # planコマンド
        command_options = ["-no-color", "-input=false"]
        if secure_tfvars_flg is True:
            command_options.append("-var-file")
            command_options.append("secure.tfvars")
        if run_mode != TFCLIConst.RUN_MODE_DESTROY:
            command = ["terraform", "plan"]
            command.extend(command_options)
        else:
            command = ["terraform", "plan", "-destroy"]
            command.extend(command_options)

        ret_status, execute_data = exec_command(wsDb, execute_data, command, plan_log, error_log)
        if ret_status != TFCLIConst.STATUS_COMPLETE:
            update_status = ret_status
        result_matter_arr.append(plan_log)

    if ret_status == TFCLIConst.STATUS_COMPLETE:
        # 緊急停止のチェック
        ret_emgy, execute_data = is_emergency_stop(wsDb, execute_data)
        if ret_emgy is False:
            True, execute_data

        # applyコマンド
        command_options = ["-no-color", "-auto-approve"]
        if secure_tfvars_flg is True:
            command_options.append("-var-file")
            command_options.append("secure.tfvars")
        if run_mode == TFCLIConst.RUN_MODE_APPLY:
            command = ["terraform", "apply"]
            command.extend(command_options)
        # destroyコマンド
        elif run_mode == TFCLIConst.RUN_MODE_DESTROY:
            command = ["terraform", "destroy"]
            command.extend(command_options)

        ret_status, execute_data = exec_command(wsDb, execute_data, command, apply_log, error_log)
        if ret_status != TFCLIConst.STATUS_COMPLETE:
            update_status = ret_status
        result_matter_arr.append(apply_log)

        # stateファイルの暗号化
        # エラーを無視する
        save_encrypt_statefile(execute_data)

    lock.close()

    # 結果ZIPファイルを作成する(ITAダウンロード用)
    # エラーを無視する
    result_matter_arr.append(result_file_path)
    is_zip = make_result_zip_file()

    # Conductorからの実行時、output出力結果を格納する
    output_conducor(conductor_instance_no)

    # 最終ステータスを更新
    wsDb.db_transaction_start()
    update_data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": update_status,
        "TIME_END": get_timestamp(),
    }
    if is_zip is True:
        update_data["FILE_RESULT"] = result_zip_file_name

    result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("BKY-52010", [update_status, execution_no]))

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
        is_zip = make_result_zip_file()
        if is_zip is True:
            update_data["FILE_INPUT"] = input_zip_file_name
    elif len(result_matter_arr) > 0 and "FILE_RESULT" not in execute_data:
        is_zip = make_input_zip_file()
        if is_zip is True:
            update_data["FILE_RESULT"] = result_zip_file_name

    result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no, tf_workspace_id]))


# コマンド実行
def exec_command(wsDb, execute_data, command, cmd_log, error_log, init_flg=False):
    time_limit = execute_data['I_TIME_LIMIT']  # 遅延タイマ
    current_status = execute_data['STATUS_ID']

    # すでに結果ファイルが存在していた（重複処理が走らなければ、ありえない)
    if init_flg is True and os.path.exists(result_file_path):
        log_err(g.appmsg.get_log_message("BKY-52003", [execution_no]))
        return TFCLIConst.STATUS_EXCEPTION, execute_data

    # terraformコマンドを発行
    str_command = " ".join(command)
    g.applogger.debug(g.appmsg.get_log_message("BKY-52004", [str_command]))
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
                result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
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
def make_kvs_str_row(key, value, type_id):
    str_row = ''

    if (type_id == '' or type_id == '1' or type_id == '18') or not value:
        str_row = '{} = "{}"'.format(key, value)
    else:
        str_row = '{} = {}'.format(key, value)

    return str_row


# 投入zipファイルを作成
def make_input_zip_file():
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
        log_err(g.appmsg.get_log_message("BKY-52005", [command]))
        return False

    return True


def make_result_zip_file():
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
        log_err(g.appmsg.get_log_message("BKY-52006", [command]))
        return False

    return True


# terraformのstateファイルを暗号化
def save_encrypt_statefile(execute_data):
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
        log_err(e)
        return False


# 緊急停止の処理
def is_emergency_stop(wsDb: DBConnectWs, execute_data):
    # 緊急停止ファイルの存在有無
    if os.path.exists(emergency_stop_file_path) is False:
        return True, execute_data

    # 緊急停止を検知しました
    g.applogger.debug(g.appmsg.get_log_message("BKY-52007", [execution_no]))

    # 結果ファイルがあれば作る
    if len(result_matter_arr) > 0:
        make_result_zip_file()

    # ステータスを緊急停止に更新
    wsDb.db_transaction_start()
    update_data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": TFCLIConst.STATUS_SCRAM,
        "TIME_END": get_timestamp()
    }
    if len(input_matter_arr) > 0 and not execute_data["FILE_INPUT"]:
        is_zip = make_input_zip_file()
        if is_zip is True:
            update_data["FILE_INPUT"] = input_zip_file_name
    elif len(result_matter_arr) > 0 and not execute_data["FILE_RESULT"]:
        is_zip = make_result_zip_file()
        if is_zip is True:
            update_data["FILE_RESULT"] = result_zip_file_name

    result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data, tmp_execution_dir)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10736", [execution_no]))

    return False, execute_data


# Conductorからの実行時、output出力結果を格納する
def output_conducor(conductor_instance_no):
    if not conductor_instance_no:
        return

    output_dir = base_dir + "/driver/conductor/{}".format(conductor_instance_no)
    os.makedirs(output_dir, exist_ok=True)
    output_file_name = 'terraform_output_' + execution_no + '.json'
    output_file_path = output_dir + "/" + output_file_name

    command = ["terraform", "output", "-json"]
    cp = subprocess.run(command, cwd=workspace_work_dir, capture_output=True, text=True)

    if cp.returncode == 0:
        # 正常終了した場合
        with open(output_file_path, mode='w', encoding='UTF-8') as f:
            f.write(cp.stdout)

        return True
    else:
        # 異常終了した場合
        cp.check_returncode()
        # g.applogger.error(cp.stderr)

        return False


def prepare_vars_file(wsDb: DBConnectWs, execute_data):  # noqa: C901
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
                # g.applogger.debug(cp)
                log_err(g.appmsg.get_log_message("BKY-52008", ["Copying ModuleFile", matter_file_path, workspace_work_dir]))
                return False, execute_data

            # 投入ファイルのリストに追加
            input_matter_arr.append(workspace_work_dir + "/" + val["matter_file_name"])

        # operation_idとmovement_idから変数名と代入値を取得
        # 下記のSQLについて
        # `T_TERC_VALUE`.`MEMBER_VARS_ID` は、movementメンバー変数紐づけのID（`V_TERC_MVMT_VAR_MEMBER_LINK`.`MVMT_VAR_MEMBER_LINK_ID`）
        # なので　AS `MVMT_VAR_MEMBER_LINK_ID` と名づけ
        # `V_TERC_MVMT_VAR_MEMBER_LINK`.`CHILD_MEMBER_VARS_ID`
        # を　AS `MEMBER_VARS_ID` と名づける（メンバー変数テーブルのIDとして分かるように）
        sql = "SELECT \
                D_TERRAFORM_CLI_VARS_DATA.MODULE_VARS_LINK_ID, \
                D_TERRAFORM_CLI_VARS_DATA.VARS_NAME, \
                D_TERRAFORM_CLI_VARS_DATA.HCL_FLAG, \
                D_TERRAFORM_CLI_VARS_DATA.SENSITIVE_FLAG, \
                D_TERRAFORM_CLI_VARS_DATA.VARS_ENTRY, \
                D_TERRAFORM_CLI_VARS_DATA.MEMBER_VARS_ID, \
                D_TERRAFORM_CLI_VARS_DATA.ASSIGN_SEQ, \
                T_TERC_MOD_VAR_LINK.TYPE_ID, \
                V_TERC_VAR_MEMBER.VARS_ASSIGN_FLAG, \
                D_TERRAFORM_CLI_VARS_DATA.LAST_UPDATE_TIMESTAMP \
            FROM ( \
                SELECT \
                    `T_TERC_VALUE`.`ASSIGN_ID` AS `ASSIGN_ID`, \
                    `T_TERC_VALUE`.`EXECUTION_NO` AS `EXECUTION_NO`, \
                    `T_TERC_VALUE`.`OPERATION_ID` AS `OPERATION_ID`, \
                    `T_TERC_VALUE`.`MOVEMENT_ID` AS `MOVEMENT_ID`, \
                    `V_TERC_MVMT_VAR_LINK`.`MODULE_VARS_LINK_ID` AS `MODULE_VARS_LINK_ID`, \
                    `V_TERC_MVMT_VAR_LINK`.`VARS_NAME` AS `VARS_NAME`, \
                    `T_TERC_VALUE`.`VARS_ENTRY` AS `VARS_ENTRY`, \
                    `T_TERC_VALUE`.`MEMBER_VARS_ID` AS `MVMT_VAR_MEMBER_LINK_ID`, \
                    `V_TERC_MVMT_VAR_MEMBER_LINK`.`CHILD_MEMBER_VARS_ID` AS `MEMBER_VARS_ID`, \
                    `T_TERC_VALUE`.`ASSIGN_SEQ` AS `ASSIGN_SEQ`, \
                    `T_TERC_VALUE`.`HCL_FLAG` AS `HCL_FLAG`, \
                    `T_TERC_VALUE`.`SENSITIVE_FLAG` AS `SENSITIVE_FLAG`, \
                    `T_TERC_VALUE`.`DISUSE_FLAG` AS `DISUSE_FLAG`, \
                    `T_TERC_VALUE`.`LAST_UPDATE_TIMESTAMP` AS `LAST_UPDATE_TIMESTAMP` \
                FROM `T_TERC_VALUE`  \
                    LEFT JOIN `V_TERC_MVMT_VAR_LINK`  \
                        ON( \
                            `V_TERC_MVMT_VAR_LINK`.`MOVEMENT_ID` = `T_TERC_VALUE`.`MOVEMENT_ID` AND  \
                            `V_TERC_MVMT_VAR_LINK`.`MVMT_VAR_LINK_ID` = `T_TERC_VALUE`.`MVMT_VAR_LINK_ID` \
                        ) \
                    LEFT JOIN `V_TERC_MVMT_VAR_MEMBER_LINK`  \
                        ON( \
                            `V_TERC_MVMT_VAR_MEMBER_LINK`.`MOVEMENT_ID` = `T_TERC_VALUE`.`MOVEMENT_ID` AND  \
                            `V_TERC_MVMT_VAR_MEMBER_LINK`.`MVMT_VAR_MEMBER_LINK_ID` = `T_TERC_VALUE`.`MEMBER_VARS_ID` \
                        ) \
                WHERE \
                    T_TERC_VALUE.EXECUTION_NO = %s \
                    AND T_TERC_VALUE.OPERATION_ID = %s \
                    AND T_TERC_VALUE.MOVEMENT_ID = %s  \
                ) AS D_TERRAFORM_CLI_VARS_DATA \
                LEFT OUTER JOIN T_TERC_MOD_VAR_LINK \
                    ON D_TERRAFORM_CLI_VARS_DATA.MODULE_VARS_LINK_ID = T_TERC_MOD_VAR_LINK.MODULE_VARS_LINK_ID \
                LEFT OUTER JOIN V_TERC_VAR_MEMBER \
                    ON D_TERRAFORM_CLI_VARS_DATA.MEMBER_VARS_ID = V_TERC_VAR_MEMBER.CHILD_MEMBER_VARS_ID \
            WHERE \
                T_TERC_MOD_VAR_LINK.DISUSE_FLAG = '0' "
        records = wsDb.sql_execute(sql, [execution_no, operation_id, movement_id])

        # 代入値（変数）の有無フラグ
        vars_set_flag = False if len(records) == 0 else True
        # メンバー変数
        vars_list = []
        # メンバー変数以外の代入値
        member_vars_link_id_list = []

        for record in records:
            if "MEMBER_VARS_ID" in record and record["MEMBER_VARS_ID"] is not None:
                member_vars_link_id_list.append(record)
            else:
                vars_list.append(record)

        for vars in vars_list:
            vars_link_id = vars['MODULE_VARS_LINK_ID']
            vars_name = vars['VARS_NAME']
            vars_entry = vars['VARS_ENTRY']
            vars_assign_seq = vars['ASSIGN_SEQ']
            vars_type_id = vars['TYPE_ID']
            last_update_timestamp = vars['LAST_UPDATE_TIMESTAMP']
            vars_list = []

            # HCL設定を判定
            hcl_flag = False
            if vars['HCL_FLAG'] == '0':
                hcl_flag = False  # 1(OFF)ならfalse
            elif vars['HCL_FLAG'] == '1':
                hcl_flag = True  # 2(ON)ならtrue

            # Sensitive設定を判定
            sensitive_flag = False
            if vars['SENSITIVE_FLAG'] == '0':
                sensitive_flag = False  # 0(OFF)ならfalse
            elif vars['SENSITIVE_FLAG'] == '1':
                sensitive_flag = True  # 1(ON)ならtrue
                vars_entry = ky_decrypt(vars_entry)  # 具体値をデコード

            if vars_link_id not in vars_data_arr:
                vars_data_arr[vars_link_id] = {
                    'VARS_NAME': vars_name,
                    'VARS_ENTRY': vars_entry,
                    'ASSIGN_SEQ': vars_assign_seq,
                    'MEMBER_VARS_ID': [],
                    'HCL_FLAG': hcl_flag,
                    'SENSITIVE_FLAG': sensitive_flag,
                    'VARS_TYPE_ID': vars_type_id,
                    'VARS_LIST': {}
                }
            # 代入値順序のためにキーを生成
            vars_list_len = str(len(vars_data_arr[vars_link_id]['VARS_LIST']))
            if not vars_assign_seq:
                # 代入値順序の値がないものは、ソート時に後ろにいけるようにしておく
                key_name = vars_list_len + "_1_" + str(last_update_timestamp)
            else:
                key_name = str(vars_assign_seq) + "_0_" + str(last_update_timestamp)
            vars_data_arr[vars_link_id]['VARS_LIST'][key_name] = vars_entry

        for vars in member_vars_link_id_list:
            vars_link_id = vars['MODULE_VARS_LINK_ID']
            vars_name = vars['VARS_NAME']
            vars_entry = vars['VARS_ENTRY']
            vars_assign_seq = vars['ASSIGN_SEQ']
            vars_type_id = vars['TYPE_ID']
            vars_member_vars = vars['MEMBER_VARS_ID']
            vars_assign_flag = vars["VARS_ASSIGN_FLAG"]  # 代入値系管理フラグ

            # HCL設定を判定
            hcl_flag = False

            # Sensitive設定を判定
            sensitive_flag = False
            if vars['SENSITIVE_FLAG'] == '0':
                sensitive_flag = False  # 0(OFF)ならFalse
            elif vars['SENSITIVE_FLAG'] == '1':
                sensitive_flag = True  # 1(ON)ならTrue
                vars_entry = ky_decrypt(vars_entry)  # 具体値をデコード

            if vars_link_id not in vars_data_arr:
                vars_data_arr[vars_link_id] = {
                    'VARS_NAME': vars_name,
                    'VARS_ENTRY': vars_entry,
                    'ASSIGN_SEQ': vars_assign_seq,
                    'MEMBER_VARS_ID': vars_member_vars,
                    'HCL_FLAG': hcl_flag,
                    'SENSITIVE_FLAG': sensitive_flag,
                    'VARS_TYPE_ID': vars_type_id,
                    'MEMBER_VARS_LIST': []
                }
            vars_data_arr[vars_link_id]['MEMBER_VARS_LIST'].append({
                'VARS_ENTRY': vars_entry,
                'ASSIGN_SEQ': vars_assign_seq,
                'MEMBER_VARS_ID': vars_member_vars,
                'SENSITIVE_FLAG': sensitive_flag,
                "VARS_ASSIGN_FLAG": vars_assign_flag
            })

        # g.applogger.debug(vars_data_arr)

        # Movementに紐づく代入値がある場合、代入値(Variables)登録処理を実行
        if vars_set_flag is True:
            for vars_link_id, data in vars_data_arr.items():
                var_key = data['VARS_NAME']
                var_value = data['VARS_ENTRY']
                # assign_seq = data['ASSIGN_SEQ']
                vars_list = data['VARS_LIST'] if 'VARS_LIST' in data else {}
                member_vars_list = data['MEMBER_VARS_LIST'] if 'MEMBER_VARS_LIST' in data else []
                hclFlag = data['HCL_FLAG']
                sensitiveFlag = data['SENSITIVE_FLAG']
                vars_type_id = data['VARS_TYPE_ID']
                vars_type_info = get_type_info(wsDb, TFCLIConst, vars_type_id)

                # HCL組み立て
                #########################################
                # 1.Module変数紐付けのタイプが配列型でない場合
                # 2.Module変数紐付けのタイプが配列型且つメンバー変数がない場合
                # 3.Module変数紐付けのタイプが配列型且つメンバー変数である場合
                #########################################
                # 1.Module変数紐付けのタイプが配列型でない場合
                if hclFlag is True or vars_type_info["MEMBER_VARS_FLAG"] == '0' and vars_type_info["ASSIGN_SEQ_FLAG"] == '0' and vars_type_info["ENCODE_FLAG"] == 0:  # noqa:E501
                    pass
                # 2.Module変数紐付けのタイプが配列型且つメンバー変数がない場合
                elif vars_type_info["MEMBER_VARS_FLAG"] == '0' and vars_type_info["ASSIGN_SEQ_FLAG"] == '1' and vars_type_info["ENCODE_FLAG"] == '1':
                    if len(vars_list) > 0:
                        # 代入値順序のために並び替え
                        vars_list2 = dict(sorted(vars_list.items()))
                        # HCLに変換
                        var_value = encode_hcl(list(vars_list2.values()))
                    hclFlag = True
                # 3.Module変数紐付けのタイプが配列型且つメンバー変数である場合
                else:
                    # HCL組み立て(メンバー変数)
                    if len(member_vars_list) > 0 and hclFlag is False:
                        tmp_member_vars_list = []
                        # １．対象変数のメンバー変数を全て取得（引数：Module変数紐付け/MODULE_VARS_LINK_ID）
                        trg_member_vars_records = get_member_vars_ModuleVarsLinkID_for_hcl(wsDb, TFCLIConst, vars_link_id)
                        # MEMBER_VARS_IDのリスト（重複の削除）
                        member_vars_ids_array = list(set([m.get('MEMBER_VARS_ID') for m in member_vars_list]))

                        # ２．配列型の変数を配列にする
                        for member_vars_id in member_vars_ids_array:
                            # メンバー変数IDからタイプ情報を取得する
                            key = [m.get('CHILD_MEMBER_VARS_ID') for m in trg_member_vars_records].index(member_vars_id)
                            type_info = get_type_info(wsDb, TFCLIConst, trg_member_vars_records[key]["CHILD_VARS_TYPE_ID"])

                            # メンバー変数対象でない配列型のみ配列型に形成する
                            if type_info["MEMBER_VARS_FLAG"] == '0' and type_info["ASSIGN_SEQ_FLAG"] == '1' and type_info["ENCODE_FLAG"] == '1':
                                tmp_list = {}
                                # 代入順序をキーインデックスにして具体値をtemp_aryに収める
                                for member_vars_data in member_vars_list:
                                    if member_vars_id == member_vars_data["MEMBER_VARS_ID"]:
                                        tmp_list[member_vars_data["ASSIGN_SEQ"]] = member_vars_data["VARS_ENTRY"]
                                # 並べ替え
                                tmp_list2 = dict(sorted(tmp_list.items()))
                                tmp_arr = list(tmp_list2.values())
                                sensitive_flag = False
                                if "SENSITIVE_FLAG" in trg_member_vars_records[key]:
                                    sensitive_flag = trg_member_vars_records[key]["SENSITIVE_FLAG"]
                                tmp_member_vars_list.append({
                                    "MEMBER_VARS": member_vars_id,
                                    "SENSITIVE_FLAG": sensitive_flag,
                                    "VARS_ENTRY": tmp_arr,
                                    "VARS_ASSIGN_FLAG": trg_member_vars_records[key]["VARS_ASSIGN_FLAG"]
                                })
                            else:
                                key = [m.get('MEMBER_VARS_ID') for m in member_vars_list].index(member_vars_id)
                                tmp_member_vars_list.append({
                                    "MEMBER_VARS": member_vars_id,
                                    "SENSITIVE_FLAG": member_vars_list[key]["SENSITIVE_FLAG"],
                                    "VARS_ENTRY": member_vars_list[key]["VARS_ENTRY"],
                                    "VARS_ASSIGN_FLAG": member_vars_list[key]["VARS_ASSIGN_FLAG"]
                                })

                        # MEMBER_VARS_LISTの中身を入れ替える
                        member_vars_list = tmp_member_vars_list

                        # ３．代入値管理で取得した値を置き換え
                        for member_vars_data in member_vars_list:
                            for trg_member_vars_record in trg_member_vars_records:
                                if member_vars_data["MEMBER_VARS"] == trg_member_vars_record["CHILD_MEMBER_VARS_ID"]:
                                    trg_member_vars_record["CHILD_MEMBER_VARS_VALUE"] = member_vars_data["VARS_ENTRY"]
                                    trg_member_vars_record["VARS_ENTRY_FLAG"] = '1'
                                    trg_member_vars_record["VARS_ASSIGN_FLAG"] = member_vars_data["VARS_ASSIGN_FLAG"]

                            # sensitive設定をチェック
                            # 対象代入値に一つでもsensitive設定があればseneitiveはON
                            if sensitiveFlag is False and member_vars_data["SENSITIVE_FLAG"] == '1':
                                sensitiveFlag = True

                        # ４．置換する値がなかった場合、エラーとする
                        err_id_list = []
                        for trg_member_vars_record in trg_member_vars_records:
                            if trg_member_vars_record["VARS_ENTRY_FLAG"] == '0' and trg_member_vars_record["VARS_ASSIGN_FLAG"] == '1':
                                err_id_list.append(trg_member_vars_record["CHILD_MEMBER_VARS_ID"])

                        if len(err_id_list) > 0:
                            ids_string = json.dumps(err_id_list)
                            # error_logにメッセージを追記
                            # メンバー変数の取得に失敗しました。ID:[]
                            g.applogger.info(g.appmsg.get_log_message("BKY-52009", [ids_string]))

                        # ５．取得したデータから配列を形成
                        trg_member_vars_arr = generate_member_vars_array_for_hcl(wsDb, TFCLIConst, trg_member_vars_records)
                        # ６．HCLに変換
                        var_value = encode_hcl(trg_member_vars_arr)
                        hclFlag = True

                # 変数のkey&valueをキャッシュ
                var_kv_str_row = make_kvs_str_row(var_key, var_value, vars_type_id)
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
