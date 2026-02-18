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
"""
ita_ag_ansible_execution agent common function module
"""
from flask import g
import traceback
import os
import datetime
import tarfile
import uuid
import glob
import shutil
import shlex
import subprocess
import json
import mimetypes
import re

from common_libs.common.exception import AppException
from common_libs.common.util import arrange_stacktrace_format, retry_makedirs, retry_chmod, retry_rmtree, retry_copy, retry_copytree, retry_remove
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst


def get_agent_id(organization_id, workspace_id, agent_name):
    """
        agent_idの取得・永続指定領域になければ、生成する
    Returns:
        agent_id
    """
    storagepath = os.environ.get('STORAGEPATH')
    version_file_path = f"{storagepath}/agent_id"
    version_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/ag_ansible_execution/{agent_name}"
    version_file_name = "agent_id"
    version_file_path = f"{version_dir_path}/{version_file_name}"
    if os.path.isfile(version_file_path):
        with open(version_file_path, mode='r') as f:
            agent_id= f.read()
    else:
        retry_makedirs(version_dir_path)
        agent_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        with open(version_file_path, mode='w') as f:
            f.write(agent_id)
    return agent_id

def get_agent_version():
    """
        agent_versionの取得
    Returns:
        agent_version
    """
    version_file_path = "{}{}".format(g.get("PYTHONPATH"),"VERSION.txt")
    if os.path.isfile(version_file_path):
        with open(version_file_path, mode='r') as f:
            agent_version = f.read()
            # 末尾の改行があった場合、取り除く
            agent_version = agent_version.strip()
    else:
        agent_version = "2.5.0" #####
    return agent_version

def delete_status_file(organization_id, workspace_id, driver_id, execution_no):
    """
        ステータスファイル関連の削除
    """
    clear_execution_status_file(organization_id, workspace_id, driver_id, execution_no)
    clear_execution_parameters_file(organization_id, workspace_id, driver_id, execution_no)
    clear_execution_restart_status_file(organization_id, workspace_id, driver_id, execution_no)

def get_upload_file_info(organization_id, workspace_id, driver_id, execution_no):
    """
        作業状態通知送信(ファイル)用のアーカイブ作成
    """
    storagepath = os.environ.get('STORAGEPATH')
    upload_file_info = {
        "out_data": None,
        "conductor_data": None
    }
    out_data_dir = f"{storagepath}/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/out"
    conductor_dir = f"{storagepath}/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/conductor"
    _uuid = str(uuid.uuid4())
    tmp_dir_name = f"/tmp/{organization_id}/{workspace_id}/{_uuid}"
    retry_makedirs(tmp_dir_name)

    try:
        # 対象ファイルを tmpへcopy
        # ZIP or TAR
        pass
    finally:
        # 一時作業用削除
        pass


def retry_api_call(exastro_api, endpoint, mode="json" ,method="POST", body=None, query=None, files=None, data=None, fields=None, retry=3):
    """
        api_requestのリトライ用
    Args:
        exastro_api: Exastro_API()
        endpoint: endpoint
        mode: mode, Defaults to json , (json, form, stream, form_stream)
        method: method, Defaults to POST,
        body: {} Defaults to None
        query: {key: value}, Defaults to None
        files: {file: file_data}, Defaults to None
        data: {}, Defaults to None
        fields: { key: json.dumps(xxx) or (filename, open(filepath,'rb'), content_type)}, Defaults to None
        retry: retry, Defaults to 3
    Returns:
        status_code:
        response:
    """
    status_code = None
    response = None

    for t in range(int(retry)):
        try:
            if mode == "json":
                status_code, response = exastro_api.api_request(
                    method,
                    endpoint,
                    body=body,
                    query=query
                )
            elif mode == "form":
                status_code, response = exastro_api.api_request_formdata(
                    method,
                    endpoint,
                    body=body,
                    query=query,
                    files=files,
                    data=data
                )
            elif mode == "stream":
                status_code, response = exastro_api.api_request_stream(
                    method,
                    endpoint,
                    body=body,
                    query=query,
                    files=files,
                    data=data
                )
            elif mode == "form_stream":
                status_code, response = exastro_api.api_request_formdata_stream_file(
                    method,
                    endpoint,
                    query=query,
                    fields=fields
                )
            if status_code == 200:
                break
            else:
                pass
                g.applogger.info(f"{endpoint=} {status_code=} {response=} retry:{t}")

        except Exception as e:
            g.applogger.info(f"{endpoint=} {status_code=} retry:{t} \n {e}")

    return status_code, response,


