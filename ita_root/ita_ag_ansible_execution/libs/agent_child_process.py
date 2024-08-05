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
import sys

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.ag.util import app_exception, exception
from common_libs.common.storage_access import storage_read


def main_logic():
    try:
        # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
        args = sys.argv
        organization_id = args[1]
        workspace_id = args[2]
        execution_no = args[3]
        driver_id = args[4]
        build_type = args[5]
        user_name = [6]
        password = [7]

        # 実行環境構築方法がITAの場合builder.sh実行
        if build_type == "ITA":
            cmd = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no + "in/builder_executable_files/builder.sh"
            ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if ret.returncode != 0:
                msg = g.appmsg.get_api_message('MSG-10948', [])
                raise app_exception(msg)

        # start.sh実行
        cmd = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no + "in/runner_executable_files/start.sh"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            msg = g.appmsg.get_api_message('MSG-10949', [])
            raise app_exception(msg)

        # インターバル
        interval = int(os.environ.get("EXECUTE_INTERVAL", 5))

        while True:
            # alive.sh実行
            cmd = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no + "in/runner_executable_files/alive.sh"
            ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if ret.returncode != 0:
                msg = g.appmsg.get_api_message('MSG-10950', [])
                raise app_exception(msg)

            if ret.stdout == '0':
                # 作業実行が実行中
                file_path = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "/out/forced.txt"
                if os.path.isfile(file_path):
                    # 緊急停止ボタンが押された
                    cmd = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no + "in/runner_executable_files/stop.sh"
                    if ret.returncode != 0:
                        msg = g.appmsg.get_api_message('MSG-10951', [])
                        raise app_exception(msg)

                    if ret.stdout == '0':
                        # forced_exec作成
                        file_path = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "/out/forced_exec"
                        f = open(file_path, 'w')
                        f.close
                        continue
                    else:
                        # rcファイルの中身を確認する
                        file_path = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "rc"
                        if os.path.isfile(file_path):
                            obj = storage_read()
                            obj.open(file_path)
                            rc_data = obj.read()
                            obj.close()
                            if rc_data == "0":
                                # 作業状態通知送信
                                api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status"
                                response_array = requests.get(api_uri, {})

                                break
                            else:
                                # 作業状態通知送信
                                api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status"
                                response_array = requests.get(api_uri, {})

                                # ログを残す

                                break
                        else:
                            # rcファイルなし
                            # 作業状態通知送信
                            api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status"
                            response_array = requests.get(api_uri, {})

                            # ログを残す

                            break
                else:
                    # rcファイルの中身を確認する
                    file_path = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "rc"
                    if os.path.isfile(file_path):
                        obj = storage_read()
                        obj.open(file_path)
                        rc_data = obj.read()
                        obj.close()
                        if rc_data == "0":
                            # 作業状態通知送信
                            api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status"
                            response_array = requests.get(api_uri, {})

                            break
                        else:
                            # 作業状態通知送信
                            api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status"
                            response_array = requests.get(api_uri, {})

                            # ログを残す

                            break
                    else:
                        # rcファイルなし
                        # 作業状態通知送信
                        api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status"
                        response_array = requests.get(api_uri, {})
                        continue
            else:
                # 作業実行が停止中
                file_path = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "/out/forced_exec"
                if os.path.isfile(file_path):
                    # 緊急停止
                    # 作業状態通知送信
                    api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status"
                    response_array = requests.get(api_uri, {})
                    break
                else:
                    # rcファイルの中身を確認する
                    file_path = "exastro/share_volume_dir/" + driver_id + "/" + execution_no + "rc"
                    if os.path.isfile(file_path):
                        obj = storage_read()
                        obj.open(file_path)
                        rc_data = obj.read()
                        obj.close()
                        if rc_data == "0":
                            # 作業状態通知送信
                            api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status:"
                            response_array = requests.get(api_uri, {})

                            break
                        else:
                            # 作業状態通知送信
                            api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status:"
                            response_array = requests.get(api_uri, {})

                            # ログを残す

                            break
                    else:
                        # rcファイルなし
                        # 作業状態通知送信
                        api_uri = "/api/" + organization_id + "/workspaces/" + workspace_id + "/execution/status:"
                        response_array = requests.get(api_uri, {})

                        # ログを残す

                        break