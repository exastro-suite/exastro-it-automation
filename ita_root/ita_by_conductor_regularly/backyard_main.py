# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:# www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from flask import g  # noqa: F401
from common_libs.common.dbconnect import *  # noqa: F401, F403
import datetime
import re
import calendar
import traceback
import json
from common_libs.conductor.classes.exec_util import ConductorExecuteLibs
from common_libs.loadtable import *  # noqa: F403
from common_libs.common.util import get_exastro_platform_users
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format, print_exception_msg
from common_libs.common.exception import AppException


def backyard_main(organization_id, workspace_id):  # noqa: C901
    debug_msg = g.appmsg.get_log_message("BKY-20001", [])
    g.applogger.debug(debug_msg)

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # Status変数
        status_ids_list = {
            "STATUS_IN_PREPARATION": "1",  # ステータス：準備中
            "STATUS_IN_OPERATION": "2",  # ステータス：稼働中
            "STATUS_COMPLETED": "3",  # ステータス：完了
            "STATUS_MISMATCH_ERROR": "4",  # ステータス：不整合エラー
            "STATUS_LINKING_ERROR": "5",  # ステータス：紐付けエラー
            "STATUS_UNEXPECTED_ERROR": "6",  # ステータス：想定外エラー
            "STATUS_CONDUCTOR_DISCARD": "7",  # ステータス：conductor廃止
            "STATUS_OPERATION_DISCARD": "8"  # ステータス：operation廃止
        }

        # ################次回実行日付の設定（初回）
        table_name = "T_COMN_CONDUCTOR_REGULARLY_LIST"
        where_str = "WHERE DISUSE_FLAG=0 AND NEXT_EXECUTION_DATE IS NULL AND `STATUS_ID`=%s"
        prep_list = objdbca.table_select(table_name, where_str, status_ids_list["STATUS_IN_PREPARATION"])
        if len(prep_list) != 0:

            for item in prep_list:
                objdbca.db_transaction_start()
                status_id, next_execution_date = calc_next_execution_date(item, status_ids_list)
                try:
                    data_list = {
                        "REGULARLY_ID": item["REGULARLY_ID"],
                        "STATUS_ID": status_id,
                        "NEXT_EXECUTION_DATE": next_execution_date,
                        "LAST_UPDATE_USER": g.get('USER_ID')
                    }
                    ret = objdbca.table_update(table_name, data_list, "REGULARLY_ID")
                    debug_msg = g.appmsg.get_log_message("BKY-40009", [item["REGULARLY_ID"]])
                    g.applogger.debug(debug_msg)

                except Exception as e:
                    objdbca.db_transaction_end(False)
                    t = traceback.format_exc()
                    g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
                    debug_msg = g.appmsg.get_log_message("BKY-40012", [])
                    g.applogger.info(debug_msg)

                objdbca.db_transaction_end(True)
        else:
            debug_msg = g.appmsg.get_log_message("BKY-40001", [])
            g.applogger.debug(debug_msg)
        # 次回実行日付の設定（初回）################

        # ################ Conductorの予約と次回実行日付の更新
        # インターバル設定
        system_settings = objdbca.table_select("T_COMN_SYSTEM_CONFIG", "WHERE CONFIG_ID=%s", ["INTERVAL_TIME"])
        system_interval = system_settings[0]["VALUE"]
        interval_time = "3"
        max_interval = 525600
        min_interval = 1
        try:
            if max_interval >= int(system_interval) and int(system_interval) >= min_interval:
                interval_time = int(system_interval)
        except ValueError:
            interval_time = 3

        current_datetime = datetime.datetime.now()

        current_plus_interval = current_datetime + datetime.timedelta(minutes=interval_time)
        where_str2 = "WHERE DISUSE_FLAG=0 AND (STATUS_ID=%s OR STATUS_ID=%s) AND (NEXT_EXECUTION_DATE<%s)"
        bind_values = [
            status_ids_list["STATUS_IN_OPERATION"],
            status_ids_list["STATUS_LINKING_ERROR"],
            current_plus_interval.strftime("%Y-%m-%d %H:%M:%S")
        ]
        inOps_list = objdbca.table_select(table_name, where_str2, bind_values)  # noqa: E501

        platform_users = {}
        try:
            platform_users = get_exastro_platform_users()
        except AppException as e:
            msg_code, logmsg_args = e.args
            msg = g.appmsg.get_log_message(msg_code, [logmsg_args[0], logmsg_args[1]])
            print_exception_msg(msg)
        except Exception:
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))

        active_user_list = []
        for user_id in platform_users.keys():
            active_user_list.append(user_id)

        c_menu = 'conductor_instance_list'
        n_menu = 'conductor_node_instance_list'
        cc_menu = 'conductor_class_edit'
        m_menu = 'movement_list'
        notice = 'conductor_notice_definition'
        objconductor = load_table.loadTable(objdbca, c_menu)  # noqa: F405
        objnode = load_table.loadTable(objdbca, n_menu)  # noqa: F405
        objmovement = load_table.loadTable(objdbca, m_menu)  # noqa: F405
        objcclass = load_table.loadTable(objdbca, cc_menu)  # noqa: F405
        objcnotice = load_table.loadTable(objdbca, notice)  # noqa: F405
        objmenus = {
            "objconductor": objconductor,
            "objnode": objnode,
            "objmovement": objmovement,
            "objcclass": objcclass,
            "objcnotice": objcnotice
        }

        objCexec = ConductorExecuteLibs(objdbca, "", objmenus)

        if len(inOps_list) != 0:
            for item in inOps_list:

                execute_flag = True
                status_id = item["STATUS_ID"]
                next_execution_date = item["NEXT_EXECUTION_DATE"]

                # レコードのステータスIDが紐付けエラーの場合、一度「準備中」に設定
                if status_id == status_ids_list["STATUS_LINKING_ERROR"]:
                    status_id = status_ids_list["STATUS_IN_PREPARATION"]

                # 実行ユーザの廃止チェック
                if item["EXECUTION_USER_ID"] not in active_user_list:
                    status_id = status_ids_list["STATUS_LINKING_ERROR"]
                    execute_flag = False
                    debug_msg = g.appmsg.get_log_message("BKY-40003", [item["EXECUTION_USER_ID"]])
                    g.applogger.debug(debug_msg)

                # conductorの廃止チェック
                cclass_disuse = check_conductor_disuse(objdbca, item["CONDUCTOR_CLASS_ID"])
                if cclass_disuse is True:
                    status_id = status_ids_list["STATUS_CONDUCTOR_DISCARD"]
                    execute_flag = False

                # operationの廃止チェック
                op_disuse = check_operation_disuse(objdbca, item["OPERATION_ID"])
                if op_disuse is True:
                    status_id = status_ids_list["STATUS_OPERATION_DISCARD"]
                    execute_flag = False

                # conductorインスタンス登録処理
                objdbca.db_transaction_start()
                if next_execution_date >= current_datetime:
                    if execute_flag is True:
                        tmp_parameter = {
                            'conductor_class_id': item["CONDUCTOR_CLASS_ID"],
                            'operation_id': item["OPERATION_ID"],
                            'schedule_date': str(item["NEXT_EXECUTION_DATE"]).replace("-", "/"),
                            'conductor_data': {},
                        }
                        try:
                            # パラメータチェック
                            check_param = objCexec.chk_execute_parameter_format(tmp_parameter)
                            tmp_parameter = check_param[2]
                            parameter = objCexec.create_execute_register_parameter(tmp_parameter, None)
                            conductor_parameter = parameter[1].get('conductor')
                            node_parameters = parameter[1].get('node')

                            # conductorインスタンス, nodeインスタンス登録
                            debug_msg = g.appmsg.get_log_message("BKY-40007", [])
                            g.applogger.debug(debug_msg)

                            # パラメータのexecution_userを、レコードを登録したユーザに差し替え
                            user_setting_flag = False
                            for key, value in platform_users.items():
                                if key == item["EXECUTION_USER_ID"]:
                                    user_setting_flag = True
                                    conductor_parameter["parameter"]["execution_user"] = value
                                    break

                            # 差し替えに失敗した場合
                            if user_setting_flag is False:
                                debug_msg = g.appmsg.get_log_message("BKY-40011", [])
                                g.applogger.debug(debug_msg)
                                raise Exception

                            instance_ret = objCexec.conductor_instance_exec_maintenance(conductor_parameter)  # noqa: F841
                            debug_msg = g.appmsg.get_log_message("BKY-40008", [])
                            g.applogger.debug(debug_msg)
                            node_ret = objCexec.node_instance_exec_maintenance(node_parameters)  # noqa: F841
                            objdbca.db_transaction_end(True)

                            # 次回実行日付計算
                            status_id, next_execution_date = calc_next_execution_date(item, status_ids_list)

                        except Exception as e:
                            t = traceback.format_exc()
                            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
                            debug_msg = g.appmsg.get_log_message("BKY-40006", [item["CONDUCTOR_CLASS_ID"], item["OPERATION_ID"], str(item["NEXT_EXECUTION_DATE"])])  # noqa: E501
                            g.applogger.info(debug_msg)
                            objdbca.db_transaction_end(False)
                            status_id = status_ids_list["STATUS_LINKING_ERROR"]
                else:
                    if status_id == status_ids_list["STATUS_LINKING_ERROR"]:
                        pass
                    else:
                        status_id = status_ids_list["STATUS_IN_PREPARATION"]
                        next_execution_date = None

                if status_id == status_ids_list["STATUS_COMPLETED"]:
                    next_execution_date = None

                try:
                    if item["STATUS_ID"] == status_ids_list["STATUS_LINKING_ERROR"] and status_id == status_ids_list["STATUS_LINKING_ERROR"]:
                        pass
                    else:
                        data_list = {
                            "REGULARLY_ID": item["REGULARLY_ID"],
                            "STATUS_ID": status_id,
                            "NEXT_EXECUTION_DATE": next_execution_date,
                            "LAST_UPDATE_USER": g.get('USER_ID')
                        }
                        objdbca.db_transaction_start()
                        ret = objdbca.table_update(table_name, data_list, "REGULARLY_ID")
                        objdbca.db_transaction_end(True)
                except Exception as e:
                    t = traceback.format_exc()
                    g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
                    debug_msg = g.appmsg.get_log_message("BKY-40012", [])
                    g.applogger.info(debug_msg)
        else:
            debug_msg = g.appmsg.get_log_message("BKY-40002", [])
            g.applogger.debug(debug_msg)
        # Conductorの予約と次回実行日付の更新################

        # ################ ConductorとOpertionの復活チェック
        where_str3 = "WHERE DISUSE_FLAG=0 AND (STATUS_ID=%s OR STATUS_ID=%s)"
        restore_check_list = objdbca.table_select(table_name, where_str3, [status_ids_list["STATUS_CONDUCTOR_DISCARD"], status_ids_list["STATUS_OPERATION_DISCARD"]])    # noqa: E501
        if restore_check_list != 0:
            for item in restore_check_list:
                status_id = item["STATUS_ID"]

                # conductorの廃止チェック
                if status_id == status_ids_list["STATUS_CONDUCTOR_DISCARD"]:
                    cclass_disuse = check_conductor_disuse(objdbca, item["CONDUCTOR_CLASS_ID"])
                    if cclass_disuse is True:
                        break

                # operationの廃止チェック
                if status_id == status_ids_list["STATUS_OPERATION_DISCARD"]:
                    op_disuse = check_operation_disuse(objdbca, item["OPERATION_ID"])
                    if op_disuse is True:
                        break

                try:
                    data_list = {
                        "REGULARLY_ID": item["REGULARLY_ID"],
                        "STATUS_ID": status_ids_list["STATUS_IN_PREPARATION"],
                        "NEXT_EXECUTION_DATE": None,
                        "LAST_UPDATE_USER": g.get('USER_ID')
                    }
                    objdbca.db_transaction_start()
                    ret = objdbca.table_update(table_name, data_list, "REGULARLY_ID")  # noqa: F841
                    objdbca.db_transaction_end(True)
                except Exception as e:
                    t = traceback.format_exc()
                    g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
                    debug_msg = g.appmsg.get_log_message("BKY-40012", [])
                    g.applogger.info(debug_msg)
                    objdbca.db_transaction_end(False)

        # ConductorとOperationの復活チェック################

    finally:
        objdbca.db_disconnect()

    debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    g.applogger.debug(debug_msg)


