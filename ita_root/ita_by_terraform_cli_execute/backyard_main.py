# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.2 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.2
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import subprocess
import time
import re
import os
from datetime import datetime

from flask import g
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.util import get_timestamp
from common_libs.ci.util import log_err

from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
from libs import functions as func


def backyard_main(organization_id, workspace_id):
    g.applogger.debug(g.appmsg.get_log_message("BKY-00001"))

    retBool = main_logic(organization_id, workspace_id)
    if retBool is True:
        # 正常終了
        g.applogger.debug(g.appmsg.get_log_message("BKY-00002"))
    else:
        # エラーが一つでもある
        g.applogger.debug(g.appmsg.get_log_message("BKY-00003"))


def main_logic(organization_id, workspace_id):
    # db instance
    wsDb = DBConnectWs(workspace_id)  # noqa: F405

    # 準備中/実行中の作業インスタンスに関して、実行プロセスが存在しているかの存在確認
    if child_process_exist_check(wsDb, organization_id, workspace_id) is False:
        g.applogger.debug(g.appmsg.get_log_message("MSG-10059"))
        return False

    # 実行中インスタンスのワークスペースIDをキャッシュ
    records = get_running_process(wsDb)
    executed_worksapce_id_list = []
    for record in records:
        worksapce_id = record['I_WORKSPACE_ID']

        if worksapce_id in executed_worksapce_id_list:
            continue
        executed_worksapce_id_list.append(worksapce_id)

    # 未実行（実行待ち）の作業を実行
    retBool = run_unexecuted(wsDb, organization_id, workspace_id, executed_worksapce_id_list)
    if retBool is False:
        return False

    return True


def child_process_exist_check(wsDb: DBConnectWs, organization_id, workspace_id):
    """
    実行中の子プロの起動確認

    Returns:
        bool
    """
    # psコマンドでbackyard_child_init.pyの起動プロセスリストを作成
    # psコマンドがマレに起動プロセスリストを取りこぼすことがあるので3回分を作成
    # command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no]

    child_process_1 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_2 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_3 = child_process_exist_check_ps()

    records = get_running_process(wsDb)
    for rec in records:
        tf_workspace_id = rec["I_WORKSPACE_ID"]
        execution_no = rec["EXECUTION_NO"]

        # 子プロ起動確認
        is_running = False

        # command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, tf_workspace_id, execution_no]
        command_args = "{} {} {} {} {}".format('backyard/backyard_child_init.py', g.ORGANIZATION_ID, g.WORKSPACE_ID, tf_workspace_id, execution_no)  # noqa: E501

        child_process_arr = child_process_1.split('\n')
        for r_child_process in child_process_arr:
            if re.search(command_args, r_child_process) is not None:
                is_running = True

        if is_running is False:
            child_process_arr = child_process_2.split('\n')
            for r_child_process in child_process_arr:
                if re.search(command_args, r_child_process) is not None:
                    is_running = True

        if is_running is False:
            child_process_arr = child_process_3.split('\n')
            for r_child_process in child_process_arr:
                if re.search(command_args, r_child_process) is not None:
                    is_running = True

        # DBのステータスが実行中なのに、子プロセスが存在しない
        if is_running is False:
            g.applogger.info(g.appmsg.get_log_message("MSG-10056", [execution_no, tf_workspace_id]))

            # 情報を再取得して、想定外エラーにする
            result = func.get_execution_process_info(wsDb, TFCLIConst, execution_no)
            if result[0] is False:
                log_err(result[1])
                return False
            execute_data = result[1]

            # 実行中か再確認
            status_id_list = [TFCLIConst.STATUS_PREPARE, TFCLIConst.STATUS_PROCESSING, TFCLIConst.STATUS_PROCESS_DELAYED]
            if execute_data["STATUS_ID"] in status_id_list:
                # 想定外エラーに更新
                wsDb.db_transaction_start()
                time_stamp = get_timestamp()
                update_data = {
                    "EXECUTION_NO": execution_no,
                    "STATUS_ID": TFCLIConst.STATUS_EXCEPTION,
                    "TIME_START": time_stamp,
                    "TIME_END": time_stamp,
                }
                result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data)
                if result is True:
                    wsDb.db_commit()
                    g.applogger.debug(g.appmsg.get_log_message("MSG-10060", [execution_no, tf_workspace_id]))

    return True


