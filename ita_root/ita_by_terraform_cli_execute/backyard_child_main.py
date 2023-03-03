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

from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.exception import AppException, ValidationException
from common_libs.common.util import get_timestamp, file_encode, ky_encrypt
from common_libs.loadtable import load_table

from common_libs.driver.functions import operation_LAST_EXECUTE_TIMESTAMP_update

from common_libs.terraform_driver.cli.Const import Const
from libs import common_functions as cm


# 定数をロード
const = Const()
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

input_zip_file_name = ""  # 投入ファイルのパス
result_zip_file_name = ""  # 結果ファイルのパス


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
    g.applogger.debug(g.appmsg.get_log_message("MSG-10720", [execution_no]))

    # db instance
    wsDb = DBConnectWs(workspace_id)  # noqa: F405

    try:
        result = main_logic(wsDb)
        if result[0] is True:
            # 正常終了
            g.applogger.debug(g.appmsg.get_log_message("MSG-10721", [tf_workspace_id, execution_no]))
        else:
            g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [tf_workspace_id, execution_no]))
    except AppException as e:
        update_status_error(wsDb)

        g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [tf_workspace_id, execution_no]))

        raise e
    except Exception as e:
        update_status_error(wsDb)

        g.applogger.debug(g.appmsg.get_log_message("MSG-10722", [tf_workspace_id, execution_no]))

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
    # 処理対象の作業インスタンス情報取得
    retBool, execute_data = cm.get_execution_process_info(wsDb, const, execution_no)
    if retBool is False:
        err_log = g.appmsg.get_log_message(execute_data, [execution_no])
        raise Exception(err_log)

    # 処理対象の作業インスタンス実行
    retBool, execute_data = instance_execution(wsDb, execute_data)

    # 実行結果から、処理対象の作業インスタンスのステータス更新
    if retBool is False:
        # ステータスを想定外エラーに設定
        update_status_error(wsDb)

    # ステータスが実行中以外は終了（緊急停止）
    if execute_data["STATUS_ID"] != const.STATUS_PROCESSING:
        return True,

    # [処理]処理対象インスタンス 作業確認の終了(作業No.:{})
    g.applogger.debug(g.appmsg.get_log_message("MSG-10738", [execution_no]))

    return True,