# conductor廃止チェック用 廃止の場合はTrueを返す
def check_conductor_disuse(objdbca, id):
    where_string = "WHERE DISUSE_FLAG=0 AND CONDUCTOR_CLASS_ID=%s"
    check = objdbca.table_select(
        "T_COMN_CONDUCTOR_CLASS",
        where_string,
        [id]
    )
    if len(check) != 1:
        debug_msg = g.appmsg.get_log_message("BKY-40004", [id])
        g.applogger.debug(debug_msg)
        return True
    else:
        return False


# operation廃止チェック用 廃止の場合はTrueを返す
def check_operation_disuse(objdbca, id):
    where_string = "WHERE DISUSE_FLAG=0 AND OPERATION_ID=%s"
    check = objdbca.table_select(
        "T_COMN_OPERATION",
        where_string,
        [id]
    )
    if len(check) != 1:
        debug_msg = g.appmsg.get_log_message("BKY-40005", [id])
        g.applogger.debug(debug_msg)
        return True
    else:
        return False


# 次回実行日付とステータスIDを返す
def calc_next_execution_date(col_list, status_ids_list):    # noqa: C901
    current_datetime = datetime.datetime.now()

    start_date = col_list["START_DATE"]
    end_date = col_list["END_DATE"]
    period_id = col_list["REGULARLY_PERIOD_ID"]
    interval = col_list["EXECUTION_INTERVAL"]
    pattern_week_num = col_list["PATTERN_WEEK_NUMBER_ID"]
    pattern_DoW = col_list["PATTERN_DAY_OF_WEEK_ID"]
    pattern_day = col_list["PATTERN_DAY"]
    pattern_time = col_list["PATTERN_TIME"]
    stop_start_date = col_list["EXECUTION_STOP_START_DATE"]
    stop_end_date = col_list["EXECUTION_STOP_END_DATE"]
    next_execution_date = col_list["NEXT_EXECUTION_DATE"]

    status_id = status_ids_list["STATUS_IN_PREPARATION"]
    failed_validation = False
    # 作業停止期間のチェック①
    if (stop_start_date and stop_end_date) is False:
        failed_validation = True
        status_id = status_ids_list["STATUS_MISMATCH_ERROR"]

    # 作業停止期間のチェック②
    if (stop_start_date or stop_end_date) is False:
        failed_validation = True
        status_id = status_ids_list["STATUS_MISMATCH_ERROR"]

    # 間隔のチェック
    if interval:
        regex_format = r"^[1-9]$|^[1-9]\d$"
        checked = check_regex(regex_format, str(interval))
        if checked is None:
            failed_validation = True
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"]

    # 週番号のチェック
    if pattern_week_num:
        regex_format = r"^[1-5]$"
        checked = check_regex(regex_format, pattern_week_num)
        if checked is None:
            failed_validation = True
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"]

    # 曜日のチェック
    if pattern_DoW:
        try:
            id_dict = json.loads(pattern_DoW)
            if not isinstance(id_dict["id"], list):
                failed_validation = True
                status_id = status_ids_list["STATUS_MISMATCH_ERROR"]
            for DoW_str in id_dict["id"]:
                if DoW_str not in ["1", "2", "3", "4", "5", "6", "7"]:
                    failed_validation = True
                    break
        except Exception:
            failed_validation = True
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"]

    # 日付のチェック
    if pattern_day:
        regex_format = r"^[1-9]$|^[1-2]\d$|^3[0-1]$"
        checked = check_regex(regex_format, str(pattern_day))
        if checked is None:
            failed_validation = True
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"]

    # 時間のチェック
    if pattern_time:
        regex_format = r"^$|^(0\d|1\d|2[0-3]):(0\d|[1-5]\d):(0\d|[1-5]\d)$"
        checked = check_regex(regex_format, str(pattern_time))
        if checked is None:
            failed_validation = True
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"]

    # バリデーション後、次回実行日付の計算とステータスの判定
    if failed_validation is False:
        status_id = status_ids_list["STATUS_IN_OPERATION"]
        if next_execution_date is False:
            next_execution_date = None

        if period_id in ["1", "7"]:
            next_execution_date = calc_period_time(next_execution_date, start_date, interval, current_datetime, stop_start_date, stop_end_date, period_id)
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"] if next_execution_date is None else status_ids_list["STATUS_IN_OPERATION"]
        elif period_id == "2":
            next_execution_date = calc_period_day(next_execution_date, start_date, interval, pattern_time, current_datetime, stop_start_date, stop_end_date)  # noqa: E501
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"] if next_execution_date is None else status_ids_list["STATUS_IN_OPERATION"]
        elif period_id == "3":
            next_execution_date = calc_period_week(next_execution_date, start_date, interval, pattern_time, pattern_DoW, current_datetime, stop_start_date, stop_end_date)  # noqa: E501
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"] if next_execution_date is None else status_ids_list["STATUS_IN_OPERATION"]
        elif period_id == "4":
            next_execution_date = calc_period_month_day(next_execution_date, start_date, interval, pattern_time, pattern_day, current_datetime, stop_start_date, stop_end_date)  # noqa: E501
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"] if next_execution_date is None else status_ids_list["STATUS_IN_OPERATION"]
        elif period_id == "5":
            next_execution_date = calc_period_month_DoW_num(next_execution_date, start_date, interval, pattern_time, pattern_DoW, pattern_week_num, current_datetime, stop_start_date, stop_end_date)  # noqa: E501
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"] if next_execution_date is None else status_ids_list["STATUS_IN_OPERATION"]
        elif period_id == "6":
            next_execution_date = calc_period_end_of_month(next_execution_date, start_date, interval, pattern_time, current_datetime, stop_start_date, stop_end_date)  # noqa: E501
            status_id = status_ids_list["STATUS_MISMATCH_ERROR"] if next_execution_date is None else status_ids_list["STATUS_IN_OPERATION"]
        else:
            status_id = status_ids_list["STATUS_UNEXPECTED_ERROR"]

        if next_execution_date is not None and end_date is not None:
            if next_execution_date > end_date:
                status_id = status_ids_list["STATUS_COMPLETED"]
    return status_id, next_execution_date


