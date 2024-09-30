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
import tarfile
import glob

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.ag.util import app_exception, exception
from common_libs.common.storage_access import storage_read
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from agent.libs.exastro_api import Exastro_API
from libs.util import *


def agent_main(organization_id, workspace_id, loop_count, interval):

    # 環境変数の取得
    baseUrl = os.environ["EXASTRO_URL"]
    refresh_token = os.environ['EXASTRO_REFRESH_TOKEN']
    agent_name = os.environ['AGENT_NAME']

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
    status_code, response = post_agent_version(organization_id, workspace_id, exastro_api)
    if not status_code == 200:
        # g.applogger.info(f"バージョン通知に失敗しました。")
        g.applogger.info(g.appmsg.get_log_message("MSG-10981"))
        g.applogger.info(f"post_agent_version: {status_code=} {response=}")
    else:
        target_data = response["data"] if isinstance(response["data"], dict) else {}
        version_diff = target_data.get("version_diff")
        # 作業実行可否
        main_logic_execute = True if version_diff and str(version_diff) in execute_status_list else False
    g.applogger.info(f"{'Execute main_logic' if main_logic_execute else 'Skip main_logic'}({main_logic_execute=} {version_diff=})")

    count = 1
    max = int(loop_count)

    while True:
        print("")
        print("")

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

    # 未実行インスタンス取得
    body = {}
    str_een = os.getenv('EXECUTION_ENVIRONMENT_NAMES', None)
    if str_een:
        execution_environment_names = str_een.split(',')
        body = {
            "execution_environment_names": execution_environment_names
        }
    status_code, response = post_unexecuted_instance(organization_id, workspace_id, exastro_api, body=body)
    if status_code == 200:
        target_executions = response["data"] if isinstance(response["data"], dict) else {}
        for execution_no, value in target_executions.items():
            g.applogger.debug(f"{execution_no=}: \n {json.dumps(value, indent=4) if value else {}}")
            # 子プロ起動時の引数対応: None -> ""
            user_name = value["user_name"] if value["user_name"] else ""
            password = value["password"] if value["password"] else ""

            # 子プロ起動
            command = ["python3", "agent/agent_child_init.py", organization_id, workspace_id, execution_no, value["driver_id"], value["build_type"], user_name, password, value["base_image"]]
            cp = subprocess.Popen(command)  # noqa: F841

            # 子プロ死活監視
            child_process_exist_check(organization_id, workspace_id, execution_no, value["driver_id"], value["build_type"], user_name, password, value["base_image"])

            # 起動した未実行インスタンスを保存
            start_up_list.append(execution_no)
    else:
        g.applogger.info(g.appmsg.get_log_message("MSG-10955", [status_code, response]))

    # 実行中インスタンス取得: 起動した未実行インスタンスは除く
    ps_count, working_ps_list, error_ps_list = get_working_child_process(organization_id, workspace_id, start_up_list)

    # 作業中通知
    if ps_count != 0:
        status_code, response = post_notification_execution(organization_id, workspace_id, exastro_api, working_ps_list)
        if not status_code == 200:
            # g.applogger.info(f"作業中通知に失敗しました。")
            g.applogger.info(g.appmsg.get_log_message("MSG-10982"))
            g.applogger.info(f"post_notification_execution: {status_code=} {response=}")

        # 指定リトライ回数以上のステータス更新、ステータスファイルファイルの削除
        update_error_executions(organization_id, workspace_id, exastro_api, error_ps_list)
    else:
        g.applogger.info(f"get_working_child_process: {ps_count=}")


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
        raise AppException('MSG-10947', [])

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
        raise AppException('MSG-10947', [])


def child_process_exist_check(organization_id, workspace_id, execution_no, driver_id, build_type=None, user_name="", password="", base_image=None ,reboot=True):
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
    child_process_retry_limit = int(os.getenv('CHILD_PROCESS_RETRY_LIMIT', 3))

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

    # 子プロ確認のみ(reboot=false)
    if reboot is False:
        return is_running

    if is_running is False:
        # ステータスファイルがあるか確認
        # status_file_path = "/storage/" + organization_id + "/" + workspace_id + "/ag_ansible_execution/status/" + execution_no
        status_file_path = f"/storage/{organization_id}/{workspace_id}/ag_ansible_execution/status/{driver_id}/{execution_no}"
        if os.path.isfile(status_file_path):
            # ステータスファイルに書き込まれている再起動回数取得
            obj = storage_read()
            obj.open(status_file_path)
            reboot_cnt = obj.read()
            obj.close()

            # 再起動回数が10回を超える場合、再起動しない
            if int(reboot_cnt) <= child_process_retry_limit:
                # ステータスファイルに再起動回数書き込み
                obj = storage_write()
                obj.open(status_file_path, 'w')
                obj.write(str(int(reboot_cnt) + 1))
                obj.close()

                # 子プロ再起動
                command = ["python3", "agent/agent_child_init.py", organization_id, workspace_id, execution_no, driver_id, user_name, password, base_image]
                cp = subprocess.Popen(command)  # noqa: F841
            else:
                g.applogger.info(g.appmsg.get_log_message("MSG-10056", [execution_no, workspace_id]))

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