def instance_execution(wsDb: DBConnectWs, execute_data):
    global base_dir
    global workspace_work_dir
    global exe_lock_file_path
    global result_file_path
    global default_tfvars_file_path
    global secure_tfvars_file_path
    global emergency_stop_file_path

    module_matter_id_str_arr = []  # モジュール素材IDを格納する配列
    module_matter_arr = {}  # モジュール素材情報を格納する配列
    input_matter_arr = []  # 投入ファイルに必要なファイルリスト
    result_matter_arr = []  # 結果ファイルに必要なファイルリスト

    vars_set_flag = False  # 変数追加処理を行うかの判定
    vars_data_arr = []  # 対象の変数を格納する配列

    variable_tfvars = []  # terraform.tfvarsに書き込むkey=value
    secure_tfvars = []  # secure.tfvarsに書き込むkey=value
    secure_tfvars_flg = False  # secure.tfvarsが存在している

    # 作業実行データ
    # tf_workspace_name_org = execute_data['I_WORKSPACE_NAME']
    run_mode = execute_data['RUN_MODE']
    movement_id = execute_data['MOVEMENT_ID']
    operation_id = execute_data['OPERATION_ID']
    conductor_instance_no = execute_data["CONDUCTOR_INSTANCE_NO"]

    # [処理]処理対象インスタンス 作業実行開始(作業No.:{})
    g.applogger.debug(g.appmsg.get_log_message("MSG-10763", [execution_no]))

    # 代入値自動登録とパラメータシートからデータを抜く
    # 		該当のオペレーション、Movementのデータを代入値管理に登録
    # 一時的に呼ばないように
    # sub_value_auto_reg = SubValueAutoReg(wsDb, tf_workspace_id)
    # try:
    #     sub_value_auto_reg.get_data_from_parameter_sheet(operation_id, movement_id, execution_no)
    # except ValidationException as e:
    #     raise ValidationException(e)

    # 実行モードが「パラメータ確認」の場合は終了
    if run_mode == const.RUN_MODE_PARAM:
        wsDb.db_transaction_start()
        update_data = {
            "EXECUTION_NO": execution_no,
            "STATUS_ID": const.STATUS_COMPLETE,
            "TIME_END": get_timestamp(),
        }
        result = cm.update_execution_record(wsDb, const, update_data)
        if result[0] is True:
            wsDb.db_commit()
            g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no]))

        return True, execute_data

    # logファイルを生成
    base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
    log_dir = base_dir + const.DIR_EXECUTE + "/{}/out/".format(execution_no)

    error_log = log_dir + "/error.log"
    init_log = log_dir + "/init.log"
    plan_log = log_dir + "/plan.log"
    apply_log = log_dir + "/apply.log"

    os.makedirs(log_dir, exist_ok=True)
    os.chmod(log_dir, 0o777)

    # ディレクトリを準備
    workspace_work_dir = base_dir + const.DIR_WORK + "/{}/work".format(tf_workspace_id)  # CLI実行場所

    exe_lock_file_path = workspace_work_dir + "/.tf_exec_lock"  # ロックファイル
    result_file_path = workspace_work_dir + "/result.txt"  # 実行内容を記録したファイル

    default_tfvars_file_path = workspace_work_dir + "/terraform.tfvars"  # terraform.tfvars
    secure_tfvars_file_path = workspace_work_dir + "/secure.tfvars"  # secure.tfvars
    emergency_stop_file_path = workspace_work_dir + "/emergency_stop"  # 緊急停止ファイル

    if os.path.exists(workspace_work_dir) is False:
        return False, execute_data

    # 前回の実行ファイルの削除
    # destroy以外・・・tfファイルなど、stateファイル以外の全てを削除
    # destroy・・・・・結果ファイル・ロックファイルのみを削除（前回実行状態にする）
    rm_list = [exe_lock_file_path, result_file_path, emergency_stop_file_path]  # ロックファイル、結果ファイル、緊急停止ファイル

    if run_mode != const.RUN_MODE_DESTROY:
        cmd = '/bin/rm -fr *.tf *.tfvars {}'.format(" ".join(rm_list))
        subprocess.run(cmd, cwd=workspace_work_dir, shell=True)
    else:
        cmd = '/bin/rm -fr {}'.format(" ".join(rm_list))
        subprocess.run(cmd, cwd=workspace_work_dir, shell=True)

    # 緊急停止のチェック
    ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data, result_matter_arr)
    if ret_emgy is False:
        True, execute_data

    # WORKSPACE_IDから対象Workspace(B_TERRAFORM_CLI_WORKSPACES)のレコードを取得して、workspace名をキャッシュ
    # condition = """WHERE `DISUSE_FLAG`=0 AND WORKSPACE_ID = %s"""
    # records = wsDb.table_select(const.T_WORKSPACE, condition, [tf_workspace_id])
    # if len(records) == 0:
    #     False, execute_data
    # tf_workspace_name = records[0]['WORKSPACE_NAME']

    if run_mode != const.RUN_MODE_DESTROY:
        # 投入オペレーションの最終実施日を更新する
        result = operation_LAST_EXECUTE_TIMESTAMP_update(wsDb, operation_id)
        if result[0] is True:
            g.applogger.debug(g.appmsg.get_log_message("BKY-10003", [execution_no]))

        # MOVEMENT_IDからMovement詳細のレコードを取得
        condition = "WHERE DISUSE_FLAG = '0' AND MOVEMENT_ID = %s"
        records = wsDb.table_select(const.T_MOVEMENT_MODULE, condition, [movement_id])

        for record in records:
            module_matter_id_str_arr.append("'" + record['MODULE_MATTER_ID'] + "'")

        # Moduleのファイル名を取得
        module_matter_id_str_arr_concat = ','.join(module_matter_id_str_arr)
        condition = "WHERE DISUSE_FLAG = '0' AND MODULE_MATTER_ID in ({}) ".format(module_matter_id_str_arr_concat)
        records = wsDb.table_select(const.T_MODULE, condition, [])

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
            matter_file_path = "{}{}/{}/{}/".format(base_dir, const.DIR_MODULE, module_matter_id, val["matter_file_name"])
            cmd = '/bin/cp -rfp {} {}/.'.format(matter_file_path, workspace_work_dir)

            # 投入ファイルのリストに追加
            input_matter_arr.append(workspace_work_dir + "/" + val["matter_file_name"])

        # operation_noとmovement_idから変数名と代入値を取得
        vars_set_flag = False
        # 処理
        vars_set_flag = True

        # Movementに紐づく代入値がある場合、代入値(Variables)登録処理を実行
        if vars_set_flag is True:
            # 処理
            sensitiveFlag = False
            ary_vars_data = {}
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
        if os.path.exists(secure_tfvars_file_path) is True:
            secure_tfvars_flg = True

    # 投入ファイル:ZIPファイルを作成する(ITAダウンロード用)
    MakeInputZipFile(input_matter_arr)

    # ステータスを実行中に更新
    wsDb.db_transaction_start()
    execute_data["STATUS_ID"] = const.STATUS_PROCESSING
    if input_zip_file_name:
        execute_data["FILE_INPUT"] = input_zip_file_name
    # ログリストを保存
    logfilelist_json = ["init.log", "plan.log"]
    if const.RUN_MODE_APPLY or const.RUN_MODE_DESTROY:
        logfilelist_json.append("apply.log")
    execute_data["LOGFILELIST_JSON"] = logfilelist_json
    execute_data["MULTIPLELOG_MODE"] = 1
    result = cm.update_execution_record(wsDb, const, execute_data)
    if result[0] is True:
        wsDb.db_transaction_start()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no]))

    # 緊急停止のチェック
    ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data, result_matter_arr)
    if ret_emgy is False:
        True, execute_data

    # 準備で異常がなければ、terraformコマンドの実行にうつる
    g.applogger.debug(g.appmsg.get_log_message("MSG-10761", [execution_no]))
    # ファイルによる実行中の排他ロック


    # 更新するステータスの初期値
    update_status = const.STATUS_COMPLETE

    # initコマンド
    command_options = ["-no-color"]
    command = "terraform init " + " ".join(command_options)
    ret_status, execute_data = ExecCommand(wsDb, execute_data, command, init_log, error_log, True)
    if ret_status != const.STATUS_COMPLETE:
        update_status = ret_status
    result_matter_arr.append(error_log)
    result_matter_arr.append(workspace_work_dir + "/.terraform.lock.hcl")
    result_matter_arr.append(init_log)

    if ret_status != const.STATUS_COMPLETE:
        # 緊急停止のチェック
        ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data, result_matter_arr)
        if ret_emgy is False:
            True, execute_data

        # planコマンド
        command_options = ["-no-color", "-input=false"]
        if secure_tfvars_flg is True:
            command_options.append("-var-file secure.tfvars")
        if run_mode != const.RUN_MODE_DESTROY:
            command = "terraform plan " + " ".join(command_options)
        else:
            command = "terraform plan -destroy " + " ".join(command_options)

        ret_status, execute_data = ExecCommand(wsDb, execute_data, command, plan_log, error_log)
        if ret_status != const.STATUS_COMPLETE:
            update_status = ret_status
        result_matter_arr.append(plan_log)

    if ret_status != const.STATUS_COMPLETE:
        # 緊急停止のチェック
        ret_emgy, execute_data = IsEmergencyStop(wsDb, execute_data, result_matter_arr)
        if ret_emgy is False:
            True, execute_data

        # applyコマンド
        command_options = ["-no-color"]
        if secure_tfvars_flg is True:
            command_options.append("-var-file secure.tfvars")
        if run_mode == const.RUN_MODE_APPLY:
            command = "terraform apply -auto-approve " + " ".join(command_options)
        # destroyコマンド
        elif run_mode == const.RUN_MODE_DESTROY:
            command = "terraform destroy -auto-approve " + " ".join(command_options)

        ret_status, execute_data = ExecCommand(wsDb, execute_data, command, apply_log, error_log)
        if ret_status != const.STATUS_COMPLETE:
            update_status = ret_status
        result_matter_arr.append(apply_log)

        # stateファイルの暗号化
        SaveEncryptStateFile(execute_data)

    # 結果ファイルの作成
    MakeResultZipFile(result_matter_arr)

    # Conductorからの実行時、output出力結果を格納する


    # 最終ステータスを更新
    wsDb.db_transaction_start()
    execute_data["STATUS_ID"] = update_status
    execute_data["TIME_END"] = get_timestamp()
    if result_zip_file_name:
        execute_data["FILE_RESULT"] = result_zip_file_name
    result = cm.update_execution_record(wsDb, const, execute_data)
    if result[0] is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no]))

    return True, execute_data