# 正規表現チェック用
def check_regex(format_str, string):
    regex_format = re.compile(format_str)
    checked = regex_format.search(string)  # マッチしてない場合、Noneを返す
    return checked


# 周期ID：1, 7の時の計算（時間・分）
def calc_period_time(next_execution_date, start_date, interval, current_datetime, stop_start_date, stop_end_date, period_id):
    calcd_next_date = None
    if next_execution_date is None:
        required_column = [start_date, interval]
    else:
        required_column = [interval]

    for value in required_column:
        if value is False:
            calcd_next_date = None
            return calcd_next_date

    if next_execution_date is None:
        if start_date > current_datetime:
            calcd_next_date = start_date
        else:
            loop_check_date = start_date
            added_time = start_date
            while current_datetime > added_time:
                if period_id == "1": # hours
                    added_time = added_time + datetime.timedelta(hours=interval)
                elif period_id == "7": # minutes
                    added_time = added_time + datetime.timedelta(minutes=interval)
                if loop_check_date >= added_time:
                    calcd_next_date = None
                    return calcd_next_date
            calcd_next_date = added_time

    else:
        if period_id == "1": # hours
            calcd_next_date = next_execution_date + datetime.timedelta(hours=interval)
        elif period_id == "7": # minutes
            calcd_next_date = next_execution_date + datetime.timedelta(minutes=interval)

    # 抑止期間チェック
    if stop_start_date and stop_end_date:
        if calcd_next_date >= stop_start_date and stop_end_date >= calcd_next_date:
            loop_check_date = calcd_next_date
            added_time = calcd_next_date
            while stop_end_date >= calcd_next_date:
                if period_id == "1": # hours
                    added_time = added_time + datetime.timedelta(hours=interval)
                elif period_id == "7": # minutes
                    added_time = added_time + datetime.timedelta(minutes=interval)
                if loop_check_date >= added_time:
                    calcd_next_date = None
                    return calcd_next_date
                calcd_next_date = added_time

    return calcd_next_date