def child_process_exist_check_ps():
    """
    実行中の子プロのpsコマンド取得結果

    Returns:
        stdout row
    """
    # ps -efw | grep backyard/backyard_child_init.py | grep -v grep
    cp1 = subprocess.run(
        ["ps", "-efw"],
        capture_output=True,
        text=True
    )
    if cp1.returncode != 0 and cp1.stderr:
        cp1.check_returncode()

    cp2 = subprocess.run(
        ["grep", "backyard/backyard_child_init.py"],
        capture_output=True,
        text=True,
        input=cp1.stdout
    )
    if cp2.returncode != 0 and cp2.stderr:
        cp2.check_returncode()

    cp3 = subprocess.run(
        ["grep", "-v", "grep"],
        capture_output=True,
        text=True,
        input=cp2.stdout
    )

    if cp3.returncode == 0:
        # 検索結果あり
        return cp3.stdout
    elif cp3.returncode == 1 and not cp3.stderr:
        # 検索結果なし（0行）
        return ""
    else:
        # 例外を起こす
        cp3.check_returncode()


def get_running_process(wsDb):
    """
    実行中の作業データを取得

    Returns:
        records
    """
    status_id_list = [TFCLIConst.STATUS_PREPARE, TFCLIConst.STATUS_PROCESSING, TFCLIConst.STATUS_PROCESS_DELAYED]
    prepared_list = list(map(lambda a: "%s", status_id_list))

    condition = 'WHERE `DISUSE_FLAG`=0 AND `STATUS_ID` in ({})'.format(','.join(prepared_list))
    records = wsDb.table_select(TFCLIConst.T_EXEC_STS_INST, condition, status_id_list)

    return records


def get_now_datetime(format='%Y/%m/%d %H:%M:%S', type='str'):
    dt = datetime.now().strftime(format)
    if type == 'str':
        return '{}'.format(dt)
    else:
        return dt


def run_unexecuted(wsDb: DBConnectWs, organization_id, workspace_id, executed_worksapce_id_list):
    """
    未実行（実行待ち）の作業を実行

    Returns:
        bool
        err_msg
    """
    condition = """WHERE `DISUSE_FLAG`=0 AND (
        ( `TIME_BOOK` IS NULL AND `STATUS_ID` = %s ) OR
        ( `TIME_BOOK` <= %s AND `STATUS_ID` = %s )
    ) ORDER BY TIME_REGISTER ASC"""
    records = wsDb.table_select(TFCLIConst.T_EXEC_STS_INST, condition, [TFCLIConst.STATUS_NOT_YET, get_now_datetime(), TFCLIConst.STATUS_RESERVE])

    # 処理対象レコードが0件の場合は処理終了
    if len(records) == 0:
        g.applogger.debug(g.appmsg.get_log_message("MSG-10749"))
        return True

    # 実行順リストを作成する
    # ・並び替え（workspace混在・同一ワークスペースを含む）
    execution_info_datalist = {}
    execution_order_list = []

    for rec in records:
        execution_no = rec["EXECUTION_NO"]

        # 予約時間or最終更新日+ソート用カラム+作業番号（判別用）でリスト生成
        id = str(rec["LAST_UPDATE_TIMESTAMP"]) + "_" + str(rec["TIME_REGISTER"]) + "_" + execution_no
        if rec["TIME_BOOK"]:
            if rec["LAST_UPDATE_TIMESTAMP"] < rec["TIME_BOOK"]:
                id = str(rec["TIME_BOOK"]) + "_" + str(rec["TIME_REGISTER"]) + "_" + execution_no
        execution_order_list.append(id)
        execution_info_datalist[id] = rec
    # ソート
    execution_order_list.sort()

    # 現在の実行数
    num_of_run_instance = 0
    # 並列実行数の上限
    num_of_parallel_exec = 100

    # 処理実行順に対象作業インスタンスを実行
    is_fail = False  # 一つでも失敗した
    for execution_order in execution_order_list:
        execute_data = execution_info_datalist[execution_order]
        execution_no = execute_data['EXECUTION_NO']
        tf_workspace_id = execute_data['I_WORKSPACE_ID']

        # 既に実行に回されたワークスペースは実行しない（次回のサービス実行まで待つ）
        if tf_workspace_id in executed_worksapce_id_list:
            continue

        # 並列実行数判定
        if num_of_run_instance >= num_of_parallel_exec:
            g.applogger.info(g.appmsg.get_log_message("BKY-10001"))
            return False
        num_of_run_instance = num_of_run_instance + 1

        # ワークスペースを配列にキャッシュ
        executed_worksapce_id_list.append(tf_workspace_id)

        # データを取り直して、作業実行
        result = run_child_process(wsDb, execute_data, organization_id, workspace_id)
        if result[0] is False:
            # 準備中にエラーが発生
            g.applogger.error(result[1])
            is_fail = True
            # 処理対象の作業インスタンスのステータスを想定外エラーに設定
            wsDb.db_transaction_start()
            time_stamp = get_timestamp()
            update_data = {
                "EXECUTION_NO": execution_no,
                "STATUS_ID": TFCLIConst.STATUS_EXCEPTION,
                "TIME_START": time_stamp,
                "TIME_END": time_stamp,
            }
            result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data)
            if result is True:
                wsDb.db_commit()
                g.applogger.debug(g.appmsg.get_log_message("MSG-10060", [execution_no, tf_workspace_id]))

    if is_fail is True:
        return False
    else:
        return True


