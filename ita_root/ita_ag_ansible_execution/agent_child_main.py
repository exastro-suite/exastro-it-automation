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
import pathlib

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.common.storage_access import storage_read, storage_write
from common_libs.ag.util import app_exception, exception
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
    runtime_data_del = args[6]
    global ansc_const
    global driver_error_log_file

    g.applogger.set_tag("EXECUTION_NO", execution_no)

    # MSG-10720 [処理]プロシージャ開始 (作業No.:{})
    g.applogger.debug(g.appmsg.get_log_message("MSG-10720", [execution_no]))

    try:
        agent_child()
    except AppException as e:
        app_exception(e)
        # 異常時の共通処理
        # 結果データ更新+作業状態通知送信
        status = AnscConst.FAILURE
        status_code, response, error_code, error_arg = post_upload_file_and_status(
            None, organization_id, workspace_id,
            execution_no, status, driver_id
        )
        if not status_code == 200:
            g.applogger.info(g.appmsg.get_log_message(error_code, error_arg))
    except Exception as e:
        exception(e)
        # 異常時の共通処理
        # 結果データ更新+作業状態通知送信
        status = AnscConst.FAILURE
        status_code, response, error_code, error_arg = post_upload_file_and_status(
            None, organization_id, workspace_id,
            execution_no, status, driver_id
        )
        if not status_code == 200:
            g.applogger.info(g.appmsg.get_log_message(error_code, error_arg))
    finally:
        # ステータスファイルの削除
        delete_status_file(organization_id, workspace_id, driver_id, execution_no)
        # /tmpのゴミ掃除
        clear_execution_tmpdir(organization_id, workspace_id, driver_id, execution_no)
        # 作業ディレクトリ削除
        clear_execution_dir(organization_id, workspace_id, driver_id, execution_no, runtime_data_del)
    return 0

