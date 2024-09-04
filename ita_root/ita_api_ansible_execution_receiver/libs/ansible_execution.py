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
import tarfile
import datetime
import glob

from flask import g
from common_libs.common import *  # noqa: F403
from common_libs.ag.util import ky_decrypt, app_exception, exception
from common_libs.common import storage_access
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_execution.version import AnsibleExexutionVersion

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

    # Legacy
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
            current_status = record.get["STATUS"]
            result["SCRAM_STATUS"] = record.get["ABORT_EXECUTE_FLAG"]
        # ステータス更新制御
        # 実行中(遅延)→実行中にならないように
        if current_status == AnscConst.PROCESS_DELAYED and status == AnscConst.PROCESSING:
            return result
        # 完了→実行中、実行中(遅延)、完了(異常)、想定外エラー、緊急停止にならないように
        if current_status == AnscConst.COMPLETE and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.FAILURE, AnscConst.EXCEPTION, AnscConst.SCRAM]:
            return result
        # 完了(異常)→実行中、実行中(遅延)、完了、想定外エラー、緊急停止にならないように
        if current_status == AnscConst.FAILURE and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.EXCEPTION, AnscConst.SCRAM]:
            return result
        # 想定外エラー→実行中、実行中(遅延)、完了、完了(異常)、緊急停止にならないように
        if current_status == AnscConst.EXCEPTION and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.SCRAM]:
            return result
        # 緊急停止→実行中、実行中(遅延)、完了、完了(異常)、想定外エラーにならないように
        if current_status == AnscConst.SCRAM and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.EXCEPTION]:
            return result
        # ステータス更新
        objdbca.table_update(t_ansl_exec_sts_inst, data_list, "EXECUTION_NO")
    elif driver_id == "pioneer":
        ret = objdbca.table_select(t_ansp_exec_sts_inst, 'WHERE  EXECUTION_NO=%s', [execution_no])
        for record in ret:
            result["SCRAM_STATUS"] = record.get["ABORT_EXECUTE_FLAG"]
        # ステータス更新制御
        # 実行中(遅延)→実行中にならないように
        if current_status == AnscConst.PROCESS_DELAYED and status == AnscConst.PROCESSING:
            return result
        # 完了→実行中、実行中(遅延)、完了(異常)、想定外エラー、緊急停止にならないように
        if current_status == AnscConst.COMPLETE and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.FAILURE, AnscConst.EXCEPTION, AnscConst.SCRAM]:
            return result
        # 完了(異常)→実行中、実行中(遅延)、完了、想定外エラー、緊急停止にならないように
        if current_status == AnscConst.FAILURE and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.EXCEPTION, AnscConst.SCRAM]:
            return result
        # 想定外エラー→実行中、実行中(遅延)、完了、完了(異常)、緊急停止にならないように
        if current_status == AnscConst.EXCEPTION and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.SCRAM]:
            return result
        # 緊急停止→実行中、実行中(遅延)、完了、完了(異常)、想定外エラーにならないように
        if current_status == AnscConst.SCRAM and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.EXCEPTION]:
            return result
        # ステータス更新
        objdbca.table_update(t_ansp_exec_sts_inst, data_list, "EXECUTION_NO")
    elif driver_id == "legacy_role":
        ret = objdbca.table_select(t_ansr_exec_sts_inst, 'WHERE  EXECUTION_NO=%s', [execution_no])
        for record in ret:
            result["SCRAM_STATUS"] = record.get["ABORT_EXECUTE_FLAG"]
        # ステータス更新制御
        # 実行中(遅延)→実行中にならないように
        if current_status == AnscConst.PROCESS_DELAYED and status == AnscConst.PROCESSING:
            return result
        # 完了→実行中、実行中(遅延)、完了(異常)、想定外エラー、緊急停止にならないように
        if current_status == AnscConst.COMPLETE and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.FAILURE, AnscConst.EXCEPTION, AnscConst.SCRAM]:
            return result
        # 完了(異常)→実行中、実行中(遅延)、完了、想定外エラー、緊急停止にならないように
        if current_status == AnscConst.FAILURE and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.EXCEPTION, AnscConst.SCRAM]:
            return result
        # 想定外エラー→実行中、実行中(遅延)、完了、完了(異常)、緊急停止にならないように
        if current_status == AnscConst.EXCEPTION and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.SCRAM]:
            return result
        # 緊急停止→実行中、実行中(遅延)、完了、完了(異常)、想定外エラーにならないように
        if current_status == AnscConst.SCRAM and status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED, AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.EXCEPTION]:
            return result
        # ステータス更新
        objdbca.table_update(t_ansr_exec_sts_inst, data_list, "EXECUTION_NO")

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

    if driver_id == "legacy":
        # in,outディレクトリ相当のパス
        dir_path = "/storage/" + organization_id + "/" + workspace_id + legacy_dir_path + "/" + execution_no
        tmp_path = "/tmp/" + organization_id + "/" + workspace_id + legacy_dir_path
        if os.path.exists(dir_path):
            # 一時フォルダに移動
            if not os.path.exists(tmp_path):
                os.makedirs(tmp_path)
                os.chmod(tmp_path, 0o777)
            shutil.move(dir_path, tmp_path)

        # conductorディレクトリ相当のパス
        conductor_dir_path = "/storage/" + organization_id + "/" + workspace_id + legacy_dir_path + "/" + execution_no + "/conductor"
        if os.path.exists(conductor_dir_path):
            # 一時フォルダに移動
            if not os.path.exists(tmp_path):
                os.makedirs(tmp_path)
                os.chmod(tmp_path, 0o777)
            shutil.move(dir_path, tmp_path)

        gztar_path = tmp_path + "/" + execution_no + ".tar.gz"
        with tarfile.open(gztar_path, "w:gz") as tar:
            tar.add(tmp_path, arcname="")

        # ステータスを実行待ちに変更
        data_list = {"STATUS_ID": "12", "EXECUTION_NO": execution_no}
        objdbca.table_update(t_ansl_exec_sts_inst, data_list, "EXECUTION_NO")

        objdbca.db_commit()

    # pioneer
    if driver_id == "pioneer":
        # in,outディレクトリ相当のパス
        dir_path = "/storage/" + organization_id + "/" + workspace_id + pioneer_dir_path + "/" + execution_no
        tmp_path = "/tmp/" + organization_id + "/" + workspace_id + pioneer_dir_path
        if os.path.exists(dir_path):
            # 一時フォルダに移動
            if not os.path.exists(tmp_path):
                os.makedirs(tmp_path)
                os.chmod(tmp_path, 0o777)
            shutil.move(dir_path, tmp_path)

        # conductorディレクトリ相当のパス
        conductor_dir_path = "/storage/" + organization_id + "/" + workspace_id + pioneer_dir_path + "/" + execution_no + "/conductor"
        if os.path.exists(conductor_dir_path):
            # 一時フォルダに移動
            if not os.path.exists(tmp_path):
                os.makedirs(tmp_path)
                os.chmod(tmp_path, 0o777)
            shutil.move(dir_path, tmp_path)

        gztar_path = tmp_path + "/" + execution_no + ".tar.gz"
        with tarfile.open(gztar_path, "w:gz") as tar:
            tar.add(tmp_path, arcname="")

        # ステータスを実行待ちに変更
        data_list = {"STATUS_ID": "12", "EXECUTION_NO": execution_no}
        objdbca.table_update(t_ansp_exec_sts_inst, data_list, "EXECUTION_NO")

        objdbca.db_commit()

    # role
    if driver_id == "pioneer":
        # in,outディレクトリ相当のパス
        dir_path = "/storage/" + organization_id + "/" + workspace_id + role_dir_path + "/" + execution_no
        tmp_path = "/tmp/" + organization_id + "/" + workspace_id + role_dir_path
        if os.path.exists(dir_path):
            # 一時フォルダに移動
            if not os.path.exists(tmp_path):
                os.makedirs(tmp_path)
                os.chmod(tmp_path, 0o777)
            shutil.move(dir_path, tmp_path)

        # conductorディレクトリ相当のパス
        conductor_dir_path = "/storage/" + organization_id + "/" + workspace_id + role_dir_path + "/" + execution_no + "/conductor"
        # 一時フォルダに移動
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
            os.chmod(tmp_path, 0o777)
        shutil.move(dir_path, tmp_path)

        gztar_path = tmp_path + "/" + execution_no + ".tar.gz"
        with tarfile.open(gztar_path, "w:gz") as tar:
            tar.add(tmp_path, arcname="")

        # ステータスを実行待ちに変更
        data_list = {"STATUS_ID": "12", "EXECUTION_NO": execution_no}
        objdbca.table_update(t_ansr_exec_sts_inst, data_list, "EXECUTION_NO")

        objdbca.db_commit()

    return gztar_path


