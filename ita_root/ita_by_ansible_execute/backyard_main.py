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
import hashlib
import requests
import json
from datetime import datetime
from operator import itemgetter

from flask import g
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import get_timestamp, get_all_execution_limit, get_org_execution_limit
from common_libs.ci.util import log_err
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnslConstClass import AnslConst
from common_libs.ansible_driver.classes.AnspConstClass import AnspConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.functions.util import getAnsibleConst
from common_libs.ansible_driver.classes.controll_ansible_agent import DockerMode, KubernetesMode
from common_libs.common.exception import AppException
from libs import common_functions as cm

# ansible共通の定数をロード
ansc_const = AnscConst()


def backyard_main(common_db, organization_id=None, workspace_id=None):
    """
    [ita_by_ansible_execute]
    main logicのラッパー
    called 実行君
    """
    g.applogger.debug(g.appmsg.get_log_message("BKY-00001"))

    retBool = main_logic(common_db)
    if retBool is True:
        # 正常終了
        g.applogger.debug(g.appmsg.get_log_message("BKY-00002"))
    else:
        g.applogger.debug(g.appmsg.get_log_message("BKY-00003"))


def main_logic(common_db):
    """
    main logic
    """
    container_base = os.getenv('CONTAINER_BASE')
    if container_base == 'docker':
        ansibleAg = DockerMode()
    else:
        ansibleAg = KubernetesMode()

    try:
        # システム全体の同時実行数取得
        all_execution_limit = get_all_execution_limit("ita.system.ansible.execution_limit")
        # organization毎の同時実行数取得
        org_execution_limit = get_org_execution_limit("ita.organization.ansible.execution_limit")
        g.applogger.debug("START execute_control")
        execution_list, all_exec_count, org_exec_count_list, target_shema = execute_control(common_db, all_execution_limit, org_execution_limit)
        g.applogger.debug("END execute_control")

        # 実行中のコンテナの状態確認
        g.applogger.debug("START child_process_exist_check")
        if child_process_exist_check(common_db, target_shema, ansibleAg) is False:
            g.applogger.debug(g.appmsg.get_log_message("MSG-10059"))
            return False

        if len(execution_list) == 0:
            return True

        # 現在の実行数
        crr_count = 0
        for data in execution_list:
            g.applogger.debug("main_logic EXECUTION_NO=" + data["EXECUTION_NO"])
            crr_count += 1
            # 実行前に同時実行数比較
            if all_execution_limit != 0 and crr_count + int(all_exec_count) > int(all_execution_limit):
                return True
            if org_execution_limit[data["ORGANIZATION_ID"]] != 0 and crr_count + int(org_exec_count_list[data["ORGANIZATION_ID"]]) > int(org_execution_limit[data["ORGANIZATION_ID"]]):
                return True

            common_db.db_transaction_start()
            # 対象データのレコードロック
            sql = "SELECT * FROM `" + data["WORKSPACE_DB"] + "`.`" + data["VIEW_NAME"] + "` "
            sql += "WHERE EXECUTION_NO = %s "
            sql += "AND STATUS_ID IN (%s, %s, %s) "
            sql += "FOR UPDATE "
            records3 = common_db.sql_execute(sql, [data["EXECUTION_NO"], ansc_const.NOT_YET, ansc_const.PREPARE, ansc_const.RESERVE])

            if records3 is not None and len(records3) > 0:
                for rec3 in records3:
                    if rec3["WORKSPACE_ID"] == data["WORKSPACE_ID"]:
                        # レコード取得・レコードロック確保できたときは状態を更新し即時COMMIT
                        sql = "UPDATE `" + data["WORKSPACE_DB"] + "`.`" + data["VIEW_NAME"] + "` "
                        sql += "SET EXECUTE_HOST_NAME = %s "
                        sql += "WHERE EXECUTION_NO = %s"
                        common_db.sql_execute(sql, [os.uname()[1], data["EXECUTION_NO"]])
                        common_db.db_commit()
                    else:
                        # 最初からやり直し
                        common_db.db_rollback()
                        common_db.db_disconnect()
                        return True
            else:
                # 最初からやり直し
                common_db.db_rollback()
                common_db.db_disconnect()
                return True

            wsDb = DBConnectWs(data["WORKSPACE_ID"], data["ORGANIZATION_ID"])

            # 未実行（実行待ち）の作業を実行
            g.applogger.debug("START run_unexecuted")
            result = run_unexecuted(wsDb, data["EXECUTION_NO"], data["ORGANIZATION_ID"], data["WORKSPACE_ID"])
            g.applogger.debug("END run_unexecuted")
            if result[0] is False:
                g.applogger.error(result[1])
                wsDb.db_disconnect()
                return False

            wsDb.db_disconnect()

    except AppException as e:
        common_db.db_rollback()
        common_db.db_disconnect()
        raise AppException(e)

    return True


