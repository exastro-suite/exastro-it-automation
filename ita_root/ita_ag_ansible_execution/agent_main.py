# Copyright 2024 NEC Corporation#
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
import os
import glob
import json
import re
import mimetypes

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.ag.util import app_exception, exception
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from agent.libs.exastro_api import Exastro_API
from libs.util import *  # noqa: F403


def agent_main(organization_id, workspace_id, loop_count, interval):

    # 環境変数の取得
    baseUrl = os.environ["EXASTRO_URL"]
    refresh_token = os.environ['EXASTRO_REFRESH_TOKEN']

    # 作業実行可能ステータス
    #   1: Not compatible (old)→古い: 作業実行不可
    #   2: Compatible (newest)→最新:  作業実行可
    #   3: Compatible→最新ではない:   作業実行可
    execute_status_list = [
        "2",
        "3"
    ]

    # ITAのAPI呼び出しモジュール
    exastro_api = Exastro_API(
        base_url=baseUrl,
        refresh_token=refresh_token
    )
    exastro_api.get_access_token(organization_id, refresh_token)

    main_logic_execute = False
    version_diff = None
    # バージョン通知API実行
    g.applogger.info(g.appmsg.get_log_message("MSG-10996", [workspace_id]))
    status_code, response = post_agent_version(organization_id, workspace_id, exastro_api)  # noqa: F405
    if not status_code == 200:
        g.applogger.info(g.appmsg.get_log_message("MSG-10997", [workspace_id, status_code, response]))
    else:
        target_data = response["data"] if isinstance(response["data"], dict) else {}
        version_diff = target_data.get("version_diff")
        # 作業実行可否
        main_logic_execute = True if version_diff and str(version_diff) in execute_status_list else False
    g.applogger.info(f"{'Execute main_logic' if main_logic_execute else 'Skip main_logic'}({main_logic_execute=} {version_diff=})")

    count = 1
    max = int(loop_count)

    while True:
        try:
            if main_logic_execute:
                main_logic(organization_id, workspace_id, exastro_api, baseUrl)
        except AppException as e:  # noqa F405
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)

        # インターバルを置いて、max数までループする
        time.sleep(interval)
        if count >= max:
            break
        else:
            count = count + 1


