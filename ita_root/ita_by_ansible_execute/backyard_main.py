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

import subprocess
import time
import re
import os

from flask import g
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.util import get_timestamp
from common_libs.ci.util import log_err
from common_libs.ansible_driver.classes.AnsrConstClass import AnscConst
from common_libs.ansible_driver.classes.controll_ansible_agent import DockerMode, KubernetesMode
from libs import common_functions as cm

# ansible共通の定数をロード
ansc_const = AnscConst()


def backyard_main(organization_id, workspace_id):
    """
    [ita_by_ansible_execute]
    main logicのラッパー
    called 実行君
    """
    g.applogger.info(g.appmsg.get_log_message("BKY-00001"))

    # db instance
    wsDb = DBConnectWs(g.get('WORKSPACE_ID'))  # noqa: F405

    retBool = main_logic(organization_id, workspace_id, wsDb)
    if retBool is True:
        # 正常終了
        g.applogger.info(g.appmsg.get_log_message("BKY-00002"))
    else:
        g.applogger.info(g.appmsg.get_log_message("BKY-00003"))


def main_logic(organization_id, workspace_id, wsDb):
    """
    main logic
    """
    container_base = os.getenv('CONTAINER_BASE')
    if container_base == 'docker':
        ansibleAg = DockerMode()
    else:
        ansibleAg = KubernetesMode()

    # 実行中のコンテナの状態確認
    if child_process_exist_check(wsDb, ansibleAg) is False:
        g.applogger.debug(g.appmsg.get_log_message("MSG-10059"))
        return False

    # 実行中の作業の数を取得
    num_of_run_instance = len(get_running_process(wsDb))

    # 未実行（実行待ち）の作業を実行
    result = run_unexecuted(wsDb, ansibleAg, num_of_run_instance, organization_id, workspace_id)
    if result[0] is False:
        g.applogger.error(result[1])
        return False

    return True


def child_process_exist_check(wsDb: DBConnectWs, ansibleAg):
    """
    実行中の子プロの起動確認
    
    Returns:
        bool
    """
    # psコマンドでbackyard_child_init.pyの起動プロセスリストを作成
    # psコマンドがマレに起動プロセスリストを取りこぼすことがあるので3回分を作成
    # command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no, driver_id]

    child_process_1 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_2 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_3 = child_process_exist_check_ps()

    records = get_running_process(wsDb)
    for rec in records:
        driver_id = rec["DRIVER_ID"]
        driver_name = rec["DRIVER_NAME"]
        execution_no = rec["EXECUTION_NO"]

        # 子プロ起動確認
        is_running = False
        # command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no, driver_id]
        command_args = "{} {} {} {} {}".format('backyard/backyard_child_init.py', g.ORGANIZATION_ID, g.WORKSPACE_ID, execution_no, driver_id)

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
            log_err(g.appmsg.get_log_message("MSG-10056", [driver_name, execution_no]))

            # 情報を再取得して、想定外エラーにする
            result = cm.get_execution_process_info(wsDb, execution_no)
            if result[0] is False:
                log_err(g.appmsg.get_log_message(result[1], [execution_no]))
                return False
            execute_data = result[1]

            # 実行中か再確認
            status_id_list = [ansc_const.PREPARE, ansc_const.PROCESSING, ansc_const.PROCESS_DELAYED]
            if execute_data["STATUS_ID"] in status_id_list:
                # 更新
                wsDb.db_transaction_start()
                time_stamp = get_timestamp()
                data = {
                    "EXECUTION_NO": execution_no,
                    "STATUS_ID": ansc_const.EXCEPTION,
                    "TIME_END": time_stamp,
                }
                if not execute_data["TIME_START"]:
                    data["TIME_START"] = time_stamp
                result = cm.update_execution_record(wsDb, data)
                if result[0] is True:
                    wsDb.db_commit()
                    g.applogger.debug(g.appmsg.get_log_message("MSG-10060", [driver_name, execution_no]))

            # コンテナが残っている場合に備えて掃除
            # ゴミ掃除に失敗しても処理は続ける
            result = ansibleAg.is_container_running(execution_no)
            if result[0] is True:
                result = ansibleAg.container_kill(execution_no)
                if result[0] is False:
                    log_err(g.appmsg.get_log_message("BKY-10007", [result[1], execution_no]))
            else:
                result = ansibleAg.container_clean(execution_no)
                if result[0] is False:
                    log_err(g.appmsg.get_log_message("BKY-10007", [result[1], execution_no]))

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
    status_id_list = [ansc_const.PREPARE, ansc_const.PROCESSING, ansc_const.PROCESS_DELAYED]
    prepared_list = list(map(lambda a: "%s", status_id_list))

    condition = 'WHERE `DISUSE_FLAG`=0 AND `STATUS_ID` in ({})'.format(','.join(prepared_list))
    records = wsDb.table_select('V_ANSC_EXEC_STS_INST', condition, status_id_list)

    return records


