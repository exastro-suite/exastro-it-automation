#   Copyright 2024 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import subprocess

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.ag.util import ky_decrypt, app_exception, exception
from common_libs.common import storage_access
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

def unexecuted_instance(objdbca):
    """
        未実行インスタンス取得
        ARGS:
            organization_id:OrganizationID
            workspace_id: WorkspaceID
        RETRUN:
            statusCode, {}, msg
    """

    # 各テーブル
    t_ansl_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
    t_ansp_exec_sts_inst = "T_ANSP_EXEC_STS_INST"
    t_ansr_exec_sts_inst = "T_ANSR_EXEC_STS_INST"
    t_ansc_execdev = "T_ANSC_EXECDEV"
    t_ansc_info = "T_ANSC_IF_INFO"

    # Legacy_role
    # 準備完了の作業インスタンス取得
    where = 'WHERE  DISUSE_FLAG=%s AND STATUS_ID = %s'
    parameter = ['0', '11']
    ret = objdbca.table_select(t_ansl_exec_sts_inst, where, parameter)

    result = {}
    for record in ret:
        execution_no = record.get("EXECUTION_NO") # 作業番号

        result[execution_no] = {
            "driver_id": "legacy"
        }

    # pioneer
    # 準備完了の作業インスタンス取得
    where = 'WHERE  DISUSE_FLAG=%s AND STATUS_ID = %s'
    parameter = ['0', '11']
    ret = objdbca.table_select(t_ansp_exec_sts_inst, where, parameter)

    for record in ret:
        execution_no = record.get("EXECUTION_NO") # 作業番号

        result[execution_no] = {
            "driver_id": "pioneer"
        }

    # role
    # 準備完了の作業インスタンス取得
    where = 'WHERE  DISUSE_FLAG=%s AND STATUS_ID = %s'
    parameter = ['0', '11']
    ret = objdbca.table_select(t_ansr_exec_sts_inst, where, parameter)

    for record in ret:
        execution_no = record.get("EXECUTION_NO") # 作業番号

        result[execution_no] = {
            "driver_id": "legacy_role"
        }

    # 実行環境構築方法取得
    where = 'WHERE  DISUSE_FLAG=%s'
    parameter = ['0']
    ret = objdbca.table_select(t_ansc_execdev, where, parameter)

    for record in ret:
        build_type = record['BUILD_TYPE']
        user_name = record['USER_NAME']
        password = record['PASSWORD']
        base_image = record['BASE_IMAGE_OS_TYPE']
        attach_repository = record['ATTACH_REPOSITORY']
        password = ky_decrypt(password)

    # 実行時データ削除フラグ取得
    where = 'WHERE  DISUSE_FLAG=%s'
    parameter = ['0']
    ret = objdbca.table_select(t_ansc_info, where, parameter)
    for record in ret:
        anstwr_del_runtime_data = record['ANSTWR_DEL_RUNTIME_DATA']

    result[execution_no]["build_type"] = build_type
    result[execution_no]["user_name"] = user_name
    result[execution_no]["password"] = password
    result[execution_no]["base_image"] = base_image
    result[execution_no]["attach_repository"] = attach_repository
    result[execution_no]["anstwr_del_runtime_data"] = anstwr_del_runtime_data

    objdbca.db_commit()

    return result

def get_execution_status(objdbca, execution_no, body):
    """
        緊急停止状態を返す
        ARGS:
            organization_id:OrganizationID
            workspace_id: WorkspaceID
        RETRUN:
            scram_status: 緊急停止状態
    """

    # 各テーブル
    t_ansl_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
    t_ansp_exec_sts_inst = "T_ANSP_EXEC_STS_INST"
    t_ansr_exec_sts_inst = "T_ANSR_EXEC_STS_INST"

    # トランザクション開始
    objdbca.db_transaction_start()

    # ドライバーID
    driver_id = body["driver_id"]
    # ステータス
    status = body["status"]

    # ステータス更新、緊急停止状態取得
    result = {}
    data_list = {"EXECUTION_NO": execution_no, "STATUS": status}
    if driver_id == "legacy":
        ret = objdbca.table_select(t_ansl_exec_sts_inst, 'WHERE  EXECUTION_NO=%s', [execution_no])
        for record in ret:
            result["SCRAM_STATUS"] = record.get["ABORT_EXECUTE_FLAG"]
        objdbca.table_update(t_ansl_exec_sts_inst, data_list, execution_no)
    elif driver_id == "pioneer":
        ret = objdbca.table_select(t_ansp_exec_sts_inst, 'WHERE  EXECUTION_NO=%s', [execution_no])
        for record in ret:
            result["SCRAM_STATUS"] = record.get["ABORT_EXECUTE_FLAG"]
        objdbca.table_update(t_ansp_exec_sts_inst, data_list, execution_no)
    elif driver_id == "legacy_role":
        ret = objdbca.table_select(t_ansr_exec_sts_inst, 'WHERE  EXECUTION_NO=%s', [execution_no])
        for record in ret:
            result["SCRAM_STATUS"] = record.get["ABORT_EXECUTE_FLAG"]
        objdbca.table_update(t_ansr_exec_sts_inst, data_list, execution_no)

    objdbca.db_commit()

    return result


