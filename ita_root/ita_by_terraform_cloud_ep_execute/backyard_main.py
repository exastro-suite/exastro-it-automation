# Copyright 2023 NEC Corporation#
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
from flask import g
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import get_timestamp
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.common.SubValueAutoReg import SubValueAutoReg
from libs.common_functions import update_execution_record
from common_libs.terraform_driver.cloud_ep.terraform_restapi import *  # noqa: F403
from libs.execute_terraform_run import execute_terraform_run
from libs.check_terraform_condition import check_terraform_condition


def backyard_main(organization_id, workspace_id):
    """
        Terraform Cloud/EP backyardメイン処理
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETRUN:

    """
    # メイン処理開始
    g.applogger.debug(g.appmsg.get_log_message("BKY-00001"))

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    error_flag = False

    # 「未実行」「未実行(予約)」の作業インスタンスを取得し、ステータスを「準備中」に変更する
    retBool = instance_prepare(objdbca)
    if retBool is False:
        error_flag = True

    # 「準備中」の作業インスタンスを取得し、TerraformのRUNまでの作業を行う。最後にステータスを「実行中」に変更する。
    retBool = instance_execute(objdbca)
    if retBool is False:
        error_flag = True

    # 「実行中」「実行中(遅延)」の作業インスタンスを取得し、TerraformのRUN状態を監視する。最後にステータスを「完了」に変更する。
    retBool = instance_check(objdbca)
    if retBool is False:
        error_flag = True

    if error_flag is False:
        # 正常終了
        g.applogger.debug(g.appmsg.get_log_message("BKY-00002"))
    else:
        # エラーが一つでもある
        g.applogger.debug(g.appmsg.get_log_message("BKY-00003"))