def decompress_tar_file(organization_id, workspace_id, driver_id, dir_path, conductor_dir_path, file_name, conductor_file_name, execution_no):
    """
    tarファイルを解凍してagent用のディレクトリに移動する
    ARGS:
        dir_path: in,outのtarファイルディレクトリ
        conductor_dir_path: conductorのtarファイルディレクトリ
        file_name: in,outのtarファイル名
        conductor_file_name: conductorのtarファイル名
        driver_id: ドライバーID
        execution_no: 作業番号

    Returns:
        stdout row
    """

    # in,outのtarファイルを展開
    with tarfile.open(dir_path + "/" + file_name, 'r:gz') as tar:
        tar.extractall(path=dir_path + "/tmp")

    # 展開したファイルの一覧を取得
    lst = os.listdir(dir_path + "/tmp")

    # in/out親ディレクトリパス
    root_dir_path = "/storage/ " + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no

    # 展開したファイルを移動する
    for dir_name in lst:
        if dir_name == "in":
            # inディレクトリの移動先
            move_dir = root_dir_path + "in/project"
        elif dir_name == "inventory":
            # inventoryディレクトリの移動先
            move_dir = root_dir_path + "/inventory"
        elif dir_name == "env":
            # envディレクトリの移動先
            move_dir = root_dir_path + "/env"
        elif dir_name == "builder_executable_files":
            # builder_executable_filesディレクトリの移動先
            move_dir = root_dir_path + "/builder_executable_files"
        elif dir_name == "runner_executable_files":
            # runner_executable_filesディレクトリの移動先
            move_dir = root_dir_path + "/runner_executable_files"
        elif dir_name == "out":
            # outディレクトリの移動先
            move_dir = root_dir_path + "/out"
        elif dir_name == ".tmp":
            # .tmpディレクトリの移動先
            move_dir = root_dir_path + "/.tmp"
        elif dir_name == "tmp":
            # tmpディレクトリの移動先
            move_dir = root_dir_path + "/tmp"
        # 移動先のディレクトリがない場合作成
        if os.path.exists(move_dir):
            os.mkdir(move_dir)
            os.chmod(move_dir, 0o777)
        join_path = os.path.join(dir_path + "/tmp", dir_name)
        move_path = os.path.join(move_dir, dir_name)
        shutil.move(join_path,move_path)

        #移動後作業ディレクトリ削除
        shutil.rmtree(dir_path + "/tmp")

    # conductorのtarファイルを展開
    with tarfile.open(conductor_dir_path + "/" + conductor_file_name, 'r:gz') as tar:
        tar.extractall(path=conductor_dir_path + "/conductor_tmp")

    # 展開したファイルの一覧を取得
    lst = os.listdir(conductor_dir_path + "/conductor_tmp")

    # 展開したファイルを移動する
    for dir_name in lst:
        # conductorディレクトリの移動先
        move_dir = root_dir_path + "/conductor"
        # 移動先のディレクトリがない場合作成
        if os.path.exists(move_dir):
            os.mkdir(move_dir)
            os.chmod(move_dir, 0o777)
        join_path = os.path.join(conductor_dir_path + "/tmp", dir_name)
        move_path = os.path.join(move_dir, dir_name)
        shutil.move(join_path,move_path)

        # 移動後作業ディレクトリ削除
        shutil.rmtree(conductor_dir_path + "/conductor_tmp")


def check_child_process(execution_no):
    """
    子プロの死活監視
    ARGS:
        execution_no: 作業番号

    """