def run_unexecuted(wsDb: DBConnectWs, ansibleAg, num_of_run_instance, organization_id, workspace_id):
    """
    未実行（実行待ち）の作業を実行
    
    Returns:
        bool
        err_msg
    """
    condition = """WHERE `DISUSE_FLAG`=0 AND (
        ( `TIME_BOOK` IS NULL AND `STATUS_ID` = %s ) OR
        ( `TIME_BOOK` <= NOW(6) AND `STATUS_ID` = %s )
    ) ORDER BY TIME_REGISTER ASC"""
    records = wsDb.table_select('V_ANSC_EXEC_STS_INST', condition, [ansc_const.NOT_YET, ansc_const.RESERVE])

    # 処理対象レコードが0件の場合は処理終了
    if len(records) == 0:
        g.applogger.info(g.appmsg.get_log_message("MSG-10749"))
        return True,

    # 実行順リストを作成する
    execution_info_datalist = {}
    execution_order_list = []
    
    for rec in records:
        # print(rec)
        execution_no = rec["EXECUTION_NO"]

        # 予約時間or最終更新日+ソート用カラム+作業番号（判別用）でリスト生成
        id = str(rec["LAST_UPDATE_TIMESTAMP"]) + "-" + str(rec["TIME_REGISTER"]) + "-" + execution_no
        if rec["TIME_BOOK"]:
            if rec["LAST_UPDATE_TIMESTAMP"] < rec["TIME_BOOK"]:
                id = str(rec["TIME_BOOK"]) + "-" + str(rec["TIME_REGISTER"]) + "-" + execution_no
        execution_order_list.append(id)
        execution_info_datalist[id] = rec
    # ソート
    # print(execution_order_list)
    execution_order_list.sort()
    # print(execution_order_list)

    # ANSIBLEインタフェース情報
    retBool, result = cm.get_ansible_interface_info(wsDb)
    if retBool is False:
        return False, g.appmsg.get_log_message(result, [execution_no])
    ansible_interface_info = result
    # 並列実行数の上限
    num_of_parallel_exec = ansible_interface_info['ANSIBLE_NUM_PARALLEL_EXEC']

    # 処理実行順に対象作業インスタンスを実行
    for execution_order in execution_order_list:
        # 並列実行数判定
        if num_of_run_instance >= num_of_parallel_exec:
            return False, g.appmsg.get_log_message("BKY-10001")

        num_of_run_instance = num_of_run_instance + 1

        # データを取り出して、作業実行
        execute_data = execution_info_datalist[execution_order]
        result = run_child_process(wsDb, execute_data, organization_id, workspace_id)
        if result[0] is False:
            return False, result[1]

    return True,


def run_child_process(wsDb, execute_data, organization_id, workspace_id):
    """
    作業実行するための子プロセスの準備・実行
    
    Returns:
        bool
        err_msg
    """
    driver_id = execute_data["DRIVER_ID"]
    driver_name = execute_data["DRIVER_NAME"]
    execution_no = execute_data["EXECUTION_NO"]

    # 処理対象の作業インスタンス情報取得(再取得)
    retBool, result = cm.get_execution_process_info(wsDb, execution_no)
    if retBool is False:
        return False, g.appmsg.get_log_message(result, [execution_no])
    execute_data = result

    # 未実行状態で緊急停止出来るようにしているので
    # 未実行状態かを判定
    status_id = execute_data["STATUS_ID"]
    if status_id != ansc_const.NOT_YET and status_id != ansc_const.RESERVE:
        return False, g.appmsg.get_log_message("BKY-10002", [execution_no])

    # 処理対象の作業インスタンスのステータスを準備中に設定
    wsDb.db_transaction_start()
    data = {
        "EXECUTION_NO": execution_no,
        "STATUS_ID": ansc_const.PREPARE,
    }
    if not execute_data["TIME_START"]:
        data["TIME_START"] = get_timestamp()
    result = cm.update_execution_record(wsDb, data)
    if result[0] is True:
        wsDb.db_commit()

    # 子プロセスにして、実行
    g.applogger.debug(g.appmsg.get_log_message("MSG-10745", [driver_name, execution_no]))

    command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no, driver_id]
    # cp = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cp = subprocess.Popen(command)  # noqa: F841

    return True,
