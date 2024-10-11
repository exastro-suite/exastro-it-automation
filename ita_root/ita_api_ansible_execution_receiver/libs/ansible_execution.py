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
from common_libs.ansible_execution.encrypt import agent_encrypt


def unexecuted_instance(objdbca, body={}):
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

    # t_xxxx_exec_sts_instのPrimary key
    exec_sts_inst_pkey = "EXECUTION_NO"

    # 各ドライバ
    driver_ids = [
        "legacy",
        "pioneer",
        "legacy_role"
    ]

    # 実行時データ削除フラグ取得
    where = 'WHERE DISUSE_FLAG=%s'
    parameter = ['0']
    ret = objdbca.table_select(t_ansc_info, where, parameter)
    for record in ret:
        anstwr_del_runtime_data = record['ANSTWR_DEL_RUNTIME_DATA']

    # 実行環境構築方法取得
    where = 'WHERE DISUSE_FLAG=%s'
    parameter = ['0']
    ret = objdbca.table_select(t_ansc_execdev, where, parameter)
    execdev_data = {_r.get("EXECUTION_ENVIRONMENT_NAME"): _r for _r in ret \
        if _r.get("EXECUTION_ENVIRONMENT_NAME") is not None} if ret else {}

    # bodyから対象実行環境名のリスト取得
    _eens = body["execution_environment_names"] if body and "execution_environment_names" in body else None
    execution_environment_names = _eens if _eens and len(_eens) != 0 else None

    try:
        # トランザクション開始
        objdbca.db_transaction_start()

        result = {}
        pass_phrase = g.ORGANIZATION_ID + " " + g.WORKSPACE_ID

        # 各driver
        for driver_id in driver_ids:
            # 各driverのテーブル
            if driver_id == "legacy":
                t_exec_sts_inst = t_ansl_exec_sts_inst
            elif driver_id == "pioneer":
                t_exec_sts_inst = t_ansp_exec_sts_inst
            elif driver_id == "legacy_role":
                t_exec_sts_inst = t_ansr_exec_sts_inst

            # 準備完了の作業インスタンス取得
            where = 'WHERE DISUSE_FLAG=%s AND STATUS_ID = %s'
            parameter = ['0', '11']

            # 実行環境名の指定がある場合に条件追加
            if execution_environment_names:
                prepared_list = ','.join(['%s']*len(execution_environment_names))
                where +=  f" AND I_AG_EXECUTION_ENVIRONMENT_NAME IN ({prepared_list})"
                parameter.extend(execution_environment_names)

            ret = objdbca.table_select(t_exec_sts_inst, where, parameter)

            # 各作業実行関連テーブルの行ロック
            execution_no_list = [_r.get(exec_sts_inst_pkey) for _r in ret if _r.get(exec_sts_inst_pkey)]
            if len(execution_no_list) != 0:
                sql_str = f"SELECT `{exec_sts_inst_pkey}` FROM `{t_exec_sts_inst}` WHERE `{exec_sts_inst_pkey}` IN (%s) FOR UPDATE"
                objdbca.sql_execute(sql_str, [",".join(execution_no_list)])
                g.applogger.debug(f"SELECT FOR UPDATE :{exec_sts_inst_pkey}, [{execution_no_list}]")

            for record in ret:
                # 実行環境名
                ag_execution_env_name = record.get("I_AG_EXECUTION_ENVIRONMENT_NAME")
                # 実行環境情報
                execdev_record = execdev_data[ag_execution_env_name] \
                    if ag_execution_env_name in execdev_data else {}
                # 作業番号
                execution_no = record.get("EXECUTION_NO")

                # 複合化→暗号化（エージェント用）
                password = execdev_record.get('PASSWORD')
                password = ky_decrypt(password)
                password = agent_encrypt(execdev_record.get('PASSWORD'), pass_phrase)\
                    if execdev_record.get('PASSWORD') else execdev_record.get('PASSWORD')

                # set result[execution_no]
                result[execution_no] = {
                    "driver_id": driver_id
                }
                result[execution_no]["build_type"] = execdev_record.get('BUILD_TYPE')
                result[execution_no]["user_name"] = execdev_record.get('USER_NAME')
                result[execution_no]["password"] = password
                result[execution_no]["base_image"] = execdev_record.get('BASE_IMAGE_OS_TYPE')
                result[execution_no]["attach_repository"] = execdev_record.get('ATTACH_REPOSITORY')
                result[execution_no]["anstwr_del_runtime_data"] = anstwr_del_runtime_data

                # ステータスを実行待ちに変更
                data_list = {
                    "STATUS_ID": AnscConst.PROCESSING_WAIT,
                    "EXECUTION_NO": execution_no
                }
                objdbca.table_update(t_exec_sts_inst, data_list, "EXECUTION_NO")

        # コミット/トランザクション終了
        objdbca.db_transaction_end(True)
    except Exception as e:
        result = {}
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))

        if objdbca._is_transaction is True:
            # ロールバック/トランザクション終了
            objdbca.db_transaction_end(False)

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

    status_list = [
        AnscConst.NOT_YET,          # 未実行
        AnscConst.PREPARE,          # 準備中
        AnscConst.PROCESSING,       # 実行中
        AnscConst.PROCESS_DELAYED,  # 実行中(遅延)
        AnscConst.COMPLETE,         # 完了
        AnscConst.FAILURE,          # 完了(異常)
        AnscConst.EXCEPTION,        # 想定外エラー
        AnscConst.SCRAM,            # 緊急停止
        AnscConst.RESERVE,          # 未実行(予約中)
        AnscConst.RESERVE_CANCEL,   # 予約取消
        AnscConst.PREPARE_COMPLETE, # 準備完了
        AnscConst.PROCESSING_WAIT,  # 実行待ち
    ]

    # ドライバーID
    driver_id = body["driver_id"]
    # ステータス
    status = body["status"]

    if driver_id == "legacy":
        t_exec_sts_inst = t_ansl_exec_sts_inst
    elif driver_id == "pioneer":
        t_exec_sts_inst = t_ansp_exec_sts_inst
    elif driver_id == "legacy_role":
        t_exec_sts_inst = t_ansr_exec_sts_inst
    else:
        g.applogger.info(f"Not found {driver_id=}")
        return {}

    if status not in status_list:
        g.applogger.info(f"Not found {status=}")
        return {}

    # ステータス更新、緊急停止状態取得
    result = {}
    ret = objdbca.table_select(t_exec_sts_inst, 'WHERE  EXECUTION_NO=%s', [execution_no])
    for record in ret:
        current_status = record.get("STATUS_ID")
        result["SCRAM_STATUS"] = record.get("ABORT_EXECUTE_FLAG")

    # ステータス更新制御
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

    update_status_flg = False
    # パラメータのステータスが、実行中, 実行中(遅延)の場合 / 他
    if status in [AnscConst.PROCESSING, AnscConst.PROCESS_DELAYED]:
        # ステータス更新: 実行中->実行中(遅延)に変更する場合のみ
        if current_status == AnscConst.PROCESSING and status == AnscConst.PROCESS_DELAYED:
            update_status_flg = True
        # ステータス更新: 実行待ち->実行中に変更する場合のみ
        elif current_status == AnscConst.PROCESSING_WAIT and status == AnscConst.PROCESSING:
            update_status_flg = True
        else:
            # 最終更新日時のみ：実行中->実行中, 実行中(遅延)->実行中 , 実行中(遅延)->実行中(遅延)
            update_status_flg = False
    else:
        # ステータス更新: 完了、完了(異常)、想定外エラー,緊急停止
        update_status_flg = True

    # トランザクション開始
    objdbca.db_transaction_start()

    if update_status_flg:
        # ステータス更新
        data_list = {"EXECUTION_NO": execution_no, "STATUS_ID": status}
        objdbca.table_update(t_exec_sts_inst, data_list, "EXECUTION_NO")
    else:
        # 最終更新日時のみ更新: 履歴なし
        data_list = {"EXECUTION_NO": execution_no}
        objdbca.table_update(t_exec_sts_inst, data_list, "EXECUTION_NO", is_register_history=False, last_timestamp=True)

    # コミット/トランザクション終了
    objdbca.db_transaction_end(True)

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

    if driver_id == "legacy":
        t_exec_sts_inst = t_ansl_exec_sts_inst
    elif driver_id == "pioneer":
        t_exec_sts_inst = t_ansp_exec_sts_inst
    elif driver_id == "legacy_role":
        t_exec_sts_inst = t_ansr_exec_sts_inst


    conductor_instance_no = None

    # 作業インスタンス取得
    where = 'WHERE  DISUSE_FLAG = %s AND EXECUTION_NO = %s'
    parameter = ['0', execution_no]
    ret = objdbca.table_select(t_exec_sts_inst, where, parameter)
    if ret:
        conductor_instance_no = ret[0].get("CONDUCTOR_INSTANCE_NO", None) if len(ret) == 1 else None

    # パス
    dir_path = f"/storage/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}"
    tmp_basse_path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/"
    tmp_path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/{execution_no}"
    conductor_dir_path = f"/storage/{organization_id}/{workspace_id}/driver/conductor/{conductor_instance_no}"
    tmp_c_path = f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}/conductor"
    gztar_path = f"{tmp_path}/{execution_no}.tar.gz"

    try:
        # tmp_pathの初期化
        shutil.rmtree(tmp_basse_path) if os.path.exists(tmp_basse_path) else None

        # execution_no/*
        # dir_path -> tmp_path に移動
        if os.path.exists(dir_path):
            if not os.path.isdir(tmp_path):
                shutil.copytree(dir_path, tmp_path)
                g.applogger.debug(f"shutil.copytree({dir_path}, {tmp_path})")

        # __conductor_workflowdir__/*
        if conductor_instance_no:
            # conductor_dir_path -> tmp_c_path に移動: conductor_dir_path無ければ作成
            if not os.path.exists(conductor_dir_path):
                os.makedirs(conductor_dir_path)
                os.chmod(conductor_dir_path, 0o777)
                g.applogger.debug(f"os.makedirs, os.chmod, ({conductor_dir_path})")

            if os.path.isdir(conductor_dir_path):
                shutil.copytree(conductor_dir_path, tmp_c_path)
                g.applogger.debug(f"shutil.copytree({conductor_dir_path}, {tmp_c_path})")
        else:
            # tmp_c_pathをdummyで空作成
            if not os.path.exists(tmp_c_path):
                os.makedirs(tmp_c_path)
                os.chmod(tmp_c_path, 0o777)
                g.applogger.debug(f"os.makedirs, os.chmod, ({tmp_c_path})")

        # tar.gz
        with tarfile.open(gztar_path, "w:gz") as tar:
            tar.add(tmp_basse_path, arcname="")
        g.applogger.debug(f"tarfile.open({gztar_path}, 'w:gz'):  tar.add({tmp_basse_path})")

    finally:
        # clear tmp_path
        if os.path.isdir(tmp_path):
            for _tp in glob.glob(f"{tmp_path}/*", recursive=True):
                if os.path.isdir(_tp):
                    shutil.rmtree(_tp)
                    g.applogger.debug(f"shutil.rmtree({_tp})")

        with tarfile.open(gztar_path, 'r:gz') as tar:
            g.applogger.debug(f"{tar.getmembers()=}")


    return gztar_path