# 周期ID：2の時の計算（日）
def calc_period_day(next_execution_date, start_date, interval, pattern_time, current_datetime, stop_start_date, stop_end_date):
    calcd_next_date = None
    if next_execution_date is None:
        required_column = [start_date, interval, pattern_time]
    else:
        required_column = [interval, pattern_time]

    for value in required_column:
        if value is False:
            return calcd_next_date

    if next_execution_date is None:
        start_date_pattern_added = datetime.datetime.strptime(f"{start_date.date()} {pattern_time}", "%Y-%m-%d %H:%M:%S")
        if start_date > current_datetime:
            calcd_next_date = start_date_pattern_added
        else:
            loop_check_date = start_date_pattern_added
            added_time = start_date_pattern_added
            while current_datetime > added_time:
                added_time = added_time + datetime.timedelta(days=interval)
                if loop_check_date >= added_time:
                    calcd_next_date = None
                    return calcd_next_date
            calcd_next_date = added_time
    else:
        calcd_next_date = next_execution_date + datetime.timedelta(days=interval)

    # 抑止期間チェック
    if stop_start_date and stop_end_date:
        if calcd_next_date >= stop_start_date and stop_end_date >= calcd_next_date:
            loop_check_date = calcd_next_date
            added_time = calcd_next_date
            while stop_end_date >= added_time:
                added_time = added_time + datetime.timedelta(days=interval)
                if loop_check_date >= added_time:
                    calcd_next_date = None
                    return calcd_next_date
                calcd_next_date = added_time

    return calcd_next_date