def instance_prepare(objdbca):
    """
        「未実行」「未実行(予約)」の作業インスタンスを取得し、ステータスを「準備中」に変更する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
        RETRUN:

    """
    error_flg = False

    # 作業管理テーブルをロック
    objdbca.table_lock([TFCloudEPConst.T_EXEC_STS_INST])

    # 「作業管理」からステータスが「未実行」「未実行(予約)」の作業インスタンスを取得する。(ただし「未実行(予約)」は予約日時(TIME_BOOK)が現時刻を過ぎているものが対象)
    where_str = 'WHERE (STATUS_ID = %s) OR (STATUS_ID = %s AND TIME_BOOK <= %s) AND DISUSE_FLAG = %s ORDER BY TIME_REGISTER'
    not_execute_list = objdbca.table_select(TFCloudEPConst.T_EXEC_STS_INST, where_str, [TFCloudEPConst.STATUS_NOT_YET, TFCloudEPConst.STATUS_RESERVE, get_timestamp(), 0])  # noqa: E501

    # 「未実行」の対象レコードの分だけループし、ステータスを「準備中」に変更
    for record in not_execute_list:
        try:
            # トランザクション開始
            objdbca.db_transaction_start()

            # ステータス更新用データを作成
            execution_no = record.get('EXECUTION_NO')
            update_data = {
                "EXECUTION_NO": execution_no,
                "STATUS_ID": TFCloudEPConst.STATUS_PREPARE,
                "TIME_START": get_timestamp(),
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            ret, execute_data = update_execution_record(objdbca, TFCloudEPConst, update_data)
            if ret:
                objdbca.db_commit()
                g.applogger.debug(g.appmsg.get_log_message("BKY-51001", [execution_no]))
            else:
                log_msg = g.appmsg.get_log_message("BKY-50101", [])  # Failed to update status.
                g.applogger.error(log_msg)
                raise Exception()

            # トランザクション終了
            objdbca.db_transaction_end(True)

        except Exception:
            # トランザクション終了
            objdbca.db_transaction_end(False)

            # エラーフラグ
            error_flg = True

    if error_flg:
        return False
    else:
        return True


def instance_execute(objdbca):
    """
        「準備中」の作業インスタンスを取得し、TerraformのRUNまでの作業を行う。最後にステータスを「実行中」に変更する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
        RETRUN:

    """
    error_flg = False

    # 作業管理テーブルをロック
    objdbca.table_lock([TFCloudEPConst.T_EXEC_STS_INST])

    # 「作業管理」からステータスが「準備中」の作業インスタンスを取得する。
    where_str = 'WHERE (STATUS_ID = %s) AND DISUSE_FLAG = %s ORDER BY TIME_REGISTER'
    prepare_list = objdbca.table_select(TFCloudEPConst.T_EXEC_STS_INST, where_str, [TFCloudEPConst.STATUS_PREPARE, 0])  # noqa: E501

    # 「準備中」の対象レコードの分だけループし、TerraformのRUNまでの作業を行う。
    for record in prepare_list:
        try:
            # トランザクション開始
            objdbca.db_transaction_start()

            # パラメータを抽出
            run_mode = record.get('RUN_MODE')
            movement_id = record.get('MOVEMENT_ID')
            operation_id = record.get('OPERATION_ID')
            execution_no = record.get('EXECUTION_NO')

            # 実行種別が「作業実行」「Plan確認」「パラメータ確認」なら代入値自動登録設定から代入値管理へレコードを登録
            if run_mode == TFCloudEPConst.RUN_MODE_PARAM or run_mode == TFCloudEPConst.RUN_MODE_APPLY or run_mode == TFCloudEPConst.RUN_MODE_PLAN:
                g.applogger.debug("[Process] Start register records in substituted value management. (Execution No.:{})".format(execution_no))
                sub_value_auto_reg = SubValueAutoReg(objdbca, TFCloudEPConst, operation_id, movement_id, execution_no)
                result, msg = sub_value_auto_reg.set_assigned_value_from_parameter_sheet()
                if not result:
                    # 代入値自動登録設定から代入値管理へのレコード登録に失敗
                    raise Exception(msg)

            # 実行種別が「パラメータ確認」ならステータスを「完了」としてcontinue。
            if run_mode == TFCloudEPConst.RUN_MODE_PARAM:
                update_data = {
                    "EXECUTION_NO": execution_no,
                    "STATUS_ID": TFCloudEPConst.STATUS_COMPLETE,
                    "TIME_END": get_timestamp(),
                    "DISUSE_FLAG": "0",
                    "LAST_UPDATE_USER": g.get('USER_ID')
                }
                ret, execute_data = update_execution_record(objdbca, TFCloudEPConst, update_data)
                if ret:
                    objdbca.db_commit()
                    g.applogger.debug(g.appmsg.get_log_message("BKY-51004", [execution_no]))
                continue

            if run_mode == TFCloudEPConst.RUN_MODE_APPLY or run_mode == TFCloudEPConst.RUN_MODE_PLAN:
                # 実行種別が「作業実行」「Plan確認」なら連携先Terraformに対しRUNを実行
                g.applogger.debug("[Process] Start execute terraform run. (Execution No.:{})".format(execution_no))
                result = execute_terraform_run(objdbca, record, False)
                if not result:
                    # 作業実行に失敗
                    raise Exception()

            elif run_mode == TFCloudEPConst.RUN_MODE_DESTROY:
                # 実行種別が「リソース削除」なら連携先Terraformに対しDestroyを実行
                g.applogger.debug("[Process] Start execute terraform run(Destroy). (Execution No.:{})".format(execution_no))
                result = execute_terraform_run(objdbca, record, True)
                if not result:
                    # リソース削除に失敗
                    raise Exception()
            else:
                # 実行種別が不正
                log_msg = g.appmsg.get_log_message("MSG-00027", [execution_no])
                g.applogger.info(log_msg)
                raise Exception()

            # トランザクション終了
            objdbca.db_transaction_end(True)

        except Exception:
            # トランザクション終了
            objdbca.db_transaction_end(False)

            # ステータスを「想定外エラー」に変更する
            update_data = {
                "EXECUTION_NO": execution_no,
                "STATUS_ID": TFCloudEPConst.STATUS_EXCEPTION,
                "TIME_END": get_timestamp(),
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            ret, execute_data = update_execution_record(objdbca, TFCloudEPConst, update_data)
            if not ret:
                log_msg = g.appmsg.get_log_message("BKY-50101", [])  # Failed to update status.
                g.applogger.error(log_msg)
            else:
                objdbca.db_commit()
                g.applogger.debug(g.appmsg.get_log_message("BKY-51006", [execution_no]))

            # エラーフラグ
            error_flg = True

    if error_flg:
        return False
    else:
        return True


def instance_check(objdbca):
    """
        「実行中」「実行中(遅延)」の作業インスタンスを取得し、TerraformのRUN状態を監視する。最後にステータスを「完了」に変更する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
        RETRUN:

    """
    error_flg = False

    # 作業管理テーブルをロック
    objdbca.table_lock([TFCloudEPConst.T_EXEC_STS_INST])

    # 「作業管理」からステータスが「実行中」「実行中(遅延)」の作業インスタンスを取得する。
    where_str = 'WHERE (STATUS_ID = %s) OR (STATUS_ID = %s) AND DISUSE_FLAG = %s ORDER BY TIME_REGISTER'
    executed_list = objdbca.table_select(TFCloudEPConst.T_EXEC_STS_INST, where_str, [TFCloudEPConst.STATUS_PROCESSING, TFCloudEPConst.STATUS_PROCESS_DELAYED, 0])  # noqa: E501

    # 「実行中」の対象レコードの分だけループし、Terraformの実行状況の監視を行う。
    for record in executed_list:
        try:
            # トランザクション開始
            objdbca.db_transaction_start()

            # パラメータを抽出
            execution_no = record.get('EXECUTION_NO')

            # メイン処理2（連携先TerraformのRUNの状態を監視する）
            g.applogger.debug("[Process] Start check condition. (Execution No.:{})".format(execution_no))
            result = check_terraform_condition(objdbca, record)
            if not result:
                # RUNの状態確認に失敗
                raise Exception()

            # トランザクション終了
            objdbca.db_transaction_end(True)

        except Exception:
            # トランザクション終了
            objdbca.db_transaction_end(False)

            # ステータスを「想定外エラー」に変更する
            update_data = {
                "EXECUTION_NO": execution_no,
                "STATUS_ID": TFCloudEPConst.STATUS_EXCEPTION,
                "TIME_END": get_timestamp(),
                "DISUSE_FLAG": "0",
                "LAST_UPDATE_USER": g.get('USER_ID')
            }
            ret, execute_data = update_execution_record(objdbca, TFCloudEPConst, update_data)
            if not ret:
                log_msg = g.appmsg.get_log_message("BKY-50101", [])  # Failed to update status.
                g.applogger.error(log_msg)
            else:
                objdbca.db_commit()
                g.applogger.debug(g.appmsg.get_log_message("BKY-51006", [execution_no]))

            # エラーフラグ
            error_flg = True

    if error_flg:
        return False
    else:
        return True