def get_populated_data_path(objdbca, organization_id, workspace_id, execution_no, driver_id):
    """
        投入データ取得
        ARGS:
            organization_id:OrganizationID
            workspace_id: WorkspaceID
        RETRUN:
            statusCode, {}, msg
    """

    # 各テーブル
    t_ansl_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
    t_ansp_exec_sts_inst = "T_ANSP_EXEC_STS_INST"
    t_ansr_exec_sts_inst = "T_ANSR_EXEC_STS_INST"

    # 各Driverパス
    legacy_dir_path = "/driver/ansible/legacy"
    pioneer_dir_path = "/driver/ansible/pioneer"
    role_dir_path = "/driver/ansible/legacy_role"

    # トランザクション開始
    objdbca.db_transaction_start()

    result = {}
    if driver_id == "legacy":
        # in,outディレクトリ相当のパス
        dir_path = "/storage/" + organization_id + "/" + workspace_id + legacy_dir_path + "/" + execution_no
        if os.path.exists(dir_path):
            result[execution_no] = {"in_out_data": dir_path}

        # conductorディレクトリ相当のパス
        conductor_dir_path = "/storage/" + organization_id + "/" + workspace_id + legacy_dir_path + "/" + execution_no + "/conductor"
        if os.path.exists(dir_path):
            result[execution_no] = {"conductor_data": conductor_dir_path}

        # ステータスを実行待ちに変更
        data_list = {"STATUS_ID": "12", "EXECUTION_NO": execution_no}
        objdbca.table_update(t_ansl_exec_sts_inst, data_list, execution_no)

        objdbca.db_commit()

    # pioneer
    if driver_id == "pioneer":
        # in,outディレクトリ相当のパス
        dir_path = "/storage/" + organization_id + "/" + workspace_id + pioneer_dir_path + "/" + execution_no
        if os.path.exists(dir_path):
            result[execution_no] = {"in_out_data": dir_path}

        # conductorディレクトリ相当のパス
        conductor_dir_path = "/storage/" + organization_id + "/" + workspace_id + pioneer_dir_path + "/" + execution_no + "/conductor"
        if os.path.exists(dir_path):
            result[execution_no] = {"conductor_data": conductor_dir_path}

        # ステータスを実行待ちに変更
        data_list = {"STATUS_ID": "12", "EXECUTION_NO": execution_no}
        objdbca.table_update(t_ansp_exec_sts_inst, data_list, execution_no)

        objdbca.db_commit()

    # role
    if driver_id == "pioneer":
        # in,outディレクトリ相当のパス
        dir_path = "/storage/" + organization_id + "/" + workspace_id + role_dir_path + "/" + execution_no
        if os.path.exists(dir_path):
            result[execution_no] = {"in_out_data": dir_path}

        # conductorディレクトリ相当のパス
        conductor_dir_path = "/storage/" + organization_id + "/" + workspace_id + role_dir_path + "/" + execution_no + "/conductor"
        if os.path.exists(dir_path):
            result[execution_no] = {"conductor_data": conductor_dir_path}

        # ステータスを実行待ちに変更
        data_list = {"STATUS_ID": "12", "EXECUTION_NO": execution_no}
        objdbca.table_update(t_ansr_exec_sts_inst, data_list, execution_no)

        objdbca.db_commit()

    return result