# 周期ID：3の時の計算（週）
def calc_period_week(next_execution_date, start_date, interval, pattern_time, pattern_DoW, current_datetime, stop_start_date, stop_end_date):
    calcd_next_date = None
    if next_execution_date is None:
        required_column = [start_date, interval, pattern_time, pattern_DoW]
    else:
        required_column = [interval, pattern_time, pattern_DoW]

    for value in required_column:
        if value is False:
            return calcd_next_date

    # 文字列のリストを数値のリストに変換
    DoW_list = [int(i) for i in json.loads(pattern_DoW)["id"]]
    # 基準日時と同じ週の対象曜日の日時リストを返す関数
    def get_week_days(base_datetime, monday_calender=False):
        if monday_calender:
            start_of_week = base_datetime - datetime.timedelta(days=(base_datetime.date().weekday()))
        else:
            start_of_week = base_datetime - datetime.timedelta(days=(base_datetime.date().weekday() + 1) % 7)

        week_days = []
        for day in sorted(DoW_list):
            day_offset = (day) % 7
            week_day = start_of_week + datetime.timedelta(days=day_offset)
            week_days.append(week_day)
        return sorted(week_days)


    if next_execution_date is None:
        start_date_pattern_added = datetime.datetime.strptime(f"{start_date.date()} {pattern_time}", "%Y-%m-%d %H:%M:%S")  # noqa: E501
        # 開始日時以降かつ一番近い初回実行日時を割り出す
        execution_date_week_days = get_week_days(start_date_pattern_added)
        if execution_date_week_days[-1] < start_date:
            execution_date_week_days = get_week_days(start_date_pattern_added + datetime.timedelta(weeks=interval))
        for date in execution_date_week_days:
            if date >= start_date:
                first_datetime = date
                break
        calcd_next_date = first_datetime

        # 初回実行日時が現在日時より小さい場合は、一番近い日時を割り出す
        if calcd_next_date < current_datetime:
            added_time = calcd_next_date
            loop_check_date = calcd_next_date
            if current_datetime >= execution_date_week_days[-1]:
                added_time = added_time + datetime.timedelta(weeks=interval)
                execution_date_week_days = get_week_days(added_time)
            exit_loop = False
            while current_datetime >= added_time:
                for date in execution_date_week_days:
                    if current_datetime <= date:
                        added_time = date
                        exit_loop = True
                        break
                if exit_loop:
                    break
                added_time = added_time + datetime.timedelta(weeks=interval)
                execution_date_week_days = get_week_days(added_time)
                added_time = execution_date_week_days[0]
            if loop_check_date >= added_time:
                calcd_next_date = None
                return calcd_next_date
            calcd_next_date = added_time
    else:
        execution_date_week_days = get_week_days(next_execution_date)
        # 対象実行日時がその週の最後の指定曜日か確認
        if next_execution_date == execution_date_week_days[-1]:
            next_execution_date = next_execution_date + datetime.timedelta(weeks=interval)
            execution_date_week_days = get_week_days(next_execution_date)
            calcd_next_date = execution_date_week_days[0]
        else:
            for date in execution_date_week_days:
                if date >= next_execution_date:
                    calcd_next_date = date
                    break

    # 抑止期間チェック
    if stop_start_date and stop_end_date:
        if calcd_next_date >= stop_start_date and stop_end_date >= calcd_next_date:
            added_time = calcd_next_date
            loop_check_date = calcd_next_date
            if stop_end_date >= execution_date_week_days[-1]:
                added_time = added_time + datetime.timedelta(weeks=interval)
                execution_date_week_days = get_week_days(added_time)
            exit_loop = False
            while stop_end_date >= added_time and not exit_loop:
                for date in execution_date_week_days:
                    if stop_end_date <= date:
                        added_time = date
                        exit_loop = True
                        break
                if exit_loop:
                    break
                added_time = added_time + datetime.timedelta(weeks=interval)
                execution_date_week_days = get_week_days(added_time)
                added_time = execution_date_week_days[0]

            if loop_check_date >= added_time:
                calcd_next_date = None
                return calcd_next_date
            calcd_next_date = added_time
    return calcd_next_date