def update_status_error(wsDb: DBConnectWs):
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
        "STATUS_ID": const.STATUS_EXCEPTION,
        "TIME_END": get_timestamp(),
    }
    if input_zip_file_name:
        update_data["FILE_INPUT"] = input_zip_file_name
    if result_zip_file_name:
        update_data["FILE_RESULT"] = result_zip_file_name
    result = cm.update_execution_record(wsDb, const, update_data)
    if result[0] is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10060", [execution_no, tf_workspace_id]))


# コマンド実行
def ExecCommand(wsDb, execute_data, command, cmd_log, error_log, init_flg=False):
    time_limit = execute_data['I_TIME_LIMIT']  # 遅延タイマ
    current_status = execute_data['STATUS_ID']

    # すでに結果ファイルが存在していた（重複処理が走らなければ、ありえない)
    if init_flg is True and os.path.exists(result_file_path):
        return const.STATUS_EXCEPTION, execute_data

    try:
        proc = subprocess.Popen(command, cwd=workspace_work_dir, shell=True, stdout=cmd_log, stderr=error_log)

        # 結果ファイルにコマンドとPIDを書き込む
        str_body = command + " : PID=" + proc.pid + "\n"
        if init_flg is True:
            with open(result_file_path, 'X', encoding='UTF-8') as f:
                f.write(str_body)
        else:
            with open(result_file_path, 'a', encoding='UTF-8') as f:
                f.write(str_body)

        # ステータスが実行中(3)、かつ制限時間が設定されている場合のみ遅延判定する
        delay_flag = False
        if current_status == const.STATUS_PROCESSING and time_limit:
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
                        "STATUS_ID": const.STATUS_PROCESS_DELAYED,
                    }
                    result = cm.update_execution_record(wsDb, const, update_data)
                    if result[0] is True:
                        wsDb.db_commit()
                        g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no]))

                # プロセスが実行中はNoneを返す
                if proc.poll() is not None:
                    # 終了判定
                    break
        else:
            # 遅延判定しない場合は、終了するまで待つ
            proc.wait()

        exit_status = proc.returncode
        if exit_status == 0:
            # 正常終了した場合
            update_status = const.STATUS_COMPLETE
            str_body = "COMPLETED(0)\n"
        else:
            # 異常終了した場合
            update_status = const.STATUS_FAILURE
            str_body = "PREVENTED({})\n".format(exit_status)

        # 結果を書き込む
        with open(result_file_path, 'a', encoding='UTF-8') as f:
            f.write(str_body)

        return update_status, execute_data
    except AppException as e:
        raise e
    except Exception as e:
        g.applogger.error(e)
        return const.STATUS_EXCEPTION, execute_data