def run_child_process(wsDb, execute_data, organization_id, workspace_id):
    """
    作業実行するための子プロセスの準備・実行

    Returns:
        bool
        err_msg
    """
    execution_no = execute_data['EXECUTION_NO']
    tf_workspace_id = execute_data['I_WORKSPACE_ID']
    # tf_workspace_name = execute_data['I_WORKSPACE_NAME']

    # 処理対象の作業インスタンス情報取得(再取得)
    retBool, result = func.get_execution_process_info(wsDb, TFCLIConst, execution_no)
    if retBool is False:
        return False, result
    execute_data = result

    # 未実行状態かを判定
    status_id = execute_data["STATUS_ID"]
    if status_id != TFCLIConst.STATUS_NOT_YET and status_id != TFCLIConst.STATUS_RESERVE:
        return False, g.appmsg.get_log_message("BKY-10002", [execution_no])

    # 処理対象の作業インスタンスのステータスを準備中に設定
    wsDb.db_transaction_start()
    update_data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": TFCLIConst.STATUS_PREPARE,
        "TIME_START": get_timestamp()
    }
    result, execute_data = func.update_execution_record(wsDb, TFCLIConst, update_data)
    if result is True:
        wsDb.db_commit()
        g.applogger.debug(g.appmsg.get_log_message("MSG-10730", [execution_no]))

    # ワークスペース毎のディレクトリを準備
    base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
    workspace_work_dir = base_dir + TFCLIConst.DIR_WORK + "/{}/work".format(tf_workspace_id)
    os.makedirs(workspace_work_dir, exist_ok=True)
    os.chmod(workspace_work_dir, 0o777)

    # （前回実行した）ファイルを削除しておく
    # ・緊急停止ファイル
    emergency_stop_file_path = "{}/{}".format(workspace_work_dir, TFCLIConst.FILE_EMERGENCY_STOP)
    rm_file_list = [emergency_stop_file_path]
    for rm_file in rm_file_list:
        if os.path.isfile(rm_file):
            os.remove(rm_file)

    # 子プロセスにして、実行
    g.applogger.debug(g.appmsg.get_log_message("MSG-10745", [execution_no, tf_workspace_id]))

    command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, tf_workspace_id, execution_no]
    # print(" ".join(command))
    cp = subprocess.Popen(command)  # noqa: F841

    return True,
