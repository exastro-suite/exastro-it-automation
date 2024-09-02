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
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
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
    root_in_dir_path = "/exastro/project_dir/" + driver_id + "/" + execution_no
    root_out_dir_path = "/exastro/share_volume_dir/" + driver_id + "/" + execution_no

    # rcファイルディレクトリパス
    rc_dir_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no + "/artifacts/" + execution_no

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

    # 投入資材取得
    _chunk_size=1024*1024
    g.applogger.info(g.appmsg.get_log_message("MSG-10954", []))
    status_code, response = get_execution_populated_data(organization_id, workspace_id, exastro_api, execution_no, query=driver_id)
    if not status_code == 200:
        g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
        raise AppException()
    for execution_no, value in response.items():
        dir_path = value["in_out_data"]
        conductor_dir_path = value["conductor_data"]
        with open(dir_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=_chunk_size):
                if chunk:
                    f.write(chunk)
                    f.flush()

        if not conductor_dir_path == "":
            conductor_dir_path = value["conductor_data"]
            with open(conductor_dir_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=_chunk_size):
                    if chunk:
                        f.write(chunk)
                        f.flush()

            # tarファイルの中身のディレクトリ、ファイル移動
            decompress_tar_file(organization_id, workspace_id, value["driver_id"], dir_path, conductor_dir_path, "tmp.gz", "conductor_tmp.gz", value["driver_id"], execution_no)
        else:
            # tarファイルの中身のディレクトリ、ファイル移動
            decompress_tar_file(organization_id, workspace_id, value["driver_id"], dir_path, conductor_dir_path, "tmp.gz", "", value["driver_id"], execution_no)

    response.close()

    # 実行環境構築方法がITAの場合builder.sh実行
    if build_type == "ITA":
        cmd = root_in_dir_path + "/builder_executable_files/builder.sh"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            msg = g.appmsg.get_api_message('MSG-10948', [])
            raise app_exception(msg)

    # start.sh実行
    cmd = root_in_dir_path + "/runner_executable_files/start.sh"
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if ret.returncode != 0:
        msg = g.appmsg.get_api_message('MSG-10949', [])
        raise app_exception(msg)

    while True:
        # 各種ファイルをtarファイルにまとめる
        out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path = arcive_tar_data(driver_id, execution_no, status)

        # alive.sh実行
        cmd = root_in_dir_path + "/runner_executable_files/alive.sh"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            msg = g.appmsg.get_api_message('MSG-10950', [])
            raise app_exception(msg)

        if ret.stdout == '0':
            # 作業実行が実行中
            file_path = root_out_dir_path + "/out/forced.txt"
            if os.path.isfile(file_path):
                # 緊急停止ボタンが押された
                cmd = root_in_dir_path + "/runner_executable_files/stop.sh"
                ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                if ret.returncode != 0:
                    msg = g.appmsg.get_api_message('MSG-10951', [])
                    raise app_exception(msg)

                if ret.stdout == '0':
                    # forced_exec作成
                    file_path = root_out_dir_path + "/out/forced_exec"
                    f = open(file_path, 'w')
                    f.close
                    continue
                else:
                    # rcファイルの中身を確認する
                    file_path = root_in_dir_path + "artifacts/" + execution_no + "/rc"
                    if os.path.isfile(file_path):
                        obj = storage_read()
                        obj.open(file_path)
                        rc_data = obj.read()
                        obj.close()
                        if rc_data == "0":
                            # 結果データ更新
                            status = AnscConst.COMPLETE
                            endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                            body = {
                                "driver_id": driver_id,
                                "status": status
                            }
                            form_data = {
                                "json_parameters": json.dumps(body),
                                "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                                "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                                "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                                "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                            }
                            status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                            if not status_code == 200:
                                g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                                raise AppException()

                            # 作業状態通知送信
                            body = {
                                "driver_id": driver_id,
                                "status": status
                            }
                            g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                            status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                            if not status_code == 200:
                                g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                                raise AppException()
                            break
                        else:
                            # ログを残す
                            msg = g.appmsg.get_api_message('MSG-10953', [])
                            obj = storage_write()
                            obj.open(root_out_dir_path + "/out/error.log", 'w')
                            obj.write(msg)
                            obj.close()

                            # 結果データ更新
                            status = AnscConst.FAILURE
                            endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                            body = {
                                "driver_id": driver_id,
                                "status": status
                            }
                            form_data = {
                                "json_parameters": json.dumps(body),
                                "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                                "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                                "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                                "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                            }
                            status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                            if not status_code == 200:
                                g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                                raise AppException()

                            # 作業状態通知送信
                            body = {
                                "driver_id": driver_id,
                                "status": status
                            }
                            g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                            status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                            if not status_code == 200:
                                g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                                raise AppException()
                            break
                    else:
                        # rcファイルなし
                        # ログを残す
                        msg = g.appmsg.get_api_message('MSG-10953', [])
                        obj = storage_write()
                        obj.open(root_out_dir_path + "/out/error.log", 'w')
                        obj.write(msg)
                        obj.close()

                        # 結果データ更新
                        status = AnscConst.FAILURE
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        form_data = {
                            "json_parameters": json.dumps(body),
                            "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                            "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                            "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                            "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                        }
                        status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()

                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()
                        break
            else:
                # rcファイルの中身を確認する
                file_path = root_in_dir_path + "artifacts/" + execution_no + "/rc"
                if os.path.isfile(file_path):
                    obj = storage_read()
                    obj.open(file_path)
                    rc_data = obj.read()
                    obj.close()
                    if rc_data == "0":
                        # 結果データ更新
                        status = AnscConst.COMPLETE
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        form_data = {
                            "json_parameters": json.dumps(body),
                            "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                            "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                            "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                            "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                        }
                        status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()

                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/execution/{status}"
                        body = {}
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="POST", body=body)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()
                        break
                    else:
                        # 結果データ更新
                        status = AnscConst.FAILURE
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        form_data = {
                            "json_parameters": json.dumps(body),
                            "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                            "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                            "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                            "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                        }
                        status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()

                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()
                        break
                else:
                    # rcファイルなし
                    # 結果データ更新
                    status = AnscConst.PROCESSING
                    endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                    body = {
                        "driver_id": driver_id,
                        "status": status
                    }
                    form_data = {
                        "json_parameters": json.dumps(body),
                        "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                        "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                        "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                        "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                    }
                    status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                    if not status_code == 200:
                        g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        raise AppException()

                    # 作業状態通知送信
                    endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                    body = {
                        "driver_id": driver_id,
                        "status": status
                    }
                    g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                    status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                    if not status_code == 200:
                        g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        raise AppException()
                    continue
        else:
            # 作業実行が停止中
            file_path = root_out_dir_path + "/out/forced_exec"
            if os.path.isfile(file_path):
                # 緊急停止
                # 結果データ更新
                status = AnscConst.SCRAM
                endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                body = {
                    "driver_id": driver_id,
                    "status": status
                }
                form_data = {
                    "json_parameters": json.dumps(body),
                    "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                    "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                    "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                    "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                }
                status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                if not status_code == 200:
                    g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                    raise AppException()

                # 作業状態通知送信
                endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                body = {
                    "driver_id": driver_id,
                    "status": status
                }
                g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                if not status_code == 200:
                    g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                    raise AppException()
                break
            else:
                # rcファイルの中身を確認する
                file_path = root_in_dir_path + "artifacts/" + execution_no + "/rc"
                if os.path.isfile(file_path):
                    obj = storage_read()
                    obj.open(file_path)
                    rc_data = obj.read()
                    obj.close()
                    if rc_data == "0":
                        # 結果データ更新
                        status = AnscConst.COMPLETE
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        form_data = {
                            "json_parameters": json.dumps(body),
                            "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                            "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                            "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                            "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                        }
                        status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()

                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()
                        break
                    else:
                        # 結果データ更新
                        status = AnscConst.FAILURE
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        form_data = {
                            "json_parameters": json.dumps(body),
                            "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                            "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                            "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                            "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                        }
                        status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()

                        # 作業状態通知送信
                        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                        body = {
                            "driver_id": driver_id,
                            "status": status
                        }
                        g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                        status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            raise AppException()
                        break
                else:
                    # rcファイルなし
                    # ログを残す
                    msg = g.appmsg.get_api_message('MSG-10953', [])
                    obj = storage_write()
                    obj.open(root_out_dir_path + "/out/error.log", 'w')
                    obj.write(msg)
                    obj.close()

                    # 結果データ更新
                    status = AnscConst.FAILURE
                    endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                    body = {
                        "driver_id": driver_id,
                        "status": status
                    }
                    form_data = {
                        "json_parameters": json.dumps(body),
                        "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                        "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                        "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                        "conductor_tar_data" : (os.path.basename(conductor_dir_path), open(conductor_dir_path, "rb"), mimetypes.guess_type(conductor_dir_path, False)[0]),
                    }
                    status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                    if not status_code == 200:
                        g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        raise AppException()

                    # 作業状態通知送信
                    body = {
                        "driver_id": driver_id,
                        "status": status
                    }
                    g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
                    status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                    if not status_code == 200:
                        g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        raise AppException()
                    break

    # ステータスファイル削除
    os.remove(status_file_path + "/" + execution_no)

if __name__ == "__main__":
    agent_child_main()

def decompress_tar_file(organization_id, workspace_id, driver_id, dir_path, conductor_dir_path, file_name, conductor_file_name, driver_id, execution_no):
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