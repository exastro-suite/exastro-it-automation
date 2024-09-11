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
import time

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.common.storage_access import storage_read, storage_write
from common_libs.ag.util import app_exception, exception
from common_libs.ansible_driver.functions.util import get_OSTmpPath
from common_libs.ansible_driver.functions.util import rmAnsibleCreateFiles
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_execution.encrypt import agent_decrypt
from agent.libs.exastro_api import Exastro_API
from libs.util import *

def agent_child_main():
    """
    agent_childのラッパー
    """
    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
    args = sys.argv
    organization_id = args[1]
    workspace_id = args[2]
    execution_no = args[3]
    driver_id = args[4]

    global ansc_const
    global driver_error_log_file

    g.applogger.set_tag("EXECUTION_NO", execution_no)

    g.applogger.debug(g.appmsg.get_log_message("MSG-10720", [execution_no]))

    g.AnsibleCreateFilesPath = "{}/Ansible_{}".format(get_OSTmpPath(), execution_no) #####

    try:
        agent_child()
    except AppException as e:
        app_exception(e)
        # 異常時の共通処理
        # 結果データ更新+作業状態通知送信
        status = AnscConst.FAILURE
        status_code, response = post_upload_file_and_status(
            None, organization_id, workspace_id,
            execution_no, status, driver_id
        )
        if not status_code == 200:
            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
    except Exception as e:
        exception(e)
        # 異常時の共通処理
        # 結果データ更新+作業状態通知送信
        status = AnscConst.FAILURE
        status_code, response = post_upload_file_and_status(
            None, organization_id, workspace_id,
            execution_no, status, driver_id
        )
        if not status_code == 200:
            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
    finally:
        # /tmpをゴミ掃除
        # rmAnsibleCreateFiles()
        # 作業ディレクトリ削除
        clear_execution_tmpdir(organization_id, workspace_id, driver_id, execution_no)

        # ステータスファイルの削除
        clear_execution_status_file(organization_id, workspace_id, driver_id, execution_no)
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
    redhad_user_name = args[6]
    redhad_password = args[7]
    base_image = args[8]

    # パスワードの復号化
    if redhad_password != "":
        pass_phrase = organization_id + " " + workspace_id
        redhad_password = agent_decrypt(redhad_password, pass_phrase)

    # in/out親ディレクトリパス
    root_dir_path = f"/storage/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"
    # rcファイルディレクトリパス
    rc_dir_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no + "/artifacts/" + execution_no

    # ログファイルパス
    exec_log_pass = f"{root_dir_path}/out/exec.log"
    error_log_pass = f"{root_dir_path}/out/error.log"
    # 親プロ用エラーログ
    parent_error_log_pass = f"{root_dir_path}/out/ag_parent_err.log"
    # 子プロ用ログファイルパス
    child_exec_log_pass = f"{root_dir_path}/out/child_exec.log"
    child_error_log_pass = f"{root_dir_path}/out/child_error.log"
    # runnerログファイルパス
    runner_exec_log_pass = f"/storage/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/artifacts/{execution_no}/stdout"
    runner_error_log_pass = f"/storage/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/artifacts/{execution_no}/stderr"

    # 実行状態確認用のステータスファイル作成
    status_file_dir_path, status_file_path = get_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    if not os.path.exists(status_file_dir_path):
        os.makedirs(status_file_dir_path)
        os.chmod(status_file_dir_path, 0o777)
    if not os.path.isfile(status_file_path):
        # ファイル名を作業番号で作成
        obj = storage_write()
        obj.open(status_file_path, 'w')
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
    query= {"driver_id": driver_id}
    status_code, response = get_execution_populated_data(organization_id, workspace_id, exastro_api, execution_no, query=query)
    if not status_code == 200:
        raise AppException("MSG-10955", [status_code, response], [status_code, response])

    # tarファイル解凍
    dir_path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/{execution_no}/"
    shutil.rmtree(dir_path) if os.path.isdir(dir_path) else None
    os.makedirs(dir_path)
    file_name = f"{execution_no}.tar.gz"
    with open(dir_path + file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=_chunk_size):
            if chunk:
                f.write(chunk)
                f.flush()

        # tarファイルの中身のディレクトリ、ファイル移動
        decompress_tar_file(organization_id, workspace_id, driver_id, dir_path, file_name, execution_no)

    response.close()

    # ログファイルの作成
    obj = storage_write()
    if not os.path.isfile(exec_log_pass):
        obj.open(exec_log_pass, "w")
        obj.write("")
        obj.close()

    if not os.path.isfile(error_log_pass):
        obj.open(error_log_pass, "w")
        obj.write("")
        obj.close()

    if not os.path.isfile(child_exec_log_pass):
        obj.open(child_exec_log_pass, "w")
        obj.write("")
        obj.close()

    if not os.path.isfile(child_error_log_pass):
        obj.open(child_error_log_pass, "w")
        obj.write("")
        obj.close()

    # 実行環境構築方法がITAの場合builder.sh実行
    if build_type == "2":
        builder_result = True
        try:
            # ベースイメージがredhad
            if base_image == "1":
                cmd = ["sh", f"{root_dir_path}/builder_executable_files/builder.sh", "Yes", redhad_user_name, redhad_password]
            # ベースイメージがothers
            else:
                cmd = ["sh", f"{root_dir_path}/builder_executable_files/builder.sh", "No", redhad_user_name, redhad_password]

            with open(child_error_log_pass, 'a') as fp:
                ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            builder_result = False

        except Exception as e:
            builder_result = False

        finally:
            # builder.shの実行に失敗した場合完了(異常)
            if builder_result is False:
                # ログ更新
                status = AnscConst.FAILURE
                log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                # agent_child_mainのAppExceptionで異常時の共通処理
                # ansible-builderの実行に失敗しました。(builder_executable_files/builder.sh)
                status_code = "MSG-10986"
                msg_args = ["ansible-builder", "builder_executable_files/builder.sh"]
                raise AppException(status_code, msg_args, msg_args)

    # start.sh実行
    try:
        start_result = True
        cmd = ["sh", f"{root_dir_path}/runner_executable_files/start.sh"]
        with open(child_error_log_pass, 'a') as fp:
            ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        start_result = False

    except Exception as e:
        start_result = False
    finally:
        # start.shの実行に失敗した場合完了(異常)
        if start_result is False:
            # ログ更新
            status = AnscConst.FAILURE
            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

            # agent_child_mainのAppExceptionで異常時の共通処理
            # ansible-runnerの実行に失敗しました。(runner_executable_files/start.sh)
            status_code = "MSG-10986"
            msg_args = ["ansible-runner", "runner_executable_files/start.sh"]
            raise AppException(status_code, msg_args, msg_args)

    artifact_path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/artifacts"
    runner_exec_log_pass = f"{artifact_path}/{execution_no}/stdout"
    runner_error_log_pass = f"{artifact_path}/{execution_no}/stderr"
    if os.path.exists(artifact_path):
        # runnerのログファイルがあればコピー
        if os.path.exists(runner_exec_log_pass):
            shutil.copy(runner_exec_log_pass, exec_log_pass)
        if os.path.exists(runner_error_log_pass):
            shutil.copy(runner_error_log_pass, error_log_pass)

    while True:
        # 5秒スリーブ
        time.sleep(5)

        # alive.sh実行
        try:
            alive_result = True
            cmd = ["sh", f"{root_dir_path}/runner_executable_files/alive.sh"]
            with open(child_error_log_pass, 'a') as fp:
                ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            alive_result = False

        except Exception as e:
            alive_result = False

        if alive_result is True:
            # 作業実行が実行中
            file_path = root_dir_path + "/out/forced.txt"
            if os.path.isfile(file_path):
                # 緊急停止ボタンが押された
                try:
                    stop_result = True
                    cmd = ["sh", f"{root_dir_path}/runner_executable_files/stop.sh"]
                    with open(child_error_log_pass, 'a') as fp:
                        ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    stop_result = False

                except Exception as e:
                    stop_result = False
                finally:
                    if stop_result is False:
                        # stop.shの実行に失敗した場合完了(異常)
                        status = AnscConst.FAILURE
                        log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                        # agent_child_mainのAppExceptionで異常時の共通処理
                        # 緊急停止の実行に失敗しました。(runner_executable_files/stop.sh)
                        status_code = "MSG-10986"
                        msg_args = ["Emergency stop", "runner_executable_files/stop.sh"]
                        raise AppException(status_code, msg_args, msg_args)

                if stop_result is True:
                    # forced_exec作成
                    file_path = root_dir_path + "/out/forced_exec"
                    f = open(file_path, 'w')
                    f.close
                    continue
                else:
                    # rcファイルの中身を確認する
                    file_path = root_dir_path + "/artifacts/" + execution_no + "/rc"
                    if os.path.isfile(file_path):
                        obj = storage_read()
                        obj.open(file_path)
                        rc_data = obj.read()
                        obj.close()
                        if rc_data == "0":
                            # 結果データ更新
                            status = AnscConst.COMPLETE
                            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)
                            # # 各種ファイルをtarファイルにまとめる
                            # out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path = arcive_tar_data(organization_id, workspace_id, driver_id, execution_no, status)
                            # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                            # body = {
                            #     "driver_id": driver_id,
                            #     "status": status
                            # }
                            # form_data = {
                            #     "json_parameters": json.dumps(body),
                            #     "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                            #     "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                            #     "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                            #     "conductor_tar_data" : (os.path.basename(conductor_gztar_path), open(conductor_gztar_path, "rb"), mimetypes.guess_type(conductor_gztar_path, False)[0]),
                            # }
                            # status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                            # if not status_code == 200:
                            #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))

                            # # 作業状態通知送信
                            # body = {
                            #     "driver_id": driver_id,
                            #     "status": status
                            # }
                            # status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                            # if not status_code == 200:
                            #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            # break

                            # 結果データ更新->作業状態通知送信
                            status_code, response = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                            )
                            if not status_code == 200:
                                g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                            break
                        else:
                            # ログを残す
                            msg = g.appmsg.get_api_message('MSG-10953', [])
                            obj = storage_write()
                            obj.open(child_error_log_pass, 'a')
                            obj.write(msg)
                            obj.close()

                            # 結果データ更新
                            status = AnscConst.FAILURE
                            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                            # agent_child_mainのAppExceptionで異常時の共通処理
                            status_code = "MSG-10953"
                            msg_args = []
                            raise AppException(status_code, msg_args, msg_args)

                    else:
                        # rcファイルなし
                        # ログを残す
                        msg = g.appmsg.get_api_message('MSG-10953', [])
                        obj = storage_write()
                        obj.open(child_error_log_pass, 'a')
                        obj.write(msg)
                        obj.close()

                        # 結果データ更新
                        status = AnscConst.FAILURE
                        log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                        # agent_child_mainのAppExceptionで異常時の共通処理
                        status_code = "MSG-10953"
                        msg_args = []
                        raise AppException(status_code, msg_args, msg_args)
            else:
                # rcファイルの中身を確認する
                file_path = root_dir_path + "/artifacts/" + execution_no + "/rc"
                if os.path.isfile(file_path):
                    obj = storage_read()
                    obj.open(file_path)
                    rc_data = obj.read()
                    obj.close()
                    if rc_data == "0":
                        # 結果データ更新
                        status = AnscConst.COMPLETE
                        log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)
                        # # 各種ファイルをtarファイルにまとめる
                        # out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path = arcive_tar_data(organization_id, workspace_id, driver_id, execution_no, status)
                        # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                        # body = {
                        #     "driver_id": driver_id,
                        #     "status": status
                        # }
                        # form_data = {
                        #     "json_parameters": json.dumps(body),
                        #     "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                        #     "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                        #     "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                        #     "conductor_tar_data" : (os.path.basename(conductor_gztar_path), open(conductor_gztar_path, "rb"), mimetypes.guess_type(conductor_gztar_path, False)[0]),
                        # }
                        # status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                        # if not status_code == 200:
                        #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))

                        # # 作業状態通知送信
                        # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/execution/{status}"
                        # body = {}

                        # status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="POST", body=body)
                        # if not status_code == 200:
                        #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        # break

                        # 結果データ更新->作業状態通知送信
                        status_code, response = post_upload_file_and_status(
                            exastro_api, organization_id, workspace_id,
                            execution_no, status, driver_id
                        )
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        break
                    else:
                        # 結果データ更新
                        status = AnscConst.FAILURE

                        # agent_child_mainのAppExceptionで異常時の共通処理
                        # RCファイルの値が0ではありません。(X)
                        status_code = "MSG-10987"
                        msg_args = [rc_data]
                        raise AppException(status_code, msg_args, msg_args)
                else:
                    # rcファイルなし
                    # 結果データ更新
                    status = AnscConst.PROCESSING
                    # ログ更新
                    log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)
                    # 各種ファイルをtarファイルにまとめる
                    # out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path = arcive_tar_data(organization_id, workspace_id, driver_id, execution_no, status)
                    # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                    # body = {
                    #     "driver_id": driver_id,
                    #     "status": status
                    # }
                    # form_data = {
                    #     "json_parameters": json.dumps(body),
                    #     "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                    # }
                    # status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                    # if not status_code == 200:
                    #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))

                    # # 作業状態通知送信
                    # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                    # body = {
                    #     "driver_id": driver_id,
                    #     "status": status
                    # }

                    # status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                    # if not status_code == 200:
                    #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                    # continue

                    # 結果データ更新->作業状態通知送信
                    status_code, response = post_upload_file_and_status(
                        exastro_api, organization_id, workspace_id,
                        execution_no, status, driver_id
                    )
                    if not status_code == 200:
                        raise AppException("MSG-10957", [status_code, response], [status_code, response])
                    continue
        else:
            # 作業実行が停止中
            file_path = root_dir_path + "/out/forced_exec"
            if os.path.isfile(file_path):
                # 緊急停止
                # 結果データ更新
                status = AnscConst.SCRAM
                log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)
                # # 各種ファイルをtarファイルにまとめる
                # out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path = arcive_tar_data(organization_id, workspace_id, driver_id, execution_no, status)
                # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                # body = {
                #     "driver_id": driver_id,
                #     "status": status
                # }
                # form_data = {
                #     "json_parameters": json.dumps(body),
                #     "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                #     "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                #     "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                #     "conductor_tar_data" : (os.path.basename(conductor_gztar_path), open(conductor_gztar_path, "rb"), mimetypes.guess_type(conductor_gztar_path, False)[0]),
                # }
                # status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                # if not status_code == 200:
                #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))

                # # 作業状態通知送信
                # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                # body = {
                #     "driver_id": driver_id,
                #     "status": status
                # }

                # status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                # if not status_code == 200:
                #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                # break

                # 結果データ更新->作業状態通知送信
                status_code, response = post_upload_file_and_status(
                    exastro_api, organization_id, workspace_id,
                    execution_no, status, driver_id
                )
                if not status_code == 200:
                    g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                break
            else:
                # rcファイルの中身を確認する
                file_path = root_dir_path + "/artifacts/" + execution_no + "/rc"
                if os.path.isfile(file_path):
                    obj = storage_read()
                    obj.open(file_path)
                    rc_data = obj.read()
                    obj.close()
                    if rc_data == "0":
                        # 結果データ更新
                        status = AnscConst.COMPLETE
                        log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)
                        # # 各種ファイルをtarファイルにまとめる
                        # out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path = arcive_tar_data(organization_id, workspace_id, driver_id, execution_no, status)
                        # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
                        # body = {
                        #     "driver_id": driver_id,
                        #     "status": status
                        # }
                        # form_data = {
                        #     "json_parameters": json.dumps(body),
                        #     "out_tar_data" : (os.path.basename(out_gztar_path), open(out_gztar_path, "rb"), mimetypes.guess_type(out_gztar_path, False)[0]),
                        #     "parameters_tar_data" : (os.path.basename(parameters_gztar_path), open(parameters_gztar_path, "rb"), mimetypes.guess_type(parameters_gztar_path, False)[0]),
                        #     "parameters_file_tar_data" : (os.path.basename(parameters_file_gztar_path), open(parameters_file_gztar_path, "rb"), mimetypes.guess_type(parameters_file_gztar_path, False)[0]),
                        #     "conductor_tar_data" : (os.path.basename(conductor_gztar_path), open(conductor_gztar_path, "rb"), mimetypes.guess_type(conductor_gztar_path, False)[0]),
                        # }
                        # status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
                        # if not status_code == 200:
                        #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))

                        # # 作業状態通知送信
                        # endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
                        # body = {
                        #     "driver_id": driver_id,
                        #     "status": status
                        # }

                        # status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
                        # if not status_code == 200:
                        #     g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        # break

                        # 結果データ更新->作業状態通知送信
                        status_code, response = post_upload_file_and_status(
                            exastro_api, organization_id, workspace_id,
                            execution_no, status, driver_id
                        )
                        if not status_code == 200:
                            g.applogger.info(g.appmsg.get_log_message("MSG-10957", [status_code, response]))
                        break
                    else:
                        # 結果データ更新
                        status = AnscConst.FAILURE
                        log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                        # agent_child_mainのAppExceptionで異常時の共通処理
                        # RCファイルの値が0ではありません。(X)
                        status_code = "MSG-10987"
                        msg_args = [rc_data]
                        raise AppException(status_code, msg_args, msg_args)

                else:
                    # rcファイルなし
                    # ログを残す
                    msg = g.appmsg.get_api_message('MSG-10953', [])
                    obj = storage_write()
                    obj.open(child_error_log_pass, 'a')
                    obj.write(msg)
                    obj.close()

                    # 結果データ更新
                    status = AnscConst.FAILURE
                    log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                    # agent_child_mainのAppExceptionで異常時の共通処理
                    status_code = "MSG-10953"
                    msg_args = []
                    raise AppException(status_code, msg_args, msg_args)

    # ステータスファイル削除
    clear_execution_status_file(organization_id, workspace_id, driver_id, execution_no)