def update_result(organization_id, workspace_id, execution_no, parameters, file_path):
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
    driver_id = parameters["driver_id"]
    # ステータス
    status = parameters["status"]

    if driver_id == "legacy":
        out_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/out"
        in_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/in/project"
        conductor_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/conductor"
        tmp_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/"
    elif driver_id == "pioneer":
        out_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/out"
        in_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/in/project"
        conductor_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/conductor"
        tmp_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "/"
    else:
        out_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/out"
        in_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/in/project"
        conductor_directory_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/conductor"
        tmp_path = "/tmp/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "/"

    for file_key, record_file_paths in file_path.items():
        if not os.path.exists(tmp_path + file_key):
            os.mkdir(tmp_path + file_key)
        with tarfile.open(record_file_paths, 'r:gz') as tar:
            tar.extractall(path=tmp_path + file_key)

        # outディレクトリ更新
        if file_key == "out_tar_data":
            # 展開したファイルの一覧を取得
            lst = glob.glob(tmp_path + file_key + "/**", recursive=True)
            file_list = []
            for path in lst:
                if os.path.isfile(path):
                    file_list.append(path)

            for file_path in file_list:
                # 通知されたファイルで上書き
                shutil.move(file_path, out_directory_path + "/" + os.path.basename(file_path))

        # parameters, parameters_fileディレクトリ更新
        if file_key == "parameters_tar_data" or file_key == "parameters_file_tar_data":
            # ステータスが完了、完了(異常)の場合
            if status == AnscConst.COMPLETE or status == AnscConst.FAILURE:
                # 展開したファイルの一覧を取得
                lst = glob.glob(tmp_path + file_key + "/**", recursive=True)
                file_list = {}
                for path in lst:
                    if os.path.isfile(path):
                        path = Path(path)
                        parent_dirctory = str(path.parent)
                        file_list[parent_dirctory] = os.path.basename(path)
                for dir_name, file_name in file_list.items():
                    # 通知されたファイルで上書き
                    shutil.move(dir_name + "/" + file_name, in_directory_path + "/" + os.path.basename(dir_name) + "/" + os.path.basename(file_name))

        # conductorディレクトリ更新
        if file_key == "conductor_tar_data":
            if status == AnscConst.COMPLETE or status == AnscConst.FAILURE:
                # 展開したファイルの一覧を取得
                lst = glob.glob(tmp_path + file_key + "/**", recursive=True)
                file_list = []
                for path in lst:
                    if os.path.isfile(path):
                        file_list.append(path)

                for file_path in file_list:
                    # 通知されたファイルで上書き
                    shutil.move(file_path, conductor_directory_path + "/" + os.path.basename(file_path))