def main_logic(organization_id, workspace_id, exastro_api, baseUrl):

    # 起動した未実行インスタンス
    start_up_list = []

    # 未実行作業取得数
    execution_limit = None

    # 同時実行数の上限値取得
    _execution_limit = getenv_int('EXECUTION_LIMIT', 1)

    # 未実行作業取得の上限値取得
    _movement_limit = getenv_int('MOVEMENT_LIMIT', 1)

    # 実行中のプロセス数
    ps_exec_count, ps_error_count, working_ps_list, error_ps_list = get_working_child_process(organization_id, workspace_id, start_up_list)

    # 実行可能な作業数: 同時実行数の上限値 - 実行中のプロセス数
    allow_execution_limit = _execution_limit - ps_exec_count
    g.applogger.info(f"Process: {allow_execution_limit=} ({ps_exec_count}/{_execution_limit}) API: {_movement_limit=}")

    # 作業実行可能な場合
    if allow_execution_limit > 0:
        # 未実行作業取得数を設定
        execution_limit = _movement_limit if allow_execution_limit > _movement_limit else allow_execution_limit
        body = {}
        str_een = os.getenv('EXECUTION_ENVIRONMENT_NAMES', None)
        # パラメータの追加
        body.setdefault("execution_environment_names", str_een.split(',')) if str_een else None
        body.setdefault("execution_limit", execution_limit) if execution_limit else None
        # 未実行インスタンス取得
        g.applogger.info(g.appmsg.get_log_message("MSG-10988", [workspace_id]))
        g.applogger.debug(f"post_unexecuted_instance: {organization_id=} {workspace_id=} {body=}")
        status_code, response = post_unexecuted_instance(organization_id, workspace_id, exastro_api, body=body)  # noqa: F405
        if status_code == 200:
            target_executions = response["data"] if isinstance(response["data"], dict) else {}
            for execution_no, value in target_executions.items():
                g.applogger.debug(f"{execution_no=}: \n {json.dumps(value, indent=4) if value else {}}")
                # 子プロ起動時の引数対応: None -> ""
                runtime_data_del = value["anstwr_del_runtime_data"] if value["anstwr_del_runtime_data"] else "0"

                # 子プロ起動
                g.applogger.info(g.appmsg.get_log_message("MSG-11006", [workspace_id, execution_no]))

                command = ["python3", "agent/agent_child_init.py", organization_id, workspace_id, execution_no, value["driver_id"], value["build_type"], runtime_data_del, "start"]

                subprocess.Popen(command)

                # 子プロ起動状態ファイル生成
                create_execution_status_file(organization_id, workspace_id, value["driver_id"], execution_no)  # noqa: F405

                # 子プロ起動パラメータ退避
                create_execution_parameters_file(organization_id, workspace_id, value["driver_id"], execution_no, value["build_type"], runtime_data_del)  # noqa: F405

                # 子プロ再起動状態ファイル生成
                create_execution_restart_status_file(organization_id, workspace_id, value["driver_id"], execution_no)  # noqa: F405

                # 起動した子プロの作業番号を退避
                # なんらかの理由で子プロの起動に失敗した場合の。子プロ死活監視の為
                start_up_list.append(execution_no)

        else:
            g.applogger.info(g.appmsg.get_log_message("MSG-10989", [workspace_id, status_code, response]))
    else:
        # 同時実行数制御で未実行作業取得をSKIP
        g.applogger.info(f"Skipped acquiring unexecuted tasks due to the concurrent task limit. Processes in progress: {ps_exec_count}")

    # 子プロのステータスファイルより子プロの動作状況を判定し、必要に応じて子プロを再起動する
    g.applogger.debug("Determine the operating status of the child program")
    ps_exec_count, ps_error_count, working_ps_list, error_ps_list = get_working_child_process(organization_id, workspace_id, start_up_list)

    g.applogger.debug("ps_exec_count:" + str(ps_exec_count))
    g.applogger.debug("ps_error_count:" + str(ps_error_count))
    g.applogger.debug("working_ps_list: " + str(working_ps_list))
    g.applogger.debug("error_ps_list: " + str(error_ps_list))

    # 作業中の作業がある場合、作業中通知
    if ps_exec_count != 0:
        g.applogger.info(g.appmsg.get_log_message("MSG-10998", [workspace_id, str(working_ps_list)]))
        status_code, response = post_notification_execution(organization_id, workspace_id, exastro_api, working_ps_list)  # noqa: F405
        if not status_code == 200:
            g.applogger.info(g.appmsg.get_log_message("MSG-10999", [workspace_id, str(working_ps_list), status_code, response]))

    # 子プロセスが存在しない作業がある場合、作業中通知
    if ps_error_count != 0:
        # 指定リトライ回数以上のステータス更新、ステータスファイルファイルの削除
        update_error_executions(organization_id, workspace_id, exastro_api, error_ps_list)


def decode_tar_file(base_64data, dir_path):
    """
        tarファイルをbase64に変換する
        ARGS:
            file_path:ファイルパス
            workspace_id: WorkspaceID
        RETRUN:
            statusCode, {}, msg
    """

    cmd = "base64 -d " + base_64data + " " + dir_path + "tmp.gz"
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    if ret.returncode != 0:
        # enomoto ログ出力
        raise AppException('MSG-11000', ["tar file type:out"])  # noqa: F405


def conductor_decode_tar_file(base_64data, dir_path):
    """
        tarファイルをbase64に変換する
        ARGS:
            file_path:ファイルパス
            workspace_id: WorkspaceID
        RETRUN:
            statusCode, {}, msg
    """

    cmd = "base64 -d " + base_64data + " " + dir_path + "conductor_tmp.gz"
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    if ret.returncode != 0:
        # enomoto ログ出力
        raise AppException('MSG-11000', ["tar file type:conductor"])  # noqa: F405