if __name__ == "__main__":
    agent_child_main()

def decompress_tar_file(organization_id, workspace_id, driver_id, dir_path, file_name, execution_no):
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

    # tarファイル解凍先
    tar_path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/tar"

    # in,outのtarファイルを展開
    with tarfile.open(dir_path + file_name, 'r:gz') as tar:
        tar.extractall(path=tar_path)

    # 展開したファイルの一覧を取得
    lst = os.listdir(tar_path)

    # in/out親ディレクトリパス
    root_dir_path = f"/storage/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"

    # 展開したファイルを移動する
    move_dir = ""
    for dir_name in lst:
        if dir_name == execution_no:
            sublst = os.listdir(f"{tar_path}/{dir_name}")
            for dir_name in sublst:
                if dir_name == "in":
                    # inディレクトリの中身取得
                    in_lst = os.listdir(f"{tar_path}/{execution_no}/{dir_name}")
                    for in_dir_name in in_lst:
                        if in_dir_name in ["inventory", "env", "builder_executable_files", "runner_executable_files"]:
                            # 1つ上の階層へ移動
                            shutil.move(f"{tar_path}/{execution_no}/{dir_name}/{in_dir_name}", f"{tar_path}/{execution_no}")
                            # inventory,.env.,builder_executable_files,runner_executable_filesディレクトリの移動
                            join_path = f"{tar_path}/{execution_no}/{in_dir_name}"
                            shutil.move(join_path, root_dir_path)
                    # inディレクトリの移動先
                    move_dir = root_dir_path + "/project"
                    join_path = f"{tar_path}/{execution_no}/{dir_name}"
                    shutil.move(join_path, move_dir)
                elif dir_name in ["out", ".tmp", "tmp"]:
                    # out,.tmp.,tmpディレクトリの移動
                    join_path = f"{tar_path}/{execution_no}/{dir_name}"
                    shutil.move(join_path, root_dir_path)
        elif dir_name == "conductor":
            # conductorディレクトリの移動先
            join_path = f"{tar_path}/{dir_name}"
            shutil.move(join_path, root_dir_path)

    # 作業ディレクトリ削除
    clear_execution_tmpdir(organization_id, workspace_id, driver_id, execution_no)