# 周期ID：4の時の計算 (月：日付指定)
def calc_period_month_day(next_execution_date, start_date, interval, pattern_time, pattern_day, current_datetime, stop_start_date, stop_end_date):  # noqa: C901, E501
    calcd_next_date = None
    if next_execution_date:
        required_column = [start_date, interval, pattern_time, pattern_day]
    else:
        required_column = [interval, pattern_time, pattern_day]

    for value in required_column:
        if value is False:
            return calcd_next_date

    def check_date(year, month, day):
        try:
            tmp_date = datetime.date(year, month, day)  # noqa: F841
            return True
        except ValueError:
            return False

    def generate_datetime(year, month, day, time):
        if check_date(year, month, day):
            datetime_str = f"{year}-{month}-{day} {time}"
            new_datetime = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return new_datetime
        else:
            return None

    if next_execution_date is None:
        year_num = start_date.year
        month_num = start_date.month

        check_bool = check_date(year_num, month_num, pattern_day)
        while check_bool is False:
            month_num += interval
            check_bool = check_date(year_num, month_num, pattern_day)

        start_date_pattern_added = generate_datetime(year_num, month_num, pattern_day, pattern_time)

        if check_bool and start_date > current_datetime:
            if start_date_pattern_added > start_date:
                calcd_next_date = start_date_pattern_added
            else:
                loop_check_date = start_date_pattern_added
                added_time = start_date_pattern_added
                while start_date > added_time:
                    month_num += interval
                    if month_num > 12:
                        year_num += 1
                        month_num = month_num - 12
                    check_bool = check_date(year_num, month_num, pattern_day)
                    while check_bool is False:
                        month_num += interval
                        check_bool = check_date(year_num, month_num, pattern_day)
                    added_time = generate_datetime(year_num, month_num, pattern_day, pattern_time)
                    if loop_check_date > added_time or added_time is None:
                        calcd_next_date = None
                        return None
                calcd_next_date = added_time

        else:
            loop_check_date = start_date_pattern_added
            added_time = start_date_pattern_added
            while current_datetime > added_time:
                month_num += interval
                if month_num > 12:
                    year_num += 1
                    month_num = month_num - 12
                check_bool = check_date(year_num, month_num, pattern_day)
                while check_bool is False:
                    month_num += interval
                    check_bool = check_date(year_num, month_num, pattern_day)
                added_time = generate_datetime(year_num, month_num, pattern_day, pattern_time)
                if loop_check_date > added_time or added_time is None:
                    calcd_next_date = None
                    return None
            calcd_next_date = added_time

    else:
        loop_check_date = next_execution_date
        added_time = next_execution_date
        year_num = next_execution_date.year
        month_num = next_execution_date.month + interval
        if month_num > 12:
            year_num += 1
            month_num = month_num - 12
        check_bool = check_date(year_num, month_num, pattern_day)
        while check_bool is False:
            month_num += interval
            check_bool = check_date(year_num, month_num, pattern_day)
        added_time = generate_datetime(year_num, month_num, pattern_day, pattern_time)
        if loop_check_date >= added_time:
            calcd_next_date = None
            return calcd_next_date
        calcd_next_date = added_time

    # 抑止期間チェック
    if stop_start_date and stop_end_date:
        if calcd_next_date >= stop_start_date and stop_end_date >= calcd_next_date:
            loop_check_date = calcd_next_date
            while stop_end_date >= calcd_next_date:
                year_num = calcd_next_date.year
                month_num = calcd_next_date.month + interval
                if month_num > 12:
                    year_num += 1
                    month_num = month_num - 12
                check_bool = check_date(year_num, month_num, pattern_day)
                while check_bool is False:
                    month_num += interval
                    check_bool = check_date(year_num, month_num, pattern_day)
                added_time = generate_datetime(year_num, month_num, pattern_day, pattern_time)
                if loop_check_date >= added_time:
                    calcd_next_date = None
                    return calcd_next_date
                calcd_next_date = added_time

    return calcd_next_date