def execute_control(common_db, all_execution_limit, org_execution_limit):
    """
    同時実行数の制御

    Returns:
        bool
    """
    # 取得対象schemaの検索
    sql = "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS "
    sql += "WHERE TABLE_NAME IN ('V_ANSL_EXEC_STS_INST2','V_ANSP_EXEC_STS_INST2','V_ANSR_EXEC_STS_INST2') "

    records = common_db.sql_execute(sql, [])

    if records is not None and len(records) > 0:
        count = 0
        sql = ""
        for rec in records:
            table_schema = rec["TABLE_SCHEMA"]
            table_name = rec["TABLE_NAME"]
            count += 1
            if sql == "":
                sql = "SELECT * FROM `" + table_schema + "`.`" + table_name + "` "
            else:
                sql += "SELECT * FROM `" + table_schema + "`.`" + table_name + "` "

            sql += "WHERE ( `TIME_BOOK` IS NULL AND `STATUS_ID` = " + ansc_const.NOT_YET + " ) "
            sql += "OR (`TIME_BOOK` <= '" + get_now_datetime() + "' AND `STATUS_ID` = " + ansc_const.RESERVE + " ) "

            if len(records) > count:
                sql += "UNION ALL "

        target_records = common_db.sql_execute(sql, [])

        # 全オーガナイゼーションのオーガナイゼーション毎の処理中件数を取得
        sql = "SELECT ORGANIZATION_ID, COUNT(*) AS EXEC_COUNT FROM ( "
        count = 0
        for rec in records:
            table_schema = rec["TABLE_SCHEMA"]
            table_name = rec["TABLE_NAME"]
            count += 1
            sql += "SELECT ORGANIZATION_ID FROM `" + table_schema + "`.`" + table_name + "` "
            sql += "WHERE `STATUS_ID` in (" + ansc_const.PREPARE + ", " + ansc_const.PROCESSING + ", " + ansc_const.PROCESS_DELAYED + ") "
            if len(records) > count:
                sql += "UNION ALL "

        sql += ") T1 GROUP BY ORGANIZATION_ID "
        exec_count_records = common_db.sql_execute(sql, [])

        all_exec_count = 0
        org_exec_count_list = {}
        exclusion_list = []
        if exec_count_records is not None and len(exec_count_records) > 0:
            for rec in exec_count_records:
                all_exec_count += rec["EXEC_COUNT"]
                org_exec_count_list[rec["ORGANIZATION_ID"]] = rec["EXEC_COUNT"]

            # 全オーガナイゼーションの処理件数と上限値比較
            if all_execution_limit != 0 and all_exec_count > int(all_execution_limit):
                return []

            # オーガナイゼーション毎の処理件数と上限値比較
            for rec in exec_count_records:
                if rec["ORGANIZATION_ID"] in org_execution_limit:
                    if org_execution_limit[rec["ORGANIZATION_ID"]] != 0 and rec["EXEC_COUNT"] > org_execution_limit[rec["ORGANIZATION_ID"]]:
                        exclusion_list.append(rec["ORGANIZATION_ID"])

        # 処理対象のソート
        execution_list = []
        organization_priority = 0
        for rec in target_records:
            if rec["ORGANIZATION_ID"] in exclusion_list:
                continue

            # 「オーガナイゼーション毎の処理中件数」/ 「オーガナイゼーションの同時実行数のLimit値
            for rec2 in exec_count_records:
                if rec["ORGANIZATION_ID"] == rec2["ORGANIZATION_ID"]:
                    organization_priority = rec2["EXEC_COUNT"] // org_execution_limit[rec2["ORGANIZATION_ID"]]
            if rec["TIME_BOOK"] is None:
                time_book = rec["TIME_REGISTER"]
            else:
                time_book = rec["TIME_BOOK"]

            # EXECUTION_NO + VIEW_NAME ＋ ワークスペースID + オーガナイゼーションIDのHASH値
            data = rec["EXECUTION_NO"] + rec["VIEW_NAME"] + rec["WORKSPACE_ID"] + rec["ORGANIZATION_ID"]
            hs = hashlib.md5(data.encode()).hexdigest()
            tmp_dict = {"ORGANIZATION_PRIORITY": organization_priority,
                        "TIME_BOOK": time_book,
                        "TIME_REGISTER": rec["TIME_REGISTER"],
                        "HASH": hs,
                        "ORGANIZATION_ID": rec["ORGANIZATION_ID"],
                        "WORKSPACE_ID": rec["WORKSPACE_ID"],
                        "EXECUTION_NO": rec["EXECUTION_NO"],
                        "WORKSPACE_DB": rec["WORKSPACE_DB"],
                        "VIEW_NAME": rec["VIEW_NAME"]}
            execution_list.append(tmp_dict)
            # 処理対象のソート
            execution_list = sorted(execution_list, key=lambda x: (x["ORGANIZATION_PRIORITY"], x["TIME_BOOK"], x["TIME_REGISTER"], x["HASH"]))

            # organizationに実行中の処理があるか確認
            if rec["ORGANIZATION_ID"] not in org_exec_count_list:
                org_exec_count_list[rec["ORGANIZATION_ID"]] = 0

    return execution_list, all_exec_count, org_exec_count_list, records


