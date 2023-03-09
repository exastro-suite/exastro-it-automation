#   Copyright 2023 NEC Corporation
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
from flask import g
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.common.exception import AppException
from common_libs.terraform_driver.cloud_ep.RestApiCaller import RestApiCaller
from common_libs.terraform_driver.cloud_ep.terraform_restapi import *  # noqa: F403


def execution_scram(objdbca, execution_no):
    """
        緊急停止を実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            execution_no: 作業実行ID
        RETRUN:
            boolean
    """
    # ステータスを確認するのでテーブルをロック
    objdbca.table_lock(TFCloudEPConst.T_EXEC_STS_INST)

    # 作業実行IDの対象が存在することを確認
    where_str = 'WHERE EXECUTION_NO = %s AND DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCloudEPConst.T_EXEC_STS_INST, where_str, [execution_no, 0])
    if not ret:
        # 指定された作業番号が存在しない。
        raise AppException("499-00903", [execution_no], [execution_no])
    t_exec_sts_inst_record = ret[0]

    # ステータスが「実行中」「実行中(遅延)」であるかを判定
    status_id = t_exec_sts_inst_record.get('STATUS_ID')
    if not str(status_id) == TFCloudEPConst.STATUS_PROCESSING and not str(status_id) == TFCloudEPConst.STATUS_PROCESS_DELAYED:
        # ステータスが「実行中」「実行中(遅延)」以外の場合は、緊急停止対象外のため終了
        if g.LANGUAGE == 'ja':
            sql = "SELECT EXEC_STATUS_NAME_JA AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
        else:
            sql = "SELECT EXEC_STATUS_NAME_EN AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
        rows = objdbca.sql_execute(sql, [str(status_id)])
        row = rows[0]
        #  緊急停止できる状態ではない
        raise AppException("499-00904", [row["NAME"]], [row["NAME"]])

    # RUN-IDを取得
    run_id = t_exec_sts_inst_record.get('TERRAFORM_RUN_ID')
    if not run_id:
        # 対象作業のRUN-IDを特定できませんでした。(作業No.:{})
        raise AppException("499-00914", [execution_no], [execution_no])

    # 「インターフェース情報」取得
    where_str = 'WHERE DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCloudEPConst.T_IF_INFO, where_str, [0])

    # 「インターフェース情報」レコードが1つではない場合エラー
    if not len(ret) == 1:
        raise AppException("499-01103", [], [])

    # 「インターフェース情報」のレコードを変数にセット
    if_protocol = ret[0].get('TERRAFORM_PROTOCOL')
    if_hostname = ret[0].get('TERRAFORM_HOSTNAME')
    if_port = ret[0].get('TERRAFORM_PORT')
    if_token = ret[0].get('TERRAFORM_TOKEN')
    if_proxy_address = ret[0].get('TERRAFORM_PROXY_ADDRESS')
    if_proxy_port = ret[0].get('TERRAFORM_PROXY_PORT')

    # RESTAPI用Class呼び出し
    proxy_setting = {'address': if_proxy_address, "port": if_proxy_port}
    restApiCaller = RestApiCaller(if_protocol, if_hostname, if_port, if_token, proxy_setting)

    # トークンをセット
    restApiCaller.authorize()

    # 緊急停止RESTAPIを実行
    response_array = cancel_run(restApiCaller, run_id)  # noqa: F405
    response_status_code = response_array.get('statusCode')

    # ステータスコードが202の場合正常にキャンセル要求を終えた。(それ以外の場合にエラー判定)
    if not response_status_code == 202:
        if response_status_code == 409:
            # PlanおよびApplyはキャンセルできない状態です。(作業No: {})
            raise AppException("499-00914", [execution_no], [execution_no])
        else:
            # 緊急停止できませんでした。連携先Terraformの状況をご確認ください。(作業No.:{})
            raise AppException("499-00915", [execution_no], [execution_no])

    return True