def update_result(objdbca, organization_id, workspace_id, execution_no, parameters, file_path):
    """
        通知されたファイルの更新
        ARGS:
            organization_id:OrganizationID
            workspace_id: WorkspaceID
            execution_no: 作業番号
        RETRUN:
            statusCode, {}, msg
    """

    # 各テーブル
    t_ansl_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
    t_ansp_exec_sts_inst = "T_ANSP_EXEC_STS_INST"
    t_ansr_exec_sts_inst = "T_ANSR_EXEC_STS_INST"

    # ドライバーID
    driver_id = parameters["driver_id"]
    # ステータス
    status = parameters["status"]

    if driver_id == "legacy":
        t_exec_sts_inst = t_ansl_exec_sts_inst
    elif driver_id == "pioneer":
        t_exec_sts_inst = t_ansp_exec_sts_inst
    elif driver_id == "legacy_role":
        t_exec_sts_inst = t_ansr_exec_sts_inst

    current_status_id = None
    allowed_update_status = [
        AnscConst.PROCESSING,       # 実行中
        AnscConst.PROCESS_DELAYED,  # 実行中(遅延)
        AnscConst.PREPARE_COMPLETE, # 準備完了
        AnscConst.PROCESSING_WAIT,  # 実行待ち
    ]

    # 作業インスタンス取得
    where = 'WHERE DISUSE_FLAG = %s AND EXECUTION_NO = %s'
    parameter = ['0', execution_no]
    ret = objdbca.table_select(t_exec_sts_inst, where, parameter)
    if ret:
        current_status_id = ret[0].get("STATUS_ID", None) if len(ret) == 1 else None

    # 準備完了～実行中ステータスの場合以外、ファイルの更新はさせない
    if current_status_id and current_status_id not in allowed_update_status:
        return {}

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
            os.makedirs(tmp_path + file_key)
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

    return {}

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

    # コミット/トランザクション終了
    objdbca.db_transaction_end(True)

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
                file_size_str = f"{int(file_size):,} byte(s)"
                storage = storage_base()
                can_save, free_space = storage.validate_disk_space(file_size)
                if can_save is False:
                    status_code = "499-00222"
                    log_msg_args = [file_size_str]
                    api_msg_args = [file_size_str]
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