def child_process_exist_check(common_db, target_shema, ansibleAg):
    """
    実行中の子プロの起動確認

    Returns:
        bool
    """
    global ansc_const
    # psコマンドでbackyard_child_init.pyの起動プロセスリストを作成
    # psコマンドがマレに起動プロセスリストを取りこぼすことがあるので3回分を作成
    # command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no, driver_id]

    child_process_1 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_2 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_3 = child_process_exist_check_ps()

    records = get_running_process(common_db, target_shema)
    for rec in records:
        driver_id = rec["DRIVER_ID"]
        driver_name = rec["DRIVER_NAME"]
        execution_no = rec["EXECUTION_NO"]
        organization_id = rec["ORGANIZATION_ID"]
        workspace_id = rec["WORKSPACE_ID"]

        g.ORGANIZATION_ID = organization_id
        g.WORKSPACE_ID = workspace_id

        wsDb = DBConnectWs(workspace_id)

        ansc_const = getAnsibleConst(driver_id)

        # 子プロ起動確認
        is_running = False
        # command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no, driver_id]
        command_args = "{} {} {} {} {}".format('backyard/backyard_child_init.py', organization_id, workspace_id, execution_no, driver_id)

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
            result = cm.get_execution_process_info(wsDb, ansc_const, execution_no)
            if result[0] is False:
                log_err(g.appmsg.get_log_message(result[1], [execution_no]))
                wsDb.db_disconnect()
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
                    "TIME_START": time_stamp,
                }
                result = cm.update_execution_record(wsDb, ansc_const, data)
                if result[0] is True:
                    wsDb.db_commit()
                    g.applogger.debug(g.appmsg.get_log_message("MSG-10060", [driver_name, execution_no]))

            # コンテナが残っている場合に備えて掃除
            # ゴミ掃除に失敗しても処理は続ける
            result = ansibleAg.is_container_running(execution_no)
            if result[0] is True:
                result = ansibleAg.container_kill(ansc_const, execution_no)
                if result[0] is False:
                    log_err(g.appmsg.get_log_message("BKY-10007", [result[1], execution_no]))
            else:
                result = ansibleAg.container_clean(ansc_const, execution_no)
                if result[0] is False:
                    log_err(g.appmsg.get_log_message("BKY-10007", [result[1], execution_no]))

        wsDb.db_disconnect()

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


def get_running_process(common_db, target_shema):
    """
    実行中の作業データを取得

    Returns:
        records
    """
    global ansc_const

    if target_shema is not None and len(target_shema) > 0:
        count = 0
        sql = ""
        for rec in target_shema:
            table_schema = rec["TABLE_SCHEMA"]
            table_name = rec["TABLE_NAME"]
            count += 1
            if sql == "":
                sql = "SELECT * FROM `" + table_schema + "`.`" + table_name + "` "
            else:
                sql += "SELECT * FROM `" + table_schema + "`.`" + table_name + "` "

            sql += " WHERE `DISUSE_FLAG` = 0 AND `STATUS_ID` in ('{}', '{}', '{}') ".format(ansc_const.PREPARE, ansc_const.PROCESSING, ansc_const.PROCESS_DELAYED)

            if len(target_shema) > count:
                sql += "UNION ALL "

        records = common_db.sql_execute(sql, [])

    return records


def get_now_datetime(format='%Y/%m/%d %H:%M:%S', type='str'):
    dt = datetime.now().strftime(format)
    if type == 'str':
        return '{}'.format(dt)
    else:
        return dt


def run_unexecuted(wsDb, execution_no, organization_id, workspace_id):
    """
    未実行（実行待ち）の作業を実行

    Returns:
        bool
        err_msg
    """
    global ansc_const

    condition = "WHERE EXECUTION_NO = %s "

    records = wsDb.table_select('V_ANSC_EXEC_STS_INST', condition, [execution_no])

    # 処理対象レコードが0件の場合は処理終了
    if len(records) == 0:
        g.applogger.debug(g.appmsg.get_log_message("MSG-10749"))
        return True,

    for rec in records:

        # データを取り出して、作業実行
        result = run_child_process(wsDb, rec, organization_id, workspace_id)
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
    # global ansc_const

    driver_id = execute_data["DRIVER_ID"]
    driver_name = execute_data["DRIVER_NAME"]
    execution_no = execute_data["EXECUTION_NO"]

    ansc_const = getAnsibleConst(driver_id)

    # 処理対象の作業インスタンス情報取得(再取得)
    retBool, result = cm.get_execution_process_info(wsDb, ansc_const, execution_no)
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

    result = cm.update_execution_record(wsDb, ansc_const, data)
    if result[0] is True:
        wsDb.db_commit()

    # 子プロセスにして、実行
    g.applogger.debug(g.appmsg.get_log_message("MSG-10745", [driver_name, execution_no]))

    command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no, driver_id]
    # cp = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cp = subprocess.Popen(command)  # noqa: F841

    return True,