def log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id):
    """
    runnerのログファイルをマージする
    ARGS:
        exec_log_pass: 作業状態確認に表示される実行ログ
        error_log_pass: 作業状態確認に表示されるエラーログ
        parent_error_log_pass: 親プロ用エラーログ
        child_exec_log_pass: 子プロ用実行ログ
        child_error_log_pass: 子プロ用エラーログ
        runner_exec_log_pass: runner用実行ログ
        runner_error_log_pass: runner用エラーログ
    """

    # runner実行ログ読み取り
    if os.path.isfile(runner_exec_log_pass):
        obj = storage_read()
        obj.open(runner_exec_log_pass)
        text =  obj.read()
        obj.close()

        # exec.logへ追記
        obj = storage_write()
        obj.open(exec_log_pass, "a")
        obj.write(text)
        obj.close()

    # 子プロ用実行ログ読み取り
    if os.path.isfile(child_exec_log_pass):
        obj = storage_read()
        obj.open(child_exec_log_pass)
        text =  obj.read()
        obj.close()

        # exec.logへ追記
        obj = storage_write()
        obj.open(exec_log_pass, "a")
        obj.write(text)
        obj.close()

    # runnerエラーログ読み取り
    if os.path.isfile(runner_error_log_pass):
        obj = storage_read()
        obj.open(runner_error_log_pass)
        text =  obj.read()
        obj.close()

        # error.logへ追記
        obj = storage_write()
        obj.open(error_log_pass, "a")
        obj.write(text)
        obj.close()

    # 子プロ用エラーログ読み取り
    if os.path.isfile(parent_error_log_pass):
        obj = storage_read()
        obj.open(parent_error_log_pass)
        text =  obj.read()
        obj.close()

        # error.logへ追記
        obj = storage_write()
        obj.open(error_log_pass, "a")
        obj.write(text)
        obj.close()

    # 子プロ用エラーログ読み取り
    if os.path.isfile(child_error_log_pass):
        obj = storage_read()
        obj.open(child_error_log_pass)
        text =  obj.read()
        obj.close()

        # error.logへ追記
        obj = storage_write()
        obj.open(error_log_pass, "a")
        obj.write(text)
        obj.close()

    # 特定のキーワードで改行しansibleのログを見やすくする
    if os.path.isfile(exec_log_pass):
        obj = storage_read()
        obj.open(exec_log_pass, "r")
        log_data = obj.read()
        obj.close()

        if driver_id == "pioneer":
            # ログ(", ")  =>  (",\n")を改行する
            log_data = log_data.replace("\", \"", "\",\n\"")
            # 改行文字列\r\nを改行コードに置換える
            log_data = log_data.replace("\\r\\n", "\n")
            # python改行文字列\\nを改行コードに置換える
            log_data = log_data.replace("\\n", "\n")
        else:
            # ログ(", ")  =>  (",\n")を改行する
            log_data = log_data.replace("\", \"", "\",\n\"")
            # ログ(=> {)  =>  (=> {\n)を改行する
            log_data = log_data.replace("=> {", "=> {\n")
            # ログ(, ")  =>  (,\n")を改行する
            log_data = log_data.replace(", \"", ",\n\"")
            # 改行文字列\r\nを改行コードに置換える
            log_data = log_data.replace("\\r\\n", "\n")
            # python改行文字列\\nを改行コードに置換える
            log_data = log_data.replace("\\n", "\n")
    else:
        log_data = ""

    if os.path.isfile(exec_log_pass):
        obj = storage_write()
        obj.open(exec_log_pass, "w")
        obj.write(log_data)
        obj.close()

