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
from common_libs.common.util import get_timestamp, ky_encrypt
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from libs.common_functions import update_execution_record
from common_libs.terraform_driver.cloud_ep.terraform_restapi import *  # noqa: F403
import time
import json
import os
import shutil


def check_terraform_condition(objdbca, instance_data):  # noqa: C901
    """
        RUNを実行中のTerraformから状態を取得する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            instance_data: 対象の作業インスタンスのレコード
        RETRUN:

    """
    try:
        # 変数定義
        execution_no = instance_data.get('EXECUTION_NO')
        tf_workspace_id = instance_data.get('I_WORKSPACE_ID')
        tf_workspace_name = instance_data.get('I_WORKSPACE_NAME')
        run_mode = instance_data.get('RUN_MODE')
        tf_run_id = instance_data.get('TERRAFORM_RUN_ID')
        set_status_id = None
        status_update_flag = False  # ステータス更新フラグ
        make_zip_flag = False  # ZIPファイル(ResultData.zip)作成フラグ
        time_limit_check_flag = False  # 実行中(遅延)確認フラグ
        plan_complete_flag = False  # Plan完了フラグ
        policy_check_start_flag = False  # PolicyCheck開始フラグ
        policy_check_failed_flag = False  # PolicyCheck失敗フラグ
        get_state_file_flag = False  # Stateファイル取得フラグ
        msg = ''
        update_data = {}
        result_data_rename_dir_path = None  # 結果データの格納先

        # ディレクトリ/ログファイル定義
        base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
        temp_dir = base_dir + TFCloudEPConst.DIR_TEMP + '/' + execution_no
        log_dir = base_dir + TFCloudEPConst.DIR_EXECUTE + '/' + execution_no + '/out'
        error_log = log_dir + '/error.log'
        plan_log = log_dir + '/plan.log'
        policy_check_log = log_dir + '/policyCheck.log'
        apply_log = log_dir + '/apply.log'

        # インターフェース情報を取得する
        ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
        if not ret:
            log_msg = g.appmsg.get_log_message("MSG-82001", [])
            g.applogger.info(log_msg)
            msg = g.appmsg.get_api_message("MSG-82001", [])
            raise Exception(msg)

        # RESTAPIコールクラス
        ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
        if not ret:
            log_msg = g.appmsg.get_log_message("MSG-82002", [])
            g.applogger.info(log_msg)
            msg = g.appmsg.get_api_message("MSG-82002", [])
            raise Exception(msg)

        # tf_workspace_idをもとにORGANIZATION_WORKSPACEビューからレコードを取得
        where_str = 'WHERE WORKSPACE_ID = %s AND DISUSE_FLAG = %s'
        ret = objdbca.table_select(TFCloudEPConst.V_ORGANIZATION_WORKSPACE, where_str, [tf_workspace_id, 0])
        if not ret:
            log_msg = g.appmsg.get_log_message("MSG-82003", [tf_workspace_name])
            g.applogger.info(log_msg)
            msg = g.appmsg.get_api_message("MSG-82003", [tf_workspace_name])
            raise Exception(msg)

        # 対象のtf_organizationとtf_workspaceを特定する
        tf_organization_name = ret[0].get('ORGANIZATION_NAME')
        tf_workspace_name = ret[0].get('WORKSPACE_NAME')

        # [RESTAPI]RUN-IDの対象からステータスを取得
        g.applogger.info(g.appmsg.get_log_message("BKY-51024", [execution_no, tf_run_id]))
        response_array = get_run_data(restApiCaller, tf_run_id)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if not response_status_code == 200:
            log_msg = g.appmsg.get_log_message("MSG-82032", [tf_workspace_name])
            g.applogger.info(log_msg)
            msg = "[API Error]" + g.appmsg.get_api_message("MSG-82032", [tf_workspace_name])
            raise Exception(msg)
        g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

        # Terraform Runの詳細からステータス/Planの実行ID/Applyの実行IDを取得する
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        attributes = respons_contents_data.get('attributes')
        relationships = respons_contents_data.get('relationships')
        tf_run_status = attributes.get('status')  # RUNステータス
        tf_plan_id = relationships['plan']['data']['id']  # Plan ID
        tf_apply_id = relationships['apply']['data']['id']  # Apply ID
        is_confirmable = attributes['actions']['is-confirmable']  # Apply実行可能フラグ
        is_discardable = attributes['actions']['is-discardable']  # 実行中止可能フラグ

        # [RESTAPI]Planの詳細データを取得
        g.applogger.info(g.appmsg.get_log_message("BKY-51025", [execution_no]))
        response_array = get_plan_data(restApiCaller, tf_plan_id)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if not response_status_code == 200:
            log_msg = g.appmsg.get_log_message("MSG-82033", [tf_workspace_name])
            g.applogger.info(log_msg)
            msg = "[API Error]" + g.appmsg.get_api_message("MSG-82033", [tf_workspace_name])
            raise Exception(msg)
        g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

        # Planの詳細からステータス/PlanLog取得URLを取得
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        attributes = respons_contents_data.get('attributes')
        tf_plan_status = attributes.get('status')  # Planステータス
        tf_plan_log_url = attributes.get('log-read-url')

        # Planログファイルがなければ生成
        if os.path.isfile(plan_log) is False:
            with open(plan_log, 'w'):
                pass

        # [RESTAPI]Planログを取得し、plan.logに書き込み(上書き)
        g.applogger.info(g.appmsg.get_log_message("BKY-51026", [execution_no]))
        content_log = get_run_log(restApiCaller, tf_plan_log_url, True)  # noqa: F405
        with open(plan_log, 'w') as f:
            f.write(content_log)
        g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

        # Planのステータスから次の処理の動きを判定する
        if tf_plan_status == TFCloudEPConst.TF_PLAN_ERROR:
            # 「errored」の場合
            set_status_id = TFCloudEPConst.STATUS_FAILURE  # 完了(異常)
            status_update_flag = True
            make_zip_flag = True
        elif tf_plan_status == TFCloudEPConst.TF_PLAN_FINISH:
            # 「finished」の場合
            time_limit_check_flag = True
            policy_check_start_flag = True
            plan_complete_flag = True
        elif tf_plan_status == TFCloudEPConst.TF_PLAN_CANCEL or tf_run_status == TFCloudEPConst.TF_RUN_CANCEL:
            # 「canceled」の場合
            set_status_id = TFCloudEPConst.STATUS_SCRAM  # 緊急停止
            status_update_flag = True
            make_zip_flag = True
        elif tf_plan_status == TFCloudEPConst.TF_PLAN_RUNNING:
            # 「running」の場合
            time_limit_check_flag = True
        # else:
        #     # それ以外(何もしない)

        # PolicyCheck開始判定
        if plan_complete_flag or policy_check_start_flag:
            # [RESTAPI]Policy-checkの詳細データを取得
            g.applogger.info(g.appmsg.get_log_message("BKY-51027", [execution_no]))
            response_array = get_policy_check_data(restApiCaller, tf_run_id)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 200:
                log_msg = g.appmsg.get_log_message("MSG-82034", [tf_workspace_name])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82034", [tf_workspace_name])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # PolicyCheckの有無を判定(無ければ次の処理へ)
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            if respons_contents_data:
                # Policy-checkの詳細からステータス/Policy-checklog取得URLを取得
                attributes = respons_contents_data[0].get('attributes')
                policy_check_status = attributes.get('status')  # PolicyCheckステータス
                policy_result = attributes.get('result')
                policy_output_url = respons_contents_data[0].get('links', {}).get('output', {})
                if policy_output_url:
                    # [RESTAPI]PolicyCheckログを取得し、policy_check_logに書き込み(上書き)
                    g.applogger.info(g.appmsg.get_log_message("BKY-51028", [execution_no]))
                    content_log = get_run_log(restApiCaller, policy_output_url, False)  # noqa: F405
                    with open(policy_check_log, 'w') as f:
                        f.write(content_log)
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                # PolicyCheckの緊急停止判定
                if policy_check_status == TFCloudEPConst.TF_POLICY_CANCEL and tf_run_status == TFCloudEPConst.TF_RUN_CANCEL:
                    set_status_id = TFCloudEPConst.STATUS_SCRAM  # 緊急停止
                    status_update_flag = True
                    make_zip_flag = True
                    policy_check_failed_flag = True

                else:
                    # PolicyCheckの結果判定
                    if policy_result is False:
                        # PolicyCheck失敗時
                        set_status_id = TFCloudEPConst.STATUS_FAILURE  # 完了(異常)
                        status_update_flag = True
                        make_zip_flag = True
                        policy_check_failed_flag = True
                    else:
                        # PolicyCheck成功時
                        policy_check_failed_flag = False

        # Apply開始判定
        if plan_complete_flag and policy_check_failed_flag is False:
            # Applyを実行しているかどうかの判定
            if is_confirmable and is_discardable:
                # Applyを実行していない場合
                if run_mode == TFCloudEPConst.RUN_MODE_PLAN:
                    # [RESTAPI]「Plan確認」の場合はRUN-IDに対してApplyを中止する
                    g.applogger.info(g.appmsg.get_log_message("BKY-51029", [execution_no, tf_run_id]))
                    response_array = apply_discard(restApiCaller, tf_run_id)  # noqa: F405
                    response_status_code = response_array.get('statusCode')
                    if not response_status_code == 202:
                        log_msg = g.appmsg.get_log_message("MSG-82035", [tf_workspace_name])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82035", [tf_workspace_name])
                        raise Exception(msg)
                    else:
                        # Applyの中止に成功。各フラグを設定
                        set_status_id = TFCloudEPConst.STATUS_COMPLETE  # 完了
                        status_update_flag = True
                        make_zip_flag = True
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                else:
                    # [RESTAPI]「Plan確認」以外（通常、リソース削除）の場合はRUN-IDに対してApplyを実行する(成功時は何もせずに処理を進める。)
                    g.applogger.info(g.appmsg.get_log_message("BKY-51030", [execution_no, tf_run_id]))
                    response_array = apply_execution(restApiCaller, tf_run_id)  # noqa: F405
                    response_status_code = response_array.get('statusCode')
                    if not response_status_code == 202:
                        log_msg = g.appmsg.get_log_message("MSG-82036", [tf_workspace_name])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82036", [tf_workspace_name])
                        raise Exception(msg)
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            else:
                # Applyを実行している場合
                # [RESTAPI]Applyの詳細データを取得
                g.applogger.info(g.appmsg.get_log_message("BKY-51031", [execution_no]))
                response_array = get_apply_data(restApiCaller, tf_apply_id)  # noqa: F405
                response_status_code = response_array.get('statusCode')
                if not response_status_code == 200:
                    log_msg = g.appmsg.get_log_message("MSG-82037", [tf_workspace_name])
                    g.applogger.info(log_msg)
                    msg = "[API Error]" + g.appmsg.get_api_message("MSG-82037", [tf_workspace_name])
                    raise Exception(msg)
                g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                # Planの詳細からステータス/PlanLog取得URLを取得
                respons_contents_json = response_array.get('responseContents')
                respons_contents = json.loads(respons_contents_json)
                respons_contents_data = respons_contents.get('data')
                attributes = respons_contents_data.get('attributes')
                tf_apply_status = attributes.get('status')  # Applyステータス
                tf_apply_log_url = attributes.get('log-read-url')

                # Applyログファイルがなければ生成
                if os.path.isfile(apply_log) is False:
                    with open(apply_log, 'w'):
                        pass

                # [RESTAPI]Applyログを取得し、apply.logに書き込み(上書き)
                g.applogger.info(g.appmsg.get_log_message("BKY-51032", [execution_no]))
                content_log = get_run_log(restApiCaller, tf_apply_log_url, True)  # noqa: F405
                with open(apply_log, 'w') as f:
                    f.write(content_log)
                g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                # Applyのステータスから次の処理の動きを判定する
                if tf_apply_status == TFCloudEPConst.TF_APPLY_ERROR:
                    # 「errored」の場合
                    set_status_id = TFCloudEPConst.STATUS_FAILURE  # 完了(異常)
                    status_update_flag = True
                    make_zip_flag = True
                elif tf_apply_status == TFCloudEPConst.TF_APPLY_FINISH:
                    # 「finished」の場合
                    set_status_id = TFCloudEPConst.STATUS_COMPLETE  # 完了
                    status_update_flag = True
                    get_state_file_flag = True
                    make_zip_flag = True
                elif tf_apply_status == TFCloudEPConst.TF_APPLY_CANCEL or tf_run_status == TFCloudEPConst.TF_RUN_CANCEL:
                    # 「canceled」の場合
                    set_status_id = TFCloudEPConst.STATUS_SCRAM  # 緊急停止
                    status_update_flag = True
                    make_zip_flag = True
                elif tf_apply_status == TFCloudEPConst.TF_APPLY_UNREACH:
                    # 「unreachable」(Plab/PolicyCheckの結果、Applyを実行しないと判断された)の場合
                    set_status_id = TFCloudEPConst.STATUS_COMPLETE  # 完了
                    status_update_flag = True
                    make_zip_flag = True
                elif tf_apply_status == TFCloudEPConst.TF_APPLY_RUNNING:
                    # 「running」の場合
                    time_limit_check_flag = True
                # else:
                #     # それ以外(何もしない)

        # stateファイル取得処理
        if get_state_file_flag:
            # [RESTAPI]stateの一覧取得APIを実行(最新の10件)
            g.applogger.info(g.appmsg.get_log_message("BKY-51033", [execution_no]))
            response_array = get_workspace_state_version(restApiCaller, tf_organization_name, tf_workspace_name)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 200:
                log_msg = g.appmsg.get_log_message("MSG-82038", [tf_workspace_name])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82038", [tf_workspace_name])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # 取得したStateの一覧をループし、RUN-IDが一致する対象を取得
            tf_state_url = ''
            tf_state_id = ''
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for state_data in respons_contents_data:
                target_run_id = state_data['relationships']['run']['data']['id']
                if tf_run_id == target_run_id:
                    tf_state_url = state_data['attributes']['hosted-state-download-url']
                    tf_state_id = state_data.get('id')
                    outputs = state_data['relationships']['outputs']['data']
                    break

            # [RESTAPI]stateファイルを取得し、ky_encryptをかけたものを生成する。
            g.applogger.info(g.appmsg.get_log_message("BKY-51034", [execution_no]))
            if tf_state_url and tf_state_id:
                tf_state_org = get_run_log(restApiCaller, tf_state_url, True)  # noqa: F405
                if tf_state_org:
                    tf_state_enc = ky_encrypt(tf_state_org)
                    tf_state_file = log_dir + '/' + tf_state_id + '.tfstate'
                    with open(tf_state_file, 'w') as f:
                        f.write(tf_state_enc)
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))
                else:
                    log_msg = g.appmsg.get_log_message("MSG-82039", [tf_workspace_name])
                    g.applogger.info(log_msg)
                    msg = "[API Error]" + g.appmsg.get_api_message("MSG-82039", [tf_workspace_name])
                    set_status_id = TFCloudEPConst.STATUS_FAILURE  # ステータスを「完了(異常)」に設定
                    # エラーログに追記
                    with open(error_log, 'w') as f:
                        f.write(str(msg))
            else:
                log_msg = g.appmsg.get_log_message("MSG-82039", [tf_workspace_name])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82039", [tf_workspace_name])
                set_status_id = TFCloudEPConst.STATUS_FAILURE  # ステータスを「完了(異常)」に設定
                # エラーログに追記
                with open(error_log, 'w') as f:
                    f.write(str(msg))

            # Conductorから実行されている場合、outputの結果を格納する
            conductor_instance_no = instance_data.get('CONDUCTOR_INSTANCE_NO')
            if conductor_instance_no:
                output_data = {}
                for output in outputs:
                    state_version_output_id = output.get('id')
                    # [RESTAPI]outputを取得
                    g.applogger.info(g.appmsg.get_log_message("BKY-51035", [execution_no]))
                    response_array = get_outputs(restApiCaller, state_version_output_id)  # noqa: F405
                    response_status_code = response_array.get('statusCode')
                    if not response_status_code == 200:
                        log_msg = g.appmsg.get_log_message("MSG-82040", [tf_workspace_name])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82040", [tf_workspace_name])
                        set_status_id = TFCloudEPConst.STATUS_FAILURE  # ステータスを「完了(異常)」に設定
                        # エラーログに追記
                        with open(error_log, 'w') as f:
                            f.write(str(msg))
                    else:
                        # output_dataに取得結果を格納する
                        respons_contents_json = response_array.get('responseContents')
                        respons_contents = json.loads(respons_contents_json)
                        respons_contents_data = respons_contents.get('data')
                        attributes = respons_contents_data.get('attributes')
                        output_name = attributes.get('name')
                        output_value = attributes.get('value')
                        output_sensitive = attributes.get('sensitive')
                        output_type = attributes.get('type')
                        output_detail = {'sensitive': output_sensitive, 'type': output_type, 'value': output_value}
                        output_data[output_name] = output_detail
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                # output_dataをjson化
                output_data_json = json.dumps(output_data, ensure_ascii=False, indent=2, sort_keys=True, separators=(',', ': '))
                # 格納先のディレクトリを指定
                output_dir = base_dir + '/driver/conductor/' + str(conductor_instance_no) + '/'
                # output_dataのjsonファイルを保存
                output_file_name = 'terraform_output_' + str(execution_no) + '.json'
                output_data_full = output_dir + output_file_name
                with open(output_data_full, 'w') as f:
                    f.write(output_data_json)

        # 遅延タイマーチェックフラグがTrueの場合かつ、ステータス更新フラグがFalseの場合、遅延タイマーチェック処理を実行する
        if time_limit_check_flag and status_update_flag is False:
            if instance_data.get('I_TIME_LIMIT'):
                time_limit = int(instance_data.get('I_TIME_LIMIT'))
            else:
                time_limit = None
            current_status = instance_data.get('STATUS_ID')
            # ステータスが「実行中」かつ遅延タイマーが設定されている場合、遅延チェック処理を実行
            if current_status == TFCloudEPConst.STATUS_PROCESSING and time_limit:
                # 開始時刻(「エポック秒.マイクロ秒」)を生成(localタイムでutcタイムではない)
                start_time_unixtime = instance_data.get('TIME_START').timestamp()
                # 開始時刻(マイクロ秒)＋制限時間(分→秒)＝制限時刻(マイクロ秒)
                limit_unixtime = start_time_unixtime + (time_limit * 60)
                # 現在時刻(「エポック秒.マイクロ秒」)を生成(localタイムでutcタイムではない)
                now_unixtime = time.time()
                # 制限時刻と現在時刻を比較
                if limit_unixtime < now_unixtime:
                    # 遅延が検出された場合、ステータスを「実行中(遅延)」に変更する。
                    g.applogger.debug(g.appmsg.get_log_message("BKY-51036", [execution_no]))
                    status_update_flag = True
                    set_status_id = TFCloudEPConst.STATUS_PROCESS_DELAYED

        # zipファイル作成フラグがTrueの場合、結果データ用のZIPファイルを作成する
        if make_zip_flag:
            # 投入データ用のZIPファイルを作成する
            result_data_path = shutil.make_archive(base_name=temp_dir, format="zip", root_dir=log_dir)
            if os.path.exists(result_data_path) is False:
                log_msg = g.appmsg.get_log_message("MSG-82009", [tf_workspace_name])
                g.applogger.error(log_msg)
                msg = g.appmsg.get_api_message("MSG-82009", [tf_workspace_name])
                raise Exception(msg)
            else:
                # zipファイル名を変更 [execution_no].zip > InputData_[execution_no].zip
                result_data_rename_dir_path = base_dir + TFCloudEPConst.DIR_TEMP
                result_data_rename_path = result_data_rename_dir_path + '/ResultData_' + execution_no + '.zip'
                os.rename(result_data_path, result_data_rename_path)
                if os.path.exists(result_data_rename_path) is False:
                    log_msg = g.appmsg.get_log_message("MSG-82009", [tf_workspace_name])
                    g.applogger.error(log_msg)
                    msg = g.appmsg.get_api_message("MSG-82009", [tf_workspace_name])
                    raise Exception(msg)

        # ステータス更新フラグがTrueの場合、ステータス更新を実行。
        if status_update_flag:
            # update_dataに値をセット
            update_data['EXECUTION_NO'] = execution_no
            update_data['STATUS_ID'] = set_status_id

            # ステータスが「完了」「完了(異常)」なら終了時間をセット
            if set_status_id == TFCloudEPConst.STATUS_COMPLETE or set_status_id == TFCloudEPConst.STATUS_FAILURE:
                update_data['TIME_END'] = get_timestamp()

            # make_zip_flagがTrueなら結果データをセット
            if make_zip_flag:
                zip_file_name = "ResultData_" + execution_no + ".zip"
                update_data['FILE_RESULT'] = zip_file_name

            # 作業インスタンスのステータスを更新
            ret, execute_data = update_execution_record(objdbca, TFCloudEPConst, update_data, result_data_rename_dir_path)
            if ret:
                objdbca.db_commit()
                if set_status_id == TFCloudEPConst.STATUS_COMPLETE:
                    g.applogger.debug(g.appmsg.get_log_message("BKY-51004", [execution_no]))
                elif set_status_id == TFCloudEPConst.STATUS_FAILURE:
                    g.applogger.debug(g.appmsg.get_log_message("BKY-51005", [execution_no]))
                elif set_status_id == TFCloudEPConst.STATUS_PROCESS_DELAYED:
                    g.applogger.debug(g.appmsg.get_log_message("BKY-51003", [execution_no]))
            else:
                log_msg = g.appmsg.get_log_message("BKY-50101", [])  # Failed to update status.
                g.applogger.error(log_msg)
                raise Exception(log_msg)

        return True

    except Exception as msg:
        # 受け取ったメッセージをerror_logに書き込み
        with open(error_log, 'w') as f:
            f.write(str(msg))

        return False