def post_agent_version(organization_id, workspace_id, exastro_api, body=None, query=None, retry=3):
    """
        バージョン通知: agent_main
    Args:
        organization_id : organization_id
        workspace_id : workspace_id
        exastro_api : Exastro_API()
        body: {}, Defaults to None
        query: {key: value}, Defaults to None
        retry: retry. Defaults to 3.
    Returns:
        status_code:
        response:
    """
    endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/version"
    body = {
        # "agent_id": get_agent_id(organization_id, workspace_id, os.environ["AGENT_NAME"]),
        "agent_name": os.environ["AGENT_NAME"],
        "version": get_agent_version(),
    }
    status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="POST", body=body, retry=retry)
    # response["data"] = {"version_diff": boolean}
    return status_code, response

def post_unexecuted_instance(organization_id, workspace_id, exastro_api, body=None, query=None, retry=3):
    """
        未実行インスタンス取得: agent_main
    Args:
        organization_id : organization_id
        workspace_id : workspace_id
        exastro_api : Exastro_API()
        retry: retry. Defaults to 3.
    Returns:
        status_code:
        response:
    """
    endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/instance/unexecuted"
    status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="POST", body=body, retry=retry)
    return status_code, response

def post_notification_execution(organization_id, workspace_id, exastro_api, body=None, query=None, retry=3):
    """
        作業中通知: agent_main
    Args:
        organization_id : organization_id
        workspace_id : workspace_id
        exastro_api : Exastro_API()
        body: {}, Defaults to None
        query: {key: value}, Defaults to None
        retry: retry. Defaults to 3.
    Returns:
        status_code:
        response:
    """
    endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/notification/execution"
    status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="POST", body=body, retry=retry)
    return status_code, response

def get_execution_populated_data(organization_id, workspace_id, exastro_api, execution_no, body=None, query=None, retry=5):
    """
        投入データ取得: agent_child_main
    Args:
        organization_id : organization_id
        workspace_id : workspace_id
        exastro_api : Exastro_API()
        execution_no: execution_no
        body: {}, Defaults to None
        query: {key: value}, Defaults to None
        retry: retry. Defaults to 3.
    Returns:
        status_code:
        response:
    """
    endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/populated_data"
    status_code, response = retry_api_call(exastro_api, endpoint, mode="stream", method="GET", query=query, retry=retry)
    return status_code, response

def post_update_execution_status(organization_id, workspace_id, exastro_api, execution_no, body=None, query=None, retry=3):
    """
        作業状態通知: agent_main / agent_child_main
    Args:
        organization_id : organization_id
        workspace_id : workspace_id
        exastro_api : Exastro_API()
        execution_no: execution_no
        body: {}, Defaults to None
        query: {key: value}, Defaults to None
        retry: retry. Defaults to 3.
    Returns:
        status_code:
        response:
    """
    endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/notification/status"
    status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="POST", body=body, query=query, retry=retry)
    return status_code, response

def post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body=None, query=None, form_data=None, retry=5):
    """
        作業状態通知(ファイル): 結果データ受け取り・更新 : agent_child_main
    Args:
        organization_id : organization_id
        workspace_id : workspace_id
        exastro_api : Exastro_API()
        execution_no: execution_no
        body: {}, Defaults to None
        query: {key: value}, Defaults to None
        fields: { key: json.dumps(xxx) or (filename, open(filepath,'rb'), content_type)}, Defaults to None
        retry: retry. Defaults to 3.
    Returns:
        status_code:
        response:
    """
    endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/ansible_execution_agent/{execution_no}/result_data"
    try:
        status_code, response = retry_api_call(exastro_api, endpoint, mode="form_stream", method="POST", fields=form_data, retry=retry)
    except Exception as e:
        raise e
    finally:
        pass
    return status_code, response