def agent_child():
    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id", …, …]
    args = sys.argv
    organization_id = args[1]
    workspace_id = args[2]
    execution_no = args[3]
    driver_id = args[4]
    build_type = args[5]
    runtime_data_del = args[6]
    # 再起動の処理は実装しない
    strat_mode = args[7]

    # in/out親ディレクトリパス
    storagepath = os.environ.get('STORAGEPATH')
    root_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"
    # rcファイルディレクトリパス
    rc_dir_path = storagepath + "/" + organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no + "/artifacts/" + execution_no

    # ログファイルパス
    exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass = get_log_file_path(organization_id, workspace_id, driver_id, execution_no)

    # builder Runnerのshellで使用する環境変数設定
    project_base_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"
    os.environ['PROJECT_BASE_DIR'] = project_base_path

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
    g.applogger.info(g.appmsg.get_log_message("MSG-10992", [workspace_id, execution_no]))
    query= {"driver_id": driver_id}
    status_code, response = get_execution_populated_data(organization_id, workspace_id, exastro_api, execution_no, query=query)
    if not status_code == 200:
        g.applogger.info(g.appmsg.get_log_message("MSG-10993", [workspace_id, execution_no, status_code, response]))
        raise AppException("MSG-10993", [workspace_id, execution_no, status_code, response], [workspace_id, execution_no, status_code, response])

    # tarファイル解凍
    dir_path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/{execution_no}/"
    retry_rmtree(dir_path) if os.path.isdir(dir_path) else None  # noqa: F405
    retry_makedirs(dir_path)  # noqa: F405
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
    if not os.path.isfile(exec_log_pass):
        p = pathlib.Path(exec_log_pass)
        p.touch()

    if not os.path.isfile(error_log_pass):
        p = pathlib.Path(error_log_pass)
        p.touch()

    if not os.path.isfile(child_exec_log_pass):
        p = pathlib.Path(child_exec_log_pass)
        p.touch()

    if not os.path.isfile(child_error_log_pass):
        p = pathlib.Path(child_error_log_pass)
        p.touch()

    # 実行環境構築方法がITAの場合builder.sh実行
    if build_type == "2":
        builder_result = True
        try:
            g.applogger.debug(g.appmsg.get_log_message( "MSG-11007", [workspace_id, execution_no]))
            cmd = ["sh", f"{root_dir_path}/builder_executable_files/builder.sh"]

            with open(child_error_log_pass, 'w') as fp:
                ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            exception(e)
            builder_result = False

        except Exception as e:
            exception(e)
            builder_result = False

        finally:
            # builder.shの実行に失敗した場合完了(異常)
            if builder_result is False:
                # ansible-builderの実行に失敗しました。(builder_executable_files/builder.sh)
                erro_log = g.appmsg.get_log_message("MSG-10986", ["ansible-builder", "builder_executable_files/builder.sh"])
                error_log_write(child_error_log_pass, erro_log)

                status = AnscConst.FAILURE
                log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                status_code = "MSG-10986"
                msg_args = ["ansible-builder", "builder_executable_files/builder.sh"]
                raise AppException(status_code, msg_args, msg_args)
            else:
                # ログファイルクリア
                with open(child_error_log_pass, "w") as f:
                    pass

    # start.sh実行
    try:
        g.applogger.debug(g.appmsg.get_log_message( "MSG-11008", [workspace_id, execution_no]))
        start_result = True
        cmd = ["sh", f"{root_dir_path}/runner_executable_files/start.sh"]
        with open(child_error_log_pass, 'a') as fp:
            ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        exception(e)
        start_result = False

    except Exception as e:
        exception(e)
        start_result = False
    finally:
        # start.shの実行に失敗した場合完了(異常)
        if start_result is False:
            # ログ更新
            erro_log = g.appmsg.get_log_message("MSG-10986", ["ansible-runner", "runner_executable_files/start.sh"])
            error_log_write(child_error_log_pass, erro_log)

            status = AnscConst.FAILURE
            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

            # agent_child_mainのAppExceptionで異常時の共通処理
            status_code = "MSG-10986"
            msg_args = ["ansible-runner", "runner_executable_files/start.sh"]
            raise AppException(status_code, msg_args, msg_args)

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
            # runnerが終るとaliveの戻りが0以外になるので、正常とする。
            # ログをクリアする
            with open(child_error_log_pass,"w") as f:
                pass
            alive_result = True
        except Exception as e:
            exception(e)
            alive_result = False

        # runner作業実行状態判定
        g.applogger.debug(g.appmsg.get_log_message( "MSG-11009", [workspace_id, execution_no, alive_result]))
        if alive_result is True:
            # runner作業中
            file_path = root_dir_path + "/out/forced.txt"
            # 緊急停止ボタンがクリックされたか判定
            if os.path.isfile(file_path):
                # 緊急停止ボタン クリック
                g.applogger.debug(g.appmsg.get_log_message( "MSG-11010", [workspace_id, execution_no, "True"]))
                try:
                    stop_result = True
                    cmd = ["sh", f"{root_dir_path}/runner_executable_files/stop.sh"]
                    with open(child_error_log_pass, 'a') as fp:
                        ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    exception(e)
                    stop_result = False

                except Exception as e:
                    exception(e)
                    stop_result = False
                finally:
                    g.applogger.debug(g.appmsg.get_log_message( "MSG-11011", [workspace_id, execution_no, stop_result]))
                    if stop_result is True:
                        # 緊急停止に成功
                        # runner停止完了
                        # forced_exec作成
                        file_path = root_dir_path + "/out/forced_exec"
                        f = open(file_path, 'w')
                        f.close

                        # 結果データ更新 作業状態:緊急停止
                        status = AnscConst.SCRAM
                        log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                        # 結果データ更新->作業状態通知送信
                        status_code, response, error_code, error_arg = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                        )
                        if not status_code == 200:
                            raise AppException(error_code, error_arg)

                        break

                    else:
                        # 緊急停止に失敗
                        g.applogger.info(g.appmsg.get_log_message("MSG-10986", ["ansibe_runner", "runner_executable_files/stop.sh"]))

                        # rcファイルの中身を確認する
                        rc_data = get_runner_rc_status_file(root_dir_path, execution_no)

                        if rc_data is False:
                            # rcファイルなし
                            # ログを残す
                            runner_rc_status_file_none_log(child_error_log_pass, workspace_id, execution_no, "1")

                            # 結果データ更新 ステータス:完了(異常)
                            status = AnscConst.FAILURE
                            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                            # 結果データ更新->作業状態通知送信
                            status_code, response, error_code, error_arg = post_upload_file_and_status(
                                                        exastro_api, organization_id, workspace_id,
                                                        execution_no, status, driver_id
                                                    )
                            if not status_code == 200:
                                raise AppException(error_code, error_arg)

                            break

                        elif rc_data == "0":
                            # 結果データ更新 作業状態:完了
                            status = AnscConst.COMPLETE
                            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                            # 結果データ更新->作業状態通知送信
                            status_code, response, error_code, error_arg = post_upload_file_and_status(
                                                        exastro_api, organization_id, workspace_id,
                                                        execution_no, status, driver_id
                                                    )
                            if not status_code == 200:
                                raise AppException(error_code, error_arg)

                            break
                        else:
                            # 結果データ更新 作業状態:完了(異常)
                            status = AnscConst.FAILURE
                            log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                            # 結果データ更新->作業状態通知送信
                            status_code, response, error_code, error_arg = post_upload_file_and_status(
                                                        exastro_api, organization_id, workspace_id,
                                                        execution_no, status, driver_id
                                                    )
                            if not status_code == 200:
                                raise AppException(error_code, error_arg)

                            break

            else:
                # 緊急停止ボタンは未クリック
                g.applogger.debug(g.appmsg.get_log_message( "MSG-11010", [workspace_id, execution_no, "False"]))
                rc_data = get_runner_rc_status_file(root_dir_path, execution_no)
                if rc_data is False:
                    # rcファイルなし

                    # 結果データ更新 ステータス:実行中
                    status = AnscConst.PROCESSING
                    log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                    # 結果データ更新->作業状態通知送信
                    status_code, response, error_code, error_arg = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                    )
                    if not status_code == 200:
                        raise AppException(error_code, error_arg)

                    continue

                elif rc_data == "0":
                    # 結果データ更新 ステータス:完了
                    status = AnscConst.COMPLETE
                    log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                    # 結果データ更新->作業状態通知送信
                    status_code, response, error_code, error_arg = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                    )
                    if not status_code == 200:
                        raise AppException(error_code, error_arg)

                    break

                else:
                    # 結果データ更新 ステータス:完了(異常)
                    status = AnscConst.FAILURE
                    log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                    # 結果データ更新->作業状態通知送信
                    status_code, response, error_code, error_arg = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                    )
                    if not status_code == 200:
                        raise AppException(error_code, error_arg)

                    break
        else:
            # runner作業状態取得失敗
            rc_data = get_runner_rc_status_file(root_dir_path, execution_no)
            if rc_data is False:
                # rcファイルなし
                # ログを残す
                erro_log = g.appmsg.get_log_message("MSG-10986", ["ansible_runner", "runner_executable_files/alive.sh"])
                error_log_write(child_error_log_pass, erro_log)
                g.applogger.info(erro_log)

                runner_rc_status_file_none_log(child_error_log_pass, workspace_id, execution_no, "2")

                # 結果データ更新 ステータス:完了(異常)
                status = AnscConst.FAILURE
                log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                # 結果データ更新->作業状態通知送信
                status_code, response, error_code, error_arg = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                )
                if not status_code == 200:
                    raise AppException(error_code, error_arg)

                break

            elif rc_data == "0":
                # 結果データ更新 ステータス:完了
                status = AnscConst.COMPLETE
                log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                # 結果データ更新->作業状態通知送信
                status_code, response, error_code, error_arg = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                )
                if not status_code == 200:
                    raise AppException(error_code, error_arg)

                break

            else:
                # 結果データ更新 ステータス:完了(異常)
                status = AnscConst.FAILURE
                log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id)

                # 結果データ更新->作業状態通知送信
                status_code, response, error_code, error_arg = post_upload_file_and_status(
                                exastro_api, organization_id, workspace_id,
                                execution_no, status, driver_id
                )
                if not status_code == 200:
                    raise AppException(error_code, error_arg)

                break

    # ステータスファイルの削除
    delete_status_file(organization_id, workspace_id, driver_id, execution_no)

