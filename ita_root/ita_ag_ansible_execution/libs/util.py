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

from common_libs.common.exception import AppException
from common_libs.common.util import arrange_stacktrace_format


def get_agent_id(organization_id, workspace_id, agent_name):
    """
        agent_idの取得・永続指定領域になければ、生成する
    Returns:
        agent_id
    """
    version_file_path = "/storage/agent_id"
    version_dir_path = f"/storage/{organization_id}/{workspace_id}/ag_ansible_execution/{agent_name}"
    version_file_name = "agent_id"
    version_file_path = f"{version_dir_path}/{version_file_name}"
    if os.path.isfile(version_file_path):
        with open(version_file_path, mode='r') as f:
            agent_id= f.read()
    else:
        os.makedirs(version_dir_path) if not os.path.isdir(version_dir_path) else None
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
    version_file_path = "/exastro/VERSION.txt"
    if os.path.isfile(version_file_path):
        with open(version_file_path, mode='r') as f:
            agent_version= f.read()
    else:
        agent_version = "2.5.0" #####

    return agent_version

def delete_status_file(organization_id, workspace_id, driver_id, execution_no):
    """
        ステータスファイルの削除
    """
    status_file = f"/storage/{organization_id}/{workspace_id}/ag_ansible_execution/starus/{driver_id}/{execution_no}"
    print(status_file)
    # os.remove(status_file) if os.path.isfile(status_file) else None

def get_upload_file_info(organization_id, workspace_id, driver_id, execution_no):
    """
        作業状態通知送信(ファイル)用のアーカイブ作成
    """
    upload_file_info = {
        "out_data": None,
        "conductor_data": None
    }
    out_data_dir = f"/storage/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/out"
    conductor_dir = f"/storage/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/conductor"
    _uuid = str(uuid.uuid4())
    tmp_dir_name = f"/tmp/{organization_id}/{workspace_id}/{_uuid}"
    os.makedirs(tmp_dir_name) if not os.path.isdir(tmp_dir_name) else None

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
    retry=1
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

def get_unexecuted_instance(organization_id, workspace_id, exastro_api, body=None, query=None, retry=3):
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
    status_code, response = retry_api_call(exastro_api, endpoint, mode="json", method="GET", retry=retry)
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

def get_execution_populated_data(organization_id, workspace_id, exastro_api, execution_no, body=None, query=None, retry=3):
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
    status_code, response = retry_api_call(exastro_api, endpoint, mode="stream", method="POST", query=query, retry=retry)
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

def post_upload_execution_files(organization_id, workspace_id, exastro_api, execution_no, body=None, query=None, form_data=None, retry=3):
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