# 周期ID：5の時の計算 (月：曜日指定)
def calc_period_month_DoW_num(next_execution_date, start_date, interval, pattern_time, pattern_DoW, pattern_week_num, current_datetime, stop_start_date, stop_end_date):  # noqa: C901, E501

    calcd_next_date = None
    if next_execution_date is None:
        required_column = [start_date, interval, pattern_time, pattern_DoW, pattern_week_num]
    else:
        required_column = [interval, pattern_time, pattern_DoW, pattern_week_num]

    pattern_DoW = json.loads(pattern_DoW)["id"][0]

    for value in required_column:
        if value is False:
            return calcd_next_date

    def generate_datetime(year, month, nth, DoW, time):
        try:
            days = calendar.monthrange(year, month)[1]  # 月の日数を取得
            nth = int(nth)
            DoW = int(DoW)
            target_DoW_date = []
            for day in range(1, days + 1):
                # 日数分の日付とその曜日を取得
                tmp_date = datetime.date(year, month, day)
                tmp_date_DoW = tmp_date.weekday()
                # 対象の曜日と一致する日付をリストに追加
                if tmp_date_DoW + 1 == DoW:
                    target_DoW_date.append(tmp_date)

            # 対象曜日の日付が4週分かつ最終曜日を指定している場合、最終曜日は4番目になる
            if len(target_DoW_date) < 5 and nth == 5:
                nth = 4

            tmp_datetime = datetime.datetime.strptime(f"{target_DoW_date[nth - 1]} {time}", "%Y-%m-%d %H:%M:%S")
            return tmp_datetime

        except ValueError:
            return None

    if next_execution_date is None:
        year_num = start_date.year
        month_num = start_date.month

        start_date_pattern_added = generate_datetime(year_num, month_num, pattern_week_num, pattern_DoW, pattern_time)
        if start_date_pattern_added is None:
            calcd_next_date = None
            return calcd_next_date

        if start_date > current_datetime:
            if start_date_pattern_added > start_date:
                calcd_next_date = start_date_pattern_added
            else:
                loop_check_date = start_date_pattern_added
                added_time = start_date_pattern_added
                while start_date > added_time:
                    month_num += interval
                    if month_num > 12:
                        year_num += 1
                        month_num = month_num - 12
                    added_time = generate_datetime(year_num, month_num, pattern_week_num, pattern_DoW, pattern_time)
                    if loop_check_date > added_time or added_time is None:
                        calcd_next_date = None
                        return calcd_next_date
                calcd_next_date = added_time

        else:
            loop_check_date = start_date_pattern_added
            added_time = start_date_pattern_added
            while current_datetime > added_time:
                month_num += interval
                if month_num > 12:
                    year_num += 1
                    month_num = month_num - 12
                added_time = generate_datetime(year_num, month_num, pattern_week_num, pattern_DoW, pattern_time)
                if loop_check_date > added_time or added_time is None:
                    calcd_next_date = None
                    return calcd_next_date
            calcd_next_date = added_time

    else:
        loop_check_date = next_execution_date
        year_num = next_execution_date.year
        month_num = next_execution_date.month + interval
        if month_num > 12:
            year_num += 1
            month_num = month_num - 12
        added_time = generate_datetime(year_num, month_num, pattern_week_num, pattern_DoW, pattern_time)
        if loop_check_date > added_time or added_time is None:
            calcd_next_date = None
            return calcd_next_date
        calcd_next_date = added_time

    # 抑止期間チェック
    if stop_start_date and stop_end_date:
        if calcd_next_date >= stop_start_date and stop_end_date >= calcd_next_date:
            loop_check_date = calcd_next_date
            added_time = calcd_next_date
            year_num = calcd_next_date.year
            month_num = calcd_next_date.month + interval
            while stop_end_date >= added_time:
                month_num += interval
                if month_num > 12:
                    year_num += 1
                    month_num = month_num - 12
                added_time = generate_datetime(year_num, month_num, pattern_week_num, pattern_DoW, pattern_time)
            calcd_next_date = added_time

    return calcd_next_date


