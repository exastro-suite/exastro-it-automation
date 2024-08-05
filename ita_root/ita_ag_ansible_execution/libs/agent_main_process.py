# # Copyright 2024 NEC Corporation#
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# #

import subprocess
import time
import requests
import os
import tarfile

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.ag.util import app_exception, exception
from common_libs.common import storage_access


def agent_main(organization_id, workspace_id, loop_count, interval):
    count = 1
    max = int(loop_count)

    while True:
        print("")
        print("")

        try:
            main_logic(organization_id, workspace_id)
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

def main_logic(organization_id, workspace_id):
    try:
        # インターバル
        interval = int(os.environ.get("EXECUTE_INTERVAL", 5))
        while True:
            # 未実行インスタンス確認送信
            api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/unexecuted/instance:"
            response_array = requests.get(api_uri, {})

            if response_array.status_code == "200":
                for execution_no, value in response_array.items():
                    # tarファイルを解凍
                    tar_data = value["in_out_data"]
                    dir_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + value["driver_id"] + "/" + execution_no
                    decode_tar_file(tar_data, dir_path)

                    conductor_tar_data = value["conductor_data"]
                    # conductor用tarファイルがあるか確認
                    if not conductor_tar_data == "":
                        # conductor用tarファイルを解凍
                        conductor_dir_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/conductor/"
                        conductor_decode_tar_file(conductor_tar_data, dir_path)

                        # tarファイルの中身のディレクトリ、ファイル移動
                        decompress_tar_file(dir_path, conductor_dir_path, "tmp.gz", "conductor_tmp.gz", value["driver_id"], execution_no)
                    else:
                        # tarファイルの中身のディレクトリ、ファイル移動
                        decompress_tar_file(dir_path, conductor_dir_path, "tmp.gz", "", value["driver_id"], execution_no)

                    # 子プロ起動
                    child_process_exist_check(organization_id, workspace_id, execution_no, value["driver_id"], value["build_type"], value["user_name"], value["password"])

            # インターバルを置いて、max数までループする
            time.sleep(interval)
            if count >= max:
                break
            else:
                count = count + 1
    except Exception as e:
        raise app_exception(e)


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
        msg = g.appmsg.get_api_message('MSG-10947', [])
        raise app_exception(msg)

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
        msg = g.appmsg.get_api_message('MSG-10947', [])
        raise app_exception(msg)


def child_process_exist_check(organization_id, workspace_id, execution_no, driver_id, build_type, user_name, password):
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

    # 子プロ起動確認
    is_running = False
    # command = ["python3", "backyard/backyard_child_init.py", organization_id, workspace_id, execution_no, driver_id]
    command_args = "{} {} {} {} {}".format('libs/agent_child_process.py', organization_id, workspace_id, execution_no, driver_id, build_type, user_name, password)

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
        g.applogger.info(g.appmsg.get_log_message("MSG-10056", [execution_no, workspace_id]))

        return False

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
        ["grep", "libs/agent_child_process.py"],
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

def decompress_tar_file(dir_path, conductor_dir_path, file_name, conductor_file_name, driver_id, execution_no):
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

    # 展開したファイルを移動する
    for dir_name in lst:
        if dir_name == "in":
            # inディレクトリの移動先
            move_dir = "exastro/project_dir/" + driver_id + "/" + execution_no + "/project"
        elif dir_name == "inventory":
            # inventoryディレクトリの移動先
            move_dir = "exastro/project_dir/" + driver_id + "/" + execution_no + "/inventory"
        elif dir_name == "env":
            # envディレクトリの移動先
            move_dir = "exastro/project_dir/" + driver_id + "/" + execution_no + "/env"
        elif dir_name == "builder_executable_files":
            # builder_executable_filesディレクトリの移動先
            move_dir = "exastro/project_dir/" + driver_id + "/" + execution_no + "/builder_executable_files"
        elif dir_name == "runner_executable_files":
            # runner_executable_filesディレクトリの移動先
            move_dir = "exastro/project_dir/" + driver_id + "/" + execution_no + "/runner_executable_files"
        elif dir_name == "out":
            # outディレクトリの移動先
            move_dir = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "/out"
        elif dir_name == ".tmp":
            # .tmpディレクトリの移動先
            move_dir = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "/.tmp"
        elif dir_name == "tmp":
            # tmpディレクトリの移動先
            move_dir = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "/tmp"
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
        move_dir = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "/conductor"
        # 移動先のディレクトリがない場合作成
        if os.path.exists(move_dir):
            os.mkdir(move_dir)
            os.chmod(move_dir, 0o777)
        join_path = os.path.join(conductor_dir_path + "/tmp", dir_name)
        move_path = os.path.join(move_dir, dir_name)
        shutil.move(join_path,move_path)

        # 移動後作業ディレクトリ削除
        shutil.rmtree(conductor_dir_path + "/conductor_tmp")