def arcive_tar_data(organization_id, workspace_id, driver_id, execution_no, status, mode="child"):
    """
        作業状態通知(ファイル): 結果データ受け取り・更新 : agent_child_main
    Args:
        driver_id : ドライバーID
        execution_no: 作業番号
        status: ステータス
        mode: パス指定のモード, Defaults to "child".
            child: agent_child_main
            parent: agent_main
    Returns:
        out_gztar_path: outディレクトリtarファイルパス
        parameters_gztar_path: parametersディレクトリtarファイルパス
        parameters_file_gztar_path: parameters_fileディレクトリtarファイルパス
        conductor_gztar_path: conductor_fileディレクトリtarファイルパス
    """
    storagepath = os.environ.get('STORAGEPATH')
    if mode == "child":
        # outディレクトリパス
        out_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}/out"
        # inディレクトリパス
        in_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}/project"
        # conductorディレクトリパス
        conductor_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}/conductor"
        # 作業用ディレクトリパス
        tmp_dir_path = "/tmp/" +  organization_id + "/" + workspace_id + "/driver/ansible/" + driver_id + "/" + execution_no
    elif mode == "parent":
        _base_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"
        _tmp_path = _base_path.replace(storagepath, "/tmp/")
        # outディレクトリパス
        out_dir_path = f"{_base_path}/out"
        # inディレクトリパス
        in_dir_path = f"{_base_path}/in"
        # conductorディレクトリパス
        conductor_dir_path = f"{_base_path}/conductor"
        # 作業用ディレクトリパス
        tmp_dir_path = _tmp_path

    # 作業ディレクトリがなければ作成しておく
    retry_makedirs(tmp_dir_path)
    # /out無ければ空で作成しておく
    retry_makedirs(out_dir_path)
    # parameters・parameters_file無ければ空で作成しておく
    retry_makedirs(in_dir_path + "/_parameters")
    retry_makedirs(in_dir_path + "/_parameters_file")
    # /conductor無ければ空で作成しておく
    retry_makedirs(conductor_dir_path)

    out_tar_dir_path = tmp_dir_path + "/out"
    out_gztar_path = out_tar_dir_path + ".tar.gz"
    parameters_tar_dir_path = ""
    parameters_gztar_path = ""
    parameters_file_tar_dir_path = ""
    parameters_file_gztar_path = ""
    conductor_tar_dir_path = ""
    conductor_gztar_path = ""

    # 作業ディレクトリ削除してから処理実行
    if os.path.exists(out_tar_dir_path):
        retry_rmtree(out_tar_dir_path)

    # ステータスが実行中、実行中(遅延)の場合
    if status == AnscConst.PROCESSING or status == AnscConst.PROCESS_DELAYED:
        retry_makedirs(out_tar_dir_path)

        # ログファイルをtarファイルにまとめる
        retry_copy(out_dir_path + "/exec.log", out_tar_dir_path)
        retry_copy(out_dir_path + "/error.log", out_tar_dir_path)
        with tarfile.open(out_gztar_path, "w:gz") as tar:
            tar.add(out_tar_dir_path, arcname="")

    # ステータスが完了、完了(異常)、緊急停止場合
    else:
        parameters_tar_dir_path = tmp_dir_path + "/_parameters"
        parameters_gztar_path = parameters_tar_dir_path + ".tar.gz"
        parameters_file_tar_dir_path = tmp_dir_path + "/_parameters_file"
        parameters_file_gztar_path = parameters_file_tar_dir_path + ".tar.gz"
        conductor_tar_dir_path = tmp_dir_path + "/conductor"
        conductor_gztar_path = conductor_tar_dir_path + ".tar.gz"

        # 作業ディレクトリ削除してから処理実行
        if os.path.exists(parameters_tar_dir_path):
            retry_rmtree(parameters_tar_dir_path)
        if os.path.exists(parameters_file_tar_dir_path):
            retry_rmtree(parameters_file_tar_dir_path)
        if os.path.exists(conductor_tar_dir_path):
            retry_rmtree(conductor_tar_dir_path)

        retry_makedirs(out_tar_dir_path)
        retry_makedirs(parameters_tar_dir_path)
        retry_makedirs(parameters_file_tar_dir_path)

        # outディレクトリをtarファイルにまとめる
        retry_copytree(out_dir_path, out_tar_dir_path)
        with tarfile.open(out_gztar_path, "w:gz") as tar:
            tar.add(out_tar_dir_path, arcname="")


        # parameters・parameters_fileをtarファイルにまとめる
        retry_copytree(in_dir_path + "/_parameters", parameters_tar_dir_path)
        retry_copytree(in_dir_path + "/_parameters_file", parameters_file_tar_dir_path)
        with tarfile.open(parameters_gztar_path, "w:gz") as tar:
            tar.add(parameters_tar_dir_path, arcname="")
        with tarfile.open(parameters_file_gztar_path, "w:gz") as tar:
            tar.add(parameters_file_tar_dir_path, arcname="")

        # conductorディレクトリをtarファイルにまとめる
        if os.path.exists(conductor_dir_path):
            retry_makedirs(conductor_tar_dir_path)
            retry_copytree(conductor_dir_path, conductor_tar_dir_path)
            with tarfile.open(conductor_gztar_path, "w:gz") as tar:
                tar.add(conductor_tar_dir_path, arcname="")

    return out_gztar_path, parameters_gztar_path, parameters_file_gztar_path, conductor_gztar_path