# terraformのstateファイルを暗号化
def SaveEncryptStateFile(execute_data):
    # 一時利用ディレクトリの存在をチェックし、なければ作成
    os.makedirs(base_dir + const.DIR_TEMP, exist_ok=True)
    os.chmod(base_dir + const.DIR_TEMP, 0o777)

    # 一時格納先ディレクトリ名を定義
    tgt_execution_dir = base_dir + const.DIR_TEMP + "/" + execution_no

    # 作業実行Noのディレクトリを作成
    os.makedirs(tgt_execution_dir, exist_ok=True)
    os.chmod(tgt_execution_dir, 0o777)

    # 1:tfstate
    org_state_file = workspace_work_dir + "/terraform.tfstate"
    encrypt_state_file = tgt_execution_dir + "/terraform.tfstate"

    if os.path.isfile(org_state_file) is False:
        return True
    else:
        # stateファイルの中身を取得
        str_body = ""
        with open(org_state_file, 'r', encoding='UTF-8') as f:
            str_body = f.read()

    # ファイルに中身を新規書き込み
    str_encrypt_body = ky_encrypt(str_body)
    with open(encrypt_state_file, 'x', encoding='UTF-8') as f:
        f.write(str_encrypt_body)

    # 2:tfstate.backup
    org_state_file = workspace_work_dir + "/terraform.tfstate.backup"
    encrypt_state_file = tgt_execution_dir + "/terraform.tfstate.backup"

    if os.path.isfile(org_state_file) is False:
        return True
    else:
        # stateファイルの中身を取得
        str_body = ""
        with open(org_state_file, 'r', encoding='UTF-8') as f:
            str_body = f.read()

    # ファイルに中身を新規書き込み
    str_encrypt_body = ky_encrypt(str_body)
    with open(encrypt_state_file, 'x', encoding='UTF-8') as f:
        f.write(str_encrypt_body)

    return True