def get_agent_version(objdbca, body):
    """
        エージェント名とバージョン情報を取得
        ARGS:
            organization_id:OrganizationID
            workspace_id: WorkspaceID
        RETRUN:
            statusCode, {}, msg
    """

    # エージェント名
    agent_name = body["agent_name"]
    version = body["version"]

    # トランザクション開始
    objdbca.db_transaction_start()

    # ITAの対応するバージョンと比較
    result = {"version_diff": ""}
    version_list = AnsibleExexutionVersion()

    result["version_diff"] = version_list.check_diff_version(version)

    where = "WHERE AGENT_NAME = %s AND DISUSE_FLAG = '0'"
    ret = objdbca.table_select("T_ANSC_AGENT", where, [agent_name])

    if len(ret) == 0:
        # エージェント管理へ登録
        data_list = {
            "AGENT_NAME": agent_name,
            "VERSION": version,
            "STATUS_ID": result["version_diff"],
            "DISUSE_FLAG": "0"
        }
        ret = objdbca.table_insert("T_ANSC_AGENT", data_list, "ROW_ID", False)
        if ret is False:
            return False
    else:
        # エージェント管理へ登録
        data_list = {
            "AGENT_NAME": agent_name,
            "VERSION": version,
            "STATUS_ID": result["version_diff"]
        }
        ret = objdbca.table_update("T_ANSC_AGENT", data_list, "AGENT_NAME", False)
        if ret is False:
            return False

    objdbca.db_commit()

    return result