def clear_execution_status_file(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ起動状態ファイル削除
    """
    _x, _path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    if os.path.isfile(_path):
        g.applogger.debug(f"delete status file. (path:{_path})")
        retry_remove(_path)


def clear_execution_parameters_file(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ起動パラメータファイル削除
    """
    _x, _path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    _path += "_parameter"
    if os.path.isfile(_path):
        g.applogger.debug(f"delete execution restart file. (path:{_path})")
        retry_remove(_path)


def clear_execution_restart_status_file(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ再起動状態ファイル削除
    """
    _x, _path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    _path += "_restart"
    if os.path.isfile(_path):
        g.applogger.debug(f"delete execution restart file. (path:{_path})")
        retry_remove(_path)


def get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ起動状態ファイルパス取得
    """
    storagepath = os.environ.get('STORAGEPATH')
    status_file_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/ag_ansible_execution/status/{driver_id}"
    status_file_path = f"{status_file_dir_path}/{execution_no}"
    return status_file_dir_path, status_file_path,

def create_execution_status_file(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ起動状態ファイル生成
    """
    status_file_dir_path, status_file_path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    retry_makedirs(status_file_dir_path)
    retry_chmod(status_file_dir_path, 0o777)
    if not os.path.isfile(status_file_path):
        # ファイル名を作業番号で作成
        with open(status_file_path, 'w') as f:
            g.applogger.debug(f"create execution staus file. (path:{status_file_path})")
            f.write("0")

def create_execution_parameters_file(organization_id, workspace_id, driver_id, execution_no, build_type, runtime_data_del):
    """
    子プロ起動パラメータファイル生成
    """
    ary = {}
    ary["build_type"] = build_type
    ary["runtime_data_del"] = runtime_data_del
    ary_dump = json.dumps(ary)
    status_file_dir_path, status_file_path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    status_file_path += "_parameter"
    retry_makedirs(status_file_dir_path)
    retry_chmod(status_file_dir_path, 0o777)
    if not os.path.isfile(status_file_path):
        # ファイル名を作業番号で作成
        with open(status_file_path, 'w') as f:
            g.applogger.debug(f"create execution parameter  file. (path:{status_file_path})")
            f.write(ary_dump)

def create_execution_restart_status_file(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ再起動状態ファイル生成
    """
    ary = {}
    ary["status"] = "staus_0"
    ary_dump = json.dumps(ary)
    status_file_dir_path, status_file_path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    status_file_path += "_restart"
    retry_makedirs(status_file_dir_path)
    retry_chmod(status_file_dir_path, 0o777)
    if not os.path.isfile(status_file_path):
        # ファイル名を作業番号で作成
        with open(status_file_path, 'w') as f:
            g.applogger.debug(f"create execution restart file. (path:{status_file_path})")
            f.write(ary_dump)


def get_execution_parameters_file(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ起動パラメータファイルより起動パラメータ取得
    """
    status_file_dir_path, status_file_path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    status_file_path += "_parameter"
    with open(status_file_path, 'r') as f:
        g.applogger.debug(f"read execution parameter file. (path:{status_file_path})")
        ary_dump =  f.read()
        ary = json.loads(ary_dump)

    return ary["build_type"], ary["runtime_data_del"]


def get_execution_restart_status_file(organization_id, workspace_id, driver_id, execution_no):
    """
    子プロ再起動状態ファイル取得
    """
    status_file_dir_path, status_file_path = get_execution_status_file_path(organization_id, workspace_id, driver_id, execution_no)
    status_file_path += "_restart"
    with open(status_file_path, 'r') as f:
        ary_dump =  f.read()
        ary = json.loads(ary_dump)
        status = ary["status"]
        g.applogger.debug(f"read execution restart file. (path:{status_file_path} status:{status})")
    return status

def get_log_file_path(organization_id, workspace_id, driver_id, execution_no):
    """
    ログファイルのパスを返却
    """
    # in/out親ディレクトリパス
    storagepath = os.environ.get('STORAGEPATH')
    root_dir_path = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}"
    # ログファイルパス
    exec_log_pass = f"{root_dir_path}/out/exec.log"
    error_log_pass = f"{root_dir_path}/out/error.log"
    # 親プロ用エラーログ
    #parent_error_log_pass = f"{root_dir_path}/ag_parent_log/ag_parent_err.log"
    parent_error_log_pass = f"{root_dir_path}/out/ag_parent_err.log"
    # 子プロ用ログファイルパス
    child_exec_log_pass = f"{root_dir_path}/out/child_exec.log"
    child_error_log_pass = f"{root_dir_path}/out/child_error.log"
    # runnerログファイルパス
    runner_exec_log_pass = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}/artifacts/{execution_no}/stdout"
    runner_error_log_pass = f"{storagepath}/{organization_id}/{workspace_id}/driver/ag_ansible_execution/{driver_id}/{execution_no}/artifacts/{execution_no}/stderr"

    return exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass


def log_merge(exec_log_pass, error_log_pass, parent_error_log_pass, child_exec_log_pass, child_error_log_pass, runner_exec_log_pass, runner_error_log_pass, driver_id):
    """
    builder・runner・アプリのログファイルをマージする
    ARGS:
        exec_log_pass: 作業状態確認に表示される実行ログ
        error_log_pass: 作業状態確認に表示されるエラーログ
        parent_error_log_pass: 親プロ用エラーログ
        child_exec_log_pass: 子プロ用実行ログ
        child_error_log_pass: 子プロ用エラーログ
        runner_exec_log_pass: runner用実行ログ    ansible 標準出力
        runner_error_log_pass: runner用エラーログ ansible 標準エラー出力
    """
    # 作業状態確認に表示するエラーログにrunnerのエラーログを設定する
    log_data = ""
    if os.path.isfile(runner_error_log_pass):
        with open(runner_error_log_pass, "r") as f:
            log_data = f.read()
    # 作業状態確認に表示するエラーログにagent(親)のエラーログを設定する
    if os.path.isfile(parent_error_log_pass):
        with open(parent_error_log_pass, "r") as f:
            log_data += f.read()
        with open(error_log_pass, "w") as f:
            f.write(log_data)
    # 作業状態確認に表示するエラーログにagent(子)のエラーログを設定する
    if os.path.isfile(child_error_log_pass):
        with open(child_error_log_pass, "r") as f:
            log_data += f.read()
    # 作業状態確認に表示するエラーログに書き込む
    with open(error_log_pass, "w") as f:
        f.write(log_data)

    # 特定のキーワードで改行しrunnerの実行ログを見やすくする
    if os.path.isfile(runner_exec_log_pass):
        runner_exec_original_log_pass = runner_exec_log_pass + ".org"
        retry_copy(runner_exec_log_pass, runner_exec_original_log_pass)
        with open(runner_exec_original_log_pass, "r") as f:
            log_data = f.read()

        # カラーエスケープシーケンスを削除する。
        while True:
            log_data = re.sub(  '\x1b\[([0-9]{1,2});([0-9]{1,2})m','',log_data, 9999999999)
            ret = re.match('\x1b\[([0-9]{1,2});([0-9]{1,2})m', log_data)
            if ret is None:
                break
        while True:
            log_data = re.sub(  '\x1b\[([0-9]{1,2})m','',log_data, 9999999999)
            ret = re.match('\x1b\[([0-9]{1,2})m', log_data)
            if ret is None:
                break
        # 改行コードをCRLFからLFに置換する
        while True:
            log_data = re.sub('\\r','',log_data, 999999999)
            ret = re.match('\\r' ,log_data)
            if ret is None:
                break

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

    # 作業状態確認に表示する実行ログにrunnerの実行ログを設定する
    with open(exec_log_pass, "w") as f:
        f.write(log_data)

    # 作業状態確認に表示する実行ログにagentの実行ログを設定する
    if os.path.isfile(child_exec_log_pass):
        with open(child_exec_log_pass, "r") as f:
            log_data = f.read()
        with open(exec_log_pass, "a") as f:
            f.write(log_data)