def get_working_child_process(organization_id, workspace_id, start_up_list):
    """ステータスファイルから作業一覧取得
    Args:
        organization_id (_type_): organization_id
        workspace_id (_type_): workspace_id
        start_up_list: execution_no started in main_logic. [execution_no,]

    Returns:
        working_ps_list: { driver_id : []}
        error_ps_list: { driver_id : []}
    """
    driver_id_list = [
        "legacy",
        "pioneer",
        "legacy_role",
    ]
    ps_count = 0
    working_ps_list = {}
    error_ps_list = {}
    status_file_dir = f"/storage/{organization_id}/{workspace_id}/ag_ansible_execution/status/"

    # プロセス再起動上限値
    child_process_retry_limit = int(os.getenv('CHILD_PROCESS_RETRY_LIMIT', 3))

    [working_ps_list.setdefault(_d, []) for _d in driver_id_list]
    [error_ps_list.setdefault(_d, []) for _d in driver_id_list]

    for driver_id in driver_id_list:
        for _file in glob.glob(f"{status_file_dir}/{driver_id}/*"):
            if not os.path.isfile(_file):
                g.applogger.debug(f"{_file}: {os.path.isfile(_file)}")
                continue
            # ステータスファイルに書き込まれている再起動回数取得
            obj = storage_read()
            obj.open(_file)
            reboot_cnt = obj.read()
            obj.close()
            reboot_cnt = int(reboot_cnt) if len(reboot_cnt) != 0 else 0
            execution_no = os.path.basename(_file)

            # 起動した未実行インスタンスは除く
            if execution_no in start_up_list:
                continue

            # 子プロ死活監視
            result_child_process = child_process_exist_check(organization_id, workspace_id, execution_no, driver_id, reboot=False)
            g.applogger.debug(f"{driver_id=}, {execution_no=}, {reboot_cnt=}, {result_child_process=}")
            if result_child_process and int(reboot_cnt) <= child_process_retry_limit:
                # 子プロ実行中
                working_ps_list[driver_id].append(execution_no)
            else:
                # 子プロ存在しない
                error_ps_list[driver_id].append(execution_no)
            ps_count += 1

    g.applogger.debug(f"ps_count: {ps_count}")
    g.applogger.debug(f"working_ps_list: \n {json.dumps(working_ps_list, indent=4) if working_ps_list else {}}")
    g.applogger.debug(f"error_ps_list: \n {json.dumps(error_ps_list, indent=4) if error_ps_list else {}}")

    return ps_count, working_ps_list, error_ps_list

def update_error_executions(organization_id, workspace_id, exastro_api, error_ps_list):
    """エラー対象の作業状態通知送信
        結果ファイル更新＋ステータス更新
    Args:
        organization_id (_type_): organization_id
        workspace_id (_type_): workspace_id
        exastro_api: Exastro_API()
        error_ps_list: : { driver_id : []}
    """

    status_id = AnscConst.FAILURE # 完了(異常)
    for driver_id , del_execution_list in error_ps_list.items():
        for del_execution in del_execution_list:
            status_update = True
            # 作業状態通知送信: 異常時

            # ステータスファイル有りで、作業中の実行プロセス停止時、エラーログに追記して通知
            _base_dir = f"/storage/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{del_execution}"
            [os.makedirs(f"{_base_dir}/{_c}") for _c in ["out", "in", "conductor"] if not os.path.isdir(f"{_base_dir}/{_c}")]
            ag_parent_error_log =f"{_base_dir}/ag_parent_error.log"
            obj = storage_write()
            obj.open(ag_parent_error_log, 'w')
            # Ansible実行エージェントで作業中の実行プロセスが停止した為、終了します。(Execution no:{})
            obj.write(g.appmsg.get_api_message('MSG-10985', [del_execution]))
            obj.close()

            # 作業状態通知(ファイル)

            # 各種tar＋ファイルパス取得
            out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path\
                = arcive_tar_data(organization_id, workspace_id, driver_id, del_execution, status_id, mode="parent")

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
                form_data["out_tar_data"] =  (
                    os.path.basename(out_gztar_path),
                    open(out_gztar_path, "rb"),
                    mimetypes.guess_type(out_gztar_path, False)[0])
            if os.path.isfile(parameters_gztar_path):
                form_data["parameters_tar_data"] =  (
                    os.path.basename(parameters_gztar_path),
                    open(parameters_gztar_path, "rb"),
                    mimetypes.guess_type(parameters_gztar_path, False)[0])
            if os.path.isfile(parameters_file_gztar_path):
                form_data["parameters_file_tar_data"] =  (
                    os.path.basename(parameters_file_gztar_path),
                    open(parameters_file_gztar_path, "rb"),
                    mimetypes.guess_type(parameters_file_gztar_path, False)[0])
            if os.path.isfile(conductor_gztar_path):
                form_data["conductor_tar_data"] =  (
                    os.path.basename(conductor_gztar_path),
                    open(conductor_gztar_path, "rb"),
                    mimetypes.guess_type(conductor_gztar_path, False)[0])

            status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, del_execution, body, form_data=form_data)
            if not status_code == 200:
                # g.applogger.info(f"作業状態通知(ファイル)に失敗しました。(execution={del_execution}, {status_id=})")
                g.applogger.info(g.appmsg.get_log_message("MSG-10983", [del_execution, f"{status_id=}"]))
                status_update = False

            # 作業状態通知
            if status_update:
                status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, del_execution, body)
                if not status_code == 200:
                    # g.applogger.info(f"作業状態通知に失敗しました。(execution_no={del_execution}, {status_id=})")
                    g.applogger.info(g.appmsg.get_log_message("MSG-10984", [f"execution_no={del_execution}", f"{status_id=}"]))
                    status_update = False

            if status_update:
                # ステータスファイルの削除
                delete_status_file(organization_id, workspace_id, driver_id, del_execution)