def clear_execution_tmpdir(organization_id, workspace_id, driver_id, execution_no):
    _path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}"
    if os.path.isdir(_path):
        shutil.rmtree(_path)
        g.applogger.info(f"clear_execution_tmpdir: ({_path})")

def clear_execution_status_file(organization_id, workspace_id, driver_id, execution_no):
    _x, _path = get_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    if os.path.isfile(_path):
        os.remove(_path)
        g.applogger.info(f"clear_execution_status_file: ({_path})")

def get_status_file_path(organization_id, workspace_id, driver_id, execution_no):
    status_file_dir_path = f"/storage/{organization_id}/{workspace_id}/ag_ansible_execution/status/{driver_id}"
    status_file_path = f"{status_file_dir_path}/{execution_no}"
    return status_file_dir_path, status_file_path,

def post_upload_file_and_status(exastro_api, organization_id, workspace_id, execution_no, status, driver_id):

    status_code, response = (000, {})

    # 各種ファイルをtarファイルにまとめる
    out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_dir_path = \
        arcive_tar_data(organization_id, workspace_id, driver_id, execution_no, status)

    if exastro_api is None:
        # 環境変数の取得
        baseUrl = os.environ["EXASTRO_URL"]
        refresh_token = os.environ['EXASTRO_REFRESH_TOKEN']

        # ITAのAPI呼び出しモジュール
        exastro_api = Exastro_API(
            base_url=baseUrl,
            refresh_token=refresh_token
        )
        exastro_api.get_access_token(organization_id, refresh_token)

    # パラメータ
    body = {
        "driver_id": driver_id,
        "status": status
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
    if os.path.isfile(conductor_dir_path):
        form_data["conductor_tar_data"] =  (
            os.path.basename(conductor_dir_path),
            open(conductor_dir_path, "rb"),
            mimetypes.guess_type(conductor_dir_path, False)[0])

    # 実行中の場合はjson_parameters、out_tar_data以外除外
    if status == AnscConst.PROCESSING:
        accept_key = [
            "json_parameters",
            "out_tar_data"
        ]
        for k, v in form_data.keys():
            if k not in accept_key:
                del form_data[k]

    # 結果データ更新
    status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
    if not status_code == 200:
        return status_code, response

    # 作業状態通知送信
    g.applogger.info(g.appmsg.get_log_message("MSG-10956", []))
    status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
    if not status_code == 200:
        return status_code, response

    return status_code, response