def update_result_data(organization_id, workspace_id, execution_no, body):
    """
        通知されたファイルの更新
        ARGS:
            organization_id:OrganizationID
            workspace_id: WorkspaceID
            execution_no: 作業番号
        RETRUN:
            statusCode, {}, msg
    """

    # ドライバーID
    driver_id = body["driver_id"]
    # ステータス
    status = body["status"]

    # outディレクトリ相当のtarデータ
    out_base64_data = body["out_tar_data"]
    parameters_base64_data = body["parameters_tar_data"]
    parameters_file_base64_data = body["parameters_file_tar_data"]
    conductor_base64_data = body["conductor_tar_data"]

    if driver_id == "legacy":
        from_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "in/project"
        tmp_out_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/out"
        tmp_parameters_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/parameters"
        tmp_parameters_file_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/parameters_file"
        tmp_conductor_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/conductor"
    elif driver_id == "pioneer":
        from_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "in/project"
        tmp_out_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/out"
        tmp_parameters_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/parameters"
        tmp_parameters_file_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/parameters_file"
        tmp_conductor_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/conductor"
    else:
        from_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "in/project"
        tmp_out_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/out"
        tmp_parameters_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/parameters"
        tmp_parameters_file_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/parameters_file"
        tmp_conductor_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/conductor"

    # outディレクトリ更新
    # 作業ディレクトリ作成
    if not os.path.exists(tmp_out_path):
        os.mkdir(tmp_out_path)
        os.chmod(tmp_out_path, 0o777)

    # outディレクトリのtarファイル展開
    decode_tar_file(out_base64_data, tmp_out_path)

    # 展開したファイルの一覧を取得
    lst = os.listdir(tmp_out_path)

    if status == AnscConst.PROCESSING or status == AnscConst.PROCESS_DELAYED:
        for file_name in lst:
            if file_name == "error.log" or file_name == "exec.log":
                # 通知されたファイルで上書き
                shutil.move(tmp_out_path + "/" + file_name, from_path)
    elif status == AnscConst.COMPLETE or status == AnscConst.FAILURE:
        for file_name in lst:
            # 通知されたファイルで上書き
            shutil.move(tmp_out_path + "/" + file_name, from_path)

    # parametersディレクトリ更新
    # 作業ディレクトリ作成
    if not os.path.exists(tmp_parameters_path):
        os.mkdir(tmp_parameters_path)
        os.chmod(tmp_parameters_path, 0o777)

    # parametersディレクトリのtarファイル展開
    decode_tar_file(parameters_base64_data, tmp_parameters_path)

    # 展開したファイルの一覧を取得
    lst = os.listdir(tmp_parameters_path)

    if status == AnscConst.COMPLETE or status == AnscConst.FAILURE:
        for dir_name in lst:
            # 展開したファイルの一覧を取得
            lst = os.listdir(tmp_parameters_path + "/" + dir_name)
            for file_name in lst:
                # 通知されたファイルで上書き
                shutil.move(tmp_parameters_path + "/" + dir_name + "/" + file_name, from_path)

    # parameters_fileディレクトリ更新
    # 作業ディレクトリ作成
    if not os.path.exists(tmp_parameters_file_path):
        os.mkdir(tmp_parameters_file_path)
        os.chmod(tmp_parameters_file_path, 0o777)

    # parametersディレクトリのtarファイル展開
    decode_tar_file(parameters_file_base64_data, tmp_parameters_file_path)

    # 展開したファイルの一覧を取得
    lst = os.listdir(tmp_parameters_file_path)

    if status == AnscConst.COMPLETE or status == AnscConst.FAILURE:
        for dir_name in lst:
            # 展開したファイルの一覧を取得
            lst = os.listdir(tmp_parameters_file_path + "/" + dir_name)
            for file_name in lst:
                # 通知されたファイルで上書き
                shutil.move(tmp_parameters_file_path + "/" + dir_name + "/" + file_name, from_path)

    # conductorディレクトリ更新
    # 作業ディレクトリ作成
    if not os.path.exists(tmp_conductor_path):
        os.mkdir(tmp_conductor_path)
        os.chmod(tmp_conductor_path, 0o777)

    # conductorディレクトリのtarファイル展開
    decode_tar_file(conductor_base64_data, tmp_conductor_path)

    # 展開したファイルの一覧を取得
    lst = os.listdir(tmp_conductor_path)

    if status == AnscConst.COMPLETE or status == AnscConst.FAILURE:
        for file_name in lst:
            # 通知されたファイルで上書き
            shutil.move(tmp_conductor_path + "/" + file_name, from_path)

    # 作業ディレクトリ削除
    shutil.rmtree(tmp_out_path)
    shutil.rmtree(tmp_parameters_path)
    shutil.rmtree(tmp_conductor_path)

def get_agent_version(objdbca, organization_id, workspace_id):
    """
        エージェント名とバージョン情報を取得
        ARGS:
            organization_id:OrganizationID
            workspace_id: WorkspaceID
        RETRUN:
            statusCode, {}, msg
    """

    # 環境変数からエージェント名を取得
    agent_name = os.environ.get("AGENT_NAME")

    # ファイルからバージョン情報を取得
    file_path = "exastro/common_libs/ansible_execution/version.txt"
    if os.path.isfile(file_path):
        obj = storage_access.storage_read()
        obj.open(file_path)
        version = obj.read()
        obj.close()

    result = {
        "agent_name": agent_name,
        "version": version
    }

    return result

def encode_tar_file(dir_path, file_name):
    """
        tarファイルをbase64に変換する
        ARGS:
            dir_path:ディレクトリパス
            workspace_id: ファイル名
        RETRUN:
            statusCode, {}, msg
    """

    cmd = "base64" + dir_path + "/" + file_name + "> tmp.txt"
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    if ret.returncode != 0:
        msg = g.appmsg.get_api_message('MSG-10947', [])
        raise app_exception(msg)

    obj = storage_access.storage_read()
    obj.open(dir_path + "/tmp.txt")
    base64_data = obj.read()
    obj.close()

    # 処理終了後、作業ファイル削除
    os.remove(dir_path + "/" + file_name)
    os.remove(dir_path + "/tmp.txt")

    return base64_data

def decode_tar_file(base64_data, dir_path):
    """
        base64をtarファイルに変換する
        ARGS:
            base64_data: base64データ
            dir_path:ディレクトリパス
        RETRUN:
            statusCode, {}, msg
    """
    cmd = "base64 -d " + base64_data + " > " + dir_path
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    if ret.returncode != 0:
        msg = g.appmsg.get_api_message('MSG-10947', [])
        raise app_exception(msg)

    return base64_data