def child_process_exist_check(organization_id, workspace_id, execution_no, driver_id, build_type=None, runtime_data_del="0"):
    """
    実行中の子プロの起動確認

    Returns:
        bool
    """
    # psコマンドでagent/agent_child_init.pyの起動プロセスリストを作成
    # psコマンドがマレに起動プロセスリストを取りこぼすことがあるので3回分を作成
    # command = ["python3", "agent/agent_child_init.py", organization_id, workspace_id, execution_no, driver_id]

    child_process_1 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_2 = child_process_exist_check_ps()
    time.sleep(0.05)
    child_process_3 = child_process_exist_check_ps()

    # プロセス再起動上限値
    # 子プロ再起動は行わない
    # プロセス再起動上限値は0とする
    child_process_retry_limit = int(os.getenv('CHILD_PROCESS_RETRY_LIMIT', 0))

    # 子プロ起動確認
    is_running = False
    # command = ["python3", "agent/agent_child_init.py", organization_id, workspace_id, execution_no]
    command_args = "{} {} {} {}".format('agent/agent_child_init.py', organization_id, workspace_id, execution_no)

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

    if is_running is False:
        # ステータスファイルがあるか確認
        status_file_dir_path, status_file_path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)  # noqa: F405
        if os.path.isfile(status_file_path):
            # ステータスファイルに書き込まれている再起動回数取得
            with open(status_file_path) as f:
                reboot_cnt = f.read()

            # 再起動回数回を超える場合、再起動しない
            if int(reboot_cnt) < child_process_retry_limit:
                # ステータスファイルに再起動回数書き込み
                with open(status_file_path, "w") as f:
                    reboot_cnt = int(reboot_cnt) + 1
                    f.write(str(reboot_cnt))

                g.applogger.info(g.appmsg.get_log_message("MSG-11005", [workspace_id, execution_no, str(reboot_cnt)]))
                # 子プロ再起動
                command = ["python3", "agent/agent_child_init.py", organization_id, workspace_id, execution_no, driver_id, runtime_data_del, "restart"]
                cp = subprocess.Popen(command)  # noqa: F841
            else:
                g.applogger.info(g.appmsg.get_log_message("MSG-11004", [workspace_id, execution_no]))
                return False

    return True