# 周期ID：6の時の計算 (月末)
def calc_period_end_of_month(next_execution_date, start_date, interval, pattern_time, current_datetime, stop_start_date, stop_end_date):  # noqa: C901
    calcd_next_date = None
    if next_execution_date is None:
        required_column = [start_date, interval, pattern_time]
    else:
        required_column = [interval, pattern_time]

    for value in required_column:
        if value is False:
            return calcd_next_date

    def generate_datetime(year, month, time):
        try:
            last_day_of_month = calendar.monthrange(year, month)[1]
            datetime_str = f"{year}-{month}-{last_day_of_month} {time}"
            tmp_datetime = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return tmp_datetime
        except ValueError:
            return None

    if next_execution_date is None:
        year_num = start_date.year
        month_num = start_date.month
        start_date_pattern_added = generate_datetime(year_num, month_num, pattern_time)
        if start_date_pattern_added is None:
            calcd_next_date = None
            return calcd_next_date

        if start_date > current_datetime:
            if start_date_pattern_added > start_date:
                calcd_next_date = start_date_pattern_added
            else:
                loop_check_date = start_date_pattern_added
                added_time = start_date_pattern_added
                while start_date > added_time:
                    month_num += interval
                    if month_num > 12:
                        year_num += 1
                        month_num = month_num - 12
                    added_time = generate_datetime(year_num, month_num, pattern_time)
                    if loop_check_date > added_time or added_time is None:
                        calcd_next_date = None
                        return calcd_next_date
                    calcd_next_date = added_time

        else:
            loop_check_date = start_date_pattern_added
            added_time = start_date_pattern_added
            while current_datetime > added_time:
                month_num += interval
                if month_num > 12:
                    year_num += 1
                    month_num = month_num - 12
                added_time = generate_datetime(year_num, month_num, pattern_time)
                if loop_check_date > added_time or added_time is None:
                    calcd_next_date = None
                    return calcd_next_date
            calcd_next_date = added_time

    else:
        loop_check_date = next_execution_date
        added_time = next_execution_date
        year_num = next_execution_date.year
        month_num = next_execution_date.month + interval
        if month_num > 12:
            year_num += 1
            month_num = month_num - 12
        added_time = generate_datetime(year_num, month_num, pattern_time)
        if loop_check_date > added_time or added_time is None:
            calcd_next_date = None
            return calcd_next_date
        calcd_next_date = added_time

    # 抑止期間チェック
    if stop_start_date and stop_end_date:
        if calcd_next_date >= stop_start_date and stop_end_date >= calcd_next_date:
            loop_check_date = calcd_next_date
            added_time = calcd_next_date
            year_num = calcd_next_date.year
            month_num = calcd_next_date.month + interval
            while stop_end_date >= added_time:
                month_num += interval
                if month_num > 12:
                    year_num += 1
                    month_num = month_num - 12
                added_time = generate_datetime(year_num, month_num, pattern_time)
            calcd_next_date = added_time

    return calcd_next_date