if __name__ == "__main__":
    agent_child_main()


def get_runner_rc_status_file(root_dir_path, execution_no):
    rc_data = False
    file_path = root_dir_path + "/artifacts/" + execution_no + "/rc"
    if os.path.isfile(file_path):
        obj = storage_read()
        with open(file_path) as f:
            rc_data = f.read()
    return rc_data


def runner_rc_status_file_none_log(child_error_log_path, workspace_id, execution_no, location):
    # MSG-10953  rcファイルがありません。
    g.applogger.info(g.appmsg.get_log_message("MSG-10953", [workspace_id, execution_no, location]))
    msg = g.appmsg.get_log_message('MSG-10953', [workspace_id, execution_no, location])
    error_log_write(child_error_log_path, msg)


def error_log_write(log_file, msg):
    with open(log_file, 'a') as f:
        f.write(msg + "\n")


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
    storagepath = os.environ.get('STORAGEPATH')
    root_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"

    # 移動前に作業用ディレクトリを作成しておく
    retry_makedirs(root_dir_path)  # noqa: F405

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
                            retry_move(f"{tar_path}/{execution_no}/{dir_name}/{in_dir_name}", f"{tar_path}/{execution_no}")  # noqa: F405
                            # inventory,.env.,builder_executable_files,runner_executable_filesディレクトリの移動
                            join_path = f"{tar_path}/{execution_no}/{in_dir_name}"
                            retry_move(join_path, root_dir_path)  # noqa: F405
                    # inディレクトリの移動先
                    move_dir = root_dir_path + "/project"
                    join_path = f"{tar_path}/{execution_no}/{dir_name}"
                    retry_move(join_path, move_dir)  # noqa: F405
                elif dir_name in ["out", ".tmp", "tmp"]:
                    # out,.tmp.,tmpディレクトリの移動
                    join_path = f"{tar_path}/{execution_no}/{dir_name}"
                    retry_move(join_path, root_dir_path)  # noqa: F405
        elif dir_name == "conductor":
            # conductorディレクトリの移動先
            join_path = f"{tar_path}/{dir_name}"
            retry_move(join_path, root_dir_path)  # noqa: F405

    # 作業ディレクトリ削除
    clear_execution_tmpdir(organization_id, workspace_id, driver_id, execution_no)


