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
import os
import sys

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.common.storage_access import storage_read
from common_libs.ag.util import app_exception, exception
from common_libs.ansible_driver.functions.util import get_OSTmpPath
from common_libs.ansible_driver.functions.util import rmAnsibleCreateFiles
from agent.libs.exastro_api import Exastro_API
from libs.util import *

def agent_child_main():
    """
    agent_childのラッパー
    """
    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
    args = sys.argv
    execution_no = args[3]

    global ansc_const
    global driver_error_log_file

    g.applogger.set_tag("EXECUTION_NO", execution_no)

    g.applogger.debug(g.appmsg.get_log_message("MSG-10720", [execution_no]))

    g.AnsibleCreateFilesPath = "{}/Ansible_{}".format(get_OSTmpPath(), execution_no) #####

    try:
        # ステータスファイル作成は？ ####
        agent_child()
        # 正常終了 / 以外 #####
        # ステータスファイル削除 ####
    except AppException as e:
        # ステータスファイル削除 ####
        app_exception(e)
    except Exception as e:
        exception(e)
    finally:
        # /tmpをゴミ掃除
        # rmAnsibleCreateFiles()
        pass
    return 0


def agent_child():
    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
    args = sys.argv
    organization_id = args[1]
    workspace_id = args[2]
    execution_no = args[3]
    driver_id = args[4]
    build_type = args[5]
    # redhad_user_name = args[6]
    # redhad_password = args[7]

    # in/out親ディレクトリパス
    root_dir_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no

    # 実行状態確認用のステータスファイル作成
    status_file_path = "/storage/" + organization_id + "/" + workspace_id + "/ag_ansible_execution/status/" + driver_id
    if not os.path.exists(status_file_path):
        os.mkdir(status_file_path)
        os.chmod(status_file_path, 0o777)
    if not os.path.isfile(status_file_path + "/" + execution_no):
        # ファイル名を作業番号で作成
        obj = storage_write()
        obj.open(status_file_path + "/" + execution_no, 'w')
        obj.write("0")
        obj.close()

    # 環境変数の取得
    baseUrl = os.environ["EXASTRO_URL"]
    refresh_token = os.environ['EXASTRO_REFRESH_TOKEN']

    # ITAのAPI呼び出しモジュール
    exastro_api = Exastro_API(
        base_url=baseUrl,
        refresh_token=refresh_token
    )
    exastro_api.get_access_token(organization_id, refresh_token)

    ##### 投入資材取得、展開テスト
    # _chunk_size=1024*1024 #####
    # method = "GET"
    # endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/execution/xxxxxx" #####
    # status_code, response = retry_api_call(exastro_api, endpoint, mode="stream" ,method="POST")
    # if not status_code == 200:
    #     raise AppException("MSG-10957", [status_code, response])
    # tmp_dir_path = f"{root_dir_path}.tmp.gz"
    # dir_path = f"{tmp_dir_path}".replace("/storage/", "/tmp/")
    # with open(dir_path, 'wb') as f:
    #     for chunk in response.iter_content(chunk_size=_chunk_size):
    #         if chunk:
    #             f.write(chunk)
    #             f.flush()
    # response.close()
    # 解凍→配置(input, conductor) #####

    # 実行環境構築方法がITAの場合builder.sh実行
    if build_type == "ITA":
        cmd = root_dir_path + "in/builder_executable_files/builder.sh"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            raise AppException('MSG-10948', [])

    # start.sh実行
    cmd = root_dir_path + "in/runner_executable_files/start.sh"
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if ret.returncode != 0:
        raise AppException('MSG-10949', [])

    # インターバル
    interval = int(os.environ.get("EXECUTE_INTERVAL", 5))

    while True:
        # alive.sh実行
        cmd = root_dir_path + "in/runner_executable_files/alive.sh"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            raise AppException('MSG-10950', [])

        if ret.stdout == '0':
            # 作業実行が実行中
            file_path = root_dir_path + "/out/forced.txt"
            if os.path.isfile(file_path):
                # 緊急停止ボタンが押された
                cmd = root_dir_path + "in/runner_executable_files/stop.sh"
                ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                if ret.returncode != 0:
                    raise AppException('MSG-10951', [])

                if ret.stdout == '0':
                    # forced_exec作成
                    file_path = root_dir_path + "/out/forced_exec"
                    f = open(file_path, 'w')
                    f.close
                    continue
                else:
                    # rcファイルの中身を確認する
                    file_path = root_dir_path + "/rc"
                    if os.path.isfile(file_path):
                        obj = storage_read()
                        obj.open(file_path)
                        rc_data = obj.read()
                        obj.close()
                        if rc_data == "0":
                            # 作業状態通知送信
                            endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                            g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                            try:
                                status_code, response = exastro_api.api_request(
                                    "GET",
                                    endpoint
                                )
                                if not status_code == 200:
                                    raise AppException("MSG-10957", [status_code, response])
                            except AppException as e:  # noqa E405
                                app_exception(e)
                            break
                            ##### 以下、テスト
                            # # 作業状態通知送信
                            # endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/execution/xxxxx" #####
                            # body = {}
                            # g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                            # status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="POST", body=body)
                            # if not status_code == 200:
                            #     raise AppException("MSG-10957", [status_code, response])

                            # # 作業状態通知送信(ログ、ファイル)
                            # endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/execution/xxxxx" #####
                            # body = {}
                            # g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                            # upload_path = root_dir_path + "/out/log.tar.gz" #####
                            # with open(upload_path, "rb") as r:
                            #     files = {"file": (r.name, r.read())}
                            #     status_code, response = retry_api_call(exastro_api, endpoint, mode="form", method="POST", body=body, files=files)
                            # if not status_code == 200:
                            #     raise AppException("MSG-10957", [status_code, response])
                        else:
                            # 作業状態通知送信
                            endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                            g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                            try:
                                status_code, response = exastro_api.api_request(
                                    "GET",
                                    endpoint
                                )
                                if not status_code == 200:
                                    raise AppException("MSG-10957", [status_code, response])
                            except AppException as e:  # noqa E405
                                app_exception(e)

                            # ログを残す
                            msg = g.appmsg.get_api_message('MSG-10952', [])
                            obj = storage_write()
                            obj.open(root_dir_path + "/out/error.log", 'w')
                            obj.write(msg)
                            obj.close()
                            break
                    else:
                        # rcファイルなし
                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        try:
                            status_code, response = exastro_api.api_request(
                                "GET",
                                endpoint
                            )
                            if not status_code == 200:
                                raise AppException("MSG-10957", [status_code, response])
                        except AppException as e:  # noqa E405
                            app_exception(e)

                        # ログを残す
                        msg = g.appmsg.get_api_message('MSG-10953', [])
                        obj = storage_write()
                        obj.open(root_dir_path + "/out/error.log", 'w')
                        obj.write(msg)
                        obj.close()
                        break
            else:
                # rcファイルの中身を確認する
                file_path = root_dir_path + "/rc"
                if os.path.isfile(file_path):
                    obj = storage_read()
                    obj.open(file_path)
                    rc_data = obj.read()
                    obj.close()
                    if rc_data == "0":
                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        try:
                            status_code, response = exastro_api.api_request(
                                "GET",
                                endpoint
                            )
                            if not status_code == 200:
                                raise AppException("MSG-10957", [status_code, response])
                        except AppException as e:  # noqa E405
                            app_exception(e)

                        break
                    else:
                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        try:
                            status_code, response = exastro_api.api_request(
                                "GET",
                                endpoint
                            )
                            if not status_code == 200:
                                raise AppException("MSG-10957", [status_code, response])
                        except AppException as e:  # noqa E405
                            app_exception(e)

                        break
                else:
                    # rcファイルなし
                    # 作業状態通知送信
                    endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                    g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                    try:
                        status_code, response = exastro_api.api_request(
                            "GET",
                            endpoint
                        )
                        if not status_code == 200:
                            raise AppException("MSG-10957", [status_code, response])
                    except AppException as e:  # noqa E405
                        app_exception(e)
                    continue
        else:
            # 作業実行が停止中
            file_path = root_dir_path + "/out/forced_exec"
            if os.path.isfile(file_path):
                # 緊急停止
                # 作業状態通知送信
                endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                try:
                    status_code, response = exastro_api.api_request(
                        "GET",
                        endpoint
                    )
                    if not status_code == 200:
                        raise AppException("MSG-10957", [status_code, response])
                except AppException as e:  # noqa E405
                    app_exception(e)
                break
            else:
                # rcファイルの中身を確認する
                file_path = root_dir_path + "/rc"
                if os.path.isfile(file_path):
                    obj = storage_read()
                    obj.open(file_path)
                    rc_data = obj.read()
                    obj.close()
                    if rc_data == "0":
                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        try:
                            status_code, response = exastro_api.api_request(
                                "GET",
                                endpoint
                            )
                            if not status_code == 200:
                                raise AppException("MSG-10957", [status_code, response])
                        except AppException as e:  # noqa E405
                            app_exception(e)

                        break
                    else:
                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        try:
                            status_code, response = exastro_api.api_request(
                                "GET",
                                endpoint
                            )
                            if not status_code == 200:
                                raise AppException("MSG-10957", [status_code, response])
                        except AppException as e:  # noqa E405
                            app_exception(e)
                        break
                else:
                    # rcファイルなし
                    # 作業状態通知送信
                    endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/execution/status"
                    g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                    try:
                        status_code, response = exastro_api.api_request(
                            "GET",
                            endpoint
                        )
                        if not status_code == 200:
                            raise AppException("MSG-10957", [status_code, response])
                    except AppException as e:  # noqa E405
                        app_exception(e)

                    # ログを残す
                    msg = g.appmsg.get_api_message('MSG-10953', [])
                    obj = storage_write()
                    obj.open(root_dir_path + "/out/error.log", 'w')
                    obj.write(msg)
                    obj.close()
                    break

    # ステータスファイル削除
    os.remove(status_file_path + "/" + execution_no)

if __name__ == "__main__":
    agent_child_main()