def update_ansible_agent_status_file(organization_id, workspace_id, body):
    """
        作業中通知
        ARGS:
            body: 作業実行中の作業番号リスト
            workspace_id: ファイル名
        RETRUN:
            statusCode, {}, msg
    """

    legacy = body["legacy"]
    pioneer = body["pioneer"]
    legacy_role = body["legacy_role"]

    # 作業状態通知受信ファイルを空更新する
    for execution_no in legacy:
        file_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy/" + execution_no + "/out/ansible_agent_status_file.txt"
        if os.path.exists(file_path):
            # 元の日時を取得
            sr = os.stat(path=file_path)
            # 更新日時のみ変更
            now = datetime.datetime.now().timestamp()
            os.utime(path=file_path, times=(sr.st_atime, now))
    for execution_no in pioneer:
        file_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/pioneer/" + execution_no + "out/ansible_agent_status_file.txt"
        if os.path.exists(file_path):
            # 元の日時を取得
            sr = os.stat(path=file_path)
            # 更新日時のみ変更
            os.utime(path=file_path, times=(sr.st_atime, datetime.datetime.now()))
    for execution_no in legacy_role:
        file_path = "/storage/" + organization_id + "/" + workspace_id + "/driver/ansible/legacy_role/" + execution_no + "out/ansible_agent_status_file.txt"
        if os.path.exists(file_path):
            # 元の日時を取得
            sr = os.stat(path=file_path)
            # 更新日時のみ変更
            os.utime(path=file_path, times=(sr.st_atime, datetime.datetime.now()))

    return True

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

def create_file_path(connexion_request, tmp_path, execution_no):
    """
        base64をtarファイルに変換する
        ARGS:
            connexion_request: connexion.request
            tmp_path: ファイル格納先
            execution_no: 作業番号
        RETRUN:
            bool, parameters, file_paths
    """

    parameters = []
    file_paths = {}

    # get parameters
    if connexion_request.is_json:
        # application/json
        parameters = connexion_request.get_json()
    elif connexion_request.form:
        # multipart/form-data, application/x-www-form-urlencoded
        # check key : json_parameters
        if 'json_parameters' in connexion_request.form:
            # json.loads
            try:
                parameters = json.loads(connexion_request.form['json_parameters'])
            except Exception as e:   # noqa: E722
                print_exception_msg(e)

                parameters = connexion_request.form['json_parameters']
                if isinstance(parameters, (list, dict)) is False:
                    return False, [], file_paths

            if parameters["driver_id"] == "legacy":
                tmp_path = tmp_path + "/driver/ansible/legacy/" + execution_no
            elif parameters["driver_id"] == "pioneer":
                tmp_path = tmp_path + "/driver/ansible/pioneer" + execution_no
            elif parameters["driver_id"] == "legacy_role":
                tmp_path = tmp_path + "/driver/ansible/legacy_role" + execution_no

            # set parameter['file'][rest_name]
            if connexion_request.files:
                # ファイルが保存できる容量があるか確認
                file_size = connexion_request.headers.get("Content-Length")
                file_size_mb = f"{int(file_size)/(1024*1024):,.6f} MB"
                storage = storage_base()
                can_save, free_space = storage.validate_disk_space(file_size)
                if can_save is False:
                    status_code = "499-00222"
                    log_msg_args = [file_size_mb]
                    api_msg_args = [file_size_mb]
                    raise AppException(status_code, log_msg_args, api_msg_args)

                for _file_key in connexion_request.files:
                    _file_data = connexion_request.files[_file_key]
                    file_name = _file_data.filename
                    if not os.path.exists(tmp_path):
                        os.makedirs(tmp_path)
                    file_path = os.path.join(tmp_path, file_name)
                    file_paths[_file_key] = file_path

                    f = open(file_path, 'wb')
                    while True:
                        # fileの読み込み
                        buf = _file_data.stream.read(1000000)
                        if len(buf) == 0:
                            break
                        # yield buf
                        # fileの書き込み
                        f.write(buf)
                    f.close()

        else:
            return False, [], file_paths

        # check parameters
        if len(parameters) == 0:
            return False, [], file_paths

    return True, parameters, file_paths