def clear_execution_tmpdir(organization_id, workspace_id, driver_id, execution_no):
    _path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}"
    if os.path.isdir(_path):
        retry_rmtree(_path)  # noqa: F405
        g.applogger.debug(f"remove execution tmp dirs. (path:{_path})")

def clear_execution_dir(organization_id, workspace_id, driver_id, execution_no, runtime_data_del):
    # インターフェース情報の実行時削除がTrueの場合
    if runtime_data_del == "1":
        storagepath = os.environ.get('STORAGEPATH')
        _path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"
        if os.path.isdir(_path):
            retry_rmtree(_path)  # noqa: F405
            g.applogger.debug(f"remove execution dirs. (path:{_path})")
        _path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}"
        if os.path.isdir(_path):
            retry_rmtree(_path)  # noqa: F405
            g.applogger.debug(f"remove execution dirs. (path:{_path})")


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
        for k in form_data.keys():
            if k not in accept_key:
                del form_data[k]

    # 結果データ更新
    g.applogger.info(g.appmsg.get_log_message("MSG-10994", [workspace_id, execution_no]))
    status_code, response = post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body, form_data=form_data)
    if not status_code == 200:
        return status_code, response, "MSG-10995", [workspace_id, execution_no, status_code, response]

    # 作業状態通知送信
    g.applogger.info(g.appmsg.get_log_message("MSG-10990", [workspace_id, execution_no, status]))
    status_code, response = post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body)
    if not status_code == 200:
        return status_code, response, "MSG-10991", [workspace_id, execution_no, status, status_code, response]


    # 作業状態通知のレスポンスで緊急停止フラグが設定されている場合、forced.txtファイル作成
    chk_emergency_stop(response, organization_id, workspace_id, driver_id, execution_no)
    return status_code, response, "", []

def chk_emergency_stop(response, organization_id, workspace_id, driver_id, execution_no):
    storagepath = os.environ.get('STORAGEPATH')
    root_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"
    # 作業状態通知のレスポンスで緊急停止ありの場合
    if response['data']['SCRAM_STATUS'] == "1":
        g.applogger.debug(g.appmsg.get_log_message("MSG-11012", [workspace_id, execution_no]))
        p = pathlib.Path(root_dir_path + "/out/forced.txt")
        p.touch()