# tfvarsファイルに書き込む行データを作成
def makeKVStrRow(key, value, type_id):
    str_row = ''

    if (type_id == '' or type_id == '1' or type_id == '18') or not value:
        str_row = '{} = "{}"'.format(key, value)
    else:
        str_row = '{} = {}'.format(key, value)

    return str_row


# 投入zipファイルを作成
def MakeInputZipFile(input_matter_arr):
    global input_zip_file_name

    # zipファイルを格納するディレクトリ
    zip_path = base_dir + const.DIR_POPLATED_DATA + "/" + execution_no
    os.makedirs(zip_path, exist_ok=True)
    os.chmod(zip_path, 0o777)

    # ファイル名の定義
    input_zip_file_name = 'InputData_' + execution_no + '.zip'
    # 圧縮するファイル名のリスト
    str_input_matter = " ".join(input_matter_arr)

    # ZIPファイルを作成
    command = ["zip", "-j", zip_path + "/" + input_zip_file_name, str_input_matter]
    cp = subprocess.run(command, capture_output=True, text=True)
    if cp.returncode != 0 or cp.stderr:
        # zipファイルの作成に失敗しました
        g.applogger.error(g.appmsg.get_log_message("BKY-00004", ["createTmpZipFile", ""]))
        return False

    return True


# 結果zipファイルを作成
def MakeResultZipFile(result_matter_arr):
    global result_zip_file_name

    # zipファイルを格納するディレクトリ
    zip_path = base_dir + const.DIR_RESILT_DATA + "/" + execution_no
    os.makedirs(zip_path, exist_ok=True)
    os.chmod(zip_path, 0o777)

    # ファイル名の定義
    result_zip_file_name = 'InputData_' + execution_no + '.zip'
    # 圧縮するファイル名のリスト
    str_result_matter = " ".join(result_matter_arr)

    # ZIPファイルを作成
    command = ["zip", "-j", zip_path + "/" + result_zip_file_name, str_result_matter]
    cp = subprocess.run(command, capture_output=True, text=True)
    if cp.returncode != 0 and cp.stderr:
        # zipファイルの作成に失敗しました
        g.applogger.error(g.appmsg.get_log_message("BKY-00004", ["createTmpZipFile", ""]))

    return True


# 緊急停止の処理
def IsEmergencyStop(wsDb: DBConnectWs, execute_data, result_matter_arr):
    # 緊急停止ファイルの存在有無
    if os.path.exists(emergency_stop_file_path) is False:
        return True, execute_data

    # 緊急停止を検知しました
    g.applogger.debug(g.appmsg.get_log_message("MSG-10763", [execution_no]))

    # 結果ファイルがあれば作る
    if len(result_matter_arr) > 0:
        MakeResultZipFile(result_matter_arr)

    # ステータスを緊急停止に更新
    wsDb.db_transaction_start()
    execute_data["STATUS_ID"] = const.STATUS_SCRAM
    execute_data["TIME_END"] = get_timestamp()
    if input_zip_file_name:
        execute_data["FILE_INPUT"] = input_zip_file_name
    if result_zip_file_name:
        execute_data["FILE_RESULT"] = result_zip_file_name

    result = cm.update_execution_record(wsDb, const, execute_data)
    if result[0] is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10735", [execution_no]))

    return False, execute_data


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