def child_process_exist_check_ps():
    """
    実行中の子プロのpsコマンド取得結果

    Returns:
        stdout row
    """
    # ps -efw | grep agent/agent_child_init.py | grep -v grep
    cp1 = subprocess.run(
        ["ps", "-efw"],
        capture_output=True,
        text=True
    )
    if cp1.returncode != 0 and cp1.stderr:
        cp1.check_returncode()

    cp2 = subprocess.run(
        ["grep", "agent/agent_child_init.py"],
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


def get_working_child_process(organization_id, workspace_id, start_up_list):
    """ステータスファイルから作業一覧取得
    Args:
        organization_id (_type_): organization_id
        workspace_id (_type_): workspace_id

    Returns:
        working_ps_list: { driver_id : []}
        error_ps_list: { driver_id : []}
    """
    driver_id_list = [
        "legacy",
        "pioneer",
        "legacy_role",
    ]
    ps_exec_count = 0
    ps_error_count = 0
    working_ps_list = {}
    error_ps_list = {}
    storagepath = os.environ.get('STORAGEPATH')
    status_file_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/ag_ansible_execution/status/"

    # プロセス再起動上限値
    # 子プロ再起動は行わない
    # プロセス再起動上限値は0とする

    # ドライバ毎の空リスト作成
    [working_ps_list.setdefault(_d, []) for _d in driver_id_list]
    [error_ps_list.setdefault(_d, []) for _d in driver_id_list]

    for driver_id in driver_id_list:
        for _file in glob.glob(f"{status_file_dir_path}/{driver_id}/*"):
            if len(os.path.basename(_file)) > 36:
                # ステータスファイル以外もあるのでファイル名が36文字以上はスキップ
                continue

            if not os.path.isfile(_file):
                continue

            # ステータスファイルに書き込まれている再起動回数取得
            with open(_file) as f:
                reboot_cnt = f.read()
            if len(reboot_cnt) == 0:
                reboot_cnt = "0"

            execution_no = os.path.basename(_file)

            if execution_no in start_up_list:
                # 起動直後の子プロ起動確認は行わず、次のループから実施
                continue

            # 子プロ起動パラメータ退避ファイルから起動パラメータ取得
            build_type, runtime_data_del = get_execution_parameters_file(organization_id, workspace_id, driver_id, execution_no)  # noqa: F405
            ret = child_process_exist_check(organization_id, workspace_id, execution_no, driver_id, build_type, runtime_data_del)
            if ret is True:
                # 子プロ実行中
                g.applogger.debug(g.appmsg.get_log_message("MSG-11002", [workspace_id, execution_no]))
                working_ps_list[driver_id].append(execution_no)
                ps_exec_count += 1
            else:
                # 子プロ未実行
                g.applogger.debug(g.appmsg.get_log_message("MSG-11003", [workspace_id, execution_no]))
                error_ps_list[driver_id].append(execution_no)
                ps_error_count += 1

    g.applogger.debug(f"working_ps_list: \n {json.dumps(working_ps_list, indent=4) if working_ps_list else {}}")
    g.applogger.debug(f"error_ps_list: \n {json.dumps(error_ps_list, indent=4) if error_ps_list else {}}")

    return ps_exec_count, ps_error_count, working_ps_list, error_ps_list


def update_error_executions(organization_id, workspace_id, exastro_api, error_ps_list):
    """エラー対象の作業状態通知送信
        結果ファイル更新＋ステータス更新
    Args:
        organization_id (_type_): organization_id
        workspace_id (_type_): workspace_id
        exastro_api: Exastro_API()
        error_ps_list: : { driver_id : []}
    """

    status_id = AnscConst.FAILURE  # 完了(異常)
    for driver_id, del_execution_list in error_ps_list.items():
        for del_execution in del_execution_list:
            status_update = True
            # 作業状態通知送信: 異常時

            # ステータスファイル有りで、作業中の実行プロセス停止時、エラーログに追記して通知
            # enomoto /ag_parent_error.logパス確認
            storagepath = os.environ.get('STORAGEPATH')
            _base_dir = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{del_execution}"
            [os.makedirs(f"{_base_dir}/{_c}") for _c in ["out"] if not os.path.isdir(f"{_base_dir}/{_c}")]
            # ログファイルのパス取得
            exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass = get_log_file_path(organization_id, workspace_id, driver_id, del_execution)  # noqa: F405

            with open(parent_error_log_pass, 'w') as f:
                # Ansible実行エージェントで作業中の実行プロセスが停止した為、終了します。(Execution no:{})
                f.write(g.appmsg.get_log_message('MSG-10985', [del_execution]))

            # ansibleのログファイルとアプリのログをマージする
            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)  # noqa: F405

            # 各種tar＋ファイルパス取得
            out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path\
                = arcive_tar_data(organization_id, workspace_id, driver_id, del_execution, status_id, mode="parent")  # noqa: F405

            g.applogger.debug(f"{out_gztar_path=}, {parameters_gztar_path=}, {parameters_file_gztar_path=}, {conductor_gztar_path=}")

            body = {
                "driver_id": driver_id,
                "status": status_id,
            }

            form_data = {
                "json_parameters": json.dumps(body)
            }

            # form_dataへのtarデータ追加
            if os.path.isfile(out_gztar_path):
                form_data["out_tar_data"] = (
                    os.path.basename(out_gztar_path),
                    open(out_gztar_path, "rb"),
                    mimetypes.guess_type(out_gztar_path, False)[0])
            if os.path.isfile(parameters_gztar_path):
                form_data["parameters_tar_data"] = (
                    os.path.basename(parameters_gztar_path),
                    open(parameters_gztar_path, "rb"),
                    mimetypes.guess_type(parameters_gztar_path, False)[0])
            if os.path.isfile(parameters_file_gztar_path):
                form_data["parameters_file_tar_data"] = (
                    os.path.basename(parameters_file_gztar_path),
                    open(parameters_file_gztar_path, "rb"),
                    mimetypes.guess_type(parameters_file_gztar_path, False)[0])
            if os.path.isfile(conductor_gztar_path):
                form_data["conductor_tar_data"] = (
                    os.path.basename(conductor_gztar_path),
                    open(conductor_gztar_path, "rb"),
                    mimetypes.guess_type(conductor_gztar_path, False)[0])

            # 結果データ更新
            g.applogger.info(g.appmsg.get_log_message("MSG-10994", [workspace_id, del_execution]))
            status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, del_execution, body, form_data=form_data)  # noqa: F405
            if not status_code == 200:
                g.applogger.info(g.appmsg.get_log_message("MSG-10995", [workspace_id, del_execution, status_code, response]))
                status_update = False

            # 作業状態通知
            if status_update:
                g.applogger.info(g.appmsg.get_log_message("MSG-10990", [workspace_id, del_execution, status_id]))
                status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, del_execution, body)  # noqa: F405
                if not status_code == 200:
                    g.applogger.info(g.appmsg.get_log_message("MSG-10991", [workspace_id, del_execution, status_id, status_code, response]))
                    status_update = False

            # ステータスファイルの削除
            delete_status_file(organization_id, workspace_id, driver_id, del_execution)  # noqa: F405


def getenv_int(key, default):
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        g.applogger.info(f"The environment variable is not a number. {key=}")
        return default
